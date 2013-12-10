#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import os
import sys
import math
import argparse
from subprocess import call

def ParseLine(line):
  # Line format is <screen_name>,"<id1>,<id2>,..."\n
  split_index = line.index(',')
  screen_name = line[:split_index]
  repo_string = line[split_index+1:-1]
  if repo_string[0] == '"':
    repo_string = repo_string[1:-1]
  if repo_string.find('"') > -1:
    # Shouldn't be any quotes in the line, but print in case something is weird.
    print 'Found quote in line which should not have one: %s' % repo_string
  return screen_name, [int(x) for x in repo_string.split(',')]

def Convert(inpath, outpath, minrepos, maxrepos):
  count = 0
  mindump = 0
  maxdump = 0
  with open(inpath, 'rb') as infile:
    with open(outpath, 'w') as outfile:
      infile.next() # Discard header.
      for line in infile:
        screen_name, repos = ParseLine(line)
        if len(repos) > maxrepos:
          # Some users touch a LOT of repos, like "Try-Git"
          print " Skipping '%s' with %s repos" % (screen_name, len(repos))
          maxdump += 1
          continue
        if len(repos) < minrepos:
          mindump += 1
          continue
        repos.sort()
        outfile.write("%s\n" % " ".join(map(str, repos)))
        count += 1
  fmt = "Converted %s records from %s to %s, dropped %s small %s large records"
  print fmt % (count, inpath, outpath, mindump, maxdump)

def Apriori(binary, data, rulesets, minsup, minconf):
  minsup = '-s-%s' % minsup
  minconf = '-c%s' % minconf
  call([binary, '-tr', minsup, minconf, data, rulesets])

def ParseRule(line):
  parts = line.split(' ')
  consequents = list()
  antecedents = list()
  in_cons = True
  for part in parts:
    if part == '<-':
      in_cons = False
      continue
    elif part == '':
      break
    elif part[0] == '(':
      break
    if in_cons:
      consequents.append(part)
    else:
      antecedents.append(part)
  return (frozenset(antecedents), frozenset(consequents))

def ReadRules(path):
  rules = []
  with open(path, 'r') as f:
    for line in f:
      rules.append(ParseRule(line))
  return rules

def ScoreRule(ant, con, trans, cache):
  if not cache.has_key(ant):
    cache[ant] = ant.issubset(trans)
  if not cache.has_key(con):
    cache[con] = con.issubset(trans)
  if cache[ant]:
    if cache[con]:
      return 'TP'
    else:
      return 'FP'
  else:
    if cache[con]:
      return 'FN'
    else:
      return 'TN'

def PrintProgress(count, length):
  pct = float(100 * count) / float(length)
  print >> sys.stdout, "\r  Line %s of %s = %3.4f" % (count, length, pct),
  sys.stdout.flush()

def ScoreFile(rules, testpath):
  counts = {
      'Rules': len(rules),
      'TP': 0,
      'TN': 0,
      'FP': 0,
      'FN': 0,
  }
  length = 0
  with open(testpath) as f:
    for line in f:
      length += 1

  count = 0
  with open(testpath) as f:
    for line in f:
      count += 1
      if count % 20 == 0:
        PrintProgress(count, length)
      trans = frozenset(line.split(' '))
      cache = {}
      seen_fn = False
      seen_score = False
      for ant, con in rules:
        score = ScoreRule(ant, con, trans, cache)
        if score == 'TP' or score == 'FP':
          counts[score] += 1
          seen_score = True
        elif score == 'FN':
          seen_fn = True
      if not seen_score:
        if seen_fn:
          counts['FN'] += 1
        else:
          counts['TN'] += 1
    print
  return counts

def Test(ruleset, test, outfile):
  rules = ReadRules(ruleset)
  counts = ScoreFile(rules, test)
  print "Outputting counts to %s" % outfile
  with open(outfile, 'w') as f:
    for key, count in counts.iteritems():
      f.write("%s,%s\n" % (key, count))
      print '%s: %s' % (key, count)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--binary',   default='lib/apriori/apriori/src/apriori')
  parser.add_argument('--tmpdir',   default='/tmp')
  parser.add_argument('--minsup',   default=80, type=int)
  parser.add_argument('--minconf',  default=50, type=int)
  parser.add_argument('--minrepos', default=2, type=int)
  parser.add_argument('--maxrepos', default=1000, type=int)
  parser.add_argument('--train',    default=None, type=str)
  parser.add_argument('--ruleset',  default=None, type=str)
  parser.add_argument('--results',  default=None, type=str)
  parser.add_argument('--test',     default=None, type=str)
  parser.add_argument('--clear',    action='store_true')
  args = parser.parse_args()

  if args.ruleset is None:
    parser.exit(1, 'Ruleset file must be specified for both train and test')

  if args.train is not None:
    if os.path.isfile(args.ruleset) and args.clear == False:
      print 'Skipping train %s because ruleset %s exists' % (args.train, args.ruleset)
    else:
      tmpfile = os.path.join(args.tmpdir, 'apriori_train_tmp')
      Convert(args.train, tmpfile, args.minrepos, args.maxrepos)
      Apriori(args.binary, tmpfile, args.ruleset, args.minsup, args.minconf)

  if args.test is not None:
    if args.results is None:
      parser.exit(1, 'Results output file must be specified')
    if os.path.isfile(args.results) and args.clear == False:
      print 'Skipping test %s because output %s exists' % (args.test, args.results)
    else:
      if not os.path.isfile(args.ruleset):
        parser.exit(1, 'Ruleset file must exist')
      tmpfile = os.path.join(args.tmpdir, 'apriori_test_tmp')
      Convert(args.test, tmpfile, args.minrepos, args.maxrepos)
      Test(args.ruleset, tmpfile, args.results)
