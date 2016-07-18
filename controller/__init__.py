#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The controller is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/17/2016
version: 0.1.0
"""

import time
import numpy as np
from scipy import signal
from scipy.io import wavfile
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class Controller:
    """
    Helpful docstring
    """
    def __init__(self, model, view):
        self.model = model
        self.view  = view
        self.appWindow = view.appWindow

        # Callbacks for menu items
        def file_menu_open():
            fname = QFileDialog.getOpenFileName(self.appWindow, "Open file")
            if fname[0]:
                old_fs, x = wavfile.read(fname[0])
                new_fs = model.default_parms.resample_fs
                new_n  = round(new_fs/old_fs*len(x))
                new_x  = signal.resample(x, new_n)
                self.model.loaded_sound.waveform = new_x
                self.model.loaded_sound.fs = new_fs
                self.appWindow.wave_cv.ax.plot(new_x)
        def file_menu_quit():
            self.appWindow.close()
        def help_menu_about():
            QMessageBox.about(self.appWindow, "About",\
"""
<b>TrackDraw v0.1.0</b>
Copyright (c) 2016 Adrian Y. Cho and Daniel R Guest
""")

        # Bind the menu callbacks
        self.appWindow.file_menu.addAction("&Open file", file_menu_open,\
                                           QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.appWindow.file_menu.addAction('&Quit', file_menu_quit,\
                                           QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.appWindow.help_menu.addAction('&About', help_menu_about)

        # Bind the spectrogram canvas callbacks
        self.appWindow.spec_cv.mpl_connect('button_press_event', self.click)
        self.appWindow.spec_cv.mpl_connect('motion_notify_event', self.drag)
        
        # Send default tracks to view
        self.appWindow.spec_cv.startTracks(self.model.tracks)
        self.locked_track = 0
            
    def click(self, event):
        """
        When an area in the main canvas is clicked, mouse() returns the click's
        location in terms of the data dimensions if the click was within the
        plot region. This location is passed to model by updateTrackClick(), 
        which finds the nearest track/vertex to the click and updates the track
        data accordingly. Data from the updated track is then passed to the view,
        which updates the appropriate track in the view and redraws everything.
        At the end, the selected track is stored in locked_track, which drag()
        uses to lock to a particular track for a given click-drag movement.
        """
        x_loc, y_loc = self.appWindow.spec_cv.mouse(event)
        trackNo, updated_track = self.model.updateTrackClick(x_loc, y_loc)
        self.appWindow.spec_cv.updateTrack(trackNo, updated_track)
        self.appWindow.spec_cv.updateTracks()
        self.locked_track = trackNo
    
    def drag(self, event):
        """
        Similar functionality to click() above, except chooses the
        locked_track-th track instead of the closest to the mouse, and does not
        update the locked_track. 
        """
        if event.button:
            try:
                x_loc, y_loc = self.appWindow.spec_cv.mouse(event)
                trackNo, updated_track =\
                    self.model.updateTrackDrag(x_loc, y_loc, self.locked_track)
                self.appWindow.spec_cv.updateTrack(trackNo, updated_track)
                self.appWindow.spec_cv.updateTracks()
            except TypeError:
                pass

    def run(self):
        self.appWindow.show()
        self.view.exec_()

