import hashlib
import time
import urllib
import urllib.parse  
import urllib.request  
from config import ACCESS_KEY,SECRET_KEY


HUOBI_SERVICE_API="https://api.huobi.com/apiv3"
ACCOUNT_INFO = "get_account_info"
GET_ORDERS = "get_orders"
ORDER_INFO = "order_info"
BUY = "buy"
BUY_MARKET = "buy_market"
CANCEL_ORDER = "cancel_order"
NEW_DEAL_ORDERS = "get_new_deal_orders"
ORDER_ID_BY_TRADE_ID = "get_order_id_by_trade_id"
SELL = "sell"
SELL_MARKET = "sell_market"

'''
发送信息到api
'''
def send2api(pParams, extra):
	pParams['access_key'] = ACCESS_KEY
	pParams['created'] = int(time.time())
	pParams['sign'] = createSign(pParams)
	if(extra) :
		for k in extra:
			v = extra.get(k)
			if(v != None):
				pParams[k] = v
		#pParams.update(extra)
	tResult = httpRequest(HUOBI_SERVICE_API, pParams)
	return tResult

'''
生成签名
'''
def createSign(params):
	params['secret_key'] = SECRET_KEY;
	params = sorted(params.items(), key=lambda d:d[0], reverse=False)
	message = urllib.parse.urlencode(params)
	message=message.encode(encoding='UTF8')
	m = hashlib.md5()
	m.update(message)
	m.digest()
	sig=m.hexdigest()
	return sig

'''
request
'''
def httpRequest(url, params):
	postdata = urllib.parse.urlencode(params)
	postdata = postdata.encode('utf-8')

	fp = urllib.request.urlopen(url, postdata)
	if fp.status != 200 :
		return None
	else:
		mybytes = fp.read()
		mystr = mybytes.decode("utf8")
		fp.close()
		return mystr

'''
获取账号详情
'''
def getAccountInfo(method):
	params = {"method":method}
	extra = {}
	res = send2api(params, extra)
	return res

'''
限价
@param coinType
@param price
@param amount
@param tradePassword
@param tradeid
@param method
'''
def query_order(coinType,price,amount,tradePassword,tradeid,method):
	params = {"method":method}
	params['coin_type'] = coinType
	params['price'] = price
	params['amount'] = amount
	extra = {}
	extra['trade_password'] = tradePassword
	extra['trade_id'] = tradeid
	res = send2api(params, extra)
	return res