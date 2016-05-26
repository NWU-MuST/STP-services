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
    db_curs.execute("CREATE TABLE services ( name VARCHAR(32) PRIMARY KEY, command VARCHAR (64) )")
    db_curs.executemany("INSERT INTO services (name, command) VALUES(?,?)",
     [("diarize", "diarize_builder.sh"), ("asr","asr_builder.sh"), ("align","align_builder.sh")])

    db_curs.execute("CREATE TABLE require ( name VARCHAR(32) PRIMARY KEY, audio VARCHAR(1), text VARCHAR(1) )")
    require = [("diarize", "Y", "N"), ("asr", "Y", "N"), ("align", "Y", "Y")]
    db_curs.executemany("INSERT INTO require(name, audio, text) VALUES(?,?,?)", require)

    db_curs.execute("CREATE TABLE diarize ( name VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO diarize(name) VALUES(?)", ("default",))

    db_curs.execute("CREATE TABLE asr ( name VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO asr(name) VALUES(?)", ("en-ZA-Parl",))

    db_curs.execute("CREATE TABLE align ( name VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO align(name) VALUES(?)", ("en-ZA-Parl",))

    db_conn.commit()
