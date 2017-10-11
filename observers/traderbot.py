import logging
import config
import time
from .observer import Observer
import sys
from private_markets import huobi_main as main, huobi_new as new, huobi_pro as pro

# second
ORDER_EXPIRATION_TIME = 20

class TraderBot(Observer):

    def opportunity(self, item):
        logging.info('%s Amount %f Expected Profit %f' % (item[0][1]['case'], item[0][1]['amount'], item[0][1]['profit']) )
        if item[0][1]['best_case'] == 1:
            #case 1: cny -> btc -> cc -> cny
            logging.info('step 1')
            trade = item[0][1]['best_trades'][0]
            cny_balance = float(eval(main.getAccountInfo(main.ACCOUNT_INFO) )['available_cny_display'])
            if float(cny_balance) < float(trade['rate'] * trade['amount']):
                trans = self.verify("new.query_transfer('new','main','cny'," + str(round(trade['amount'] * trade['rate'], 2)) + " )", time.time())
                if trans['status'] == 'error':
                    logging.warn('step 1: new\'s cny transfer main failed %s' % trans['err-msg'])
                    return
            if not self.recur(self.perform_trade(trade,False), time.time() ):           
                return   

            logging.info('step 2')
            trade = item[0][1]['best_trades'][1]
            trans = self.verify("pro.query_transfer('main', 'pro', 'btc'," + str(trade['transfer']) + " )", time.time())
            if trans['status'] == 'error':
                logging.warn('step 2: main\'s btc transfer pro failed %s' % trans['err-msg'])
                return
            if not self.recur(self.perform_trade(trade,False), time.time() ):           
                return     

            logging.info('step 3')
            trade = item[0][1]['best_trades'][2]
            if trade['pair'] in ['eth_cny','bcc_cny','etc_cny']:
                trans = self.verify("pro.query_transfer('pro', 'new', " + "'"+trade['pair'][:3]+"'" + ", " +str(trade['transfer']) +")", time.time())
            else:
                trans = self.verify("pro.query_transfer('pro','main'," + "'"+trade['pair'][:3]+"'" + "," +str(trade['transfer']) + ")", time.time()) 
            if trans['status'] == 'error':
                logging.warn('step 3: transfer failed %s' % trans['err-msg'])
                return 
            if not self.recur(self.perform_trade(trade,False), time.time() ):           
                return    
        elif item[0][1]['best_case'] == 2:       
            #case 2: cny -> cc -> btc -> cny
            logging.info('step 1')
            trade = item[0][1]['best_trades'][0]
            if trade['pair'] in ['eth_cny','bcc_cny','etc_cny']:
                for x in new.get_account_info()['data']['list']:
                    if x['currency'] == 'cny' and x['type'] == 'trade':
                        cny_balance = x['balance']
                if float(cny_balance) < float(trade['rate'] * trade['amount']):        
                    trans = self.verify("new.query_transfer('main', 'new', 'cny', " + str(round(trade['amount'] * trade['rate'], 2)) + " )", time.time()) 
                    if trans['status'] == 'error':
                        logging.warn('step 1: main\'s cny transfer new failed %s' % trans['err-msg'])
                        return
                if not self.recur(self.perform_trade(trade,False), time.time() ):           
                    return          
            else:
                cny_balance = float(eval(main.getAccountInfo(main.ACCOUNT_INFO) )['available_cny_display'])
                if float(cny_balance) < float(trade['rate'] * trade['amount']):
                    trans = self.verify("new.query_transfer('new','main','cny'," + str(round(trade['amount'] * trade['rate'], 2)) + ")", time.time())
                    if trans['status'] == 'error':
                        logging.warn('step 1: new\'s cny transfer main failed %s' % trans['err-msg'])
                        return
                if not self.recur(self.perform_trade(trade,False), time.time() ):           
                    return   

            logging.info('step 2')
            trade = item[0][1]['best_trades'][1]
            f = 'main' if trade['pair'] == 'ltc_btc' else 'new'
            trans = self.verify("pro.query_transfer(f, 'pro', " + "'"+trade['pair'][:3]+"'" + "," + str(trade['amount']) + ")", time.time())       
            if trans['status'] == 'error':
                logging.warn('step 2: main\'s btc transfer pro failed %s' % trans['err-msg'])
                return
            if not self.recur(self.perform_trade(trade,False), time.time() ):           
                return 

            logging.info('step 3') 
            trade = item[0][1]['best_trades'][2]
            if trade['pair'] in ['eth_cny','bcc_cny','etc_cny']:
                trans = self.verify("pro.query_transfer('pro', 'new', 'btc', " + str(trade['amount']) + ")", time.time())
            else:
                trans = self.verify("pro.query_transfer('pro', 'main', 'btc', " + str(trade['amount']) + ")", time.time()) 
            if trans['status'] == 'error':
                logging.warn('step 3: transfer failed %s' % trans['err-msg'])
                return 
            if not self.recur(self.perform_trade(trade,False), time.time() ):           
                return                
         
    def recur(self, query_order, time_now):
        if 'status' in query_order.keys(): 
            if query_order['status'] == 'ok': 
                return True
            else:
                logging.warn('trade failed %s' % query_order['err-msg']) 
                return False  
        elif 'result' in query_order.keys():
            if query_order['result'] == 'success':
                return True
            else:
                logging.warn('trade failed %s' % query_order['message']) 
                return False                 

    # def recur(self, query_order, time_now):
    # if 'status' in query_order.keys() and query_order['status'] == 'ok': 
    #     return True
    # else:
    #     if time.time() - time_now < ORDER_EXPIRATION_TIME:
    #         self.recur(query_order, time_now)
    #     if 'code' in query_order.keys():  
    #         logging.warn('trade failed %s' % query_order['msg']) 
    #     else:
    #         logging.warn('trade failed, unknown error')
    #     return False  

    def verify(self, trans_str, time_now):
        while time.time() - time_now < ORDER_EXPIRATION_TIME:
            trans = eval(trans_str)
            if trans['status'] == 'ok':
                break
        return trans                    

    def perform_trade(self, trade, show_balance):
        symbols = {
            'btc_cny':1,
            'eth_btc':'ethbtc',
            'eth_cny':'ethcny',
            'ltc_btc':'ltcbtc',
            'ltc_cny':2,
            'bcc_btc':'bccbtc',
            'bcc_cny':'bcccny',
            'etc_btc':'etcbtc',
            'etc_cny':'etccny',
        }

        if trade['pair'] in ['btc_cny', 'ltc_cny']:
            query_order = eval(main.query_order(symbols[trade['pair']],trade['rate'],trade['amount'],None,None,trade['type']) )

        if trade['pair'] in ['eth_btc','ltc_btc','bcc_btc','etc_btc']:
            t = 'buy-limit' if trade['type'] == 'buy' else 'sell-limit'   
            query_order = pro.query_order(trade['amount'], trade['rate'], symbols[trade['pair']], t)
                
        if trade['pair'] in ['eth_cny','bcc_cny','etc_cny']:
            t = 'buy-limit' if trade['type'] == 'buy' else 'sell-limit'   
            query_order = new.query_order(trade['amount'], trade['rate'], symbols[trade['pair']], t) 

        return query_order 
       


