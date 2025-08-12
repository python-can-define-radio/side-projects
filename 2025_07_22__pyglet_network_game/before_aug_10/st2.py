import numpy as np
import pyglet

def display_grayscale_image(data: np.ndarray) -> None:
    """
    Display a 2D NumPy array as a grayscale image using pyglet.

    :param data: 2D array of dtype uint8 with values from 0–255.
    """
    # Ensure input is uint8 and 2D
    if data.ndim != 2:
        raise ValueError("Input must be a 2D NumPy array.")
    if data.dtype != np.uint8:
        data = np.clip(data, 0, 255).astype(np.uint8)

    height, width = data.shape
    pitch = -width  # top-to-bottom row order

    window = pyglet.window.Window(width=width, height=height, caption='Grayscale Image')

    @window.event
    def on_draw():
        window.clear()
        image = pyglet.image.ImageData(
            width,
            height,
            'L',
            data.tobytes(),
            pitch=pitch
        )
        image.blit(0, 0)

    pyglet.app.run()


img = np.random.randint(0, 256, (300, 400), dtype=np.uint8)
display_grayscale_image(img)

