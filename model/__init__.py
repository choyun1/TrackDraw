#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The model is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import numpy as np


class Model:
    """
    Helpful docstring
    """
    def __init__(self):
        self.default_parms = Parameters()
        self.current_parms = Parameters()
        self.tracks = [Track() for i in range(self.default_parms.get_ntracks())]

    def get_curr_parms(self):
        return self.current_parms

    def set_curr_parms(self):
        # This is a stub
        self.current_parms = Parameters()


class Sound:
    """
    Helpful docstring
    """
    def __init__(self, waveform=np.array([]), fs=10000, n_channels=1):
        self.waveform = waveform
        self.n_samples = len(self.waveform)
        self.fs = fs
        self.n_channels = n_channels


class Track:
    """
    Helpful docstring
    """
    def __init__(self, points=np.array([])):
        self.points = points

    def get_track(self):
        return self.points

    def set_track(self, new_points):
        self.points = new_points


class Parameters:
    """
    Helpful docstring
    """
    def __init__(self, F0=100,\
                       FF=[800, 1600, 2400, 3200, 4000],\
                       BW=[20, 20, 20, 20, 20],\
                       voicing=0):
        self.F0 = F0
        self.FF = FF
        self.BW = BW
        self.n_tracks = len(self.FF)
        self.voicing = voicing

    def update(self, F0, FF, BW, voicing):
        self.F0 = F0
        self.FF = FF
        self.BW = BW
        self.n_tracks = len(self.FF)
        self.voicing = voicing

    def get_ntracks(self):
        return self.n_tracks


