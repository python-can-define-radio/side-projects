import zmq
import turtle
import random
from threading import Thread
import time
import json

from shared import getTurtle

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
myid = random.randint(0, 1000000)


def updatepositions():
    xf, yf = turtle.pos()
    x = int(xf)
    y = int(yf)
    socket.send(f'{myid},{x},{y}'.encode())
    others = json.loads(socket.recv())
    for turtid, x, y in others["data"]:
        print(turtid, x, y)


def updateforever():
    while True:
        updatepositions()
        time.sleep(0.1)

def left():
    turtle.left(90)
    updatepositions()

def right():
    turtle.right(90)
    updatepositions()

def fwd():
    turtle.forward(25)
    updatepositions()

turtle.speed(0)
turtle.onkeyrelease(left, "a")
turtle.onkeyrelease(fwd, "w")
turtle.onkeyrelease(right, "d")
turtle.listen()
Thread(target=updateforever).start()
turtle.mainloop()