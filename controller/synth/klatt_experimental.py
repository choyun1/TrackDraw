"""
@name:    klatt.py
@author:  Daniel R Guest
@date:    07/20/2016
@version: 0.2.0
@purpose: Klatt voice synthesizer and interface between TrackDraw 2016 and
          Klatt syntheiszer.

@overview:
    klatt.py is composed of three sections: klatt_make, klatt_bridge, and
    klatt_synth. klatt_make accepts a Parameters object from the TrackDraw 2016
    program and extracts necessary synthesis parameters from the object.
    klatt_bridge accepts these extracted synthesis parameters, converts them 
    to a format better suited for Klatt synthesis, and passes them to an
    instance of a klatt_synth object. Then, klatt_bridge calls the object's
    synth() method, which synthesizes the waveform. Finally, klatt_bridge takes
    the object's output and returns it to klatt_make, which in turn returns it
    to TrackDraw 2016.
    
    klatt.py is based on Klatt (1980), but only includes the portions necessary
    for synthesis of isolated vowels. The main synthesis procedure synthesizes 
    the output vowel waveform in small intervals (default 50 samples).
    
    Klatt, D. (1980). Software for a cascade/parallel formant synthesizer. 
    The Journal Of The Acoustical Society Of America, 67(3), 971. 
    http://dx.doi.org/10.1121/1.383940
"""
def klatt_make(parms):
    """
    """
    f0 = parms.F0
    ff = parms.FF
    bw = parms.BW
    fs = parms.synth_fs
    dur = parms.dur
    env = parms.envelope
    y = klatt_bridge(f0, ff, bw, fs, dur, env)
    return(y)
    
def klatt_bridge(f0, ff, bw, fs, dur, env, inv_samp=50):
    """
    Takes a variety of synthesis parameters passed to it from klatt_make and 
    interpolates them or derives other values from them as necessary for Klatt
    synthesis. Then passes them to a klatt_synth object and runs the synthesis
    routine, returning the resultant waveform back to klatt_make. 
    """
    from scipy.interpolate import interp1d
    import numpy as np
    
    # First, determine necessary number of update intervals
    n_inv = round(dur*fs/inv_samp)
    # Next, determine the number of formants
    n_form = ff.shape[1]
    # Next, take all input parameters and interpolate as necessary
    def interpolate(input_vector, n_inv):
        """
        Takes input vector, linearlly interpolates to output vector with length
        n_inv, returns as list.
        """
        try:
            n_input_steps = len(input_vector)
            seq = np.arange(0, n_input_steps)
            seq_new = np.linspace(0, n_input_steps-1, n_inv)
            return(list(interp1d(seq, input_vector)(seq_new)))
        except TypeError:
            return([input_vector] * n_inv) # Returns constant function in len = 1
    interp_f0 = []
    interp_ff = []
    interp_bw = []
    interp_env = []
    interp_f0 = interpolate(f0, n_inv)
    for i in range(n_form):
        interp_ff.append(interpolate(ff[:,i], n_inv))
        interp_bw.append(interpolate(bw[:,i], n_inv))
    interp_env = interpolate(env, n_inv)
    # Finally, create synth object, run it, and return its output waveform    
    synth = klatt_synth(f0=interp_f0, ff=interp_ff, bw=interp_bw,
                        env=interp_env, fs=fs, n_inv=n_inv, n_form=n_form,
                        inv_samp=inv_samp)
    synth.synth()
    return(synth.output)
    
class klatt_synth:
    """
    klatt_synth accepts a variety of synthesis parameters and synthesizes an
    output waveform when called with the synth() method. klatt_synth expects
    the inputs f0 and env to be lists of length n_inv, and expects ff and bw
    to be lists containing n_form lists each length n_inv. 
    
    As of version 0.2, klatt_synth contains default values for the rgp and rgz
    components of the Klatt (1980) synthesizer, and synthesizes vowels with 
    time-varying formant and fundamental frequency contours. Support for
    voicing amplitude, noise source, nasal resonators, etc., has not yet been
    added.
    
    The output vowel waveform is synthesized in intervals of length inv_samp.
    Each resonator and antiresonator is represented by an instance of either a
    Resonator or Antiresonator object. Other necessary functions (impulse 
    generation, coefficient calculation, index updating, etc.) are contained 
    within methods of the klatt_synth class. [This will likely change!]
    """
    def __init__(self, f0, ff, bw, env, fs, n_inv, n_form, inv_samp):
        import math
        # Initialize time-varying synthesis parameters
        self.f0 = f0
        self.ff = ff
        self.bw = bw
        self.fs = fs
        self.env = env
        self.dt = 1/self.fs
        
        # Initialize non-time-varying synthesis parameters 
        self.inv_samp = inv_samp
        self.n_inv = n_inv
        self.n_form = n_form
        self.rgp_c = -math.exp(-2*math.pi*100*self.dt)
        self.rgp_b = (2*math.exp(-math.pi*100*self.dt)*math.cos(2*math.pi*0*self.dt))
        self.rgp_a = 1-self.rgp_b-self.rgp_c
        self.rgz_c = -math.exp(-2*math.pi*6500*self.dt)
        self.rgz_b = (2*math.exp(-math.pi*6500*self.dt)*math.cos(2*math.pi*1500*self.dt))
        self.rgz_a = 1-self.rgz_b-self.rgz_c
        
        # Initialize trackers
        self.last_glot_pulse = 0
        self.current_inv = 0 # Index in terms of intervals
        self.next_inv = 1
        self.current_ind = self.current_inv*self.inv_samp # Index in terms of samples
        self.next_ind = self.next_inv*self.inv_samp
        
        # Initialize input/output vectors
        self.input = [0] * self.n_inv*self.inv_samp
        self.output = [0] * self.n_inv*self.inv_samp

        # Initialize resonators
        self.rgp = Resonator(self)
        self.rgz = Antiresonator(self)
        self.forms = []
        for form in range(self.n_form):
            self.forms.append(Resonator(self))
        
    def synth(self):
        for i in range(self.n_inv):
            self.impulse_gen()
            self.rgp.resonate(self.rgp_a, self.rgp_b, self.rgp_c)
            self.rgz.antiresonate(self.rgz_a, self.rgz_b, self.rgz_c)
            for form in range(self.n_form):
                a, b, c = self.calc_coef(current_form=form)
                self.forms[form].resonate(a, b, c)
                self.radiation_characteristic()
            self.update_inv()
        self.reset()
            
    def impulse_gen(self):
        glot_period = round(self.fs/self.f0[self.current_inv])
        for i in range(self.inv_samp):
            if (self.current_ind+i)-self.last_glot_pulse >= glot_period:
                self.output[self.current_ind+i] = 1
                self.last_glot_pulse = self.current_ind+i
        self.perpetuate()
        
    def radiation_characteristic(self):
        if self.current_inv == 0:
            self.output[0] = self.input[0]
            for n in range(1, self.inv_samp):
                self.output[n] = self.input[n] - self.input[n-1]
        else:
            for n in range(0, self.inv_samp):
                self.output[self.current_ind+n] =\
                     self.input[self.current_ind+n]\
                     - self.input[self.current_ind+n-1]
        
#    def noise_gen(self):
#        noise_big = np.random.uniform(low = 0.0, high = 1.0, size = self.inv_samp*16)
#        noise = np.zeros([self.inv_samp])
#        for i in range(self.inv_samp):
#            temp = np.zeros([16])
#            for j in range(16):
#                temp[j] = noise_big[i*8+j]
#            noise[i] = np.mean(temp)
#        self.output[self.current_ind:self.next_ind] = noise[:]
#        self.perpetuate()    
#        # Apply 6 dB/oct filter
#        noise_out = np.zeros([n_samples])
#        noise_out[0] = (1/2)*noise[0]
#        for i in range(1, n_samples, 1):
#            noise_out[i] = (1/2)*(noise[i] + noise[i-1])
                
    def calc_coef(self, current_form):
        import math
        c = -math.exp(-2*math.pi*self.bw[current_form][self.current_inv]*self.dt)
        b = (2*math.exp(-math.pi*self.bw[current_form][self.current_inv]*self.dt)\
             *math.cos(2*math.pi*self.ff[current_form][self.current_inv]*self.dt))
        a = 1-b-c
        return(a, b, c)
        
    def perpetuate(self):
        """
        Makes the input of the current interval the output of the current
        interval. As each component of the synthesizer completes its job, it 
        calls this function so that the next component receives the output of
        the previous component.
        """
        self.input[self.current_ind:self.next_ind] = self.output[self.current_ind:self.next_ind]    
                
    def update_inv(self):
        self.current_inv = self.current_inv + 1
        self.next_inv = self.next_inv + 1
        self.current_ind = self.current_inv*self.inv_samp
        self.next_ind = self.next_inv*self.inv_samp
        
    def reset(self):
        """
        Probably not necessary, but resets the current interval and input so
        that if updated parameters are passed to the object, synth() can be 
        called again. 
        """
        self.current_inv = 0
        self.next_inv = 1
        self.current_ind = self.current_inv*self.inv_samp
        self.next_ind = self.next_inv*self.inv_samp
        self.input = [0] * self.n_inv*self.inv_samp

class Resonator(object):
    """
    Resonator ala Klatt (1980). If the interval being processed is the first
    interval, the first fifty samples are calculated assuming that input(-1)
    and input(-2) are zero. Then, the two final calculated samples of the 
    interval are stored in self.delay. These samples are used in calculation of
    the first two samples of the next interval, since the difference equation 
    contains a maximum delay of two samples. Operation continues in this 
    pattern (calculating inv_samp samples, storing the final two calculated in
    the delay, using the samples in the delay to calculate the first two
    samples of the next interval, etc. etc.).
    """
    def __init__(self, mast):
        self.mast = mast
        self.delay = [0] * 2
    
    def resonate(self, a, b, c):
        if self.mast.current_inv == 0:
            self.mast.output[0] = a*self.mast.input[0]
            self.mast.output[1] = a*self.mast.input[1] + b*self.mast.output[0]
            for n in range(2, self.mast.inv_samp):
                self.mast.output[n] = a*self.mast.input[n]\
                     - (-b*self.mast.output[n-1])\
                     - (-c*self.mast.output[n-2])
        else:
            self.mast.output[self.mast.current_ind] =\
                     a*self.mast.input[self.mast.current_ind]\
                     - (-b*self.delay[1]) - (-c*self.delay[0])
            self.mast.output[self.mast.current_ind+1] =\
                     a*self.mast.input[self.mast.current_ind+1]\
                     - (-b*self.mast.output[self.mast.current_ind])\
                     - (-c*self.delay[1])
            for n in range(2, self.mast.inv_samp):
                self.mast.output[self.mast.current_ind+n] =\
                     a*self.mast.input[self.mast.current_ind+n]\
                     - (-b*self.mast.output[self.mast.current_ind+n-1])\
                     - (-c*self.mast.output[self.mast.current_ind+n-2])     
        self.delay[:] = self.mast.output[self.mast.next_ind-2:self.mast.next_ind]
        self.mast.perpetuate()
        
class Antiresonator(object):
    """
    Functions similarly to Resonator, but with -dB in place of dB. See Klatt
    (1980) for more information.
    """
    def __init__(self, mast):
        self.mast = mast
        self.delay = [0] * 2
    
    def antiresonate(self, a, b, c):
        a_prime = 1/a
        b_prime = -b/a
        c_prime = -c/a
        a = a_prime
        b = b_prime
        c = c_prime
        if self.mast.current_inv == 0:
            self.mast.output[0] = a*self.mast.input[0]
            self.mast.output[1] = a*self.mast.input[1] + b*self.mast.output[0]
            for n in range(2, self.mast.inv_samp):
                self.mast.output[n] = a*self.mast.input[n]\
                     - (-b*self.mast.output[n-1])\
                     - (-c*self.mast.output[n-2])
        else:
            self.mast.output[self.mast.current_ind] =\
                     a*self.mast.input[self.mast.current_ind]\
                     - (-b*self.delay[1]) - (-c*self.delay[0])
            self.mast.output[self.mast.current_ind+1] =\
                     a*self.mast.input[self.mast.current_ind+1]\
                     - (-b*self.mast.output[self.mast.current_ind])\
                     - (-c*self.delay[1])
            for n in range(2, self.mast.inv_samp):
                self.mast.output[self.mast.current_ind+n] =\
                     a*self.mast.input[self.mast.current_ind+n]\
                     - (-b*self.mast.output[self.mast.current_ind+n-1])\
                     - (-c*self.mast.output[self.mast.current_ind+n-2])     
        self.delay[:] = self.mast.output[self.mast.next_ind-2:self.mast.next_ind]
        self.mast.perpetuate()