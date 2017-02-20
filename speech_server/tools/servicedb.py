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
    db_curs.execute("CREATE TABLE services ( name VARCHAR(32) PRIMARY KEY, command VARCHAR (128) )")
    db_curs.executemany("INSERT INTO services (name, command) VALUES(?,?)",
     [("diarize", "diarize.sh"), ("recognize","recognize.sh"), ("align","align.sh"),
     ("diarize_html", "diarize_html.sh"), ("recognize_html","recognize_html.sh"), ("align_html","align_html.sh")])

    db_curs.execute("CREATE TABLE require ( name VARCHAR(32) PRIMARY KEY, audio VARCHAR(1), text VARCHAR(1) )")
    require = [("diarize", "Y", "N"), ("recognize", "Y", "N"), ("align", "Y", "Y"),
        ("diarize_html", "Y", "Y"), ("recognize_html", "Y", "Y"), ("align_html", "Y", "Y")]
    db_curs.executemany("INSERT INTO require(name, audio, text) VALUES(?,?,?)", require)

    db_curs.execute("CREATE TABLE diarize ( subsystem VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO diarize(subsystem) VALUES(?)", ("default",))

    db_curs.execute("CREATE TABLE recognize ( subsystem VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO recognize(subsystem) VALUES(?)", ("en_ZA_16000",))

    db_curs.execute("CREATE TABLE align ( subsystem VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO align(subsystem) VALUES(?)", ("en_ZA_16000",))

    db_curs.execute("CREATE TABLE diarize_html ( subsystem VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO diarize_html(subsystem) VALUES(?)", ("default",))

    db_curs.execute("CREATE TABLE recognize_html ( subsystem VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO recognize_html(subsystem) VALUES(?)", ("en_ZA_16000",))

    db_curs.execute("CREATE TABLE align_html ( subsystem VARCHAR(32) PRIMARY KEY )")
    db_curs.execute("INSERT INTO align_html(subsystem) VALUES(?)", ("en_ZA_16000",))

    db_conn.commit()

