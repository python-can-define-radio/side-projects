import asyncio
from dataclasses import dataclass, field, fields
import html
import inspect
import random
from typing import Any, Callable, TYPE_CHECKING, Literal, overload, Coroutine

from pyodide.http import pyfetch  # type: ignore
from js import document, Image  # type: ignore



if TYPE_CHECKING:
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

    class CanvasRenderingContext:
        fillStyle: str
        """should be a color or hex code"""
        font: str
        textAlign: str
        @staticmethod
        def fillText(text: str, x: int, y: int):
            ...
        fillRect: Callable[[int, int, int, int], None]
        @staticmethod
        def drawImage(img: JSImg, x: int, y: int, h: int, w: int):
            ...

    class Canvas(HTMLElement):
        getContext: Callable
        height: int
        width: int

console_div = document.getElementById("console")
def print_to_div(*args):
    text = " ".join(html.escape(str(a)) for a in args)
    console_div.innerHTML += text + "<br>"


# Override built-in print
print = print_to_div


def prex(func):
    """A decorator that calls the function in a `try...except`.
    Any exceptions will be printed in the pseudo-console using the modified `print` function.
    Works for sync and async functions;
    Works regardless of whether the function is used with parentheses (`func()` and `onclick = func` both work)."""
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
    current_missions: "list[int]"
    avatar: str = "/assets/femaleAdventurer_idle.png"
    facing_direction: Literal["w", "a", "s", "d"] = "d"
    """wasd -> up, left, down, right"""


@dataclass
class Entity:
    x: int
    y: int
    name: str
    avatar: str
    passable: bool
    available_missions: "list[int]" = field(default_factory=list)
    
    @prex
    def todict(self):
        """
        Omits attrs that end with _
        >>> Entity(3, 5, "abc", "/assets/cool.png", True).todict()
        {'x': 3, 'y': 5, 'name': 'abc', 'avatar': '/assets/cool.png', 'passable': True}
        """
        def impl():
            fds = fields(self.__class__)
            for fd in fds:
                if not fd.name.endswith("_"):
                    yield fd.name, getattr(self, fd.name)
        return dict(impl()) 
    

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

try:
    class G:
        """Global vars. Don't instantiate this class; it's just a grouping"""
        body = querySelectorWithErr("body")
        startBtn = getElementByIdWithErr('startBtn')
        menu = getElementByIdWithErr('menu')
        gameContainer = getElementByIdWithErr('game-container')
        canvas: "Canvas" = getElementByIdWithErr('canvas')  # type: ignore
        infoName = getElementByIdWithErr('info-name')
        ctx: "CanvasRenderingContext" = canvas.getContext('2d')  # type: ignore
        userConfig = {}
        static: "dict[str, Entity]" = {}
        dynamic: "dict[str, Entity]" = {}
        img_cache: "dict[str, JSImg]" = {}
        player: "Player"
        y_tmp: int = 300
except Exception as _exception_while_create_G:
    print("Exception while creating class G:", _exception_while_create_G)


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
    elif event.key == " ":
        for entity in G.dynamic.values():
            if is_adjacent(G.player, entity) and entity.available_missions:
                mission = await next_available_mission(entity.available_missions)
                show_mission_panel(entity, mission)


    if is_passable(new_x, new_y):
        G.player.x, G.player.y = new_x, new_y
    if event.key in ["w", "a", "s", "d"]:
        G.player.facing_direction = event.key # type: ignore
    


@prex
async def keyup(event):
    ...
    # print("released:", event.key)


@prex
async def start_btn_clicked(event=None):
    global userConfig
    userConfig = {
        "name": getElementByIdWithErr('name').value.strip(),
        "avatar": querySelectorWithErr('input[name="avatar"]:checked').value,
        "x": 0,
        "y": 0,
    }
    G.infoName.textContent = userConfig["name"]
    G.menu.style.display = 'none'
    G.gameContainer.style.display = 'flex'
    G.body.onkeydown = keydown
    G.body.onkeyup = keyup
    G.static, G.dynamic = await loadmap()
    G.player = Player(500, 500, userConfig["name"], userConfig["avatar"])
    asyncio.create_task(draw_loop())    


@prex
def is_passable(new_x: int, new_y: int) -> bool:
    """Check if the player can move to (new_x, new_y) based on entities."""
    for entity in G.static.values():
        if not entity.passable:
            if (
                new_x < entity.x + 50 and
                new_x + 50 > entity.x and
                new_y < entity.y + 50 and
                new_y + 50 > entity.y
            ):
                return False
    for entity in G.dynamic.values():
        if not entity.passable:
            if (
                new_x < entity.x + 50 and
                new_x + 50 > entity.x and
                new_y < entity.y + 50 and
                new_y + 50 > entity.y
            ):
                return False
    return True


@prex
def is_adjacent(p: Player, e: Entity):
    if p.x == e.x and p.facing_direction == "w" and p.y == e.y + 50:
        return True
    elif p.x == e.x and p.facing_direction == "s" and p.y == e.y - 50:
        return True
    elif p.y == e.y and p.facing_direction == "a" and p.x == e.x + 50:
        return True
    elif p.y == e.y and p.facing_direction == "d" and p.x == e.x - 50:
        return True
    return False


@prex
async def load_missions():
        import toml
        filename = "missions.toml"
        response = await pyfetch(filename)
        if not response.ok:
            raise FileNotFoundError(f"Failed to load {filename} (status {response.status})")
        text = await response.text()
        file = toml.loads(text)
        return file


# arguments for this function (mission_status: "list[Mission]")
@prex
async def next_available_mission(available_missions: "list[int]") -> Mission:
    missionstoml = await load_missions()
    missions_section = missionstoml["missions"]
    assert type(missions_section) == list
    missions = list(map(lambda item: Mission(**item), missions_section))
    avail_missions = list(filter(lambda x: x.id in available_missions, missions))
    return avail_missions[0]


@prex
def show_mission_panel(npc: Entity, mission: Mission):
    panel = getElementByIdWithErr("mission-panel")
    npc_img = getElementByIdWithErr("mission-npc-img")
    dialog = getElementByIdWithErr("mission-dialog")
    accept_btn = getElementByIdWithErr("mission-accept")
    cancel_btn = getElementByIdWithErr("mission-cancel")

    def cancel_mission():
        panel.style.display = "none"
        print(f"Mission cancelled: {mission.name}")

    # Show panel
    panel.style.display = "flex"  # make sure flex layout shows it

    # Set NPC avatar
    npc_img.src = npc.avatar
    npc_img.style.width = "300px" 
    npc_img.style.height = "auto"

    # Set mission dialog
    dialog.innerHTML = mission.dialog

    # Button actions
    accept_btn.onclick = lambda e=None: accept_mission(mission)
    cancel_btn.onclick = lambda e=None: cancel_mission()


@prex
def accept_mission(mission: Mission):
    print(f"Mission accepted: {mission.name}")
    panel = getElementByIdWithErr("mission-panel")
    panel.style.display = "none"
    G.player.current_missions.append(mission.id)
    # TODO: Add mission logic here (e.g., mark objectives active)


@prex
def make_image(ep: "Entity | Player") -> "JSImg":
    """Creates an image object for either an Entity or the Player and caches it in img_cache"""
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
        screen_x = entity.x - G.player.x + G.canvas.width // 2
        screen_y = entity.y - G.player.y + G.canvas.height // 2
        G.ctx.drawImage(img, screen_x - 25, screen_y - 25, 50, 50)  # center entity image
        

@prex
def draw_player():
    """Draws the player at the center of the canvas and their chosen name below their avatar."""
    img = make_image(G.player)
    cx = G.canvas.width // 2
    cy = G.canvas.height // 2
    G.ctx.drawImage(img, cx - 25, cy - 25, 50, 50) 
    G.ctx.font = '12px Arial'
    G.ctx.fillStyle = 'black'
    G.ctx.textAlign = 'center'
    G.ctx.fillText(G.player.name, cx, cy + 40)


@prex
def draw_one_frame():
    """draws bg and runs draw_player() and draw_entities() functions"""
    G.ctx.fillStyle = "#bfb"
    G.ctx.fillRect(0, 0, G.canvas.width, G.canvas.height)
    draw_player()
    draw_entities()


@prex
async def loadmap():
    filename = "map.txt"
    response = await pyfetch(filename)
    if not response.ok:
        raise FileNotFoundError(f"Failed to load {filename} (status {response.status})")
    text: str = await response.text()
    lines = text.splitlines()
    static = {}
    dynamic = {}
    xindexes = range(-10, len(lines[0]))
    yindexes = range(-10, len(lines))
    for yidx, line in zip(yindexes, lines):
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
    print("Installing modules:", to_install)
    import pyodide_js # type: ignore
    await pyodide_js.loadPackage("micropip")
    import micropip # type: ignore
    for modulename in to_install:
        await micropip.install(modulename)


@prex
async def main():
    await install_modules(["toml", "fdtd"])
    G.startBtn.onclick = start_btn_clicked
    print("Ready.")
    

    # TODO: convert below from JS
#         #                     infoX.textContent = me.x.toFixed(0);
#         #                     infoY.textContent = me.y.toFixed(0);
#         #                     infoScore.textContent = score; // static for now
#         #                     if (me.talking_to) {
#         #                         // SHOW MISSION PANEL
#         #                         missionPanel.style.display = "block";
#         #                         missionNPCImg.src = me.talking_to.avatar;
#         #                         if (me.potential_mission) {
#         #                             missionDialog.innerHTML = me.potential_mission.dialog;
#         #                         } else {
#         #                             missionDialog.innerHTML = "not sure what to say";
#         #                         }

#         #                     } else {
#         #                         // HIDE MISSION PANEL
#         #                         missionPanel.style.display = "none";
#         #                     }
#         #                    
#         #                     draw(dynamic, me.x, me.y);

#         #     const missionPanel = document.getElementById("mission-panel");
#         #     const missionNPCImg = document.getElementById("mission-npc-img");
#         #     const missionDialog = document.getElementById("mission-dialog");

#         #     document.getElementById("mission-cancel").onclick = () => {
#         #         missionPanel.style.display = "none";

#         #     document.getElementById("mission-accept").onclick = () => {
#         #         // For now: simply hide panel
#         #         missionPanel.style.display = "none";

#         #         // NOTE: you can later add mission acceptance logic here.
#         #     };
#         # }


    