#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import math
import sys
debug = sys.stderr #open("/dev/null", "wb")

import openfst

#All weights in this script represented as probs and mapped finally
ALT_WEIGHT = 0.02

def weight(w):
    """Map weight from prob to whatever is necessary...
    """
    return -math.log(w)
    
if __name__ == "__main__":
    symtabfn = sys.argv[1]
    with open(symtabfn) as infh: #we don't even bother to decode this to Unicode
        symtab = dict([(line.split()[0], int(line.split()[1])) for line in infh if line.strip() != ""])
    revsymtab = dict([(v, k) for k, v in symtab.iteritems()])

    fst = openfst.Read(b"")
    # #Add sent-start/end symbols
    startstate = fst.Start()
    # #DEMITASSE: need to update for potentially multiple final states:
    finalstate = [i for i in range(fst.NumStates()) if fst.IsFinal(i)][0]
    # newst = fst.AddState()
    # fst.SetStart(newst)
    # fst.AddArc(newst, symtab["<s>"], symtab["<s>"], weight(1.0), startstate)
    # startstate = newst
    # newst = fst.AddState()
    # fst.SetFinal(newst, 0.0)
    # fst.SetNotFinal(finalstate)
    # fst.AddArc(finalstate, symtab["</s>"], symtab["</s>"], weight(1.0), newst)
    # finalstate = newst
    #Add skip arcs, <unk> paths, <unk>-skips and reweight other arcs uniformly to sum to 1.0
    for i in range(fst.NumStates()):
        arcs = [(arc.nextstate, arc.ilabel, arc.olabel) for arc in fst.iterarcs(i)]
        if arcs:
            w = (1.0 - ALT_WEIGHT) / len(arcs)
            nextstates = set([nextstate for nextstate, ilabel, olabel in arcs])
            aw = ALT_WEIGHT / (len(arcs) + len(nextstates)*2)
            fst.DeleteArcs(i)
            for nextstate, ilabel, olabel in arcs:
                if revsymtab[olabel].startswith("#"): #don't add unks for disambig "words"
                    fst.AddArc(i, ilabel, olabel, weight(1.0), nextstate)
                else:
                    newst = fst.AddState()
                    fst.AddArc(i, ilabel, olabel, weight(w), nextstate)
                    fst.AddArc(i, ilabel, olabel, weight(aw), newst)
                    fst.AddArc(newst, symtab["<unk>"], symtab["<unk>"], weight(1.0), nextstate)
            for nextstate in nextstates:
                if not revsymtab[olabel].startswith("#"):
                    fst.AddArc(i, symtab["#0"], symtab["<eps>"], weight(aw), nextstate)
                    fst.AddArc(i, symtab["<unk>"], symtab["<unk>"], weight(aw), nextstate)

    openfst.TopSort(fst)
    fst.Write(b"")
