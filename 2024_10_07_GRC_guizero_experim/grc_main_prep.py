from distutils.version import StrictVersion
from PyQt5 import Qt
from gnuradio import gr
import sys
import signal


def grc_main_prep(top_block_cls: gr.top_block) -> Qt.QApplication:
    """Copy/paste of the main() function that is generated
    by GRC for Graphical (Qt) flowgraphs. Omits the last line,
    `qapp.exec_()`, because it is blocking; the developer using
    this function is responsible for running `.exec_()`
    on the returned QApplication object."""

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
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
    return qapp
