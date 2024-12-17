# from nullsourcenullsink import nullsourcenullsink
from distutils.version import StrictVersion
import multiprocessing as mp
import queue
import signal
import sys
import time
from typing import (
    Type, TypeVar, Generic, Callable,
    Protocol, Tuple, Any, Iterable,
    List, Literal, runtime_checkable, TYPE_CHECKING
)



T = TypeVar("T")

Tgr = TypeVar("Tgr", bound="gr.top_block")
"""A gr top block or a subclass of such."""


if TYPE_CHECKING:
    from typing_extensions import ParamSpec, Concatenate, TypeAlias
    from gnuradio import gr  # type: ignore[import-untyped]
    from turtle import Turtle
    
    P = ParamSpec("P")

    TPFunc = Callable[Concatenate[T, P], None]
    """A function which takes at least one argument.
    In this particular project, the first argument is most often 
    an instance of `gr.top_block` or any subclass.

    Examples:

    ```python
    def f(tb) -> None: ...
    def f(tb, a) -> None: ...
    def f(tb, a, b) -> None: ...
    def f(tb, a, b, c) -> None: ...
    # etc...
    ```
    """

    _cmdqueue = mp.Queue[Tuple[TPFunc[T, P], Iterable[P.args]]]
    """A queue of tuples. Each tuple is (func, args), 
    where the function's first argument is of type `T` (generic),
    and the functions other args are of "the correct type". Example:
    ```python3
    def f(a: list, b: str, c: int):
        ...
    
    q = mp.Queue()
    args = ("foo", 33)
    q.put((f, args))
    ```
    """


@runtime_checkable
class _AboutToQuitAttr(Protocol):
    def connect(self, f: Callable[[], Any]) -> Any: ...

@runtime_checkable
class _QAppProt(Protocol):
    def exec_(self) -> Any: ...
    aboutToQuit: _AboutToQuitAttr


class ProcessTerminated(RuntimeError):
    ...
    

def _grc_main_prep(top_block_cls: "Type[Tgr]") -> "Tuple[Tgr, _QAppProt]":
    """This is a copy/paste of the main() function that is generated
    by GRC for Graphical (Qt) flowgraphs. It omits the last line
    of that main function, `qapp.exec_()`, because it is blocking.
    The developer using this function is responsible for running `.exec_()`.
    Example usage 1:
    ```python
    tb, qapp = _grc_main_prep(a_specific_gr_top_block)
    qapp.exec_()
    ```
    Example usage 2:
    ```python
    tb, qapp = _grc_main_prep(a_specific_gr_top_block)
    ## hypothetically, if your `tb` has a signal source block
    tb.signal_source.set_frequency(101.3e6)
    qapp.exec_()
    ```
    """
    from PyQt5 import Qt     # type: ignore[import-untyped]
    from gnuradio import gr

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    tb.start()
    tb.show()

    def sig_handler(sig=None, frame=None) -> None:  # type: ignore[no-untyped-def]
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    def quitting() -> None:
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    assert isinstance(tb, gr.top_block)
    assert isinstance(qapp, _QAppProt)
    assert isinstance(qapp.aboutToQuit, _AboutToQuitAttr)
    return tb, qapp


def _processcmds(instance: "T", q: "_cmdqueue[T, P]") -> None:
    """Pulls a command from the queue `q`, and calls it
    with `instance` as the first argument. `instance` is often a `gr.top_block`
    (which is conventionally named `tb` in the .py files generated by GRC.)"""
    try:
        cmd, args = q.get(block=False)
        cmd(instance, *args)
    except queue.Empty:
        pass


def _event_loop_gr(top_block_cls: "Type[Tgr]", q: "_cmdqueue[Tgr, P]") -> None:
    """Run the Qt/GR process.
    - Sets up the top_block similarly to the `main()` function in the .py file that GRC generates
    - Starts a repeating Qt timer to get and execute commands from `q`
    - Runs the Qt application (assumes that `top_block_cls` is a Qt-based GR flowgraph)"""
    from PyQt5 import Qt
    tb, qapp = _grc_main_prep(top_block_cls)
    timer = Qt.QTimer()
    timer.start(1)
    timer.timeout.connect(lambda: _processcmds(tb, q))
    qapp.aboutToQuit.connect(lambda: print("Gracefully exiting GRC flowgraph."))
    qapp.exec_()


class ParallelGR(Generic[Tgr]):
    def __init__(self, top_block_cls: "Type[Tgr]") -> None:
        self.__q: "_cmdqueue[Tgr, ...]" = mp.Queue()
        self.__proc = mp.Process(target=lambda: _event_loop_gr(top_block_cls, self.__q))

    def start(self) -> None:
        self.__proc.start()

    def put_cmd(self, f: "TPFunc[Tgr, P]", *args: "P.args", **kwargs: "P.kwargs") -> None:
        """Put a command into the queue for the child
        process to execute. Any extra args provided will be
        passed to `f`."""
        if not self.__proc.is_alive():
            raise ProcessTerminated("The parallel process has terminated; cannot execute commands.")
        self.__q.put((f, args))


##### commands for student use

if TYPE_CHECKING:
    from .specan import specan_fg
    import numpy as np


class PGRWrapperCommon():
    _pgr: ParallelGR[Any]

    def start(self) -> None:
        """Start the parallel process and its associated GUI."""
        self._pgr.start()


if TYPE_CHECKING:
    _can_set_center_freq: TypeAlias = specan_fg

class PGR_can_set_center_freq(PGRWrapperCommon):
    @staticmethod
    def _set_center_freq_child(tb: "_can_set_center_freq", freq: float) -> None:
        tb.set_center_freq(freq)  # type: ignore[no-untyped-call]

    def set_center_freq(self, freq: float) -> None:
        """Set the center frequency of the SDR peripheral and any associated GUI elements."""
        This_Class = self.__class__
        self._pgr.put_cmd(This_Class._set_center_freq_child, freq)


if TYPE_CHECKING:
    _can_set_if_gain: TypeAlias = specan_fg

class PGR_can_set_if_gain(PGRWrapperCommon):
    @staticmethod
    def _set_if_gain_child(tb: "_can_set_if_gain", gain: float) -> None:
        tb.osmosdr_source_0.set_if_gain(gain)

    def set_if_gain(self, gain: float) -> None:
        """Set the Intermediate Frequency gain of the SDR peripheral."""
        This_Class = self.__class__
        self._pgr.put_cmd(This_Class._set_if_gain_child, gain)


if TYPE_CHECKING:
    _can_set_bb_gain: TypeAlias = specan_fg

class PGR_can_set_bb_gain(PGRWrapperCommon):
    @staticmethod
    def _set_bb_gain_child(tb: "_can_set_bb_gain", gain: float) -> None:
        tb.osmosdr_source_0.set_bb_gain(gain)

    def set_bb_gain(self, gain: float) -> None:
        """Set the Baseband gain of the SDR peripheral."""
        This_Class = self.__class__
        self._pgr.put_cmd(This_Class._set_bb_gain_child, gain)


if TYPE_CHECKING:
    _can_set_bw: TypeAlias = specan_fg

class PGR_can_set_bw(PGRWrapperCommon):
    @staticmethod
    def _set_bw_child(tb: "_can_set_bw", bw: float) -> None:
        tb.set_samp_rate(bw)  # type: ignore[no-untyped-call]

    def set_bw(self, bw: float) -> None:
        """Set the Bandwidth. The specific meaning is
        documented in the docstring of child classes."""
        This_Class = self.__class__
        self._pgr.put_cmd(This_Class._set_bw_child, bw)


class SpecAn(
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
        PGR_can_set_bb_gain,
        PGR_can_set_bw,
    ):
    def __init__(self, bw: float = 2e6, freq: float = 98e6, if_gain: int = 24) -> None:
        """Create a Paragradio Spectrum Analyzer.
        Arguments are explained in their associated methods:
        bw: see `set_bw()`
        freq: see `set_center_freq()`
        if_gain: see `if_gain()`
        """
        from .specan import specan_fg
        self._pgr = ParallelGR(specan_fg)
        self.set_bw(bw)
        self.set_center_freq(freq)
        self.set_if_gain(if_gain)

    def set_bw(self, bw: float) -> None:
        """Sets the bandwidth (the amount of viewable spectrum)
        of the GUI spectrum view. Also sets the sample rate 
        of the SDR peripheral."""
        super().set_bw(bw)


class SpecAnSim(PGR_can_set_center_freq):
    def __init__(self) -> None:
        """Create a Paragradio Simulated Spectrum Analyzer with simulated activity on 93.5 MHz.
        """
        from .specansim import specansim_fg
        self._pgr = ParallelGR(specansim_fg)

    def set_center_freq(self, freq: float) -> None:
        """Set the center frequency of simulated spectrum view."""
        super().set_center_freq(freq)


class WBFM_Rx(
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
        PGR_can_set_bb_gain,
        PGR_can_set_bw,
    ):
    def __init__(self, bw: float = 2e6, freq: float = 98e6, if_gain: int = 24) -> None:
        """Create a Paragradio Wideband FM Receiver.
        Arguments are explained in their associated methods:
        bw: see `set_bw()`
        freq: see `set_center_freq()`
        if_gain: see `if_gain()`
        """
        from .wbfm_rx import wbfm_rx_fg
        self._pgr = ParallelGR(wbfm_rx_fg)
        self.set_bw(bw)
        self.set_center_freq(freq)
        self.set_if_gain(if_gain)

    def set_bw(self, bw: float) -> None:
        """Sets the bandwidth (the amount of viewable spectrum)
        of the GUI spectrum view. Also sets the sample rate 
        of the SDR peripheral."""
        super().set_bw(bw)


class Noise_Tx(
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
    ):
    def __init__(self) -> None:
        from .noise_tx import noise_tx_fg
        self._pgr = ParallelGR(noise_tx_fg)

    ## TODO:
    ## for noise transmitter, allow user to set using string.
    ## "uniform" -> 200
    ## "gaussian" -> 201


def _pick_flowgraph(modulation: Literal["BPSK", "QPSK", "DQPSK", "8PSK", "16QAM"]) -> "gr.top_block":
    from .psk_tx_loop import bpsk_tx_loop_fg, qpsk_tx_loop_fg, dqpsk_tx_loop_fg, psk8_tx_loop_fg, qam16_tx_loop_fg
    if modulation == "BPSK":
        return bpsk_tx_loop_fg
    elif modulation == "QPSK":
        return qpsk_tx_loop_fg
    elif modulation == "DQPSK":
        return dqpsk_tx_loop_fg
    elif modulation == "8PSK":
        return psk8_tx_loop_fg
    elif modulation == "16QAM":
        return qam16_tx_loop_fg


class PSK_Tx_loop(
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
    ):
    def __init__(
            self,
            modulation: Literal["BPSK", "QPSK", "DQPSK", "8PSK", "16QAM"],
        ) -> None:
        fg = _pick_flowgraph(modulation)
        self._pgr = ParallelGR(fg)

    def set_data(self, data: "np.ndarray"):
        """Update what data is being repeatedly transmitted."""
        ...


