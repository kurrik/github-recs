#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import os
import sys
import argparse
from subprocess import check_call, call, CalledProcessError

TABLE_EVENTS    = 'events'
TABLE_REPOS     = 'repos'
TABLE_USERS     = 'users'
TABLE_REPO_USER = 'repo_user'
TABLE_REPO_REPO = 'repo_repo'
TABLE_USER_USER = 'user_user'
TABLE_ADHOC     = 'adhoc'

class BigQuery(object):
  def __init__(self, dataset):
    self.dataset = dataset

  def __Path(self, table):
    return '%s.%s' % (self.dataset, table)

  def __Log_Cmd(self, cmd):
    print 'Running:\n  %s' % ' '.join(cmd)

  def __Exists(self, table):
    cmd = ['bq', 'show', self.__Path(table)]
    self.__Log_Cmd(cmd)
    return call(cmd) == 0

  def __ExportTable(self, bucket, table):
    url = 'gs://{0}/{1}/{2}'.format(bucket, self.dataset, table)
    check_call(['bq', 'extract', self.__Path(table), url])

  def __Query(self, sql, table):
    if self.__Exists(table):
      print 'Skipping query for %s because table exists' % table
      return
    sql = ' '.join([x.replace("'", '"').strip() for x in sql.split('\n')])
    cmd = [
        'bq',
        'query',
        '--allow_large_results',
        '--destination_table=' + self.__Path(table),
        "'%s'" % sql,
    ]
    self.__Log_Cmd(cmd)
    check_call(' '.join(cmd), shell=True)

  def ClearTable(self, table):
    cmd = ['bq', 'rm', '-f', self.__Path(table)]
    self.__Log_Cmd(cmd)
    return call(cmd) == 0

  def ClearDataset(self):
    check_call(['bq', 'rm', '-r', '-f', self.dataset])

  def CreateDataset(self):
    if call(['bq', 'show', self.dataset]) == 0:
      return
    check_call(['bq', 'mk', self.dataset])

  def Export(self, bucket):
    tables = [
      TABLE_REPOS,
      TABLE_USERS,
      TABLE_REPO_REPO,
      TABLE_USER_USER,
    ]
    for table in tables:
      self.__ExportTable(bucket, table)

  def SelectEvents(self, select_file):
    if not os.path.isfile(select_file):
      raise IOError('%s did not exist' % select_file)
    with open(select_file, 'r') as f:
      self.__Query(f.read(), TABLE_EVENTS)

  def SelectRepos(self):
    sql = """
      SELECT
        ROW_NUMBER() OVER (ORDER BY repo_url ASC) AS repo_id,
        repository_url AS repo_url
      FROM [{0}]
      GROUP EACH BY repo_url
    """.format(self.__Path(TABLE_EVENTS))
    self.__Query(sql, TABLE_REPOS)

  def SelectUsers(self):
    sql = """
      SELECT
        ROW_NUMBER() OVER (ORDER BY user ASC) AS user_id,
        actor AS user
      FROM [{0}]
      GROUP EACH BY user
    """.format(self.__Path(TABLE_EVENTS))
    self.__Query(sql, TABLE_USERS)

  def SelectRepoUser(self):
    sql = """
      SELECT
        repo_users.repo_id AS repo_id,
        users.user_id AS user_id
      FROM (
        SELECT
          events.actor AS user,
          repos.repo_id AS repo_id
        FROM
          [{0}] AS events
          JOIN EACH [{1}] AS repos
          ON events.repository_url = repos.repo_url
      ) AS repo_users
      JOIN EACH [{2}] AS users
      ON repo_users.user = users.user
      GROUP EACH BY repo_id, user_id
    """.format(
      self.__Path(TABLE_EVENTS),
      self.__Path(TABLE_REPOS),
      self.__Path(TABLE_USERS))
    self.__Query(sql, TABLE_REPO_USER)

  def SelectRepoRepo(self):
    sql = """
      SELECT
        a.repo_id AS id_a,
        b.repo_id AS id_b
      FROM
        [{0}] AS a
        JOIN EACH [{0}] AS b
        ON a.user_id = b.user_id
      WHERE a.repo_id < b.repo_id
      ORDER BY id_a, id_b
    """.format(
      self.__Path(TABLE_REPO_USER))
    self.__Query(sql, TABLE_REPO_REPO)

  def SelectUserUser(self):
    sql = """
      SELECT
        a.user_id AS id_a,
        b.user_id AS id_b
      FROM
        [{0}] AS a
        JOIN EACH [{0}] AS b
        ON a.repo_id = b.repo_id
      WHERE a.user_id < b.user_id
      ORDER BY id_a, id_b
    """.format(
      self.__Path(TABLE_REPO_USER))
    self.__Query(sql, TABLE_USER_USER)

  def QueryUser(self, name):
    sql = """
      SELECT
        repoid_user.user,
        repos.repo_url
      FROM (
        SELECT
          repo_users.repo_id AS repo_id,
          users.user AS user
        FROM
          [{0}] AS repo_users
          JOIN EACH [{1}] AS users
          ON repo_users.user_id = users.user_id
          WHERE users.user = "kurrik"
      ) AS repoid_user
      JOIN EACH [{3}] AS repos
      ON repos.repo_id = repoid_user.repo_id
    """.format(
      self.__Path(TABLE_REPO_USER),
      self.__Path(TABLE_USERS),
      name,
      self.__Path(TABLE_REPOS))
    self.ClearTable(TABLE_ADHOC)
    self.__Query(sql, TABLE_ADHOC)

  def Select(self, select_file, clear=False):
    if clear:
      query.ClearDataset()
    query.CreateDataset()
    query.SelectEvents('%s.sql' % args.dataset)
    query.SelectRepos()
    query.SelectUsers()
    query.SelectRepoUser()
    query.SelectRepoRepo()
    query.SelectUserUser()

if __name__ == '__main__':
  actions = ['select', 'query', 'export']
  parser = argparse.ArgumentParser()
  parser.add_argument('--dataset', default='golang', type=str)
  parser.add_argument('--bucket', 'kurrik_cs224w', type=str)
  parser.add_argument('--clear', action='store_true')
  parser.add_argument('--action', choices=actions, default='select')
  parser.add_argument('--user', type=str, default='kurrik')
  args = parser.parse_args()

  query = BigQuery(args.dataset)

  try:
    if args.action == 'select':
      path = os.path.join(os.path.dirname(__file__), '%s.sql' % args.dataset)
      query.Select(path, args.clear)
    elif args.action == 'query':
      query.QueryUser(args.user)
    elif args.action == 'export':
      query.Export(args.bucket)
  except CalledProcessError, ex:
    print
    print '--' * 40
    print 'ERROR Command "%s" exited with nonzero response code' % ex.cmd
