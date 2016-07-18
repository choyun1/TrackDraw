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
import tkinter.filedialog as fdialog
from scipy import signal
from scipy.io import wavfile


class Controller:
    """
    Helpful docstring
    """
    def __init__(self, model, view):
        self.model = model
        self.view  = view

        # Define callback functions for the buttons in the sidepanel
        def load_callback(event):
            file_opt = {}
            file_opt["defaultextension"] = ".wav"
            file_opt["filetypes"] = [("wave files", ".wav")]
            file_opt["title"] = "Load wav file"
            filename = fdialog.askopenfilename(**file_opt)
            if filename:
                old_fs, x = wavfile.read(filename)
                new_fs = model.default_parms.resample_fs
                new_n  = round(new_fs/old_fs*len(x))
                new_x  = signal.resample(x, new_n)

                self.model.loaded_sound.waveform = new_x
                self.model.loaded_sound.fs = new_fs
            return

        def clear_callback(event):
            self.model.loaded_sound.waveform = np.array([])
            self.model.loaded_sound.fs = self.model.default_parms.resample_fs

        def quit_callback(event):
            self.view.destroy()

        def spec_check_callback(event):
            # Just a test function to display messages
            pass

        # Bind the button callbacks
        self.view.load_but.bind("<Button-1>", load_callback)
        self.view.quit_but.bind("<Button-1>", quit_callback)
        self.view.clear_but.bind("<Button-1>", clear_callback)
        self.view.spec_check.bind("<Button-1>", spec_check_callback)
        
        # Bind the canvas callbacks
        self.view.main.canvas.mpl_connect('button_press_event', self.click)
        self.view.main.canvas.mpl_connect('motion_notify_event', self.drag)
        
        # Send default tracks to view
        self.view.main.startTracks(self.model.tracks)
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
        try:
            x_loc, y_loc = self.view.main.mouse(event)
            trackNo, updated_track = self.model.updateTrackClick(x_loc, y_loc)
            self.view.main.updateTrack(trackNo, updated_track)
            self.view.main.updateTracks()
            self.locked_track = trackNo
        except TypeError:
            pass
    
    def drag(self, event):
        """
        Similar functionality to click() above, except chooses the
        locked_track-th track instead of the closest to the mouse, and does not
        update the locked_track. 
        """
        if event.button:
            try:
                x_loc, y_loc = self.view.main.mouse(event)
                trackNo, updated_track =\
                    self.model.updateTrackDrag(x_loc, y_loc, self.locked_track)
                self.view.main.updateTrack(trackNo, updated_track)
                self.view.main.updateTracks()
            except TypeError:
                pass

    def run(self):
        self.view.mainloop()

