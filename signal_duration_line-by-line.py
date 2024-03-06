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


from prettytable import PrettyTable
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading
import time

def convert_delta(dlt: timedelta) -> str:
    minutes, seconds = divmod(int(dlt.total_seconds()), 60)
    return f"{minutes}:{seconds:02}"

def output_table(): # 每幾秒輸出一次當前信號
    global monitor
    global state_changes
    global delay_table_display
    while True:
        time.sleep(delay_table_display)
        # print("start")
        table = PrettyTable(['Ticker','state','state_change_at','duration'])
        for ticker in monitor:
            if state_changes[ticker] != []:
                if state_changes[ticker][-1]['state'] == 'high' or state_changes[ticker][-1]['state'] == 'low':
                    # print(f"{ticker}: state {state_changes[ticker][-1]['state']}")
                    list1 = [ticker, state_changes[ticker][-1]['state'], datetime.strftime(state_changes[ticker][-1]['state_change_at'], "%H:%M"), convert_delta(datetime.now()-state_changes[ticker][-1]['state_change_at'])]
                    table.add_row(list1)
        print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        print(table)
        table.clear()
    print("error!!!!!!!!!!!!!!!!")

def save_states(): # 每幾分鐘存檔state_changes
    global state_changes
    global delay_save_states
    while True:
        time.sleep(delay_save_states)
        print("state_changes saved at " + datetime.now().strftime("%H:%M:%S"))
        t_filename = datetime.now().strftime("%Y-%m-%d") # .strftime("%Y-%m-%d_%Hh%Mm%Ss")
        # 存到檔案下次沒開盤可讀
        # import pickle # Provides functions for object serialization and deserialization.
        with open(f"state_changes_above-time-threshold_{t_filename}.pkl", "wb") as file:
            pickle.dump(state_changes, file)
    print("error!!!!!!!!!!!!!!!!")

# # new code
# monitor = deque(['1101', '1102', '1103']) # 自定義
# msg_queue = {
#     '1101': deque([1, 2, 3, 4, 5]),
#     '1102': deque([10, 20, 30, 40, 50, 60]),
#     '1103': deque([100, 100]),
# }
global monitor
global delay_table_display
global delay_save_states
monitor = deque(['6290'])
# monitor = deque(['2330','8299','2368','3228','6290','7556','1513','2313'])
threshold_high = 94.71
threshold_low = 94.70
threshold_duration = timedelta(seconds=0) # e.g. days=2, hours=1, minutes=30, seconds=2
delay_table_display = 10 # 每幾秒印一次信號表格
delay_save_states = 600   # 每幾秒存一次信號表格

global state_changes
state_changes = defaultdict(list) # 存狀態改變, 結構={'ticker': [{'state_change_at': ...,'state': high/low/no_sig, 'duration': ...}, {}, ...]}

t_table = threading.Thread(target=output_table)  #建立執行緒
t_table.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
t_table.start()  #執行
t_save_states = threading.Thread(target=save_states)  #建立執行緒
t_save_states.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
t_save_states.start()  #執行

counter = 200
while counter > 0: # True:
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
    
    info1 = current_stock_information['bid_price'][0]
    info2 = current_stock_information['ask_price'][0]
    if info1==0 or info2==0: # 如果輸入值為0就直接跳過 否則會造成state出錯
        continue
    criteria_high = current_stock_information['bid_price'][0]
    criteria_low  = current_stock_information['ask_price'][0]
    #  2-0 初始化, 
    if state_changes[ticker] == []:
        # print(f"initializing state_changes[{ticker}]")
        if criteria_high>=threshold_high:
            state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_information['datetime']})
            print(f"{ticker} state initiated to high at {criteria_high}")
        elif criteria_low<=threshold_low:
            state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_information['datetime']})
            print(f"{ticker} state initiated to low at {criteria_low}")
        else:
            state_changes[ticker].append({'state': 'no_sig', 'state_change_at': current_stock_information['datetime']})
            print(f"{ticker} state initiated to no_sig at {criteria_low}")
        continue
    # duration1 needs debugging
    # print(f"debug: {ticker}'s state[-1]={state_changes[ticker][-1]['state']}")
    duration1 = current_stock_information['datetime']-state_changes[ticker][-1]['state_change_at']
    # 2-3 如果信號high/low->low/high, 且大於設定時長, 就改值且加一行; 小於時長就只把state改成low/high
    if state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and duration1>=threshold_duration:
        state_changes[ticker][-1]['duration'] = duration1
        state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_information['datetime']})
        print(f"{ticker} state changed high to low at {criteria_low} and high signal duration>threshold")
        continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
    elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and duration1>=threshold_duration:
        state_changes[ticker][-1]['duration'] = duration1
        state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_information['datetime']})
        print(f"{ticker} state changed low to high at {criteria_high} and low signal duration>threshold")
        continue
    elif state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and duration1<threshold_duration:
        state_changes[ticker][-1]['state']= 'low'
        print(f"{ticker} state changed high to low at {criteria_low}, high signal continued for {duration1}")
        continue
    elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and duration1<threshold_duration:
        state_changes[ticker][-1]['state']= 'high'
        print(f"{ticker} state changed low to high at {criteria_high}, low signal continued for {duration1}")
        continue
    # 2-2 如果信號high/low->no_sig, 且大於設定時長, 就改值且加一行; 小於時長就只把state改回'no_sig
    elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and duration1>=threshold_duration:
        state_changes[ticker][-1]['duration'] = duration1
        state_changes[ticker].append({'state': 'no_sig', 'state_change_at': current_stock_information['datetime']})
        print(f"{ticker} state changed high to no_sig at {criteria_high} and high signal duration>threshold")
    elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low and duration1>=threshold_duration:
        state_changes[ticker][-1]['duration'] = duration1
        state_changes[ticker].append({'state': 'no_sig', 'state_change_at': current_stock_information['datetime']})
        print(f"{ticker} state changed low to no_sig at {criteria_low} and low signal duration>threshold")
    elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and duration1<threshold_duration:
        state_changes[ticker][-1]['state']= 'no_sig'
        print(f"{ticker} state changed high to no_sig at {criteria_high}, high signal continued for {duration1}")
    elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low  and duration1<threshold_duration:
        state_changes[ticker][-1]['state']= 'no_sig'
        print(f"{ticker} state changed low to no_sig at {criteria_low}, low signal continued for {duration1}")
    # 2-1 如果信號no_sig->high/low, 就改值
    elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_high>=threshold_high:
        state_changes[ticker][-1]['state']= 'high'
        state_changes[ticker][-1]['state_change_at'] = current_stock_information['datetime']
        print(f"{ticker} state changed no_sig to high at {criteria_high}")
    elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_low<=threshold_low:
        state_changes[ticker][-1]['state']= 'low'
        state_changes[ticker][-1]['state_change_at'] = current_stock_information['datetime']
        print(f"{ticker} state changed no_sig to low at {criteria_low}")

    

    """
    3. display 
    """
    # 輸出現在有信號的標的
    # table = PrettyTable(['Ticker','state','state_change_at','duration'])
    # for ticker in monitor:
    #     if state_changes[ticker] != []:
    #         if state_changes[ticker][-1]['state'] == 'high' or state_changes[ticker][-1]['state'] == 'low':
    #             # print(f"{ticker}: state {state_changes[ticker][-1]['state']}")
    #             list1 = [ticker, state_changes[ticker][-1]['state'], datetime.strftime(state_changes[ticker][-1]['state_change_at'], "%H:%M"), convert_delta(duration1)]
    #     table.add_row(list1)
    #     print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
    #     print(table)
    #     table.clear()
    # 清掉table下個迴圈重新建比較好 還是用更新的比較好
    """
    4. save signal data 
    """
    # 儲存state_changes到檔案

    counter -= 1


print(state_changes)