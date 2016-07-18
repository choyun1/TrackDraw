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
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QHBoxLayout,  QVBoxLayout, QGridLayout,
                             QMenu,        QPushButton, QDesktopWidget)


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
        self.resize(0.6*screen_width, 0.8*screen_height)
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
        self.wave_canv = WaveCanvas(sound_widget, width=8, height=1)
        self.stft_canv = STFTCanvas(sound_widget, width=1, height=6)
        self.spec_canv = SpecCanvas(sound_widget, width=8, height=6)
        sound_layout.addWidget(self.wave_canv, 0, 1)
        sound_layout.addWidget(self.stft_canv, 1, 0)
        sound_layout.addWidget(self.spec_canv, 1, 1)

        # Right widget is for buttons
        buttn_names  = ['test1', 'test2', 'test3']
        buttn_layout = QVBoxLayout(buttn_widget)
        for name in buttn_names:
            buttn = QPushButton(name)
            buttn_layout.addWidget(buttn)

        # Status bar
        self.statusBar().showMessage("Welcome to TrackDraw!")


class WaveCanvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent, *arg, **kwarg):
        width  = kwarg["width"]
        height = kwarg["height"]
        self.fig = Figure(figsize=(width, height))
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)


class STFTCanvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent, *arg, **kwarg):
        width  = kwarg["width"]
        height = kwarg["height"]
        self.fig = Figure(figsize=(width, height))
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)

        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2*np.pi*t)
        self.ax.plot(s, t)

        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)


class SpecCanvas(FigCanvas):
    """Ultimately, this is a QWidget (as well as a FigCanvasAgg, etc.)."""
    def __init__(self, parent, *arg, **kwarg):
        width  = kwarg["width"]
        height = kwarg["height"]
        self.fig = Figure(figsize=(width, height))
        self.ax  = self.fig.add_subplot(111)
        FigCanvas.__init__(self, self.fig)
        self.setParent(parent)

        self.tracks = []
        self.locked_track = 0
        self.inv = self.ax.transData.inverted()
        self.background = None

        # Testing background
        t = np.linspace(0, 40, 1000)
        x = 2500*np.sin(t) + 2500
        self.ax.plot(t, x)


    def mouse(self, event):
        x_loc, y_loc = self.inv.transform((event.x, event.y))
        if 0 < x_loc < 1 and 0 < y_loc < 1:
            return 40*x_loc, 5000*y_loc

    def startTracks(self, tracks):
        """
        Draws canvas without tracks and grabs the background. Then plots
        tracks, sets limits, and renders the plot again.
        """
        #self.background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.tracks = [self.ax.plot(track.points,\
                                    marker="o",\
                                    markersize=4,\
                                    markeredgewidth=0.0)\
                       for track in tracks]
        self.ax.set_xlim(0, 39)
        self.ax.set_ylim(0, 5000)
    
    def updateTrack(self, trackNo, updated_track):
        self.tracks[trackNo][0].set_ydata(updated_track)
   
    def updateTracks(self):
        """
        Restores empty background (doesn't have to redraw everything and waste
        time), then redraws only lines.
        """
        #self.fig.canvas.restore_region(self.background)
        for i in range(len(self.tracks)):
            self.ax.draw_artist(self.tracks[i][0])
        self.draw()

