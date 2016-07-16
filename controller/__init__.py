#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The controller is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""


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
        return 0

    def quit(self, event):
        self.view.destroy()

