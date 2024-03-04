# 存到檔案下次沒開盤可讀
# import pickle # Provides functions for object serialization and deserialization.
# with open("msg-queue.pkl", "wb") as file:
#     pickle.dump(msg_queue, file)

# 讀檔案 沒開盤時可試如何處理資料
import pickle
with open("msg_queue_240304-2.pkl", "rb") as file:
# with open("msg-queue-2330.pkl", "rb") as file:
    msg_queue = pickle.load(file)
# display(msg_queue)

"""
msg_queue = {'key1': deque([BidAsk(xxx=ooo,
                                   list=[360, 205, 325, 236, 208]),
                            BidAsk(xxx=ooo,
                                   list=[30, 25, 35, 26, 28]),
                            ...
                          ]),
            'key2': deque([BidAsk(xxx=ooo,
                                   list=[360, 205, 325, 236, 208]),
                            BidAsk(xxx=ooo,
                                   list=[30, 25, 35, 26, 28]),
                            ...
                          ])
            }
"""

# (觀察多檔股票, 直接輸出信號 & 偵測信號持續時間)


from collections import defaultdict, deque
from datetime import datetime, timedelta


# # new code
# monitor = deque(['1101', '1102', '1103']) # 自定義
# msg_queue = {
#     '1101': deque([1, 2, 3, 4, 5]),
#     '1102': deque([10, 20, 30, 40, 50, 60]),
#     '1103': deque([100, 100]),
# }
monitor = deque(['6290'])
# monitor = deque(['2330','8299','2368','3228','6290','7556','1513','2313'])
threshold_high = 94.71
threshold_low = 94.70
threshold_duration = timedelta(seconds=0) # e.g. days=2, hours=1, minutes=30, seconds=2
state_changes = defaultdict(list) # 存狀態改變, 結構={'ticker': [{'state_change_at': ...,'state': high/low/no_sig, 'duration': ...}, {}, ...]}
counter = 200
while counter > 0:
    """
    1. get and clean values from msg_queue
    """
    # Error handling, 1. 可容忍錯誤, 2. 不可容忍錯誤
    try:
        ticker = monitor.popleft() # 1101
    except Exception:
        raise Exception
    monitor.append(ticker)

    current_stock_queue: deque = msg_queue[ticker]  # [1, 2, 3, 4, 5]

    try:
        current_stock_information = current_stock_queue.popleft() # 1
    except Exception:
        print("no signal at", datetime.now())
        counter -= 1
        continue

    print(f"{counter}#: stock code: {ticker}, current value: {current_stock_information}")
   
    """
    2. capture state changes
        2-0. initialize
        if no value, add signal as no_sig

        2-1.
        no_sig -> high, change(ticker, high, timestamp),
        no_sig -> low, change(ticker, low, timestamp),

        2-2.
        low -> no_sig,
            if (now-timestamp)<threshold:
            change row(ticker, no_sig, ),
            else
            change row(duration),
            寫row到檔案,
            add row(ticker, no_sig,)
        high -> no_sig,
            if (now-timestamp)<threshold:
            change row(ticker, no_sig, ),
            else
            change row(duration),
            寫row到檔案,
            add row(ticker, no_sig,)

        2-3.
        low -> high,
            if (now-timestamp)<threshold:
            change row(ticker, high, timestamp, ),
            else
            change row(duration),
            寫row到檔案,
            add row(ticker, high, timestamp,)

        high -> low,
            if (now-timestamp)<threshold:
            change row(ticker, low, timestamp, ),
            else
            change row(duration),
            寫row到檔案,
            add row(ticker, low, timestamp,)
    """
    # 2-0 初始化
    if state_changes[ticker] == []:
        if current_stock_information['bid_price'][0]>=threshold_high:
            state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_information['datetime']})
        elif current_stock_information['bid_price'][0]<=threshold_low:
            state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_information['datetime']})
        else:
            state_changes[ticker].append({'state': 'no_sig'})
        continue
    # 2-3 如果信號high/low->low/high, 且大於設定時長, 就改值且加一行; 小於時長就只把state改成low/high
    elif state_changes[ticker][-1]['state'] == 'high' and current_stock_information['bid_price'][0]<=threshold_low and (datetime.now()-current_stock_information['datetime'])>=threshold_duration:
        state_changes[ticker][-1]['duration'] = datetime.now()-current_stock_information['datetime']
        state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_information['datetime']})
        continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
    elif state_changes[ticker][-1]['state'] == 'low' and current_stock_information['bid_price'][0]>=threshold_high and (datetime.now()-current_stock_information['datetime'])>=threshold_duration:
        state_changes[ticker][-1]['duration'] = datetime.now()-current_stock_information['datetime']
        state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_information['datetime']})
        continue
    elif state_changes[ticker][-1]['state'] == 'high' and current_stock_information['bid_price'][0]<=threshold_low and (datetime.now()-current_stock_information['datetime'])<threshold_duration:
        state_changes[ticker][-1]['state']= 'low'
        continue
    elif state_changes[ticker][-1]['state'] == 'low' and current_stock_information['bid_price'][0]>=threshold_high and (datetime.now()-current_stock_information['datetime'])<threshold_duration:
        state_changes[ticker][-1]['state']= 'high'
        continue
    # 2-2 如果信號high/low->no_sig, 且大於設定時長, 就改值且加一行; 小於時長就只把state改回'no_sig
    elif state_changes[ticker][-1]['state'] == 'high' and current_stock_information['bid_price'][0]<threshold_high and (datetime.now()-current_stock_information['datetime'])>=threshold_duration:
        state_changes[ticker][-1]['duration'] = datetime.now()-current_stock_information['datetime']
        state_changes[ticker].append({'state': 'no_sig'})
    elif state_changes[ticker][-1]['state'] == 'low' and current_stock_information['bid_price'][0]>threshold_low and (datetime.now()-current_stock_information['datetime'])>=threshold_duration:
        state_changes[ticker][-1]['duration'] = datetime.now()-current_stock_information['datetime']
        state_changes[ticker].append({'state': 'no_sig'})
    elif state_changes[ticker][-1]['state'] == 'high' and current_stock_information['bid_price'][0]<threshold_high and (datetime.now()-current_stock_information['datetime'])<threshold_duration:
        state_changes[ticker][-1]['state']= 'no_sig'
    elif state_changes[ticker][-1]['state'] == 'low' and current_stock_information['bid_price'][0]>threshold_low  and (datetime.now()-current_stock_information['datetime'])<threshold_duration:
        state_changes[ticker][-1]['state']= 'no_sig'
    # 2-1 如果信號no_sig->high/low, 就改值
    elif state_changes[ticker][-1]['state'] == 'no_sig' and current_stock_information['bid_price'][0]>=threshold_high:
        state_changes[ticker][-1]['state']= 'high'
        state_changes[ticker][-1]['state_change_at'] = current_stock_information['datetime']
    elif state_changes[ticker][-1]['state'] == 'no_sig' and current_stock_information['bid_price'][0]<=threshold_low:
        state_changes[ticker][-1]['state']= 'low'
        state_changes[ticker][-1]['state_change_at'] = current_stock_information['datetime']

    # do something with current_stock_information
    # filter_set() .....
    # filter_status() ....
    #
    counter -= 1


print(state_changes)