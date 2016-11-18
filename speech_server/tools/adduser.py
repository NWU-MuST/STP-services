#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple script to make empty authentication database ("auth.db") for
   the application server.
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import os
import argparse
try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

import bcrypt #Ubuntu/Debian: apt-get install python-bcrypt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("infn", metavar="INFN", type=str, help="Input DB filename.")
    parser.add_argument("username", metavar="USERNAME", type=str, help="New user name")
    parser.add_argument("password", metavar="PASSWORD", type=str, help="Password for new user")
    args = parser.parse_args()

    infn = args.infn
    username = args.username
    password = args.password

    salt = bcrypt.gensalt(prefix=b"2a")
    pwhash = bcrypt.hashpw(password, salt)

    db_conn = sqlite.connect(infn)
    db_curs = db_conn.cursor()
    db_curs.execute("INSERT INTO users ( username, pwhash, salt, name, surname, email, tmppwhash ) VALUES (?,?,?,?,?,?,?)", (username, pwhash, salt, "", "", "", ""))
    db_conn.commit()
