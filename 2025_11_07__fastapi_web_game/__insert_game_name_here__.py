import numpy as np


import numpy as np

def wave_propagate_point_source(
    timesteps: int, xsize: int, ysize: int, zsize: int, walls=None
) -> np.ndarray:
    """
    Return a 4D numpy array of shape (timesteps, xsize, ysize, zsize).
    Simulate a simple wave propagation from a point source at the center.
    Walls are a list of (x, y, z) tuples that perfectly reflect the wave.
    """
    if walls is None:
        walls = []

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

        # Apply wall reflections
        for (wx, wy, wz) in walls:
            if 0 <= wx < xsize and 0 <= wy < ysize and 0 <= wz < zsize:
                # Invert amplitude at wall location to simulate reflection
                wave[t+1, wx, wy, wz] = -wave[t+1, wx, wy, wz]

    return wave


grid = wave_propagate_point_source(500, 100, 2, 100)
