#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals #Py2

import os
import sys
import logging

NAME = os.path.basename(sys.argv[0])
DEF_LOG = os.path.join(os.environ.get("MODEL_ROOT"), "kaldi_align.log")
DEF_LOGLEVEL = 20
try:
    fmt = "%(asctime)s [%(levelname)s] " + NAME + ": %(message)s"
    LOG = logging.getLogger(NAME)
    formatter = logging.Formatter(fmt)
    ofstream = logging.FileHandler(DEF_LOG, "a")
    ofstream.setFormatter(formatter)
    LOG.addHandler(ofstream)
    LOG.setLevel(DEF_LOGLEVEL)
    # Console output.
    # console = logging.StreamHandler()
    # console.setFormatter(formatter)
    # LOG.addHandler(console)
except Exception, e:
    print("ERROR: Could not create logging instance.\n\tReason: %s" %e)
    sys.exit(1)
