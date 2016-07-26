#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
authors: A. Y. Cho and Daniel R Guest
date:    07/17/2016
version: 0.1.0
"""


import numpy as np


class Sound:
    """
    The Sound class now automatically updates n_samples whenever the waveform
    attribute changes. n_samples should never be changed individually.
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
    def __init__(self, F0=100,
                       FF=[800, 1600, 2400, 3200, 4000],
                       BW=np.array([50, 100, 100, 200, 250]),
                       resample_fs=10000,
                       synth_fs=10000,
                       track_npoints=40,
                       voicing="Voicing",
                       window_len=256,
                       dur=1,
                       inc_ms=5,
                       envelope=np.array([0, 1, 1, 1, 0]),
                       radiation=0,
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


DEFAULT_PARAMS = Parameters()
CURRENT_PARAMS = Parameters()
LOADED_SOUND = Sound(np.zeros([1, 10000]), DEFAULT_PARAMS.resample_fs, 1)
SYNTH_SOUND  = Sound(np.zeros([1, 10000]), DEFAULT_PARAMS.resample_fs, 1)

npoints = DEFAULT_PARAMS.track_npoints
F0 = DEFAULT_PARAMS.F0
allFF = DEFAULT_PARAMS.FF
F0_TRACK =  Track(F0*np.ones([1, npoints]))
TRACKS   = [Track(FF*np.ones([1, npoints])) for FF in allFF]

