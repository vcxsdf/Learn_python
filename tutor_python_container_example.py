from collections import defaultdict, deque


def main():

    array = []  #
    array = [1, 2, 3, 4, 5, 6]
    dictionary = {}  # k, v

    # 1101, 2330, 2331

    event = {1101: 27}
    
    def event_generator():
        for i in range(100):
            yield {
                "key": 1101,
                "price": 27 + i
            }

        for i in range(100):
            yield {
                "key": 2330,
                "price": 300 + i
            }


    gen = event_generator()  # {1101: 27}, {2330: 301}


    # In practical, deque First in First out, (FIFO)

    """  # Queue
    2, 3, 4, 5  ->  []
    [2, 3, 4, 5] -> 
    [] -> 2, 3, 4, 5

    2 -> []
    [2]
    [] -> 2

    2 -> [3]
    [2, 3]
    [2] -> 3
    """

    """Double end Queue (Deque)

    """


    # normal_dict = {}   # {1101: [27, 28, 29, 30], 2330: [300, 301]}
    normal_default_dict = defaultdict(deque)
    for event in gen:
        # very boring .......
        # if 1101 not in normal_dict:
        #     normal_dict[1101] = []

        # if 2330 not in normal_dict:
        #     normal_dict[2330] = []

        normal_default_dict[event["key"]].append(event["price"])

    # import pprint  # pretty print
    # pprint.pprint(normal_default_dict)

    # find 2330 prices
    print(normal_default_dict[2330][0])

    key = { 
        2330:[1, 2, 3, 4, 5]
    }

main()