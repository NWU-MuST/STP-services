#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function #Py2

import time
import os
import json
import argparse
import subprocess
import drmaa
import threading

from core.jobs import Jobs


class Daemon(threading.Thread):

    def __init__(self, timing, config_file):
        threading.Thread.__init__(self)
        self.running = True
        self.timing = timing
        self.config_file = config_file
        self.jobs = Jobs(config_file)
        self.sge = drmaa.Session()
        self.sge.initialize()
        self.sge_jobs = {}

    def run(self):
        while self.running:
            self.jobs.sync(self.sge, self.sge_jobs)
            #TODO: if SGE empty shutdown session and restart
            time.sleep(self.timing)
        self.jobs.shutdown()
        self.sge.exit()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("config", metavar="CONFIG", type=str, help="Config filename.")
    args = parser.parse_args()
    config_file = args.config
    config = json.load(open(config_file, 'rb'))

    # Check SGE running
    FNULL = open(os.devnull, 'w')
    status = subprocess.call("qstat -help", stdout=FNULL, stderr=FNULL, shell=True)
    if status != 0:
        raise RuntimeError("SGE not running: qstat no working!!!")
    status = subprocess.call("qsub -help", stdout=FNULL, stderr=FNULL, shell=True)
    if status != 0:
        raise RuntimeError("SGE not running: qsub no working!!!")
    FNULL.close()

    with open(config["jobsdb"], "rb") as f:
        pass

    daemon = Daemon(float(config["SYNC_TIME"]), config_file)
    try:
        daemon.start()
        while True:
            time.sleep(1)
    except:
        daemon.stop()
        daemon.join()

