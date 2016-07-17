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

        # Define callback functions for buttons in view
        def load_callback(event):
            file_opt = {}
            file_opt["defaultextension"] = ".wav"
            file_opt["filetypes"] = [("wave files", ".wav")]
            file_opt["title"] = "Load wav file"
            filename = fdialog.askopenfilename(**file_opt)
            if filename:
                fs, x = wavfile.read(filename)
        def quit_callback(event):
            self.view.destroy()
        def spec_check_callback(event):
            # Just a test function to display messages
            print(self.model.loaded_sound.nsamples)

        # Bind the callbacks
        self.view.load_but.bind("<Button-1>", load_callback)
        self.view.quit_but.bind("<Button-1>", quit_callback)
        self.view.spec_check.bind("<Button-1>", spec_check_callback)

    def run(self):
        self.view.mainloop()

