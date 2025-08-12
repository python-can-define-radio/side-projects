## Ideas:
## - test whether this works with multiple players currently
## - Use pyglet instead of turtle
## - Keybindings


from dataclasses import dataclass
import zmq
import threading
import turtle


@dataclass
class Entity:
    eid: str
    x: int
    y: int
    turt: turtle.Turtle


ents: "list[Entity]" = []

context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world serverâ€¦")
to_srv_sock = context.socket(zmq.PUB)
to_srv_sock.connect("tcp://localhost:5555")
from_srv_sock = context.socket(zmq.SUB)
from_srv_sock.connect("tcp://localhost:5556")
from_srv_sock.setsockopt_string(zmq.SUBSCRIBE, "")


def find_ent_by_id(id_: str) -> "Entity | None":
    for e in ents:
        if e.eid == id_:
            return e
    return None    


def update_ent_attr(e: Entity, message: dict):
    atn = message["attrname"]
    val = message["val"]
    if atn == "shape":
        e.turt.shape(val)
    elif atn == "x":
        e.x = int(val)
    elif atn == "y":
        e.y = int(val)
    else:
        raise NotImplementedError()


def update_state(message: dict):
    """Set all positions of entities; create new entities as needed"""
    
    matching_ent = find_ent_by_id(message["eid"])
    if matching_ent is None:
        e = Entity(eid=message["eid"], x=0, y=0, turt=turtle.Turtle())
        e.turt.penup()
        ents.append(e)
    else:
        e = matching_ent
    update_ent_attr(e, message)
    
    

def update_ui():
    for e in ents:
        e.turt.goto(e.x, e.y)


def send():
    while True:
        eid = input("Which one do you want to move? ")
        attrname = input("Which attr?")
        val = input("New val?")
        to_srv_sock.send_json({"eid": eid, "attrname": attrname, "val": val})


def recv():
    while True:
        message = from_srv_sock.recv_json()
        print(f"Received request: {message}")
        update_state(message)
        update_ui()


st = threading.Thread(target=send)
st.start()

rt = threading.Thread(target=recv)
rt.start()