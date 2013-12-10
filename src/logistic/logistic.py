#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import argparse
import random
import numpy
import sys
import os

def Sigmoid(x):
  return 1.0 / (1.0 + numpy.exp((-1)*x))

def Normalize(x, mean, stddev):
  m, n = x.shape
  x = numpy.array(x)
  x = (x - mean) / stddev
  const = numpy.array([1] * m).reshape(m, 1)
  return numpy.append(const, x, axis=1)

class LogisticRegression:
  def __init__(self, X, Y, alpha=0.0005, lam=0.1):
    m, n = X.shape
    self.mean = numpy.mean(X, axis=0)
    self.stddev = numpy.std(X, axis=0)
    self.X = Normalize(X, self.mean, self.stddev)
    self.Y = numpy.array(Y)
    self.alpha = alpha
    self.lam = lam
    self.theta = numpy.array([0.0]*(n + 1))

  def __cost(self):
    m, n = self.X.shape
    h_theta = Sigmoid(numpy.dot(self.X, self.theta))
    cost1 = (-1) * self.Y * numpy.log(h_theta)
    cost2 = (1.0 - self.Y) * numpy.log(1.0 - h_theta)
    cost = (sum(cost1 - cost2) + 0.5 * self.lam * sum(self.theta[1:]**2)) / m
    return cost

  def Run(self, thresh):
    m,n = self.X.shape
    last = 1000000
    change = 1000000
    counter = 0
    while change > thresh:
      h_theta = Sigmoid(numpy.dot(self.X, self.theta))
      diff = h_theta - self.Y
      alpha_m = self.alpha * (1.0 / m)
      self.theta[0] -= alpha_m * sum(diff * self.X[:,0])
      for j in range(1,n):
        self.theta[j] -= alpha_m * (sum(diff * self.X[:,j]) + self.lam * m * self.theta[j])
      cost = self.__cost();
      change = abs(last - cost)
      last = cost
      counter += 1
      if counter % 100 == 0:
        print "\rIteration %i\tCost: %2.10f\tChange: %2.10f" % (counter, cost, change),
        sys.stdout.flush()
    print

  def Theta(self):
    return self.theta

  def SetTheta(self, theta):
    self.theta = theta

class Tester(object):
  def __init__(self, theta, mean, stddev):
    self.mean = mean
    self.stddev = stddev
    self.theta = theta

  def Predict(self, X):
    X = Normalize(X, self.mean, self.stddev)
    pred = Sigmoid(numpy.dot(X, self.theta))
    numpy.putmask(pred, pred >= 0.5 , 1.0)
    numpy.putmask(pred, pred < 0.5 , 0.0)
    return pred

def Train(args):
  if os.path.isfile(args.theta) and args.clear == False:
    print 'Skipping train because "%s" exists' % args.theta
    return
  data = numpy.loadtxt(args.train, delimiter=',', skiprows=1)
  y = data[:,5]
  x = data[:,[2,3,4]]
  lr = LogisticRegression(x, y)
  lr.Run(args.thresh)
  writefloat = lambda x: '%2.20f' % x
  with open(args.theta, 'w') as f:
    f.write('\t'.join(map(writefloat, lr.mean)) + '\n')
    f.write('\t'.join(map(writefloat, lr.stddev)) + '\n')
    f.write('\t'.join(map(writefloat, lr.Theta())))
  print 'Wrote mean: %s' % lr.mean
  print 'Wrote stddev: %s' % lr.stddev
  print 'Wrote theta: %s' % lr.theta

def Test(args):
  if os.path.isfile(args.results) and args.clear == False:
    print 'Skipping test because "%s" exists' % args.results
    return
  with open(args.theta, 'r') as f:
    mean = numpy.array(map(float, f.readline().split('\t')))
    stddev = numpy.array(map(float, f.readline().split('\t')))
  theta = numpy.loadtxt(args.theta, delimiter='\t', skiprows=2)
  tester = Tester(theta, mean, stddev)
  print 'Loaded mean: %s' % mean
  print 'Loaded stddev: %s' % stddev
  print 'Loaded theta: %s' % theta
  data = numpy.loadtxt(args.test, delimiter=',', skiprows=1)
  y = data[:,5]
  x = data[:,[2,3,4]]
  pred = tester.Predict(x)
  counts = {
    'TP': 0,
    'TN': 0,
    'FP': 0,
    'FN': 0,
  }
  for i, p in enumerate(pred):
    if p == 1 and y[i] == 1:
      counts['TP'] += 1
    elif p == 1 and y[i] == 0:
      counts['FP'] += 1
    elif p == 0 and y[i] == 1:
      counts['FN'] += 1
    elif p == 0 and y[i] == 0:
      counts['TN'] += 1
  print counts
  print "Outputting counts to %s" % args.results
  with open(args.results, 'w') as f:
    for key, count in counts.iteritems():
      f.write("%s,%s\n" % (key, count))
      print '%s: %s' % (key, count)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--train',   default=None, type=str)
  parser.add_argument('--test',    default=None, type=str)
  parser.add_argument('--theta',   default=None, type=str)
  parser.add_argument('--results', default=None, type=str)
  parser.add_argument('--thresh',  default=0.0000005, type=float)
  parser.add_argument('--clear',   action='store_true')
  parser.add_argument('--alpha',   default=0.0005, type=float, help='Learning rate')
  parser.add_argument('--lam',     default=0.1, type=float, help='Theta penalty')
  args = parser.parse_args()

  if args.theta is None:
    parser.exit(1, 'Theta file must be specified for both train and test')

  if args.train is not None:
    Train(args)

  if args.test is not None:
    Test(args)
