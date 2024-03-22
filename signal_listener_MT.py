# multithreading, one per stock
# one thread for display current signal summary
# periodically save state_changes to sqlite3
# 漲跌停 表格會鎖在states裡 因為買賣一邊信號為0會被濾掉

# 如果用lock, 跑一陣 可能會卡state
# todo: deal with 漲停跌停
# known issue: DB write not working

import shioaji as sj # 永豐API
from shioaji import BidAskSTKv1, Exchange
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import time
import pandas as pd
from tabulate import tabulate
from prettytable import PrettyTable
import sqlite3
from sqlite3 import Error
from apscheduler.schedulers.background import BackgroundScheduler

def main():
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(listener_control, 'cron', day_of_week='0-4', hour=9, minute=0)
    scheduler.start()
    now = datetime.now()
    while now < datetime(year = now.year, month = now.month, \
        day = now.day, hour = 13, minute = 35) : # 最晚到1:35pm
        time.sleep(30)
        now = datetime.now()
    print("end")

def listener_control():
    monitor = deque(['2317','3163','3050'])
    threshold_high = 100   
    threshold_low = 30  #
    threshold_duration = timedelta(seconds=1) # e.g. days=2, hours=1, minutes=30, seconds=2
    delay_signal_display = 10 # 每幾秒印一次信號表格
    delay_duration_display = 15 # 每幾秒印一次信號表格
    db_file = r"D:\sqlite.db"
    table_name = 'signal_realtime_MT'

    global msg_queue, state_changes, accumulated_duration, lock, conn

    conn = create_connection(db_file)
    msg_queue = defaultdict(deque)
    state_changes = defaultdict(list) # 存狀態改變, 結構={'ticker': [{'state_change_at': ...,'state': high/low/no_sig, 'duration': ...}, {}, ...]}
    accumulated_duration = pd.DataFrame({
        "Ticker": [],
        "High_duration": [],
        "Low_duration": []
    })
    accumulated_duration.set_index('Ticker', inplace=True)

    register_stock_code(monitor)

    for ticker in monitor:
        thread = threading.Thread(target=stock_listener, args=(ticker, msg_queue[ticker], threshold_high, threshold_low, threshold_duration, table_name))
        thread.daemon = True
        thread.start()

    t_output_accumulated_duration = threading.Thread(target=output_accumulated_duration, args=(delay_duration_display,))  #建立執行緒
    t_output_accumulated_duration.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
    t_output_newest_state = threading.Thread(target=output_newest_state, args=(monitor, delay_signal_display,))  #建立執行緒
    t_output_newest_state.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束

    t_output_accumulated_duration.start()  #執行
    t_output_newest_state.start()  #執行

    program_starts = time.time()
    while True:
        """經過四小時半就停止程式"""
        now = time.time()
        timeframe = now - program_starts 
        if timeframe > 16220: # seconds 
            break
        time.sleep(30)
        continue
# refactor
def register_stock_code(monitor):
    #Login
    api = sj.Shioaji()   # Production Mode
    api.login(
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

def stock_listener(ticker, current_stock_queue, threshold_high, threshold_low, threshold_duration, table_name):
    global state_changes, accumulated_duration

    while True: #len(msg_queue[ticker]) > 0:
        """
        1. get and clean values from msg_queue
        """
        if len(current_stock_queue) ==0:
            time.sleep(5)
            continue
        current_stock_info = current_stock_queue.popleft() 
        """
        2. record state changes
        """
        """
        setting starts
        """
        criteria_high = current_stock_info['bid_price'][0]
        criteria_low  = current_stock_info['ask_price'][0]
        date_time = current_stock_info['datetime']
    
        if criteria_high==0 or criteria_low==0: # 如果輸入值為0就直接跳過 否則會造成state出錯
            continue

        """dev DB access"""
        # 改datatype成 float 才能存DB
        price_avg = float((criteria_low+criteria_high)/2)
        insert_to_DB(table_name, [ticker, date_time, price_avg, criteria_high])
        """
        setting ends
        """
        #  2-0 初始化, 
        if state_changes[ticker] == []:
            # print(f"initializing state_changes[{ticker}]")
            string = "{ticker} state initiated to {op} at {criteria}"
            if criteria_high>=threshold_high:
                state_changes[ticker].append({'state': 'high', 'state_change_at': current_stock_info['datetime'], 'duration': 0})
                string.format(ticker=ticker,op="high",criteria=criteria_high)

            elif criteria_low<=threshold_low:
                state_changes[ticker].append({'state': 'low', 'state_change_at': current_stock_info['datetime'], 'duration': 0})
                string.format(ticker=ticker,op="low",criteria=criteria_low)
            
            else:
                state_changes[ticker].append({'state': 'no_sig', 'state_change_at': current_stock_info['datetime'], 'duration': 0})
                string.format(ticker=ticker,op="no_sig",criteria=criteria_low)
            
            print(string)
            continue
    
        # TODO: refactor this
        state_change_duration = date_time-state_changes[ticker][-1]['state_change_at']
        # 2-3 如果信號high/low->low/high, 且大於設定時長, 就改值且加一行; 小於時長就只把state改成low/high
        if state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and state_change_duration>=threshold_duration:
            change_state(ticker, state_change_duration, 'low', current_stock_info['datetime'])
            accumulate_duration(ticker, "High_duration", state_change_duration)
            print(f"{ticker} state changed from high to low at {criteria_low} and high signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and state_change_duration>=threshold_duration:
            change_state(ticker, state_change_duration, 'high', current_stock_info['datetime'])
            accumulate_duration(ticker, "Low_duration", state_change_duration)
            print(f"{ticker} state changed from low to high at {criteria_high} and low signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_low<=threshold_low and state_change_duration<threshold_duration:
            reset_state(ticker, 'low', current_stock_info['datetime'])
            print(f"{ticker} state changed from high to low at {criteria_low}, high signal continued for {state_change_duration}")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_high>=threshold_high and state_change_duration<threshold_duration:
            reset_state(ticker, 'high', current_stock_info['datetime'])
            print(f"{ticker} state changed from low to high at {criteria_high}, low signal continued for {state_change_duration}")
        # 2-2 如果信號high/low->no_sig, 且大於設定時長, 就改值且加一行; 小於時長就只把state改回'no_sig
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and state_change_duration>=threshold_duration:
            change_state(ticker, state_change_duration, 'no_sig', current_stock_info['datetime'])
            accumulate_duration(ticker, "High_duration", state_change_duration)
            print(f"{ticker} state changed from high to no_sig at {criteria_high} and high signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low and state_change_duration>=threshold_duration:
            change_state(ticker, state_change_duration, 'no_sig', current_stock_info['datetime'])
            accumulate_duration(ticker, "Low_duration", state_change_duration)
            print(f"{ticker} state changed from low to no_sig at {criteria_low} and low signal duration>threshold")
        elif state_changes[ticker][-1]['state'] == 'high' and criteria_high<threshold_high and state_change_duration<threshold_duration:
            reset_state(ticker, 'no_sig', current_stock_info['datetime'])
            print(f"{ticker} state changed from high to no_sig at {criteria_high}, high signal continued for {state_change_duration}")
        
        elif state_changes[ticker][-1]['state'] == 'low' and criteria_low>threshold_low  and state_change_duration<threshold_duration:
            reset_state(ticker, 'no_sig', current_stock_info['datetime'])
            print(f"{ticker} state changed from low to no_sig at {criteria_low}, low signal continued for {state_change_duration}")
        
        # 2-1 如果信號no_sig->high/low, 就改值
        elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_high>=threshold_high:
            reset_state(ticker, 'high', current_stock_info['datetime'])
            print(f"{ticker} state changed from no_sig to high at {criteria_high}")
        elif state_changes[ticker][-1]['state'] == 'no_sig' and criteria_low<=threshold_low:
            reset_state(ticker, 'low', current_stock_info['datetime'])
            print(f"{ticker} state changed from no_sig to low at {criteria_low}")

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

def accumulate_duration(ticker, state, duration1):
    global accumulated_duration
    try:
        accumulated_duration.at[ticker, state] += duration1
    except Exception as e:
        accumulated_duration.at[ticker, state] = duration1
        print(f"<< {e} >> no previous value: {ticker} duration initialized ")

def output_accumulated_duration(delay_duration_display): # 輸出高低狀態信號長度總和
    global accumulated_duration
    while True:
        time.sleep(delay_duration_display)
        print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        print(tabulate(accumulated_duration.sort_values(by=['Ticker']), headers='keys', tablefmt='psql'))

def output_newest_state(monitor, delay_table_display): # 每幾秒輸出一次當前信號
    # get newest states and output if values are high or low
    global state_changes
    while True:
        table = PrettyTable(['Ticker','state','state_change_at','duration'])
        for ticker in monitor:
            if len(state_changes[ticker]) == 0:
                continue
            last_state, state_time = state_changes[ticker][-1]['state'], state_changes[ticker][-1]['state_change_at']
            if last_state == 'high' or last_state == 'low':
                table.add_row([ticker, last_state, datetime.strftime(state_time, "%H:%M"), convert_delta(datetime.now() - state_time)])
        print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        print(table.get_string(sortby="Ticker"))
        table.clear()
        time.sleep(delay_table_display)

        # use tabulate to print
        """Exception in thread Thread-58 (output_newest_state)"""
        # print("use tabulate to print")
        # current_states = pd.DataFrame({'Ticker':[], 'High_duration':[], 'Low_duration':[]})
        # # lock.acquire()
        # for ticker in monitor:
        #     # if state_changes[ticker] != []:
        #     if state_changes[ticker][-1]['state'] == 'high' or state_changes[ticker][-1]['state'] == 'low':
        #         list1 = [ticker, state_changes[ticker][-1]['state'], datetime.strftime(state_changes[ticker][-1]['state_change_at'], "%H:%M"), convert_delta(datetime.now()-state_changes[ticker][-1]['state_change_at'])]
        #         current_states.loc[len(current_states.index)] = list1
        # # lock.release()
        # current_states=current_states.sort_values(by=['Ticker'])
        # print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        # print(tabulate(current_states, headers='keys', tablefmt='psql'))
        # del current_states
    print("error!!!!!!!!!!!!!!!!")

def convert_delta(dlt: timedelta) -> str:
    minutes, seconds = divmod(int(dlt.total_seconds()), 60)
    return f"{minutes}:{seconds:02}"

def insert_to_DB(table_name, values):
    global conn
    # values.to_sql(name=table_name, con=conn, if_exists='append', index=False)
    c=conn.cursor()
    c.execute('insert into {}(ticker, ts, price, ratio) values (?, ?, ?, ?)'.format(table_name), values)
    conn.commit()

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

main()