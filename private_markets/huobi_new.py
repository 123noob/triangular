import base64
import hmac
import hashlib
import urllib
import json
import time
from urllib import parse
from urllib import request
from datetime import datetime
from config import ACCESS_KEY,SECRET_KEY

# timeout in 5 seconds:
TIMEOUT = 5

ACCOUNT_ID = 

API_HOST = 'be.huobi.com'

SCHEME = 'https'

# language setting: 'zh-CN', 'en':
LANG = 'zh-CN'

DEFAULT_GET_HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
}

DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
}

class ApiClient(object):

    def __init__(self, appKey, appSecret, assetPassword=None, host=API_HOST):
        '''
        Init api client object, by passing appKey and appSecret.
        '''
        self._accessKeyId = appKey
        self._accessKeySecret = appSecret.encode('utf-8') # change to bytes
        self._assetPassword = assetPassword
        self._host = host
    
    def get(self, path, **params):
        qs = self._sign('GET', path, self._utc(), params)
        return self._call('GET', '%s?%s' % (path, qs))

    def post(self, path, obj=None):
        qs = self._sign('POST', path, self._utc())
        data = None
        if obj is not None:
            data = json.dumps(obj).encode('utf-8')
        return self._call('POST', '%s?%s' % (path, qs), data)

    def _call(self, method, uri, data=None):
        url = '%s://%s%s' % (SCHEME, self._host, uri)
        # print(method + ' ' + url)
        headers = DEFAULT_GET_HEADERS if method=='GET' else DEFAULT_POST_HEADERS
        req = request.Request(url, data=data, headers=headers, method=method)
        with request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.getcode()!=200:
                raise ApiNetworkError('Bad response code: %s %s' % (resp.getcode(), resp.reason))
            # type dict    
            return json.loads(resp.read().decode('utf-8'))


    def _sign(self, method, path, ts, params=None):
        self._method = method
        # create signature:
        if params is None:
            params = {}
        params['SignatureMethod'] = 'HmacSHA256'
        params['SignatureVersion'] = '2'
        params['AccessKeyId'] = self._accessKeyId
        params['Timestamp'] = ts
        # sort by key:
        keys = sorted(params.keys())
        # build query string like: a=1&b=%20&c=:
        qs = '&'.join(['%s=%s' % (key, self._encode(params[key])) for key in keys])
        # build payload:
        payload = '%s\n%s\n%s\n%s' % (method, self._host, path, qs)
        # print('payload:\n%s' % payload)
        dig = hmac.new(self._accessKeySecret, msg=payload.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sig = self._encode(base64.b64encode(dig).decode())
        # print('sign: ' + sig)
        qs = qs + '&Signature=' + sig
        return qs

    def _utc(self):
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    def _encode(self, s):
        return parse.quote(s, safe='')


def query_order(amount, price, symbol, _type):
    client = ApiClient(ACCESS_KEY, SECRET_KEY)
    return client.post('/v1/order/orders/place',  {
            'account-id': ACCOUNT_ID,
            'amount': amount,
            'price': price,
            'symbol': symbol,
            'type': _type,
            'source': 'api',
        })

def query_transfer(_from, to, currency, amount):
    client = ApiClient(ACCESS_KEY, SECRET_KEY)
    return client.post('/v1/dw/balance/transfer',  {
            'from' : _from,
            'to' : to,
            'currency' : currency,
            'amount' : amount,
        })

def get_account():
    client = ApiClient(ACCESS_KEY, SECRET_KEY)
    return client.get('/v1/account/accounts')

def get_account_info():
    client = ApiClient(ACCESS_KEY, SECRET_KEY)
    return client.get('/v1/account/accounts/' + str(ACCOUNT_ID) + '/balance')  



