#!/usr/bin/env python
# DGC/BTC trading script for cryptsy.
# PLEASE USE IT UNDER YOUR OWN RISK, YOU CAN LOSE MONEY
# I just did it for fun, if you have an improvement or want to do a pull
# request please fell free to do so.
#
# If you made some earnings and want to donate some coins these are my addresses
# BTC: 1NKa1T2fsZU3KZrNhguuzXySoMufHe99ch
# DGC: DFbXoeq24duJ8S7pSKNr853vsuJPMBu4gm
#
# This script uses the Cryptsy API Python module from
# https://github.com/ScriptProdigy/CryptsyPythonAPI/
#
# Copyright (C) Matias Kreder, 2014, mkreder@gmail.com
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import Cryptsy
import time
from pprint import pprint
# Ger your keys from https://www.cryptsy.com/users/settings
Exchange = Cryptsy.Cryptsy('PUBLIC KEY', 'PRIVATE KEY')
#TODO: use a stadistical method to determine if we need to revaluate the values
# number of minutes until we should try with a lower difference
patience = 30

timeout = 0
buy_step = 0
sell_step = 0
o_min = 0
o_max = 0

while True:
    try:
        min = 'x'
        max = 'x'
        did_stg = 0
        trades = Exchange.marketTrades(26)
        if trades['success'] == '1':
            for order in trades['return']:
                if (max == 'x' or float(order['tradeprice']) > max):
                    max = float(order['tradeprice'])
                if (min == 'x' or float(order['tradeprice']) < min):
                    min = float(order['tradeprice'])

        info = Exchange.getInfo()
        if info['success'] == '1':
            balances = info['return']['balances_available']
            DGCbalance = float(balances['DGC'])
            BTCbalance = float(balances["BTC"])

        if not (min == o_min) or not (max == o_max):
            print("Processing new values.. resetting steps")
            buy_step = 0
            sell_step = 0
        o_min = min
        o_max = max
#       Stepping is not currently working, after doing some testing it lost a
#       lot
#        min += (min * (0.01 * buy_step))
#        max -= (max * (0.01 * sell_step))
        print("Min %.8f Max %.8f") % (min, max)
        print("Balances:")
        print("  DGC: %.8f BTC: %.8f ") % (DGCbalance, BTCbalance)
        print("Steps:")
        print("  Buy: %s Sell: %s ") % (buy_step, sell_step)

        #buy
        if (min < max):
            if ((BTCbalance / min) > 0.1):
                print "We have enough money to buy"
                amount = (BTCbalance / min)
                fee = float(Exchange.calculateFees("Buy", amount, min)['return']['fee'])
                print "Fee is %.8f BTC" % fee
                if ((4 * fee) < ((max - min) * amount)):
                    amount = ((BTCbalance - fee) / min)
                    print "Buying %s at %s" % (amount, min)
                    order = Exchange.createOrder(26, "Buy", amount, min)
                    if order['success'] == '1':
                        print(order['moreinfo'])
                        did_stg = 1
                    else:
                        print(order['error'])
                else:
                    print("Not buying due to fee, going back to step 0")
                    buy_step = 0
            else:
                print("Not enough money to buy")
        else:
            print("going back to step 0")
            buy_step = 0
        #Sell
        if (min < max):
            if (DGCbalance > 0.1):
                print "We have enough money to sell"
                fee = float(Exchange.calculateFees("Sell", DGCbalance, max)['return']['fee'])
                print "Fee is %.8f BTC" % fee
                if ((4 * fee) < ((max - min) * DGCbalance)):
                    print "Selling %s at %s" % (DGCbalance, max)
                    order = Exchange.createOrder(26, "Sell", DGCbalance, max)
                    if order['success'] == '1':
                        print(order['moreinfo'])
                        did_stg = 1
                    else:
                        print(order['error'])
                else:
                    print("Not selling due to fee, going back to step 0")
                    sell_step = 0
            else:
                print("Not enough money to sell")
        else:
            print("going back to step 0")
            sell_step = 0

        print("Pending orders:")
        pprint(Exchange.myOrders(26)['return'])
        print("Sleeping 1 minute")
        print("Waiting %s minutes until making decisions") % (patience - timeout)
        time.sleep(60)
        if did_stg == 0:
            timeout += 1
            if timeout == patience:
                print("Have being %s minutes without buying/selling") % timeout
                orders=Exchange.myOrders(26)
                if orders['success'] == '1':
                    for order in orders['return']:
                        cancel = Exchange.cancelOrder(order['orderid'])
                        tpe = order['ordertype']
                        if cancel['success'] == '1':
                            print(cancel['return'])
                            timeout = 0
                            tpe = order['ordertype']
                            if tpe == 'Buy':
                                print("Increasing buy step")
                                buy_step += 1
                            else:
                                print("Increasing sell step")
                                sell_step += 1
                        else:
                            print("Couldn't cancel the order, will wait 1 minute")
                            timeout = patience - 1
                    print("Waiting 30 secs so we get our balance back")
                    time.sleep(30)
        else:
            timeout = 0
    except Exception as e:
        print("Exception catched.. waiting 1 minute")
        print e
        time.sleep(60)
        pass
