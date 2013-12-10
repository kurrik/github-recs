#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import os
import sys
import snap
import argparse
from subprocess import call
import dendrogram
import cPickle as pickle
from itertools import combinations
from operator import itemgetter

def PrintProgress(count, length):
  pct = float(100 * count) / float(length)
  print >> sys.stdout, "\r  %s of %s = %3.4f" % (count, length, pct),
  sys.stdout.flush()

def GetCsvGraph(path):
  graph = snap.TUNGraph.New()
  with open(path, 'r') as f:
    f.readline()
    for line in f:
      a,b = map(int, line.split(','))
      if not graph.IsNode(a):
        graph.AddNode(a)
      if not graph.IsNode(b):
        graph.AddNode(b)
      graph.AddEdge(a, b)
  return graph

def DrawLikelihood(llh, r, tmpdir, out):
  if not os.path.isfile(r):
    raise IOError("%s did not exist" % r)
  datafile = os.path.join(tmpdir, 'hierarchy_likelihood')
  with open(datafile, 'w') as f:
    for i, ll in llh:
      f.write("%i\t%4.10f\n" % (i, ll))
  with open(r) as f:
    call(['R', '--slave', '--no-save', datafile, out], stdin=f)

def DrawGraph(dend, tmp, out):
  dotfile = os.path.join(tmp, 'dotfile')
  with open(dotfile, 'w') as f:
    f.write('graph network {\n')
    f.write('  layout=neato;\n')
    f.write('  overlap=scale;\n')
    for e in dend.graph.Edges():
      f.write('  %s -- %s;\n' % (e.GetSrcNId(), e.GetDstNId()))
    f.write('}')
  call(['dot', '-Tpdf', '-o%s' % out, dotfile])

def DrawDendrogram(dend, r, tmpdir, out):
  if not os.path.isfile(r):
    raise IOError("%s did not exist" % r)
  datafile = os.path.join(tmpdir, 'hierarchy_data')
  labelfile = os.path.join(tmpdir, 'hierarchy_labels')
  with open(datafile, 'w') as f:
    for line in dend.merges():
      f.write("%s\n" % line)
  with open(labelfile, 'w') as f:
    for line in dend.labels():
      f.write("%s\n" % line)
  with open(r) as f:
    call(['R', '--slave', '--no-save', datafile, labelfile, out], stdin=f)

def Test(args):
  if os.path.isfile(args.results) and args.clear == False:
    print 'Skipping test because "%s" exists' % args.results
    return

  tester = dendrogram.Tester(args.ruleset)
  nodes = set()
  edges = set()
  with open(args.test, 'r') as f:
    f.readline()
    for line in f:
      edges.add(line.strip())
      nida, nidb = map(int,line.split(','))
      nodes.add(nida)
      nodes.add(nidb)

  counts = {
      'TP': 0,
      'TN': 0,
      'FP': 0,
      'FN': 0,
  }
  total = (len(nodes)) * (len(nodes) - 1) / 2 # n! / r! / (n-r)!
  count = 0
  probs = []
  for nida, nidb in combinations(nodes, 2):
    if count % 100 == 0:
      PrintProgress(count, total)
    prob = tester.prob(nida, nidb)
    is_edge = '%i,%i' % (nida, nidb) in edges
    probs.append((prob, is_edge))
    count += 1
  probs.sort(key=itemgetter(0), reverse=True)
  thresh = args.thresh * count
  for i in xrange(count):
    is_edge = probs[i][1]
    if i <= thresh:
      if is_edge:
        counts['TP'] += 1
      else:
        counts['FP'] += 1
    else:
      if is_edge:
        counts['FN'] += 1
      else:
        counts['TN'] += 1
  print

  print "Outputting counts to %s" % args.results
  with open(args.results, 'w') as f:
    for key, count in counts.iteritems():
      f.write("%s,%s\n" % (key, count))
      print '%s: %s' % (key, count)

def Train(args):
  if os.path.isfile(args.ruleset) and args.clear == False:
    print 'Skipping train because "%s" exists' % args.ruleset
    return

  graph = GetCsvGraph(args.train)
  dend = dendrogram.Dendrogram(graph)

  if args.draw_network:
    path_graph = '{0}.network.pdf'.format(args.train)
    if os.path.isfile(path_graph) and args.clear == False:
      print 'Skipping creating "%s" because file exists' % path_graph
    else:
      DrawGraph(dend, args.tmpdir, path_graph)

  if args.draw_dendrogram:
    path_graph = '{0}.dendrogram_pre.pdf'.format(args.train)
    r_dendrogram = os.path.join(os.path.dirname(__file__), args.r_dendrogram)
    if os.path.isfile(path_graph) and args.clear == False:
      print 'Skipping creating "%s" because file exists' % path_graph
    else:
      DrawDendrogram(dend, r_dendrogram, args.tmpdir, path_graph)

  lh = []
  postfix = ''
  print
  try:
    for i in range(args.iter):
      dend.markov()
      print("\rMarkov step %s: Likelihood: %s" % (i, dend.likelihood())),
      sys.stdout.flush()
      lh.append((i, dend.likelihood()))
  except KeyboardInterrupt:
    # Allow Interrupt
    postfix = '_incomplete'
  print
  dend.save_train_file(5, args.ruleset + postfix)

  if args.draw_dendrogram:
    path_graph = '{0}.dendrogram_post{1}.pdf'.format(args.train, postfix)
    r_dendrogram = os.path.join(os.path.dirname(__file__), args.r_dendrogram)
    if os.path.isfile(path_graph) and args.clear == False:
      print 'Skipping creating "%s" because file exists' % path_graph
    else:
      DrawDendrogram(dend, r_dendrogram, args.tmpdir, path_graph)

  if args.draw_likelihood:
    path_graph = '{0}.likelihood{1}.pdf'.format(args.train, postfix)
    r_likelihood = os.path.join(os.path.dirname(__file__), args.r_likelihood)
    if os.path.isfile(path_graph) and args.clear == False:
      print 'Skipping creating "%s" because file exists' % path_graph
    else:
      DrawLikelihood(lh, r_likelihood, args.tmpdir, path_graph)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--draw_network',    action='store_true')
  parser.add_argument('--draw_dendrogram', action='store_true')
  parser.add_argument('--draw_likelihood', action='store_true')
  parser.add_argument('--tmpdir',          default='/tmp', type=str)
  parser.add_argument('--r_dendrogram',    default='dendrogram.r', type=str)
  parser.add_argument('--r_likelihood',    default='likelihood.r', type=str)
  parser.add_argument('--iter',            default=10000, type=int)
  parser.add_argument('--train',           default=None, type=str)
  parser.add_argument('--ruleset',         default=None, type=str)
  parser.add_argument('--results',         default=None, type=str)
  parser.add_argument('--test',            default=None, type=str)
  parser.add_argument('--thresh',          default=0.01, type=float)
  parser.add_argument('--clear',           action='store_true')
  args = parser.parse_args()

  if args.ruleset is None:
    parser.exit(1, 'Ruleset file must be specified for both train and test')

  if args.train is not None:
    Train(args)

  if args.test is not None:
    Test(args)

