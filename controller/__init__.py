#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The controller is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/17/2016
version: 0.1.0
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sounddevice as sd
import controller.synth as synth
from scipy import signal
from scipy.io import wavfile
import time
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

        # Callbacks for interface items
        def plot_loaded_callback():
            self.plot_tag = "loaded"
            self.plot()
            
        def plot_synth_callback():
            self.plot_tag = "synth"
            self.plot()
            
        def play_loaded_callback():
            self.play_tag = "loaded"
            self.play()
            
        def play_synth_callback():
            self.play_tag = "synth"
            self.play()
            
        def default_callback():
            self.appWindow.setDefaults()
            update_parms_callback()
            
        def update_parms_callback():
            self.model.current_parms.window_len = self.appWindow.fft_length_slider.value()
            self.model.current_parms.dur = 0.5*self.appWindow.dur_slider.value()
            if self.appWindow.voicing_check.checkState() == 0:
                self.model.current_parms.voicing = 0
            elif self.appWindow.voicing_check.checkState() == 2:
                self.model.current_parms.voicing = 1
            self.model.current_parms.synthesis_type = self.appWindow.synth_dropdown.currentText()
            self.plot()
            
        # Bind the spectrogram canvas callbacks
        self.appWindow.spec_cv.mpl_connect('button_press_event', self.click)
        self.appWindow.spec_cv.mpl_connect('motion_notify_event', self.drag)
        self.appWindow.spec_cv.mpl_connect('motion_notify_event', self.stft)
        self.appWindow.f0_cv.mpl_connect('button_press_event', self.f0_mouse)
        self.appWindow.f0_cv.mpl_connect('motion_notify_event', self.f0_mouse)
        
        # Bind the button callbacks
        self.appWindow.plot_loaded_but.clicked.connect(plot_loaded_callback)
        self.appWindow.synth_but.clicked.connect(self.synth)
        self.appWindow.plot_synth_but.clicked.connect(plot_synth_callback)
        self.appWindow.play_loaded_but.clicked.connect(play_loaded_callback)
        self.appWindow.play_synth_but.clicked.connect(play_synth_callback)
        self.appWindow.default_but.clicked.connect(default_callback)
            
        # Bind the slider/checkbox/combobox callbacks
        self.appWindow.fft_length_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.voicing_check.stateChanged.connect(update_parms_callback)
        self.appWindow.dur_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.synth_dropdown.currentIndexChanged.connect(update_parms_callback)
        
        # Create tracker attributes and grab current parms
        self.locked_track = 0
        self.plot_tag = "loaded"
        self.play_tag = "loaded"
        update_parms_callback()
            
    def click(self, event):
        """
        Explain!
        """
        try:
            x_loc, y_loc = self.appWindow.spec_cv.mouse(event)
            dist_to_x_pts = np.abs(np.linspace(0,39,40) - x_loc)
            nearest_x_idx = dist_to_x_pts.argmin()
            y_coords_at_nearest_x = np.array(\
                    [track.points[nearest_x_idx] for track in self.model.tracks])
            dist_to_y_pts = np.abs(y_coords_at_nearest_x - y_loc)
            trackNo = dist_to_y_pts.argmin()
            self.model.tracks[trackNo].points[nearest_x_idx] = y_loc
            self.appWindow.spec_cv.update_track(self.model.tracks[trackNo].points, trackNo)
            self.locked_track = trackNo
        except TypeError:
            pass
    
    def drag(self, event):
        """
        Explain!
        """
        if event.button:
            try:
                x_loc, y_loc = self.appWindow.spec_cv.mouse(event)
                dist_to_x_pts = np.abs(np.linspace(0,39,40) - x_loc)
                nearest_x_idx = dist_to_x_pts.argmin()
                self.model.tracks[self.locked_track].points[nearest_x_idx] = y_loc
                self.appWindow.spec_cv.update_track(self.model.tracks[self.locked_track].points, self.locked_track)
            except TypeError:
                pass
            
    def f0_mouse(self, event):
        if event.button:
            try:
                x_loc, y_loc = self.appWindow.f0_cv.mouse(event)
                dist_to_x_pts = np.abs(np.linspace(0,39,40) - x_loc)
                nearest_x_idx = dist_to_x_pts.argmin()
                self.model.f0_track.points[nearest_x_idx] = y_loc
                self.appWindow.f0_cv.update_track(self.model.f0_track.points)
            except TypeError:
                pass
            
    def stft(self, event):
        if self.appWindow.stft_check.checkState() == 2:
            try:
                x_loc, y_loc = self.appWindow.spec_cv.mouse(event)
                if self.plot_tag == "loaded":
                    waveform = self.model.loaded_sound.waveform
                    fs = self.model.loaded_sound.fs
                    nsamples = self.model.loaded_sound.nsamples
                elif self.plot_tag == "synth": 
                    waveform = self.model.synth_sound.waveform
                    fs = self.model.synth_sound.fs
                    nsamples = self.model.synth_sound.nsamples
                if len(waveform) == 0:
                    return
                nearest_sample = round(x_loc*nsamples/39)
                waveform = waveform/np.max(np.abs(waveform))
                try:
                    stspec = np.fft.rfft(waveform[nearest_sample-128:nearest_sample+128])
                    stspec = 20*np.log10(stspec)
                    self.appWindow.stft_cv.update_stft(stspec[0:128])
                except ValueError:
                    pass
            except TypeError:
                pass
            
    def synth(self):
        self.model.current_parms.FF = self.model.getTracks()
        self.model.current_parms.F0 = self.model.getF0Track()
        if self.model.current_parms.synthesis_type == "Klatt 1980":
            self.model.synth_sound.waveform =\
                    synth.klatt_experimental.klatt_make(self.model.current_parms)
        elif self.model.current_parms.synthesis_type == "Sine Wave":
            self.model.synth_sound.waveform = (synth.sine.sinemake(
                                               self.model.current_parms.FF,
                                               self.model.current_parms.envelope,
                                               self.model.current_parms.dur,
                                               self.model.current_parms.synth_fs
                                               ))

    def plot(self):
        if self.plot_tag == "loaded":
            waveform = self.model.loaded_sound.waveform
            fs = self.model.loaded_sound.fs
        elif self.plot_tag == "synth":
            waveform = self.model.synth_sound.waveform
            fs = self.model.synth_sound.fs
        if len(waveform) == 0:
            return
        window_len = self.model.current_parms.window_len
        xmin, xmax = self.appWindow.spec_cv.plot_specgram(waveform, fs,
                                                 window_len, self.model.tracks)
        self.appWindow.wave_cv.ax.plot(waveform)
        self.appWindow.wave_cv.ax.set_xlim(0, len(waveform))
        self.appWindow.wave_cv.fig.canvas.draw()
        
    def play(self):
        if self.play_tag == "loaded":
            waveform = self.model.loaded_sound.waveform
            fs = self.model.loaded_sound.fs
            nsamples = self.model.loaded_sound.nsamples
        elif self.play_tag == "synth":
            waveform = self.model.synth_sound.waveform
            fs = self.model.synth_sound.fs
            nsamples = self.model.synth_sound.nsamples
        if len(waveform) == 0:
            return
        waveform = waveform/np.max(np.abs(waveform))*0.9
        sd.play(waveform, fs)
        time.sleep(nsamples/fs)
            
    def run(self):
        self.appWindow.show()
        self.appWindow.stft_cv.start()
        self.appWindow.f0_cv.start(self.model.f0_track)
        self.appWindow.spec_cv.start(self.model.tracks, n_form=5)
        self.view.exec_()

