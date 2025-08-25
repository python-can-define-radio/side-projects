import zmq

_context = zmq.Context()
from_players_sock = _context.socket(zmq.SUB)
from_players_sock.bind("tcp://*:5555")
from_players_sock.setsockopt_string(zmq.SUBSCRIBE, "")
to_players_sock = _context.socket(zmq.PUB)
to_players_sock.bind("tcp://*:5556")

def recv_player_msg() -> "dict | None":
    try:
        return from_players_sock.recv_json(flags=zmq.NOBLOCK)
    except zmq.Again:
        return None