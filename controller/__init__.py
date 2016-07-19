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
import sounddevice as sd
import controller.synth as synth
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
        self.appWindow.spec_cv.mpl_connect('motion_notify_event', self.stft)
        
        # Callbacks for buttons
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
        
        # Bind the button callbacks
        self.appWindow.plot_loaded_but.clicked.connect(plot_loaded_callback)
        self.appWindow.synth_but.clicked.connect(self.synth)
        self.appWindow.plot_synth_but.clicked.connect(plot_synth_callback)
        self.appWindow.play_loaded_but.clicked.connect(play_loaded_callback)
        self.appWindow.play_synth_but.clicked.connect(play_synth_callback)
        self.appWindow.default_but.clicked.connect(default_callback)
        
        # Callbacks for sliders/checkboxes
            
        def update_parms_callback():
            self.model.current_parms.window_len = self.appWindow.fft_length_slider.value()
            self.model.current_parms.F0 = self.appWindow.f0_slider.value()
            self.model.current_parms.dur = 0.5*self.appWindow.dur_slider.value()
            if self.appWindow.voicing_check.checkState() == 0:
                self.model.current_parms.voicing = 0
            elif self.appWindow.voicing_check.checkState() == 2:
                self.model.current_parms.voicing = 1
            if self.appWindow.radiation_check.checkState() == 0:
                self.model.current_parms.radiation = 0
            elif self.appWindow.radiation_check.checkState() == 2:
                self.model.current_parms.radiation = 1
            self.model.current_parms.BW[0:1,0] = self.appWindow.bw1_slider.value()
            self.model.current_parms.BW[0:1,1] = self.appWindow.bw2_slider.value()
            self.model.current_parms.BW[0:1,2] = self.appWindow.bw3_slider.value()
            self.model.current_parms.BW[0:1,3] = self.appWindow.bw4_slider.value()
            self.model.current_parms.BW[0:1,4] = self.appWindow.bw5_slider.value()
            self.model.current_parms.synthesis_type = self.appWindow.synth_dropdown.currentText()
            self.plot()
            
        # Bind the slider/checkbox/combobox callbacks
        self.appWindow.fft_length_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.voicing_check.stateChanged.connect(update_parms_callback)
        self.appWindow.f0_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.dur_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.radiation_check.stateChanged.connect(update_parms_callback)
        self.appWindow.bw1_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.bw2_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.bw3_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.bw4_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.bw5_slider.sliderReleased.connect(update_parms_callback)
        self.appWindow.synth_dropdown.currentIndexChanged.connect(update_parms_callback)
        
        # Send default tracks to view, create useful plotting attributes
        self.appWindow.spec_cv.startTracks(self.model.tracks)
        self.locked_track = 0
        self.x_high = 39
        self.plot_tag = "loaded"
        self.play_tag = "loaded"
        update_parms_callback()
            
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
        trackNo, updated_track = self.model.updateTrackClick(x_loc, y_loc,\
                                                             self.x_high)
        self.appWindow.spec_cv.updateTrack(trackNo, updated_track)
        self.appWindow.spec_cv.redrawTracks()
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
                    self.model.updateTrackDrag(x_loc, y_loc,\
                                               self.locked_track, self.x_high)
                self.appWindow.spec_cv.updateTrack(trackNo, updated_track)
                self.appWindow.spec_cv.redrawTracks()
            except TypeError:
                pass
            
    def stft(self, event):
        if self.appWindow.stft_check.checkState() == 2:
            try:
                x_loc, y_loc = self.appWindow.spec_cv.mouse(event)
                if self.plot_tag == "loaded":
                    waveform = self.model.loaded_sound.waveform
                    fs = self.model.loaded_sound.fs
                elif self.plot_tag == "synth": 
                    waveform = self.model.synth_sound.waveform
                    fs = self.model.synth_sound.fs
                if len(waveform) == 0:
                    return
                nearest_sample = round(x_loc*fs)
                waveform = waveform/np.max(np.abs(waveform))
                stspec = np.fft.rfft(waveform[nearest_sample-128:nearest_sample+128])
                stspec = 20*np.log10(stspec)
                self.appWindow.stft_cv.updateSTFT(stspec)
                self.appWindow.stft_cv.redrawSTFT()
            except TypeError:
                pass
            
    def synth(self):
        self.model.current_parms.FF = self.model.getTracks()
        if self.model.current_parms.synthesis_type == "Klatt 1980":
            self.model.synth_sound.waveform = (synth.klatt.klattmake(
                                       self.model.current_parms.FF,                      
                                       self.model.current_parms.BW,
                                       self.model.current_parms.envelope,
                                       self.model.current_parms.F0,
                                       self.model.current_parms.voicing,
                                       self.model.current_parms.inc_ms,
                                       self.model.current_parms.dur,
                                       self.model.current_parms.synth_fs,
                                       self.model.current_parms.radiation
                                       ))
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
            nsamples = self.model.loaded_sound.nsamples
        elif self.plot_tag == "synth":
            waveform = self.model.synth_sound.waveform
            fs = self.model.synth_sound.fs
            nsamples = self.model.synth_sound.nsamples
        if len(waveform) == 0:
            return
        window_len = self.model.current_parms.window_len
        
        self.appWindow.spec_cv.ax.clear()
        self.x_high = nsamples/fs
        self.appWindow.spec_cv.x_high = self.x_high
        self.appWindow.spec_cv.ax.specgram(waveform, NFFT=window_len,
                                           Fs=fs, noverlap=window_len*0.75, 
                                           cmap = plt.cm.gist_heat)
        self.appWindow.spec_cv.rescaleTracks()
        
        self.appWindow.wave_cv.ax.plot(waveform)
        self.appWindow.wave_cv.ax.set_xlim(0,len(waveform))
        self.appWindow.wave_cv.fig.canvas.draw()
        
    def play(self):
        if self.play_tag == "loaded":
            waveform = self.model.loaded_sound.waveform
            fs = self.model.loaded_sound.fs
        elif self.play_tag == "synth":
            waveform = self.model.synth_sound.waveform
            fs = self.model.synth_sound.fs
        if len(waveform) == 0:
            return
        waveform = waveform/np.max(np.abs(waveform))*0.9
        sd.play(waveform, fs)
            
    def run(self):
        self.appWindow.show()
        self.view.exec_()

