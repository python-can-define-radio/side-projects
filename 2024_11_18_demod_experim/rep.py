import zmq
from shared import getTurtle
import json

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

   
def serialize(players: dict) -> str:
    def do():
        for id_, turt in players.items():
            x, y = turt.pos()
            yield [id_, x, y]
    locations = list(do())
    return json.dumps({"locations": locations})


def updateAll(sock, players):
    message: str = sock.recv().decode()
    cmd, turtid, clientdata = message.split(",", 2)
    if cmd == "MOVE":
        xs, ys = clientdata.split(",")
        turt = getTurtle(turtid, players)
        turt.goto(int(xs), int(ys))
    else:
        print("cmd", cmd, "not implemented")
    # elif cmd == "STAMP":
    #     turt = getTurtle(f"{turtid}_stamp_{random.randint(0, 100000)}", players)
    sock.send_string(serialize(players))


def main():
    print("Waiting for connections. You may want to use `ip a` to check your own ip address")
    players: "dict[str, Turtle]" = {}
    sock = zmqsock(5555)
    while True:
        updateAll(sock, players)


if __name__ == "__main__":
    main()