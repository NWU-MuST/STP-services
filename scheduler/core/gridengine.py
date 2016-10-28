#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import subprocess
import re
import getpass

class SGE:

    def __init__(self, logger):
        self._logger = logger
        self._sge_state = ["qw", "r", "Eqw", "S"]

    def query(self, jobid):
        """
            Query job state
            Using combination of qstat, qacct
        """
        self._logger.info("Querying SGE queue for job - {}".format(jobid))
        cmd = "qstat -j {}".format(jobid)
        status, stdout, stderr = self._call(cmd)

        if status == 0:
            # Job in qstat queue or running
            return self._get_state(jobid)
        else:
            match = re.search("Following jobs do not exist:\s*(\d+)", stderr.replace("\n"," "))
            if match is not None:
                # Job might be finished - check status
                return self._get_status(jobid)

            # Something unexpected happened
            self._logger.error("query command error: {}".format(stderr.strip()))
            raise RuntimeError("query command error")

    def _get_state(self, jobid):
        """
            Job running or queued
        """
        self._logger.info("Querying SGE job state - {}".format(jobid))
        cmd = "qstat | grep -P '^\s+{} ' ".format(jobid)
        status, stdout, stderr = self._call(cmd)

        if status == 0:
            # Extract state
            toks = stdout.strip().split()
            (jobID, prior, name, user, state) = toks[:5]
            if state not in self._sge_state:
                self._logger.error("Unknown state {} for job {}".format(state, jobid))
                raise RuntimeError("Unknown state - {}".format(state))
            return state
        else:
            if len(stdout.strip()) == 0 and len(stderr.strip()) == 0:
                # Job missing: go check finish status
                return self._get_status(jobid)

            self._logger.error("qstat command error: {}, {}".format(stdout.strip(), stderr.strip()))
            raise RuntimeError("qstat command error")

    def _get_status(self, jobid):
        """
        """
        self._logger.info("Query accounting SGE system for job - {}".format(jobid))
        cmd = "qacct -j {}".format(jobid)
        status, stdout, stderr = self._call(cmd)

        if status == 0:
            match = re.search("\s+failed\s+(.+?)\s+", stdout.replace("\n", " "))
            if match is None:
                self._logger.error("Failed to query failure state of job {}".format(jobid))
                raise RuntimeError("Failed to query failure state")
            failed_state = match.group(1)

            match = re.search("\s+exit_status\s+(\d+)\s+", stdout.replace("\n", " "))
            if match is None:
                self._logger.error("Failed to query exit status of job {}".format(jobid))
                raise RuntimeError("Failed to query exit status")
            exit_status = match.group(1)

            if failed_state == "0" and exit_status == "0":
                return "D"
            else:
                return "F"
        else:
            match = re.search("error: job id (\d+?) not found", stderr)
            if match is not None:
                self._logger.error("Job {} does not exist".format(jobid))
                raise KeyError("Job not found")

            return self._get_zombie(jobid)

    def _get_zombie(self, jobid):
        """
            Check if job in zombie queue
        """
        cmd = "qstat -s z | grep -P '^\s+{}\s".format(jobid)
        status, stdout, stderr = self._call(cmd)

        if status == 0:
            if len(stdout) > 0:
                return "Z"
            else:
                self._logger.error("qacct command error:{}".format(stderr.strip()))
                raise RuntimeError("qacct command error")
        else:
            self._logger.error("qacct command error:{}".format(stderr.strip()))
            raise RuntimeError("qacct command error")

    def qsub(self, script_name):
        """
            Submit job to SGE via qsub
            script_name should be a Bash file that can be submitted to SGE
            Returns jobid
            RuntimeError for all other errors
        """
        self._logger.info("Submitting job {}".format(script_name))
        cmd = "qsub {}".format(script_name)
        status, stdout, stderr = self._call(cmd)

        if status == 0:
            match = re.search("Your job (\d+?) (.+?) has been submitted", stdout)
            if match is None:
                self._logger.error("Unexpected SGE format for qsub: {}".format(stdout))
                raise RuntimeError("Unexpected SGE format for qsub - can't extract jobid")
            self._logger.info("Returning jobid - {}".format(match.group(1)))
            return match.group(1)
        else:
            self._logger.error("qsub command error: {}".format(stderr.strip()))
            raise RuntimeError("qsub command error")

    def qdel(self, jobid):
        """
            Mark SGE job for deletion
            Returns confirmation string
            KeyError if job does not exist
            RuntimeError for all other errors
        """
        self._logger.info("Marking job {} for deletion".format(jobid))
        cmd = "qdel {}".format(jobid)
        status, stdout, stderr = self._call(cmd)

        if status == 0:
            match_1 = re.search("{} has deleted job (\d+?)".format(getpass.getuser()), stdout)
            match_2 = re.search("job (\d+?) is already in deletion", stdout)
            match_3 = re.search("{} has registered the job (\d+) for deletion".format(getpass.getuser()), stdout)

            if all(v is None for v in [match_1, match_2, match_3]):
                self._logger.error("Unexpected SGE format for qdel: {}".format(stdout))
                raise RuntimeError("Unexpected SGE format for qdel")
            return "Deleting job {}".format(jobid)
        else:
            match = re.search('denied: job "(\d+?)" does not exist', stdout)
            if match is not None:
                self._logger.error("Job {} does not exist".format(jobid))
                raise KeyError("Job not found")

            self._logger.error("qdel command error: {}".format(stderr.strip()))
            raise RuntimeError("qdel command error")

    def _call(self, cmd):
        """
            Make a system call to the SGE using Subprocess
            Returns exit code, stdout and stderr of sub-process or RuntimeError
        """
        try:
            self._logger.info("Making a system call - {}".format(cmd))
            proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            return proc.returncode, stdout, stderr
        except Exception as e:
            self._logger.error("Subprocess error: {}".format(repr(e)))
            raise RuntimeError(repr(e))

if __name__ == "__main__":
    pass

