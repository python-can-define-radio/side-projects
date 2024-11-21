import zmq
from shared import getTurtle, Player
import json
from threading import Thread

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from turtle import Turtle
    from zmq.sugar.context import Context
    from zmq.sugar.socket import Socket


def zmqsock(port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://0.0.0.0:{port}")
    return socket

   
def serialize(pturtles: "dict[str, Turtle]") -> str:
    players = list(map(Player.turttodict, pturtles.items()))
    return json.dumps(players)


def updateAll(sock, pturtles: "dict[str, Turtle]"):
    message: str = sock.recv().decode()
    try:
        turtid, cmd, clientdata = message.split(" ", 2)
        if cmd == "MOVE":
            turt = getTurtle(turtid, pturtles)
            xs, ys = clientdata.split(" ")
            turt.goto(int(xs), int(ys))
        elif cmd == "SETPENCOLOR":
            turt = getTurtle(turtid, pturtles)
            turt.pencolor(clientdata)
        elif cmd == "SETFILLCOLOR":
            turt = getTurtle(turtid, pturtles)
            turt.fillcolor(clientdata)
        else:
            print("cmd", cmd, "not implemented")
    except ValueError:
        print("Invalid command")
    # elif cmd == "STAMP":
    #     turt = getTurtle(f"{turtid}_stamp_{random.randint(0, 100000)}", players)
    sock.send_string(serialize(pturtles))

# def cmdloop():
#     while True:
#         cmd = input("Admin command: ")
#         if cmd.startswith("kick"):
            


def main():
    print("Waiting for connections. You may want to use `ip a` to check your own ip address")
    pturtles: "dict[str, Turtle]" = {}
    sock = zmqsock(5555)
    # Thread(target=cmdloop).start()
    while True:
        updateAll(sock, pturtles)


if __name__ == "__main__":
    main()