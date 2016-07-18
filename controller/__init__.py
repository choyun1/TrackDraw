#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The controller is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/17/2016
version: 0.1.0
"""

import tkinter.filedialog as fdialog
from scipy import signal
from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import time

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

                model.loaded_sound.waveform = new_x
                model.loaded_sound.fs = new_fs

        def quit_callback(event):
            self.view.destroy()

        def spec_check_callback(event):
            # Just a test function to display messages
            print(self.model.loaded_sound.nsamples)
            
        def plot_loaded_callback(event):
            self.plot_tag = "loaded"
            self.plot()
            
        def plot_synth_callback(event):
            self.plot_tag = "synth"
            self.plot()
            
        def fft_length_callback(event):
            self.model.current_parms.window_len = self.view.fft_length_scale.get()
            self.plot()
            
        def play_loaded_callback(event):
            self.play_tag = "loaded"
            self.play()
            
        def play_synth_callback(event):
            self.play_tag = "synth"
            self.play()

        # Bind the button callbacks
        self.view.load_but.bind("<Button-1>", load_callback)
        self.view.quit_but.bind("<Button-1>", quit_callback)
        self.view.plot_loaded_but.bind("<Button-1>", plot_loaded_callback)
        self.view.fft_length_scale.bind("<B1-Motion>", fft_length_callback)
        self.view.play_loaded_but.bind("<Button-1>", play_loaded_callback)
        self.view.play_synth_but.bind("<Button-1>", play_synth_callback)
        
        # Bind the canvas callbacks
        self.view.main.canvas.mpl_connect('button_press_event', self.click)
        self.view.main.canvas.mpl_connect('motion_notify_event', self.drag)
        
        # Send default tracks to view, create useful attributes for track/plot
        self.view.main.startTracks(self.model.tracks)
        self.locked_track = 0
        self.x_low = 0
        self.x_high = 40
        self.plot_tag = None
        self.play_tag = None
            
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
            trackNo, updated_track = self.model.updateTrackClick(x_loc, y_loc,
                                                                 self.x_high)
            self.view.main.updateTrack(trackNo, updated_track)
            self.view.main.redrawTracks()
            self.locked_track = trackNo
        except TypeError:
            return
    
    def drag(self, event):
        """
        Similar functionality to click() above, except chooses the
        locked_track-th track instead of the closest to the mouse, and does not
        update the locked_track. 
        """
        if event.button == 1:
            try:
                x_loc, y_loc = self.view.main.mouse(event)
                trackNo, updated_track = self.model.updateTrackDrag(x_loc,
                                                                    y_loc,
                                                                    self.x_high,
                                                                    self.locked_track)
                self.view.main.updateTrack(trackNo, updated_track)
                self.view.main.redrawTracks()
            except TypeError:
                return       
        else:
            return
            
    def plot(self):
        if self.plot_tag == "loaded":
            waveform = self.model.loaded_sound.waveform
            fs = self.model.loaded_sound.fs
            nsamples = self.model.loaded_sound.nsamples
        elif self.plot_tag == "synth":
            waveform = self.model.synth_sound.waveform
            fs = self.model.synth_sound.fs
            nsamples = self.model.synth_sound.nsamples
        window_len = self.model.current_parms.window_len
        self.view.main.ax.clear()
        self.x_high = nsamples/fs
        self.view.main.x_high = self.x_high
        self.view.main.ax.specgram(waveform, NFFT=window_len,
                                   Fs=fs, noverlap=window_len*0.75, 
                                   cmap = plt.cm.gist_heat)
        self.view.main.rescaleTracks()    
        
    def play(self):
        self.normalize()
        if self.play_tag == "loaded":
            waveform = self.model.loaded_sound.waveform
            fs = self.model.loaded_sound.fs
            nsamples = self.model.loaded_sound.nsamples
        elif self.play_tag == "synth":
            waveform = self.model.synth_sound.waveform
            fs = self.model.synth_sound.fs
            nsamples = self.model.synth_sound.nsamples
        sd.play(waveform, fs)
        time.sleep((1/fs)*nsamples)
        
    def normalize(self):
        self.model.loaded_sound.waveform = (self.model.loaded_sound.waveform/
                                            np.max(np.abs(self.model.loaded_sound.waveform)))
#        self.model.synth_sound.waveform = (self.model.synth_sound.waveform/
#                                           np.max(np.abs(self.model.synth_sound.waveform)))

    def run(self):
        self.view.mainloop()

