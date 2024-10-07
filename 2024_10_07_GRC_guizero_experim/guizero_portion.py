from guizero import App, Slider
from mod_grc_signal_source import GRC_QBR


qbr = GRC_QBR()


app = App()
s = Slider(app, end=2000, command=lambda: qbr.set_freq(s.value))
app.display()
