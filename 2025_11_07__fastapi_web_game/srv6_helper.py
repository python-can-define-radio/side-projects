"""
>>> gs = GameState(create_entities=False)

Initially no players:
>>> gs.current()
{'dynamic': {}, 'players': {}}

A client joins:
>>> ce = CliEvent('fakeid', '{"eventkind": "init", "name": "abc", "avatar": "/assets/somefile.png"}')
>>> gs.process_cli_msg(ce)
>>> gs.current()
{'dynamic': {}, 'players': {'fakeid': Player(x=500, y=500, name='abc', avatar='/assets/somefile.png', change_x=0, change_y=0)}}

>>> gs.handleCE(CliEvent('fakeid', '{"eventkind": "keydown", "key": "w"}'))
>>> gs.current()
{'dynamic': {}, 'players': {'fakeid': Player(x=500, y=500, name='abc', avatar='/assets/somefile.png', change_x=0, change_y=-50)}}
"""
import copy
from dataclasses import dataclass
import dataclasses
import json
import random
from typing import Literal, Callable


@dataclass
class InitEv:
    name: str
    avatar: str
    """a path to the image location. Example: /assets/tree.png"""
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
    avatar: str = "/assets/femaleAdventurer_idle.png"
    change_x: int = 0
    change_y: int = 0

    def todict(self):
        return dataclasses.asdict(self)


@dataclass
class Entity:
    x: int
    y: int
    name: str
    avatar: str
    passable: bool
    on_touch_: "Callable[[Entity, Player]] | None" = None
    def on_touch(self, p: Player):
        if self.on_touch_:
            self.on_touch_(self, p)
    def todict(self):
        """
        Omits attrs that end with _
        >>> Entity(3, 5, "abc", "/assets/cool.png", True).todict()
        {'x': 3, 'y': 5, 'name': 'abc', 'avatar': '/assets/cool.png', 'passable': True}
        """
        def impl():
            fds = dataclasses.fields(self.__class__)
            for fd in fds:
                if not fd.name.endswith("_"):
                    yield fd.name, getattr(self, fd.name)
        return dict(impl())
           
        

@dataclass
class CliEvent:
    """Client Event"""
    cid: str
    """Client ID"""
    payload_raw: str
    """A string which we can parse using get_payload"""

    def get_payload(self):
        """Parse the payload to the appropriate event type. Examples in module docstring/doctests"""
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


def loadmap(currentmap):
    f = open(currentmap)
    lines = f.read().splitlines()
    f.close()
    static = {}
    dynamic = {}
    xindexes = range(-10, len(lines[0]))
    yindexes = range(-10, len(lines))
    for yidx, line in zip(yindexes, lines):
        for xidx, char in zip(xindexes, line):
            if char == "w":
                static[f"wall{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/brick2.png", False)
            elif char == "t":
                static[f"tree{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/tree.png", False)
            elif char == "c":
                dynamic[f"coin{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/coin.png", True)
            elif char == "👮":
                dynamic[f"npc{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/alienBlue_front.png", False)
    return static, dynamic


@dataclass
class GameState:
    """Examples in docstring/doctests for module"""
    __players: "dict[str, Player]" 
    __dynamic: "dict[str, Entity]"
    __static: "dict[str, Entity]"
    def __init__(self, create_entities = True):
        """Can specify create_entities = False if you want no entities, which can be useful for doctests."""
        self.__players = {} 
        if create_entities:
            self.__static, self.__dynamic = loadmap("map.txt")
        else:
            self.__static, self.__dynamic = {}, {}

    def get_static(self):
        staticdict = {k: v.todict() for k, v in self.__static.items()}
        return json.dumps({
            "static": staticdict
        })
    
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
            self.__players[ce.cid] = Player(500, 500, paylo.name, paylo.avatar)
        elif type(paylo) == ClickEv:
            xcmp = self.__players[ce.cid].x - paylo.x
            ycmp = self.__players[ce.cid].y - paylo.y
            if xcmp < -100:
                self.__players[ce.cid].change_x = 50
            elif xcmp > 100:
                self.__players[ce.cid].change_x = -50
            else:
                self.__players[ce.cid].change_x = 0
            if ycmp < -100:
                self.__players[ce.cid].change_y = 50
            elif ycmp > 100:
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
        all_ents = list(self.__static.values()) + list(self.__dynamic.values())
        for p in self.__players.values():
            for e in all_ents:
                if p.x == e.x and p.y == e.y:
                    if not e.passable:
                        p.x -= p.change_x
                        p.y -= p.change_y
                    e.on_touch(p)

    def current(self):
        """Copy of current state. Examples in module docstring/doctests."""
        return {"dynamic": copy.deepcopy(self.__dynamic), "players": copy.deepcopy(self.__players)}

    def jsondumps(self):
        """Current state in json. Examples in module docstring/doctests"""
        dynamicdict = {k: v.todict() for k, v in self.__dynamic.items()}
        playersdict = {k: v.todict() for k, v in self.__players.items()}
        return json.dumps({
            "dynamic": dynamicdict,
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
  - Create some dynamic entities(once)
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


- Diagonal movement should not work in this case:
  p w w  player, wall, open space
  w o w  
  w w o
"""

if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)