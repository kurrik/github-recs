#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import argparse
import sys
import os
import glob
import math
import subprocess as sp
from collections import Counter

class ResultCounter(object):
  LABELS = frozenset(['TP', 'FP', 'TN', 'FN'])

  def __init__(self):
    self.counter = Counter()

  def GetMCC(self):
    num = (
        (self.counter['TP'] * self.counter['TN']) -
        (self.counter['FP'] * self.counter['FN']))
    den = math.sqrt(
        (self.counter['TP'] + self.counter['FP']) *
        (self.counter['TP'] + self.counter['FN']) *
        (self.counter['TN'] + self.counter['FP']) *
        (self.counter['TN'] + self.counter['FN']))
    return float(num) / float(den)

  def GetAccuracy(self):
    num = self.counter['TP'] + self.counter['TN']
    den = (self.counter['TP'] + self.counter['FP'] +
        self.counter['FN'] + self.counter['TN'])
    return float(num) / float(den)

  def GetPrecision(self):
    num = self.counter['TP']
    den = self.counter['TP'] + self.counter['FP']
    return float(num) / float(den)

  def AddFile(self, path):
    with open(path, 'r') as f:
      for line in f:
        label,valstr = line.split(',')
        if label in self.LABELS:
          self.counter[label] += int(valstr)
        else:
          print 'label %s not in %s' % (label, self.LABELS)

  def AddFiles(self, paths):
    for p in paths:
      self.AddFile(p)

  def Save(self, path):
    dirpath = os.path.dirname(path)
    if not os.path.exists(dirpath):
      os.makedirs(dirpath)
    with open(path, 'w') as f:
      for label, val in self.counter.iteritems():
        f.write('%s,%i\n' % (label, val))
      f.write('MCC,%f\n'       % self.GetMCC())
      f.write('Accuracy,%f\n'  % self.GetAccuracy())
      f.write('Precision,%f\n' % self.GetPrecision())


class TestDataset(object):
  def __init__(self, k, resultroot, dataroot, dataset):
    self.k = k
    self.resultroot = resultroot
    self.dataroot = dataroot
    self.dataset = dataset
    self.overwrite = False

  def __rp(self, path):
    return os.path.join(self.resultroot, self.dataset, path)

  def __dp(self, path):
    return os.path.join(self.dataroot, self.dataset, path)

  def __exists(self, path):
    if self.overwrite:
      return False
    if os.path.exists(path) and os.path.isfile(path):
      print 'Path %s exists...' % path
      return True
    return False

  def __call(self, args):
    try:
      sp.check_call(args)
    except sp.CalledProcessError, ex:
      print
      print '--' * 40
      print 'ERROR: "%s" exited with nonzero response' % ' '.join(ex.cmd)
      os.exit(1)

  def KFold(self):
    """ Creates every kfold train/test file."""
    if self.__exists(self.__dp('kfold/repo_repo.0.test')):
      return
    self.__call([
      'python',
      'src/kfold/kfold.py',
      '--k=%i'       % self.k,
      '--input=%s'   % self.dataroot,
      '--dataset=%s' % self.dataset,
    ])

  def Apriori(self, repo, mapping, minsup, minconf):
    trainglob = 'kfold/%s.*.train' % repo
    resultpaths = []
    for trainpath in glob.iglob(self.__dp(trainglob)):
      i = int(trainpath.split('.')[1])
      prefix     = 'kfold/%s.%i' % (repo, i)
      rulepath   = self.__dp('%s.ruleset_%i_%i' % (prefix, minsup, minconf))
      resultpath = self.__dp('%s.results_%i_%i' % (prefix, minsup, minconf))
      testpath   = self.__dp('%s.test'          % (prefix))
      resultpaths.append(resultpath)
      if not self.__exists(rulepath):
        self.__call([
          'python',
          'src/apriori/apriori.py',
          '--ruleset=%s' % rulepath,
          '--train=%s'   % trainpath,
          '--minsup=%i'  % minsup,
          '--minconf=%i' % minconf,
        ])
      if not self.__exists(resultpath):
        self.__call([
          'python',
          'src/apriori/apriori.py',
          '--ruleset=%s' % rulepath,
          '--test=%s'    % testpath,
          '--results=%s' % resultpath,
        ])
    outpath = self.__rp('%s_apriori_%i_%i.csv' % (mapping, minsup, minconf))
    if not self.__exists(outpath):
      results = ResultCounter()
      results.AddFiles(resultpaths)
      results.Save(outpath)

  def Hierarchy(self, repo, mapping, thresh, iterations):
    trainglob = 'kfold/%s.*.train' % repo
    resultpaths = []
    for trainpath in glob.iglob(self.__dp(trainglob)):
      i = int(trainpath.split('.')[1])
      prefix     = 'kfold/%s.%i' % (repo, i)
      postfix    = ('%i_%f' % (iterations, thresh)).replace('.', 'p')
      rulepath   = self.__dp('%s.ruleset_%s' % (prefix, postfix))
      resultpath = self.__dp('%s.results_%s' % (prefix, postfix))
      testpath   = self.__dp('%s.test'       % prefix)
      resultpaths.append(resultpath)
      if not self.__exists(rulepath):
        self.__call([
          'python',
          'src/hierarchy/hierarchy.py',
          '--draw_likelihood',
          '--ruleset=%s' % rulepath,
          '--train=%s'   % trainpath,
          '--iter=%i'    % iterations,
        ])
      if not self.__exists(resultpath):
        self.__call([
          'python',
          'src/hierarchy/hierarchy.py',
          '--thresh=%2.10f'  % thresh,
          '--ruleset=%s' % rulepath,
          '--test=%s'    % testpath,
          '--results=%s' % resultpath,
        ])
    outpath = self.__rp('%s_hierarchy_%s.csv' % (mapping, postfix))
    if not self.__exists(outpath):
      results = ResultCounter()
      results.AddFiles(resultpaths)
      results.Save(outpath)

  def Logistic(self, repo, mapping, thresh):
    trainglob = 'kfold/%s.*.train' % repo
    resultpaths = []
    for trainpath in glob.iglob(self.__dp(trainglob)):
      i = int(trainpath.split('.')[1])
      prefix     = 'kfold/%s.%i' % (repo, i)
      postfix    = ('%f' % thresh).replace('.', 'p')
      rulepath   = self.__dp('%s.ruleset_%s' % (prefix, postfix))
      resultpath = self.__dp('%s.results_%s' % (prefix, postfix))
      testpath   = self.__dp('%s.test'       % prefix)
      resultpaths.append(resultpath)
      if not self.__exists(rulepath):
        self.__call([
          'python',
          'src/logistic/logistic.py',
          '--draw_costs',
          '--theta=%s'  % rulepath,
          '--train=%s'  % trainpath,
          '--thresh=%2.10f' % thresh,
        ])
      if not self.__exists(resultpath):
        self.__call([
          'python',
          'src/logistic/logistic.py',
          '--theta=%s'   % rulepath,
          '--test=%s'    % testpath,
          '--results=%s' % resultpath,
        ])
    outpath = self.__rp('%s_logistic_%s.csv' % (mapping, postfix))
    if not self.__exists(outpath):
      results = ResultCounter()
      results.AddFiles(resultpaths)
      results.Save(outpath)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--resultroot',       default='results', type=str)
  parser.add_argument('--dataroot',         default='data', type=str)
  parser.add_argument('--dataset',          default='golang_recent', type=str)
  parser.add_argument('--k',                default=3, type=int)
  args = parser.parse_args()

  APRIORI_MINSUP   = 3
  APRIORI_MINCONF  = 80
  HIERARCHY_THRESH = 0.005
  HIERARCHY_ITER   = 10000
  LOGISTIC_THRESH  = 0.0000005

  runs = {
    'golang_recent': {
      'apriori': [
        ('repo_trans', 'repos', APRIORI_MINSUP, APRIORI_MINCONF),
        ('user_trans', 'users', APRIORI_MINSUP, APRIORI_MINCONF),
      ],
      'hierarchy': [
        ['repo_repo', 'repos', HIERARCHY_THRESH, 1000],
        ['user_user', 'users', HIERARCHY_THRESH, HIERARCHY_ITER],
      ],
      'logistic': [
        ['repo_train', 'repos', 0.00001],
        ['user_train', 'users', LOGISTIC_THRESH],
      ],
    },
  }

  for dataset, conf in runs.iteritems():
    ds = TestDataset(args.k, args.resultroot, args.dataroot, dataset)
    ds.KFold()
    for (table, mapping, minsup, minconf) in conf['apriori']:
      ds.Apriori(table, mapping, minsup, minconf)
    for (table, mapping, thresh, iterations) in conf['hierarchy']:
      ds.Hierarchy(table, mapping, thresh, iterations)
    for (table, mapping, thresh) in conf['logistic']:
      ds.Logistic(table, mapping, thresh)
