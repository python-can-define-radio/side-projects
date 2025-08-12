from typing import NamedTuple, Any

import deal

from projtypes import ID



class Obj(NamedTuple):
    id: ID
    x: int
    y: int
    transmitter_on: bool
    tx_freq: float


class GameState(NamedTuple):
    id: ID
    x: int = 100
    y: int = 100
    velocity_x: int = 0
    velocity_y: int = 0
    transmitter_on: bool = False
    tx_freq: float = 0.0
    
    @deal.has()
    def serialize(self) -> dict:
        """A customized `asdict`"""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "transmitter_on": self.transmitter_on,
            "tx_freq": self.tx_freq,
        }


class Update(NamedTuple):
    field: "str | None"
    val: Any