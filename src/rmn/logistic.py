#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import numpy as np
from numpy import linalg

Y = [-1,1]

class Logistic(object):
  def __init__(self, gamma, step):
    self.__gamma = gamma
    self.__step = step

  def Weights(self, D):
    label, x = D[0]
    w = np.array([1] * len(x))
    return w / linalg.norm(w)

  def Gradient(self, w, D):
    total = np.array([0] * len(w))
    for y, x in D:
      diff = x - self.EPw(x, w)
      total += diff
    return total - self.Prior(w)

  def Descent(self, D, w):
    gradient = self.Gradient(w, D)
    change = gradient * self.__step
    delta = linalg.norm(change)
    w += change
    return w, delta

  def EPw(self, x, w):
    total = np.array([0] * len(w))
    for y in Y:
      total += x * self.Pw(y, x, w)
    return total

  def Pw(self, y, x, w):
    prob = 1.0 / self.Z(w, x)
    for i in range(len(w)):
      potential = np.exp(y * w[i] * x[i])
      prob *= potential
    return prob
    #return prob * np.exp(y * np.dot(w, x))

  def Z(self, w, x):
    total = 0.0
    for y in Y:
      prod = 1.0
      for i in range(len(w)):
        potential = np.exp(y * w[i] * x[i])
        prod *= potential
        #prod *= np.exp(y * np.dot(w, x))
      total += prod
    return total

  def Sigmoid(self, x):
    den = 1.0 + np.exp(-1.0 * x)
    d = 1.0 / den
    return d

  def Prior(self, w):
    return w / (self.__gamma * self.__gamma)

