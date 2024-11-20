import zmq
import turtle
import random
from threading import Thread
import time
import json

from shared import getTurtle


# Often, ADDR is set to an ip address, for example, "192.168.1.2"
ADDR = "localhost"


def getsock():
    context = zmq.Context()
    sock = context.socket(zmq.REQ)
    sock.connect(f"tcp://{ADDR}:5555")
    return sock
    

def unserialize(sockdata: str) -> "list[tuple[str, int, int]]":
    sockjson = json.loads(sockdata)
    return sockjson["locations"]


def updatepositions(sock, players, myid):
    xf, yf = turtle.pos()
    x = int(xf)
    y = int(yf)
    sock.send(f'MOVE,{myid},{x},{y}'.encode())
    locations = unserialize(sock.recv())
    # Update the local view of where everyone else is.
    for turtid, x, y in locations:
        if turtid != myid:
            t = getTurtle(turtid, players)
            t.goto(x, y)


def updateforever():
    sock = getsock()
    players = {}
    myid = str(random.randint(0, 1000000))

    while True:
        updatepositions(sock, players, myid)
        time.sleep(0.1)
        

def left():
    turtle.left(90)

def right():
    turtle.right(90)

def fwd():
    turtle.forward(5)


turtle.speed(0)
turtle.penup()
turtle.onkeyrelease(left, "a")
turtle.onkeyrelease(fwd, "w")
turtle.onkeyrelease(right, "d")
turtle.listen()
Thread(target=updateforever).start()
turtle.mainloop()