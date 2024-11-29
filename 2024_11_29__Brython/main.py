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



# from browser.timer import request_animation_frame
# from browser.timer import cancel_animation_frame as caf
# from browser import document as doc
# from browser import window as win
# from time import time
# from browser.html import CANVAS, BUTTON
# import math

# c1 = CANVAS(width=1000, height=1000)
# document <= c1
# ctx = c1.getContext('2d')

# toggle = True

# def draw(unused):
#     t = time() * 3
#     x = (math.sin(t) * 96 + 128) * 2
#     y = (math.cos(t * 0.9) * 96 + 128) * 2
#     global toggle
#     if toggle:
#         toggle = False
#     else:
#         toggle = True
#     ctx.fillStyle = 'rgb(200,200,20)' if toggle else 'rgb(20,20,200)'
#     ctx.beginPath()
#     ctx.arc( x, y, 6, 0, math.pi * 2, True)
#     ctx.closePath()
#     ctx.fill()
#     request_animation_frame(draw)

# request_animation_frame(draw)
# banim = BUTTON("anim")
# banim.onclick = animate
# document <= banim
# doc['btn-animate'].bind('click', animate)
# doc['btn-stop'].bind('click', stop)



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


# from browser import document, window
# from browser.html import DIV
# import random
# import javascript

# # 'importing' the bokehJS library
# Bokeh = window.Bokeh
# plt = Bokeh.Plotting

# # set up some data
# M = 100
# xx = []
# yy = []
# colors = []
# radii = []
# for y in range(0, M, 4):
#     for x in range(0, M, 4):
#         xx.append(x)
#         yy.append(y)
#         colors.append(plt.color(50+2*x, 30+2*y, 150))
#         radii.append(random.random() * 0.4 + 1.7)

# # create a data source
# source = Bokeh.ColumnDataSource.new({
#     'data': {'x': xx, 'y': yy, 'radius': radii, 'colors': colors}
# })

# # make the plot and add some tools
# tools = "pan,crosshair,wheel_zoom,box_zoom,reset,save"
# p = plt.figure({'title': "Colorful Scatter", 'tools': tools})

# # call the circle glyph method to add some circle glyphs
# circles = p.circle({'field': "x" }, {'field': "y" }, {
#     'source': source
# })

# # show the plot

# # mydiv = document['myplot']
# mydiv = DIV()
# document <= mydiv
# # below, as a second parameter you can pass an HTML element like below
# plt.show(p, mydiv)
# but also a css selector could be used so the next line would be also
# valid
# plt.show(p, '#myplot')


