#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Create initial project table
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Neil Kleynhans"
__email__ = "ntkleynhans@gmail.com"

import os
import argparse
try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("outfn", metavar="OUTFN", type=str, help="Output DB filename.")
    args = parser.parse_args()
    outfn = args.outfn
    
    db_conn = sqlite.connect(outfn)
    db_curs = db_conn.cursor()
    db_curs.execute("CREATE TABLE tasks ( taskid VARCHAR(36) PRIMARY KEY, username VARCHAR(20), audiofile VARCHAR(128), year INTEGER, creation REAL )")
    db_conn.commit()

