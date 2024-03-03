
def foo_function(param):
    print("hello world", param)


def add(*variable):  # 塞多個
    sum_var = 0
    for number in variable:
        sum_var += number
    return sum_var

def add_no_default(a, b, c, d, e):
    return a + b + c + d + e

def add_default(a=1, b=2, c=3, d=4, e=5):
    return a + b + c + d + e
