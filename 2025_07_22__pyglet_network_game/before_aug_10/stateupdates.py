from dataclasses import replace
from typing import Callable

from functools import lru_cache

import deal
import pyglet

from classes import GameState




# Schedule updates
def fixthistick(dt):
    global state, other_players, previous_state
    moved = move(state, dt)

    # Only publish if the new state differs from the current one
    if moved != previous_state:
        publish_state(moved)

    previous_state = moved
    state = moved
    other_players = ingest_messages(subscriber_socket, other_players, state.id)



def __tests():
    """
    >>> def __state_change(state, dt):
    ...   return replace(state, x=state.x - 1)
    >>> s = GameState(id="abcde")
    >>> s 
    GameState(...x=100...)
    >>> tick = make_state_updater(s, __state_change, lambda x: print(x))
    >>> tick(0.1)
    GameState(...x=99...)
    >>> tick(0.1)
    GameState(...x=98...)
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)