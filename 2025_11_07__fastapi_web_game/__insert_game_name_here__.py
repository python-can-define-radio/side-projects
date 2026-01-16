import numpy as np


def wave_propagate_point_source(timesteps: int, xsize: int, ysize: int, zsize: int) -> np.ndarray:
    """
    Return a 4D numpy array of shape (timesteps, xsize, ysize, zsize).
    Simulate a simple wave propagation from a point source at the center.
    Written by MS Copilot
    """
    # Initialize the 4D array
    wave = np.zeros((timesteps, xsize, ysize, zsize), dtype=np.float32)

    # Define the center point
    cx, cy, cz = xsize // 2, ysize // 2, zsize // 2

    # Initial condition: point source at t=0
    wave[0, cx, cy, cz] = 3.0

    # Parameters for wave propagation
    c = 2.0   # wave speed
    dt = 0.1  # time step
    dx = 1.0  # spatial step
    coeff = (c * dt / dx) ** 2

    # Time evolution using finite differences
    for t in range(1, timesteps - 1):
        # Laplacian approximation (3D)
        laplacian = (
            np.roll(wave[t], 1, axis=0) + np.roll(wave[t], -1, axis=0) +
            np.roll(wave[t], 1, axis=1) + np.roll(wave[t], -1, axis=1) +
            np.roll(wave[t], 1, axis=2) + np.roll(wave[t], -1, axis=2) -
            6 * wave[t]
        )
        # Wave equation update
        wave[t+1] = 2 * wave[t] - wave[t-1] + coeff * laplacian

    return wave

grid = wave_propagate_point_source(500, 100, 2, 100)
