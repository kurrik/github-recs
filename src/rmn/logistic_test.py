#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import logistic
import numpy as np
from numpy import linalg
from itertools import combinations

class TestFeatures(object):
  def __init__(self, labels):
    self.__labels = labels
    self.__length = len(labels) * 2 + 1

  def ParseX(self, line):
    label1, label2 = line.split(',')
    x = self.ZeroF()
    off = len(self.__labels)
    index1 = self.__labels.index(label1)
    index2 = self.__labels.index(label2)
    x[index1] = 1
    #x[index2] = 1
    #x[index1 + off] = 1
    x[index2 + off] = 1
    x[-1] = 1
    return x

  def Parse(self, line):
    exists, xline = line.split(',', 1)
    y = 1 if (exists == 'True') else -1
    x = self.ParseX(xline)
    print y, x
    return y, x

  def ZeroF(self):
    return np.array([0] * self.__length)

  def GetD(self, lines):
    return [self.Parse(line) for line in lines]

if __name__ == '__main__':
  nodes = [
      'JavaScript','JavaScript','JavaScript','JavaScript',
      'Scala', 'Scala',
      'Go','Go',
      'PHP'
  ]
  edges = set([(0,1),(0,2),(0,3),(1,2),(4,5),(6,7),(2,5),(3,6),(1,7),(1,8)])

  data = []
  for edge in combinations(range(len(nodes)), 2):
    exists = edge in edges or (edge[1],edge[0]) in edges
    data.append("%s,%s,%s" % (exists, nodes[edge[0]], nodes[edge[1]]))
  print data
  F = TestFeatures(['JavaScript', 'Scala', 'Go', 'PHP'])
  D = F.GetD(data)

  net = logistic.Logistic(0.09, 0.01)
  w = net.Weights(D)
  print w
  delta = 1
  while delta > 0.00001:
    w, delta = net.Descent(D, w)
  print w, delta

  tests = [
      'JavaScript,Go',
      'JavaScript,Scala',
      'Go,Go',
      'Scala,Scala',
      'Scala,Go',
      'JavaScript,JavaScript',
      'JavaScript,PHP',
      'Scala,PHP',
      'Go,PHP',
  ]
  for test in tests:
    pass
    x = F.ParseX(test)
    pF = net.Pw(-1, x, w)
    pT = net.Pw(1, x, w)
    print "Testing %s: P(T) = %s, P(F) = %s, Result = " % (test, pT, pF),
    if pF > pT:
      print "False"
    elif pT > pF:
      print "True"
    else:
      print "Tie"
    print "Dot: %s" % net.Sigmoid(np.dot(x, w))
