# 讀檔案 沒開盤時可試如何處理資料
import pickle
with open("msg_queue_240304-2.pkl", "rb") as file:
# with open("msg-queue-2330.pkl", "rb") as file:
    msg_queue = pickle.load(file)
# display(msg_queue)
    

# 跑一陣 可能會卡state

import shioaji as sj # 永豐API
from shioaji import BidAskSTKv1, Exchange
from datetime import datetime, timedelta
from prettytable import PrettyTable
from collections import defaultdict, deque
import threading
import time
import pandas as pd
from tabulate import tabulate

def main():
    # monitor = deque(['1809'])
    monitor = deque(['2330','8299','2368','3228','6290','7556','1513','2313'])
    # monitor = deque(['82992','1809', '6425', '8092', '6535', '4303', '5202', '3131', '6446', '1773', '2417', '6165', '1815', '2313', '1589', '6805', '3548', '3376', '1513', '2367', '7402', '3324', '1503', '3653', '3363', '2543', '3443', '4912', '3689', '1456', '3516', '4755', '8299', '2476', '6290', '4763', '8089', '2059', '3390', '4945', '6799', '2329', '4164', '8064', '6716', '3228', '7556', '4961', '8473', '2460', '2025', '5498', '2449', '3013', '3171', '6275'])
    threshold_high = 100   # 偵測信號在高檔
    threshold_low = 90  # 偵測信號在低檔
    threshold_duration = timedelta(seconds=1) # e.g. days=2, hours=1, minutes=30, seconds=2
    delay_signal_display = 10 # 每幾秒印一次信號表格
    delay_duration_display = 15 # 每幾秒印一次信號表格
    delay_API_connection_start = 3 # wait for API connection to establish
    
    global msg_queue, state_changes, accumulated_duration, lock
    msg_queue = defaultdict(deque)
    state_changes = defaultdict(list) # 存狀態改變, 結構={'ticker': [{'state_change_at': ...,'state': high/low/no_sig, 'duration': ...}, {}, ...]}
    accumulated_duration = pd.DataFrame({
    "Ticker": [],
    "High_duration": [],
    "Low_duration": []
    })
    accumulated_duration.set_index('Ticker', inplace=True)
    
    get_data(monitor)
    time.sleep(delay_API_connection_start)
    
    lock = threading.Lock()         # 建立 Lock
    threads = []
    for ticker in monitor:
        thread = threading.Thread(target=stock_listener, args=(ticker, threshold_high, threshold_low, threshold_duration,))
        threads.append(thread)

    for run_threads in threads:
        run_threads.daemon = True
        run_threads.start()
    
    t_output_accumulated_duration = threading.Thread(target=output_accumulated_duration, args=(delay_duration_display,))  #建立執行緒
    t_output_accumulated_duration.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
    t_output_newest_state = threading.Thread(target=output_newest_state, args=(monitor, delay_signal_display,))  #建立執行緒
    t_output_newest_state.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
    
    t_output_accumulated_duration.start()  #執行
    t_output_newest_state.start()  #執行

    while True:
        continue

def get_data(monitor):
    #Login
    api = sj.Shioaji()   # Production Mode
    accounts = api.login(
        api_key="",         # edit it
        secret_key=""    # edit it
    )

    # 讓callback 信號出現時只加入queue
    global msg_queue  #msg_queue = defaultdict(deque)
    api.set_context(msg_queue)
    @api.on_bidask_stk_v1(bind=True) # In order to use context, set bind=True
    def quote_callback(self, exchange: Exchange, bidask:BidAskSTKv1):
        self[bidask.code].append(bidask)
    for ticker in monitor:
        api.quote.subscribe(api.Contracts.Stocks[ticker], quote_type='bidask')
    """如何定期清理msg_queue"""

def stock_listener(ticker, threshold_high, threshold_low, threshold_duration):
    global state_changes, accumulated_duration

    while True: #len(msg_queue[ticker]) > 0:
        """
        1. get and clean values from msg_queue
        """
        # Error handling, 1. 可容忍錯誤, 2. 不可容忍錯誤
        current_stock_queue: deque = msg_queue[ticker]  # [1, 2, 3, 4, 5]

        try:
            current_stock_information = current_stock_queue.popleft() # 1
        except Exception:
            # print("no signal at", datetime.now())
            continue
    
        """
        2. record state changes
        """
        """
        setting starts
        """
        info1 = current_stock_information['bid_price'][0]
        info2 = current_stock_information['ask_price'][0]
        if info1==0 or info2==0: # 如果輸入值為0就直接跳過 否則會造成state出錯
            continue
        criteria_high = current_stock_information['bid_price'][0]
        criteria_low  = current_stock_information['ask_price'][0]
        """
        setting ends
        """
        #  2-0 初始化, 
        if state_changes[ticker] == []:
            # print(f"initializing state_changes[{ticker}]")
            lock.acquire()
            if criteria_high>=threshold_high:
                state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_information['datetime'], 'duration': 0})
                print(f"{ticker} state initiated to high at {criteria_high}")
            elif criteria_low<=threshold_low:
                state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_information['datetime'], 'duration': 0})
                print(f"{ticker} state initiated to low at {criteria_low}")
            else:
                state_changes[ticker].append({'state': 'no_sig', 'state_change_at': current_stock_information['datetime'], 'duration': 0})
                print(f"{ticker} state initiated to no_sig at {criteria_low}")
            lock.release()
            continue
        duration1 = current_stock_information['datetime']-state_changes[ticker][-1]['state_change_at']
        # 2-3 如果信號high/low->low/high, 且大於設定時長, 就改值且加一行; 小於時長就只把state改成low/high
        if state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and duration1>=threshold_duration:
            change_state(ticker, duration1, 'low', current_stock_information['datetime'])
            accumulate_duration(ticker, "High_duration", duration1)
            print(f"{ticker} state changed from high to low at {criteria_low} and high signal duration>threshold")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and duration1>=threshold_duration:
            change_state(ticker, duration1, 'high', current_stock_information['datetime'])
            accumulate_duration(ticker, "Low_duration", duration1)
            print(f"{ticker} state changed from low to high at {criteria_high} and low signal duration>threshold")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and duration1<threshold_duration:
            reset_state(ticker, 'low', current_stock_information['datetime'])
            print(f"{ticker} state changed from high to low at {criteria_low}, high signal continued for {duration1}")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and duration1<threshold_duration:
            reset_state(ticker, 'high', current_stock_information['datetime'])
            print(f"{ticker} state changed from low to high at {criteria_high}, low signal continued for {duration1}")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        # 2-2 如果信號high/low->no_sig, 且大於設定時長, 就改值且加一行; 小於時長就只把state改回'no_sig
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and duration1>=threshold_duration:
            change_state(ticker, duration1, 'no_sig', current_stock_information['datetime'])
            accumulate_duration(ticker, "High_duration", duration1)
            print(f"{ticker} state changed from high to no_sig at {criteria_high} and high signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low and duration1>=threshold_duration:
            change_state(ticker, duration1, 'no_sig', current_stock_information['datetime'])
            accumulate_duration(ticker, "Low_duration", duration1)
            print(f"{ticker} state changed from low to no_sig at {criteria_low} and low signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and duration1<threshold_duration:
            reset_state(ticker, 'no_sig', current_stock_information['datetime'])
            print(f"{ticker} state changed from high to no_sig at {criteria_high}, high signal continued for {duration1}")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low  and duration1<threshold_duration:
            reset_state(ticker, 'no_sig', current_stock_information['datetime'])
            print(f"{ticker} state changed from low to no_sig at {criteria_low}, low signal continued for {duration1}")
        # 2-1 如果信號no_sig->high/low, 就改值
        elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_high>=threshold_high:
            reset_state(ticker, 'high', current_stock_information['datetime'])
            print(f"{ticker} state changed from no_sig to high at {criteria_high}")
        elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_low<=threshold_low:
            reset_state(ticker, 'low', current_stock_information['datetime'])
            print(f"{ticker} state changed from no_sig to low at {criteria_low}")

def change_state(ticker, duration1, new_state, new_time):
    global state_changes
    lock.acquire()
    state_changes[ticker][-1]['duration'] = duration1
    state_changes[ticker].append({'state': new_state, 'state_change_at': new_time})
    lock.release()

def reset_state(ticker, new_state, new_time):
    global state_changes
    lock.acquire()
    state_changes[ticker][-1]['state']= new_state
    state_changes[ticker][-1]['state_change_at'] = new_time
    lock.release()

def accumulate_duration(ticker, state, duration1):
    global accumulated_duration
    try:
        accumulated_duration.at[ticker, state] += duration1
    except Exception as e:
        accumulated_duration.at[ticker, state] = duration1
        print(f"<< {e} >> no previous value: duration initialized ")

def output_accumulated_duration(delay_duration_display): # 輸出高低狀態信號長度總和
    global accumulated_duration
    while True:
        time.sleep(delay_duration_display)
        accumulated_duration.sort_values(by=['Ticker'])
        print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        print(tabulate(accumulated_duration, headers='keys', tablefmt='psql'))

def output_newest_state(monitor, delay_table_display): # 每幾秒輸出一次當前信號
    global state_changes
    while True:
        time.sleep(delay_table_display)
        table = PrettyTable(['Ticker','state','state_change_at','duration'])
        current_states = pd.DataFrame()
        lock.acquire()
        for ticker in monitor:
            if state_changes[ticker] != []:
                if state_changes[ticker][-1]['state'] == 'high' or state_changes[ticker][-1]['state'] == 'low':
                    list1 = [ticker, state_changes[ticker][-1]['state'], datetime.strftime(state_changes[ticker][-1]['state_change_at'], "%H:%M"), convert_delta(datetime.now()-state_changes[ticker][-1]['state_change_at'])]
                    table.add_row(list1)
                    current_states.loc[len(current_states.index)] = list1
        lock.release()
        print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        print("PrettyTable")
        print(table.get_string(sortby="Ticker"))
        table.clear()
        current_states.sort_values(by=['Ticker'])
        print("tabulate")
        print(tabulate(current_states, headers='keys', tablefmt='psql'))
        del current_states
    print("error!!!!!!!!!!!!!!!!")

def convert_delta(dlt: timedelta) -> str:
    minutes, seconds = divmod(int(dlt.total_seconds()), 60)
    return f"{minutes}:{seconds:02}"

main()

######################## 我是分隔線 #################################
def stock_listener(queue):
    while len(queue) > 0:
        info = queue.popleft()
        ...


def main():
    monitor = ["1101", "3310", "1102", "1103", "1104", "1105"]
    threads = []
    for code in monitor:
        queue = msg_queue[code]
        thread = threading.Thread(target=stock_listener, arg=(queue,))
        threads.append(thread)

    for th in threads:
        th.daemon = True
        th.start()

    print(state_changes)

main()