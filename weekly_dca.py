#!/usr/bin/python3
from coinbase.wallet.client import Client
import time
import gdax

import logging
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
logger.addHandler(ch)

fh = logging.FileHandler('logs/dca.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


gdaxapi = gdax.AuthenticatedClient('your-gdax-key', 'your-gdax-secret', 'your-gdax-password')
coinb = Client('your-coinbase-key','your-coinbase-secret')
BTC_ADDR = '1CoFjh7uvBBybucCmDBARJJHFKNC7rX5EE'


def transfer():
    try:
        # Get EUR acct ID
        for acc_data in coinb.get_accounts()['data']:
            if acc_data['currency'] == 'EUR':
                acct_id = acc_data['id']
                #logger.info(acct_id)
        acct = coinb.get_account(acct_id)
        
        # Get EUR acct Balance
        eur_bal = float(acct['balance']['amount'])
        logger.info('EUR Acct ID: ' + acct_id + ' : Balance ' + str(eur_bal) + ' EUR' )
        
        if eur_bal > 0:
            logger.info('Depositing '+str(eur_bal) + ' EUR to GDAX.')
            # Deposit Coinbase EUR into GDAX Eur acct
            dep = gdaxapi.coinbase_deposit(eur_bal,"EUR", acct_id)
            logger.info(dep)
        else:
            logger.info('Insufficient Balance to Transfer.')
        
        
        
        
    except:
        raise
    
def buy():
    try:
        # Get GDAX EUR Acct data
        for gdacc in  gdaxapi.get_accounts():
            if gdacc['currency'] == 'EUR':
                gdax_acct = gdacc['id']
                gdax_bal = gdacc['balance']
        
        #logger.info(gdax_acct)
        order_status = None
        book = gdaxapi.get_product_order_book('BTC-EUR', level=1)
        
        #Get GDAX Eur account Balance
        gdax_eur_bal= round(float(gdax_bal),2)*0.996
        price = round(float(book['asks'][0][0])-0.01,2)
        size = round(float(gdax_eur_bal/price),8)
        
        if size > 0.01:
            while order_status != 'done':
    
                # Get current BTC-EUR order book
                book = gdaxapi.get_product_order_book('BTC-EUR', level=1)
                #logger.info(book)
                
                #Get GDAX Eur account Balance
                gdax_eur_bal= round(float(gdax_bal),2)*0.996
                price = round(float(book['asks'][0][0])-0.01,2)
                size = round(float(gdax_eur_bal/price),8)
                logger.info('EUR Balance: ' + str(gdax_eur_bal) + ' : Buy Price ' +str(price) + ' : BTC ' + str(size))
                
                try:
                    buy = gdaxapi.buy(price=''+str(round(price,2))+'', 
                                  size=''+str(round(size,8))+'',
                                  product_id='BTC-EUR')
                    #logger.info(buy)
                    order_id = buy['id']
                    logger.info('Order ID: ' + order_id)
                    #gdax_bal = gdaxapi.get_account(gdax_acct)['balance']
                    
                except:
                    logger.info('Buy Failed')
                    logger.info(buy)
                    raise
                
                
                order = gdaxapi.get_order(order_id)
                order_status = order['status']
                order_spread = float(gdaxapi.get_product_order_book('BTC-EUR', level=1)['asks'][0][0]) - float(order['price'])
                #logger.info(order_status)
                
    
                while float(order['filled_size']) < float(order['size']) and abs(order_spread) <= 0.02:
                    gdax_bal = gdaxapi.get_account(gdax_acct)['balance']
                    #logger.info('Order Open. Waiting')
                    time.sleep(1)
                    order = gdaxapi.get_order(order_id)
                    order_status = order['status']
                    order_spread = float(gdaxapi.get_product_order_book('BTC-EUR', level=1)['asks'][0][0]) - float(order['price'])
                    logger.info(time.strftime('%X') + ' Spread: ' + str(round(order_spread,3)), end="")
                    if abs(order_spread) > 0.02:
                        gdaxapi.cancel_order(order_id)
                        logger.info('Spread too large. Order Cancelled. Re-attempting Buy Order.')
                        order_status = 'cancelled'
    
        
            if gdaxapi.get_order(order_id)['status'] == 'done':
                logger.info('Withrawing ' + str(order['size']) +' BTC to ' + BTC_ADDR + '.')
                withdraw = gdaxapi.crypto_withdraw(order['size'], 'BTC', BTC_ADDR)
                logger.info(withdraw)
        else:
            logger.info('Insufficient Funds to buy BTC.')
    
    except:
        raise
        
transfer()
buy()
