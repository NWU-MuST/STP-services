#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import os
import uwsgi
import json
from router import Router
from msg_queue import Message
from monitor_server import MonitorServer


service_router = Router(os.environ['services_config'])
service_router.load()

ms = MonitorServer('127.0.0.1', 8000, service_router, os.environ['services_config'])
ms.start()

# Perform cleanup when server shutdown
def app_shutdown():
	print('Shutting down subsystem instance...')
	sys.stdout.flush()
	service_router.shutdown()
	ms.stop()

uwsgi.atexit = app_shutdown


# Entry point
def application(env, start_response):

	print(env)
	if env['REQUEST_METHOD'] == 'GET':
		(status, response) = service_router.get(env)
		response_header = [('Content-Type','application/json'), ('Content-Length', str(len(response)))]
		start_response('200 OK', response_header)
		return [response]

	elif env['REQUEST_METHOD'] == 'POST':
		service_router.post(env)

	elif env['REQUEST_METHOD'] == 'PUT':
		(status, response) = service_router.put(env)
		response_header = [('Content-Type','application/json'), ('Content-Length', str(len(response)))]
		start_response('200 OK', response_header)
		return [response]

	elif env['REQUEST_METHOD'] == 'DELETE':
		(status, response) = service_router.delete(env)
		response_header = [('Content-Type','application/json'), ('Content-Length', str(len(response)))]
		start_response('200 OK', response_header)
		return [response]

	elif env['REQUEST_METHOD'] == 'OPTIONS':
		services = service_router.options()
		response_header = [('Content-Type','text/plain'), ('Content-Length', '0'), ('Allow', str(services))]
		#str(len(services))
		start_response('200 OK', response_header)
		return ['']
	else:
		msg = json.dumps({'message' : 'Error: use either GET, PUT or OPTIONS'})
		response_header = [('Content-Type','application/json'), ('Content-Length', str(len(msg)))]
		start_response('405 Method Not Allowed', response_header)
		return [msg]

