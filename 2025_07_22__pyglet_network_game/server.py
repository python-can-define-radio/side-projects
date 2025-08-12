import zmq


context = zmq.Context()
from_players_sock = context.socket(zmq.SUB)
from_players_sock.bind("tcp://*:5555")
from_players_sock.setsockopt_string(zmq.SUBSCRIBE, "")
to_players_sock = context.socket(zmq.PUB)
to_players_sock.bind("tcp://*:5556")

while True:
    message = from_players_sock.recv_json()
    print(f"Received request: {message}")
    to_players_sock.send_json(message)
