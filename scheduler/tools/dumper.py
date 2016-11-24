#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import time
import BaseHTTPServer
import cgi
import cStringIO

HOST_NAME = '10.0.0.11' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 9000 
TEMP_FILE = 'tmp.dump'

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(s):
        length = int(s.headers['Content-Length'])
        data = s.rfile.read(length)
        print(s.headers)
        with open(TEMP_FILE, 'wb') as f:
            f.write(data)

        out = {}
        (header, bound) = s.headers['Content-Type'].split('boundary=')
        form_raw = cgi.parse_multipart(cStringIO.StringIO(data), {'boundary': bound})
        #print("{}".format(form_raw))

        for key in form_raw.keys():
            out[key] = form_raw[key][0]
        #print("Data keys: {}".format(out.keys()))

        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.send_header('Access-Control-Allow-Origin', '*')
        s.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
        s.send_header("Access-Control-Allow-Headers", "Content-Type")
        s.end_headers()

    def do_OPTIONS(s):
        s.send_response(200, "ok")
        s.send_header('Access-Control-Allow-Origin', '*')
        s.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
        s.send_header("Access-Control-Allow-Headers", "Content-Type")
        s.end_headers()


if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

