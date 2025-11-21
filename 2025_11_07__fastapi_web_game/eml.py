import asyncio
from dataclasses import dataclass
import random
from typing import Any, Callable, TYPE_CHECKING

from js import document


if TYPE_CHECKING:
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
        fillRect: Callable[[int, int, int, int], None]

    class Canvas(HTMLElement):
        getContext: Callable
        height: int
        width: int

console_div = document.getElementById("console")
def print_to_div(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    console_div.innerHTML += text + "<br>"

# Override built-in print
print = print_to_div


class ElementNotFoundError(Exception):
    ...

@dataclass
class Player:
    x: int
    y: int
    name: str
    avatar: str = "/assets/femaleAdventurer_idle.png"


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
        gstatic = {}
        img = {}
        player: "Player | None"
        y_tmp: int = 300
except Exception as _exception_while_create_G:
    print("Exception while creating class G:", _exception_while_create_G)


def keydown(event):
    print("pressed:", event.key)

def keyup(event):
    print("released:", event.key)

def start_btn_clicked(event=None):
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
    asyncio.create_task(draw_loop())


def draw(items, centerx, centery):
    for cid in items.keys():
        print("todo", cid)
        # const { x, y, name, avatar } = items[cid];
        # const offsetx = x - centerx + canvas.width / 2;
        # const offsety = y - centery + canvas.height / 2;
        # if (!(avatar in img)) {
        #     img[avatar] = new Image();
        #     img[avatar].src = avatar;
        # }
        # ctx.drawImage(img[avatar], offsetx - 25, offsety - 25, 50, 50);

        # ctx.font = '12px Arial';
        # ctx.fillStyle = 'black';
        # ctx.textAlign = 'center';
        # ctx.fillText(name, offsetx, offsety + 40);

def draw_background():
    G.ctx.fillStyle = "#bfb"
    G.ctx.fillRect(0, 0, G.canvas.width, G.canvas.height)
    G.ctx.fillStyle = "#000"
    G.ctx.fillRect(0, 0, 200, G.y_tmp)
    G.y_tmp += random.randint(-2, 2)

async def draw_loop():
    fps = 30
    while True:
        draw_background()
        await asyncio.sleep(1 / fps)


def main():
    print("Python started!")
    G.startBtn.onclick = start_btn_clicked


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

#         #                     draw(players, me.x, me.y);
#         #                     draw(dynamic, me.x, me.y);
#         #                     draw(gstatic, me.x, me.y);
#         #                 }
#         #             } else {
#         #                 const { static } = JSON.parse(event.data);
#         #                 if (static !== undefined) {
#         #                     gstatic = static;
#         #                 } else {
#         #                     alert("Err: Didn't receive static Entity info, but was expecting to.")
#         #                 }
#         #             }
#         #         } catch (e) {
#         #             alert(e);
#         #         }
#         #     };



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

#         #         socket.send(JSON.stringify({
#         #             eventkind: "click",
#         #             button: "mission-cancel",
#         #         }));
#         #     };

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


def main_wrapper():
    try:
        main()
    except Exception as e:
        print("Exception:", e)