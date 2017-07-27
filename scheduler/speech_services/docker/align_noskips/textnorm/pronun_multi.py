#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Lookup and G2P to create pronunciation dictionary
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import os
import sys
import codecs
try:
    import cPickle as pickle
except ImportError:
    import pickle
    
from sequitur import Translator

UNK_WORD = "<unk>" #DEMIT: centralize this at some stage

def try_map(s, m):
    try:
        return m[s]
    except:
        return s

if __name__ == "__main__":
    chardictfn = sys.argv[1]
    datadir = sys.argv[2]
    altlangtags = sys.argv[3].split(",")

    with codecs.open(chardictfn, encoding="utf-8") as infh:
        chardict = dict([(line.split()[0], line.split()[1:]) for line in infh if line.strip() != ""])
    translators = {}
    phonemaps = {}
    with open(os.path.join(datadir, "g2p.model.pickle")) as infh:
        translators[""] = Translator(pickle.load(infh))
    for altlangtag in altlangtags:
        with open(os.path.join(datadir, "g2p.model."+altlangtag+".pickle")) as infh:
            translators[altlangtag] = Translator(pickle.load(infh))
        with open(os.path.join(datadir, "g2p.phonemap."+altlangtag+".tsv")) as infh:
            fields = [line.strip().split("\t") for line in infh if line.strip()]
            phonemaps[altlangtag] = dict(fields)
                
    for line in sys.stdin:
        line = unicode(line, encoding="utf-8").strip()
        word = line.split("<")[0]
        try:
            pronun = chardict[word]
        except KeyError:
            try:
                pronun = None
                for altlangtag in altlangtags:
                    prefix = altlangtag+"_"
                    if word.startswith(prefix):
                        pronun = " ".join([try_map(e, phonemaps[altlangtag]) for e in translators[altlangtag](word[len(prefix):])]).split()
                        break
                if not pronun: #default lang
                    pronun = translators[""](word)
                if not pronun:
                    pronun = chardict[UNK_WORD]
            except BaseException as e:
                print("FAILED WORD:", word.encode("utf-8"), file=sys.stderr)
                pronun = chardict[UNK_WORD]                
                
        print(" ".join([line, " ".join(pronun)]).encode("utf-8"))
