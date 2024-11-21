import zmq
import turtle
import random
from threading import Thread
import time
import json
from queue import SimpleQueue

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


def updatepositions():
    xf, yf = myturtle.pos()
    x = int(xf)
    y = int(yf)
    cmd = f'{myid} MOVE {x} {y}'
    cmdqueue.put(cmd)


def readqueue():
    def sendcmd_and_update(cmd: str):
        sock.send(cmd.encode())
        locations = unserialize(sock.recv())
        # Update the local view of where everyone else is.
        for turtid, x, y in locations:
            if turtid != myid:
                t = getTurtle(turtid, players)
                t.goto(x, y)

    while True:
        cmd = cmdqueue.get(block=True)
        sendcmd_and_update(cmd)


def updateforever():
    while True:
        updatepositions()
        time.sleep(0.1)

def cmds():
    while True:
        cmd = input("Command or h for help: ")
        if cmd == "h":
            print(
                "Examples:\n"
                "SETPENCOLOR red\n"
                "SETFILLCOLOR green\n")
        else:
            cmdwithid = f"{myid} {cmd.upper()}"
            cmdqueue.put(cmdwithid)


def left():
    myturtle.left(90)

def right():
    myturtle.right(90)

def fwd():
    myturtle.forward(5)


sock = getsock()
players = {}
myid = str(random.randint(0, 1000000))
cmdqueue = SimpleQueue()
myturtle = getTurtle(myid, players)
myturtle.speed(0)
myturtle.penup()
turtle.onkeyrelease(left, "a")
turtle.onkeyrelease(fwd, "w")
turtle.onkeyrelease(right, "d")
turtle.listen()
Thread(target=updateforever).start()
Thread(target=readqueue).start()
Thread(target=cmds).start()
turtle.mainloop()