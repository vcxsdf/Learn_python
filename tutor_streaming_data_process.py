
a = [1, 2, 3, 4, 5]
val = a.pop()
print(val)

import copy
# streaming -> 串流 -> non-stopping
# original deque     outputs <- [1, 2, 3, 4, 5] <- inputs time=1
# new deque copy.deepcopy [1, 2, 3, 4, 5] time=2
# time=2 [1, 2, 3, 4, 5, 6] # original deque  (Race condition)
# 

from collections import deque



import time
import datetime
# new code
monitor = deque([1101, 1102, 1103]) # 自定義
msg_queue = {
    1101: deque([1, 2, 3, 4, 5]),
    1102: deque([10, 20, 30, 40, 50, 60]),
    1103: deque([100, 100]),
}

counter = 18
while counter > 0:
    # Error handling, 1. 可容忍錯誤, 2. 不可容忍錯誤
    try:
        current_stock_code = monitor.popleft() # 1101
    except Exception:
        raise Exception
    monitor.append(current_stock_code)

    current_stock_queue: deque = msg_queue[current_stock_code]  # [1, 2, 3, 4, 5]

    try:
        current_stock_information = current_stock_queue.popleft() # 1
    except Exception:
        # print("no signal at", time.time())
        print("no signal at", datetime.now())
        counter -= 1
        continue

    print(f"{counter}#: stock code: {current_stock_code}, current value: {current_stock_information}")

    # do something with current_stock_information
    # filter_set() .....
    # filter_status() ....
    #
    counter -= 1
