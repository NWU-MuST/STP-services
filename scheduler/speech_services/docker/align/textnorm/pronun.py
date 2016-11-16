#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Lookup and G2P to create pronunciation dictionary
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import sys
import codecs
try:
    import cPickle as pickle
except ImportError:
    import pickle
    
from sequitur import Translator


if __name__ == "__main__":
    chardictfn = sys.argv[1]
    g2pmodelfn = sys.argv[2]

    with codecs.open(chardictfn, encoding="utf-8") as infh:
        chardict = dict([(line.split()[0], line.split()[1:]) for line in infh if line.strip() != ""])
    with open(g2pmodelfn) as infh:
        g2pmodel = pickle.load(infh)
    translator = Translator(g2pmodel)
    
    for line in sys.stdin:
        line = unicode(line, encoding="utf-8").strip()
        word = line.split("<")[0]
        try:
            pronun = chardict[word]
        except KeyError:
            pronun = translator(word)
        print(" ".join([line, " ".join(pronun)]))
