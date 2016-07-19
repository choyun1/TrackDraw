#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: daniel r guest
temporary sine wave synthesis algorithm for 07/19 lab meeting demo
"""

def sinemake(input_formants, input_envelope, dur, Fs):
    # Import
    import numpy as np
    from scipy.interpolate import interp1d
    import matplotlib.pyplot as plt
    
    # Create necessary variables
    dt = 1/Fs
    n_formants = input_formants.shape[1]
    n_samples = round(dur*Fs)
    t = np.arange(0, dur, dt)
    
    # Interpolate "formants"
    interpolated_formants = np.zeros([n_samples, n_formants])
    for i in range(n_formants):
        seq = np.arange(0, input_formants.shape[0])
        seq_new = np.linspace(0, input_formants.shape[0]-1, n_samples)
        temp = interp1d(seq, input_formants[:,i])(seq_new)
        interpolated_formants[:,i] = temp

    # Interpolate envelope
    seq = np.arange(0, input_envelope.shape[0])
    seq_new = np.linspace(0, input_envelope.shape[0]-1, n_samples)
    interpolated_envelope = interp1d(seq, input_envelope)(seq_new)
    
    # Generate sine waves
    waves = []
    for i in range(n_formants):
        phase = np.cumsum(2*np.pi*interpolated_formants[:,i]/Fs)
        waves.append(np.cos(phase))
    output_wave = np.zeros([n_samples])
    output_wave = waves[0]+waves[1]+waves[2]+waves[3]+waves[4]
    output_wave = output_wave*interpolated_envelope
    return(output_wave)
        