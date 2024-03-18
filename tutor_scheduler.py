import time
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

def job1():
        # client = shioija(name, password)
        # pricing = client.request_twse("廣達")

        # if pricing > 151:
        #     # short ....
        #     # pop notification
        #     ...
    print(f'hello I am job 1  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def job2():
    #     client = shioija(name, password)
    #     pricing = client.request_twse("台積電")

    #     if pricing < 500:
    #         # buy
    #         # pop notification
    #         ...
    print(f'hello I am job 2  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
def job3(var):
    print(f'{var} hello I am job 3  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def job4(var):
    print(f'{var} hello I am job 4  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def main():

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # interval有weeks days hours minutes seconds
    # cron有year month day hour minute second day_of_week
    scheduler.add_job(job1, 'interval', seconds=0)

    scheduler.add_job(job2, 'interval', seconds=2)

    var = 'test'
    scheduler.add_job(job3, trigger='interval', args= [var], seconds=3)
    # scheduler.add_job(lambda: job3(var), trigger='interval', seconds=3)

    # can add other file? 
    # can pass variable to functions?
    scheduler.add_job(job4, 'cron', day_of_week='0-4', hour=9, minute=0)

    scheduler.start()

    print('Schedule started ...')

    while True:
        time.sleep(10) # 暫停10秒鐘
        print("I'm still alive....")

if __name__ == "__main__":
    main()

# 開關功能
"""sample 2"""

import schedule
import time


def job():
    program_starts = time.time()

    while True:
        now = time.time()
        timeframe = now - program_starts
        print("It has been {0} seconds since the loop started".format(timeframe))
        if timeframe > 3600:
            break

schedule.every().day.at("19:20:30").do(job)

while True:
    schedule.run_pending()
    #time.sleep(60) # wait one minute