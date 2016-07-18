#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The view is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class View(tk.Tk):
    """
    Helpful docstring
    The left frame contains all representations of sound
    The right frame contains all buttons
    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.style = ttk.Style()
        self.style.configure("side.TButton",\
                             foreground="#333333",\
                             background="#cccccc",\
                             font=("Helvetica", 16))

        # Main container frames
        self.frame_L = tk.Frame(self)
        self.frame_R = tk.Frame(self)
        self.frame_L.pack(side="left")
        self.frame_R.pack(side="right")

        self.wave = WaveView(self.frame_L)
        self.spec = SpecView(self.frame_L)
        self.main = MainView(self.frame_L)
        self.wave.grid(row=0, column=1)
        self.spec.grid(row=1, column=0)
        self.main.grid(row=1, column=1)

        # Button initializations
        self.plot_loaded_but = ttk.Button(self.frame_R, text="Plot Input Spectrogram")
        self.load_but = ttk.Button(self.frame_R, text="Load Waveform")
        self.synth_but = ttk.Button(self.frame_R, text="Synthesize Waveform")
        self.plot_synth_but = ttk.Button(self.frame_R, text="Plot Synth Spectrogram")
        self.quit_but = ttk.Button(self.frame_R, text="Quit")
        self.play_loaded_but = ttk.Button(self.frame_R, text="Play Input Waveform")
        self.play_synth_but = ttk.Button(self.frame_R, text="Play Synthesized Waveform")
        
        # Scale initializations
        self.fft_length_scale = tk.Scale(self, label="DFT Window Length", from_=64,
                                 to=512, resolution=4, orient="horizontal")
        self.fft_length_scale.set(256)
        
        # Pack buttons
        self.load_but.pack(side="top", fill=tk.BOTH)
        self.plot_loaded_but.pack(side="top", fill=tk.BOTH)
        self.play_loaded_but.pack(side="top", fill=tk.BOTH)
        self.synth_but.pack(side="top", fill=tk.BOTH)
        self.plot_synth_but.pack(side="top", fill=tk.BOTH)
        self.play_synth_but.pack(side="top", fill=tk.BOTH)
        self.quit_but.pack(side="top", fill=tk.BOTH)
        
        # Pack scales
        self.fft_length_scale.pack()
        
class WaveView(tk.Frame):
    """
    Helpful docstring
    """
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)


class SpecView(tk.Frame):
    """
    Helpful docstring
    """
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)


class MainView(tk.Frame):
    """
    Helpful docstring
    """
    def __init__(self, *args, **kwargs):
        
        # Initialize frame, figure, axes, canvas
        tk.Frame.__init__(self, *args, **kwargs)
        self.fig = Figure(figsize = (8, 8), dpi = 80)
        self.ax = self.fig.add_axes((0.1, 0.1, 0.8, 0.8), axisbg =
                                    (0.5, 0.5, 0.5), frameon = False)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self)
        self.canvas.get_tk_widget().pack()
        
        # Create tracks
        self.tracks = []

        # Create utilities as attributes for tracks
        self.inv = self.ax.transData.inverted()
        self.x_low = 0
        self.x_high = 40
        
        # Create background attribute for later use
        self.background = None

    def mouse(self, event):
        """
        Simply converts mouse location to data dimensions and returns them if 
        mouse location is within the plot area
        
        Something wonky is going on with self.inv - Daniel 07/16
        """
        x_loc, y_loc = self.inv.transform((event.x, event.y))
        if 0 < x_loc < 1 and 0 < y_loc < 1:
            x_loc = x_loc*self.x_high
            y_loc = y_loc*5000
            return(x_loc, y_loc)
        else:
            return
            
    def startTracks(self, tracks):
        """
        Draws canvas without tracks and grabs the background, then plots tracks,
        sets limits, and renders the plot again (so tracks are seen on startup)
        """
        self.canvas.draw()
        self.getBackground()
        for i in range(5):
            self.tracks.append(self.ax.plot(tracks[i].points, color="blue", marker='+'))
        self.ax.set_xlim(0, 40)
        self.ax.set_ylim(0, 5000)
        self.canvas.draw()
    
    def getBackground(self):
        self.background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        
    def updateTrack(self, trackNo, updated_track):
        self.tracks[trackNo][0].set_ydata(updated_track)
   
    def redrawTracks(self):
        """
        Restores empty background (doesn't have to redraw everything and waste
        time), then redraws only lines.
        """
        self.fig.canvas.restore_region(self.background)
        for i in range(5):
            self.ax.draw_artist(self.tracks[i][0])
        self.fig.canvas.blit(self.ax.bbox)        
        
    def rescaleTracks(self):
        """
        Changes the x-data in the tracks to scale them (visually) in the x-dimension.
        """
        self.ax.set_xlim(0, self.x_high)
        self.ax.set_ylim(0, 5000)
        self.canvas.draw()
        self.getBackground()
        for i in range(5):
            self.tracks[i][0].set_xdata(np.arange(0, self.x_high, self.x_high/40))
        self.redrawTracks()
