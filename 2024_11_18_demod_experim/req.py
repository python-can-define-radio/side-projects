import zmq
import turtle
import random

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
myid = random.randint(0, 1000000)

def sendpos():
    x, y = turtle.pos()
    socket.send(f'{myid},{x},{y}'.encode())
    print(f"Received: {socket.recv()}")

def left():
    turtle.left(90)
    sendpos()

def right():
    turtle.right(90)
    sendpos()

def fwd():
    turtle.forward(25)
    sendpos()

turtle.onkeyrelease(left, "a")
turtle.onkeyrelease(fwd, "w")
turtle.onkeyrelease(right, "d")
turtle.listen()
turtle.mainloop()