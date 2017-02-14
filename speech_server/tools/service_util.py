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
    parser.add_argument("task", metavar="task", type=str, help="Task to perform: ADD, DEL, LS, SUBADD")
    args = parser.parse_args()
    outfn = args.outfn
    task = args.task.upper()

    if task == "ADD":
        # Collect details
        service_name = input("Enter service name: ")
        service_script = input("Enter service script name: ")
        text_require = input("Does it require text input (Y/N)? ")
        if text_require.upper() not in ["Y", "N"]:
            raise RuntimeError("Answer should Y or N")

        audio_require = input("Does it require audio input (Y/N)? ")
        if audio_require.upper() not in ["Y", "N"]:
            raise RuntimeError("Answer should Y or N")
        subsystem = input("Enter subsystem name: ")

        try:
            db_conn = sqlite.connect(outfn)
            db_curs = db_conn.cursor()
            db_curs.execute("INSERT INTO services (name, command) VALUES(?,?)", (service_name, service_script))
            db_curs.execute("INSERT INTO require(name, audio, text) VALUES(?,?,?)", (service_name, audio_require.upper(), text_require.upper()))
            db_curs.execute("CREATE TABLE {} ( subsystem VARCHAR(32) PRIMARY KEY )".format(service_name))
            db_curs.execute("INSERT INTO {}(subsystem) VALUES(?)".format(service_name), (subsystem,))
            db_conn.commit()
        except Exception as e:
            print(str(e))            

    elif task == "SUBADD":
        service_name = input("Enter service name: ")
        subsystem = input("Enter subsystem name: ")

        try:
            db_conn = sqlite.connect(outfn)
            db_curs = db_conn.cursor()
            db_curs.execute("INSERT INTO {}(subsystem) VALUES(?)".format(service_name), (subsystem,))
            db_conn.commit()
        except Exception as e:
            print(str(e))            

    elif task == "DEL":
        service_name = input("Enter service name: ")
        try:
            db_conn = sqlite.connect(outfn)
            db_curs = db_conn.cursor()
            db_curs.execute("DELETE FROM services WHERE name=?", (service_name,))
            db_curs.execute("DELETE FROM require WHERE name=?", (service_name,))
            db_curs.execute("DROP TABLE {}".format(service_name))
            db_conn.commit()
        except Exception as e:
            print(str(e))            

    elif task == "LS":
        db_conn = sqlite.connect(outfn)
        db_curs = db_conn.cursor()
        db_curs.execute("SELECT * FROM services")
        services = db_curs.fetchall()
        for service_name, service_script in services:
            print("Service Name: ", service_name)
            print("Service Script: ", service_script)
            db_curs.execute("SELECT audio, text FROM require WHERE name=?", (service_name,))
            audio, text = db_curs.fetchone()
            print("Require audio: ", audio)
            print("Require text: ", text)
            db_curs.execute("SELECT * FROM {}".format(service_name))
            subs = db_curs.fetchall()
            print("Subsystem: {}".format(subs))
            print("")

    else:
        print("UNKNOWN TASK: {}".format(task))

