#!/usr/bin/python

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import argparse
import codecs
import copy

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--timechunk", help="Ideal chunk size in seconds", type=float, default=600)
parser.add_argument("segin", help="Segment input file")
parser.add_argument("segout", help="Segment output file")
args = parser.parse_args()

with codecs.open(args.segin, "r", "utf-8") as f:
    data = f.readlines()

    order = []
    segs = {}
    items = []
    seg_ct = 0
    now_spk = ""
    for line in data:
        spk, start, end = line.strip().split()
        if now_spk != spk:
            if now_spk != "":
                order.append(seg_ct)
                segs[seg_ct] = copy.deepcopy(items)
                seg_ct += 1
                items = []
            now_spk = spk
        items.append((spk, start, end))
    if len(items) > 0:
        order.append(seg_ct)
        segs[seg_ct] = items

out_segs = []
for seg_ct in order:
    seg_cur = segs[seg_ct]
    spk, start, end = seg_cur[0]
    spk, tmp, end = seg_cur[-1]

    dur = float(end) - float(start)
    if dur > args.timechunk:
        n = 1
        while (n*args.timechunk) < dur:
            n += 1
        inc = dur / float(n)
        #print(n, inc)

        subs = [start]
        for n in range(1, n):
            mid = float(start) + n*inc
            #print(mid)
            pos = 0
            for m, item in enumerate(seg_cur):
                spk, st, ed = item
                if float(st) > mid:
                    pos = m
                    break
            subs.append(seg_cur[m][1])

        if subs[-1] != end:
            subs.append(end)
        #print(subs)
        for ndx in range(len(subs)-1):
            out_segs.append((spk, subs[ndx], subs[ndx+1]))
    else:
        out_segs.append((spk, start, end))

with codecs.open(args.segout, "w", "utf-8") as f:
    for spk, start, end in out_segs:
        f.write("{} {} {}\n".format(spk, start, end))

