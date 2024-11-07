# from nullsourcenullsink import nullsourcenullsink
from distutils.version import StrictVersion
import multiprocessing as mp
import signal
import sys
from threading import Thread
from typing import Type, TypeVar, Generic, Callable, Protocol, Tuple, Any

from gnuradio import gr, analog  # type: ignore[import-untyped]
from PyQt5 import Qt


Tgr = TypeVar("Tgr", bound=gr.top_block)
class TCmd(Protocol):
    def __call__(self, Tgr, *args) -> None: ...



class AboutToQuitAttr(Protocol):
    def connect(self, f: Callable) -> Any: ...

class QAppProt(Protocol):
    def exec_(self) -> Any: ...
    aboutToQuit: AboutToQuitAttr


def grc_main_prep(top_block_cls: Type[gr.top_block]) -> Tuple[gr.top_block, QAppProt]:
    """This is a copy/paste of the main() function that is generated
    by GRC for Graphical (Qt) flowgraphs. It omits the last line
    of that main function, `qapp.exec_()`, because it is blocking.
    The developer using this function is responsible for running `.exec_()`.
    Example usage 1:
    ```python
    tb, qapp = grc_main_prep(a_specific_gr_top_block)
    qapp.exec_()
    ```
    Example usage 2:
    ```python
    tb, qapp = grc_main_prep(a_specific_gr_top_block)
    ## hypothetically, if your `tb` has a signal source block
    tb.signal_source.set_frequency(101.3e6)
    qapp.exec_()
    ```
    """

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):  # type: ignore
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    tb.start()
    tb.show()

    def sig_handler(sig=None, frame=None):
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    def quitting():
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    assert isinstance(qapp, Qt.QApplication)
    return tb, qapp






def _stop_and_wait_q(q: mp.Queue) -> None:
    q.put((_quitcmd, ()))
    q.put((sys.exit, ()))

# def _stop_and_wait(pgrc: "ParallelGRC") -> None:
#     _stop_and_wait_q(pgrc.q)


def _quitcmd(tb):
    from PyQt5 import Qt
    Qt.QApplication.quit()


def _event_loop(top_block_cls: gr.top_block, q: "mp.Queue[TCmd[Tgr]]") -> None:
    """Used to run the Qt/GR process."""
    def processcmds():
        while True:
            cmd, args = q.get(block=True)                
            cmd(tb, *args)

    tb, qapp = grc_main_prep(top_block_cls)
    thread = Thread(target=processcmds)
    thread.start()
    qapp.aboutToQuit.connect(lambda: _stop_and_wait_q(q))
    qapp.exec_()
    

class ParallelGRC(Generic[Tgr]):
    def __init__(self, top_block_cls: Type[Tgr]) -> None:
        self.q: "mp.Queue[TCmd[Tgr]]" = mp.Queue()
        self.proc = mp.Process(target=lambda: _event_loop(top_block_cls, self.q))

    def start(self) -> None:
        self.proc.start()

    def do(self, f: "TCmd[Tgr]", args = ()) -> None:
        self.q.put((f, args))


##### commands for student use


class HasSigSource(Protocol):
    analog_sig_source_x_0: analog.sig_source_c

def _set_freq_tbaction(tb: HasSigSource, freq: float) -> None:
    tb.analog_sig_source_x_0.set_frequency(freq)

def set_freq(pgrc: ParallelGRC, freq: float):
    pgrc.do(_set_freq_tbaction, args=[freq])
