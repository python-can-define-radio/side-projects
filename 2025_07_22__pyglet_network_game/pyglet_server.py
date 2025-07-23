import zmq

context = zmq.Context()

# SUB socket: binds to receive incoming publisher connections
sub_socket = context.socket(zmq.SUB)
sub_socket.bind("tcp://*:5555")                # ⬅ Game publishers connect to this address
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

# PUB socket: rebroadcasts to subscribers
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:5566")                # ⬅ Clients subscribe here

print("Relay server listening for publishers...")

while True:
    message = sub_socket.recv_string()
    print("Relaying", message)
    pub_socket.send_string(message)
