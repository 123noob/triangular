import urllib.request
import urllib.error
import urllib.parse
import json
from .market import Market

class HuobiCNY(Market):
	def __init__(self):
		super().__init__()
		self.depths = {
			'btc_cny' : 'http://api.huobi.com/staticmarket/depth_btc_10.js',
			'ltc_cny' : 'http://api.huobi.com/staticmarket/depth_ltc_10.js',
			'eth_cny' : 'https://be.huobi.com/market/depth?symbol=ethcny&type=step0',
			'etc_cny' : 'https://be.huobi.com/market/depth?symbol=etccny&type=step0',
			'bcc_cny' : 'https://be.huobi.com/market/depth?symbol=bcccny&type=step0',
			'eth_btc' : 'https://api.huobi.pro/market/depth?symbol=ethbtc&type=step0',
			'bcc_btc' : 'https://api.huobi.pro/market/depth?symbol=bccbtc&type=step0',
			'etc_btc' : 'https://api.huobi.pro/market/depth?symbol=etcbtc&type=step0',
			'ltc_btc' : 'https://api.huobi.pro/market/depth?symbol=ltcbtc&type=step0',
		}

	def update_depth(self, symbol):
		url = self.depths[symbol];
		req = urllib.request.Request(url,headers={
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36"})
		res = urllib.request.urlopen(req)
		depth = json.loads(res.read().decode('utf8'))
		self.depth = self.format_depth(depth)
		# print(self.depth)

	def sort_and_format(self, l, reverse=False):
		l.sort(key=lambda x: float(x[0]), reverse=reverse)
		r = []
		for i in l:
			r.append({'price': float(i[0]), 'amount': float(i[1])})	
		return r	

	def format_depth(self, depth):
		if 'tick' in depth.keys():
			depth['bids'] = depth['tick']['bids']
			depth['asks'] = depth['tick']['asks']
		bids = self.sort_and_format(depth['bids'], True)
		asks = self.sort_and_format(depth['asks'], False)
		return {'asks':asks, 'bids':bids}		




