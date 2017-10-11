import time
import urllib.request
import urllib.error
import urllib.parse
import config
import logging
from utils import log_exception

class Market():
	def __init__(self):
		self.name = self.__class__.__name__
		self.depth_updated = 0
		self.update_rate = 2

	def get_depth(self, pair):
		timediff = time.time() - self.depth_updated
		if timediff > self.update_rate:
			self.ask_update_depth(pair)
		timediff = time.time() - self.depth_updated

		if timediff > config.market_expiration_time:
			logging.warn('Market: %s order book is expired' % self.name)
			self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [
			{'price': 0, 'amount': 0}]}
		return self.depth	

	def ask_update_depth(self, pair):
		try:
			self.update_depth(pair)
			self.depth_updated = time.time()
		except (urllib.error.HTTPError, urllib.error.URLError) as e:
			logging.error("HTTPError, can't update market: %s" % self.name)
			log_exception(logging.DEBUG)
		except Exception as e:
			logging.error("Can't update market: %s - %s" % (self.name, str(e)))	
			log_exception(logging.DEBUG)	
		
	def update_depth(self):
		pass

	def buy(self, price, amount):
		pass

	def sell(self, price, amount):
		pass				   



			
			

