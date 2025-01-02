#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: noise_tx_gr3_10
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import osmosdr
import time
import sip



class noise_tx_gr3_10(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "noise_tx_gr3_10", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("noise_tx_gr3_10")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "noise_tx_gr3_10")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 2e6
        self.noise_type = noise_type = 201
        self.if_gain = if_gain = 0
        self.filter_transition_width = filter_transition_width = 70e3
        self.filter_cutoff_freq = filter_cutoff_freq = 300e3
        self.center_freq = center_freq = 2.4e9
        self.amplitude = amplitude = 0

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            center_freq, #fc
            samp_rate, #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_win)
        self.osmosdr_sink_0 = osmosdr.sink(
            args="numchan=" + str(1) + " " + "hackrf=0"
        )
        self.osmosdr_sink_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(center_freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        self.osmosdr_sink_0.set_gain(0, 0)
        self.osmosdr_sink_0.set_if_gain(if_gain, 0)
        self.osmosdr_sink_0.set_bb_gain(0, 0)
        self.osmosdr_sink_0.set_antenna('', 0)
        self.osmosdr_sink_0.set_bandwidth(0, 0)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                filter_cutoff_freq,
                filter_transition_width,
                window.WIN_HAMMING,
                6.76))
        self.analog_noise_source_x_0 = analog.noise_source_c(noise_type, amplitude, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_noise_source_x_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.qtgui_waterfall_sink_x_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "noise_tx_gr3_10")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.filter_cutoff_freq, self.filter_transition_width, window.WIN_HAMMING, 6.76))
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(self.center_freq, self.samp_rate)

    def get_noise_type(self):
        return self.noise_type

    def set_noise_type(self, noise_type):
        self.noise_type = noise_type
        self.analog_noise_source_x_0.set_type(self.noise_type)

    def get_if_gain(self):
        return self.if_gain

    def set_if_gain(self, if_gain):
        self.if_gain = if_gain
        self.osmosdr_sink_0.set_if_gain(self.if_gain, 0)

    def get_filter_transition_width(self):
        return self.filter_transition_width

    def set_filter_transition_width(self, filter_transition_width):
        self.filter_transition_width = filter_transition_width
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.filter_cutoff_freq, self.filter_transition_width, window.WIN_HAMMING, 6.76))

    def get_filter_cutoff_freq(self):
        return self.filter_cutoff_freq

    def set_filter_cutoff_freq(self, filter_cutoff_freq):
        self.filter_cutoff_freq = filter_cutoff_freq
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.filter_cutoff_freq, self.filter_transition_width, window.WIN_HAMMING, 6.76))

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.osmosdr_sink_0.set_center_freq(self.center_freq, 0)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(self.center_freq, self.samp_rate)

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
        self.analog_noise_source_x_0.set_amplitude(self.amplitude)




def main(top_block_cls=noise_tx_gr3_10, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
