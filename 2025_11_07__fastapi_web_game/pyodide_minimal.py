import asyncio
import html
from typing import TYPE_CHECKING

from js import document, ImageData, Uint8ClampedArray  # type: ignore
from pyodide.http import pyfetch  # type: ignore


def setup_all_fdtd():
    """
    Most of this is copied from the `grid.visualize` method provided in
    the fdtd module.
    """
    import fdtd
    import numpy as np

    # relative
    from fdtd.backend import backend as bd

    def np_array_to_imagedata(img: "np.ndarray"):
        """Convert `img` to the Javascript `ImageData` type,
        which is useable in an HTML canvas context's putImageData. Source: ChatGPT"""
        assert img.ndim == 2
        h, w = img.shape
        img[img > 255] = 255
        # Convert to RGBA, which Uint8ClampedArray expects 
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[:, :, 0] = img  # red?
        rgba[:, :, 1] = img  # green?
        rgba[:, :, 2] = img  # blue?
        rgba[:, :, 3] = 255  # opacity / "alpha"
        # Convert NumPy array -> JS Uint8ClampedArray
        clamp = Uint8ClampedArray.new(rgba.tobytes())
        # Create and return JS ImageData
        return ImageData.new(clamp, w, h)


# 0 -> 85  would be 0 red to 255 red
# 86 -> 170 would be 0 blue to max blue
# 171 -> 255 would be 0 blue to max blue

    def visualize_supersimple_v1(grid):
        grid_energy_3d = bd.sum(grid.E ** 2 + grid.H ** 2, -1)  # type: ignore 
        assert type(grid_energy_3d) == np.ndarray
        grid_energy_xy = grid_energy_3d[:, :, 0]
        geplus1 = grid_energy_xy
        grid_energy_logscale = geplus1 * 50000
        canvas = document.getElementById("simpledrawcanvas")
        ctx = canvas.getContext("2d")
        imageData = np_array_to_imagedata(grid_energy_logscale)
        ctx.putImageData(imageData, 0, 0)


    

    fdtd.set_backend("numpy")
    return visualize, visualize_supersimple_v1



######## WEB BROWSER STUFF
console_div = document.getElementById("console")
def print_to_div(*args):
    text = " ".join(html.escape(str(a)) for a in args)
    console_div.innerHTML += text + "<br>"

print = print_to_div

persistvars = {}

def exec_text(ev, el):
    try:
        if ev.key == "Enter":
            v = el.value
            print(">>>", v)
            exec(v, globals(), persistvars)
    except Exception as e:
        print(e)



async def loadgrid():
    import fdtd
    filename = "fdtdmap.txt"
    response = await pyfetch(filename)
    if not response.ok:
        raise FileNotFoundError(f"Failed to load {filename} (status {response.status})")
    text: str = await response.text()
    lines = text.splitlines()
    if TYPE_CHECKING:
        from typing_extensions import TypedDict
        class MaterialProperty(TypedDict):
            permittivity: float
            conductivity: float
    materials: "dict[str, MaterialProperty]" = {
            "metal": {"permittivity": 1e4, "conductivity": 1e5},  # source: ChatGPT
            "dry sand": {"permittivity": 3.0, "conductivity": 1e-4},  # source: ChatGPT
            "moist sand": {"permittivity": 10.0, "conductivity": 1e-2},  # source: ChatGPT
            "fake1": {"permittivity": 4.5, "conductivity": 1e-3},  # source: made it up
        }

    grid = fdtd.Grid(
                # height (y), width (x), depth (z)
        shape = (100, 200, 1),  # type: ignore
        grid_spacing = 1,
    )
    yindexes = range(len(lines))
    for yidx, line in zip(yindexes, lines):
        xindexes = range(len(line))
        for xidx, char in zip(xindexes, line):
            if char == "m":
                grid[yidx, xidx, 0] = fdtd.AbsorbingObject(**materials["metal"])
            if char == "p":
                grid[yidx, xidx, 0] = fdtd.PointSource(period = 60, amplitude=4, pulse=True, cycle=1) # type: ignore
            
    return grid
    ## idea:
    ## read the file map.txt
    ## create a PointSource in spots with "p"
    ## create metal in spots with "m"


async def main():
    print("Loading fdtd package...")
    try:
        import pyodide_js # type: ignore
        await pyodide_js.loadPackage("micropip")
        import micropip  # type: ignore
        await micropip.install("fdtd")
        
        visualize, visualize_supersimple_v1 = setup_all_fdtd()
        grid = await loadgrid()
        for unus in range(2000):
            visualize_supersimple_v1(grid)
            grid.step() 
            await asyncio.sleep(0)


        if False:
            el = document.getElementById("execthis")
            el.onkeyup = lambda event: exec_text(event, el)
            exec("import fdtd", globals(), persistvars)
            exec("visualize = setup_all_fdtd()", globals(), persistvars)
            print("ready")
            async def dostuff():
                

            

            

                try:
                    visualize = globals()["persistvars"]["visualize"]
                    # grid = globals()["persistvars"]["grid"]
                    for unus in range(700):
                        visualize(grid, z=0, animate=True, norm="log")
                        grid.step() 
                        await asyncio.sleep(0)  # apparently this allows the browser to refresh
                except Exception as e:
                    print("ex", e)
            asyncio.create_task(dostuff())
    except Exception as e:
        print(e)
