# (觀察多檔股票, 直接輸出信號 & 偵測信號持續時間)

import shioaji as sj # 永豐API
from collections import defaultdict, deque
from shioaji import BidAskSTKv1, Exchange
import copy  # 內建
from datetime import datetime, timedelta

# 抓 股價大於200
def filter_state(ticker, snapshot_msg_queue, state_changes, previous_state):  # 第1次filter, 存想看的資料
    for stock_info in snapshot_msg_queue:
        if (previous_state == False)&(stock_info['avg_price']>=threshold):
            #  加入新的state
            info ={
                'state_change_at': stock_info['datetime'],
                'state': True,
            }
            state_changes[ticker].append(info)
        elif (previous_state == True)&(stock_info['avg_price']<threshold):
            #  加入新的state
            info ={
                'state_change_at': stock_info['datetime'],
                'state': False,
            }
            state_changes[ticker].append(info)
    return state_changes

def filter_calc_duration(ticker, state_changes): # 第2次filter, 用資料做計算
    for i in range(len(state_changes[ticker])):
        if i==0:
            pass #第一筆資料要等到第二筆才能算duration, 最後一筆的duration會是空的(沒辦法算)
        else:
            state_changes[ticker][i-1]['duration']=state_changes[ticker][i]["state_change_at"]-state_changes[ticker][i-1]["state_change_at"]
    return state_changes

def display_when_duration_meets_criteria(state_changes, duration_greater_than): # 顯示持續時間超過xx的信號
    for ticker in state_changes:
        for item in state_changes[ticker]:
            if item['state']==True and item['duration']>= duration_greater_than :
                print(ticker, "has signal over", item['duration'], "since", item['state_change_at'])

#Login
api = sj.Shioaji()   # Production Mode
accounts = api.login(
    api_key="",         # edit it
    secret_key=""    # edit it
)

# 讓callback 信號出現時只加入queue
from collections import defaultdict, deque
from shioaji import BidAskSTKv1, TickFOPv1, Exchange
msg_queue = defaultdict(deque)
api.set_context(msg_queue)
@api.on_bidask_stk_v1(bind=True) # In order to use context, set bind=True
def quote_callback(self, exchange: Exchange, bidask:BidAskSTKv1):
    self[bidask.code].append(bidask)


# 設定偵測的threshold & duration
threshold = 200
duration_greater_than = timedelta(seconds=2) # e.g. days=2, hours=1, minutes=30, seconds=2
# 設定觀察清單
monitor=['2330','8299','2368','3228','6290','7556','3443','1815','2476']


