from parallel_gr_v01 import PGR_specan
from guizero import App, Slider, Text  # type: ignore[import-untyped]
import time


def _set_freq():
    pgr.set_freq(freqslider.value)

def _set_if_gain():
    pgr.set_if_gain(gainslider.value)

default_freq = 98e6
default_gain = 16
pgr = PGR_specan(default_freq, default_gain)
pgr.start()

# app = App(height=200, width=400)
# lbl = Text(app, text="Frequency Slider")
# freqslider = Slider(app, 88e6, 108e6, command=_set_freq)
# freqslider.value = default_freq
# lbl2 = Text(app, text="If Gain Slider")
# gainslider = Slider(app, 0, 40, command=_set_if_gain)
# gainslider.value = default_gain
# gainslider._set_tk_config("resolution", 8)

# app.display()
















# p = P_turtle_xsquared()
# p.start()
# p.set_scale(0.1)
# time.sleep(2)
# p.set_scale(0.03)
# time.sleep(2)
# p.set_scale(2)


## Spec An
##  - freq
##  - if gain
## FM Receiver
##  - freq
##  - if gain
##  - fav stations (radio buttons)
##  - hardware filter?
## Noise Jammer
##  - freq
##  - transit width
##  - cutoff freq
## Digital Jammer
##  - freq