from gnuradio import gr

v = gr.version()
assert isinstance(v, str)
if v.startswith("3.8"):
    from .specan_gr3_8 import specan_gr3_8 as specan
elif v.startswith("3.10"):
    from .specan_gr3_10 import specan_gr3_10 as specan
else:
    raise NotImplementedError(f"gnuradio version {v} is not known to be supported; you can submit a pull request on URL HERE FOR PARAGRADIO ON GITHUB")