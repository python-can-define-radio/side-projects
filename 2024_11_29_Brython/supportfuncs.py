from more_itertools import flatten

def addself(x):
    return x + x

def lmap(f, x):
    return list(map(f, x))

def bin_(x):
    return f"{x:08b}"

