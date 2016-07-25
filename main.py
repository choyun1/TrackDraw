#!/usr/bin/env python

import sys
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import TDWidgets
import TDSlots


__version__ = "0.2.0"


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setCentralWidget(TDWidgets.TDCanvases(self))

        ##### Menus #####
        # File menu
        audioOpen = partial(TDSlots.audioOpen, parent=self)
        audioSave = partial(TDSlots.audioSave, parent=self)
        helpAbout = partial(TDSlots.helpAbout, parent=self)
        fileMenuActions = [\
                self.createMenuAction("&Open a sound file...", 
                    audioOpen, QKeySequence.Open, None,
                    "Open a sound file"),
                self.createMenuAction("&Save synthesis...", audioSave,
                    QKeySequence.Save, None, "Save the synthesized sound file"),
                "|",
                self.createMenuAction("&Quit", self.close, "Ctrl+Q", None,
                    "Close TrackDraw") ]
        self.fileMenu = self.menuBar().addMenu("&File")
        for action in fileMenuActions:
            if action == "|":
                self.fileMenu.addSeparator()
            else:
                self.fileMenu.addAction(action)
        # Help menu
        helpMenuActions = [\
                self.createMenuAction("&About", helpAbout,
                    tip="About TrackDraw")]
        self.helpMenu = self.menuBar().addMenu("&Help")
        for action in helpMenuActions:
            self.helpMenu.addAction(action)
        ##### End menu setup #####

        ##### Docks on the left hand side #####
        displayDock = TDWidgets.DisplayDock(parent=self)
        displayDock.setAllowedAreas(Qt.LeftDockWidgetArea)
        displayDock.setFeatures(QDockWidget.DockWidgetMovable)
        analysisDock = TDWidgets.AnalysisDock(parent=self)
        analysisDock.setAllowedAreas(Qt.LeftDockWidgetArea)
        analysisDock.setFeatures(QDockWidget.DockWidgetMovable)
        synthesisDock = TDWidgets.SynthesisDock(parent=self)
        synthesisDock.setAllowedAreas(Qt.LeftDockWidgetArea)
        synthesisDock.setFeatures(QDockWidget.DockWidgetMovable)

        self.addDockWidget(Qt.LeftDockWidgetArea, displayDock)
        self.addDockWidget(Qt.LeftDockWidgetArea, analysisDock)
        self.addDockWidget(Qt.LeftDockWidgetArea, synthesisDock)
        self.tabifyDockWidget(displayDock, analysisDock)
        self.tabifyDockWidget(analysisDock, synthesisDock)

        self.setTabPosition(Qt.LeftDockWidgetArea, 2)
        ##### End dock setup #####

        ##### Status bar #####
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
    form = MainWindow()
    form.show()
    app.exec_()


main()

