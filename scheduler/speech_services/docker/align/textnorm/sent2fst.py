#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is a script meant to take an input sentence (text) and
   generate an utterance with all possible parses/expansions.

   The idea is to generate an FST from this representation which can
   be aligned using an acoustic model to resolve the actual expansion.

   The idea implemented here is simple, relying on:

    - Applying a list of "greedy named entity (NE) acceptors" on the
      input string to find possible TOKENISATIONS.

    - Applying an "eager natural language (NL) generator" for each
      class of detected NE for each tokenisation to find possible word
      sequences.

    Possible TODO:
      - Revise re expressions to use Unicode-aware classes
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import re
import unicodedata

import pywrapfst as wfst

import sys
debug = sys.stderr #open("/dev/null", "wb")

try:
    lang = sys.argv[1]
except IndexError:
    lang = "engZA"
exec("from {}_tokens import TOKEN_MATCHERS, TOKEN_EXPANDERS, PUNCT_TRANSTABLE".format(lang))

##############################
def standardise_text(text, punct_transtable=PUNCT_TRANSTABLE):
    """Various simple tests and transformations to ensure we are working
       with "predictable" unicode...
    """
    assert type(text) is unicode
    #replace newlines
    text = text.replace("\n", " ")
    #whitespace chunks to a single space (regex "\s+" doesn't capture all whitespace)
    text = " ".join(text.split())
    #remove control chars:
    text = "".join(c for c in text if unicodedata.category(c)[0] != "C")
    #decompose unicode (with compatibility transform -- normalises ligatures and separates diacritics):
    text = unicodedata.normalize("NFKC", text)
    #normalise some pesky punctuation characters
    if punct_transtable:
        text = text.translate(punct_transtable)
    print(text.encode("utf-8"), file=debug)
    return text

def get_tokens(text, tokmats=TOKEN_MATCHERS):
    tokens = []
    for toktype, patts in tokmats.items():
        for patt in patts:
            pattre = re.compile(patt, flags=re.UNICODE)
            tokens.extend([{"type": toktype,
                            "string": tok.group(0),
                            "match": tok,
                            "start": str(tok.start()),
                            "end": str(tok.end())} for tok in pattre.finditer(text)])
    tokens.sort(key=lambda x: int(x["start"]))
    return tokens

def get_words(tokens, tokexps=TOKEN_EXPANDERS):
    words = []
    for token in tokens:
        if token["type"] in tokexps:
            expansions = tokexps[token["type"]](token["match"])
            for i, expansion in enumerate(expansions):
                for j, word in enumerate(expansion):
                    if j == 0:
                        start = token["start"]
                    else:
                        start = "_".join([token["start"],
                                          token["type"],
                                          str(token["match"]).split()[-1][:-1],
                                          str(i), str(j)])
                    if j == len(expansion) - 1:
                        end = token["end"]
                    else:
                        end = "_".join([token["start"],
                                        token["type"],
                                        str(token["match"]).split()[-1][:-1],
                                        str(i), str(j+1)])
                    words.append({"type": token["type"],
                                  "string": word,
                                  "match": token["match"],
                                  "start": start,
                                  "end": end})
    return words

def symbol(item):
    return item["string"] + "<" + item["type"] + ">" + "<" + ",".join(map(str, [item["match"].start(), item["match"].end()])) + ">"

def get_fst(items):
    #determine states and construct symtable:
    idxs = set()
    symtablel = set()
    for item in items:
        idxs.add(item["start"])
        idxs.add(item["end"])
        symtablel.add(symbol(item))
    symtablel = ["_"] + sorted(symtablel)
    symtable = dict([(s, i) for i, s in enumerate(symtablel)])
    #build fst
    stringidxs = sorted([idx for idx in idxs if len(idx.split("_")) == 1], key=lambda x: int(x.split("_")[0]))
    wordidxs = sorted([idx for idx in idxs if len(idx.split("_")) > 1], key=lambda x: int(x.split("_")[0]))
    idxstatemap = dict([(k, v) for k, v in zip(stringidxs + wordidxs, range(len(stringidxs) + len(wordidxs)))])
    fst = wfst.Fst()
    for i in stringidxs + wordidxs:
        fst.add_state()
    fst.set_start(0)
    fst.set_final(len(stringidxs)-1, wfst.Weight.One(fst.weight_type()))
    for i, item in enumerate(items):
       fst.add_arc(idxstatemap[item["start"]],
                   wfst.Arc(symtable[symbol(item)],
                            symtable[symbol(item)],
                            wfst.Weight.One(fst.weight_type()),
                            idxstatemap[item["end"]]))
    #add symbol table to fst
    fstsymtable = wfst.SymbolTable(b"default")
    for sym, idx in symtable.iteritems():
        fstsymtable.add_symbol(sym.encode("utf-8"), idx)
    fst.set_output_symbols(fstsymtable)
    #remove dead paths:
    # openfst.Connect(fst)
    return fst


##############################
if __name__ == "__main__":
    import codecs

    text = unicode(sys.stdin.read(), encoding="utf-8")
    text = standardise_text(text)
    print(text.encode("utf-8"), file=debug)
    print(file=debug)
    tokens = get_tokens(text)
    print("TOKENS:", file=debug)
    for tok in tokens:
        print("\t", tok, file=debug)
    words = get_words(tokens)
    fst = get_fst(words)
    fst.write(b"")#b"debug.fst")
