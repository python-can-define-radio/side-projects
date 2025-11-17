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
from typing import Literal, Callable, Union


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


Payload = Union[InitEv, ClickEv, KeyupEv, KeydownEv]


@dataclass
class Player:
    x: int
    y: int
    name: str
    avatar: str = "/assets/femaleAdventurer_idle.png"
    change_x: int = 0
    change_y: int = 0
    facing_direction: Literal["w", "a", "s", "d"] = "d"
    """wasd -> up, left, down, right"""
    trying_action: bool = False
    talking_to: "Entity | None" = None
    dialog: "str | None" = None

    def todict(self):
        return dataclasses.asdict(self)


def adjacent(a, b):
    abovebelow = abs(a.x - b.x) == 50 and a.y == b.y
    leftright = abs(a.y - b.y) == 50 and a.x == b.x
    return abovebelow or leftright


@dataclass
class Entity:
    x: int
    y: int
    name: str
    avatar: str
    passable: bool
    action: "dict | None" = None
    def on_action(self, p: Player):
        """If the player is trying to act and is adjacent to an interactable Entity,
        call the entity's on_action_ function."""
        if not p.trying_action:
            return
        if not adjacent(self, p):
            return
        if not self.action:
            return
        if "dialog" not in self.action:
            raise NotImplementedError("Only dialog is implemented right now")
        p.talking_to = self
        p.dialog = self.action["dialog"]
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

    def get_payload(self) -> Payload:
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



def handle_collisions(p: Player, e: Entity):
    if p.x == e.x and p.y == e.y:
        if not e.passable:
            p.x -= p.change_x
            p.y -= p.change_y


def handle_ce_impl(paylo: Payload, player: Player):
    """Mutate `player` based on `paylo` to set the player's speed and `trying_action` attribute."""
    if type(paylo) == ClickEv:
        pass  # Might use this eventually
    if type(paylo) == KeydownEv:
        if paylo.key == "w":
            player.change_y = -50
        elif paylo.key == "s":
            player.change_y = 50
        elif paylo.key == "a":
            player.change_x = -50
        elif paylo.key == "d":
            player.change_x = 50
        player.facing_direction = paylo.key if paylo.key in list("wasd") else player.facing_direction  # type: ignore
        print(player.facing_direction)
        player.trying_action = (paylo.key == " ")
    elif type(paylo) == KeyupEv:
        if paylo.key in ["w", "s"]:
            player.change_y = 0
        if paylo.key in ["a", "d"]:
            player.change_x = 0



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
    f = open(currentmap, encoding="utf-8")
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
                static[f"tree{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/tree.png", False, {"dialog": "woooosshhhhhh.... rustle rustle"})
            elif char == "c":
                dynamic[f"coin{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/coin.png", True)
            elif char == "👮":
                dynamic[f"npc{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/alienBlue_front.png", False, {"dialog": "Private asdf, weclome."})
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
        """Update state when clients send events, such as mouse or keyboard input.
        Specifically:
        - InitEv: Create a new player; store that player in `self.__players`  
          with a key of `ce.cid`.
        - Other events are passed to `handle_ce_impl`."""
        paylo = ce.get_payload()
        if type(paylo) == InitEv:
            self.__players[ce.cid] = Player(500, 500, paylo.name, paylo.avatar)
        else:
            handle_ce_impl(paylo, self.__players[ce.cid])

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
        all_ents = list(self.__static.values()) + list(self.__dynamic.values())
        for p in self.__players.values():
            p.x += p.change_x
            p.y += p.change_y
            for e in all_ents:
                handle_collisions(p, e)
                e.on_action(p)
            p.trying_action = False
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