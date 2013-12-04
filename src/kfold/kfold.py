#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import os
import sys
import glob
import argparse
from subprocess import check_call, call, CalledProcessError

def Clean(path):
  pathdir, pathfile = os.path.split(path)
  pattern = os.path.join(pathdir, 'kfold', '{0}*'.format(pathfile))
  for p in glob.iglob(pattern):
    os.remove(p)

def MakeKFold(k, path):
  pathdir, pathfile = os.path.split(path)
  outdir = os.path.join(pathdir, 'kfold')
  if not os.path.isdir(outdir):
    os.makedirs(outdir)

  for offset in range(k):
    print "Generating %s-fold #%s" % (k, offset)
    testp = os.path.join(outdir, '{0}.test_{1}'.format(pathfile, offset))
    trainp = os.path.join(outdir, '{0}.train_{1}'.format(pathfile, offset))
    print "  Reading\n    %s\n  Writing\n    %s\n    %s" % (path, testp, trainp)
    with open(testp, 'w') as testf:
      with open(trainp, 'w') as trainf:
        with open(path, 'r') as inpf:
          header = inpf.readline()
          testf.write(header)
          trainf.write(header)
          count = 0
          for line in inpf:
            if count % k == offset:
              testf.write(line)
            else:
              trainf.write(line)
            count += 1

if __name__ == '__main__':
  filenames = [
      'repo_repo',
      'repo_trans',
      'user_user',
      'user_trans',
  ]
  parser = argparse.ArgumentParser()
  parser.add_argument('--input', default='data', type=str)
  parser.add_argument('--dataset', default='golang_recent', type=str)
  parser.add_argument('--k', default=4, type=int)
  args = parser.parse_args()

  for filename in filenames:
    path = os.path.join(args.input, args.dataset, filename)
    if not os.path.isfile(path):
      raise IOError('File %s did not exist' % path)
    Clean(path)
    MakeKFold(args.k, path)
