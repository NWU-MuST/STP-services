#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import json
import os
import codecs
from msg_queue import Message
from logger import Logger

class Router:

    def __init__(self, config_file):
        self._config_file = config_file
        self._config = {}
        self._routing = {}
        self._service_config = {}
        self._msg = None
        self._logger = None

    def load(self):
        """
            High-level services load
        """
        self.init_logger()
        self.load_config()
        self.clear_routing()
        self.load_services()
        self.init_msgq()

    def init_logger(self):
        """
            Create logger
        """
        if self._logger is None:
            self.__base_logger = Logger(self._config_file)
            self.__base_logger.new_logger('root')
            self._logger = self.__base_logger.get_logger('base')

    def init_msgq(self):
        """
            Create messaging queue
        """
        if self._msg is None:
            self._msg = Message(self._logger.getChild('msg'), self._config['queue']['maxsize'])

    def load_config(self):
        """
            Load config containing detail's of services
        """
        self._config = {}
        with codecs.open(self._config_file, 'r', 'utf-8') as f:
            self._config = json.load(f)

    def clear_routing(self):
        """
            Clear the routing table i.e. services redirecting
        """
        if not self._routing:
            for service in self._routing:
                del self._routing[service]
        self._routing = {}

    def load_services(self):
        """
            Load services i.e. service modules - not initialized
        """
        for service in self._config["services"]:
            _temp = __import__(self._config["services"][service]["module"],
                 fromlist=[self._config["services"][service]["class"]])

            self._routing[self._config["services"][service]["uri"]] =\
                getattr(_temp, self._config["services"][service]["class"])

            self._service_config[self._config["services"][service]["uri"]] =\
                self._config["services"][service]["config"]

    def get(self, env):
        """
            Process GET resquest.
            Valid requests are: results, status, options
        """
        (junk, service, request, msg_id) = env['PATH_INFO'].split('/')

        if request not in ['result', 'status', 'options']:
            return '405 Method Not Allowed', json.dumps({'message' : 'GET service does not support: %s' % request})

        if service not in self._routing:
            return '405 Method Not Allowed', json.dumps({'message' : 'GET service not supported: %s' % service})

        mod = getattr(self._msg, request)
        feedback = mod(msg_id)
        return '200 OK', json.dumps({'message' : feedback})

    def post(self, path):
        """
            Process POST resquest.
            Valid requests are: clear
        """
        (junk, service, request, msg_id) = env['PATH_INFO'].split('/')

        if request not in ['clear']:
            return '405 Method Not Allowed', json.dumps({'message' : 'POST service does not support: %s' % request})

        if service not in self._routing:
            return '405 Method Not Allowed', json.dumps({'message' : 'POST service not supported: %s' % service})

        mod = getattr(self._msg, request)
        feedback = mod(msg_id)
        return '200 OK', json.dumps({'message' : feedback})

    def put(self, env):
        """
            Process PUT request
            Used to add a job via a service
        """
        (junk, service, request, username) = env['PATH_INFO'].split('/')

        if request not in ['addjob']:
            return '405 Method Not Allowed', json.dumps({'message' : 'PUT service does not support: %s' % request})

        if service not in self._routing:
            return '405 Method Not Allowed', json.dumps({'message' : 'PUT service not supported: %s' % service})

        job = self._routing[service](self._service_config[service], self._logger.getChild(username), env['wsgi.input'].read())
        msg_id = self._msg.add_job(job)
        return '200 OK', json.dumps({'task_id' : msg_id})

    def delete(self, env):
        """
            Process DELETE resquest.
            Valid requests are: delete
        """
        (junk, service, request, msg_id) = env['PATH_INFO'].split('/')

        if request not in ['delete']:
            return '405 Method Not Allowed', json.dumps({'message' : 'DELETE service does not support: %s' % request})

        if service not in self._routing:
            return '405 Method Not Allowed', json.dumps({'message' : 'DELETE service not supported: %s' % service})

        mod = getattr(self._msg, request)
        feedback = mod(msg_id)
        return '200 OK', json.dumps({'message' : feedback})

    def options(self):
        """
            Process OPTIONS request
            Return a list of possible services
        """
        opts = self._routing.keys()
        return ','.join(opts)

    def shutdown(self):
        """
            Shutdown the router and message queue
        """
        self._msg.shutdown_queue()      

    def msg_stats(self):
        return self._msg.queue_stats()

    def job_stats(self, job_id):
        return self._msg.job_stats(job_id)

