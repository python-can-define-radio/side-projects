from gnuradio import gr

v = gr.version()
assert isinstance(v, str)
if v.startswith("3.8"):
    from .wbfm_rx_gr3_8 import wbfm_rx_gr3_8 as wbfm_rx_fg
elif v.startswith("3.10"):
    from .wbfm_rx_gr3_10 import wbfm_rx_gr3_10 as wbfm_rx_fg
else:
    raise NotImplementedError(f"gnuradio version {v} is not known to be supported; you can submit a pull request on URL HERE FOR PARAGRADIO ON GITHUB")

__all__ = ["wbfm_rx_fg"]
