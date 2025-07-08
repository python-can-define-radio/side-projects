"""A very simplified version of this example: https://fdtd.readthedocs.io/en/latest/examples/05-lenses-and-analysing-lensing-actions.html

Creates frames and a video of a line source emanating from within an object
"""


import fdtd
import matplotlib.pyplot as plt


grid = fdtd.Grid(shape=(80, 70, 1), grid_spacing=77.5e-9)
# x boundaries
grid[0:2, :, :] = fdtd.PML(name="pml_xlow")
grid[-2:, :, :] = fdtd.PML(name="pml_xhigh")
# y boundaries
grid[:, 0:2, :] = fdtd.PML(name="pml_ylow")
grid[:, -2:, :] = fdtd.PML(name="pml_yhigh")
simfolder = grid.save_simulation("Lenses")  # initializing environment to save simulation data
print(simfolder)

grid[50:80, 20:40, 0] = fdtd.Object(permittivity=1.5 ** 2)

grid[70, 20:40, 0] = fdtd.LineSource(period=4000e-9 / (3e8), name="source")


for i in range(200):
    grid.step()  # running simulation 1 timestep a time and animating
    plt.clf()
    grid.visualize(z=0, index=i, save=True, folder=simfolder)
    plt.title(f"{i:3.0f}")
   
grid.save_data()  # saving detector readings (maybe delete?)


video_path = grid.generate_video(delete_frames=False)  # rendering video from saved frames
