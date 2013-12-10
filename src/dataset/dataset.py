#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import os
import sys
import argparse
from subprocess import check_call, call, CalledProcessError

TABLE_EVENTS          = 'events'
TABLE_REPOS           = 'repos'
TABLE_USERS           = 'users'
TABLE_REPO_USER       = 'repo_user'
TABLE_REPO_REPO       = 'repo_repo'
TABLE_USER_USER       = 'user_user'
TABLE_REPO_TRANS      = 'repo_trans'
TABLE_USER_TRANS      = 'user_trans'
TABLE_REPO_EDGES      = 'repo_edges'
TABLE_USER_EDGES      = 'user_edges'
TABLE_ADHOC           = 'adhoc'
TABLE_REPO_TRAIN_CAND = 'repo_train_cand'
TABLE_REPO_TRAIN_EDGE = 'repo_train_edge'
TABLE_REPO_TRAIN      = 'repo_train'
TABLE_USER_TRAIN_CAND = 'user_train_cand'
TABLE_USER_TRAIN_EDGE = 'user_train_edge'
TABLE_USER_TRAIN      = 'user_train'

EXPORT_TABLES = [
  TABLE_REPOS,
  TABLE_USERS,
  TABLE_REPO_REPO,
  TABLE_USER_USER,
  TABLE_REPO_TRANS,
  TABLE_USER_TRANS,
  TABLE_REPO_EDGES,
  TABLE_USER_EDGES,
  TABLE_REPO_TRAIN,
  TABLE_USER_TRAIN,
]

class BigQuery(object):
  def __init__(self, dataset):
    self.dataset = dataset

  def __CopyTable(self, bucket, table, path):
    url = 'gs://{0}/{1}/{2}'.format(bucket, self.dataset, table)
    filepath = os.path.join(path, table)
    if os.path.exists(filepath):
      os.remove(filepath)
    check_call(['gsutil', 'cp', url, path])

  def __Exists(self, table):
    cmd = ['bq', 'show', self.__Path(table)]
    self.__Log_Cmd(cmd)
    return call(cmd) == 0

  def __ExportTable(self, bucket, table):
    url = 'gs://{0}/{1}/{2}'.format(bucket, self.dataset, table)
    check_call(['bq', 'extract', self.__Path(table), url])

  def __Log_Cmd(self, cmd):
    print 'Running:\n  %s' % ' '.join(cmd)

  def __Path(self, table):
    return '%s.%s' % (self.dataset, table)

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

  def Copy(self, bucket, outputdir):
    path = os.path.join(outputdir, self.dataset)
    if not os.path.exists(path):
      os.makedirs(path)
    for table in EXPORT_TABLES:
      self.__CopyTable(bucket, table, path)

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
    for table in EXPORT_TABLES:
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
        repository_url AS repo_url,
        COUNT(actor) AS users,
        RATIO_TO_REPORT(users) OVER() AS users_ratio
      FROM [{0}]
      GROUP EACH BY repo_url
    """.format(self.__Path(TABLE_EVENTS))
    self.__Query(sql, TABLE_REPOS)

  def SelectUsers(self):
    sql = """
      SELECT
        ROW_NUMBER() OVER (ORDER BY user ASC) AS user_id,
        actor AS user,
        COUNT(repository_url) AS repos,
        RATIO_TO_REPORT(repos) OVER() AS repos_ratio
      FROM [{0}]
      GROUP EACH BY user
    """.format(self.__Path(TABLE_EVENTS))
    self.__Query(sql, TABLE_USERS)

  def SelectRepoUser(self):
    sql = """
      SELECT
        repo_users.repo_id AS repo_id,
        users.user_id AS user_id,
        repo_users.repo_users_ratio AS repo_users_ratio,
        users.repos_ratio AS user_repos_ratio
      FROM (
        SELECT
          events.actor AS user,
          repos.repo_id AS repo_id,
          repos.users_ratio AS repo_users_ratio
        FROM
          [{0}] AS events
          JOIN EACH [{1}] AS repos
          ON events.repository_url = repos.repo_url
      ) AS repo_users
      JOIN EACH [{2}] AS users
      ON repo_users.user = users.user
      GROUP EACH BY repo_id, user_id, repo_users_ratio, user_repos_ratio
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

  def SelectRepoTrans(self):
    sql = """
      SELECT user_id, GROUP_CONCAT(STRING(repo_id)) AS repo_ids
      FROM [{0}]
      GROUP EACH BY user_id
      ORDER BY user_id
    """.format(
        self.__Path(TABLE_REPO_USER))
    self.__Query(sql, TABLE_REPO_TRANS)

  def SelectUserTrans(self):
    sql = """
      SELECT repo_id, GROUP_CONCAT(STRING(user_id)) AS user_ids
      FROM [{0}]
      GROUP EACH BY repo_id
      ORDER BY repo_id
    """.format(
        self.__Path(TABLE_REPO_USER))
    self.__Query(sql, TABLE_USER_TRANS)

  def SelectRepoEdges(self):
    sql = """
      SELECT
        a.repo_id AS id_a,
        b.repo_id AS id_b,
        a.repo_users_ratio AS users_ratio_a,
        b.repo_users_ratio AS users_ratio_b,
        COUNT(a.user_id) AS common_users,
        RATIO_TO_REPORT(common_users) OVER() AS common_users_ratio
      FROM
        [{0}] as a
        JOIN EACH [{0}] as b
        ON a.user_id = b.user_id
      WHERE a.repo_id != b.repo_id
      GROUP EACH BY id_a, id_b, users_ratio_a, users_ratio_b
    """.format(
        self.__Path(TABLE_REPO_USER))
    self.__Query(sql, TABLE_REPO_EDGES)

  def SelectRepoTrainCandidates(self):
    sql = """SELECT
        a.id_a AS id_a,
        b.id_b AS id_b,
        COUNT(a.id_b) AS shared_count,
        RATIO_TO_REPORT(shared_count) OVER() AS shared_count_ratio,
        a.users_ratio_a AS users_ratio_a,
        b.users_ratio_b AS users_ratio_b,
        CONCAT(CONCAT(STRING(a.id_a),'-'),STRING(b.id_b)) AS id
      FROM
        [{0}] AS a
        JOIN EACH [{0}] AS b
        ON a.id_b = b.id_a
      WHERE a.id_a != b.id_b
      GROUP BY id_a, id_b, id, users_ratio_a, users_ratio_b
    """.format(self.__Path(TABLE_REPO_EDGES))
    self.__Query(sql, TABLE_REPO_TRAIN_CAND)

  def SelectUserTrainCandidates(self):
    sql = """SELECT
        a.id_a AS id_a,
        b.id_b AS id_b,
        COUNT(a.id_b) AS shared_count,
        RATIO_TO_REPORT(shared_count) OVER() AS shared_count_ratio,
        a.repos_ratio_a AS repos_ratio_a,
        b.repos_ratio_b AS repos_ratio_b,
        CONCAT(CONCAT(STRING(a.id_a),'-'),STRING(b.id_b)) AS id
      FROM
        [{0}] AS a
        JOIN EACH [{0}] AS b
        ON a.id_b = b.id_a
      WHERE a.id_a != b.id_b
      GROUP BY id_a, id_b, id, repos_ratio_a, repos_ratio_b
    """.format(self.__Path(TABLE_USER_EDGES))
    self.__Query(sql, TABLE_USER_TRAIN_CAND)

  def SelectRepoTrainEdges(self):
    sql = """SELECT
        1 AS is_edge,
        CONCAT(CONCAT(STRING(id_a),'-'),STRING(id_b)) AS id
      FROM
        [{0}]
    """.format(self.__Path(TABLE_REPO_EDGES))
    self.__Query(sql, TABLE_REPO_TRAIN_EDGE)

  def SelectUserTrainEdges(self):
    sql = """SELECT
        1 AS is_edge,
        CONCAT(CONCAT(STRING(id_a),'-'),STRING(id_b)) AS id
      FROM
        [{0}]
    """.format(self.__Path(TABLE_USER_EDGES))
    self.__Query(sql, TABLE_USER_TRAIN_EDGE)

  def SelectRepoTrain(self):
    sql = """SELECT
      candidates.id_a AS id_a,
      candidates.id_b AS id_b,
      candidates.shared_count_ratio AS shared_count_ratio,
      candidates.users_ratio_a AS users_ratio_a,
      candidates.users_ratio_b AS users_ratio_b,
      IFNULL(edges.is_edge, 0) AS is_edge
    FROM
      [{0}] AS candidates
      LEFT OUTER JOIN [{1}] AS edges
      ON candidates.id = edges.id
    """.format(
        self.__Path(TABLE_REPO_TRAIN_CAND),
        self.__Path(TABLE_REPO_TRAIN_EDGE))
    self.__Query(sql, TABLE_REPO_TRAIN)

  def SelectUserTrain(self):
    sql = """SELECT
      candidates.id_a AS id_a,
      candidates.id_b AS id_b,
      candidates.shared_count_ratio AS shared_count_ratio,
      candidates.repos_ratio_a AS repos_ratio_a,
      candidates.repos_ratio_b AS repos_ratio_b,
      IFNULL(edges.is_edge, 0) AS is_edge
    FROM
      [{0}] AS candidates
      LEFT OUTER JOIN [{1}] AS edges
      ON candidates.id = edges.id
    """.format(
        self.__Path(TABLE_USER_TRAIN_CAND),
        self.__Path(TABLE_USER_TRAIN_EDGE))
    self.__Query(sql, TABLE_USER_TRAIN)

  def SelectUserEdges(self):
    sql = """
      SELECT
        a.user_id AS id_a,
        b.user_id AS id_b,
        a.user_repos_ratio AS repos_ratio_a,
        b.user_repos_ratio AS repos_ratio_b,
        COUNT(a.repo_id) AS common_repos,
        RATIO_TO_REPORT(common_repos) OVER() AS common_repos_ratio
      FROM
        [{0}] as a
        JOIN EACH [{0}] as b
        ON a.repo_id = b.repo_id
      WHERE a.user_id != b.user_id
      GROUP EACH BY id_a, id_b, repos_ratio_a, repos_ratio_b
    """.format(
        self.__Path(TABLE_REPO_USER))
    self.__Query(sql, TABLE_USER_EDGES)

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
    query.SelectEvents(select_file)
    query.SelectRepos()
    query.SelectUsers()
    query.SelectRepoUser()
    query.SelectRepoRepo()
    query.SelectUserUser()
    query.SelectRepoTrans()
    query.SelectUserTrans()
    query.SelectRepoEdges()
    query.SelectUserEdges()
    query.SelectRepoTrainCandidates()
    query.SelectRepoTrainEdges()
    query.SelectRepoTrain()
    query.SelectUserTrainCandidates()
    query.SelectUserTrainEdges()
    query.SelectUserTrain()

if __name__ == '__main__':
  actions = ['select', 'query', 'export', 'copy_local']
  parser = argparse.ArgumentParser()
  parser.add_argument('--dataset',   default='golang_recent', type=str)
  parser.add_argument('--bucket',    default='kurrik_cs224w', type=str)
  parser.add_argument('--clear',     action='store_true')
  parser.add_argument('--action',    default='select', choices=actions)
  parser.add_argument('--user',      default='kurrik', type=str)
  parser.add_argument('--outputdir', default='data', type=str)
  args = parser.parse_args()

  query = BigQuery(args.dataset)

  try:
    if args.action == 'select':
      path = os.path.join(os.path.dirname(__file__), 'queries', '%s.sql' % args.dataset)
      if not os.path.isfile(path):
        raise IOError('Invalid dataset, no query at %s' % path)
      query.Select(path, args.clear)
    elif args.action == 'query':
      query.QueryUser(args.user)
    elif args.action == 'export':
      query.Export(args.bucket)
    elif args.action == 'copy_local':
      if not os.path.isdir(args.outputdir):
        raise IOError('Output directory "%s" did not exist' % args.outputdir)
      query.Copy(args.bucket, args.outputdir)
  except CalledProcessError, ex:
    print
    print '--' * 40
    print 'ERROR Command "%s" exited with nonzero response code' % ex.cmd
