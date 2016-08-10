#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import sys
import os
import uwsgi
import json
import logging
import logging.handlers

from dispatcher import Dispatch
from service.httperrs import *

#SETUP LOGGING

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

LOGNAME = "SPSRV"
LOGFNAME = os.path.join(os.getenv("PERSISTENT_FS"), "speechserver.log")
LOGLEVEL = logging.DEBUG
try:
    fmt = "%(asctime)s [%(levelname)s] %(name)s in %(funcName)s(): %(message)s"
    LOG = logging.getLogger(LOGNAME)
    formatter = CustomFormatter(fmt)
    ofstream = logging.handlers.TimedRotatingFileHandler(LOGFNAME, when="D", interval=1, encoding="utf-8")
    ofstream.setFormatter(formatter)
    LOG.addHandler(ofstream)
    LOG.setLevel(LOGLEVEL)
    #If we want console output:
    # console = logging.StreamHandler()
    # console.setFormatter(formatter)
    # LOG.addHandler(console)
except Exception as e:
    print("FATAL ERROR: Could not create logging instance: {}".format(e), file=sys.stderr)
    sys.exit(1)

router = Dispatch(os.environ['services_config'])
router.load()

# Perform cleanup when server shutdown
def app_shutdown():
    print('Shutting down subsystem instance...')
    sys.stdout.flush()
    router.shutdown()

uwsgi.atexit = app_shutdown

# Entry point
def application(env, start_response):

    try:
        if env['REQUEST_METHOD'] == 'GET':
            (status, response) = router.get(env)
            response_header = [('Content-Type','application/json'), ('Content-Length', str(len(response)))]
            start_response('200 OK', response_header)
            return [response]

        elif env['REQUEST_METHOD'] == 'POST':
            (status, response) = router.post(env)
            response_header = [('Content-Type','application/json'), ('Content-Length', str(len(response)))]
            start_response('200 OK', response_header)
            return [response]

        else:
            raise MethodNotAllowedError("Supported methods are: GET or POST")

    except BadRequestError as e:
        response, response_header = build_json_response(e)
        start_response("400 Bad Request", response_header)
        return [response]
    except NotAuthorizedError as e:
        response, response_header = build_json_response(e)
        start_response("401 Not Authorized", response_header)
        return [response]
    except ForbiddenError as e:
        response, response_header = build_json_response(e)
        start_response("403 Forbidden", response_header)
        return [response]
    except NotFoundError as e:
        response, response_header = build_json_response(e)
        start_response("404 Not Found", response_header)
        return [response]
    except MethodNotAllowedError as e:
        response, response_header = build_json_response(e)
        start_response("405 Method Not Allowed", response_header)
        return [response]
    except ConflictError as e:
        response, response_header = build_json_response(e)
        start_response("409 Conflict", response_header)
        return [response]
    except TeapotError as e:
        response, response_header = build_json_response(e)
        start_response("418 I'm a teapot", response_header)
        return [response]
    except NotImplementedError as e:
        response, response_header = build_json_response(e)
        start_response("501 Not Implemented", response_header)
        return [response]
    except Exception as e:
        response, response_header = build_json_response(e)
        start_response("500 Internal Server Error", response_header)
        return [response]

