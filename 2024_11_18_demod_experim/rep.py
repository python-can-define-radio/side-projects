import time
import zmq
import turtle
from dataclasses import dataclass
from shared import getTurtle
import json

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://0.0.0.0:5555")

players = {}
    

while True:
    message: str = socket.recv().decode()
    print(message)
    turtid, xs, ys = message.split(",")
    turt = getTurtle(turtid, players)
    turt.goto(float(xs), float(ys))
    socket.send_string(json.dumps({"data": [[1,2,3],[4,5,6]]}))
