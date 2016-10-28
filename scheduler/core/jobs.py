#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import json
import codecs
import tempfile
import datetime
import urllib
import threading
import time
import os
import uuid
import shutil
import requests

from gridengine import SGE

CHUNK_SIZE = 100*1024 # HTTP download chunk size
RETRY = 3 # number of times we'll try to download and upload
RETRY_SLEEP = 5 #300 # 5 minutes before trying to download or upload again
STALE_TIME = 1 #60*60*24 # Will wait 1 day before removing stale jobs

try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions


# Download data for job
class Downloader(threading.Thread):
    """
        Data fetching thread that downloads data needed by a job
    """
    def __init__(self, audio_url, audio_filename, jobid, ticket, dbname, logger, text_url=None, text_filename=None):
        threading.Thread.__init__(self)

        self.audio_url = audio_url
        self.audio_filename = audio_filename
        self.text_url = text_url
        self.text_filename = text_filename

        self.jobid = jobid
        self.ticket = ticket
        self.dbname = dbname
        self.logger = logger

        self.running = True
        self.done = False
        self.retry = RETRY
        self.retry_sleep = RETRY_SLEEP

    def run(self):
        self.db = sqlite.connect(self.dbname, factory=JobsDB)
        self.db.row_factory = sqlite.Row

        # Fetch data
        try:
            self._download(self.audio_url, self.audio_filename)
            if self.text_url is not None:
                self.retry = RETRY
                self._download(self.text_url, self.text_filename)

            with self.db as db:
                db.lock()
                db.update("status", "C", self.jobid)
        except:
            self.logger.error("Caught download error!!")

        self.done = True

    def _download(self, url, filename):
        self.logger.debug('Fetching: {} -> {}'.format(url, filename))
        #r = requests.get(url)
        #print len(r.content)
        while self.retry > 0:
            try:
                # Download data incrementally
                r = requests.get(url, stream=True)
                if r.status_code != 200:
                    raise RuntimeError("{} {}".format(r.status_code, r.reason))

                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            f.flush()
                            os.fsync(f.fileno())
                self.logger.debug("Download completed (jobid={}): {} saved to {}".format(self.jobid, url, filename))
                self.retry = 0
            except Exception as e:
                self.logger.error("RETRY(jobid={}): Failed to download {}: ERROR={}".format(self.jobid, url, repr(e)))
                self.logger.error("Will try again in {} seconds, retry number {}".format(self.retry_sleep, self.retry))
                self.mysleep(self.retry_sleep)
                self.retry = int(self.retry) - 1
                if os.path.exists(filename):
                    os.remove(filename)

                if self.retry == 0:
                    self.logger.error("Download failed (jobid={}), marking error: {}".format(self.jobid, url))
                    # Update db - error has occurred
                    with self.db as db:
                        db.lock()
                        db.update("status", "E", self.jobid)
                        db.update("errstatus", "Download failed: {}".format(url), self.jobid)

                    # Touch the taskfile - used by error to remove old jobs with an errstatus set
                    with codecs.open(self.ticket, "r", "utf-8") as f:
                        jvars = json.load(f)
                    jvars["touched"] = time.time()
                    jvars["error"] = "Download error: {}".format(repr(e))

                    ft = tempfile.NamedTemporaryFile(delete=False)
                    json.dump(jvars, ft)
                    ft.close()
                    shutil.move(ft.name, self.ticket)

    def stop(self):
        self.logger.debug("Stopping...")
        self.retry = 0
        self.running = False

    def mysleep(self, pause):
        """
            Custom sleep that periodically checks whether the thread should stop
        """
        for n in range(int(pause)):
            time.sleep(1)
            if not self.running:
                return

# Upload results to url
class Uploader(threading.Thread):
    """
        Upload job results to URL
    """
    def __init__(self, url, filename, tag, tostate, jobid, ticket, dbname, logger):
        threading.Thread.__init__(self)
        self.url = url
        self.filename = filename
        self.tag = tag
        self.tostate = tostate
        self.jobid = jobid
        self.ticket = ticket
        self.dbname = dbname
        self.logger = logger

        self.running = True
        self.done = False
        self.retry = int(RETRY)
        self.retry_sleep = RETRY_SLEEP

    def run(self):
        self.db = sqlite.connect(self.dbname, factory=JobsDB)
        self.db.row_factory = sqlite.Row

        # Fetch data
        self.logger.debug('Uploading: {} -> {}'.format(self.url, self.filename))

        while self.retry > 0:
            try:
                with open(self.filename, 'rb') as f:
                    result = f.read()

                # Upload result
                headers = {"Content-Type" : "application/json", "Content-Length" : str(len(result))}
                pkg = {self.tag : result}
                response = requests.post(self.url, headers=headers, data=json.dumps(pkg))
                if response.status_code != 200:
                    raise RuntimeError("{} {}".format(response.status_code, response.reason))

                self.logger.debug("Upload completed (jobid={}): {} saved to {}".format(self.url, self.url, self.filename))
                # Job done go for cleanup
                with self.db as db:
                    db.lock()
                    db.update("status", self.tostate, self.jobid)

                # We're done
                self.retry = 0

            except Exception as e:
                self.logger.error("RETRY(jobid={}): Failed to upload {}: ERROR={}".format(self.jobid, self.url, repr(e)))
                self.logger.error("Will try again in {} seconds, retry number {}".format(self.retry_sleep, self.retry))
                self.mysleep(self.retry_sleep)
                self.retry = self.retry - 1

                if self.retry == 0:
                    self.logger.error("Upload failed (jobid={}), marking error: {}".format(self.jobid, self.url))
                    # Update db - error has occurred
                    with self.db as db:
                        db.lock()
                        db.update("status", "E", self.jobid)
                        db.update("errstatus", "Upload failed: {}".format(self.url), self.jobid)

                    # Touch the taskfile - used by error to remove old jobs with an errstatus set
                    with codecs.open(self.ticket, "r", "utf-8") as f:
                        jvars = json.load(f)
                    jvars["touched"] = time.time()
                    jvars["error"] = "Upload error: {}".format(repr(e))

                    ft = tempfile.NamedTemporaryFile(delete=False)
                    json.dump(jvars, ft)
                    ft.close()
                    shutil.move(ft.name, self.ticket)

                    if os.path.exists(self.filename):
                        os.remove(self.filename)

        self.done = True

    def stop(self):
        self.logger.debug("Stopping...")
        self.retry = 0
        self.running = False

    def mysleep(self, pause):
        """
            Custom sleep that periodically checks whether the thread should stop
        """
        for n in range(int(pause)):
            time.sleep(1)
            if not self.running:
                return

class Jobs:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.sge = SGE(logger)

        self.db = sqlite.connect(config['jobsdb'], factory=JobsDB)
        self.db.row_factory = sqlite.Row

        # Downloader
        self.downloader = {}

        # Uploader
        self.uploader = {}

    def location_translate(self, full_file):
        """
            Translate storage location from docker to actual system
        """
        return full_file.replace(self.config["DIR_TRANSLATE"][0], self.config["DIR_TRANSLATE"][1])

    def load(self):
        """
            Query the tasks DB
        """
        # Update job status
        with self.db as db:
            db.lock()
            _jobs = db.get_jobs()

        # Extract jobs and convert from dict format to tuple
        jobs = []
        for val in _jobs:
            _tmp = (val["jobid"], val["username"], val["ticket"],
                    val["status"], val["sgeid"], val["creation"], val["errstatus"])
            jobs.append(_tmp)
        return jobs

    def sync(self):
        """
            Process tasks DB - check jobs, update row parameters and submit new requests
        """
        # Check if the job db is locked
        with self.db as db:
            db.lock()
            status = db.adminlockstatus()
            if status[0] == "Y":
                return

        # Parse jobs
        jobs = self.load()

        # Clean out finished threads from queues
        self.clean_queue(self.downloader)
        self.clean_queue(self.uploader)

        if jobs is not None:
            for data in jobs:
                jobid, username, ticket, status, sgeid, creation, errstatus = data
                print('Sync: {}'.format(data))
                if status == 'P': # Pending
                    self.fetch(data)
                elif status == 'C': # Downloaded
                    self.submit(data)
                elif status in ['R', 'Q']: # Running, queued
                    self.query(data)
                elif status == 'N': # Job finished without error
                    self.done(data)
                elif status == 'F': # Job finished but failed
                    self.failed(data)
                elif status == 'X': # Delete - either by user or job completed
                    self.delete(data)
                elif status == 'K': # Cleanup job files and db entry
                    self.cleanup(data)
                elif status == 'E': # Error - communicate
                    self.error(data)
                elif status == 'S': # Stale
                    self.stale(data)
                elif status in ['U', 'D']: # Uploading result or Downloading data
                    pass
                else:
                    print("Unknown status: {}".format(status))

    def clean_queue(self, queue):
        """
            Remove finished download/upload threads
        """
        for jobid in queue.keys():
            if queue[jobid].done:
                queue[jobid].join()
                self.logger.debug("CLEAN_QUEUE: removing fetcher {}".format(jobid))
                del queue[jobid]

    def fetch(self, data):
        """
            Fetch data for job
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        self.logger.debug("FETCH: {}".format(jobid))
        try:
            jvars = self.load_ticket(ticket)
            if "getaudio" not in jvars:
                raise RuntimeError("getaudio missing in job request")

            # Create a location
            data_loc = os.path.join(self.config["storage"], username, datetime.datetime.now().strftime('%Y-%m-%d'))
            if not os.path.exists(data_loc):
                os.mkdir(data_loc)

            # Create data files
            jvars["audio_file"] = self.data_file(data_loc)
            if "gettext" in jvars: # See if we need to get text
                jvars["text_file"] = self.data_file(data_loc)
            else:
                jvars["gettext"] = None
                jvars["text_file"] = None
            self.update_ticket(jvars, ticket)

            # Setup download job
            down = Downloader(jvars["getaudio"], jvars["audio_file"],
                   jobid, self.location_translate(ticket), self.config["jobsdb"],
                   self.logger, jvars["gettext"], jvars["text_file"])
            self.downloader[jobid] = down
            self.downloader[jobid].start()

            # Update job status
            with self.db as db:
                db.lock()
                db.update("status", "D", jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Download Error", jobid, ticket)

    def data_file(self, data_location):
        """
            Create a new data file and test that it can be created
        """
        # Create a new data file
        dataid = "d{}".format(str(uuid.uuid4().hex))
        data_file = os.path.join(data_location, dataid)
        self.logger.debug("DATA_FILE: creating {}".format(data_file))
        # Test new file
        with open(data_file, 'w') as ft:
            ft.write(' ')
        os.remove(data_file)
        return data_file

    def load_ticket(self, ticket):
        """
            Load the job's ticket information
        """
        self.logger.debug("LOAD_TICKET: {}".format(self.location_translate(ticket)))
        with codecs.open(self.location_translate(ticket), "r", "utf-8") as f:
            jvars = json.load(f)
        return jvars

    def update_ticket(self, jvars, ticket):
        """
            Update the ticket JSON object and save to disk
        """
        self.logger.debug("UPDATE_TICKET: {}, {}".format(self.location_translate(ticket), jvars))
        ft = tempfile.NamedTemporaryFile(delete=False)
        json.dump(jvars, ft)
        ft.close()
        shutil.move(ft.name, self.location_translate(ticket))

    def submit(self, data):
        """
            Build command, submit job and update task DB with job number
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        try:
            # Get service command
            jvars = self.load_ticket(ticket)
            command = jvars["command"]

            # Load the service template
            with codecs.open(os.path.join(self.config["services"], command), "r", "utf-8") as f:
                template = f.read()

            # Replace variable names contained in the template
            now_name = self.temp_name()
            job_name = "{}.{}".format(username, now_name)
            template = template.replace("JOB_NAME", job_name)
            real_dir = os.path.dirname(self.location_translate(ticket))
            template = template.replace("ERR_OUT", ":{}".format(real_dir))
            template = template.replace("STD_OUT", ":{}".format(real_dir))
            template = template.replace("##INSTANCE_TICKET##", self.location_translate(ticket))
            template = template.replace("##SPEECH_SERVICES##", self.config["services"])

            script_name = os.path.join(real_dir, "{}.sh".format(job_name))
            with codecs.open(script_name, "w", "utf-8") as f:
                f.write(template)

            # SGE - qsub job
            sgeid = self.sge.qsub(script_name)

            # Populate the task info JSON file
            jvars["sgeid"] = sgeid
            jvars["resultfile"] = "{}.result".format(script_name)
            jvars["scriptname"] = script_name
            self.update_ticket(jvars, ticket)
            self.logger.debug("SUBMIT: {}, {}, {}".format(jobid, sgeid, script_name))

            # Update job
            with self.db as db:
                db.lock()
                db.update("status", "Q", jobid)
                db.update("sgeid", sgeid, jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Submit Error", jobid, ticket)

    def temp_name(self):
        """
            Return a short temporary name
        """
        #TODO: there must be another way?
        f=tempfile.NamedTemporaryFile()
        name = os.path.basename(f.name)
        f.close()
        return name

    def query(self, data):
        """
            Query submitted job status
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        try:
                state = self.sge.query(sgeid)

                with self.db as db:
                    db.lock()
                    if state == "qw": # queued
                        db.update("status", "Q", jobid)
                    elif state == "r": # running
                        db.update("status", "R", jobid)
                    elif state in ["Eqw", "F"]: # waiting in error or job failed
                        db.update("status", "F", jobid)
                    elif state == "Z": # job not in qacct yet
                        db.update("status", "F", jobid)
                    elif state == "D": # job done
                        db.update("status", "N", jobid)
                    else:
                        raise RuntimeError("Unknown SGE state {}".format(state))

                self.logger.debug("QUERY: {}, {}, {}".format(jobid, sgeid, state))
        except KeyError:
            with self.db as db:
                db.lock()
                db.update("status", status, jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Job Query Error", jobid, ticket)

    def done(self, data):
        """
            Job finished running normally
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        self.logger.debug("DONE: {}".format(jobid))
        try:
            # Load the job ticket
            jvars = self.load_ticket(ticket)

            # Send the result back to user and make for cleanup
            upload = Uploader(jvars["postresult"], jvars["resultfile"], "CTM", "K", jobid,
                    self.location_translate(ticket), self.config['jobsdb'], self.logger)
            self.uploader[jobid] = upload
            self.uploader[jobid].start()

            # Mark job is uploading
            with self.db as db:
                db.lock()
                db.update("status", "U", jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Job Finished Error", jobid, ticket)

    def delete(self, data):
        """
            Delete job requested by user or server
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        self.logger.debug("DELETE: {}".format(jobid))
        try:
            # See if job is in the SGE queue
            try:
                if sgeid is not None:
                    self.sge.qdel(sgeid)

            except KeyError:
                pass

            # Mark job for cleanup
            with self.db as db:
                db.lock()
                db.update("status", "K", jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Deleting Job Error", jobid, ticket)

    def cleanup(self, data):
        """
            Job not running so all job files can now be remove
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        try:
            # Save db entry to ticket
            jvars = self.load_ticket(ticket)
            jvars["jobid"] = jobid
            jvars["username"] = username
            jvars["ticket"] = ticket
            jvars["status"] = status
            jvars["sgeid"] = sgeid
            jvars["creation"] = creation
            jvars["errstatus"] = errstatus
            self.update_ticket(jvars, ticket)

            # Create archive of data and remove
            #location = os.path.dirname(self.location_translate(ticket))
            #archive = shutil.make_archive(location, 'gztar', location)
            #shutil.rmtree(location)
            self.logger.debug("CLEANUP: {}, {}, {}".format(jobid, sgeid, username))

            # Remove from table
            with self.db as db:
                db.lock()
                db.delete(jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Clean Job Error", jobid, ticket)

    def failed(self, data):
        """
            Job ran but failed
            Send error message to user
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        try:
            try:
                if sgeid is not None:
                    self.sge.qdel(sgeid)
            except KeyError:
                pass

            # Load the job ticket
            jvars = self.load_ticket(ticket)

            # Write error message to resultfile
            with codecs.open(jvars["resultfile"], "w", "utf-8") as f:
                if errstatus is not None:
                    f.write("{}".format(errstatus))
                    self.logger.debug("FAILED: {}, {}".format(jobid, errstatus))
                else:
                    with codecs.open("{}.e{}".format(jvars["scriptname"], sgeid), "r", "utf-8") as fe:
                        f.write(fe.read())
                        fe.seek(0)
                        self.logger.debug("FAILED: {}, {}".format(jobid, fe.read()))

            # Send error message back to user and mark stale
            upload = Uploader(jvars["postresult"], jvars["resultfile"], "ERROR", "S", jobid,
                    self.location_translate(ticket), self.config['jobsdb'], self.logger)
            self.uploader[jobid] = upload
            self.uploader[jobid].start()

            # Mark job is uploading
            with self.db as db:
                db.lock()
                db.update("status", "U", jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Failed Job Error", jobid, ticket)

    def error(self, data):
        """
            Job has been marked in error
            Try to communicate the error to the user
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        try:
            # Load the job ticket
            jvars = self.load_ticket(ticket)

            # See if the resultfile exists
            if "resultfile" not in jvars:
                now_name = self.temp_name()
                job_name = "{}.{}".format(username, now_name)
                real_dir = os.path.dirname(self.location_translate(ticket))
                script_name = os.path.join(real_dir, "{}.sh".format(job_name))
                jvars["resultfile"] = "{}.result".format(script_name)
                self.update_ticket(jvars, ticket)

            self.logger.debug("Writing to: {}".format(jvars["resultfile"]))
            # Write error message to resultfile
            with codecs.open(jvars["resultfile"], "w", "utf-8") as f:
                f.write("{}".format(errstatus))
            self.logger.debug("ERROR: {}, {}".format(jobid, errstatus) )

            # Send error message back to user and mark stale
            upload = Uploader(jvars["postresult"], jvars["resultfile"], "ERROR", "S", jobid,
                    self.location_translate(ticket), self.config["jobsdb"], self.logger)
            self.uploader[jobid] = upload
            self.uploader[jobid].start()

            # Mark job is uploading
            with self.db as db:
                db.lock()
                db.update("status", "U", jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Error Job Error", jobid, ticket)

    def stale(self, data):
        """
            Job is stale
            Check it waiting time is up and if we should remove it from the db
        """
        jobid, username, ticket, status, sgeid, creation, errstatus = data
        try:
            # Load the job ticket
            jvars = self.load_ticket(ticket)
            self.logger.debug("STALE: {}".format(jobid))
            if "touched" not in jvars:
                jvars["touched"] = time.time()
                self.update_ticket(jvars, ticket)

            dt = time.time() - float(jvars["touched"])
            if dt > STALE_TIME:
                # Mark job for deletion
                self.logger.debug("STALE: removing {}".format(jobid))
                with self.db as db:
                    db.lock()
                    db.update("status", "X", jobid)

        except Exception as e:
            # Something went wrong
            self.set_error(e, "Stale Job Error", jobid, ticket)

    def set_error(self, exc, message, jobid, ticket):
        """
            An error occurred while processing a job
            Set and save error
        """
        self.logger.error("{} : {} : {}".format(jobid, message, repr(exc)))
        # Something went wrong
        with self.db as db:
            db.lock()
            db.update("status", "E", jobid)
            db.update("errstatus", "{}: {}".format(message, repr(exc)), jobid)
        jvars = self.load_ticket(ticket)
        jvars["touched"] = time.time()
        jvars["error"] = "{}: {}".format(message, repr(exc))
        self.update_ticket(jvars, ticket)

    def shutdown(self):
        """
            Shutdown upload and download threads
        """
        #TODO: check if queues are empty
        self.clean_final(self.downloader)
        self.clean_final(self.uploader)

    def clean_final(self, queue):
        """
            Run through the queue and shutdown each instance
        """
        for jobid in queue.keys():
            self.logger.debug("CLEAN_FINAL: stop {}".format(jobid))
            queue[jobid].stop()

        while True:
            for jobid, inst in queue.items():
                self.logger.debug("CF: {}, {}".format(jobid, inst.done))
                if inst.done:
                    inst.join()
                    del queue[jobid]
            if not bool(queue):
                break
            time.sleep(0.1)


class JobsDB(sqlite.Connection):
    def lock(self):
        self.execute("BEGIN IMMEDIATE")

    def get_jobs(self):
        row = self.execute("SELECT * FROM jobs")
        if row is None:
            return []
        return map(dict, row)

    def update(self, key, value, jobid):
        self.execute("UPDATE jobs SET {}=? WHERE jobid=?".format(key), (value, jobid))

    def delete(self, jobid):
        self.execute("DELETE FROM jobs WHERE jobid=?", (jobid,))

    def adminlockstatus(self):
        row = self.execute("SELECT value FROM jobCtrl WHERE key=?", ('lock',)).fetchone()
        if row is None:
            return ['ERROR: key not found']
        return list(row)

if __name__ == "__main__":
    pass

