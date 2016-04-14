#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function, with_statement #Py2

import json
import time
from monitor_service import MonitorService

class ASR(MonitorService):

	def __init__(self, config_file, logger, request):

		MonitorService.__init__(self)
		self._config_file = config_file
		self._logger = logger
		self._request = request
		self._status = 'Queued'
		self.created()
		self._logger.info('Queued')

	def status(self):
		return self._status

	def result(self):
		self._logger.info('result')
		return 'result'

	def delete(self):
		self._logger.info('delete')
		return 'clear'

	def options(self):
		return self._config_file

	def run(self):
		self.job_started()
		self._status = 'Running'
		self._logger.info('Running')
		time.sleep(5)
		self._status = 'Done'
		self._logger.info('Done')
		self.job_end()

if __name__ == "__main__":
	pass

