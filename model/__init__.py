#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The model is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/17/2016
version: 0.1.0
"""

import numpy as np


class Model:
    """
    Contains:
        default_parms - Default parameters
        current_parms - Current parameters; expect this to change at runtime
        tracks - Container for the Track class instances
        loaded_sound - Sound object for holding the loaded sound file
        synth_sound  - Sound object for holding the synthesized sound
    """
    def __init__(self):
        self.default_parms = Parameters()
        self.current_parms = Parameters()

        # Create the default formant tracks
        default_FFs = self.default_parms.FF
        default_F0 = self.default_parms.F0
        track_npoints = self.default_parms.track_npoints
        ones = np.ones(track_npoints)
        self.tracks = [Track(formant*ones) for formant in default_FFs]
        self.f0_track = Track(default_F0*ones)

        # Define the two sounds: load and synth
        resample_fs = self.default_parms.resample_fs
        synth_fs = self.default_parms.synth_fs
        self.loaded_sound = Sound(np.array([]), resample_fs, 1)
        self.synth_sound  = Sound(np.array([]), synth_fs, 1)

    def getTracks(self):
        output = np.zeros([40, len(self.tracks)])
        for i in range(len(self.tracks)):
            output[0:40, i] = self.tracks[i].points
        return(output)
        
    def getF0Track(self):
        output = np.zeros([40])
        output[:] = self.f0_track.points
        return(output)

class Sound:
    """
    The Sound class now automatically updates n_samples whenever the waveform
    attribute changes. n_samples should never be changed individually.
    - Cho, 07/16
    """
    def __init__(self, waveform, fs, nchannels):
        self.waveform = waveform
        self.fs = fs
        self.nchannels = nchannels

    @property
    def waveform(self):
        return self._waveform
    # Automatically update n_samples and t whenever waveform changes
    @waveform.setter
    def waveform(self, val):
        self._waveform = val
        self.nsamples = len(self._waveform)


class Track:
    """
    Helpful docstring
    """
    def __init__(self, points):
        self.points = points

        
class Parameters:
    """
    Helpful docstring
    """
    def __init__(self, F0=100,\
                       FF=[800, 1600, 2400, 3200, 4000],\
                       BW=np.array([[50, 100, 100, 200, 250], [50, 100, 100, 200, 250]]),\
                       resample_fs=10000,\
                       synth_fs=10000,\
                       track_npoints=40,\
                       voicing=1,\
                       window_len=256,\
                       dur=1,\
                       inc_ms=5,\
                       envelope=np.array([0, 1, 1, 1, 0]),\
                       radiation=0,\
                       synthesis_type="Klatt 1980"):
        self.F0 = F0
        self.FF = FF
        self.BW = BW
        self.resample_fs = resample_fs
        self.synth_fs = synth_fs
        self.track_npoints = track_npoints
        self.voicing = voicing
        self.window_len = window_len
        self.dur = dur
        self.inc_ms = inc_ms
        self.envelope = envelope
        self.radiation = radiation
        self.synthesis_type = synthesis_type

