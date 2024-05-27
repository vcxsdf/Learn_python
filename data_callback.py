

""">>>>>>>>>>>TODO<<<<<<<<<"""
  # 設定行情連線事件
def onQuoteEvent(self, quote):
    print(self.ConvertStrFromDll(quote))

ObjRayin.AddQuote(0, '2883') #print quote


""">>>>>>>>>>>sample 1<<<<<<<<<"""

api.set_context(msg_queue)
@api.on_bidask_stk_v1(bind=True) # In order to use context, set bind=True
def quote_callback(self, exchange: Exchange, bidask:BidAskSTKv1):
    self[bidask.code].append(bidask)
for ticker in monitor:
    api.quote.subscribe(api.Contracts.Stocks[ticker], quote_type='bidask')

""">>>>>>>>>>>sample 2<<<<<<<<<"""

import queue

api = sj.Shioaji()
accounts =  api.login("", "")

q = queue.Queue()  # bidask 所有資訊
def quote_callback(_: Exchange, bidask:BidAskSTKv1):
  q.put_nowait(bidask)

# volumn = queue.Queue()  # bidask 所有資訊
# def quote_callback1(_: Exchange, bidask:BidAskSTKv1):
#   volumn.put_nowait(bidask.volume)

# set_on_bidask_stk_v1_callback provide by package
api.quote.set_on_bidask_stk_v1_callback(quote_callback)

monitor = ['1809', '6535', '8092']
for ticker in monitor:
    api.quote.subscribe(
        api.Contracts.Stocks[ticker],
        quote_type='bidask'
    )

while True:
    item : sj.BidAskSTKv1 = q.get()
    print(item.datetime.timestamp(), item.bid_price, item.bid_volume)
    write_db(cur, item)

