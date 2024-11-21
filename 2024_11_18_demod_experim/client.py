import zmq
import turtle
import random
from threading import Thread
import time
import json
from queue import SimpleQueue

from shared import getTurtle, Player


# Often, ADDR is set to an ip address, for example, "192.168.1.2"
ADDR = "localhost"

def getsock():
    context = zmq.Context()
    sock = context.socket(zmq.REQ)
    sock.connect(f"tcp://{ADDR}:5555")
    return sock
    

def unserialize(sockdata: str):
    sockjson: "list[dict]" = json.loads(sockdata)
    return list(map(Player.fromdict, sockjson))


def updatepositions():
    xf, yf = myturtle.pos()
    x = int(xf)
    y = int(yf)
    cmd = f'{myid} MOVE {x} {y}'
    cmdqueue.put(cmd)


def readqueue():
    def sendcmd_and_update(cmd: str):
        sock.send(cmd.encode())
        players = unserialize(sock.recv())
        # Update the local view of where everyone else is.
        for player in players:
            t = getTurtle(player.id_, pturtles)
            t.pencolor(player.pencolor)
            t.fillcolor(player.fillcolor)
            # Don't goto because it might cause race condition lag odd movements
            if player.id_ != myid:
                t.goto(player.x, player.y)

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
pturtles = {}
myid = str(random.randint(0, 1000000))
cmdqueue = SimpleQueue()
myturtle = getTurtle(myid, pturtles)
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