import fdtd
import numpy as np




fdtd.set_backend("numpy")


grid = fdtd.Grid(
    shape = (40, 40, 40),  # type: ignore
    grid_spacing = 1e-4,
)

grid[0:4, 3, 0] = fdtd.LineSource(
    period = 15, name="source"  # type: ignore
)

for _unused in range(120):
    grid.visualize(z=0, animate=True, norm="log")
    grid.step()



