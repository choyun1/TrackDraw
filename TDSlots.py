#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sounddevice as sd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import signal
from scipy.io import wavfile


@pyqtSlot()
def audioOpen(*arg, parent=None, **kwarg):
    fname = QFileDialog.getOpenFileName(parent, "Open a wave file", "",
            "Wav files (*.wav)")
    if fname[0]:
        old_fs, x = wavfile.read(fname[0])
        #new_fs = model.default_parms.resample_fs
        #new_n  = round(new_fs/old_fs*len(x))
        #new_x  = signal.resample(x, new_n)
        #self.model.loaded_sound.waveform = new_x
        #self.model.loaded_sound.fs = new_fs
        #self.appWindow.wave_cv.ax.plot(new_x)


@pyqtSlot()
def audioSave(*arg, parent=None, **kwarg):
    fname = QFileDialog.getSaveFileName(parent, "Save the synthesized sound",
            "", "Wav files (*.wav)")
    print(fname)


@pyqtSlot()
def helpAbout(*arg, parent=None, **kwarg):
    aboutText = """<b>TrackDraw v0.2.0</b>\nCopyright (c) 2016"""
    QMessageBox.about(parent, "About", aboutText)


@pyqtSlot()
def clearPlots(*arg, parent=None, **kwarg):
    print(0)


@pyqtSlot()
def applyAnalysis(*arg, parent=None, **kwarg):
    print(0)


@pyqtSlot()
def synthesize(*arg, parent=None, **kwarg):
    print(0)

