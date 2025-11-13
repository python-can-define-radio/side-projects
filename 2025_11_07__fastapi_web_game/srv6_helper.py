"""
>>> gs = GameState()

Initially no players, and some coins:
>>> gs.jsondumps()
'{"entities": {...coin...}, "players": {}}'

A client joins:
>>> ce = CliEvent('fakeid', '{"eventkind": "init", "name": "abc", "shape": "circle", "color": "green"}')
>>> gs.process_cli_msg(ce)
>>> gs.jsondumps()
'{"entities": {...}, "players": {"fakeid": {"x": 500, "y": 500, "name": "abc", "change_x": 0, "change_y": 0, "engaged_with": null}}}'
>>> gs.handleCE(CliEvent('fakeid', '{"eventkind": "keydown", "key": "w"}'))
>>> gs.jsondumps()
'{"entities": {...}, "players": {"fakeid": {"x": 500, "y": 500, "name": "abc", "change_x": 0, "change_y": -50, "engaged_with": null}}}'
"""
from dataclasses import dataclass, asdict
import json
import random
from typing import Literal, Callable


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
    change_x: int = 0
    change_y: int = 0
    location: str = "world"


@dataclass
class Entity:
    x: int
    y: int
    name: str
    img_loc: str
    img_size: float
    # on_touch: Callable[[Player], None] = lambda p: None


@dataclass
class CliEvent:
    """Client Event"""
    cid: str
    """Client ID"""
    payload_raw: str
    """A string which we can parse using get_payload"""

    def get_payload(self):
        """
        >>> ce = CliEvent('fakeid', '{"eventkind": "init", "name": "abc", "shape": "circle", "color": "green"}')
        >>> ce.get_payload()
        InitEv(name='abc', shape='circle', color='green', eventkind='init')
        """
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
    """
    Round numbers to the nearest point on a grid.
    Examples: Given a gridsize of 5, 21 is closer to 20, and 24 is closer to 25.
    >>> gridify(21, 5)
    20
    >>> gridify(24, 5)
    25
    """
    return round(val/gridsize) * gridsize


def makewalls():
    f = open("map.txt")
    lines = f.read().splitlines()
    f.close()
    if len(set(map(lambda x: len(x), lines))) != 1:
        raise ValueError("Map must be rectangular, that is, each line must have the same lengths")
    walls = {}
    xindexes = range(-1, len(lines[0]))
    yindexes = range(-1, len(lines))
    for yidx, line in zip(yindexes, lines):
        for xidx, char in zip(xindexes, line):
            if char == "w":
                walls[f"wall{xidx},{yidx}"] = Entity(500*xidx, 500*yidx, "", "/assets/brick2.png", 500)
    return walls


def makecoins():
    coins1 = {f"{x}": Entity(random.randrange(20, 980), random.randrange(20, 980), "", "/assets/coinGold.png", 40) for x in range(200)}
    coins2 = {f"{x+200}": Entity(random.randrange(4020, 4980), random.randrange(20, 980), "", "/assets/coinGold.png", 40) for x in range(200)}
    coins3 = {f"{x+400}": Entity(random.randrange(20, 980), random.randrange(4020, 4980), "", "/assets/coinGold.png", 40) for x in range(200)}
    coins4 = {f"{x+600}": Entity(random.randrange(4020, 4980), random.randrange(4020, 4980), "", "/assets/coinGold.png", 40) for x in range(200)}
    return {**coins1, **coins2, **coins3, **coins4}


@dataclass
class GameState:
    """Examples in docstring/doctests for module"""
    __players: "dict[str, Player]" 
    __entities: "dict[str, Entity]"
    def __init__(self):
        self.__players = {}
        self.__entities = {**makecoins(), **makewalls()}

    def process_cli_msg(self, ce: 'CliEvent | Disconnect'):
        """Update state based an event or a disconnect"""
        if type(ce) == Disconnect:
            self.handleDC(ce)
        elif type(ce) == CliEvent:
            self.handleCE(ce)
        else:
            raise NotImplementedError()

    def handleDC(self, ce: Disconnect):
        """Remove this player's ID from self.__players"""
        if ce.cid not in self.__players:
            # Sometimes handleDC fires multiple times for the same id. Not sure why.
            return
        print("I: Removing", ce.cid, "from dict")
        del self.__players[ce.cid]
        
    def handleCE(self, ce: CliEvent):
        """Update state when clients send events, such as mouse or keyboard input."""
        paylo = ce.get_payload()
        if type(paylo) == InitEv:
            self.__players[ce.cid] = Player(500, 500, paylo.name)
        elif type(paylo) == ClickEv:
            xcmp = self.__players[ce.cid].x - paylo.x
            ycmp = self.__players[ce.cid].y - paylo.y
            if xcmp < -20:
                self.__players[ce.cid].change_x = 50
            elif xcmp > 20:
                self.__players[ce.cid].change_x = -50
            else:
                self.__players[ce.cid].change_x = 0
            if ycmp < -20:
                self.__players[ce.cid].change_y = 50
            elif ycmp > 20:
                self.__players[ce.cid].change_y = -50
            else:
                self.__players[ce.cid].change_y = 0
        elif type(paylo) == KeydownEv:
            if paylo.key == "w":
                self.__players[ce.cid].change_y = -50
            elif paylo.key == "s":
                self.__players[ce.cid].change_y = 50
            elif paylo.key == "a":
                self.__players[ce.cid].change_x = -50
            elif paylo.key == "d":
                self.__players[ce.cid].change_x = 50
        elif type(paylo) == KeyupEv:
            if paylo.key in ["w", "s"]:
                self.__players[ce.cid].change_y = 0
            if paylo.key in ["a", "d"]:
                self.__players[ce.cid].change_x = 0

    def handle_collisions(self):
        for p in self.__players.values():
            for e in self.__entities.values():
                if p.x == e.x and p.y == e.y:
                    # e.on_touch(p)
                    ...
                

    def jsondumps(self):
        """Current state in json. Examples in module docstring/doctests"""
        entitiesdict = {k: asdict(v) for k, v in self.__entities.items()}
        playersdict = {k: asdict(v) for k, v in self.__players.items()}
        return json.dumps({
            "entities": entitiesdict,
            "players": playersdict,
        })

    def tick(self):
        """Move players based on their velocities, then return self.jsondump()"""
        for p in self.__players.values():
            p.x += p.change_x
            p.y += p.change_y
        self.handle_collisions()
        return self.jsondumps()
        
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

if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)