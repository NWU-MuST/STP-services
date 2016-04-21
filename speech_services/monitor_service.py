#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import datetime
import json
import resource

class MonitorService:

    def __init__(self):
        self._queue_time = None
        self._start_time = None
        self._done_time = None

        self._usage_points = [('ru_utime', 'User time'),
        ('ru_stime', 'System time'),
        ('ru_maxrss', 'Max. Resident Set Size'),
        ('ru_ixrss', 'Shared Memory Size'),
        ('ru_idrss', 'Unshared Memory Size'),
        ('ru_isrss', 'Stack Size')]

    def created(self):
        """
            Job added to queue
        """
        self._queue_time = datetime.datetime.now()

    def job_started(self):
        """
            Job started
        """
        self._start_time = datetime.datetime.now()

    def job_end(self):
        """
            Job done
        """
        self._done_time = datetime.datetime.now()

    def stats(self):
        """
            Return service stats
        """
        data = {}
        data['queuetime'] = str(datetime.datetime.now() - self._queue_time)
        data['starttime'] = str(self._start_time)
        data['donetime'] = str(self._done_time)
        data['runtime'] = str(self._done_time - self._start_time)

        usage = resource.getrusage(resource.RUSAGE_SELF)
        for name, desc in self._usage_points:
            data[desc] = getattr(usage, name)

        return json.dumps(data)

