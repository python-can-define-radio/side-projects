from functools import lru_cache
from math import sin
from typing import Callable
from more_itertools import flatten, grouper
from guizero import App, Drawing


def lmap(f, x):
    return list(map(f, x))

def lflatten(x):
    return list(flatten(x))

def lgrouper(n, iterable):
    return list(grouper(n, iterable))

def bin_(x):
    return f"{x:08b}"

def int2(x: "list[str]") -> int:
    """Given a list of bits, treat the list as a single
    binary number (MSB first), and return the associated integer"""
    joi = "".join(x)
    return int(joi, 2)

def longshort(x) -> "list[int]":
    if x == "0":
        return [1, 0]
    elif x == "1":
        return [1, 1, 1, 0]
    else:
        raise NotImplementedError()


@lru_cache
def wave(bit: int):
    ln = 10
    wv = lmap(sin, range(0, ln))
    if bit == 1:
        return wv
    elif bit == 0:
        return [0] * ln
    else:
        print(bit)
        print(type(bit))
        raise NotImplementedError()


def morse_mod(bits: "list[str]"):
    a = lflatten(lmap(longshort, bits))
    # print("morsed:", a)
    b = lflatten(lmap(wave, a))
    # print("waved:", b)
    return b


def modulate(plain_text_msg: str) -> "list[str]":
    a = list(plain_text_msg)
    b = lmap(ord, a)
    # print("Converted to decimal:", a)
    c = lmap(bin_, b)
    # print("Converted to binary:", b)
    d = lflatten(c)
    # print("Flattened:", d)
    e = morse_mod(d)
    return e


def demodulate(mod_msg: "list[str]") -> str:
    a = lgrouper(8, mod_msg)
    b = lmap(int2, a)
    c = lmap(chr, b)
    d = "".join(c)
    return d

class Datum:
    def __init__(self, v):
        self.v = v
        self.x = 0

    def update(self, cblocks: "list[CBlock]"):
        self.x += 2
        if self.x > cblocks[0].x:
            self.v = cblocks[0].func(self.v)
            import sys
            sys.exit()

    def draw(self):
        drawing.text(self.x, 0, self.v)
        

class CBlock:
    def __init__(self, func: Callable, x: int, y: int):
        self.func = func
        self.x = x
        self.y = y
    def draw(self):
        drawing.rectangle(self.x, self.y, self.x+100, self.y+30, color="cyan", outline=True, outline_color="black")
        drawing.text(self.x, self.y, self.func.__name__)

class DrawingTracker:
    def __init__(self, msg: "list[str]", cblocks: "list[CBlock]"):
        self.cblocks = cblocks
        self.waiting: "list[Datum]" = lmap(Datum, msg)
        self.displaying: "list[Datum]" = []
        self.spacing = 0

    def add_to_displayed(self):
        if not self.waiting:
            return
        if self.spacing > 50:
            d = self.waiting.pop(0)
            self.displaying.append(d)
            self.spacing = 0 
        self.spacing += 2

    def updatetext(self):
        drawing.clear()
        self.add_to_displayed()
        for d in self.displaying:
            d.update(self.cblocks)
            d.draw()
        for cb in self.cblocks:
            cb.draw()
        
# plain_text_msg = input("Type a message: ")
def times_two(x):
    return x * 2
app = App()
drawing = Drawing(app, width="fill", height="fill")
plain_text_msg = "abc"
cblocks = [CBlock(times_two, 50, 0)]
dtr = DrawingTracker(list(plain_text_msg), cblocks)
drawing.repeat(20, dtr.updatetext)
app.display()
modulated = modulate(plain_text_msg)
# print(f"Modulated message: {modulated}")
# demod = demodulate(modulated)
# print(f"Demodulated message: {demod}")



# - explore making our own binary data transmitter so we can send "text messages" from hack rf to hack rf

# Transmit "LOL"
# -> Convert each letter to decimal numbers,
#    then binary
# -> Prepend a preamble
# -> BFSK modulate using audio (whistling)
# -> Use URH to demod as FSK:
#    -> Filter
#    -> find dividing line between frequencies
#    -> convert from binary back to ASCII