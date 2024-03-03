
# # 第一層 filter (過濾不要的資料), 第二層 filter (存state) 第三層 filter (計算duration)

def filter1():
    ...

def filter2():
    ...

def filter3():
    temp_queue = []

def filter4():
    ...
    
def pipeline():  # Mindset, Pipeline Design 
    generator = generate_stock_data()  # msg_queue
    # Target
    for data in generator:
        filtered_data1 = filter1(data)  # bid_price, datetime
        filtered_data2 = filter2(filtered_data1) # add state
        final_answer   = filter3(filtered_data2) # calculate duration


# yield
def stock_message_queue():
    arr = [] # 暫存
    for i in range(100):  # fixed size 
        arr.append(i)
    return arr

# 產生器  python yield
def stock_message_queue_optimize():
    for i in range(100):  # fixed size 
        yield i

generator = stock_message_queue_optimize()

print(next(generator))
print(next(generator))
print(next(generator))
print(next(generator))



# for number in stock_message_queue_optimize():
#     print(number)