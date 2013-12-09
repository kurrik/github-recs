#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Arne Roomann-Kurrik <kurrik@gmail.com>'

import numpy as np
from numpy import linalg

Y = [0,1]

class RMN(object):
  def FCxyr(self, C, y=None):
    total = C.Features.ZeroF()
    for c in C.Cliques():
      total += C.Features.FCxy(c, y)
    return total

  def Fxyr(self, CT, y=None):
    return [self.FCxyr(C, y) for C in CT.Templates()]

  def W(self, CT):
    return [C.Features.StartW() for C in CT.Templates()]

  def PotentialsC(self, C, c, wc, y=None):
    f = C.Features.FCxy(c, y)
    return np.exp(np.dot(f, wc))

  def Zxr(self, CT, w):
    total = 0.0
    for y in Y:
      prod = 1.0
      for i, C in enumerate(CT.Templates()):
        for c in C.Cliques():
          prod *= self.PotentialsC(C, c, w[i], y)
      total += prod
    return total

  def Pw(self, CT, w, y=None):
    prod = 1.0 / self.Zxr(CT, w)
    for i, C in enumerate(CT.Templates()):
      for c in C.Cliques():
        prod *= self.PotentialsC(C, c, w[i], y)
    return prod

  def EPwYxr(self, CT, w):
    total = [C.Features.ZeroF() for C in CT.Templates()]
    for y in Y:
      f = self.Fxyr(CT, y)
      pw = self.Pw(CT, w, y)
      total += f * pw
    return total

  def Prior(self, w, gamma):
    return [wc / (gamma * gamma) for wc in w]

  def Gradient(self, CT, w, gamma):
    f = self.Fxyr(CT, None)
    ew = self.EPwYxr(CT, w)
    pr = self.Prior(w, gamma)
    return [f[i] - ew[i] - pr[i] for i in range(len(f))]

  def Descent(self, CT, w, step, gamma):
    gradient = self.Gradient(CT, w, gamma)
    change = [gradient[i] * step for i in range(len(gradient))]
    delta = sum([linalg.norm(x) for x in change])
    w = [w[i] + change[i] for i in range(len(gradient))]
    return w, delta
