from gnuradio import gr

v = gr.version()
assert isinstance(v, str)
if v.startswith("3.8"):
    from simspecan_gr3_8 import *
elif v.startswith("3.10"):
    from simspecan_gr3_10 import *
else:
    raise NotImplementedError(f"gnuradio version {v} is not known to be supported; you can submit a pull request on URL HERE FOR PARAGRADIO ON GITHUB")