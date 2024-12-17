from gnuradio import gr


v = gr.version()
assert isinstance(v, str)
if v.startswith("3.8"):
    from .bpsk_tx_loop_gr3_8 import bpsk_tx_loop_gr3_8 as bpsk_tx_loop_fg
    from .qpsk_tx_loop_gr3_8 import qpsk_tx_loop_gr3_8 as qpsk_tx_loop_fg
    from .dqpsk_tx_loop_gr3_8 import dqpsk_tx_loop_gr3_8 as dqpsk_tx_loop_fg
    from .psk8_tx_loop_gr3_8 import psk8_tx_loop_gr3_8 as psk8_tx_loop_fg
    from .qam16_tx_loop_gr3_8 import qam16_tx_loop_gr3_8 as qam16_tx_loop_fg
elif v.startswith("3.10"):
    raise NotImplementedError("can do at home once the 3.8 flowgraphs are complete")
else:
    raise NotImplementedError(f"gnuradio version {v} is not known to be supported; you can submit a pull request on URL HERE FOR PARAGRADIO ON GITHUB")