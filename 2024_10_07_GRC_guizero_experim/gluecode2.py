# from nullsourcenullsink import nullsourcenullsink
from distutils.version import StrictVersion
import multiprocessing as mp
import signal
import sys
from threading import Thread
from typing import Type, TypeVar, Generic, Callable, Protocol, Tuple, Any, Iterable, List
from typing_extensions import ParamSpec, Concatenate

from gnuradio import gr, analog  # type: ignore[import]
from PyQt5 import Qt    # type: ignore[attr-defined]


Tgr = TypeVar("Tgr", bound=gr.top_block)
P = ParamSpec("P")

TbFunc = Callable[Concatenate[Any, P], None]
"""A function whose signature looks like any of the below.
Note that the first argument should be an instance of `gr.top_block` or any subclass,
but this is not easily enforced due to the variety of possible subclass
attributes, so it is labelled as "Any".

```python
def f(tb) -> None: ...
def f(tb, a) -> None: ...
def f(tb, a, b) -> None: ...
def f(tb, a, b, c) -> None: ...
# etc...
```
"""

cmdqueue = mp.Queue[Tuple[TbFunc[P], Iterable[Any]]]


class AboutToQuitAttr(Protocol):
    def connect(self, f: Callable[[], Any]) -> Any: ...

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

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    tb.start()
    tb.show()

    def sig_handler(sig=None, frame=None):  # type: ignore
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    def quitting():   # type: ignore
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    assert isinstance(qapp, Qt.QApplication)
    return tb, qapp


def _stop_and_wait(q: cmdqueue) -> None:  # type: ignore
    q.put((_quitcmd, ()))    # type: ignore
    q.put((sys.exit, ()))    # type: ignore


def _quitcmd(tb) -> None:   # type: ignore
    """The unused tb param is required because the queue will pass in that arg"""
    Qt.QApplication.quit()


def _event_loop(top_block_cls: gr.top_block, q: cmdqueue[Any]) -> None:
    """Used to run the Qt/GR process."""
    def processcmds() -> None:
        while True:
            cmd, args = q.get(block=True)                
            cmd(tb, *args)

    tb, qapp = grc_main_prep(top_block_cls)
    thread = Thread(target=processcmds)
    thread.start()
    qapp.aboutToQuit.connect(lambda: _stop_and_wait(q))
    qapp.exec_()
    

class ParallelGR(Generic[Tgr]):
    def __init__(self, top_block_cls: Type[Tgr]) -> None:
        self.q: cmdqueue[Any] = mp.Queue()
        self.proc = mp.Process(target=lambda: _event_loop(top_block_cls, self.q))

    def start(self) -> None:
        self.proc.start()

    def put_cmd(self, f: TbFunc[P], *args: P.args, **kwargs: P.kwargs) -> None:
        """Put a command into the queue for the child
        process to execute. Any extra args provided will be
        passed to `f`."""
        self.q.put((f, args))


##### commands for student use


class HasSigSource(Protocol):
    analog_sig_source_x_0: analog.sig_source_c

def _set_freq_tbaction(tb: HasSigSource, freq: float) -> None:
    tb.analog_sig_source_x_0.set_frequency(freq)

def set_freq(pgr: ParallelGR[Any], freq: float) -> None:
    pgr.put_cmd(_set_freq_tbaction, freq)
