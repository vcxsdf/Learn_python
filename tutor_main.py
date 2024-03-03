from package import add, add_default, foo_function

# syntax sugar
# *
# **


def main2():
    # add(1, 2, 3, 4 ,5 ,6)
    arr = [1, 2, 3, 4, 5]
    print(add(*arr))  # -> arr(1, 2, 3, 4, 5)

    number_dictionary = {
        "a": 1000,
        "b": 2000,
        "c": 3000,
    }
    # * list, tuple (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]
    # ** {"a":1, "b":2, "c":3, "d":4, "e":5}
    print(add_default(*number_dictionary))


class Stock:
    def __init__(self, stock_number: str, open: float, close: float) -> None:
        self.stock_number = None
        self.open = None

def main():
    # stock = Stock(
    #     stock_number="3310", 
    #     open=100, 
    #     close=120
    # )
    foo_function("I'm test1")
    ...

@api.on_bidask_stk_v1(bind=True)
def quote_callback(self, exchange, bidask):
    print(f"Exchange: {exchange}, BidAsk: {bidask.bid_volume, bidask.ask_volume}")
    # append quote to message queue
    # self[bidask.code].append(bidask)這個存全部
    self[bidask.code].append(bidask.ask_volume)
    self[bidask.code].append(bidask.bid_volume)

    """
    {
        "time": [10, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        "code": [1101, 1101, 1102, ...]
        "ask_volume": [11萬, 11萬, ...],
        "bid_volume": [12萬, 11萬, ...],
    }
    """

if __name__ == "__main__":
    main()
