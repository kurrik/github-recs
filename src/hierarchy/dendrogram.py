#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import snap
import math
import random
from subprocess import call
from collections import deque

class PNode(object):
  def __init__(self):
    self.left = None
    self.right = None
    self.parent = None
    self.value = None
    self.level = 0
    self.prob = None

  def setleft(self, n):
    self.left = n
    n.parent = self

  def setright(self, n):
    self.right = n
    n.parent = self

class DNode(PNode):
  def __init__(self):
    super(DNode, self).__init__()
    self.lr = 1
    self.rr = 0
    self.er = 0

  def calc_prob(self):
    return self.er / float(self.lr * self.rr)

  def __repr_prefix(self, prefix):
    if self.value != None:
      return '%s[%s]' % (prefix, self.value)
    nstr = 'Er:%s, Lr:%s, Rr:%s, Lvl:%s' % (self.er, self.lr, self.rr, self.level)
    if self.left.value != None:
      lstr = '[%s]' % self.left.value
    else:
      lstr = '\n' + self.left.__repr_prefix(prefix + '┃ ')
    if self.right.value != None:
      rstr = '[%s]' % self.right.value
    else:
      rstr = '\n' + self.right.__repr_prefix(prefix + '  ')
    return prefix + ('\n%s' % prefix).join([
      '┣ %s' % nstr,
      '┣ L:%s' % lstr,
      '┗ R:%s' % rstr,
    ])

  def __repr__(self):
    return '\n' + self.__repr_prefix('')

class Dendrogram(object):
  def __init__(self, graph):
    self.__lastnode = None
    self.__lastmove = None
    self.__likelihood = None
    self.graph = graph
    self.index = {}
    self.internal = []
    sweep = deque(GraphNodes(graph), graph.GetNodes())
    while True:
      n1 = sweep.popleft()
      if n1.value != None:
        self.index[n1.value] = n1
      try:
        n2 = sweep.popleft()
      except IndexError:
        self.root = n1
        break
      self.index[n2.value] = n2
      parent = DNode()
      parent.left = n1
      parent.right = n2
      parent.level = max(n1.level, n2.level) + 1
      parent.lr = n1.lr + n1.rr
      parent.rr = n2.lr + n2.rr
      n1.parent = parent
      n2.parent = parent
      self.internal.append(parent)
      sweep.append(parent)
    self.internal.pop() # Remove root from internal list.
    self.__calc_er()

  # Lowest common ancestor
  def lca(self, n1, n2):
    while n1 != n2:
      if n1.level > n2.level:
        n2 = n2.parent
      elif n1.level < n2.level:
        n1 = n1.parent
      else:
        n2 = n2.parent
        n1 = n1.parent
    return n1

  def randomnode(self):
    i = random.randint(0, len(self.internal)-1)
    return self.internal[i]

  def randommove(self):
    self.__lastnode = self.randomnode()
    self.__lastmove = random.randint(1,2)
    if self.__lastmove == 1:
      self.__flip1(self.__lastnode)
    else:
      self.__flip2(self.__lastnode)

  def markov(self):
    while True:
      l1 = self.__calc_likelihood()
      self.__likelihood = l1
      self.randommove()
      l2 = self.__calc_likelihood()
      if l2 - l1 >= 0:
        self.__likelihood = l2
        return
      a = math.exp(l2 -l1)
      if random.random() < a:
        print "Picked worse move with thresh %s" % a
        self.__likelihood = l2
        return
      self.undomove()

  def undomove(self):
    if self.__lastnode == None: return False
    if self.__lastmove == None: return False
    if self.__lastmove == 1:
      self.__undo1(self.__lastnode)
    else:
      self.__undo2(self.__lastnode)
    return True

  def node(self, nid):
    return self.index[nid]

  def nodes(self):
    queue = deque([self.root])
    while True:
      try:
        n = queue.popleft()
      except IndexError:
        break
      yield n
      if n.left != None:
        queue.append(n.left)
      if n.right != None:
        queue.append(n.right)

  def save_train_file(self, count, path):
    nodecount = sum(1 for _ in self.nodes())
    avg = [0] * nodecount
    for i in xrange(count):
      self.markov()
      for j, node in enumerate(self.nodes()):
        if node.value is None:
          avg[j] += node.calc_prob()
    lookup = {}
    with open(path, 'w') as f:
      f.write('id,parent_id,prob,value\n')
      for j, node in enumerate(self.nodes()):
        lookup[node] = j
        if node.parent is not None:
          parent_id = lookup[node.parent]
        else:
          parent_id = -1
        if node.value is not None:
          value = node.value
        else:
          value = -1
        pct = avg[j] / nodecount
        f.write('%i,%i,%4.10f,%i,%i\n' % (j, parent_id, pct, node.level, value))

  def __flip1(self, n):
    parent, s, t, u = self.__get_pstu(n)
    parent.setleft(s)
    parent.setright(n)
    n.setleft(t)
    n.setright(u)
    self.__fix_level(s,t,u,n)
    self.__fix_lrrr(parent, n)
    self.__calc_er()
    self.__likelihood = None

  def __undo1(self, n):
    parent = n.parent
    s = parent.left
    t = n.left
    u = n.right
    parent.setleft(n)
    parent.setright(u)
    n.setleft(s)
    n.setright(t)
    self.__fix_level(s,t,u,n)
    self.__fix_lrrr(parent, n)
    self.__calc_er()
    self.__likelihood = None

  def __flip2(self, n):
    parent, s, t, u = self.__get_pstu(n)
    parent.setleft(n)
    parent.setright(t)
    n.setleft(s)
    n.setright(u)
    self.__fix_level(s,t,u,n)
    self.__fix_lrrr(parent, n)
    self.__calc_er()
    self.__likelihood = None

  def __undo2(self, n):
    parent = n.parent
    t = parent.right
    s = n.left
    u = n.right
    parent.setleft(n)
    parent.setright(u)
    n.setleft(s)
    n.setright(t)
    self.__fix_level(s,t,u,n)
    self.__fix_lrrr(parent, n)
    self.__calc_er()
    self.__likelihood = None

  def __fix_level(self, *nodes):
    queue = deque(nodes)
    while len(queue) > 0:
      n = queue.popleft()
      if n.value != None:
        level = 0
      else:
        level = max(n.left.level, n.right.level) + 1
      if level != n.level:
        n.level = level
        if n.parent != None:
          queue.append(n.parent)

  def __fix_lrrr(self, parent, n):
    n.lr = n.left.lr + n.left.rr
    n.rr = n.right.lr + n.right.rr
    parent.lr = parent.left.lr + parent.left.rr
    parent.rr = parent.right.lr + parent.right.rr

  def __get_pstu(self, n):
    parent = n.parent
    s = n.left
    t = n.right
    if parent.left == n:
      u = parent.right
    else:
      u = parent.left
    return (parent, s, t, u)

  def __calc_er(self):
    for n in self.nodes():
      n.er = 0
    for e in self.graph.Edges():
      lca = self.lca(self.node(e.GetSrcNId()), self.node(e.GetDstNId()))
      lca.er += 1

  def __h(self, p):
    invp = 1 - p
    if p == 0:
      left = 0
    else:
      left = -(p * math.log(p))
    if invp == 0:
      right = 0
    else:
      right = (invp * math.log(invp))
    return left - right

  def __calc_likelihood(self):
    total = 0
    for n in self.nodes():
      if n.value != None:
        continue
      lrrr = float(n.lr * n.rr)
      pr = n.er / lrrr
      total += lrrr * self.__h(pr)
    return -total

  def likelihood(self):
    if self.__likelihood is None:
      self.__likelihood = self.__calc_likelihood()
    return self.__likelihood

  def merges(self):
    def nodeline(node, curr, lines):
      if node.left.value != None:
        lval = -(node.left.value+1)
      else:
        lval, curr = nodeline(node.left, curr, lines)
      if node.right.value != None:
        rval = -(node.right.value+1)
      else:
        rval, curr = nodeline(node.right, curr, lines)
      lines.append("%i,%i" % (lval, rval))
      return curr+1, curr+1
    lines = []
    nodeline(self.root, 0, lines)
    return lines

  def labels(self):
    def nodelabel(node, labels):
      if node.value != None:
        labels.append(node.value)
      else:
        nodelabel(node.left, labels)
        nodelabel(node.right, labels)
    labels = []
    nodelabel(self.root, labels)
    return labels

class Tester(object):
  def __init__(self, path):
    lookup = {}
    self.index = {}
    with open(path, 'r') as f:
      f.readline() # Header
      for line in f:
        node_id, parent_id, prob, level, value = self.__parse_line(line)
        node = PNode()
        lookup[node_id] = node

        node.level = level
        if value != -1:
          node.value = value
          self.index[value] = node
        node.prob = prob

        if parent_id != -1:
          parent = lookup[parent_id]
          if parent.left is None:
            parent.setleft(node)
          elif parent.right is None:
            parent.setright(node)
          else:
            raise ValueError('Expected to set child but parent was full')

  def __parse_line(self, line):
    node_id, parent_id, prob, level, value = line.split(',')
    return int(node_id), int(parent_id), float(prob), int(level), int(value)

  def __lca(self, n1, n2):
    while n1 != n2:
      if n1.level > n2.level:
        n2 = n2.parent
      elif n1.level < n2.level:
        n1 = n1.parent
      else:
        n2 = n2.parent
        n1 = n1.parent
    return n1

  def prob(self, n1, n2):
    if not self.index.has_key(n1) or not self.index.has_key(n2):
      return 0.0
    lca = self.__lca(self.index[n1], self.index[n2])
    return lca.prob

def GraphNodes(graph):
  for n in graph.Nodes():
    node = DNode()
    node.value = n.GetId()
    yield node
