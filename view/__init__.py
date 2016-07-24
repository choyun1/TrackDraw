#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The view is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QHBoxLayout,  QVBoxLayout, QGridLayout,
                             QMenu,        QPushButton, QDesktopWidget,
                             QLabel,       QSlider,     QCheckBox,
                             QComboBox)


class View(QApplication):
    def __init__(self, *arg, **kwarg):
        QApplication.__init__(self, *arg, **kwarg)
        self.appWindow = AppMainWindow()


class AppMainWindow(QMainWindow):
    """
    The left widget contains all representations of the sound.
    The right widget contains all buttons.
    """
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("TrackDraw")

        # Center window when initializing
        screen_width  = QDesktopWidget().availableGeometry().size().width()
        screen_height = QDesktopWidget().availableGeometry().size().height()
        screen_center = QDesktopWidget().availableGeometry().center()
#        self.resize(0.6*screen_width, 0.8*screen_height)
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_center)
        self.move(window_geometry.topLeft())

        # Menu bar setup
        self.file_menu = QMenu('&File', self)
        self.help_menu = QMenu('&Help', self)
        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.help_menu)

        # Main window widget
        self.main_widget = QWidget(self)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # Break the main widget into left and right
        main_layout = QHBoxLayout(self.main_widget)
        sound_widget = QWidget(self.main_widget)
        buttn_widget = QWidget(self.main_widget)
        main_layout.addWidget(sound_widget)
        main_layout.addWidget(buttn_widget)

        # Left widget is for displaying sound info
        sound_layout = QGridLayout(sound_widget)
        self.wave_cv = WaveCanvas(sound_widget, width=8, height=1)
        self.stft_cv = STFTCanvas(sound_widget, width=1, height=5)
        self.spec_cv = SpecCanvas(sound_widget, width=8, height=5)
        self.f0_cv = F0Canvas(sound_widget, width=8, height=1)
        sound_layout.addWidget(self.wave_cv, 0, 1)
        sound_layout.addWidget(self.stft_cv, 1, 0)
        sound_layout.addWidget(self.spec_cv, 1, 1)
        sound_layout.addWidget(self.f0_cv, 2, 1)

        # Right widget is for buttons and sliders
        buttn_layout = QVBoxLayout(buttn_widget)
        
        # Define buttons
        self.plot_loaded_but = QPushButton("Plot Input")
        self.synth_but = QPushButton("Synthesize Waveform")
        self.plot_synth_but = QPushButton("Plot Synth")
        self.play_loaded_but = QPushButton("Play Input Waveform")
        self.play_synth_but = QPushButton("Play Synth Waveform")
        self.default_but = QPushButton("Restore Defaults")
        
        # Define sliders
        fft_length_label = QLabel("Spectrogram Window Length")
        self.fft_length_slider = QSlider(QtCore.Qt.Horizontal)
        self.fft_length_slider.setMinimum(64)
        self.fft_length_slider.setMaximum(512)
        self.fft_length_slider.setSingleStep(4)
        dur_label = QLabel("Duration")
        self.dur_slider = QSlider(QtCore.Qt.Horizontal)
        self.dur_slider.setMinimum(1)
        self.dur_slider.setMaximum(10)
        self.dur_slider.setSingleStep(1)
        self.bw1_slider = QSlider(QtCore.Qt.Horizontal)
        self.bw1_slider.setMinimum(50)
        self.bw1_slider.setMaximum(400)
        self.bw1_slider.setSingleStep(5)      
        self.bw2_slider = QSlider(QtCore.Qt.Horizontal)
        self.bw2_slider.setMinimum(50)
        self.bw2_slider.setMaximum(400)
        self.bw2_slider.setSingleStep(5)  
        self.bw3_slider = QSlider(QtCore.Qt.Horizontal)
        self.bw3_slider.setMinimum(50)
        self.bw3_slider.setMaximum(400)
        self.bw3_slider.setSingleStep(5)   
        self.bw4_slider = QSlider(QtCore.Qt.Horizontal)
        self.bw4_slider.setMinimum(50)
        self.bw4_slider.setMaximum(400)
        self.bw4_slider.setSingleStep(5)  
        self.bw5_slider = QSlider(QtCore.Qt.Horizontal)
        self.bw5_slider.setMinimum(50)
        self.bw5_slider.setMaximum(400)
        self.bw5_slider.setSingleStep(5)   
        
        # Define comboboxes
        synth_dropdown_label = QLabel("Synthesis Type")
        self.synth_dropdown = QComboBox()
        self.synth_dropdown.addItem("Klatt 1980")
        self.synth_dropdown.addItem("Sine Wave")
        
        # Define checkboxes
        self.stft_check = QCheckBox("STFT Display (on/off)")
        self.voicing_check = QCheckBox("Voicing (on/off)")
        
        # Define organizational labels
        input_label = QLabel("Input")
        input_label.setAlignment(QtCore.Qt.AlignCenter)
        synth_label = QLabel("Synth")
        synth_label.setAlignment(QtCore.Qt.AlignCenter)
        plot_label = QLabel("Plot Settings")
        plot_label.setAlignment(QtCore.Qt.AlignCenter)
        parms_label = QLabel("Synthesis Settings")
        parms_label.setAlignment(QtCore.Qt.AlignCenter)        
        
        # Arrange buttons/sliders/labels
        buttn_layout.addStretch(1.0)
        buttn_layout.addWidget(self.default_but)
        buttn_layout.addWidget(input_label)
        buttn_layout.addWidget(self.plot_loaded_but)
        buttn_layout.addWidget(self.play_loaded_but)
        buttn_layout.addWidget(synth_label)
        buttn_layout.addWidget(self.synth_but)
        buttn_layout.addWidget(self.plot_synth_but)
        buttn_layout.addWidget(self.play_synth_but)
        buttn_layout.addSpacing(50)    
        buttn_layout.addWidget(plot_label)
        buttn_layout.addWidget(self.stft_check)
        buttn_layout.addWidget(fft_length_label)
        buttn_layout.addWidget(self.fft_length_slider)
        buttn_layout.addSpacing(25)        
        buttn_layout.addWidget(parms_label)
        buttn_layout.addWidget(synth_dropdown_label)
        buttn_layout.addWidget(self.synth_dropdown)
        buttn_layout.addWidget(self.voicing_check)
        buttn_layout.addWidget(dur_label)
        buttn_layout.addWidget(self.dur_slider)
        buttn_layout.addStretch(1.0)
        
        # Set sliders to defaults
        self.setDefaults()

        # Status bar
        self.statusBar().showMessage("Welcome to TrackDraw!")
        
    def setDefaults(self):
        self.fft_length_slider.setValue(256)
        self.dur_slider.setValue(2)
        self.voicing_check.setChecked(True)


class WaveCanvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent, width, height):
        self.fig = Figure(figsize=(width, height))
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)

class F0Canvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent, width, height):
        self.fig = Figure(figsize=(width, height))
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.f0_track = None
        self.background = None     
        
    def start(self, f0_track):
        self.ax.clear()
        self.ax.set_xlim(0,39)
        self.ax.set_ylim(90,150)     
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        self.f0_track = self.ax.plot(f0_track.points, color = "blue", marker="o")
        self.ax.set_xlim(0,39)
        self.ax.set_ylim(90,150) 
        
    def mouse(self, event):
        x_loc, y_loc = self.ax.transData.inverted().transform((event.x, event.y))
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        if xmin < x_loc < xmax and ymin < y_loc < ymax:
            return(x_loc, y_loc)
    
    def update_track(self, new_track):
        self.fig.canvas.restore_region(self.background)
        self.f0_track[0].set_ydata(new_track)
        self.ax.draw_artist(self.f0_track[0])
        self.fig.canvas.blit(self.ax.clipbox)

class STFTCanvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=1, height=4):
        self.fig = Figure(figsize=(width, height))
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.stft = None
        self.background = None
        
    def start(self):
        self.ax.clear()
        self.ax.set_xlim(-20, 40)
        self.ax.set_ylim(2, 128)
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        self.stft, = self.ax.plot(np.linspace(-20, -20, 128), np.arange(0, 128, 1))
        self.ax.set_xlim(-20, 40)
        self.ax.set_ylim(2, 128)
        
    def update_stft(self, new_stft):
        self.fig.canvas.restore_region(self.background)
        try:
            self.stft.set_xdata(new_stft)
            self.ax.draw_artist(self.stft)
        except (RuntimeError, ValueError):
            pass
        self.fig.canvas.blit(self.ax.clipbox)
        
class SpecCanvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4):
        self.fig = Figure(figsize=(width, height))
        self.ax = self.fig.add_subplot(111)
        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.tracks = []
        self.background = None
        self.n_form = 0
        
    def start(self, tracks, n_form):
        self.ax.clear()
        self.n_form = n_form
        self.ax.set_xlim(0,39)
        self.ax.set_ylim(0,5000)
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        for i in range(self.n_form):
            self.tracks.append(self.ax.plot(tracks[i].points, color = "blue", marker="o"))
        
    def mouse(self, event):
        x_loc, y_loc = self.ax.transData.inverted().transform((event.x, event.y))
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        if xmin < x_loc < xmax and ymin < y_loc < ymax:
            return(x_loc, y_loc)
            
    def update_track(self, new_track=0, trackNo=0, redraw=0):
        if redraw == 0:
            self.fig.canvas.restore_region(self.background)
            self.tracks[trackNo][0].set_ydata(new_track)
            for i in range(len(self.tracks)):
                self.ax.draw_artist(self.tracks[i][0])
            self.fig.canvas.blit(self.ax.clipbox)
        else:
            self.fig.canvas.restore_region(self.background)
            for i in range(len(self.tracks)):
                self.ax.draw_artist(self.tracks[i][0])
            self.fig.canvas.blit(self.ax.clipbox)
        
    def plot_specgram(self, waveform, fs, window_len, tracks):
        self.ax.clear()
        self.tracks = []
        self.ax.specgram(waveform, NFFT=window_len, Fs=fs,
                         noverlap=window_len*0.75, cmap = plt.cm.gist_heat)
        xmin, xmax = self.ax.get_xlim()
        self.fig.canvas.draw()
        self.ax.set_xlim(0,39)
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        for i in range(self.n_form):
            self.tracks.append(self.ax.plot(tracks[i].points, color = "blue", marker="o"))
        self.update_track(redraw=1)
        return(xmin, xmax)
        
