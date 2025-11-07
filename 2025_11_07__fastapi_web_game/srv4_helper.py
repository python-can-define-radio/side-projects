from dataclasses import dataclass, field
import json
from typing import Literal


@dataclass
class CliPayload:
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
    eventkind: 'Literal["msg", "dc"]'
    """Either 'msg' (message) or "dc" (disconnect)"""
    payload_raw: 'str | None'
    """A string which we can parse using get_payload"""

    def get_payload(self):
        try:
            parsed = json.loads(self.payload_raw)
            return CliPayload(**parsed)
        except json.JSONDecodeError:
            raise ValueError(f"Client {self.cid} sent invalid JSON: '{self.payload_raw}'")


@dataclass
class GameState:
    __playerInfo: "dict[str, tuple[int, int]]" = field(default_factory=dict)

    def process_cli_msg(self, ce: CliEvent) -> str:
        if ce.eventkind == "dc":
            if ce.cid in self.__playerInfo:
                print("I: Removing", ce.cid, "from dict")
                del self.__playerInfo[ce.cid]
            else:
                print("W: Attempted to remove", ce.cid, "but it was already absent.")
        else:
            p = ce.get_payload()
            self.__playerInfo[ce.cid] = {
                "x": p.x,
                "y": p.y,
                "username": p.username,
                "shape": p.shape,
                "color": p.color,
            }
        return json.dumps(self.__playerInfo)
