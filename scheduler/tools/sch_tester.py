#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import os
import time
import logging
import logging.handlers
import argparse
import readline
import BaseHTTPServer
import threading
import codecs
import stat
import uuid
import datetime
import json

try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')


"""LOGGING SECTION"""
#The following ensures that we can override "funcName" when logging
# from wrapper functions, from:
# http://stackoverflow.com/questions/7003898/using-functools-wraps-with-a-logging-decorator
class CustomFormatter(logging.Formatter):
    """Custom formatter, overrides funcName with value of funcname if it
       exists
    """
    def format(self, record):
        if hasattr(record, 'funcname'):
            record.funcName = record.funcname
        return super(CustomFormatter, self).format(record)

LOGNAME = "SCHTEST"
LOGFNAME = "scheduler_testing.log"
LOGLEVEL = logging.DEBUG
try:
    fmt = "%(asctime)s [%(levelname)s] %(name)s in %(funcName)s(): %(message)s"
    LOG = logging.getLogger(LOGNAME)
    formatter = CustomFormatter(fmt)
    ofstream = logging.handlers.TimedRotatingFileHandler(LOGFNAME, when="D", interval=1, encoding="utf-8")
    ofstream.setFormatter(formatter)
    LOG.addHandler(ofstream)
    LOG.setLevel(LOGLEVEL)

    #If we want console output:
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    LOG.addHandler(console)
except Exception as e:
    print("FATAL ERROR: Could not create logging instance: {}".format(e), file=sys.stderr)
    sys.exit(1)


"""DEFAULT VARIABLES"""
DEF_SPEECH_DB = os.path.expanduser("~/stp/speech_jobs.db")
DEF_SERVICE_DB = os.path.expanduser("~/stp/speech_services.db")
DEF_SERVICE_DIR = os.path.abspath(os.path.expanduser("../speech_services/"))
DEF_STORAGE_DIR = os.path.abspath(os.path.expanduser("~/stp/jobs/"))

"""TESTING SCRIPTS"""
NORMAL_CODE = """#!/bin/bash\nTICKET=##INSTANCE_TICKET##\nSPEECH_SERVICES=##SPEECH_SERVICES##
RESULTFILE=`python $SPEECH_SERVICES/json_parse.py $TICKET resultfile`
echo "Hello World" > $RESULTFILE\nsleep 1\nexit 0\n"""

SGE_ERROR_CODE = """#!/bin/bash\n#$ -e /root/\nsleep 2\nexit 0\n"""
EXIT_CODE = """#!/bin/bash\nsleep 1\nexit 1\n"""

"""CLIENT DOWNLOADER"""
HOST_NAME = 'localhost' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER_DOWN = 9000 
TEMP_FILE = 'tmp.dump'

class Downloader(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(s):
        length = int(s.headers['Content-Length'])
        data = s.rfile.read(length)
        with open(TEMP_FILE, 'wb') as f:
            f.write(data)
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def log_message(self, format, *args):
        LOG.info("DOWNLOAD: %s - - [%s] %s\n" % (self.address_string(),self.log_date_time_string(),format%args))

"""CLIENT UPLOADER"""
PORT_NUMBER_UP = 9001 

class Uploader(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        s.send_response(200)
        s.send_header("Content-type", "audio/ogg")
        s.send_header("Content-Length", str(100*1024))
        s.end_headers()
        s.wfile.write(os.urandom(100*1024))

    def log_message(self, format, *args):
        LOG.info("UPLOAD: %s - - [%s] %s\n" % (self.address_string(),self.log_date_time_string(),format%args))

"""Download/Upload HTTP server threads"""
class Worker(threading.Thread):

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server

    def run(self):
        LOG.info("Starting HTTP server")
        self.server.serve_forever()

    def stop(self):
        LOG.info("Closing down HTTP server")
        self.server.shutdown()
        self.server.server_close()


class SchTest:

    def __init__(self, speechdb, servicedb, servicedir, storage):
        self.speechdb = speechdb
        self.servicedb = servicedb
        self.servicedir = servicedir
        self.storage = storage

        self.spdb = sqlite.connect(self.speechdb, factory=JobsDB)
        self.spdb.row_factory = sqlite.Row

        self.svdb = sqlite.connect(self.servicedb, factory=ServicesDB)
        self.svdb.row_factory = sqlite.Row

    def add_job(self, command, username, service, subsystem, getaudio, gettext, postresult):
        """
            Add a job to the queue
        """
        # Generate new job id
        jobid = "j{}".format(str(uuid.uuid4().hex))
        token = str(uuid.uuid4().hex)
        LOG.info("Generating job - {}".format(jobid))

        request = {}
        request["command"] = command
        request["token"] = token
        request["service"] = service
        request["subsystem"] = subsystem
        request["getaudio"] = getaudio
        request["gettext"] = gettext
        request["postresult"] = postresult

        # Write the job information to job file
        new_date = datetime.datetime.now()
        ticket = os.path.join(self.storage, username, str(new_date.year), str(new_date.month), str(new_date.day), jobid)
        if not os.path.exists(ticket): os.makedirs(ticket)

        ticket = os.path.join(ticket, jobid)
        LOG.info("Generating ticket - {}".format(ticket))
        with codecs.open(ticket, "w", "utf-8") as f:
            json.dump(request, f)

        # Add job to job db
        with self.spdb as db:
            # Add job entry to table
            db.add_job(jobid, username, ticket, time.time())

        return jobid

    def add_service(self, name, script, audio, text, subsystem):
        """
            Add new service 
        """
        LOG.info("Adding service - {}, {}, {}, {}, {}".format(name, script, audio, text, subsystem))
        with self.svdb as db:
            db.lock()
            db.add_service(name, script)
            db.add_require(name, audio, text)
            db.add_table(name)
            db.add_subsystem(name, subsystem)

    def del_service(self, name):
        """
            Remove service
        """
        LOG.info("Removing service - {}".format(name))
        with self.svdb as db:
            db.lock()
            db.del_service(name)
            db.del_require(name)
            db.del_table(name)

    def add_script(self, filename, code):
        """
            Create a new script with specified code
        """
        LOG.info("Adding new script - {}".format(filename))
        with codecs.open(filename, "w", "utf-8") as f:
            f.write(code)
        os.chmod(filename, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def del_script(self, filename):
        """
            Remove script
        """
        LOG.info("Removing script - {}".format(filename))
        os.remove(filename)

    ### HIGH-LEVEL testers ###
    def test_normal(self):
        """
            Setup a normal test for the scheduler
        """
        # Add service to speech services DB
        self.add_service("test_normal", "normal.sh", "Y", "N", "default")

        # Generate the script that SGE is going to run
        script = os.path.join(self.servicedir, "normal.sh")
        self.add_script(script, NORMAL_CODE)

        # Add job to speech jobs DB
        jobid = self.add_job("normal.sh", "sch_test", "test_normal",
                "default", "http://localhost:{}".format(PORT_NUMBER_UP), None,
                "http://localhost:{}".format(PORT_NUMBER_DOWN))

        # Monitor job status
        out_line = ""
        while True:
            with self.spdb as db:
                row = db.job_status(jobid)
                if "{}".format(row) != out_line:
                    print("{}".format(row))
                    out_line = "{}".format(row)
                if not bool(row):
                    break
            time.sleep(0.5)

        # Clean up speech services DB
        self.del_service("test_normal")

        # Remove script
        #self.del_script(script)

        # Remove job if needed
        with self.spdb as db:
            db.lock()
            db.delete_job(jobid)

    def test_sge_error(self):
        pass

    def test_script_exit(self):
        pass

    def test_noupload(self):
        pass

    def test_nodownload(self):
        pass



class JobsDB(sqlite.Connection):
    def lock(self):
        self.execute("BEGIN IMMEDIATE")

    def add_job(self, jobid, username, ticket, time):
        self.execute("INSERT INTO jobs (jobid, username, ticket, status, sgeid, creation, errstatus) VALUES(?,?,?,?,?,?,?)",
            (jobid, username, ticket, "P", None, time, None))

    def delete_job(self, jobid):
        self.execute("DELETE FROM jobs WHERE jobid=?", (jobid,))

    def adminlock(self):
        self.execute("UPDATE jobCtrl SET value='Y' WHERE key=?", ('lock',))

    def adminunlock(self):
        self.execute("UPDATE jobCtrl SET value='N' WHERE key=?", ('lock',))

    def job_status(self, jobid):
        row = self.execute("SELECT status, errstatus FROM jobs WHERE jobid=?", (jobid,))
        if row is not None:
            return dict(row)
        else:
            return {}

class ServicesDB(sqlite.Connection):
    def lock(self):
        self.execute("BEGIN IMMEDIATE")

    def add_service(self, name, command):
        self.execute("INSERT INTO services (name, command) VALUES(?,?)", (name, command))

    def del_service(self, name):
        self.execute("DELETE FROM services WHERE name=?", (name,))

    def add_require(self, name, need_audio, need_text):
        self.execute("INSERT INTO require(name, audio, text) VALUES(?,?,?)", (name, need_audio, need_text))

    def del_require(self, name):
        self.execute("DELETE FROM require WHERE name=?", (name,))

    def add_table(self, name):
        self.execute("CREATE TABLE {} ( subsystem VARCHAR(32) PRIMARY KEY )".format(name))

    def del_table(self, table):
        self.execute("DROP TABLE {}".format(table))

    def add_subsystem(self, table, subsystem):
        self.execute("INSERT INTO {}(subsystem) VALUES(?)".format(table), (subsystem,))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--speechdb', metavar='BASEURL', type=str, dest="speechdb", default=DEF_SPEECH_DB, help="Speech Jobs DB")
    parser.add_argument('--servicedb', metavar='BASEURL', type=str, dest="servicedb", default=DEF_SERVICE_DB, help="Speech Services DB")
    parser.add_argument('--servicedir', metavar='BASEURL', type=str, dest="servicedir", default=DEF_SERVICE_DIR, help="Speech Services DB")
    parser.add_argument('--storage', metavar='BASEURL', type=str, dest="storage", default=DEF_STORAGE_DIR, help="Temporary storage")
    args = parser.parse_args()

    sch = SchTest(os.path.expanduser(args.speechdb), os.path.expanduser(args.servicedb),
            os.path.abspath(os.path.expanduser(args.servicedir)), os.path.abspath(os.path.expanduser(args.storage))) 

    # Bring up the downloader and uploader HTTP threads
    down_server_cls = BaseHTTPServer.HTTPServer
    ds = down_server_cls((HOST_NAME, PORT_NUMBER_DOWN), Downloader)
    up_server_cls = BaseHTTPServer.HTTPServer
    us = up_server_cls((HOST_NAME, PORT_NUMBER_UP), Uploader)
    dw = Worker(ds)
    dw.start()
    uw = Worker(us)
    uw.start()

    time.sleep(0.5)
    # Run main loop
    while True:
        try:
            cmd = raw_input("Enter command (type list, help):$ ")
            if len(cmd) == 0:
                continue
            cmd = cmd.lower()
        except BaseException as e:
            print("Closing down: {}".format(repr(e)))
            break

        if cmd == "exit":
            break
        elif cmd in ["help", "list"]:
            print("TEST_NORMAL - test a normal flow")
            print("EXIT - quit")
        else:
            try:
                meth = getattr(sch, cmd)
                meth()
            except Exception as e:
                print("Something has gone wrong:{}".format(repr(e)))


    # Shutdown threads
    dw.stop()
    dw.join()
    uw.stop()
    uw.join()

