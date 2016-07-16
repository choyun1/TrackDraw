#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The view is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class View(tk.Tk):
    """
    Helpful docstring
    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.frame_left  = tk.Frame(self)
        self.frame_right = tk.Frame(self)
        self.frame_left.pack(side="left")
        self.frame_right.pack(side="left")

        self.main = MainView(self.frame_left)
        self.wave = WaveView(self.frame_left)
        self.spec = SpecView(self.frame_left)

        self.load_but = tk.Button(self.frame_right, text="Load")
        self.quit_but = tk.Button(self.frame_right, text="Quit")
        self.load_but.pack(side="top")
        self.quit_but.pack(side="top")


class MainView(tk.Frame):
    """
    Helpful docstring
    """
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)


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

