import logging
import config
import time
from .observer import Observer
import sys
from private_markets import huobi_main as main, huobi_new as new, huobi_pro as pro

# second
ORDER_EXPIRATION_TIME = 20

class TraderBotSim(Observer):

    def opportunity(self, item):
        logging.info('%s Amount %f Expected Profit %f' % (item['case'], item['amount'], item['profit']) )

        



