from dataclasses import dataclass, replace, asdict
import json
import random
import string
from typing import Tuple, List

from annotated_types import Len
import deal
import pyglet
from typing_extensions import Annotated
import zmq


ID_LENGTH = 5
ID = Annotated[str, Len(ID_LENGTH, ID_LENGTH)]


@deal.has("random")
def make_id() -> ID:
    """Random letters"""
    return "".join(random.sample(string.ascii_letters, ID_LENGTH))

@deal.pure
def id_to_color(i: ID) -> Tuple[int, int, int]:
    """Some arbitrary math to producde an RGB color"""
    return ord(i[0]) % 256, ord(i[1]) % 256, ord(i[2]) % 256


# Set up ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect("tcp://localhost:5555")

subscriber_context = zmq.Context()
subscriber_socket = subscriber_context.socket(zmq.SUB)
subscriber_socket.connect("tcp://localhost:5566")  # Change to your relay server IP
subscriber_socket.setsockopt_string(zmq.SUBSCRIBE, "")   # Subscribe to all topics

other_players: "dict[ID, Obj]" = {}


@dataclass(frozen=True)
class Obj:
    id: ID
    x: int
    y: int
    transmitter_on: bool
    tx_freq: float


@dataclass(frozen=True)
class GameState:
    id: ID
    x: int = 100
    y: int = 100
    velocity_x: int = 0
    velocity_y: int = 0
    transmitter_on: bool = False
    tx_freq: float = 0.0
    
    def serialize(self):
        """A customized `asdict`"""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "transmitter_on": self.transmitter_on,
            "tx_freq": self.tx_freq,
        }


state = GameState(id=make_id())
previous_state = state

window = pyglet.window.Window(800, 800)
MAP_WIDTH = window.width * 5
MAP_HEIGHT = window.height * 5

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




@deal.pure
def collides(rect1: pyglet.shapes.Rectangle, rect2: pyglet.shapes.Rectangle) -> bool:
    return (
        rect1.x < rect2.x + rect2.width and
        rect1.x + rect1.width > rect2.x and
        rect1.y < rect2.y + rect2.height and
        rect1.y + rect1.height > rect2.y
    )


@deal.has("network")
def publish_state(s: GameState):
    message = json.dumps(s.serialize())
    socket.send_string(message)


@deal.pure
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


@window.event
def on_key_press(symbol, modifiers):
    global state
    if symbol == pyglet.window.key.D:
        state = replace(state, velocity_x=1)
    elif symbol == pyglet.window.key.A:
        state = replace(state, velocity_x=-1)
    elif symbol == pyglet.window.key.W:
        state = replace(state, velocity_y=1)
    elif symbol == pyglet.window.key.S:
        state = replace(state, velocity_y=-1)
    elif symbol == pyglet.window.key.R:
        state = replace(state, transmitter_on=not state.transmitter_on)
    elif symbol == pyglet.window.key.F:
        state = replace(state, tx_freq=state.tx_freq + 1.0)
    elif symbol == pyglet.window.key.V:
        new_freq = max(0.0, state.tx_freq - 1.0)  # no negative frequencies
        state = replace(state, tx_freq=new_freq)



@window.event
def on_key_release(symbol, modifiers):
    global state
    if symbol in [pyglet.window.key.D, pyglet.window.key.A]:
        state = replace(state, velocity_x=0)
    elif symbol in [pyglet.window.key.W, pyglet.window.key.S]:
        state = replace(state, velocity_y=0)


def draw_hud(game_state: GameState):
    # Transmitter status
    status_label = pyglet.text.Label(
        f"Transmitter: {'ON' if game_state.transmitter_on else 'OFF'}",
        font_name='Arial',
        font_size=14,
        x=10, y=570,
        anchor_x='left', anchor_y='top',
        color=(255, 255, 255, 255)
    )
    status_label.draw()

    # Frequency display
    freq_label = pyglet.text.Label(
        f"Frequency: {game_state.tx_freq:.2f} Hz",
        font_name='Arial',
        font_size=14,
        x=10, y=550,
        anchor_x='left', anchor_y='top',
        color=(255, 255, 255, 255)
    )
    freq_label.draw()


def draw_spectrum_analyzer():
    bar_width = 300
    bar_height = 10
    max_freq = 30.0

    # Padding from window edge
    margin_x = 10
    margin_y = 100

    # Reposition bar: top-right corner
    bar_x = window.width - bar_width - margin_x
    bar_y = window.height - bar_height - margin_y

    base_bar = pyglet.shapes.Rectangle(bar_x, bar_y, bar_width, bar_height, color=(50, 50, 50))
    base_bar.draw()

    def freq_to_x(freq):
        clamped = max(0.0, min(freq, max_freq))
        return bar_x + (clamped / max_freq) * bar_width

    # Other players
    for obj in other_players.values():
        x = freq_to_x(obj.tx_freq)
        pyglet.shapes.Line(x, bar_y, x, bar_y + bar_height, thickness=2, color=(150, 150, 150)).draw()

    # Own transmission frequency
    self_x = freq_to_x(state.tx_freq)
    pyglet.shapes.Line(self_x, bar_y, self_x, bar_y + bar_height, thickness=2, color=(255, 255, 0)).draw()

    # Label
    label = pyglet.text.Label(
        f"{state.tx_freq:.2f} Hz",
        font_name='Arial',
        font_size=12,
        x=self_x, y=bar_y + 15,
        anchor_x='center', anchor_y='bottom',
        color=(255, 255, 0, 255)
    )
    label.draw()




@window.event
def on_draw():
    window.clear()

    draw_spectrum_analyzer()

    # Compute camera offset
    camera_offset_x = window.width // 2 - state.x
    camera_offset_y = window.height // 2 - state.y

    # Draw walls
    for wall in walls:
        adjusted_wall = pyglet.shapes.Rectangle(
            wall.x + camera_offset_x,
            wall.y + camera_offset_y,
            wall.width,
            wall.height,
            color=wall.color
        )
        adjusted_wall.draw()

    # Draw local player
    square.x = state.x + camera_offset_x
    square.y = state.y + camera_offset_y
    square.draw()

    # Draw other players
    for pid, s in other_players.items():
        if pid != state.id:
            r = pyglet.shapes.Rectangle(
                s.x + camera_offset_x,
                s.y + camera_offset_y,
                25,
                25,
                color=id_to_color(s.id)
            )
            r.draw()
    
    draw_hud(state)




def ingest_messages(socket, current_players: "dict[ID, Obj]", self_id: ID) -> dict:
    """Ugly; probably should improve"""
    def receive_all():
        updates: "dict[ID, Obj]" = {}
        try:
            while True:
                message = socket.recv_string(flags=zmq.NOBLOCK)
                data = json.loads(message)
                if data["id"] != self_id:
                    updates[data["id"]] = Obj(**data)
        except zmq.Again:
            pass
        return updates

    # Start with a copy of the current state (immutability!)
    updated_players = dict(current_players)

    for pid, obj in receive_all().items():
        updated_players[pid] = obj

    return updated_players


# Schedule updates
def tick(dt):
    global state, other_players, previous_state
    moved = move(state, dt)

    # Only publish if the new state differs from the current one
    if moved != previous_state:
        publish_state(moved)

    previous_state = moved
    state = moved
    other_players = ingest_messages(subscriber_socket, other_players, state.id)




pyglet.clock.schedule_interval(tick, 1/60)
pyglet.app.run()