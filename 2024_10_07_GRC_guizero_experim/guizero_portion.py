from guizero import App, Slider, Text
from mod_grc_signal_source import GRC_QBR


qbr = GRC_QBR()


app = App()
s_slidertext = Text(app, text="Frequency Slider")
s = Slider(app, end=2000, command=lambda: qbr.set_freq(s.value))
t_slidertext = Text(app, text="Amplitude Slider")
t = Slider(app, end=100, command=lambda: qbr.set_amp(t.value))
app.display()
