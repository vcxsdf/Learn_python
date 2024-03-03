
# What is empty ?

# 型別裡面 空的
integer_var = 0
float_var = 0.0
string_var = ""
bool_var = False
arr_var = []
dictionary_var = {}
tuple_var = ()

# Java null -> Python None
integer_var = None # 真正的空......

# 缺陷
variable = None
if variable:
    print("exists")
else:
    print("not exists")

if variable is None:
    print("variable is empty")
else:
    print("variable is not empty")


# object reference, 可變 與 不可變
def add_object(arr):
    arr.append(6)   #
    print(arr) # 6

def modify_object(variable):
    variable = 2

def main():
    arr = [1, 2, 3, 4, 5] # 5
    add_object(arr)
    print(arr)

    variable = 1
    variable = modify_object(variable)
    print(variable)

    # 兩種 mutable, immutable
    # immutable
    int, float, bool, str, bytes, tuple
    variable = 2 #

    # mutable
    list, dict, set, # self defined data type class

def add(a, b):
    return a + b

f = lambda a, b: a+b
