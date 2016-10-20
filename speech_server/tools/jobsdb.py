#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Create initial jobs table
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
    db_curs.execute("CREATE TABLE jobs ( jobid VARCHAR(36) PRIMARY KEY, username VARCHAR(20), ticket VARCHAR(128), status VARCHAR(8), sgeid VARCHAR(32), creation REAL, errstatus VARCHAR(128) )")
    db_curs.execute("CREATE TABLE jobCtrl ( key VARCHAR(32), value VARCHAR(32) )")
    db_curs.execute("INSERT INTO jobCtrl (key, value) VALUES (?,?)", ( "lock" , "N" ))
    db_conn.commit()

