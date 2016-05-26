#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function #Py2

import json
import time
import uuid
import base64
import admin
import auth
import tempfile
import os
import datetime


try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

from httperrs import NotAuthorizedError, ConflictError, NotFoundError

class Admin(admin.Admin):
    pass

class Jobs(auth.UserAuth):

    def __init__(self, config_file):
        with open(config_file) as infh:
            self._config = json.loads(infh.read())

    def add_job(self, request):
        """
            Add job to the queue
        """
        #AUTHORISE REQUEST
        username = auth.token_auth(request["token"], self._config["authdb"])

        # Check request is valid
        with sqlite.connect(self._config['servicesdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Check that the service is avaliable
            db_curs.execute("SELECT * FROM services")
            _tmp_s = db_curs.fetchall()

            services = {}
            for serv, builder in _tmp_s:
                services[serv] = {}
                services[serv]["builder"] = builder

            if request["service"] not in services: raise NotFoundError("Requested service %s: not found!" % request["service"])

            # Check that all parameters have been set
            db_curs.execute("SELECT * FROM require")
            _tmp_s = db_curs.fetchall()

            for serv, aud, txt in _tmp_s:
                services[serv]["audio"] = aud
                services[serv]["text" ] = txt

            if services[request["service"]]["audio"] == 'Y' and "getaudio" not in request:
                raise NotFoundError("Requested service %s: requires 'getaudio' paramater" % request["service"])

            if services[request["service"]]["text"] == 'Y' and "gettext" not in request:
                raise NotFoundError("Requested service %s: requires 'gettext' paramater" % request["service"])

            # Check subsystem
            db_curs.execute("SELECT * FROM %s" % request["service"])
            _tmp_s = db_curs.fetchall()

            subsys = [x[0] for x in _tmp_s]
            if request["subsystem"] not in subsys: raise NotFoundError("Requested service subsystem %s: not found!" % request["subsystem"])


        # Add job to job db
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()

            # Generate new job id
            jobid = str(uuid.uuid4())
            jobid = 'j%s' % jobid.replace('-', '')

            # Write the job information to job file
            jobinfo = os.path.join(self._config["storage"], username, datetime.datetime.now().strftime('%Y-%m-%d'))
            if not os.path.exists(jobinfo): os.makedirs(jobinfo)

            jobinfo = os.path.join(jobinfo, jobid)
            f = open(jobinfo, 'wb')
            request["builder"] = services[request["service"]]["builder"]
            f.write(json.dumps(request))
            f.close()

            # Add job entry to table
            db_curs.execute("INSERT INTO jobs (jobid, username, jobinfo, status, sgeid, creation) VALUES(?,?,?,?,?,?)",
            (jobid, username, jobinfo, 'P', 0, time.time()))
            db_conn.commit()

            return {'jobid' : jobid}

    def delete_job(self, request):
        """
            Delete job from the queue if the job is not running
        """
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Delete job
            db_curs.execute("SELECT * FROM jobs WHERE jobid='%s'" % request['jobid'])
            job_info = db_curs.fetchone()

            # See if job exists
            if job_info is None: raise NotFoundError('job does not exist')

            db_curs.execute("UPDATE jobs SET status = 'D' WHERE jobid='%s'" % request['jobid'])
            db_conn.commit()

        return 'job deleted'

    def query_job(self, request):
        """
            Query job and return information
        """
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Delete job
            db_curs.execute("SELECT * FROM jobs WHERE jobid='%s'" % request['jobid'])
            job_info = db_curs.fetchone()
            print(job_info)
            # See if job exists
            if job_info is None: raise NotFoundError('job does not exist')

            # Re-format info
            info = {'jobid' : job_info[0], 'username' : job_info[1], 'status' : job_info[3], 'creation' : job_info[4]}
            with open(job_info[2], 'rb') as f:
                data = f.read()
                info[job_info[2]] = data

            return info

    def user_jobs(self, request):
        """
            Query all jobs belonging to the user and return information
        """
        #AUTHORISE REQUEST
        username = auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Delete job
            db_curs.execute("SELECT * FROM jobs WHERE username='%s'" % username)
            job_info = db_curs.fetchall()
            print(job_info)
            # See if job exists
            if job_info is None: raise NotFoundError('job does not exist')

            # Re-format the info for the user
            info = {}
            info["jobs"] = []
            for jobid, username, jobinfo, status, creation in job_info:
                info["jobs"].append((jobid, username, status, creation))
                with open(jobinfo, 'rb') as f:
                    data = f.read()
                    info[jobid] = data

            return info

    def discover(self, request):
        """
            Return all services and subsystems to user
        """
        pass

