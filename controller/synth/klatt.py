"""
    name:    klatt.py
    author:  daniel r guest
    date:    07/12/2016
    version: 0.1.3
    purpose: provide functions to perform vocal waveform synthesis ala Klatt 1980
"""

def klattresonate(x, param, Fs):
    
    # Define imports
    import math
    import numpy as np
    
    # Necessary variables
    dt = 1/Fs
    n_samples = x.size
    
    # Create y[t] (output waveform)
    y = np.zeros([n_samples])

    # Decompose parameter matrix
    frequency = param[:,0]
    bandwidth = param[:,1]

    # Calculate coefficients
    A = np.zeros([n_samples,1])
    B = np.zeros([n_samples,1])
    C = np.zeros([n_samples,1])
    for i in range(0,n_samples):
        C[i] = -math.exp(-2*math.pi*bandwidth[i]*dt)
        B[i] = (2*math.exp(-math.pi*bandwidth[i]*dt)
                *math.cos(2*math.pi*frequency[i]*dt))
        A[i] = 1-B[i]-C[i]
    
    # Calculate first two samples
    y[0] = A[0] * x[0]
    y[1] = A[1] * x[1] - (-B[1])*y[0]
    
    # Filter
    for n in range(2,n_samples):
        y[n] = (A[n] * x[n]) - ((-B[n]) * y[n-1]) - ((-C[n]) * y[n-2])

    return(y)
    
def klattantiresonate(x, param, Fs):
    
    # Imports
    import math
    import numpy as np
    
    # Necessary variables
    dt = 1/Fs
    n_samples = x.size
    
    # Create y[t] (output waveform)
    y = np.zeros([n_samples])

    # Decompose parameter matrix
    frequency = param[:,0]
    bandwidth = param[:,1]

    # Calculate coefficients
    A = np.zeros([n_samples,1])
    B = np.zeros([n_samples,1])
    C = np.zeros([n_samples,1])
    A_prime = np.zeros([n_samples, 1])
    B_prime = np.zeros([n_samples, 1])
    C_prime = np.zeros([n_samples, 1])
    for i in range(0,n_samples):
        C[i] = -math.exp(-2*math.pi*bandwidth[i]*dt)
        B[i] = (2*math.exp(-math.pi*bandwidth[i]*dt)
                *math.cos(2*math.pi*frequency[i]*dt))
        A[i] = 1-B[i]-C[i]
        A_prime[i] = 1/A[i]
        B_prime[i] = (-B[i])/A[i]
        C_prime[i] = (-C[i])/A[i]
    
    # Calculate first two samples
    y[0] = A_prime[0] * x[0]
    y[1] = A_prime[1] * x[1] - (-B_prime[1])*y[0]
    
    # Filter
    for n in range(2,n_samples):
        y[n] = A_prime[n] * x[n] + B_prime[n] * y[n-1] + C_prime[n] * y[n-2]

    return(y)
    
def klattinterpolate(x, n_inc, inc_samples, n_samples):
    
    # Imports
    from scipy.interpolate import interp1d
    import numpy as np
    
    # Perform interpolate to n_inc
    n_input_steps = x.size
    seq = np.arange(0,n_input_steps)
    seq_new = np.linspace(0,n_input_steps-1,n_inc)
    temp = interp1d(seq, x)(seq_new)
    
    # Map to step function
    vector_out = np.zeros([n_samples,])
    k = 0 # Counter
    for i in range(0,n_samples):
        if k == n_inc-1 or k == n_inc:
            k = n_inc-1
        elif i%inc_samples == 0:
            k = k + 1
        vector_out[i] = temp[int(k)]

    return(vector_out)

def klattvoice(f0, n_samples, Fs):
    
    # Imports
    import numpy as np
    
    # Generate constant impulse train
    inc = round(Fs/f0)
    voice = np.zeros([n_samples])
    for i in range(0,n_samples):
        if i%inc == 0:
            voice[i] = 1

    # Generate resonator parameters and apply resonator
    frequency = np.zeros([n_samples, 1])
    bandwidth = np.ones([n_samples, 1]) * 100
    voice = klattresonate(voice, np.concatenate((frequency, bandwidth),
                                                axis = 1), Fs)
    
    # Generate antiresonator parameters and apply antiresonator
    frequency = np.ones([n_samples, 1]) * 1500
    bandwidth = np.ones([n_samples, 1]) * 6000
    voice = klattantiresonate(voice, np.concatenate((frequency, bandwidth),
                                                    axis = 1), Fs)
    
    return(voice)
    
def klattnoise(n_samples, Fs):
    
    # Imports
    import numpy as np
    
    # Generate noise
    noise_big = np.random.uniform(low = 0.0, high = 1.0, size = n_samples*16)
    noise = np.zeros([n_samples])
    
    # Reduce noise
    for i in range(n_samples):
        temp = np.zeros([16])
        for j in range(16):
            temp[j] = noise_big[i*8+j]
        noise[i] = np.mean(temp)
        
    # Apply 6 dB/oct filter
    noise_out = np.zeros([n_samples])
    noise_out[0] = noise[0]
    for i in range(1, n_samples, 1):
        noise_out[i] = noise[i] + noise[i-1]

    return(noise)
    
def klattsynthesize(formant_track, bandwidth_track, f0, voicing, dur, n_samples, Fs):
    
    # Imports
    import numpy as np
    
    # Create necessary variables
    n_formants = formant_track.shape[1]

    # Generate voicing waveform
    if voicing == 1:
        voice = klattvoice(f0, n_samples, Fs)
    elif voicing == 0:
        voice = klattnoise(n_samples, Fs)
    
    # Apply filter cascade
    for i in range(0,n_formants):
        voice = klattresonate(voice, np.column_stack((formant_track[:,i],
                                                      bandwidth_track[:,i])), 
                                                        Fs)
    return(voice)

def klattmake(input_formants, input_bandwidths, input_envelope, f0, voicing, inc_ms, dur, Fs):

    # Import
    import numpy as np
    
    # Create necessary variables
    n_formants = input_formants.shape[1]
    n_samples = round(dur*Fs)
    inc_seconds = inc_ms*0.001
    inc_samples = inc_seconds*Fs
    if dur%inc_seconds != 0:
        n_inc = (dur-dur%inc_seconds)/inc_seconds + 1
    else:
        n_inc = dur/inc_seconds

    # Interpolate inputs
    interpolated_formants = np.zeros([n_samples, n_formants])
    interpolated_bandwidths = np.zeros([n_samples, n_formants])
    interpolated_envelope = np.zeros([n_samples])
    for i in range(0,n_formants):
        interpolated_formants[:,i] = klattinterpolate(input_formants[:,i], n_inc, inc_samples, n_samples)
        interpolated_bandwidths[:,i] = klattinterpolate(input_bandwidths[:,i], n_inc, inc_samples, n_samples)
        interpolated_envelope = klattinterpolate(input_envelope, n_inc, inc_samples, n_samples)
    
    # Synthesize
    vowel = klattsynthesize(interpolated_formants, interpolated_bandwidths, f0, voicing, dur, n_samples, Fs)
    
    # Apply envelope
    vowel = vowel*interpolated_envelope
    
    return(vowel)
