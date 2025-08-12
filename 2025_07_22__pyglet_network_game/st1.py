from typing import TYPE_CHECKING

import deal
import numpy as np
if TYPE_CHECKING:
    from numpy.ndarray import NDArray

import pyglet
from pyglet.gl import glClearColor


class SineWaveStreamer:
    def __init__(self, frequency: float = 440.0, sample_rate: int = 44100, amplitude: float = 1.0) -> None:
        self.frequency: float = frequency
        self.sample_rate: int = sample_rate
        self.amplitude: float = amplitude
        self.phase: float = 0.0
        self.t: "NDArray[np.float64]" = np.arange(1024) / self.sample_rate

    @deal.post(lambda result: len(result) == 1024)
    def get_next_chunk(self) -> "NDArray[np.float64]":
        wave: "NDArray[np.float64]" = self.amplitude * np.sin(2 * np.pi * self.frequency * self.t + self.phase)
        self.phase += 2 * np.pi * self.frequency * 1024 / self.sample_rate
        self.phase %= 2 * np.pi
        return wave

# Example usage
streamer = SineWaveStreamer(frequency=440)
chunk = streamer.get_next_chunk()
print(chunk)

class WaterfallDisplay:
    def __init__(self, width=512, height=512):
        self.streamer = SineWaveStreamer()
        self.width = width
        self.height = height
        self.image_data = np.zeros((height, width), dtype=np.uint8)
        self.window = pyglet.window.Window(width=width, height=height)
        glClearColor(0, 0, 0, 1)

        @self.window.event
        def on_draw():
            self.window.clear()
            image = pyglet.image.ImageData(
                self.width,
                self.height,
                'L',
                self.image_data.tobytes(),
                pitch=-self.width  # Negative for top-down rendering
            )
            image.blit(0, 0)

    def update(self, dt):
        chunk = self.streamer.get_next_chunk()
        fft_result = np.abs(np.fft.rfft(chunk, n=self.width))
        fft_result = np.clip(fft_result / np.max(fft_result) * 255, 0, 255).astype(np.uint8)
        self.image_data = np.roll(self.image_data, 1, axis=0)
        self.image_data[0, :] = fft_result

    def run(self):
        pyglet.clock.schedule_interval(self.update, 1 / 30.0)
        pyglet.app.run()

if __name__ == "__main__":
    WaterfallDisplay().run()
