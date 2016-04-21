#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import threading
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
from logger import Logger

class HttpServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        cts = self.path.count('/')
        if cts == 1:
            (junk, query) = self.path.split('/')
        elif cts == 2:
            (junk, query, job_id) = self.path.split('/')
        else:
            msg = 'Bad query string format: %s' % self.path
            self.send_response(400, msg)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Content-length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        msg = ''
        if query == 'queue':
            msg = self.server.router.msg_stats()
        elif query == "job":
            msg = self.server.router.job_stats(job_id)
        else:
            msg = 'Bad query: %s' % query
            self.send_response(400, msg)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Content-length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        self.send_response(200, msg)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

    def log_message(self, format, *args):
        self.server._logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(),format%args))


class CustomHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, router, config_file):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.router = router

        self._base_logger = Logger(config_file)
        self._base_logger.new_logger('monitor')
        self._logger = self._base_logger.get_logger('base')


class MonitorServer(threading.Thread):
    def __init__(self, host, port, router, config_file):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.server = None
        self.router = router
        self.config_file = config_file
         
    def run(self):
        self.server = CustomHTTPServer((self.host, self.port), HttpServerHandler, self.router, self.config_file)
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()

if __name__ == "__main__":
    pass

