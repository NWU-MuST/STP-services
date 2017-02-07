#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import argparse
import datetime

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--threshold", help="Silence threshold duration", type=float, default=0.3)
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
            if xmax - xmin > args.threshold:
                if xmin != 0.0:
                 items.append((xmin, xmax, "<SILENCE>"))

# No data
if len(items) == 0:
    with open(args.ctm, 'w') as f:
        f.write(u'<p><span style="color: #FF0000;">Sorry could not automatically index this audio!<br>'
        'Please delete this and use the manual "Timestamp" insertion to break up the audio.<br>'
        'You can do this by finding silence portions and clicking on the "Timestamp" button</span></p>\n')
    sys.exit(0)

# See if beginning is marked
if items[0][0] != 0.0:
    items.insert(0, (0.0, items[0][0], "<NON-SILENCE>"))

# See if end is marked
if items[-1][-2] != last:
    items.append((items[-1][-2], last, "<NON-SILENCE>"))

# Insert missing portions
final_out = []
for n in range(len(items)-1):
    xn, xx, text = items[n]
    xn1, xx1, text = items[n+1]
    final_out.append(items[n])
    if xx != xn1:
        final_out.append((xx, xn1, "<NON-SILENCE>"))
final_out.append(items[-1])

# Convert segments to CTM format
have_written = False
with open(args.ctm, "w") as f:
    for xmin, xmax, text in final_out:
        if text == "<SILENCE>" and xmin != xmax:
            have_written = True
            sxmax = float("{:.2f}".format(xmax))
            f.write(u'<p><time type="mark" style="background-color: #AAAAAA;" datetime="{}">{}</time></p>\n\n'.format(xmax, str(datetime.timedelta(seconds=sxmax)).rstrip(u'0000')))
            f.write(u'<p>&nbsp;</p>\n\n')

if not have_written:
    with open(args.ctm, "a") as f:
        f.write(u'<p><span style="color: #FF0000;">Sorry could not automatically index this audio!<br>'
        'Please delete this and use the manual "Timestamp" insertion to break up the audio.<br>'
        'You can do this by finding silence portions and clicking on the "Timestamp" button</span></p>\n')

