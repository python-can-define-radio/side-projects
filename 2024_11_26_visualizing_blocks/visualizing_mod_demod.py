from __future__ import annotations
from functools import lru_cache
from math import sin
from typing import Callable, TypeVar, Generic, Any
from more_itertools import flatten, grouper  # type: ignore[import-untyped]
from guizero import App, Drawing  # type: ignore[import-untyped]


T = TypeVar("T")
U = TypeVar("U")


def lmap(f, x):
    return list(map(f, x))

def lflatten(x):
    return list(flatten(x))

def lfilter(f: Callable[[T], bool], x: "list[T]") -> "list[T]":
    return list(filter(f, x))

def lgrouper(n, iterable):
    return list(grouper(n, iterable))

def lzip(a, b):
    return list(zip(a, b))


def int2(x: "list[str]") -> int:
    """Given a list of bits, treat the list as a single
    binary number (MSB first), and return the associated integer"""
    joi = "".join(x)
    return int(joi, 2)

def longshort(x: str) -> "list[int]":
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


# def modulate(plain_text_msg: str) -> "list[str]":
#     a = list(plain_text_msg)
#     b = lmap(ord, a)
#     # print("Converted to decimal:", a)
#     c = lmap(bin_, b)
#     # print("Converted to binary:", b)
#     d = lflatten(c)
#     # print("Flattened:", d)
#     e = morse_mod(d)
#     return e


def demodulate(mod_msg: "list[str]") -> str:
    a = lgrouper(8, mod_msg)
    b = lmap(int2, a)
    c = lmap(chr, b)
    d = "".join(c)
    return d


class Datum(Generic[T]):
    def __init__(self, v: T, fullwidth: int):
        self.v = v
        self.x = fullwidth + 50
        self.y = 20
        self.done_block_ids: "list[int]" = []
        self.fullwidth = fullwidth

    def newdat(self, newval, blid) -> "Datum":
        """Return a new Datum with the current
        attrs copied except for those provided in the args."""
        newdatum = Datum(newval, self.fullwidth)
        newdatum.x = self.x
        newdatum.done_block_ids = self.done_block_ids + [blid]
        return newdatum


    def apply_current_block(self, sblocks: "list[SBlock]") -> "list[Datum]":
        """Given current position, determine what processing block
        needs to happen now (if any)."""
        def seen_and_not_surpassed(cb: SBlock[Any, Any]) -> bool:
            return (
                id(cb) not in self.done_block_ids and
                self.x < cb.x and
                self.y == cb.y
            )

        seennotsurp = lfilter(seen_and_not_surpassed, sblocks)
        if seennotsurp == []:
            return [self]  # no blocks seen; nothing to do
        elif len(seennotsurp) > 1:
            raise NotImplementedError("Blocks are too close together because two were seen simultaneously.")
        else:
            currentblock = seennotsurp[0]
            f = currentblock.func
            newval = f(self.v)
            return [self.newdat(newval, id(currentblock))]

    def updatepos(self):
        self.x -= 2
        if self.x < -70:
            self.x = self.fullwidth
            self.y += 100

    def update(self, sblocks: "list[SBlock]") -> "list[Datum]":
        self.updatepos()
        newdat = self.apply_current_block(sblocks)
        return newdat

    def draw(self, drawing: Drawing) -> None:
        if isinstance(self.v, str):
            drawing.text(self.x, self.y, self.v)
        elif isinstance(self.v, (int, float)):
            drawing.rectangle(self.x, self.y, self.x+5, self.y+5)
        else:
            drawing.text(self.x, self.y, repr(self.v))
        

class SBlock(Generic[T, U]):
    def __init__(self, func: Callable[[T], U], pos: "tuple[int, int]"):
        self.func = func
        self.x = pos[0]
        self.y = pos[1]

    def draw(self, drawing: Drawing):
        drawing.rectangle(self.x-4, self.y-4, self.x+225, self.y+30, color="cyan", outline=True, outline_color="black")
        drawing.text(self.x, self.y, self.func.__name__)
    
    def __repr__(self):
        return f"<SBlock id: {id(self)} funcname: {self.func.__name__} x: {self.x}  y: {self.y}>"


class DrawingTracker(Generic[T]):
    def __init__(self, data: "list[T]", sblocks: "list[SBlock]", fullwidth: int, drawing: Drawing, dataspacing: int):
        makeDatum = lambda v: Datum(v, fullwidth)
        self.sblocks = sblocks
        self.waiting: "list[Datum[T]]" = lmap(makeDatum, data)
        self.displaying: "list[Datum[Any]]" = []
        self.dataspacing = dataspacing
        self.spacing = 0
        self.drawing = drawing

    def add_to_displayed(self):
        """Modifies self.waiting, self.displaying, and self.spacing."""
        if not self.waiting:
            return
        if self.spacing > self.dataspacing:
            d = self.waiting.pop(0)
            self.displaying.append(d)
            self.spacing = 0 
        self.spacing += 2

    def updatetext(self):
        self.drawing.clear()
        self.add_to_displayed()
        self.displaying = lflatten([d.update(self.sblocks) for d in self.displaying])
        for d in self.displaying:
            d.draw(self.drawing)
        for sb in self.sblocks:
            sb.draw(self.drawing)


class Slowgraph:
    def __init__(self, initial_data: "list[T]", funcs: "list[Callable]", dataspacing: int = 150):
        self.app = App(width=1400)
        drawing = Drawing(self.app, width="fill", height="fill")
        sblocks = Slowgraph.place_blocks(funcs)
        self.dtr = DrawingTracker(initial_data, sblocks, self.app.width, drawing, dataspacing)
        drawing.repeat(20, self.dtr.updatetext)

    @staticmethod
    def place_blocks(funcs: "list[Callable]"):
        grid = [
            (1050, 20),  (600, 20),  (150, 20),
            (1050, 120), (600, 120), (150, 120),
        ]
        makesblock = lambda x: SBlock(*x)
        funcgrid = lzip(funcs, grid)
        sblocks = lmap(makesblock, funcgrid)
        return sblocks

    def display(self):
        self.app.display()



def main():

    def ord_(x: str) -> str:
        return str(ord(x))

    def bin_(x: str) -> str:
        intx = int(x)
        return f"{intx:08b}"

    funcs = [ord_, bin_, list]
    msg = "abc"
    listymsg = list(msg)
    slowg = Slowgraph(listymsg, funcs, dataspacing=300)
    slowg.display()


if __name__ == "__main__":
    main()





# modulated = modulate(plain_text_msg)
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