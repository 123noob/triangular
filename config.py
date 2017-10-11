market = 'HuobiCNY'
market_expiration_time = 10
#按照['btc_cny', 'eth_btc', 'eth_cny']这个顺序写
currency_pairs = {
	'bcc':['btc_cny', 'bcc_btc', 'bcc_cny'],
	}

min_amount = 0.001
max_amount = 0.001
increment = 0.001

#loop间隔 s
refresh_rate = 3
#平台所有三角套利的币种
symbols = ['bcc']

observers = [
# 'TraderBotSim',
'Logger',
# 'TraderBot',
]

min_profit = 0.013
fee = 0.002
slippage = 1.002

#在此输入您的Key
ACCESS_KEY = ''
SECRET_KEY = ''


