#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import TrackDrawData as TDD
import TrackDrawSlots as TDS
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class CanvasGrid(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)

        mainGrid = QGridLayout()
        self.setLayout(mainGrid)
        mainGrid.setRowMinimumHeight(0, 80)
        mainGrid.setRowMinimumHeight(1, 300)
        mainGrid.setRowMinimumHeight(2, 120)
        mainGrid.setColumnMinimumWidth(0, 100)
        mainGrid.setColumnMinimumWidth(1, 300)

        mainGrid.setRowStretch(0, 4)
        mainGrid.setRowStretch(1, 20)
        mainGrid.setRowStretch(2, 6)
        mainGrid.setColumnStretch(0, 1)
        mainGrid.setColumnStretch(1, 6)

        canvas1 = FigureCanvas(Figure())
        canvas2 = FigureCanvas(Figure())
        canvas3 = FigureCanvas(Figure())
        canvas4 = FigureCanvas(Figure())
        mainGrid.addWidget(canvas1, 0, 1)
        mainGrid.addWidget(canvas2, 1, 0)
        mainGrid.addWidget(canvas3, 1, 1)
        mainGrid.addWidget(canvas4, 2, 1)


class DisplayDock(QDockWidget):
    def __init__(self, parent=None):
        super(DisplayDock, self).__init__(parent)
        self.setWindowTitle("Display settings")

        ### Select display group
        dispGroupBox = QGroupBox("Display")
        dispGroupVBox = QVBoxLayout()
        dispGroupBox.setLayout(dispGroupVBox)
        loadedRadioButton  = QRadioButton("Loaded sound")
        loadedRadioButton.setChecked(True)
        synthedRadioButton = QRadioButton("Synthesized sound")
        dispGroupVBox.addWidget(loadedRadioButton)
        dispGroupVBox.addWidget(synthedRadioButton)
        ###
        waveCheckBox = QCheckBox("Show waveform")
        waveCheckBox.setChecked(True)

        STFTCheckBox = QCheckBox("Show STFT")
        STFTCheckBox.setChecked(True)

        showFTCheckBox = QCheckBox("Show formant tracks")
        showFTCheckBox.setChecked(True)
        ### Clear plots button
        clearButton = QPushButton("Clear plots (Ctrl+L)")
        clearButton.setToolTip("Clear all plots")
        clearButton.setStatusTip("Clear all plots")
        clearPlots = partial(TDS.clearPlots, self)
        clearButton.clicked.connect(clearPlots)
        ###

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(dispGroupBox)
        mainVBox.addWidget(waveCheckBox)
        mainVBox.addWidget(STFTCheckBox)
        mainVBox.addWidget(showFTCheckBox)
        mainVBox.addWidget(clearButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)


class AnalysisDock(QDockWidget):
    def __init__(self, parent=None):
        super(AnalysisDock, self).__init__(parent)
        self.setWindowTitle("Analysis settings")

        ### Select analysis method group
        methodGroup = QWidget()
        methodVBox = QVBoxLayout()
        methodGroup.setLayout(methodVBox)
        resample_fs = TDD.CURRENT_PARAMS.resample_fs
        resampleLabel = QLabel("Resample rate:  " + str(resample_fs) + " Hz")
        methodLabel = QLabel("Method:")
        self.methodComboBox = QComboBox()
        self.methodComboBox.addItems(["Spectrogram", "Wavelet"])
        self.methodComboBox.currentIndexChanged.connect(self.changeAnalysis)

        methodVBox.addWidget(resampleLabel)
        methodVBox.addSpacing(15)
        methodVBox.addWidget(methodLabel)
        methodVBox.addWidget(self.methodComboBox)
        ###

        ### Spectrogram settings group box
        self.specGroup = QGroupBox("Spectrogram settings")
        specVBox = QVBoxLayout()
        self.specGroup.setLayout(specVBox)

        windowGroup = QWidget()
        windowVBox = QVBoxLayout()
        windowGroup.setLayout(windowVBox)
        windowLabel = QLabel("Window function:")
        windowComboBox = QComboBox()
        windowComboBox.addItems(["Hanning", "Rectangular"])
        windowVBox.addWidget(windowLabel)
        windowVBox.addWidget(windowComboBox)

        frameSizeGroup = SliderGroup(label="Frame size:", units="samples",
                minimum=5, maximum=10, stepDouble=True, value=8)

        overlapGroup = SliderGroup(label="Frame overlap:", units="%",
                minimum=5, maximum=15, stepSize=5, value=10)

        thresholdGroup = SliderGroup(label="Threshold:", units="dB",
                minimum=0, maximum=10, stepSize=1, value=3)

        specVBox.addWidget(windowGroup)
        specVBox.addWidget(frameSizeGroup)
        specVBox.addWidget(overlapGroup)
        specVBox.addWidget(thresholdGroup)
        ###

        ### Wavelet settings group box
        self.waveletGroup = QGroupBox("Wavelet settings")
        waveletVBox = QVBoxLayout()
        self.waveletGroup.setLayout(waveletVBox)

        settingGroup = QWidget()
        settingVBox = QVBoxLayout(settingGroup)

        waveletVBox.addWidget(settingGroup)
        ###

        ### Apply button
        applyButton = QPushButton("Apply settings (Ctrl+R)")
        applyButton.setToolTip("Apply analysis settings")
        applyButton.setStatusTip("Apply analysis settings")
        applyAnalysis = partial(TDS.applyAnalysis, parent=self)
        applyButton.clicked.connect(applyAnalysis)
        ###

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(methodGroup)
        mainVBox.addWidget(self.specGroup)
        mainVBox.addWidget(self.waveletGroup)
        self.waveletGroup.setHidden(True)
        mainVBox.addWidget(applyButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)
        ###

    @pyqtSlot()
    def changeAnalysis(self):
        currIdx = self.methodComboBox.currentIndex()
        if currIdx == 0:
            self.specGroup.setHidden(False)
            self.waveletGroup.setHidden(True)
        elif currIdx == 1:
            self.specGroup.setHidden(True)
            self.waveletGroup.setHidden(False)


class SynthesisDock(QDockWidget):
    def __init__(self, parent=None):
        super(SynthesisDock, self).__init__(parent)
        self.setWindowTitle("Synthesis settings")

        ### Select synthesis method group
        methodGroup = QWidget()
        methodVBox = QVBoxLayout()
        methodGroup.setLayout(methodVBox)
        synthesis_fs = TDD.CURRENT_PARAMS.synth_fs
        synthesisLabel = QLabel("Synthesis rate:  " + str(synthesis_fs) + " Hz")
        methodLabel = QLabel("Method:")
        self.methodComboBox = QComboBox()
        self.methodComboBox.addItems(["Klatt 1980", "Sine wave"])
        self.methodComboBox.currentIndexChanged.connect(self.changeSynthesis)

        methodVBox.addWidget(synthesisLabel)
        methodVBox.addSpacing(15)
        methodVBox.addWidget(methodLabel)
        methodVBox.addWidget(self.methodComboBox)
        ###

        nformantGroup = QWidget()
        nformantVBox = QVBoxLayout()
        nformantGroup.setLayout(nformantVBox)
        nformantLabel = QLabel("Number of formant tracks:")
        nformantComboBox = QComboBox()
        nformantComboBox.addItems(["1", "2", "3", "4", "5"])
        nformantComboBox.setCurrentIndex(4)
        nformantVBox.addWidget(nformantLabel)
        nformantVBox.addWidget(nformantComboBox)

        ### Klatt synthesis settings group box
        self.klattGroup = QGroupBox("Klatt synthesizer settings")
        klattVBox = QVBoxLayout()
        self.klattGroup.setLayout(klattVBox)

        F1BandwidthGroup = SliderGroup(label="F1 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F2BandwidthGroup = SliderGroup(label="F2 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F3BandwidthGroup = SliderGroup(label="F3 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F4BandwidthGroup = SliderGroup(label="F4 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F5BandwidthGroup = SliderGroup(label="F5 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)

        klattVBox.addWidget(F1BandwidthGroup)
        klattVBox.addWidget(F2BandwidthGroup)
        klattVBox.addWidget(F3BandwidthGroup)
        klattVBox.addWidget(F4BandwidthGroup)
        klattVBox.addWidget(F5BandwidthGroup)
        ###

        ### Sine wave synthesis settings group box
        self.sineGroup = QGroupBox("Sine wave synthesizer settings")
        sineVBox = QVBoxLayout()
        self.sineGroup.setLayout(sineVBox)
        ###

        ### Synthesize button
        synthButton = QPushButton("Synthesize (Ctrl+Y)")
        synthButton.setToolTip("Synthesize using current settings")
        synthButton.setStatusTip("Synthesize using current settings")
        synthesize = partial(TDS.synthesize, parent=self)
        synthButton.clicked.connect(synthesize)
        ###

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(methodGroup)
        mainVBox.addWidget(nformantGroup)
        mainVBox.addWidget(self.klattGroup)
        mainVBox.addWidget(self.sineGroup)
        self.sineGroup.setHidden(True)
        mainVBox.addWidget(synthButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)
        ###

    @pyqtSlot()
    def changeSynthesis(self):
        currIdx = self.methodComboBox.currentIndex()
        if currIdx == 0:
            self.klattGroup.setHidden(False)
            self.sineGroup.setHidden(True)
        elif currIdx == 1:
            self.klattGroup.setHidden(True)
            self.sineGroup.setHidden(False)


class SliderGroup(QWidget):
    """
    A convenience widget for displaying slider information (minimum, maximum,
    and current value). Set stepDouble=True to create a slider that doubles
    its value each step.
    """
    def __init__(self, parent=None, label="", units="", minimum=1, maximum=99,
            value=1, stepSize=1, stepDouble=False, orientation=Qt.Horizontal):
        super(SliderGroup, self).__init__(parent)
        self.labelTxt = label
        self.unitsTxt = units
        self.stepSize = stepSize
        self.stepDouble = stepDouble
        if self.stepDouble:
            self.currValue = 2**value
            minLabel = QLabel(str(2**minimum))
            maxLabel = QLabel(str(2**maximum))
        else:
            self.currValue = self.stepSize*value
            minLabel = QLabel(str(self.stepSize*minimum))
            maxLabel = QLabel(str(self.stepSize*maximum))

        topContainer = QWidget()
        topHBox = QHBoxLayout()
        topContainer.setLayout(topHBox)
        topTxt = self.labelTxt + "  " + str(self.currValue)\
               + " " + self.unitsTxt
        self.topLabel = QLabel(topTxt)
        topHBox.addWidget(self.topLabel)

        botContainer = QWidget()
        botHBox = QHBoxLayout()
        botContainer.setLayout(botHBox)
        self.slider = QSlider(minimum=minimum, maximum=maximum,
                value=value, orientation=orientation)
        self.slider.valueChanged.connect(self.updateValueLabel)
        botHBox.addWidget(minLabel)
        botHBox.addWidget(self.slider)
        botHBox.addWidget(maxLabel)

        vBox = QVBoxLayout()
        self.setLayout(vBox)
        vBox.addWidget(topContainer)
        vBox.addWidget(botContainer)

    @pyqtSlot()
    def updateValueLabel(self):
        if self.stepDouble:
            self.currValue = 2**self.slider.value()
        else:
            self.currValue = self.stepSize*self.slider.value()
        newTopTxt = self.labelTxt + "  " + str(self.currValue)\
                  + " " + self.unitsTxt
        self.topLabel.setText(newTopTxt)

