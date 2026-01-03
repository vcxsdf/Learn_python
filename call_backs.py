import time
import random
import math

import queue

q = []
def quote_callback(stock_price):
    q.append(stock_price)
    print(q)

state = []
def quote_callback1(stock_price):
    if stock_price > 0:
        state.append(True)
    else:
        state.append(False)

    print(state)


def quote_callback3(stock_price):  #(_: Exchange, bidask:BidAskSTKv1):
    print(stock_price)


# Shioaji Package
class StockGenerator(object):
    def __init__(self):
        self.funcs = []

    def register_callback(self,function_callback):
        self.funcs.append(function_callback)

    def start_generate_stock(self):
        current_stock_price = 0
        while True:
            current_stock_price += random.randint(-100, 100)

            # run registers
            for func in self.funcs:
                func(current_stock_price)

            time.sleep(1)
            print(current_stock_price)

stock_gen = StockGenerator()

stock_gen.register_callback(quote_callback)
stock_gen.register_callback(quote_callback1)
stock_gen.register_callback(quote_callback3)

stock_gen.start_generate_stock()
