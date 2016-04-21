#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function #Py2

import threading
import Queue
import time
import os
import uuid
import json

WORKER_SLEEP = 0.02
RESULT_SLEEP = 0.02

class Worker(threading.Thread):
    """
        Worker thread that processes jobs in queue
        Job is retrieved and Process is called to process the job
        A Process method is called via the routing table
    """
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self._queue = queue
        self._running = True

    def run(self):
        while self._running:
            try:
                (message_id, task) = self._queue.get(False)
                task.run()
                self._queue.task_done()
            except Queue.Empty:
                pass

            if self._queue.empty():
                time.sleep(WORKER_SLEEP)

    def stop(self):
        self._running = False



class Message:

    def __init__(self, logger, maxsize):
        self._logger = logger
        self._jobs = {}
        self._queue = Queue.Queue(maxsize=maxsize)
        self._worker = Worker(self._queue)
        self._worker.start()

    def add_job(self, task):
        """
            Add job to queue
        """
        message_id = str(uuid.uuid4())
        self._queue.put((message_id, task))
        self._jobs[message_id] = task
        return message_id

    def result(self, message_id):
        """
            Return result
            TODO: maybe remove??
        """
        if message_id in self._jobs:
            return self._jobs[message_id].result()

    def delete(self, message_id):
        """
            Delete request service
        """
        print(self._jobs)
        if message_id in self._jobs:
            msg = self._jobs[message_id].delete()
            del self._jobs[message_id]
            print(self._jobs)
            return msg

    def status(self, message_id):
        """
            Status of request
        """
        if message_id in self._jobs:
            return self._jobs[message_id].status()

    def options(self, message_id):
        """
            Options supported by service
        """
        if message_id in self._jobs:
            return self._jobs[message_id].options()

    def shutdown_queue(self):
        """
            Shutdwown the queue and worker
        """
        self._queue.join()
        self._worker.stop()
        self._worker.join()

    def queue_stats(self):
        data = {}
        data['queuesize'] = self._queue.qsize()
        data['queuejobs'] = self._jobs.keys()
        return json.dumps(data)

    def job_stats(self, job_id):
        if job_id in self._jobs:
            return self._jobs[job_id].stats()
        return json.dumps({'error' : 'job not found: %s' % job_id})

if __name__ == "__main__":
    pass

