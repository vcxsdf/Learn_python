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
    
def job3():
    print(f'hello I am job 3  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def job4():
    print(f'hello I am job 4  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def main():

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    scheduler.add_job(job1, 'interval', seconds=0)

    scheduler.add_job(job2, 'interval', seconds=2)

    scheduler.add_job(job3, 'interval', seconds=3)

    scheduler.add_job(job4, 'cron', day_of_week='1-6', hour=18, minute=30)

    scheduler.start()

    print('Schedule started ...')

    while True:
        time.sleep(0) # 暫停10秒鐘
        print("I'm still alive....")

if __name__ == "__main__":
    main()