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

        # Side pane initialization
        self.load_but = ttk.Button(self.frame_R, text="Load",\
                                                 style="side.TButton")
        self.quit_but = ttk.Button(self.frame_R, text="Quit",\
                                                 style="side.TButton")
        self.spec_check = ttk.Checkbutton(self.frame_R)
        self.load_but.pack(side="top")
        self.quit_but.pack(side="top")
        self.spec_check.pack(side="top")


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
        tk.Frame.__init__(self, *args, **kwargs)

