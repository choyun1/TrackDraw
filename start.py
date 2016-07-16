#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script runs TrackDraw.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import model
import view
import controller


if __name__ == "__main__":
    TrackDraw_model = model.Model()
    TrackDraw_view  = view.View()
    control = controller.Controller(TrackDraw_model, TrackDraw_view)
    control.run()

