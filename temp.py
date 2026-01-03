from enum import Enum

class State(str, Enum):
    ...



d = {
    "a": 1,
    "b": 2,
}

def function(a, b):
    print(a, b)


function(a=1, b=2)