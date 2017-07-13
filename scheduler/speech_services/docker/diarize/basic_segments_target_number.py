#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import argparse
import math

def frange(x, y, jump=1.0):
    '''Range for floats.'''
    i = 0.0
    x = float(x)  # Prevent yielding integers.
    x0 = x
    epsilon = jump / 2.0
    yield x  # yield always first value
    while x + epsilon < y:
        i += 1.0
        x = x0 + i * jump
        yield x

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--target", help="Number of segments", type=int, default=5)
parser.add_argument("txtg", help="TextGrid input file")
parser.add_argument("ctm", help="CTM output file")
args = parser.parse_args()

# Load textgrid file
with open(args.txtg, "r") as f:
    data = f.readlines()

# Parse textgrid for silence portions
xmin = 0
xmax = 0
text = 0
last = 0
duration = 0.1

items = []
for line in data:
    if "xmin" in line:
        toks = line.strip().split()
        xmin = float(toks[-1])
        continue
    if "xmax" in line:
        toks = line.strip().split()
        xmax = float(toks[-1])
        last = xmax
        continue
    if "text" in line:
        toks = line.strip().split()
        if toks[-1] == '"U"':
            if xmin != 0.0:
                if (xmax - xmin) > duration:
                    items.append((xmin, xmax))

# No data
if len(items) == 0:
    with open(args.ctm, 'w') as f:
        sxmin = "{}".format(int(100*0.0)).zfill(6)
        sxmax = "{}".format(int(100*last)).zfill(6)
        seg = "A_{}_{}".format(sxmin, sxmax)
        f.write("{} 1 {:.2f} {:.2f} <NO-DATA>\n".format(seg, 0.0, last))
    sys.exit(0)

# Split audio equally
seg_dur = float(last) / float(args.target)
pts = list(frange(0.0, last, seg_dur))
if int(last) != int(pts[-1]):
    pts.append(last)
print("{}".format(pts))
# shift times to nearest silence portion
shift = [0.0]
for ndx in range(1, len(pts)-1):
    eq_time = pts[ndx]
    best = 0.0
    for start, end in items:
        mid = (start + end)/2.0
        if math.fabs(eq_time-best) > math.fabs(eq_time-mid):
            best = mid
    shift.append(best)
shift.append(last)
print("{}".format(shift))
items = []
for ndx in range(len(shift)-1):
    items.append((shift[ndx], shift[ndx+1], "<NON-SILENCE>"))

# Convert segments to CTM format
with open(args.ctm, "w") as f:
    for xmin, xmax, text in items:
        sxmin = "{}".format(int(100*xmin)).zfill(6)
        sxmax = "{}".format(int(100*xmax)).zfill(6)
        seg = "A_{}_{}".format(sxmin, sxmax)
        f.write("{} 1 {:.2f} {:.2f} {}\n".format(seg, xmin, xmax-xmin, text))

