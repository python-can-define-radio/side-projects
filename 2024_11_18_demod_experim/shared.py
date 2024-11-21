from turtle import Turtle
from dataclasses import dataclass, asdict
import json


def newturt():
    t = Turtle()
    t.shape("circle")
    t.penup()
    return t


def getTurtle(id_: str, pturtles: "dict[str, Turtle]") -> Turtle:
    """Note: this mutates `pturtles`!"""
    if id_ not in pturtles.keys():
        pturtles[id_] = newturt()
    return pturtles[id_]


@dataclass
class Player:
    id_: str
    x: int
    y: int
    pencolor: str
    fillcolor: str

    # def tojson(self) -> str:
    #     return json.dumps(asdict(self))
    
    @staticmethod
    def fromdict(data: dict) -> "Player":
        return Player(**data)

    @staticmethod
    def fromturtle(id_: str, t: Turtle) -> "Player":
        return Player(
            id_,
            int(t.xcor()),
            int(t.ycor()),
            t.pencolor(),
            t.fillcolor()
        )
    
    @staticmethod
    def turttodict(idturt: "tuple[str, Turtle]") -> dict:
        return asdict(Player.fromturtle(idturt[0], idturt[1]))
    