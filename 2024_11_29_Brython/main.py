from browser import document, window, console, alert
from browser.timer import set_interval
from browser.html import P, B, OL, LI, BUTTON, CANVAS
from browser.timer import request_animation_frame
from random import randint
from time import time


def displayError(f):
    def do(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            alert(e)
    return do



document <= B("Hello !")
document <= P("sdf")
document <= OL([
    LI("words"),
    LI("things"),
    LI("etc"),
])
b1 = BUTTON("worddfds")
b1.onclick = lambda unused: alert("hi")
document <= b1



# from dataclasses import dataclass

# @dataclass
# class Poi:
#     x: int
#     y: int

# def aa(unused):
#     global lasttime
#     t = time()
#     elapsed = t - lasttime
#     lasttime = t
#     ctx.clearRect(0, 0, c1.width, c1.height)
#     for p in ps:
#         ctx.fillRect(p.x, p.y, 5, 5)
#         p.x += 100*elapsed
#         p.y += 100*elapsed
#         # if p.x > c1.width:
#         #     p.x -= c1.width
#         # if p.y > c1.height:
#         #     p.y = 0
#     request_animation_frame(aa)

# lasttime = time()
# ps = [Poi(randint(0, 1000), randint(0, 1000)) for unu in range(10000)]
# c1 = CANVAS(width=1000, height=1000)
# document <= c1
# ctx = c1.getContext("2d")
# request_animation_frame(aa)


# console.log("everty")
# inp1 = document.querySelector("#inp1")
# inp2 = document.querySelector("#inp2")
# def ch(ev):
#     inp2.value = inp1.value + str(randint(3, 100))
# inp1.addEventListener("keyup", ch)


# 1. Provide interactive stuff (such as the flow visualizer)
#    easily -- can just click a link
# 2. Provide a UI toolkit to advanced students that 
#    can run anywhere (i.e. the browser) so they can do
#    Python in more places (make your own interactive SPA,
#    make a phone app using Cordova or Capacitor)
# 3. Provide a taste of HTML and JS for students who
#    want to branch out, done so in a way that feels like
#    it's not totally a new skill (since it builds on Python)
# 4. Provide access to newer version of Python





