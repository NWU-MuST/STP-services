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

import pywrapfst as wfst

#All weights in this script represented as probs and mapped finally
ALT_WEIGHT = 0.02

def weight(w):
    """Map weight from prob to whatever is necessary...
    """
    return -math.log(w)

def is_final(fst, state):
    return fst.final(state) != wfst.Weight.Zero(fst.weight_type())


if __name__ == "__main__":
    symtabfn = sys.argv[1]
    with open(symtabfn) as infh: #we don't even bother to decode this to Unicode
        stoi = dict([(line.split()[0], int(line.split()[1])) for line in infh if line.strip() != b""])
    itos = dict([(v, k) for k, v in stoi.iteritems()])

    fst = wfst.Fst.read(b"")
    # #Add sent-start/end symbols
    startstate = fst.start()
    # #DEMITASSE: need to update for potentially multiple final states:
    finalstate = [i for i in range(fst.num_states()) if is_final(fst, i)][0]
    # newst = fst.add_state()
    # fst.set_start(newst)
    # fst.add_arc(newst, wfst.Arc(stoi["<s>"], stoi["<s>"], wfst.Weight.One(fst.weight_type()), startstate))
    # startstate = newst
    # newst = fst.add_state()
    # fst.set_final(newst, wfst.Weight.Zero(fst.weight_type()))
    # fst.set_final(finalstate, wfst.Weight.One(fst.weight_type())) #set "not final"
    # fst.add_arc(finalstate, wfst.Arc(stoi["</s>"], stoi["</s>"], wfst.Weight.One(fst.weight_type()), newst))
    # finalstate = newst
    #Add skip arcs, <unk> paths, <unk>-skips and reweight other arcs uniformly to sum to 1.0
    for i in range(fst.num_states()):
        arcs = [(arc.nextstate, arc.ilabel, arc.olabel) for arc in fst.arcs(i)]
        if arcs:
            w = (1.0 - ALT_WEIGHT) / len(arcs)
            nextstates = set([nextstate for nextstate, ilabel, olabel in arcs])
            aw = ALT_WEIGHT / (len(arcs) + len(nextstates)*2)
            fst.delete_arcs(i)
            for nextstate, ilabel, olabel in arcs:
                if itos[olabel].startswith(b"#"): #don't add unks for disambig "words"
                    fst.add_arc(i, wfst.Arc(ilabel, olabel, wfst.Weight.One(fst.weight_type()), nextstate))
                else:
                    newst = fst.add_state()
                    fst.add_arc(i, wfst.Arc(ilabel, olabel, weight(w), nextstate))
                    fst.add_arc(i, wfst.Arc(ilabel, olabel, weight(aw), newst))
                    fst.add_arc(newst, wfst.Arc(stoi[b"<unk>"], stoi[b"<unk>"], wfst.Weight.One(fst.weight_type()), nextstate))
            for nextstate in nextstates:
                if not itos[olabel].startswith(b"#"):
                    fst.add_arc(i, wfst.Arc(stoi[b"#0"], stoi[b"<eps>"], weight(aw), nextstate))
                    fst.add_arc(i, wfst.Arc(stoi[b"<unk>"], stoi[b"<unk>"], weight(aw), nextstate))
    fst.topsort()
    fst.write(b"")
