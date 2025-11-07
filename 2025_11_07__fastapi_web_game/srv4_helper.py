from dataclasses import dataclass, field, asdict
import json
from typing import Literal


@dataclass
class InitEv:
    username: str
    shape: str
    color: str
    eventkind: Literal['init']


@dataclass
class KeydownEv:
    key: str
    eventkind: Literal['keydown']


@dataclass
class ClickEv:
    x: int
    y: int
    eventkind: Literal['click']


@dataclass
class PlayerInfo:
    x: int
    y: int
    username: str
    shape: str
    color: str


@dataclass
class CliEvent:
    """A message from a client"""
    cid: str
    """Client ID"""
    payload_raw: 'str | None'
    """A string which we can parse using get_payload"""

    def get_payload(self):
        try:
            parsed = json.loads(self.payload_raw)
            if parsed["eventkind"] == "init":
                return InitEv(**parsed)
            elif parsed["eventkind"] == "keydown":
                return KeydownEv(**parsed)
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


@dataclass
class GameState:
    __playersInfo: "dict[str, PlayerInfo]" = field(default_factory=dict)

    def process_cli_msg(self, ce: 'CliEvent | Disconnect') -> str:
        if type(ce) == Disconnect:
            self.handleDC(ce)
        elif type(ce) == CliEvent:
            self.handleCE(ce)
        else:
            raise NotImplementedError()
        dictified = {k: asdict(v) for k, v in self.__playersInfo.items()}
        return json.dumps(dictified)

    def handleDC(self, ce: Disconnect):
        if ce.cid in self.__playersInfo:
            print("I: Removing", ce.cid, "from dict")
            del self.__playersInfo[ce.cid]
        else:
            print("W: Attempted to remove", ce.cid, "but it was already absent.")

    def handleCE(self, ce: CliEvent):
        p = ce.get_payload()
        if type(p) == InitEv:
            self.__playersInfo[ce.cid] = PlayerInfo(200, 300, p.username, p.shape, p.color)
        elif type(p) == ClickEv:
            self.__playersInfo[ce.cid].x = p.x
            self.__playersInfo[ce.cid].y = p.y
        elif type(p) == KeydownEv:
            if p.key == "w":
                self.__playersInfo[ce.cid].y -= 10
            if p.key == "a":
                self.__playersInfo[ce.cid].x -= 10
            if p.key == "s":
                self.__playersInfo[ce.cid].y += 10
            if p.key == "d":
                self.__playersInfo[ce.cid].x += 10
        