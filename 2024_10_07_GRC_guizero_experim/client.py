import time
from basicsourcesinkwater import basicsourcesinkwater
from gluecode2 import ParallelGR, set_freq
from guizero import App, Slider  # type: ignore[import]

pgr = ParallelGR(basicsourcesinkwater)
pgr.start()
time.sleep(1)
set_freq(pgr, 10e3)
time.sleep(2)
set_freq(pgr, 4e3)

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