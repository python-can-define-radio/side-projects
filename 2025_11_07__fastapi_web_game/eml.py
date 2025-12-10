import asyncio
from dataclasses import dataclass, field
import html
import inspect
import json
from typing import Any, Callable, TYPE_CHECKING, Literal
from types import SimpleNamespace as Sns  # type: ignore


try:
    from js import document, localStorage, window, ImageData, Uint8ClampedArray  # type: ignore
    # only override print if the browser imports worked
    loaded_browser_modules = True
    def print(*args):
        print_to_div(args)
except ModuleNotFoundError:
    loaded_browser_modules = False


if TYPE_CHECKING:
    from typing_extensions import TypedDict
    class MaterialProperty(TypedDict):
        permittivity: float
        conductivity: float

    class JSImg:
        """Created by Image.new(). There's probably a better name for this"""
        src: str

    class StyleAttr:
        display: str
        width: str
        height: str

    class HTMLElement:
        textContent: str
        style: StyleAttr
        onclick: Callable
        onkeydown: Callable
        onkeyup: Callable
        value: "str | Any"
        src: str
        innerHTML: str
        scrollTop: str
        scrollHeight: str
        onchange: Callable
        dataset: ...

    class CanvasRenderingContext:
        fillStyle: str
        """should be a color or hex code"""
        font: str
        textAlign: str
        @staticmethod
        def fillText(text: str, x: int, y: int):
            ...
        @staticmethod
        def fillRect(a: int, b: int, c: int, d: int):
            ...
        @staticmethod
        def drawImage(img: JSImg, x: int, y: int, h: int, w: int):
            ...
        @staticmethod
        def putImageData(img: JSImg, x: int, y: int):
            ...

    class Canvas(HTMLElement):
        @staticmethod
        def getContext(x: str) -> CanvasRenderingContext:
            ...
        height: int
        width: int


def print_to_div(args):
    """Overriding the built-in print to log messages to built-in pseudo-console"""
    text = " ".join(html.escape(str(a)) for a in args) + "<br/>"
    loader_console = getElementByIdWithErr("loader-console")
    game_console = getElementByIdWithErr("game-console")
    loader_console.innerHTML = text + loader_console.innerHTML
    game_console.innerHTML = text + game_console.innerHTML


def prex(func):
    """A decorator that calls the function in a `try...except`.
    Any exceptions will be printed in the pseudo-console using the modified `print` function.
    Works for sync and async functions;
    Works regardless of whether the function is used with parentheses (`func()` and `onclick = func` both work)."""
    
    if loaded_browser_modules == False:
        return func
    
    if inspect.iscoroutinefunction(func):
        async def wrapper1(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print("Exception in", func.__name__, e)
                raise
        return wrapper1
    else:
        def wrapper2(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print("Exception in", func.__name__, e)
                raise
        return wrapper2


class ElementNotFoundError(Exception):
    ...


@dataclass
class Player:
    x: int
    y: int
    name: str
    avatar: str = "/assets/femaleAdventurer_idle.png"
    current_missions: "list[int]" = field(default_factory=list)
    completed_missions: "set[int]" = field(default_factory=set)
    facing: Literal["w", "a", "s", "d"] = "d"
    """facing direction. wasd -> up, left, down, right"""


@dataclass
class Entity:
    x: int
    y: int
    name: str
    avatar: str
    passable: bool
    available_missions: "list[int]" = field(default_factory=list)
    

@dataclass
class Objective:
    is_complete: bool
    complete_condition: Callable


@dataclass
class Mission:
    id: int
    name: str
    dialog: str
    objectives: "list[Objective]"


@prex
def getElementByIdWithErr(elemid: str) -> "HTMLElement":
    """Same as normal `document.getElementById`, but
    raises an exception if the element does not exist."""
    r = document.getElementById(elemid)
    if r is None:
        raise ElementNotFoundError(f"Element with id '{elemid}' not found")
    else:
        return r


@prex
def querySelectorWithErr(query: str) -> "HTMLElement":
    """Same as normal `document.querySelector`, but
    raises an exception if the element does not exist."""
    r = document.querySelector(query)
    if r is None:
        raise ElementNotFoundError(f"Query '{query}' found no elements its possible you havent selected an avatar.")
    else:
        return r
    

@prex
def querySelectorAllWithErr(query: str) -> "list[HTMLElement]":
    """Returns a Python list of HTMLElements."""
    node_list = document.querySelectorAll(query)

    if node_list.length == 0:
        raise ElementNotFoundError(f"No elements match selector '{query}'")

    return [node_list[i] for i in range(node_list.length)]

try:
    class G:
        """Global vars. Don't instantiate this class; it's just a grouping"""
        static: "dict[str, Entity]" = {}
        dynamic: "dict[str, Entity]" = {}
        img_cache: "dict[str, JSImg]" = {}
        player: "Player"
        current_target: "Entity | None" = None
        all_missions: "list[Mission]"
        materials: "dict[str, MaterialProperty]" = {
            "metal": {"permittivity": 1e4, "conductivity": 1e5},  # source: ChatGPT
            "dry sand": {"permittivity": 3.0, "conductivity": 1e-4},  # source: ChatGPT
            "moist sand": {"permittivity": 10.0, "conductivity": 1e-2},  # source: ChatGPT
            "fake1": {"permittivity": 4.5, "conductivity": 1e-3},  # source: made it up
        }
        class H:
            """HTML-related globals (divs, canvas, etc)"""
            canvas: "Canvas" = getElementByIdWithErr('canvas')  # type: ignore
            ctx = canvas.getContext('2d')
            mission_panel = getElementByIdWithErr("mission-panel")
            npc_img = getElementByIdWithErr("mission-npc-img")
            dialog = getElementByIdWithErr("mission-dialog")
            accept_btn = getElementByIdWithErr("mission-accept")
            cancel_btn = getElementByIdWithErr("mission-cancel")
except Exception as _exception_while_create_G:
    print("Exception while creating class G:", _exception_while_create_G)


@prex
async def attempt_action():
    """Display mission for entity that player is adjacent and facing"""
    for entity in G.dynamic.values():
        if is_face_adj(G.player, entity) and entity.available_missions:
            mission = await next_available_mission(entity.available_missions)
            show_mission_panel(entity, mission)


@prex
async def keydown(event):
    step = 50
    new_x, new_y = G.player.x, G.player.y

    if event.key == "w":
        new_y -= step
    elif event.key == "s":
        new_y += step
    elif event.key == "a":
        new_x -= step
    elif event.key == "d":
        new_x += step
    elif event.key == "e":
        if G.H.mission_panel.style.display in ["none", ""]:
            await attempt_action()
        else:
            await cancel_mission()
    
    if is_passable(new_x, new_y):
        G.player.x, G.player.y = new_x, new_y
        update_player_info()
    if event.key in ["w", "a", "s", "d"]:
        G.player.facing = event.key # type: ignore
    

@prex
async def keyup(event):
    ...
    # print("released:", event.key)


@prex
async def startBtnclicked(event=None):
    start_game_ui_changes()
    name = getElementByIdWithErr('name').value.strip()
    avatar = querySelectorWithErr('input[name="avatar"]:checked').value
    G.player = Player(500, 500, name, avatar)
    body = querySelectorWithErr("body")
    body.onkeydown = keydown
    body.onkeyup = keyup
    await asyncio.sleep(0.0)  # yields control to browser to render DOM
    G.static, G.dynamic = await load_map("map.txt")
    
    update_player_info()
    asyncio.create_task(draw_loop())    


@prex
def is_passable(new_x: int, new_y: int) -> bool:
    """Check whether the player can move to (new_x, new_y) based on entities."""
    all_ents = list(G.static.values()) + list(G.dynamic.values())
    impas = list(filter(lambda e: not e.passable, all_ents))
    for entity in impas:
        if (
            new_x < entity.x + 50 and
            new_x + 50 > entity.x and
            new_y < entity.y + 50 and
            new_y + 50 > entity.y
        ):
                return False
    return True


@prex
def is_face_adj(p: Player, e: Entity):
    """Returns True if player is next-to and facing an entity.
    Example of player below entity, facing up:
    >>> p = Sns(x=300, y=750, facing="w")
    >>> e = Sns(x=300, y=700)
    >>> is_face_adj(p, e)
    True

    Player facing to the right:
    >>> p.facing = "d"
    >>> is_face_adj(p, e)
    False
    """
    if p.x == e.x and p.facing == "w" and p.y == e.y + 50:
        return True
    elif p.x == e.x and p.facing == "s" and p.y == e.y - 50:
        return True
    elif p.y == e.y and p.facing == "a" and p.x == e.x + 50:
        return True
    elif p.y == e.y and p.facing == "d" and p.x == e.x - 50:
        return True
    return False


@prex
async def load_missions(filename: str):
    """Read `filename`. Set `G.all_missions` to the parsed list of Missions."""
    import toml
    text = await read_text(filename)
    parsed = toml.loads(text)
    missions_section = parsed["missions"]
    assert type(missions_section) == list
    G.all_missions = list(map(lambda item: Mission(**item), missions_section))


@prex
async def next_available_mission(available_missions: "list[int]") -> Mission:
    avail_missions = list(filter(lambda x: x.id in available_missions, G.all_missions))
    return avail_missions[0]


@prex
def show_mission_panel(npc: Entity, mission: Mission):
    G.current_target = npc
    G.H.mission_panel.style.display = "flex"  
    G.H.npc_img.src = npc.avatar
    G.H.npc_img.style.width = "300px" 
    G.H.npc_img.style.height = "auto"
    G.H.dialog.innerHTML = mission.dialog
    G.H.accept_btn.onclick = accept_mission
    G.H.cancel_btn.onclick = cancel_mission


@prex
async def accept_mission(event):
    assert G.current_target is not None
    mission = await next_available_mission(G.current_target.available_missions)
    print(f"Mission accepted: {mission.name}")
    G.H.mission_panel.style.display = "none"
    if mission.id not in G.player.current_missions:
        G.player.current_missions.append(mission.id)
    # TODO: Add mission logic here (e.g., mark objectives active)


@prex
async def cancel_mission(event=None):
    assert G.current_target is not None
    G.H.mission_panel.style.display = "none"
    mission = await next_available_mission(G.current_target.available_missions)
    print(f"Mission cancelled: {mission.name}")
    

@prex
def make_image(ep: "Entity | Player") -> "JSImg":
    """Creates an image object for either an Entity or the Player and caches it in img_cache"""
    from js import Image  # type: ignore
    source = ep.avatar
    if source not in G.img_cache:
        img = Image.new()
        
        def onerror(event):
            print(f"ERROR: failed to load image '{source}'")
            raise FileNotFoundError(f"Image not found: {source}")

        img.onerror = onerror
        img.src = source
        G.img_cache[source] = img
    return G.img_cache[source]


@prex
def draw_entities():
    """Draws all entities from the static dictionary to the canvas."""
    for entity in list(G.static.values()) + list(G.dynamic.values()):
        img = make_image(entity)
        screen_x = entity.x - G.player.x + G.H.canvas.width // 2
        screen_y = entity.y - G.player.y + G.H.canvas.height // 2
        G.H.ctx.drawImage(img, screen_x - 25, screen_y - 25, 50, 50)  # center entity image
        

@prex
def draw_player():
    """Draws the player at the center of the canvas and their chosen name below their avatar."""
    img = make_image(G.player)
    cx = G.H.canvas.width // 2
    cy = G.H.canvas.height // 2
    G.H.ctx.drawImage(img, cx - 25, cy - 25, 50, 50) 
    G.H.ctx.font = '12px Arial'
    G.H.ctx.fillStyle = 'black'
    G.H.ctx.textAlign = 'center'
    G.H.ctx.fillText(G.player.name, cx, cy + 40)


@prex
def draw_one_frame():
    """draws bg and runs draw_player() and draw_entities() functions"""
    G.H.ctx.fillStyle = "#bfb"
    G.H.ctx.fillRect(0, 0, G.H.canvas.width, G.H.canvas.height)
    draw_player()
    draw_entities()


@prex
async def read_text(filename: str) -> str:
    """Fetch file using pyfetch if in a browser environment.
    Read file using conventional Python file read otherwise.
    Return the text content.
    
    This is a doctest:
    >>> r = asyncio.run(read_text(__file__))
    >>> type(r)
    <class 'str'>
    """
    try:
        from pyodide.http import pyfetch  # type: ignore
    except ModuleNotFoundError:
        pyfetch = None
    if pyfetch:
        response = await pyfetch(filename)
        if not response.ok:
            raise FileNotFoundError(f"Failed to load {filename} (status {response.status})")
        return await response.text()
    else:
        from pathlib import Path
        return Path(filename).read_text()


@prex
async def load_map(filename: str):
    text = await read_text(filename)
    lines = text.splitlines()
    static = {}
    dynamic = {}

    yindexes = range(-10, len(lines))
    for yidx, line in zip(yindexes, lines):
        xindexes = range(-10, len(line))
        for xidx, char in zip(xindexes, line):
            if char == "w":
                static[f"wall{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/brick2.png", False)
            if char == "r":
                static[f"ruin{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/ruins.png", False)
            elif char == "t":
                static[f"tree{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/tree.png", False)
            elif char == "c":
                dynamic[f"coin{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/coin.png", True)
            elif char == "n":
                dynamic[f"npcr2{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/officer.png", False, available_missions=[27, 29])
            elif char == "👮":
                dynamic[f"npcr1{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/alienBlue_front.png", False, available_missions=[23, 25])
    return static, dynamic


@prex
async def draw_loop():
    fps = 30
    while True:
        draw_one_frame()
        await asyncio.sleep(1 / fps)


@prex
async def install_modules(to_install: "list[str]"):
    print(f"Installing {to_install} modules, please standby...")
    import pyodide_js # type: ignore
    await pyodide_js.loadPackage("micropip")
    import micropip # type: ignore
    for modulename in to_install:
        await micropip.install(modulename)
        print(f"{modulename.upper()} module installed and imported")


@prex
def update_player_info():
    getElementByIdWithErr('info-name').textContent = G.player.name
    getElementByIdWithErr("info-x").textContent = str(G.player.x)
    getElementByIdWithErr("info-y").textContent = str(G.player.y)


@prex
def update_avatar_group(event=None):
    gender_select = getElementByIdWithErr("gender")
    selected = gender_select.value

    avatar_groups = querySelectorAllWithErr("#avatar_cont .avatar-group")
    for group in avatar_groups:
        if group.dataset.gender == selected:
            group.style.display = "flex"
        else:
            group.style.display = "none"


@prex
def start_game_ui_changes(event=None):
    getElementByIdWithErr("menu").style.display = "none"
    getElementByIdWithErr("loader-console").style.display = "none"
    getElementByIdWithErr("game-container").style.display = "flex"
    getElementByIdWithErr("game-console").style.display = "block"
 

@prex
def save_game(event=None):
    """Prompt the player for a save filename and save the current player state."""
    filename = window.prompt("Enter a name for your save:")
    if not filename:
        print("Save cancelled.")
        return
    
    player_dict = G.player.__dict__.copy()
    player_dict["completed_missions"] = list(player_dict["completed_missions"])
    localStorage.setItem(f"save_{filename}", json.dumps(player_dict))
    print(f"Game saved as '{filename}'.")


@prex
def load_game(event=None):
    """Prompt player to select which save to load."""
    # List available saves
    saves = [localStorage.key(i).replace("save_", "") 
             for i in range(localStorage.length) if localStorage.key(i).startswith("save_")]

    if not saves:
        print("No saved games found.")
        return

    save_to_load = window.prompt("Enter the name of the save to load:\n" + "\n".join(saves))
    if not save_to_load or not localStorage.getItem(f"save_{save_to_load}"):
        print("Load cancelled or save not found.")
        return

    raw = localStorage.getItem(f"save_{save_to_load}")
    data = json.loads(raw)
    data["completed_missions"] = set(data["completed_missions"])
    G.player = Player(**data)
    print(f"Game loaded from '{save_to_load}'.")

    try:
        update_player_info()
    except Exception as e:
        print("Error updating player info UI:", e)


def np_array_to_imagedata(img):
    """Convert `img` to the Javascript `ImageData` type,
    which is useable in an HTML canvas context's putImageData. Source: ChatGPT"""
    import numpy as np
    assert type(img) == np.ndarray
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
    return ImageData.new(clamp, w, h)


def visualize_on_canvas(grid):
    import numpy as np
    # relative
    from fdtd.backend import backend as bd  # type: ignore
    grid_energy_3d = bd.sum(grid.E ** 2 + grid.H ** 2, -1)  # type: ignore 
    assert type(grid_energy_3d) == np.ndarray
    grid_energy_xy = grid_energy_3d[:, :, 0]
    geplus1 = grid_energy_xy
    grid_energy_logscale = geplus1 * 50000
    canvas: "Canvas" = getElementByIdWithErr("simpledrawcanvas") # type: ignore 
    ctx = canvas.getContext("2d")
    imageData = np_array_to_imagedata(grid_energy_logscale)
    ctx.putImageData(imageData, 0, 0)


async def loadgrid(filename: str):
    """roughly,
    - read `filename`
    - create a PointSource in spots with "p"
    - create metal in spots with "m"
    """
    import fdtd  # type: ignore
    text = await read_text(filename)
    lines = text.splitlines()
    fdtd.set_backend("numpy")
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
                grid[yidx, xidx, 0] = fdtd.AbsorbingObject(**G.materials["metal"])
            if char == "p":
                grid[yidx, xidx, 0] = fdtd.PointSource(period = 60, amplitude=4, pulse=True, cycle=1) # type: ignore
    return grid


@prex
async def run_sim(event=None):
    await install_modules(["fdtd"])
    grid = await loadgrid("sim_map.txt")  
    for _unus in range(2000):
            visualize_on_canvas(grid)
            grid.step() 
            await asyncio.sleep(0)


@prex
async def main():
    await install_modules(["toml"])
    getElementByIdWithErr('startBtn').onclick = startBtnclicked
    getElementByIdWithErr("save_game").onclick = save_game
    getElementByIdWithErr("load_game").onclick = load_game
    getElementByIdWithErr("gender").onchange = update_avatar_group
    update_avatar_group()
    await load_missions("missions.toml")
    print("Ready.")
    getElementByIdWithErr("run_sim").onclick = run_sim

if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)