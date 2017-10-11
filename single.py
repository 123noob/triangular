import config
import sys
import logging
import time
from concurrent.futures import ThreadPoolExecutor, wait


class Single():
	def __init__(self):
		self.observers = []
		self.init_market(config.market)
		self.init_observers(config.observers)
		self.symbol = 'bcc'
		self.currency_pairs = config.currency_pairs[self.symbol]
		self.depths = {}
		self.depths2 = {}
		self.threadpool = ThreadPoolExecutor(max_workers=3)

	def init_market(self, market):
		try:
			exec('import public_markets.' + market.lower())
			m = eval('public_markets.' + market.lower() + '.' + market + '()' )
			self.market = m
		except(ImportError, AttributeError) as e:
			print('%s market name is invalid' % m)

	def init_observers(self, _observers):
		for observer_name in _observers:	
			try:
				exec('import observers.' + observer_name.lower())
				observer = eval('observers.' + observer_name.lower() + '.' + observer_name + '()')
				self.observers.append(observer)
			except(ImportError, AttributeError) as e:
				print('%s observer name is invalid' % observer_name)		

	def __get_depth(self, pair, depths):
		depths[pair] = self.market.get_depth(pair)		

	def update_depths(self):
		depths = {}	
		futures = []
		for pair in self.currency_pairs:
			futures.append(self.threadpool.submit(self.__get_depth, pair, depths))
		wait(futures, timeout=5)
		return depths		

	def ask_volume(self, orders, amount):
		vol = 0
		value = 0

		i = 0
		while i < len(orders['asks']) and value < amount:
			this_value = min(orders['asks'][i]['price'] * orders['asks'][i]['amount'], amount - value)
			this_vol = this_value / orders['asks'][i]['price']
			value += this_value
			vol += this_vol

			i += 1

		return vol		

	def bid_volume(self, orders, amount):	
		vol = 0
		value = 0

		i = 0
		while i < len(orders['bids']) and value < amount:
			this_value = min(orders['bids'][i]['amount'], amount - value)
			this_vol = this_value * orders['bids'][i]['price']
			value += this_value
			vol += this_vol

			i += 1

		return vol	

	def best_ask(self, orders):
	    return orders['asks'][0]['price']

	def best_bid(self, orders):
	    return orders['bids'][0]['price']    	

	def loop(self):
		while True:
			try:
				self.depths = self.update_depths()
				# time.sleep(0.1)
				# self.depths2 = self.update_depths()
				print(self.depths[self.currency_pairs[0]])
				# print(self.depths2[self.currency_pairs[0]])
				# sys.exit(0)
				btc_cny_orders = self.depths[self.currency_pairs[0]]
				cc_btc_orders = self.depths[self.currency_pairs[1]]
				cc_cny_orders = self.depths[self.currency_pairs[2]]

			except Exception as e:
				logging.error("Can't update depths: %s" % str(e))
				continue
			if btc_cny_orders and cc_btc_orders and cc_cny_orders:
				best_case = 0
				best_profit = 0
				best_amount = 0
				best_trades = {}

				amt = config.min_amount
				while amt <= config.max_amount:
					#Case 1: BTC -> CC -> CNY -> BTC
					c1_cc = self.ask_volume(cc_btc_orders, amt)
					c1_cny = self.bid_volume(cc_cny_orders, c1_cc)
					c1_btc = self.ask_volume(btc_cny_orders, c1_cny)

					c1_profit = c1_btc - amt
					c1_profit_percent = (c1_profit * 100) / amt

					if c1_profit > best_profit and c1_profit_percent > config.min_profit:
						best_case = 1
						best_profit = c1_profit
						best_amount = amt
						best_trades = [
						    {
							'pair':self.currency_pairs[1],
							'type':'buy',
							'amount':round(c1_cc, 4),
							'rate':round(self.best_ask(cc_btc_orders) * config.slippage, 6)
							},	
							{
							'pair':self.currency_pairs[2],
							'type':'sell',
							'amount':round(c1_cc, 4),
							'rate':round(self.best_bid(cc_cny_orders) / config.slippage, 2)
							},			
							{
							'pair':self.currency_pairs[0],
							'type':'buy',
							'amount':round(c1_btc, 4),
							'rate':round(self.best_ask(btc_cny_orders) * config.slippage, 2)
							},													
						]

					# Case 2: BTC -> CNY -> CC -> BTC
					c2_cny = self.bid_volume(btc_cny_orders, amt)
					c2_cc = self.ask_volume(cc_cny_orders, c2_cny)	
					c2_btc = self.bid_volume(cc_btc_orders, c2_cc)

					c2_profit = c2_btc - amt
					c2_profit_percent = (c2_profit * 100) / amt

					if c2_profit > best_profit and c2_profit_percent > config.min_profit:
						best_case = 2
						best_profit = c2_profit
						best_amount = amt
						best_trades = [
							{
								'pair':self.currency_pairs[0],
								'type':'sell',
								'amount':round(amt, 4),
								'rate':round(self.best_bid(btc_cny_orders) / config.slippage, 2)
							},	
							{
								'pair':self.currency_pairs[2],
								'type':'buy',
								'amount':round(c2_cc, 4),
								'rate':round(self.best_ask(cc_cny_orders) * config.slippage, 2)
							},	
							{
								'pair':self.currency_pairs[1],
								'type':'sell',
								'amount':round(c2_cc, 4),
								'rate':round(self.best_bid(cc_btc_orders) * config.slippage, 6)
							},	
						]

					amt += config.increment

				if best_case > 0:
					case = "btc -> " + self.symbol + " -> cny -> btc" if best_case == 1 else "btc -> cny -> " + self.symbol + " -> btc"				
					item = {
						'case':case,
						'amount':best_amount,
						'profit':best_profit,
						'best_trades':best_trades,
						'best_case':best_case
					}  	

					for observer in self.observers:
						observer.opportunity(item)
				time.sleep(config.refresh_rate)		