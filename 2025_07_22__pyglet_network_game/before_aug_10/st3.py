import pyglet

window = pyglet.window.Window()
# image = pyglet.resource.image('smile.png')
image = pyglet.image.ImageData(1, 1, "L", bytes(3))

@window.event
def on_draw():
    window.clear()
    image.blit(0, 0)

pyglet.app.run()
