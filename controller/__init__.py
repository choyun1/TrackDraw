#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The controller is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import tkinter.filedialog as fdialog
from scipy.io import wavfile


class Controller:
    """
    Helpful docstring
    """
    def __init__(self, model, view):
        self.model = model
        self.view  = view
        self.view.load_but.bind("<Button-1>", self.load)
        self.view.quit_but.bind("<Button-1>", self.quit)

    def run(self):
        self.view.mainloop()

    def load(self, event):
        file_opt = {}
        file_opt["defaultextension"] = ".wav"
        file_opt["filetypes"] = [("wave files", ".wav")]
        file_opt["title"] = "Load wav file"
        filename = fdialog.askopenfilename(**file_opt)
        if filename:
            fs, x = wavfile.read(filename)

    def quit(self, event):
        self.view.destroy()

