import logging
from .observer import Observer

class Logger(Observer):
	def opportunity(self, item):
		logging.info('%s Amount %f Expected Profit %f' % (item['case'], item['amount'], item['profit']) )