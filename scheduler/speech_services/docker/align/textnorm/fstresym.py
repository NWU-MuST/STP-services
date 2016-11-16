#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import sys

if __name__ == "__main__":
    symtabfn = sys.argv[1]
    with open(symtabfn) as infh:
        symtab = dict([line.split() for line in infh if line.strip() != ""])
    
    for line in sys.stdin:
        linelist = line.split()
        if len(linelist) > 3:
            linelist[2] = linelist[3] = symtab[linelist[3]]
            print("\t".join(linelist))
        else:
            print(line)
