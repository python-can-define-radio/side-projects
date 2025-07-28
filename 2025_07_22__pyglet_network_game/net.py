import json
from typing import Callable

import deal
from classes import GameState
import zmq


@deal.has("network")
def make_zmq_pub(ip: str = "localhost") -> Callable[[GameState], None]:
    """Connect to `ip`. Return a function that serializes and sends GameState to `ip`."""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect(f"tcp://{ip}:5555")
    def snd(s: GameState):
        message = json.dumps(s.serialize())
        socket.send_string(message)
    return snd


@deal.has("network")
def make_zmq_sub() -> Callable[[], str]:
    """Connect to `ip`. Return a function that receives a string from `ip`."""
    subscriber_context = zmq.Context()
    subscriber_socket = subscriber_context.socket(zmq.SUB)
    subscriber_socket.connect("tcp://localhost:5566")
    subscriber_socket.setsockopt_string(zmq.SUBSCRIBE, "")
    return lambda: subscriber_socket.recv_string()




def ingest_messages(socket, current_players: "dict[ID, Obj]", self_id: ID) -> dict:
    """Ugly; probably should improve"""
    def receive_all():
        updates: "dict[ID, Obj]" = {}
        try:
            while True:
                message = socket.recv_string(flags=zmq.NOBLOCK)
                data = json.loads(message)
                if data["id"] != self_id:
                    updates[data["id"]] = Obj(**data)
        except zmq.Again:
            pass
        return updates

    # Start with a copy of the current state (immutability!)
    updated_players = dict(current_players)

    for pid, obj in receive_all().items():
        updated_players[pid] = obj

    return updated_players



@deal.has("network")
def publish_state(s: GameState):
    message = json.dumps(s.serialize())
    socket.send_string(message)