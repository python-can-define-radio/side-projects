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
