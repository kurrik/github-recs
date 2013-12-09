#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import rmn
import numpy as np
from numpy import linalg
from itertools import combinations

class TestCliqueTemplates(object):
  def __init__(self):
    self.__templates = []

  def Templates(self):
    return self.__templates

  def AddTemplate(self, template):
    self.__templates.append(template)

class TestFeatures(object):
  def __init__(self, labels):
    self.__labels = labels
    self.__length = len(labels) * 2 + 1

  def __parse(self, line):
    label1, label2, exists = line.split(',')
    item = self.ZeroF()
    index1 = self.__labels.index(label1) + 1
    index2 = self.__labels.index(label2) + len(self.__labels) + 1
    item[index1] = 1
    item[index2] = 1
    item[0] = 1 if (exists == 'True') else 0
    return item

  def ZeroF(self):
    return np.array([0] * self.__length)

  def FCxy(self, c, y=None):
    item = self.__parse(c)
    if y is not None:
      item[0] = y
    return item

  def StartW(self):
    w = np.array([1] * self.__length)
    n = linalg.norm(w)
    return w / n

  def Candidate(self, line, y=None):
    item = self.__parse(line)
    if y is not None:
      item[0] = y
    return item

class TestCliqueTemplate(object):
  def __init__(self, features, cliques):
    self.Features = features
    self.__cliques = cliques

  def Cliques(self):
    return self.__cliques


if __name__ == '__main__':
  nodes = [
      'JavaScript','JavaScript','JavaScript','JavaScript',
      'Scala', 'Scala',
      'Go','Go',
      'PHP'
  ]
  edges = set([(0,1),(0,2),(0,3),(1,2),(4,5),(6,7),(5,2),(6,3),(7,1),(8,1)])

  CT = TestCliqueTemplates()
  data = []
  for edge in combinations(range(len(nodes)), 2):
    exists = edge in edges
    data.append("%s,%s,%s" % (nodes[edge[0]], nodes[edge[1]], exists))
  F = TestFeatures(['JavaScript', 'Scala', 'Go', 'PHP'])
  C = TestCliqueTemplate(F, data)
  CT.AddTemplate(C)

  net = rmn.RMN()
  w = net.W(CT)
  print w
  delta = 1
  while delta > 0.0001:
    w, delta = net.Descent(CT, w, 0.01, 0.3)
    print w, delta

  tests = [
      'JavaScript,Go,',
      'JavaScript,Scala,',
      'Go,Go,',
      'Scala,Scala,',
      'Go,Scala,',
      'JavaScript,JavaScript,',
      'PHP,JavaScript,',
      'PHP,Scala,',
      'PHP,Go,',
  ]
  for test in tests:
    newdata = [ test + 'False']
    NC = TestCliqueTemplate(F, newdata)
    NCT = TestCliqueTemplates()
    NCT.AddTemplate(NC)
    p0 = net.Pw(NCT, w)
    newdata = [ test + 'True']
    NC = TestCliqueTemplate(F, newdata)
    NCT = TestCliqueTemplates()
    NCT.AddTemplate(NC)
    p1 = net.Pw(NCT, w)
    print 'Predicting %s: p(0) = %2.10f, p(1) = %2.10f' % (test, p0, p1),
    if p0 > p1:
      print ' Predicted False'
    else:
      print ' Predicted True'
