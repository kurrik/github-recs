#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import argparse
import sys
import os
import os.path
import glob
import subprocess as sp
from collections import defaultdict
from itertools import product
import numpy as np

METRICS = ['MCC', 'Accuracy', 'Precision']

def ParseFile(path, metric):
  if os.path.isfile(path):
    with open(path, 'r') as fin:
      for line in fin:
        label,val = line.split(',')
        if label == metric:
          return float(val)
      return 0.0
  return 0.0

def Graph(datapath, graphpath, label):
  with open(os.path.join(os.path.dirname(__file__), 'graph.r')) as f:
    sp.call(['R', '--slave', '--no-save', datapath, graphpath, label], stdin=f)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--root', default='results', type=str)
  args = parser.parse_args()

  charts = frozenset(['repos', 'users'])
  isdir = lambda x: os.path.isdir(os.path.join(args.root,x))
  fname = lambda x: os.path.splitext(os.path.basename(x))[0]

  metrics = ['MCC','Accuracy','Precision']
  datasets = set([x for x in os.listdir(args.root) if isdir(x)])
  for chartname in charts:
    tables = set([])
    for dataset in datasets:
      csvglob = os.path.join(args.root, dataset, chartname + '*')
      tables.update(set([fname(csv) for csv in glob.iglob(csvglob)]))
    tables = sorted(list(tables))
    n = len(datasets)
    m = len(tables)
    for metric in metrics:
      data = np.zeros((m,n))
      for j, dataset in enumerate(datasets):
        for i, table in enumerate(tables):
          path = os.path.join(args.root, dataset, table + '.csv')
          data[i,j] = ParseFile(path, metric)
      outname = '%s_%s' % (chartname, metric.lower())
      outpath = os.path.join(args.root, outname + '.csv')
      graphpath = os.path.join(args.root, outname + '.pdf')
      with open(outpath, 'w') as fout:
        fout.write('Label\t' + '\t'.join(datasets) + '\n')
        for i in range(m):
          fout.write(tables[i])
          for j in range(n):
            fout.write('\t' + '%4.20f' % data[i,j])
          fout.write('\n')
      Graph(outpath, graphpath, metric)
