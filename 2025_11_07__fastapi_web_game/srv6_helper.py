from dataclasses import dataclass, field, asdict
import json
import random
from typing import Literal


@dataclass
class InitEv:
    name: str
    shape: str
    color: str
    eventkind: Literal['init']


@dataclass
class KeydownEv:
    key: str
    eventkind: Literal['keydown']


@dataclass
class KeyupEv:
    key: str
    eventkind: Literal['keyup']


@dataclass
class ClickEv:
    x: int
    y: int
    eventkind: Literal['click']


@dataclass
class Player:
    x: int
    y: int
    name: str
    shape: str
    color: str
    change_x: int = 0
    change_y: int = 0
    engaged_with: "Entity | None" = None


@dataclass
class Entity:
    x: int
    y: int
    name: str
    img_loc: str
    img_scale: float


@dataclass
class CliEvent:
    """Client Event"""
    cid: str
    """Client ID"""
    payload_raw: str
    """A string which we can parse using get_payload"""

    def get_payload(self):
        try:
            parsed = json.loads(self.payload_raw)
            if parsed["eventkind"] == "init":
                return InitEv(**parsed)
            elif parsed["eventkind"] == "keydown":
                return KeydownEv(**parsed)
            elif parsed["eventkind"] == "keyup":
                return KeyupEv(**parsed)
            elif parsed["eventkind"] == "click":
                return ClickEv(**parsed)
            else:
                raise NotImplementedError()
        except json.JSONDecodeError:
            raise ValueError(f"Client {self.cid} sent invalid JSON: '{self.payload_raw}'")

@dataclass
class Disconnect:
    """Disconnect message from a client"""
    cid: str
    """Client ID"""


def gridify(val, gridsize):
    return (val // gridsize) * gridsize

        
@dataclass
class GameState:
    __players: "dict[str, Player]" 
    __entities: "dict[str, Entity]"
    def __init__(self):
        self.__players = {}
        coins = {f"{x}": Entity(random.randrange(10, 4990), random.randrange(10, 4990), "", "assets/coinGold.png", .2) for x in range(200)}
        # walls = {x:Entity(x, y, "", "", "")}
        self.__entities = coins


    def process_cli_msg(self, ce: 'CliEvent | Disconnect'):
        """The return value is sent to the clients.
        Return value looks like this:
        
        {
            "entities": {"cactus1": Entity(...), ...}
            "players": {"abcd": Player(20, 30, ...), "efgh": Player(7, 200, ...)},
        }
        """
        
        if type(ce) == Disconnect:
            self.handleDC(ce)
        elif type(ce) == CliEvent:
            self.handleCE(ce)
        else:
            raise NotImplementedError()
        

    def handleDC(self, ce: Disconnect):
        if ce.cid in self.__players:
            print("I: Removing", ce.cid, "from dict")
            del self.__players[ce.cid]
        else:
            print("W: Attempted to remove", ce.cid, "but it was already absent.")

    def handleCE(self, ce: CliEvent):
        p = ce.get_payload()
        if type(p) == InitEv:
            self.__players[ce.cid] = Player(200, 300, p.name, p.shape, p.color)
        elif type(p) == ClickEv:
            self.__players[ce.cid].x = gridify(p.x, 5)
            self.__players[ce.cid].y = gridify(p.y, 5)
        elif type(p) == KeydownEv:
            if p.key == "w":
                self.__players[ce.cid].change_y = -5
            elif p.key == "s":
                self.__players[ce.cid].change_y = 5
            elif p.key == "a":
                self.__players[ce.cid].change_x = -5
            elif p.key == "d":
                self.__players[ce.cid].change_x = 5
        elif type(p) == KeyupEv:
            if p.key in ["w", "s"]:
                self.__players[ce.cid].change_y = 0
            if p.key in ["a", "d"]:
                self.__players[ce.cid].change_x = 0

    def handle_collisions(self):
        for p in self.__players.values():
            for e in self.__entities.values():
                if p.x == e.x and p.y == e.y:
                    p.engaged_with = e
                else:
                    p.engaged_with = None

    def tick(self):
        """Move players based on their velocities."""
        for p in self.__players.values():
            p.x += p.change_x
            p.y += p.change_y
        self.handle_collisions()
        entitiesdict = {k: asdict(v) for k, v in self.__entities.items()}
        playersdict = {k: asdict(v) for k, v in self.__players.items()}
        return json.dumps({
            "entities": entitiesdict,
            "players": playersdict,
        })
"""

Making a game...
trying to teach EM concepts

1. Add some inanimate stuff so we can tell that we're moving :-)
  - Create some entities (once)
  - Send that data to the clients
  - Draw on client side
1b. Larger world
2. switch to turn-based
Open world, then turn-based when engaged in an EM-sim situation

you're running around and encounter an enemy. popup window or something of the sort you can choose to engage or run away. if engagement happens then switches to turn-based



EM Sim: Client side or server side?
Client side:
 pros:
  - reduces server load for the most intensive part of the game
  - might be lower lag (avoids round-trip to server)
 cons:
  - more javascript code
  - need to find an EM sim lib for JS
  

--------------------------------
Thinking about the idea of using third-party simulation websites:
- When they engage with a challenge, it gives...
  - directions about how to set up the sim
  - Something they would report back?
    - A number?
    - A screenshot?
    - A set of settings?


stop now

1:00 pm to 1:30 pm 


4:45 pm to 5:30 pm

"""

