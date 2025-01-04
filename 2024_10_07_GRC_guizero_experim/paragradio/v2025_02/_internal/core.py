from distutils.version import StrictVersion
import multiprocessing as mp
import queue
import signal
import sys
import time
from typing import (
    Type, TypeVar, Generic, Callable,
    Protocol, Tuple, Any, Iterable,
    List, Literal, runtime_checkable, TYPE_CHECKING,
    Union,
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
    from .specan.specan_gr3_8 import specan_gr3_8
    from .specan.specan_gr3_10 import specan_gr3_10
    from .wbfm_rx.wbfm_rx_gr3_8 import wbfm_rx_gr3_8
    from .wbfm_rx.wbfm_rx_gr3_10 import wbfm_rx_gr3_10
    from .noise_tx.noise_tx_gr3_8 import noise_tx_gr3_8
    from .noise_tx.noise_tx_gr3_10 import noise_tx_gr3_10
    from .psk_tx_loop.bpsk_tx_loop_gr3_8 import bpsk_tx_loop_gr3_8
    from .psk_tx_loop.psk8_tx_loop_gr3_8 import psk8_tx_loop_gr3_8
    _SpecAn: TypeAlias = Union[specan_gr3_8, specan_gr3_10]
    _Noise_Tx: TypeAlias = Union[noise_tx_gr3_8, noise_tx_gr3_10]    
    _WBFM_Rx: TypeAlias = Union[wbfm_rx_gr3_8, wbfm_rx_gr3_10]
    _PSK_Tx: TypeAlias = Union[bpsk_tx_loop_gr3_8, psk8_tx_loop_gr3_8]


class PGRWrapperCommon():
    _pgr: ParallelGR[Any]
    """This handles interfacing with the parallel process. It 
    shouldn't be used externally unless you know what you're doing."""

    def start(self) -> None:
        """Start the parallel process and its associated GUI."""
        self._pgr.start()


def _set_center_freq_child(tb: "_SpecAn", freq: float) -> None:
    tb.set_center_freq(freq)  # type: ignore[no-untyped-call]

class PGR_can_set_center_freq(PGRWrapperCommon):
    def set_center_freq(self, freq: float) -> None:
        """Set the center frequency of the SDR peripheral and any associated GUI elements."""
        self._pgr.put_cmd(_set_center_freq_child, freq)


def _set_if_gain_child(tb: "_SpecAn", if_gain: float) -> None:
    tb.set_if_gain(if_gain)

class PGR_can_set_if_gain(PGRWrapperCommon):
    def set_if_gain(self, if_gain: float) -> None:
        """Set the Intermediate Frequency gain of the SDR peripheral."""
        self._pgr.put_cmd(_set_if_gain_child, if_gain)


def _set_bb_gain_child(tb: "_SpecAn", bb_gain: float) -> None:
    tb.set_bb_gain(bb_gain)

class PGR_can_set_bb_gain(PGRWrapperCommon):
    def set_bb_gain(self, bb_gain: float) -> None:
        """Set the Baseband gain of the SDR peripheral."""
        self._pgr.put_cmd(_set_bb_gain_child, bb_gain)


def _set_samp_rate_child(tb: "_SpecAn", samp_rate: float) -> None:
    tb.set_samp_rate(samp_rate)  # type: ignore[no-untyped-call]

class PGR_can_set_samp_rate(PGRWrapperCommon):
    def set_samp_rate(self, samp_rate: float) -> None:
        """Sets the sample rate of the SDR peripheral and the bandwidth
        (the amount of viewable spectrum) of the GUI spectrum view.

        Due to the physics of digital sampling, your sample rate is your bandwidth."""
        self._pgr.put_cmd(_set_samp_rate_child, samp_rate)


def _set_hw_bb_filt_child(tb: "_WBFM_Rx", val: float) -> None:
    tb.set_hw_filt_bw(val)  # type: ignore[no-untyped-call]

class PGR_can_set_hw_bb_filt(PGRWrapperCommon):
    def set_hw_bb_filt(self, val: float) -> None:
        """Set the Hardware Baseband Filter.
        
        The HackRF One and many other SDR peripherals have a built-in filter that
        precedes the Analog to Digital conversion. It is able to reduce or prevent
        aliasing, which software filters cannot do.

        Typically, you should set the baseband filter as low as possible for the signals that you wish to receive -- a tighter filter will more effectively reduce aliasing.
        
        For more info, see the Hack RF One documentation about Sampling Rate and 
        Baseband Filters <https://hackrf.readthedocs.io/en/latest/sampling_rate.html>."""
        self._pgr.put_cmd(_set_hw_bb_filt_child, val)


def _set_freq_offset_child(tb: "_WBFM_Rx", freq_offset: float) -> None:
    tb.set_freq_offset(freq_offset)  # type: ignore[no-untyped-call]

class PGR_can_set_freq_offset(PGRWrapperCommon):
    def set_freq_offset(self, freq_offset: float):
        """Set the frequency offset.
        
        When tuning the FM Radio, you'll often get a clearer sound if
        you tune offset to avoid the DC Spike."""
        self._pgr.put_cmd(_set_freq_offset_child, freq_offset)


def _set_noise_type_child(tb: "_Noise_Tx", noise_type: int) -> None:
    tb.set_noise_type(noise_type)  # type: ignore[no-untyped-call]

class PGR_can_set_noise_type(PGRWrapperCommon):
    def set_noise_type(self, noise_type: str):
        """Set the noise type to uniform or gaussian."""
        if noise_type == "uniform":
            nt = 200
        elif noise_type == "gaussian":
            nt = 201
        else:
            raise ValueError("Noise type must be uniform or gaussian.")
        self._pgr.put_cmd(_set_noise_type_child, nt)


def _set_amplitude_child(tb: "_Noise_Tx", amplitude: float) -> None:
    tb.set_amplitude(amplitude)  # type: ignore[no-untyped-call]

class PGR_can_set_amplitude(PGRWrapperCommon):
    def set_amplitude(self, amplitude: float):
        """Update the amplitude of the generated noise."""
        self._pgr.put_cmd(_set_amplitude_child, amplitude)


def _set_filter_cutoff_freq_child(tb: "_Noise_Tx", filter_cutoff_freq: float) -> None:
    tb.set_filter_cutoff_freq(filter_cutoff_freq)  # type: ignore[no-untyped-call]

class PGR_can_set_filter_cutoff_freq(PGRWrapperCommon):
    def set_filter_cutoff_freq(self, filter_cutoff_freq: float):
        """Update the cutoff frequency of the filter that shapes the generated noise before transmitting it."""
        self._pgr.put_cmd(_set_filter_cutoff_freq_child, filter_cutoff_freq)


def _set_filter_transition_width_child(tb: "_Noise_Tx", filter_transition_width: float) -> None:
    tb.set_filter_transition_width(filter_transition_width)  # type: ignore[no-untyped-call]

class PGR_can_set_filter_transition_width(PGRWrapperCommon):
    def set_filter_transition_width(self, filter_transition_width: float):
        """Update the transition width of the filter that shapes the generated noise before transmitting it."""
        self._pgr.put_cmd(_set_filter_transition_width_child, filter_transition_width)


def _set_data_child(tb: "_PSK_Tx", data: List[int]) -> None:
    tb.set_data(data)  # type: ignore[no-untyped-call]

class PGR_can_set_data(PGRWrapperCommon):
    def set_data(self, data: List[int]):
        """Update what data is being repeatedly transmitted."""
        self._pgr.put_cmd(_set_data_child, data)


class SpecAn(
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
        PGR_can_set_bb_gain,
        PGR_can_set_samp_rate,
        PGR_can_set_hw_bb_filt,
    ):
    def __init__(self) -> None:
        """Create a Paragradio Spectrum Analyzer."""
        from .specan import specan_fg
        self._pgr = ParallelGR(specan_fg)


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
        PGR_can_set_hw_bb_filt,
        PGR_can_set_freq_offset,
        # Note: Can't add set_samp_rate because the rational resampler doesn't update at runtime
    ):
    def __init__(self) -> None:
        """Create a Paragradio Wideband FM Receiver."""
        from .wbfm_rx import wbfm_rx_fg
        self._pgr = ParallelGR(wbfm_rx_fg)
    

class Noise_Tx(
        PGR_can_set_samp_rate,
        PGR_can_set_amplitude,
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
        PGR_can_set_noise_type,
        PGR_can_set_filter_cutoff_freq,
        PGR_can_set_filter_transition_width,
    ):
    def __init__(self) -> None:
        from .noise_tx import noise_tx_fg
        self._pgr = ParallelGR(noise_tx_fg)


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
    else:
        raise ValueError("modulation must be one of the options in the type signature")


class PSK_Tx_loop(
        PGR_can_set_center_freq,
        PGR_can_set_if_gain,
        PGR_can_set_amplitude,
        PGR_can_set_data,
        PGR_can_set_samp_rate,
    ):
    def __init__(
            self,
            *, 
            modulation: Literal["BPSK", "QPSK", "DQPSK", "8PSK", "16QAM"],
        ) -> None:
        fg = _pick_flowgraph(modulation)
        self._pgr = ParallelGR(fg)
