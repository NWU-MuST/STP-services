#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import json
import codecs
import tempfile
import datetime
import Queue
import urllib
import threading
import time
import os
import uuid
import shutil
import requests
import drmaa

try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

class Data(object):
    """
        Data encapsulation class
    """
    def __init__(self, job, url, data_file):
        self.job = job
        self.url = url
        self.data_file = data_file

# Download data for job
class Downloader(threading.Thread):
    """
        Data fetching thread that downloads data needed by a job
    """
    def __init__(self, queue, jobsdb):
        threading.Thread.__init__(self)
        self.jobsdb = jobsdb
        self.queue = queue
        self.running = True

    def run(self):
        while self.running:
            if not self.queue.empty():
                data = self.queue.get()
                jobid, username, taskinfo, status, sgeid, creation = data.job

                # Fetch data
                print('Fetching: %s -> %s' % (data.url, data.data_file))
                urllib.urlretrieve(data.url, data.data_file)

                #TODO: Check response
                # - Re-tries: put job back into queue

                # Update job status
                with sqlite.connect(self.jobsdb) as db_conn:
                    db_curs = db_conn.cursor()
                    db_curs.execute("UPDATE jobs SET status = 'C' WHERE jobid='%s'" % jobid)
                    db_conn.commit()

                #TODO: error in downloading

                self.queue.task_done()
            time.sleep(0.1)

    def stop(self):
        self.running = False

# Upload results to url
class Uploader(threading.Thread):
    """
        Upload job results to URL
    """
    def __init__(self, queue, jobsdb):
        threading.Thread.__init__(self)
        self.jobsdb = jobsdb
        self.queue = queue
        self.running = True

    def run(self):
        while self.running:
            if not self.queue.empty():
                data = self.queue.get()
                jobid, username, taskinfo, status, sgeid, creation = data.job

                # Read in result
                result = None
                with open(data.data_file, 'rb') as f:
                    result = f.read()

                # Upload result
                print('Uploading: %s -> %s' % (data.url, data.data_file))
                headers = {"Content-Type" : "application/json", "Content-Length" : str(len(result))}
                pkg = {"CTM" : result}
                response = requests.put(data.url, headers=headers, data=json.dumps(pkg))

                #TODO: Check response
                # - Re-tries: put job back into queue

                # Update job status - mark for deletion
                with sqlite.connect(self.jobsdb) as db_conn:
                    db_curs = db_conn.cursor()
                    db_curs.execute("UPDATE jobs SET status = 'X' WHERE jobid='%s'" % jobid)
                    db_conn.commit()

                #TODO: Error in uploading

                self.queue.task_done()
            time.sleep(0.1)

    def stop(self):
        self.running = False


class Jobs:

    def __init__(self, configfile):
        self._configfile = configfile
        self._config = None
        with codecs.open(self._configfile, 'r', 'utf-8') as f:
            self._config = json.load(f)

        self._error_submit = []

        # Downloader
        self._d_queue = Queue.Queue()
        self._downloader = Downloader(self._d_queue, self._config["jobsdb"])
        self._downloader.start()

        # Uploader
        self._u_queue = Queue.Queue()
        self._uploader = Uploader(self._u_queue, self._config["jobsdb"])
        self._uploader.start()

    def location_translate(self, full_file):
        """
            Translate storage location from docker to actual system
        """
        return full_file.replace(self._config["DIR_TRANSLATE"][0], self._config["DIR_TRANSLATE"][1])

    def load(self):
        """
            Query the tasks DB
        """
        jobs = None
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            db_curs.execute("SELECT * FROM jobs")
            jobs = db_curs.fetchall()
        return jobs

    def sync(self, sge, sge_jobs):
        """
            Process tasks DB - check jobs, update row parameters and submit new requests
        """
        jobs = self.load()
        self._error_submit = []
        if jobs is not None:
            for data in jobs:
                jobid, username, taskinfo, status, sgeid, creation = data
                print('Sync: {}'.format(data))
                if status == 'P': # Pending
                    self.fetch(data)
                elif status == 'C': # Downloaded
                    self.submit(data, sge, sge_jobs)
                elif status in ['R', 'Q']: # Running, queued
                    self.query(data, sge)
                elif status == 'N': # Job finished without error
                    self.done(data, sge, sge_jobs)
                elif status == 'F': # Job finished but failed
                    self.failed(data, sge, sge_jobs)
                elif status == 'X': # Delete - either by user or job completed
                    self.delete(data, sge, sge_jobs)
                elif status == 'E': # Error - no communicate
                    self.error(data, sge, sge_jobs)
                elif status in ['U', 'D']: # in Upload, Download queue
                    pass
                else:
                    print("Unknown status: %s", status)

        if len(self._error_submit) != 0:
            self.send_errors()

    def fetch(self, data):
        """
            Fetch data for job
        """
        jobid, username, taskinfo, status, sgeid, creation = data
        with codecs.open(self.location_translate(taskinfo), "r", "utf-8") as f:
            jvars = json.load(f)

        # Create a location
        data_loc = os.path.join(self._config["storage"], username, datetime.datetime.now().strftime('%Y-%m-%d'))
        if not os.path.exists(data_loc):
            os.mkdir(data_loc)

        count = 0
        for url, file_loc in [("getaudio", "audio_file"), ("gettext", "text_file")]:
            if url in jvars:
                # Create a new data file
                dataid = str(uuid.uuid4())
                dataid = 'd%s' % dataid.replace('-', '')
                data_file = os.path.join(data_loc, dataid)
                # Test new file
                with open(data_file, 'w') as ft:
                    ft.write(' ')
                os.remove(data_file)
                # Save to job ticket
                jvars[file_loc] = data_file

                # Add to download queue
                new_fetch = Data(data, jvars[url], data_file)
                self._d_queue.put(new_fetch)
                count += 1

        # No files for download there is an error
        if count == 0:
            pass

        # Save pointer to data file(s)
        ft = tempfile.NamedTemporaryFile(delete=False)
        json.dump(jvars, ft)
        ft.close()
        shutil.move(ft.name, self.location_translate(taskinfo))

        # Update job status
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            db_curs.execute("UPDATE jobs SET status = 'D' WHERE jobid='%s'" % jobid)
            db_conn.commit()

    def submit(self, data, sge, sge_jobs):
        """
            Build command, submit job and update task DB with job number
        """
        jobid, username, taskinfo, status, sgeid, creation = data

        # Get service command
        builder = None
        jvars = None
        with codecs.open(self.location_translate(taskinfo), "r", "utf-8") as f:
            jvars = json.load(f)
            builder = jvars["builder"]

        # Build SGE queue job
        jt = sge.createJobTemplate()
        jt.remoteCommand = 'bash'
        jt.args = [os.path.join(self._config["services"], builder),self.location_translate(taskinfo)]
        jt.errorPath=':%s.err' % self.location_translate(taskinfo)
        jt.outputPath=':%s.out' % self.location_translate(taskinfo)
        jt.joinFiles=False
        sgeid = sge.runJob(jt)

        # Populate the task info JSON file
        jvars["sgeid"] = sgeid
        jvars["sgestdout"] = jt.outputPath
        jvars["sgestderr"] = jt.errorPath
        jvars["resultfile"] = "%s.result" % self.location_translate(taskinfo)

        ft = tempfile.NamedTemporaryFile(delete=False)
        json.dump(jvars, ft)
        ft.close()
        shutil.move(ft.name, self.location_translate(taskinfo))
        print(os.path.getsize(self.location_translate(taskinfo)))

        # Update job
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            db_curs.execute("UPDATE jobs SET status = 'Q' WHERE jobid='%s'" % jobid)
            db_curs.execute("UPDATE jobs SET sgeid = '%s' WHERE jobid='%s'" % (sgeid, jobid))
            db_conn.commit()

        sge_jobs[sgeid] = jt
        #TODO: check for errors and un-roll

    def query(self, data, sge):
        """
            Query submitted job status
        """
        jobid, username, taskinfo, status, sgeid, creation = data
        status = sge.jobStatus(sgeid)
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()

            if status == drmaa.JobState.QUEUED_ACTIVE:
                db_curs.execute("UPDATE jobs SET status = 'Q' WHERE jobid='%s'" % jobid)
            elif status == drmaa.JobState.RUNNING:
                db_curs.execute("UPDATE jobs SET status = 'R' WHERE jobid='%s'" % jobid)
            elif status == drmaa.JobState.DONE:
                db_curs.execute("UPDATE jobs SET status = 'N' WHERE jobid='%s'" % jobid)
            elif status == drmaa.JobState.FAILED:
                db_curs.execute("UPDATE jobs SET status = 'F' WHERE jobid='%s'" % jobid)
            else:
                db_curs.execute("UPDATE jobs SET status = 'E' WHERE jobid='%s'" % jobid)
            db_conn.commit()

        """
        decodestatus = {drmaa.JobState.UNDETERMINED: 'process status cannot be determined',
            drmaa.JobState.QUEUED_ACTIVE: 'job is queued and active',
            drmaa.JobState.SYSTEM_ON_HOLD: 'job is queued and in system hold',
            drmaa.JobState.USER_ON_HOLD: 'job is queued and in user hold',
            drmaa.JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
            drmaa.JobState.RUNNING: 'job is running',
            drmaa.JobState.SYSTEM_SUSPENDED: 'job is system suspended',
            drmaa.JobState.USER_SUSPENDED: 'job is user suspended',
            drmaa.JobState.DONE: 'job finished normally',
            drmaa.JobState.FAILED: 'job finished, but failed'}
        """

    def done(self, data, sge, sge_jobs):
        """
            Job finished running normally
        """
        jobid, username, taskinfo, status, sgeid, creation = data

        # Load the job ticket
        jvars = None
        with codecs.open(self.location_translate(taskinfo), "r", "utf-8") as f:
            jvars = json.load(f)

        new_upload = Data(data, jvars["postresult"], jvars["resultfile"])
        self._u_queue.put(new_upload)

        # Mark job is uploading
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            db_curs.execute("UPDATE jobs SET status = 'U' WHERE jobid='%s'" % jobid)
            db_conn.commit()

    def delete(self, data, sge, sge_jobs):
        """
            Delete job as requested by user
            This is different to normal delete when job has finished running
        """
        jobid, username, taskinfo, status, sgeid, creation = data

        #TODO: job ticket clean up

        # Remove from SGE
        jt = sge_jobs[sgeid]
        sge.deleteJobTemplate(jt)
        del sge_jobs[sgeid]

        # Remove from table
        with sqlite.connect(self._config['jobsdb']) as db_conn:
            db_curs = db_conn.cursor()
            db_curs.execute("DELETE FROM jobs WHERE jobid='%s'" % jobid)
            db_conn.commit()

    def failed(self, sge, sge_jobs):
        """
            Job ran but failed to complete
        """
        #TODO: move job to error table
        pass

    def error(self, sge, sge_jobs):
        """
            An error occurred while trying to run the job
            but the server could not communicate this
            to the user/app-server
        """
        #TODO: move job to error table
        pass

    def send_errors(self):
        """
            During submission some jobs could not be submitted
            Send the error messages to the POST url provided in the job
        """
        pass

    def shutdown(self):
        """
            Shutdown upload and download threads
        """
        #TODO: check if queues are empty
        self._downloader.stop()
        self._uploader.stop()
        self._downloader.join()
        self._uploader.join()



