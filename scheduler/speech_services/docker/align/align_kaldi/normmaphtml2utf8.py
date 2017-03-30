#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Input HTML file and output UTF-8 text file and character index
   mappings...
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import sys, os
import codecs
import re
import unicodedata
import htmlentitydefs

WHITESPACE_TAGS = ["br", "p"]
WHITESPACE_ENTITIES = ["&"+entitydef+";" for entitydef, codepoint in htmlentitydefs.name2codepoint.iteritems() if unicodedata.category(unichr(codepoint))[0] == "Z"]
def basic_preprocessing(text):
    assert type(text) is unicode
    #replace newlines
    text = text.replace("\n", " ")
    #whitespace chunks to a single space:
    text = " ".join(text.split())
    #text = re.sub("\s+", " ", text) #DEMIT: This does not work for all Unicode spaces (e.g. non-breaking space \xa0)
    #remove remaining control chars:
    text = "".join(c for c in text if unicodedata.category(c)[0] != "C")
    #decompose unicode (with compatibility transform -- normalises ligatures and combines diacritics where possible):
    text = unicodedata.normalize("NFKC", text)
    #add whitespace around "whitespace tags" (all tags will be removed)
    text = re.sub("\s*((:?</?\s*?({})[^<>]*?>\s*)+)\s*".format("|".join(WHITESPACE_TAGS)), lambda x: x.group(0).replace("> ", ">").replace(" <", "<") + " ", text)
    #remove whitespace around "whitespace entities" (it will be inserted by mapping)
    text = re.sub("\s*({})\s*".format("|".join(WHITESPACE_ENTITIES)), "\\1", text)
    #remove whitespace at start of string before real text (DEMIT: this might be redundant...)
    text = re.sub("^((<[^<>]*?>\s*)+)\s+", lambda x: x.group(0).replace("> ", ">"), text)
    return text.strip()

def unichr_alternative(codepoint, altchar=["", " "], exceptcats=["C", "Z"]):
    c = unichr(codepoint)
    cat = unicodedata.category(c)[0]
    if cat not in exceptcats:
        return c
    else:
        return altchar[exceptcats.index(cat)]

IGNORESPAN_TAGS = ["demitcomment", "time"]
FIND_RE = re.compile("|".join(["<.*?>"] + ["&"+entitydef+";" for entitydef in htmlentitydefs.name2codepoint.keys()]))
IGNORESPAN_RE = re.compile("<\s*" + "|".join(IGNORESPAN_TAGS))
REPLACE_RE = re.compile("|".join(["&"+entitydef+";" for entitydef in htmlentitydefs.name2codepoint.keys()]))
REPLACE_MAP = dict([("&"+k+";", unichr_alternative(v)) for k, v in htmlentitydefs.name2codepoint.iteritems()])
def normmaptext(text):
    """This iterates through matches of HTML tags (and entities) and
       removes replaces them as needed and keeps a mapping (index)
       between location in the original and resulting strings.
    """
    def remove(ref, start, length):
        shift = tagmatch.start() - ref[0]
        inmap = (ref[0] + shift, ref[1] + shift)
        outmap = (ref[0] + shift + length, ref[1] + shift)
        if shift:                 #increment both
            for i, j in zip(range(ref[0], ref[0]+shift), range(ref[1], ref[1] + shift)):
                cmap.append((i+1, j+1))
                normtext.append(text[i])
        for i in range(length):   #just increment ORIG
            cmap.append((cmap[-1][0] + 1, cmap[-1][1]))

    def insert(ref, token):
        for c in token:
            cmap.append((ref[0], cmap[-1][1] + 1))
            normtext.append(c)
    
    #(orig, targ) where orig idx is of first char and targ insert before idx
    normtext = []
    cmap = [(0, 0)]
    prevrem = 0
    iterator = FIND_RE.finditer(text)
    for tagmatch in iterator:
        tag = tagmatch.group(0)
        #print(tag)
        if IGNORESPAN_RE.match(tag):
            #next -> find end tag:
            endtag_re = re.compile("</\s*{}".format(tag[1:].strip()))
            for tagmatch2 in iterator:
                tag2 = tagmatch2.group(0)
                if endtag_re.match(tag2):
                    break
            #print("\t", tag2)
            remove(ref=cmap[-1], start=tagmatch.start(), length=tagmatch2.end() - tagmatch.start())
        elif REPLACE_RE.match(tag):
            remove(ref=cmap[-1], start=tagmatch.start(), length=len(tag))
            insert(ref=cmap[-1], token=REPLACE_MAP[tag])
        else:
            remove(ref=cmap[-1], start=tagmatch.start(), length=len(tag))
    #print()
    return "".join(normtext), cmap
    
def preproc_normmap(text):
    text = basic_preprocessing(text)
    normtext, cmap = normmaptext(text)
    return text, normtext, cmap

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('infn', metavar='INFN', type=str, help="input HTML file")
    parser.add_argument('outtxtfn', metavar='OUTTXTFN', type=str, help="output text file (UTF-8)")
    parser.add_argument('outmapfn', metavar='OUTMAPFN', type=str, help="output map file (two tab-seperated columns of unicode character indices)")
    args = parser.parse_args()

    with codecs.open(args.infn, encoding="utf-8") as infh:
        text = infh.read()
    text = basic_preprocessing(text)
    # print("\n", text)
    normtext, cmap = normmaptext(text)
    # print(cmap)
    # print("\n", normtext)
    # print("\nTEST:")
    # print("\t", text[cmap[35][0]:cmap[35][0]+5])
    # print("\t", normtext[cmap[35][1]:cmap[35][1]+5])

    with codecs.open(args.outtxtfn, "w", encoding="utf-8") as outfh:
        outfh.write(normtext)
    with open(args.outmapfn, "w") as outfh:
        outfh.write("\n".join((["\t".join(map(str, e)) for e in cmap])) + "\n")
