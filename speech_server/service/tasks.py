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

class Tasks(auth.UserAuth):

    def __init__(self, config_file):
        with open(config_file) as infh:
            self._config = json.loads(infh.read())

    def add_task(self, request):
        """
            Add task to the queue
        """
        #AUTHORISE REQUEST
        username = auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        with sqlite.connect(self._config['tasksdb']) as db_conn:
            db_curs = db_conn.cursor()

            # Generate new task id
            taskid = str(uuid.uuid4())
            taskid = 't%s' % taskid.replace('-', '')

            # Write the task information to task file
            taskinfo = os.path.join(self._config["storage"], username, datetime.datetime.now().strftime('%Y-%m-%d'))
            if not os.path.exists(taskinfo):
                os.makedirs(taskinfo)

            taskinfo = os.path.join(taskinfo, taskid)
            f = open(taskinfo, 'wb')
            f.write(json.dumps(request))
            f.close()

            # Add task entry to table
            db_curs.execute("INSERT INTO tasks (taskid, username, taskinfo, status, creation) VALUES(?,?,?,?,?)",
            (taskid, username, taskinfo, 'P', time.time()))
            db_conn.commit()

            return {'taskid' : taskid}

    def delete_task(self, request):
        """
            Delete task from the queue if the task is not running
        """
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        with sqlite.connect(self._config['tasksdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Delete task
            db_curs.execute("SELECT * FROM tasks WHERE taskid='%s'" % request['taskid'])
            task_info = db_curs.fetchone()

            # See if task exists
            if task_info is None:
                raise NotFoundError('Task does not exist')

            # If task is running then can't delete
            if task_info[-3] == 'R':
                raise ForbiddenError('Task is busy running')

            # Remove task from task table
            db_curs.execute("DELETE FROM tasks WHERE taskid='%s'" % request['taskid'])
            db_conn.commit()

        return 'Task deleted'

    def query_task(self, request):
        """
            Query task and return information
        """
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        with sqlite.connect(self._config['tasksdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Delete task
            db_curs.execute("SELECT * FROM tasks WHERE taskid='%s'" % request['taskid'])
            task_info = db_curs.fetchone()
            print(task_info)
            # See if task exists
            if task_info is None:
                raise NotFoundError('Task does not exist')

            # Re-format info
            info = {'taskid' : task_info[0], 'username' : task_info[1], 'status' : task_info[3], 'creation' : task_info[4]}
            f = open(task_info[2], 'rb')
            data = f.read()
            f.close()
            info[task_info[2]] = data

            return info

    def user_tasks(self, request):
        """
            Query all tasks belonging to the user and return information
        """
        #AUTHORISE REQUEST
        username = auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        with sqlite.connect(self._config['tasksdb']) as db_conn:
            db_curs = db_conn.cursor()
            # Delete task
            db_curs.execute("SELECT * FROM tasks WHERE username='%s'" % username)
            task_info = db_curs.fetchall()
            print(task_info)
            # See if task exists
            if task_info is None:
                raise NotFoundError('Task does not exist')

            # Re-format the info for the user
            info = {}
            info["tasks"] = []
            for taskid, username, taskinfo, status, creation in task_info:
                info["tasks"].append((taskid, username, status, creation))
                f = open(taskinfo, 'rb')
                data = f.read()
                f.close()
                info[taskid] = data

            return info

