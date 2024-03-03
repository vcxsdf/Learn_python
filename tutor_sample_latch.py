import copy  # 內建
from collections import defaultdict
from datetime import datetime

def main():
    """
    {
        3310: [
            {
                "bid_price": [10, 20, 30, 40, 50],
                "bid_volume": [10, 20, 30, 40, 50],
                "datatime": "2024-2-19 10:30",
                "code": 3310,
            },
            {
                "bid_price": [11, 21, 31, 41, 51],
                "bid_volume": [10, 20, 30, 40, 50],
                "datatime": "2024-2-19 10:32:21",
                "code": 3310,
            },
        ],
        1101: [
                {
                    "bid_price": [10, 20, 30, 40, 50],
                    "bid_volume": [10, 20, 30, 40, 50],
                    "datatime": "2024-2-19 10:30",
                    "code": 1101,
                },
                {
                    "bid_price": [11, 21, 31, 41, 51],
                    "bid_volume": [10, 20, 30, 40, 50],
                    "datatime": "2024-2-19 10:32",
                    "code": 1101,
                },
            ]
    }

    if price > 30 and code == 3310:
        ...
    """

    """
    pipeline -> bucket1 1101
             -> bucket2 3310
             -> bucket3 2330 

    stock_bucket = {
        1101: [], 
        3310: [],
        2330: [],
    }

    arr = [1, 2, 3]
    tuple = (1, 2, 3)  # 存資料
    """
    state_changes = {'code':[],'state_change_at':[],'state':[],'duration':[]}
    monitor=['2330','8299','2368','3228','6290','7556']
    msg_queue = [] # deque
    # How to clear deque

    monitor = [1101, 1102, 1103, 1105]

    stock_bucket = defaultdict(list)
    for ticker in monitor:  # Queue
        # 當下這個moment 100 筆資料
        snapshot_msg_queue = copy.deepcopy(msg_queue[ticker])
        clear(msg_queue[ticker])  # 清掉

        # first filtering  
        for stock_info in snapshot_msg_queue:
            
            # condition [10, 20, 30, 40, 50]
            # filtering
            # Get interesting information ... ,  
            if stock_info["bid_price"][0] + stock_info["bid_price"][4] > 100:
                info = (stock_info["datetime"], stock_info["bid_price"][2])
                # alternative
                info = {
                    "time": stock_info["datetime"],
                    "price": stock_info["bid_price"][2],
                }
            
                stock_bucket[ticker].append(info)
                # complicated logic ......
                #
                #

        # 我是分隔線 ----------------------------------------------------------------
        # second filtering 
        signal_bucket = defaultdict(list)
        previous_state = False  # True, price is larger than condition, False, price is lower than condition
        for stock_info in snapshot_msg_queue:
            now = datetime.strftime(stock_info["datetime"], "%Y-%m-%d %") # add datetime format to to seconds %s
            price = stock_info["bid_price"][2]
            previous = signal_bucket[ticker][-1]["dtime"]

            info = {
                "dtime": now,
                "price": price,
                "duration": now - previous,
            }

            condition = stock_info["bid_price"][0] + stock_info["bid_price"][4] > 100
            if condition is True and previous_state is False:
                signal_bucket[ticker].append(info)
                previous_state = True

            elif condition is False and previous_state is True:
                signal_bucket[ticker].append(info)
                previous_state = False

        ################################################################
        monitor.append(ticker)

        # for i in range(len(msg_queue[ticker])):  # msg_queue 可能永遠跑不完, 
        #     ...


if __name__ == '__main__':
    main()
    # arr = [{1}, {2}, {3}, {4}, {5}]
    # for i in range(len(arr)):
    #     print(arr[i])
    # print("*"*80)
    # for obj in arr:
    #     print(obj)
