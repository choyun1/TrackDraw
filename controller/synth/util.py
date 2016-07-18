#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    name:    util.py
    author:  daniel r guest
    date:    07/12/2016
    version: 0.1.3
    purpose: provide various utility functions for TrackDraw 2016
"""

def specEnv(spectrum, f0, Fs):
    
    # Imports
    import numpy as np
    
    # Generate cepstrum
    cepstrum = np.fft.ifft(20*np.log10(abs(spectrum)))
    index = round(Fs/f0)
    index = index - 50
    print(index)
    for i in range(len(cepstrum)):
        if i == index:
            cepstrum[i] = cepstrum[i] * 0.5
        elif i > index:
            cepstrum[i] = 0
    envelope = np.fft.fft(cepstrum)
    return(envelope)
        