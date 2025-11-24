import asyncio
from dataclasses import dataclass, field, fields
import html
import random
from typing import Any, Callable, TYPE_CHECKING

from pyodide.http import pyfetch  # type: ignore
from js import document, Image  # type: ignore


if TYPE_CHECKING:
    class JSImg:
        """Created by Image.new(). There's probably a better name for this"""

    class HTMLElement:
        textContent: str
        style: ...
        onclick: Callable
        onkeydown: Callable
        onkeyup: Callable
        value: "str | Any"

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

def prex(f: Callable):
    """`try` calling `f`. Print any exceptions that are raised.
    f must take no arguments, so any functions that take arguments must be wrapped in a lambda as shown:
    prex(lambda: the_function_we_want_to_call(3, 5))"""
    try:
        return f()
    except Exception as e:
        print("Exception in", f.__name__, e)
        raise


def prex_passive(f: Callable):
    """Equivalent of `prex`, used for so-called 'passive functions'.
    Example: element.onclick = prex_passive(the_function_we_want_to_call)"""
    async def prexwrap(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            print("Exception in", f.__name__, e)
            raise
    return prexwrap


class ElementNotFoundError(Exception):
    ...

@dataclass
class Player:
    x: int
    y: int
    name: str
    avatar: str = "/assets/femaleAdventurer_idle.png"


@dataclass
class Entity:
    x: int
    y: int
    name: str
    avatar: str
    passable: bool
    available_missions: "list[int]" = field(default_factory=list)
    info: "str | None" = None
    
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
    

def getElementByIdWithErr(elemid: str) -> "HTMLElement":
    """Same as normal `document.getElementById`, but
    raises an exception if the element does not exist."""
    r = document.getElementById(elemid)
    if r is None:
        raise ElementNotFoundError(f"Element with id '{elemid}' not found")
    else:
        return r


def querySelectorWithErr(query: str) -> "HTMLElement":
    """Same as normal `document.querySelector`, but
    raises an exception if the element does not exist."""
    r = document.querySelector(query)
    if r is None:
        raise ElementNotFoundError(f"Query '{query}' found no elements")
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
        infoX = getElementByIdWithErr('info-x')
        infoY = getElementByIdWithErr('info-y')
        ctx: "CanvasRenderingContext" = canvas.getContext('2d')  # type: ignore
        userConfig = {}
        static: "dict[str, Entity]" = {}
        dynamic = {}
        img = {}
        player: "Player"
        y_tmp: int = 300
except Exception as _exception_while_create_G:
    print("Exception while creating class G:", _exception_while_create_G)


async def keydown(event):
    print("pressed:", event.key)
    if event.key == "w":
        G.player.y -= 50
    elif event.key == "d":
        G.player.x += 50
    elif event.key == "a":
        G.player.x -= 50
    elif event.key == "s":
        G.player.y += 50

async def keyup(event):
    print("released:", event.key)

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
    G.body.onkeydown = prex_passive(keydown)
    G.body.onkeyup = prex_passive(keyup)
    G.static, G.dynamic = await prex(loadmap)
    G.player = Player(500, 500, userConfig["name"], userConfig["avatar"])
    asyncio.create_task(draw_loop())    


def make_image(entity: "Entity | Player") -> "JSImg":
    img = Image.new()
    img.src = entity.avatar
    return img
    

def draw_entities():
    for entity in G.static.values():
        img = make_image(entity)
        G.ctx.drawImage(img, entity.x,entity.y,50,50)
        offsetx = entity.x - G.player.x + G.canvas.width // 2
        offsety = entity.y - G.player.y + G.canvas.height // 2
        G.ctx.font = '12px Arial'
        G.ctx.fillStyle = 'black'
        G.ctx.textAlign = 'center'
        G.ctx.fillText(entity.name, offsetx, offsety + 40)


def draw_player():
    img = make_image(G.player)
    G.ctx.drawImage(img, G.player.x, G.player.y, 50, 50)


def draw_one_frame():
    """draws bg and a randomly resizing square"""
    G.ctx.fillStyle = "#bfb"
    G.ctx.fillRect(0, 0, G.canvas.width, G.canvas.height)
    draw_player()
    draw_entities()

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
                static[f"tree{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/tree.png", False, info="You hear the leaves faintly rustling as wind passes.")
            elif char == "c":
                dynamic[f"coin{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/coin.png", True)
            elif char == "👮":
                dynamic[f"npc{xidx},{yidx}"] = Entity(50*xidx, 50*yidx, "", "/assets/alienBlue_front.png", False, available_missions=[23])
    return static, dynamic


async def draw_loop():
    fps = 30
    while True:
        prex(draw_one_frame)
        await asyncio.sleep(1 / fps)


async def main():
    print("Python started!")
    G.startBtn.onclick = prex_passive(start_btn_clicked)
    

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

#         #     addEventListener("keyup", function (event) {
#         #         socket.send(JSON.stringify({
#         #             key: event.key,
#         #             eventkind: "keyup",
#         #         }));
#         #     });

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

#         # const genderSelect = document.getElementById("gender");
#         # const avatarGroups = document.querySelectorAll(".avatar-group");

#         # function updateAvatarGroup() {
#         #     const selectedGender = document.getElementById("gender").value;
#         #     const groups = document.querySelectorAll("#avatar_cont .avatar-group");

#         #     groups.forEach(group => {
#         #         if (group.dataset.gender === selectedGender) {
#         #             group.style.display = "flex";
#         #         } else {
#         #             group.style.display = "none";
#         #         }
#         #     });
#         # }

#         # // Call on page load to set the correct default
#         # document.addEventListener("DOMContentLoaded", () => {
#         #     updateAvatarGroup();
#         #     // Add event listener for dropdown changes
#         #     document.getElementById("gender").addEventListener("change", updateAvatarGroup);
#         # });



async def main_wrapper():
    try:
        await main()
    except Exception as e:
        print("Exception:", e)