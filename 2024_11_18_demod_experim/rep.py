import time
import zmq
import turtle
from dataclasses import dataclass

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://0.0.0.0:5555")

players = {}

def newturt():
    t = turtle.Turtle()
    t.shape("circle")
    return t

def getTurtle(id_: str):
    if id_ not in players.keys():
        players[id_] = newturt()
    return players[id_]
    

while True:
    message: str = socket.recv().decode()
    print(message)
    turtid, xs, ys = message.split(",")
    turt = getTurtle(turtid)
    turt.goto(float(xs), float(ys))
    socket.send(b"R")
