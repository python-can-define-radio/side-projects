##### Sender
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect ("tcp://10.1.1.1:5556")
socket.send_string("Hello!")



##### Server
import sys
import zmq

context = zmq.Context()
socket_rx = context.socket(zmq.SUB)
socket_tx = context.socket(zmq.PUB)

socket_rx.bind("tcp://*:5556")
socket_tx.bind("tcp://*:5557")

topicfilter = ""
socket_rx.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

rcvd = socket_rx.recv_string()
socket_tx.send_string(rcvd)



##### Receiver

import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect ("tcp://10.1.1.1:5557")

topicfilter = ""
socket_rx.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

rcvd = socket_rx.recv_string()
