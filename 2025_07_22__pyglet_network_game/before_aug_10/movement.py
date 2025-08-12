from dataclasses import replace
from typing import Callable

from functools import lru_cache

import deal
import pyglet

from classes import GameState



@deal.pure
def collides(rect1: pyglet.shapes.Rectangle, rect2: pyglet.shapes.Rectangle) -> bool:
    """True if the rectangles overlap"""
    return (
        rect1.x < rect2.x + rect2.width and
        rect1.x + rect1.width > rect2.x and
        rect1.y < rect2.y + rect2.height and
        rect1.y + rect1.height > rect2.y
    )


@deal.pure
@lru_cache
def move(s: GameState, dt: float) -> GameState:
    """Update state based on velocity. Does collision detection too."""
    proposed_x = s.x + int(s.velocity_x * dt * 300)
    proposed_y = s.y + int(s.velocity_y * dt * 300)
    
    # Create hypothetical rectangle
    
    proposed_rect = pyglet.shapes.Rectangle(proposed_x, proposed_y, 25, 25)

    # Functional-style collision detection
    has_collision = any(map(lambda wall: collides(proposed_rect, wall), walls))

    if has_collision:
        return s  # No movement if blocked

    return replace(s, x=proposed_x, y=proposed_y)