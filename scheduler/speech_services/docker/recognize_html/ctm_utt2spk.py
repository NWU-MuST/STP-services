#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import codecs

if len(sys.argv) != 3:
    print("usage: {} in_ctm out_utt2spk".format(sys.argv[0]))
    sys.exit(1)

utt2spk = []
with codecs.open(sys.argv[1], "r", "utf-8") as f:
    data = f.readlines()
    for line in data:
        toks = line.strip().split()
        segment = toks[0]
        items = segment.split("_")
        utt2spk.append("{} {}".format(segment, items[0]))

with codecs.open(sys.argv[2], "w", "utf-8") as f:
    f.write("\n".join(utt2spk))
    f.write("\n")

