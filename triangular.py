import config
import sys
import logging
import time
from concurrent.futures import ThreadPoolExecutor, wait


class Triangular():
	def __init__(self):
		self.observers = []
		self.symbols = config.symbols
		self.threadpool = ThreadPoolExecutor(max_workers=4)
		self.init_observers(config.observers)

	def init_observers(self, _observers):
		for observer_name in _observers:	
			try:
				exec('import observers.' + observer_name.lower())
				observer = eval('observers.' + observer_name.lower() + '.' + observer_name + '()')
				self.observers.append(observer)
			except(ImportError, AttributeError) as e:
				print('%s observer name is invalid' % observer_name)	
	
	def __get_triangle(self, symbol, triangles):
		triangles[symbol] = Triangle(symbol).main()

	def update_cases(self):
		futures = []
		triangles = {}
		for symbol in self.symbols:
			futures.append(self.threadpool.submit(self.__get_triangle, symbol, triangles))
		wait(futures, timeout=4)
		return triangles
				
	def loop(self):
		while True:
			self.triangles = self.update_cases()
			# print(self.triangles)
			# sys.exit(0)
			item = sorted(self.triangles.items(), key=lambda x: x[1]['profit'], reverse=True)
			# print(self.triangles)
			# sys.exit(0)
			# print(item)
			if item != [] and item[0][1]['profit'] > 0:
				time.sleep(0.1)
				item2 = [(item[0][0], Triangle(item[0][0]).main() )]
				# print(item)
				# print(item2)
				# sys.exit(0)
				if item[0][1]['profit'] == item2[0][1]['profit']:
					for observer in self.observers:
						observer.opportunity(item2)	
					time.sleep(config.refresh_rate)


class Triangle():
	def __init__(self, symbol):
		self.fee = config.fee
		self.slippage = config.slippage
		self.symbol = symbol
		self.currency_pairs = config.currency_pairs[symbol]
		self.depths = {}
		self.init_market(config.market)
		self.threadpool = ThreadPoolExecutor(max_workers=3)

	def init_market(self, market):
		try:
			exec('import public_markets.' + market.lower())
			m = eval('public_markets.' + market.lower() + '.' + market + '()' )
			self.market = m
		except(ImportError, AttributeError) as e:
			print('%s market name is invalid' % m)

	def __get_depth(self, pair, depths):
		depths[pair] = self.market.get_depth(pair)		

	def update_depths(self):
		depths = {}	
		futures = []
		for pair in self.currency_pairs:
			futures.append(self.threadpool.submit(self.__get_depth, pair, depths))
		wait(futures, timeout=0.1)
		return depths

	def ask_volume(self, orders, amount):
		vol = 0
		value = 0

		i = 0
		while i < len(orders['asks']) and value < amount:
			this_value = min( (orders['asks'][i]['price'] * self.slippage) * orders['asks'][i]['amount'], amount - value)
			this_vol = this_value / (orders['asks'][i]['price'] * self.slippage)
			value += this_value
			vol += this_vol

			i += 1
		#(price, amount)
		return (value / vol, vol)	

	def bid_volume(self, orders, amount):	
		vol = 0
		value = 0

		i = 0
		while i < len(orders['bids']) and value < amount:
			this_value = min(orders['bids'][i]['amount'], amount - value)
			this_vol = this_value * (orders['bids'][i]['price'] * self.slippage)
			value += this_value
			vol += this_vol

			i += 1
		# (卖出总数， 总收入)	
		return (value, vol)
			
	def main(self):
		self.depths = self.update_depths()
		# return self.depths[self.currency_pairs[0]]
		# return self.currency_pairs[0]
		btc_cny_orders = self.depths[self.currency_pairs[0]]
		# return btc_cny_orders['asks'][0][0]
		cc_btc_orders = self.depths[self.currency_pairs[1]]
		# logging.info('cc_btc_orders %s' % cc_btc_orders)
		cc_cny_orders = self.depths[self.currency_pairs[2]]

		if btc_cny_orders and cc_btc_orders and cc_cny_orders:
			best_case = 0
			best_profit = 0
			best_amount = 0
			best_trades = {}

			amt = config.min_amount
			while amt <= config.max_amount:
				#case 1: cny -> btc -> cc -> cny
				c1_btc = self.ask_volume(btc_cny_orders, amt)
				c1_btc_balance = int( (c1_btc[1] - c1_btc[1] * self.fee) * 10000) / 10000
				c1_cc = self.ask_volume(cc_btc_orders, c1_btc_balance)
				c1_cc_balance = int( (c1_cc[1] - c1_cc[1] * self.fee) * 10000) / 10000
				c1_cny = self.bid_volume(cc_cny_orders, c1_cc_balance)
				c1_cny_balance = c1_cny[1] - c1_cny[1] * self.fee
				c1_profit = c1_cny_balance - amt
				
				if c1_profit > best_profit:
					best_case = 1
					best_profit = c1_profit
					best_amount = amt
					best_trades = [
						{
							'pair':self.currency_pairs[0],
							'type':'buy',
							'amount':round(c1_btc[1], 4),
							'rate':round(c1_btc[0], 2)

						},	
						{
							'pair':self.currency_pairs[1],
							'type':'buy',
							'amount':round(c1_cc[1], 4),
							'rate':round(c1_cc[0], 6),
							'transfer':c1_btc_balance
						},
						{
							'pair':self.currency_pairs[2],
							'type':'sell',
							'amount':round(c1_cny[0], 4),
							'rate':round(c1_cny[1] / c1_cny[0], 2),
							'transfer':c1_cc_balance
						},
					]
				'''	
				#case 2: cny -> cc -> btc -> cny
				c2_cc = self.ask_volume(cc_cny_orders, amt)
				# c2_cc_balance = int ( (c2_cc[1] - c2_cc[1] * self.fee) * 10000) / 10000
				c2_cc_balance = c2_cc[1] - c2_cc[1] * self.fee
				c2_btc = self.bid_volume(cc_btc_orders, c2_cc_balance)
				c2_btc_balance = c2_btc[1] - c2_btc[1] * self.fee
				c2_cny = self.bid_volume(btc_cny_orders, c2_btc_balance)
				c2_cny_balance = c2_cny[1] - c2_cny[1] * self.fee	
				c2_profit = c2_cny_balance - amt

				if c2_profit > best_profit:
					best_case = 2
					best_profit = c2_profit
					best_amount = amt
					best_trades = [
						{
							'pair':self.currency_pairs[2],
							'type':'buy',
							'amount':round(c2_cc[1], 4),
							'rate':round(c2_cc[0], 2)
						},	
						{
							'pair':self.currency_pairs[1],
							'type':'sell',
							'amount':round(c2_cc_balance, 4),
							'rate':round(c2_btc[1] / c2_cc_balance, 6)
						},
						{
							'pair':self.currency_pairs[0],
							'type':'sell',
							'amount':round(c2_btc_balance, 4),
							'rate':round(c2_cny[1] / c2_btc_balance, 2)
						},	
					]
					'''

				amt += config.increment


			if best_case > 0:
				case = "cny -> btc -> " + self.symbol + " -> cny" if best_case == 1 else "cny -> " + self.symbol + " -> btc -> cny"				
				return {
					'case':case,
					'amount':best_amount,
					'profit':best_profit,
					'best_trades':best_trades,
					'best_case':best_case
				}  

		return {
			'case':0,
			'amount':0,
			'profit':0,
			'best_trades':[],
			'best_case':0
		}   	                                        


