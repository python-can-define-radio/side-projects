from gnuradio import gr


v = gr.version()
assert isinstance(v, str)
if v.startswith("3.8"):
    from .psk_tx_loop_gr3_8 import psk_tx_loop_gr3_8 as psk_tx_loop_fg
else:
    raise NotImplementedError(f"gnuradio version {v} is not known to be supported; you can submit a pull request on URL HERE FOR PARAGRADIO ON GITHUB")

__all__ = ["psk_tx_loop_fg"]
