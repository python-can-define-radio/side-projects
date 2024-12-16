from gnuradio import gr


v = gr.version()
assert isinstance(v, str)
if v.startswith("3.8"):
    from .bpsk_tx_loop_gr3_8 import bpsk_tx_loop_gr3_8 as bpsk_tx_loop_fg
    from .qpsk_tx_loop_gr3_8 import qpsk_tx_loop_gr3_8 as qpsk_tx_loop_fg
    ## TODO: add other flowgraph imports
elif v.startswith("3.10"):
    raise NotImplementedError("can do at home")
else:
    raise NotImplementedError(f"gnuradio version {v} is not known to be supported; you can submit a pull request on URL HERE FOR PARAGRADIO ON GITHUB")