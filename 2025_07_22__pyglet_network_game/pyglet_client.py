import random
import pyglet
import zmq
import json
from typing import Tuple
from dataclasses import dataclass, replace, asdict


PlayerID = Tuple[int, int, int]
# Set up ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect("tcp://localhost:5555")

subscriber_context = zmq.Context()
subscriber_socket = subscriber_context.socket(zmq.SUB)
subscriber_socket.connect("tcp://localhost:5566")  # Change to your relay server IP
subscriber_socket.setsockopt_string(zmq.SUBSCRIBE, "")   # Subscribe to all topics

other_players: "dict[PlayerID, GameState]" = {}

# Immutable game state
@dataclass(frozen=True)
class GameState:
    player_id: PlayerID
    x: int = 100
    y: int = 100
    velocity_x: int = 0
    velocity_y: int = 0


state = GameState(player_id=(random.randint(10, 255), random.randint(10, 255), random.randint(10, 255)))

window = pyglet.window.Window(400, 400)
MAP_WIDTH = window.width * 5
MAP_HEIGHT = window.height * 5

square = pyglet.shapes.Rectangle(0, 0, 50, 50, color=state.player_id, batch=None)
walls = [
    pyglet.shapes.Rectangle(0, 0, MAP_WIDTH, 10, color=(100, 100, 100)),  # bottom
    pyglet.shapes.Rectangle(0, MAP_HEIGHT - 10, MAP_WIDTH, 10, color=(100, 100, 100)),  # top
    pyglet.shapes.Rectangle(0, 0, 10, MAP_HEIGHT, color=(100, 100, 100)),  # left
    pyglet.shapes.Rectangle(MAP_WIDTH - 10, 0, 10, MAP_HEIGHT, color=(100, 100, 100))  # right
]



def collides(rect1, rect2):
    return (
        rect1.x < rect2.x + rect2.width and
        rect1.x + rect1.width > rect2.x and
        rect1.y < rect2.y + rect2.height and
        rect1.y + rect1.height > rect2.y
    )

# Function to publish state to ZMQ
def publish_state(s: GameState):
    message = json.dumps(asdict(s))
    socket.send_string(message)

# Pure function to update game state
def update_state(s: GameState, dt: float) -> GameState:
    proposed_x = s.x + int(s.velocity_x * dt * 500)
    proposed_y = s.y + int(s.velocity_y * dt * 500)
    
    # Create hypothetical rectangle
    
    proposed_rect = pyglet.shapes.Rectangle(proposed_x, proposed_y, 50, 50)

    # Functional-style collision detection
    has_collision = any(map(lambda wall: collides(proposed_rect, wall), walls))

    if has_collision:
        return s  # No movement if blocked

    return replace(s, x=proposed_x, y=proposed_y)


# Key event handlers
@window.event
def on_key_press(symbol, modifiers):
    global state
    if symbol == pyglet.window.key.RIGHT:
        state = replace(state, velocity_x=1)
    elif symbol == pyglet.window.key.LEFT:
        state = replace(state, velocity_x=-1)
    elif symbol == pyglet.window.key.UP:
        state = replace(state, velocity_y=1)
    elif symbol == pyglet.window.key.DOWN:
        state = replace(state, velocity_y=-1)
    publish_state(state)

@window.event
def on_key_release(symbol, modifiers):
    global state
    if symbol in [pyglet.window.key.RIGHT, pyglet.window.key.LEFT]:
        state = replace(state, velocity_x=0)
    elif symbol in [pyglet.window.key.UP, pyglet.window.key.DOWN]:
        state = replace(state, velocity_y=0)
    publish_state(state)

@window.event
def on_draw():
    window.clear()

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
        if pid != state.player_id:
            r = pyglet.shapes.Rectangle(
                s.x + camera_offset_x,
                s.y + camera_offset_y,
                50,
                50,
                color=pid
            )
            r.draw()



def ingest_messages(socket, current_players: "dict[PlayerID, GameState]", self_id: PlayerID) -> dict:
    """Ugly; probably should improve"""
    def receive_all():
        updates: "tuple[PlayerID, GameState]" = []
        try:
            while True:
                message = socket.recv_string(flags=zmq.NOBLOCK)
                data = json.loads(message)
                if data["player_id"] != self_id:
                    updates.append((tuple(data["player_id"]), GameState(**data)))
        except zmq.Again:
            pass
        return updates

    # Start with a copy of the current state (immutability!)
    updated_players = dict(current_players)

    for pid, gs in receive_all():
        updated_players[pid] = gs

    return updated_players


# Schedule updates
def tick(dt):
    global state, other_players

    new_state = update_state(state, dt)

    # Only publish if the new state differs from the current one
    if new_state != state:
        publish_state(new_state)

    state = new_state
    other_players = ingest_messages(subscriber_socket, other_players, state.player_id)




pyglet.clock.schedule_interval(tick, 1/60)
pyglet.app.run()