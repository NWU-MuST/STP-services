#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Script to create JSON file from convenient tab-separated txt format
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import sys
import codecs
import json
from collections import defaultdict

SEP = "\t"

if __name__ == "__main__":
    d = defaultdict(list)
    for line in sys.stdin:
        line = unicode(line, encoding="utf-8")
        fields = line.strip().split(SEP)
        d[fields[0]].extend(fields[1:])

    print(json.dumps(d, indent=4, sort_keys=True).encode("utf-8"))
