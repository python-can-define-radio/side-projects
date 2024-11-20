import zmq
from dataclasses import dataclass
from shared import getTurtle
import json
from threading import Thread
import sys

from typing_extensions import TYPE_CHECKING
if TYPE_CHECKING:
    from turtle import Turtle

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://0.0.0.0:5555")

players: "dict[str, Turtle]" = {}
    
def serialize():
    for id_, turt in players.items():
        x, y = turt.pos()
        yield [id_, x, y]

def updateAll():
    global shouldquit
    while True:
        if shouldquit:
            sys.exit()
        message: str = socket.recv().decode()
        turtid, xs, ys = message.split(",")
        turt = getTurtle(turtid, players)
        turt.goto(float(xs), float(ys))
        socket.send_string(json.dumps({"data": list(serialize())}))

shouldquit = False
thread = Thread(target=updateAll)
thread.start()
while True:
    cmd = input("Cmd (h for help): ")
    if cmd == "h":
        print("h:   help")
        print("q:   quit")
        print("cl:  clear all pen markings")
        print("pu:  Pick up all pens")
    elif cmd == "cl":
        for t in players.values():
            t.clear()
    elif cmd == "pu":
        for t in players.values():
            t.penup()
    elif cmd == "q":
        print("exiting.")
        shouldquit = True
        break
        # sys.exit()