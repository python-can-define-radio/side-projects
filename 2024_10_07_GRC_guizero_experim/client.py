from parallel_gr_v01 import P_turtle_xsquared, PGR_basicsourcesinkwater
from guizero import App, Slider  # type: ignore[import-untyped]
import time

# p = P_turtle_xsquared()
# p.start()
# p.set_scale(0.1)
# time.sleep(2)
# p.set_scale(0.03)
# time.sleep(2)
# p.set_scale(2)


pgr = PGR_basicsourcesinkwater()
pgr.start()
time.sleep(1)
pgr.set_freq(10e3)
time.sleep(2)
pgr.set_freq(4e3)

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