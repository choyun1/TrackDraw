#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import TrackDrawWidgets as TDW
import TrackDrawSlots as TDS
import sys
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


__version__ = "0.2.0"


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setCentralWidget(TDW.CanvasGrid(self))

        ##### Menus #####
        # Partial function application to create appropriate callbacks
        audioOpen = partial(TDS.audioOpen, parent=self)
        audioSave = partial(TDS.audioSave, parent=self)
        helpAbout = partial(TDS.helpAbout, parent=self)
        clearPlots = partial(TDS.clearPlots, parent=self)
        applyAnalysis = partial(TDS.applyAnalysis, parent=self)
        synthesize = partial(TDS.synthesize, parent=self)
        # File menu
        fileMenuActions = [\
                self.createMenuAction("&Open a sound file...", 
                    audioOpen, QKeySequence.Open, None,
                    "Open a sound file"),
                self.createMenuAction("&Save synthesis...", audioSave,
                    QKeySequence.Save, None, "Save the synthesized sound file"),
                "|",
                self.createMenuAction("&Quit", self.close, "Ctrl+Q", None,
                    "Close TrackDraw")]
        self.fileMenu = self.menuBar().addMenu("&File")
        for action in fileMenuActions:
            if action == "|":
                self.fileMenu.addSeparator()
            else:
                self.fileMenu.addAction(action)
        # Analysis/Synthesis menu
        ASMenuActions = [\
                self.createMenuAction("C&lear plots", clearPlots, "Ctrl+L",
                    None, "Clear all plots"),
                self.createMenuAction("Apply analysis settings", applyAnalysis,
                    "Ctrl+R", None, "Apply analysis settings and refresh"),
                self.createMenuAction("S&ynthesize", synthesize,
                    "Ctrl+Y", None, "Synthesize using current settings")]
        self.ASMenu = self.menuBar().addMenu("A&nalysis/Synthesis")
        for action in ASMenuActions:
            self.ASMenu.addAction(action)
        # Help menu
        helpMenuActions = [\
                self.createMenuAction("&About", helpAbout,
                    tip="About TrackDraw")]
        self.helpMenu = self.menuBar().addMenu("&Help")
        for action in helpMenuActions:
            self.helpMenu.addAction(action)
        ##### End menu setup #####

        ##### Docks on the right hand side #####
        displayDock = TDW.DisplayDock(parent=self)
        displayDock.setAllowedAreas(Qt.RightDockWidgetArea)
        displayDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        analysisDock = TDW.AnalysisDock(parent=self)
        analysisDock.setAllowedAreas(Qt.RightDockWidgetArea)
        analysisDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        synthesisDock = TDW.SynthesisDock(parent=self)
        synthesisDock.setAllowedAreas(Qt.RightDockWidgetArea)
        synthesisDock.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.addDockWidget(Qt.RightDockWidgetArea, displayDock)
        self.addDockWidget(Qt.RightDockWidgetArea, analysisDock)
        self.addDockWidget(Qt.RightDockWidgetArea, synthesisDock)
        self.tabifyDockWidget(displayDock, analysisDock)
        self.tabifyDockWidget(analysisDock, synthesisDock)

        self.setTabPosition(Qt.RightDockWidgetArea, 3)
        ##### End dock setup #####

        ##### Status bar #####
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.sizeLabel)
        status.showMessage("Welcome to TrackDraw!", 5000)
        ##### End status bar setup #####

    
    def createMenuAction(self, text, slot=None, shortcut=None, icon=None,
            tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TrackDraw")
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()


main()

