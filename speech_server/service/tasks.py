#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function #Py2

import json
import time
import uuid
import base64
import admin
import auth

try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

from httperrs import NotAuthorizedError, ConflictError

class Admin(admin.Admin):
    pass

class Tasks(auth.UserAuth):

    def __init__(self, config_file):
        with open(config_file) as infh:
            self._config = json.loads(infh.read())

    def add_task(self, request)
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        raise NotImplementedError

    def delete_task(self, request)
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        raise NotImplementedError

    def query_task(self, request):
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        raise NotImplementedError

    def user_tasks(self, request):
        #AUTHORISE REQUEST
        auth.token_auth(request["token"], self._config["authdb"])
        #EXECUTE REQUEST
        raise NotImplementedError

