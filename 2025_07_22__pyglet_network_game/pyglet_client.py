from collections import deque
from typing import Callable

import deal
import pyglet

from classes import GameState, Update
from controls import handle_key_press


def stuff_that_may_be_put_in_main():
    other_players: "dict[ID, Obj]" = {}

    

    square = pyglet.shapes.Rectangle(0, 0, 25, 25, color=id_to_color(state.id), batch=None)
    walls = [
        pyglet.shapes.Rectangle(0, 0, MAP_WIDTH, 10, color=(100, 100, 100)),  # bottom
        pyglet.shapes.Rectangle(0, MAP_HEIGHT - 10, MAP_WIDTH, 10, color=(100, 100, 100)),  # top
        pyglet.shapes.Rectangle(0, 0, 10, MAP_HEIGHT, color=(100, 100, 100)),  # left
        pyglet.shapes.Rectangle(MAP_WIDTH - 10, 0, 10, MAP_HEIGHT, color=(100, 100, 100))  # right
    ]
    transmitter_label = pyglet.text.Label(
        'transmitter off',
        font_name='Arial',
        font_size=14,
        x=10, y=window.height - 20,
        anchor_x='left', anchor_y='top',
        color=(255, 255, 255, 255)
    )


    

# def setup_state_mgmt(state: GameState, on_key_press: Callable, statefunc: Callable, propagfunc: Callable):
#     """Set up the following functions `on_key_press` and `statefunc` to run with the current state as the argument. Update the state to the return value of the function. Also, propagate changes using `propagfunc`, but only if the new state differs from the original.
    
#     The design-use-case is that `propagfunc` will propagate the changes over the network to other players.
#     ."""
#     statetrack = {
#         "current": state,
#         "last_sent": state,
#     }

#     def tick_and_propagate(dt: float) -> None:
#         last_sent = statetrack["last_sent"]
#         updated = statefunc(statetrack["current"], dt)
#         if updated != last_sent:
#             propagfunc(updated)
#         statetrack["previous"] = statetrack["current"]
#     pyglet.clock.schedule_interval(tick_and_propagate, 1/60)



@deal.pure
def _apply(u: Update, s: GameState) -> GameState:
    if u.field is None:
        return s
    return s._replace(**{u.field: u.val})


@deal.has()
def _setup_state_mgmt(init_state: GameState, propaganda: Callable[[Update], None]):
    keypresses: "deque[int]" = deque()
    supdates: "deque[Update]" = deque()
    state = init_state

    def on_key_press(symbol: int, modifiers):
        keypresses.append(symbol)

    def key_to_event(dt: float):
        while keypresses:
            symbol = keypresses.popleft()
            supdates.append(handle_key_press(state, symbol))
    
    def update_to_state(dt: float):
        nonlocal state
        while supdates:
            su = supdates.popleft()
            propaganda(su)
            state = _apply(su, state)
            print(state)

    return on_key_press, key_to_event, update_to_state


@deal.has("network")
def make_sender():
    def propaganda(up: Update):
        print("TODO: Send", up)
    return propaganda


def main():
    window = pyglet.window.Window(800, 800)
    MAP_WIDTH = window.width * 2
    MAP_HEIGHT = window.height * 2
    state = GameState(id="abcde")
    propaganda = make_sender()
    on_key_press, tick1, tick2 = _setup_state_mgmt(state, propaganda)
    window.event(on_key_press)
    pyglet.clock.schedule_interval(tick1, 1/200)
    pyglet.clock.schedule_interval(tick2, 1/200)
    pyglet.app.run()


if __name__ == "__main__":
    main()    
