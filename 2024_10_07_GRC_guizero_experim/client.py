import time
from basicsourcesinkwater import basicsourcesinkwater
from gluecode2 import ParallelGRC, set_freq


pgrc = ParallelGRC(basicsourcesinkwater)
pgrc.start()
time.sleep(1)
set_freq(pgrc, 10e3)
time.sleep(2)
set_freq(pgrc, 4e3)
