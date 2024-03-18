from collections import deque
# Python, 
# pass by object reference#
# pass by reference
# mutable object, -> reference

def your_listener(var: int):
    var = 2

def main():
    int, float, bool, str, tuple
    # 如果更改他, 完全create new object

    list, dict, set, # class 相關 class deque, class ......
    # 如果更改他, 不會create new object

    """
    pass mutable object to function -> reference
    """

    var = 1
    your_listener(var)
    print(var)

main()