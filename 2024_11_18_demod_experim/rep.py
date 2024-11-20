import random
import zmq
from dataclasses import dataclass
from shared import getTurtle
import json
from threading import Thread
import sys

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from turtle import Turtle
    from zmq.sugar.context import Context
    from zmq.sugar.socket import Socket

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://0.0.0.0:5555")

players: "dict[str, Turtle]" = {}
    
def serialize():
    for id_, turt in players.items():
        x, y = turt.pos()
        yield [id_, x, y]

def updateAll():
    while True:
        message: str = socket.recv().decode()
        cmd, turtid, xs, ys = message.split(",")
        if cmd == "MOVE":
            turt = getTurtle(turtid, players)
            turt.penup()
            turt.goto(int(xs), int(ys))
        else:
            print("cmd", cmd, "not implemented")
        # elif cmd == "STAMP":
        #     turt = getTurtle(f"{turtid}_stamp_{random.randint(0, 100000)}", players)
        socket.send_string(json.dumps({"data": list(serialize())}))


print("Waiting for connections. You may want to use `ip a` to check your own ip address")
updateAll()