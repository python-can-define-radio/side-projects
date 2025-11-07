from dataclasses import dataclass, field
from typing import NamedTuple
import json
from typing import Literal


class CliPayload(NamedTuple):
    x: int
    y: int


class CliEvent(NamedTuple):
    """A message from a client"""
    cid: str
    """Client ID"""
    eventkind: 'Literal["msg", "dc"]'
    """Either 'msg' (message) or "dc" (disconnect)"""
    payload_raw: 'str | None'
    """A string which we can parse using get_payload"""

    def get_payload(self):
        try:
            return CliPayload(**json.loads(self.payload_raw))
        except json.JSONDecodeError:
            raise ValueError(f"Client {self.cid} sent invalid JSON: '{self.payload_raw}'")


@dataclass
class GameState:
    __playerLocs: "dict[str, tuple[int, int]]" = field(default_factory=dict)

    def process_cli_msg(self, ce: CliEvent) -> str:
        if ce.eventkind == "dc":
            if ce.cid in self.__playerLocs:
                print("I: Removing", ce.cid, "from dict")
                del self.__playerLocs[ce.cid]
            else:
                print("W: Attempted to remove", ce.cid, "but it was already absent.")
        else:
            p = ce.get_payload()
            self.__playerLocs[ce.cid] = (p.x, p.y)
        return json.dumps(self.__playerLocs)
