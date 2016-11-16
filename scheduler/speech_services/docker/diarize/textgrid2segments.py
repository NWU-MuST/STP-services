#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import os

DUR=0.800
MINSPDUR=5.0

# Parse Praat V/UV TextGrid data
# to determine split points
def segmentvuv(data, dur):
    splpt = []
    end = 0.0
    for line in data:
        if ' ' in line:
            toks = line.strip().split()
            if toks[0] == "xmax":
                end = float(toks[-1])
                continue

    xmin = 0
    xmax = 0
    for line in data:
        if ' ' in line:
            toks = line.strip().split()
            if toks[0] == "xmin":
                xmin = float(toks[-1])
                continue
            if toks[0] == "xmax":
                xmax = float(toks[-1])
                continue
            if toks[0] == "text":
                if toks[-1] == '"U"':
                    if (xmax - xmin) > dur:
                        mid = (xmax + xmin) / 2.0
                        splpt.append(mid)
                continue
    return splpt

if __name__ == "__main__":

    if len(sys.argv) != 6:
        print "usage: {} in_textgrid out_segments out_utt2spk out_wavscp out_text".format(sys.argv[0])
        sys.exit(1)

    # Load data from Praat TextGrid
    with open(sys.argv[1], 'r') as f:
        data = f.readlines()

    # Find split points - try 3 times if none found
    retry = 3
    dur = DUR
    for n in range(retry):
        splpt = segmentvuv(data, dur)
        if len(splpt) != 0:
            break
        else:
            dur = dur - 0.1

    if len(splpt) == 0:
        print "No split options found in audio file"
        sys.exit(2)

    # Filter out segments that are too short
    splpt.insert(0, 0.0)
    splpt.append((end))
    for n in range(len(splpt)-1):
        if splpt[n+1] - splpt[n] < MINSPDUR:
            splpt[n+1] = splpt[n]
    splpt = sorted(list(set(splpt)))

    # Write out KALDI data files - segments, uttspk, wav.scp, text
    tag = os.path.basename(sys.argv[1]).split('.')[0]
    with open(sys.argv[2], 'w') as f, open(sys.argv[3], 'w') as fu, open(sys.argv[4], 'w') as fw, open(sys.argv[5], 'w') as ft:
        for n in range(len(splpt)-1):
            ss = splpt[n]
            ee = splpt[n+1]

            sss = '%.2f' % ss
            eee = '%.2f' % ee

            ssss = str(int(ss * 100.0)).zfill(6)
            eeee = str(int(ee * 100.0)).zfill(6)

            f.write("{}_{}_{} {} {} {}\n".format(tag, ssss, eeee, tag, sss, eee))
            fu.write("{}_{}_{} {}\n".format(tag, ssss, eeee, tag))
            ft.write("{}_{}_{}\n".format(tag, ssss, eeee))

        fw.write("{} WAVE\n".format(tag, ))

