#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function #Py2

import time
import os
import sys
import json
import argparse
import subprocess
import threading
import logging
import logging.handlers
from core.jobs import Jobs

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

if __name__ == "__main__":
    # Setup logger
    LOGNAME = "SCHED"
    LOGFNAME = "scheduler.log"
    LOGLEVEL = logging.DEBUG
    try:
        fmt = "%(asctime)s [%(levelname)s] %(threadName)s %(name)s in %(funcName)s(): %(message)s"
        LOG = logging.getLogger(LOGNAME)
        formatter = CustomFormatter(fmt)
        ofstream = logging.handlers.TimedRotatingFileHandler(LOGFNAME, when="D", interval=1, encoding="utf-8")
        ofstream.setFormatter(formatter)
        LOG.addHandler(ofstream)
        LOG.setLevel(LOGLEVEL)

        #If we want console output:
        #console = logging.StreamHandler()
        #console.setFormatter(formatter)
        #LOG.addHandler(console)
    except Exception as e:
        print("FATAL ERROR: Could not create logging instance: {}".format(e), file=sys.stderr)
        sys.exit(1)

    #Check application arguments
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("config", metavar="CONFIG", type=str, help="Config filename.")
    args = parser.parse_args()

    # Check SGE running
    FNULL = open(os.devnull, 'w')
    status = subprocess.call("qstat -help", stdout=FNULL, stderr=FNULL, shell=True)
    if status != 0:
        raise RuntimeError("SGE not running: qstat no working!!!")
    status = subprocess.call("qsub -help", stdout=FNULL, stderr=FNULL, shell=True)
    if status != 0:
        raise RuntimeError("SGE not running: qsub no working!!!")
    FNULL.close()

    # Load Config
    config_file = args.config
    config = json.load(open(config_file, 'rb'))
    timing = float(config["SYNC_TIME"])
    timing = 2.0
    jobs = Jobs(config, LOG)

    try:
        #Main loop
        while True:
            jobs.sync()
            time.sleep(timing)
    except Exception as e:
        print(repr(e))
        #Cleanup
        jobs.shutdown()

