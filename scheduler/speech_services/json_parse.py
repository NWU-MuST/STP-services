#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import json
import codecs

if len(sys.argv) != 3:
    print("{}: json_file variable".format(sys.argv[0]))
    sys.exit(1)

with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
    data = json.load(f)

if sys.argv[2] in data:
    print("{}".format(data[sys.argv[2]]))
else:
    print("")
    sys.exit(1)

