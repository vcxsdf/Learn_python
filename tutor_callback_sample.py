@api.on_bidask_stk_v1(bind=True)
def quote_callback_2330(self, exchange: Exchange, tick):
    if (exchange.avg_price >= 250 or exchange.avg_price <= 300) and tick.code == "2330":
        print("Buy Now !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


@api.on_bidask_stk_v1(bind=True)
def quote_callback_1101(self, exchange: Exchange, tick):
    if exchange.open < tick.code == "1101":
        print("Buy Now !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


api.quote.set_on_tick_stk_v1_callback(quote_callback_2330)
api.quote.set_on_tick_stk_v1_callback(quote_callback_1101)
