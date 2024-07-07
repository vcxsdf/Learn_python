
import threading, time, threading, multiprocessing
from copy import deepcopy
from datetime import datetime, timedelta
from collections import defaultdict, deque
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor

msg_queue = defaultdict(deque)
state_changes = defaultdict(list) # 存狀態改變, 結構={'ticker': [{'state_change_at': ...,'state': high/low/no_sig, 'duration': ...}, {}, ...]}
accumulated_duration = pd.DataFrame({
"Ticker": [],
"High_duration": [],
"Low_duration": []
})
accumulated_duration.set_index('Ticker', inplace=True)
first_state_change = pd.DataFrame({
"Ticker": [],
"High_initiation": [],
"Low_initiation": []
})
first_state_change.set_index('Ticker', inplace=True)


'''=========== deepcopy會說deque mutated during iteration or sth ==========='''


while datetime.now() < endtime:
    threads = []
    threshold_pairs = [(1/5, 5), (1/4, 4), (1/3, 3) ] # [(1/5, 5)]
    for ticker in data_input['ticker']:
        if len(msg_queue[ticker])!=0:
            # lock.acquire()
            msg_queue_to_compute = deepcopy(msg_queue[ticker])
            del msg_queue[ticker]
            # lock.release()
            for threshold in threshold_pairs:
                current_stock_queue = deepcopy(msg_queue_to_compute)
                thread = threading.Thread(target=stock_listener, args=(ticker, current_stock_queue, threshold[1], threshold[0], threshold_duration, db_file, table_name, delay_msg_queue_cleared, ))
                threads.append(thread)
            del msg_queue_to_compute
    for run_threads in threads:
        run_threads.daemon = True
        run_threads.start()
    time.sleep(delay_queue_dispatch)


'''=========== 舊的做法, 跑的快很多 ==========='''



def stock_listener(ticker, current_stock_queue, threshold_high, threshold_low, threshold_duration, db_file, table_name, delay_msg_queue_cleared):
    global state_changes, accumulated_duration, first_state_change

    print("listening start for ", ticker, " at ", datetime.now())
    while True: #len(msg_queue[ticker]) > 0:
        """
        1. get and clean values from msg_queue
        """
        if len(current_stock_queue) ==0:
            # print("queue for ", ticker, " is 0")
            time.sleep(delay_msg_queue_cleared)
            continue
        current_stock_information = current_stock_queue.popleft()
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
        """dev DB access"""
        # 改datatype成 float 才能存DB
        price_avg = float((current_stock_information['ask_price'][0]+current_stock_information['bid_price'][0])/2)
        values = [ticker, current_stock_information['datetime'], price_avg, criteria_high]
        # insert2DB(db_file, table_name, values)
        """
        setting ends
        """
        # print("state machine calc for ", ticker)
        #  2-0 初始化,
        if state_changes[ticker] == []:
            # print(f"initializing state_changes[{ticker}]")
            # lock.acquire()
            if criteria_high>=threshold_high:
                state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_information['datetime'], 'duration': 0})
                # print(f"{ticker} state initiated to high at {criteria_high}")
            elif criteria_low<=threshold_low:
                state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_information['datetime'], 'duration': 0})
                # print(f"{ticker} state initiated to low at {criteria_low}")
            else:
                state_changes[ticker].append({'state': 'no_sig', 'state_change_at': current_stock_information['datetime'], 'duration': 0})
                # print(f"{ticker} state initiated to no_sig at {criteria_low}")
            # lock.release()
            continue
        duration1 = current_stock_information['datetime']-state_changes[ticker][-1]['state_change_at']
        # 2-3 如果信號high/low->low/high, 且大於設定時長, 就改值且加一行; 小於時長就只把state改成low/high
        if state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and duration1>=threshold_duration:
            change_state(ticker, duration1, 'low', current_stock_information['datetime'])
            accumulate_duration(ticker, "High_duration", duration1, current_stock_information['datetime'])
            # print(f"{ticker} state changed from high to low at {criteria_low} and high signal duration>threshold")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and duration1>=threshold_duration:
            change_state(ticker, duration1, 'high', current_stock_information['datetime'])
            accumulate_duration(ticker, "Low_duration", duration1, current_stock_information['datetime'])
            # print(f"{ticker} state changed from low to high at {criteria_high} and low signal duration>threshold")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and duration1<threshold_duration:
            reset_state(ticker, 'low', current_stock_information['datetime'])
            # print(f"{ticker} state changed from high to low at {criteria_low}, high signal continued for {duration1}")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and duration1<threshold_duration:
            reset_state(ticker, 'high', current_stock_information['datetime'])
            # print(f"{ticker} state changed from low to high at {criteria_high}, low signal continued for {duration1}")
            continue #怕跟轉no_sig條件重複, 所以high/low互轉就跳開
        # 2-2 如果信號high/low->no_sig, 且大於設定時長, 就改值且加一行; 小於時長就只把state改回'no_sig
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and duration1>=threshold_duration:
            change_state(ticker, duration1, 'no_sig', current_stock_information['datetime'])
            accumulate_duration(ticker, "High_duration", duration1, current_stock_information['datetime'])
            # print(f"{ticker} state changed from high to no_sig at {criteria_high} and high signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low and duration1>=threshold_duration:
            change_state(ticker, duration1, 'no_sig', current_stock_information['datetime'])
            accumulate_duration(ticker, "Low_duration", duration1, current_stock_information['datetime'])
            # print(f"{ticker} state changed from low to no_sig at {criteria_low} and low signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and duration1<threshold_duration:
            reset_state(ticker, 'no_sig', current_stock_information['datetime'])
            # print(f"{ticker} state changed from high to no_sig at {criteria_high}, high signal continued for {duration1}")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low  and duration1<threshold_duration:
            reset_state(ticker, 'no_sig', current_stock_information['datetime'])
            # print(f"{ticker} state changed from low to no_sig at {criteria_low}, low signal continued for {duration1}")
        # 2-1 如果信號no_sig->high/low, 就改值
        elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_high>=threshold_high:
            reset_state(ticker, 'high', current_stock_information['datetime'])
            # print(f"{ticker} state changed from no_sig to high at {criteria_high}")
        elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_low<=threshold_low:
            reset_state(ticker, 'low', current_stock_information['datetime'])
            # print(f"{ticker} state changed from no_sig to low at {criteria_low}")

def change_state(ticker, duration1, new_state, new_time):
    global state_changes
    # lock.acquire()
    #debug
    # print(f"{ticker} state {state_changes[ticker][-1]} before change")
    state_changes[ticker][-1]['duration'] = duration1
    state_changes[ticker].append({'state': new_state, 'state_change_at': new_time})
    #debug
    # print(f"{ticker} state {state_changes[ticker][-1]} after change")
    # lock.release()

def reset_state(ticker, new_state, new_time):
    global state_changes
    # lock.acquire()
    state_changes[ticker][-1]['state']= new_state
    state_changes[ticker][-1]['state_change_at'] = new_time
    # lock.release()

def accumulate_duration(ticker, state, duration1, time_state_change):
    global accumulated_duration, first_state_change
    try:
        accumulated_duration.at[ticker, state] += duration1
    except Exception as e:
        accumulated_duration.at[ticker, state] = duration1
        if state == "High_duration":
            first_state_change.at[ticker, "High_initiation"] = time_state_change.strftime('%H:%M')
        elif state == "Low_duration":
            first_state_change.at[ticker, "Low_initiation"] = time_state_change.strftime('%H:%M')
        # print(f"<< {e} >> no previous value: {ticker} duration initialized ")


'''=========== 新的做法, 速度比舊的慢超多 根本跑不動 ==========='''

# 把DF當作DB用
output_signal = pd.DataFrame(columns=["ticker","signal_type","operator","threshold",
        "first_sig","duration","current_state","state_changed_at","last_checked_at"])

def signal_listener(monitor, target_n_threshold, threshold_duration, data_input, s_local_file):
    global msg_queue, output_signal
    # threshold_df = threshold_df['signal_type', 'operator', 'threshold']
    # signal_type: price, volume
    # operator: greater, less, equal
    while True:
        output_update = pd.DataFrame()
        for ticker in monitor:
            current_stock_queue, current_status = pd.DataFrame(), pd.DataFrame()
            current_stock_queue = msg_queue[ticker]
            signal_types_thresholds = register_signal_types(target_n_threshold[target_n_threshold['ticker']==ticker])
            current_status = output_signal[output_signal['ticker'] == ticker]
            print(f"processing {ticker} with msg_queue data length {len(current_stock_queue)}")
            while len(current_stock_queue)>0:
                current_stock_info = current_stock_queue.popleft() 
                # handle signals
                # print(f"looping{ticker}, current length {len(current_stock_queue)}")
                for signal_type, thresholds in signal_types_thresholds.items():
                    if signal_type == 'price':
                        handle_price_signal(ticker, current_status, current_stock_info, thresholds, threshold_duration)
                    elif signal_type == 'volume':
                        handle_volume_signal(ticker, current_stock_info, thresholds)
            output_update = pd.concat([output_update, current_status], ignore_index=True)
            print(f"updateing output_update: {output_update}")
        print("ended looping")
        output_signal = output_update
        html_content_generator(clean_output_for_html(output_signal, data_input), s_local_file, len(monitor))
        # print(msg_queue)
        input("Press Enter to continue...") # msg_queue[ticker]



def handle_price_signal_state_true(mask, current_status, current_time):
    if current_status.at[current_status[mask].index[0], 'current_state'] == False: # 0->1
        current_status.at[current_status[mask].index[0], 'current_state'] = True
        current_status.at[current_status[mask].index[0], 'state_changed_at'] = current_time
    current_status.at[current_status[mask].index[0], 'last_checked_at'] = current_time
    return current_status

def handle_price_signal_state_false(mask, current_status, current_time, threshold_duration):
    if current_status.at[current_status[mask].index[0], 'current_state'] == True: # 1->0
        last_checked_at = current_status.at[current_status[mask].index[0], 'last_checked_at']
        state_changed_at = current_status.at[current_status[mask].index[0], 'state_changed_at']
        delta_duration = last_checked_at - state_changed_at
        if delta_duration > threshold_duration: # 大於
            duration = current_status.at[current_status[mask].index[0], 'duration']
            current_status.at[current_status[mask].index[0], 'duration'] = duration + delta_duration
            if pd.isna(current_status.at[current_status[mask].index[0], 'first_sig']): # 若還沒記錄第一次發生就紀錄
                current_status.at[current_status[mask].index[0], 'first_sig'] = state_changed_at
        current_status.at[current_status[mask].index[0], 'current_state'] = False
        current_status.at[current_status[mask].index[0], 'state_changed_at'] = current_time
    current_status.at[current_status[mask].index[0], 'last_checked_at'] = current_time
    return current_status

def handle_price_signal(ticker, current_status, current_stock_info, thresholds, threshold_duration):
    signal_type = 'price'
    current_time = current_stock_info['datetime']
    price = current_stock_info['price']

    for operator, threshold in thresholds:
        mask = (current_status['ticker'] == ticker) & \
            (np.abs(current_status['threshold'] - np.float64(threshold)) < 1e-10) &\
            (current_status['signal_type'] == signal_type) & \
            (current_status['operator'] == operator) 
        # print(f"current status is \n{current_status}")
        # print(f"current status .at[mask, 'current_state'] is\n {current_status.at[current_status[mask].index[0], 'current_state']}")
        if (price ==0): 
            current_status = handle_price_signal_state_false(mask, current_status, current_time, threshold_duration)
        else:
            if ((operator == 'greater') and (price > threshold)) or ((operator == 'less') and (price < threshold)):
                current_status = handle_price_signal_state_true(mask, current_status, current_time)
            elif ((operator == 'greater') and (price < threshold)) or ((operator == 'less') and (price > threshold)):
                current_status = handle_price_signal_state_false(mask, current_status, current_time, threshold_duration)
    return current_status

def register_signal_types(threshold_df):
    signal_types_thresholds = {}

    for index, row in threshold_df.iterrows():
        signal_type = row['signal_type']
        operator = row['operator']
        threshold = row['threshold']
        
        if signal_type not in signal_types_thresholds:
            signal_types_thresholds[signal_type] = []
        
        signal_types_thresholds[signal_type].append((operator, threshold))
    
    return signal_types_thresholds

'''=========== Multiprocessing ==========='''
# multiprocessing.Process ?
# ProcessPoolExecutor ?


'''result_queue 要用global嗎? 還是傳入functions就可以'''
def queue_dispatcher_controller(monitor, target_n_threshold, threshold_duration, delay_msg_queue_cleared, endtime):
    global msg_queue, output_signal, result_queue, msg_queue_cleared_flag
    result_queue = multiprocessing.Queue() # 收運算結果
    # manager = multiprocessing.Manager()
    # processed_tickers = manager.list()
    print("dispatch_ctrl")
    # 13:25之前 如果個股已經跑完 且有新資料 就新增process處理
    now = datetime.now()
    while now < endtime:
        listening_result_handler()
        queue_dispatcher(processed_tickers, msg_queue, monitor, target_n_threshold, threshold_duration)
        time.sleep(delay_msg_queue_cleared) # delay_msg_queue_cleared
        now = datetime.now()

    unregister_tickers_PSC(monitor) # 13:25就停止收資料
    while len(processed_tickers)>0: # 等之前的跑完
        time.sleep(delay_msg_queue_cleared)
    listening_result_handler()
    queue_dispatcher(processed_tickers, msg_queue, monitor, target_n_threshold, threshold_duration) # 開始跑最後一部分
    while len(processed_tickers)>0: # 等最後一部分跑完
        time.sleep(delay_msg_queue_cleared)
    listening_result_handler()
    print("msg_queue processing finished at", datetime.now())
    msg_queue_cleared_flag = 1

def listening_result_handler():
    global output_signal, result_queue
    # 有當機的話 就加上LOCK
    while not result_queue.empty():
        result = result_queue.get()
        # ['ticker', 'signal_type', 'operator','threshold', 'first_sig', 'duration','current_state',"state_changed_at","last_checked_at"]
        # print("Result from process:", result)
        result_dict = result.set_index(['ticker', 'signal_type', 'operator', 'threshold']).to_dict(orient='index')
        # Update 'output_signal' based on 'result'
        for idx, row in output_signal.iterrows():
            key = (row['ticker'], row['signal_type'], row['operator'], row['threshold'])
            if key in result_dict:
                result_row = result_dict[key]
                output_signal.at[idx, 'first_sig'] = result_row['first_sig']
                output_signal.at[idx, 'duration'] = result_row['duration']
                output_signal.at[idx, 'current_state'] = result_row['current_state']
                output_signal.at[idx, 'state_changed_at'] = result_row['state_changed_at']
                output_signal.at[idx, 'last_checked_at'] = result_row['last_checked_at']

''' 用processed_tickers = manager.list() 確認哪些執行中 '''
def queue_dispatcher(processed_tickers, msg_queue, monitor, target_n_threshold, threshold_duration):
    global output_signal, result_queue
    print("entering dispatcher")
    processes = []
    for ticker in monitor:
        if (ticker not in processed_tickers) & (len(msg_queue[ticker])!=0):
            current_stock_queue = deepcopy(msg_queue[ticker]) # 撈出現有資料
            del msg_queue[ticker] # 刪掉將用multiprocess處理之資料
            processed_tickers.append(ticker)
            threshold_df = target_n_threshold[target_n_threshold['ticker']==ticker]
            current_status = output_signal[output_signal['ticker'] == ticker]
            process = multiprocessing.Process(
                target=stock_listener,
                args=(ticker, current_status, current_stock_queue, threshold_df, threshold_duration, processed_tickers, result_queue,)
            )
            processes.append(process)
            # print("start process for ", ticker, "with threshold", ticker_input['threshold_high'].iloc[0])
    for run_processes in processes:
        run_processes.start()
    for run_processes in processes:
        run_processes.join()

''' 用with ProcessPoolExecutor() as executor 執行, 要等 所以會比較慢? '''
def queue_dispatcher(processed_tickers, msg_queue, monitor, target_n_threshold, threshold_duration):
    global output_signal, result_queue
    print("entering dispatcher")

    # 用ProcessPoolExecutor()啟動
    with ProcessPoolExecutor() as executor:
        futures = []
        for ticker in monitor:
            if (ticker not in processed_tickers) and (len(msg_queue[ticker]) != 0):
                current_stock_queue = deepcopy(msg_queue[ticker])  # 撈出現有資料
                del msg_queue[ticker]  # 刪掉將用multiprocess處理之資料
                print(f"procsssing {ticker} with len {len(msg_queue[ticker])}")
                processed_tickers.append(ticker)
                threshold_df = target_n_threshold[target_n_threshold['ticker'] == ticker]
                current_status = output_signal[output_signal['ticker'] == ticker]
                
                # Submit task to ProcessPoolExecutor
                future = executor.submit(
                    stock_listener,
                    ticker, current_status, current_stock_queue, threshold_df, threshold_duration, processed_tickers, result_queue
                )
                futures.append(future)

        # Wait for all futures to complete
        for future in futures:
            future.result()
        print("futures finished")

def stock_listener(ticker, current_status, current_stock_queue, threshold_df, threshold_duration, processed_tickers, result_queue):
    # threshold_df = threshold_df['signal_type', 'operator', 'threshold']
    # signal_type: price, volume
    # operator: greater, less, equal
    signal_types_thresholds = register_signal_types(threshold_df)
    print("entering stock listener")
    while len(current_stock_queue) >0:
        # get and clean values from msg_queue
        current_stock_info = current_stock_queue.popleft() 
        
        # handle signals
        for signal_type, thresholds in signal_types_thresholds.items():
            if signal_type == 'price':
                current_status = handle_price_signal(ticker, current_status, current_stock_info, thresholds, threshold_duration)
            elif signal_type == 'volume':
                current_status = handle_volume_signal(current_stock_info, thresholds)
    result_queue.put(current_status)
    processed_tickers.remove(ticker)


''' =========== 打開multiprocess時 rayinAPI.py下面偵測的code會跑起來 然後嘗試連線. 因為主程式已經連過 就壞了 =========== '''

class testPyAPI(rayinAPI):
    def __init__(self):
        super().__init__()
        self.FIsLogon = False  # 登入狀態註記預設false
        self.rNo = "0"  # 回補電文預設0

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    processed_tickers = manager.list()
    main()

main()

''' ===========  rayinAPI.py =========== '''
import platform
import os, sys
from ctypes import *

if platform.system() == 'Windows':
    print('---------------------------- API detect ----------------------------')
    path = os.getcwd()

    if platform.system() == 'Windows':
        print('----- detect : Windows platform -----')
        if (sys.maxsize > 2 ** 32) == True:
            # 檢查檔案是否存在
            dllpath = os.path.join(path, 'RayinVTS_64.dll')
            if not os.path.isfile(dllpath):
                print("RayinVTS_64.dll檔案不存在。")
                os._exit(0)
            dll = windll.LoadLibrary(dllpath)
            print('載入RayinVTS_64.dll檔' + dllpath)
        else:
            dllpath = os.path.join(path, 'RayinVTS.dll')
            if not os.path.isfile(dllpath):
                print("RayinVTS.dll檔案不存在。")
                os._exit(0)
            dll = windll.LoadLibrary(dllpath)
            print('RayinVTS.dll檔' + dllpath)
    else:
        print("不是Windows platform")
        os._exit(0)