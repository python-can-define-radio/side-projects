[[ header stuff ]]

### Introduction

Now that we've seen activity on the spectrum using the Spectrum Analyzer, let's listen to a station.

### How to build it

```python3
## First cell:
import marimo as mo
from paragradio.v2024_12 import PGR_wbfm_rx
## Second cell:
fmrx = PGR_wbfm_rx()
fmrx.start()
```

You should also add sliders for __ ,___, ___...
