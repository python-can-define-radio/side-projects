from dataclasses import replace

import deal
import pyglet.window.key as key

from classes import GameState, Update


@deal.pure
def handle_key_press(state: GameState, symbol: int) -> Update:
    if symbol == key.W:
        return Update("velocity_y", 1)
    elif symbol == key.A:
        return Update("velocity_x", -1)
    elif symbol == key.S:
        return Update("velocity_y", -1)
    elif symbol == key.D:
        return Update("velocity_x", 1)
    elif symbol == key.R:
        return Update("transmitter_on", not state.transmitter_on)
    elif symbol == key.F:
        return Update("tx_freq", state.tx_freq + 1.0)
    elif symbol == key.V:
        new_freq = max(0.0, state.tx_freq - 1.0)  # no negative frequencies
        return Update("tx_freq", new_freq)
    else:
        return Update(None, None)


def on_key_release(symbol, modifiers):
    global state
    if symbol in [pyglet.window.key.D, pyglet.window.key.A]:
        state = replace(state, velocity_x=0)
    elif symbol in [pyglet.window.key.W, pyglet.window.key.S]:
        state = replace(state, velocity_y=0)
