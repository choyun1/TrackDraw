#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class TDCanvases(QWidget):
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
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        dispGroupBox = QGroupBox("Display")
        dispGroupVBox = QVBoxLayout()
        dispGroupBox.setLayout(dispGroupVBox)
        loadedRadioButton  = QRadioButton("Loaded sound")
        loadedRadioButton.setChecked(True)
        synthedRadioButton = QRadioButton("Synthesized sound")
        dispGroupVBox.addWidget(loadedRadioButton)
        dispGroupVBox.addWidget(synthedRadioButton)

        STFTCheckBox = QCheckBox("Show STFT")
        STFTCheckBox.setChecked(True)

        showFTCheckBox = QCheckBox("Show formant tracks")
        showFTCheckBox.setChecked(True)

        clearButton = QPushButton("Clear plots")

        mainVBox.addWidget(dispGroupBox)
        mainVBox.addWidget(STFTCheckBox)
        mainVBox.addWidget(showFTCheckBox)
        mainVBox.addWidget(clearButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)


class AnalysisDock(QDockWidget):
    def __init__(self, parent=None):
        super(AnalysisDock, self).__init__(parent)
        self.setWindowTitle("Analysis settings")
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        ###
        methodGroup = QWidget()
        methodVBox = QVBoxLayout()
        methodGroup.setLayout(methodVBox)
        methodLabel = QLabel("Method:")
        methodComboBox = QComboBox()
        methodComboBox.addItems(["Spectrogram", "Wavelet"])
        methodVBox.addWidget(methodLabel)
        methodVBox.addWidget(methodComboBox)

        # Spectrogram settings group box
        specGroup = QGroupBox("Spectrogram settings")
        specVBox = QVBoxLayout()
        specGroup.setLayout(specVBox)

        windowGroup = QWidget()
        windowVBox = QVBoxLayout()
        windowGroup.setLayout(windowVBox)
        windowLabel = QLabel("Window function:")
        windowComboBox = QComboBox()
        windowComboBox.addItems(["Hanning", "Rectangular"])
        windowVBox.addWidget(windowLabel)
        windowVBox.addWidget(windowComboBox)

        #slidersGroup = QWidget()
        #slidersGrid = QGridLayout()
        #slidersGroup.setLayout(slidersGrid)

        #frameSizeLabel = QLabel("Frame size (samples):")
        #frameSizeValueLabel = QLabel("7")
        #frameSizeMinLabel = QLabel("5")
        #frameSizeSlider = QSlider(minimum=5, maximum=10, value=7, orientation=Qt.Horizontal)
        #frameSizeMaxLabel = QLabel("10")

        #overlapSizeLabel = QLabel("Frame overlap (%):")
        #overlapSizeValueLabel = QLabel("25")
        #overlapSizeMinLabel = QLabel("50")
        #overlapSizeSlider = QSlider(minimum=25, maximum=1075, value=50, orientation=Qt.Horizontal)
        #overlapSizeMaxLabel = QLabel("1075")

        #slidersGrid.addWidget(frameSizeLabel, 0, 0, 1, 2)
        #slidersGrid.addWidget(frameSizeValueLabel, 0, 2)
        #slidersGrid.addWidget(frameSizeMinLabel, 1, 0)
        #slidersGrid.addWidget(frameSizeSlider, 1, 1)
        #slidersGrid.addWidget(frameSizeMaxLabel, 1, 2)
        #slidersGrid.addWidget(overlapSizeLabel, 2, 0, 1, 2)
        #slidersGrid.addWidget(overlapSizeValueLabel, 2, 2)
        #slidersGrid.addWidget(overlapSizeMinLabel, 3, 0)
        #slidersGrid.addWidget(overlapSizeSlider, 3, 1)
        #slidersGrid.addWidget(overlapSizeMaxLabel, 3, 2)

        frameSizeGroup = SliderGroup(name="Frame size (samples):", minimum=5,
                maximum=10, stepDouble=True, value=8)

        overlapGroup = SliderGroup(name="Frame overlap (%):", minimum=5,
                maximum=15, stepSize=5, value=10)

        thresholdGroup = SliderGroup(name="Threshold (dB):", minimum=0,
                maximum=10, stepSize=1, value=3)

        #specVBox.addWidget(windowGroup)
        #specVBox.addWidget(slidersGroup)
        specVBox.addWidget(frameSizeGroup)
        specVBox.addWidget(overlapGroup)
        specVBox.addWidget(thresholdGroup)
        #
        applyButton = QPushButton("Apply")
        ###

        mainVBox.addWidget(methodGroup)
        mainVBox.addWidget(specGroup)
        mainVBox.addWidget(applyButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)


class SynthesisDock(QDockWidget):
    def __init__(self, parent=None):
        super(SynthesisDock, self).__init__(parent)
        self.setWindowTitle("Synthesis settings")
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        ###
        methodGroup = QWidget()
        methodVBox = QVBoxLayout()
        methodGroup.setLayout(methodVBox)
        methodLabel = QLabel("Method:")
        methodComboBox = QComboBox()
        methodComboBox.addItems(["Klatt 1980", "Sine wave"])
        methodVBox.addWidget(methodLabel)
        methodVBox.addWidget(methodComboBox)

        # Klatt synthesis settings group box
        klattGroup = QGroupBox("Klatt settings")
        klattVBox = QVBoxLayout()
        klattGroup.setLayout(klattVBox)

        nformantGroup = QWidget()
        nformantVBox = QVBoxLayout()
        nformantGroup.setLayout(nformantVBox)
        nformantLabel = QLabel("Number of formant tracks:")
        nformantComboBox = QComboBox()
        nformantComboBox.addItems(["1", "2", "3", "4", "5"])
        nformantComboBox.setCurrentIndex(4)
        nformantVBox.addWidget(nformantLabel)
        nformantVBox.addWidget(nformantComboBox)

        F1BandwidthGroup = SliderGroup(name="F1 bandwidth (Hz):", minimum=5,
                maximum=20, value=10)
        F2BandwidthGroup = SliderGroup(name="F2 bandwidth (Hz):", minimum=5,
                maximum=20, value=10)
        F3BandwidthGroup = SliderGroup(name="F3 bandwidth (Hz):", minimum=5,
                maximum=20, value=10)
        F4BandwidthGroup = SliderGroup(name="F4 bandwidth (Hz):", minimum=5,
                maximum=20, value=10)
        F5BandwidthGroup = SliderGroup(name="F5 bandwidth (Hz):", minimum=5,
                maximum=20, value=10)
        #F5BandwidthGroup.setEnabled(False)

        klattVBox.addWidget(nformantGroup)
        klattVBox.addWidget(F1BandwidthGroup)
        klattVBox.addWidget(F2BandwidthGroup)
        klattVBox.addWidget(F3BandwidthGroup)
        klattVBox.addWidget(F4BandwidthGroup)
        klattVBox.addWidget(F5BandwidthGroup)
        #
        applyButton = QPushButton("Synthesize")
        ###

        mainVBox.addWidget(methodGroup)
        mainVBox.addWidget(klattGroup)
        mainVBox.addWidget(applyButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)


class SliderGroup(QWidget):
    def __init__(self, parent=None, name="", minimum=1, maximum=99, value=1,
            stepSize=1, stepDouble=False, orientation=Qt.Horizontal):
        super(SliderGroup, self).__init__(parent)
        self.stepSize = stepSize
        self.stepDouble = stepDouble
        if stepDouble:
            self.currValue = 2**value
            self.valueLabel = QLabel(str(self.currValue))
            minLabel = QLabel(str(2**minimum))
            maxLabel = QLabel(str(2**maximum))
        else:
            self.currValue = self.stepSize*value
            self.valueLabel = QLabel(str(self.currValue))
            minLabel = QLabel(str(self.stepSize*minimum))
            maxLabel = QLabel(str(self.stepSize*maximum))

        topContainer = QWidget()
        topHBox = QHBoxLayout()
        topContainer.setLayout(topHBox)
        nameLabel = QLabel(name)
        topHBox.addWidget(nameLabel)
        topHBox.addWidget(self.valueLabel)

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
        #vBox.addWidget(nameLabel)
        #vBox.addWidget(self.valueLabel)
        #vBox.addWidget(self.slider)
        vBox.addWidget(botContainer)

    @pyqtSlot()
    def updateValueLabel(self):
        if self.stepDouble:
            self.currValue = 2**self.slider.value()
        else:
            self.currValue = self.stepSize*self.slider.value()
        self.valueLabel.setText(str(self.currValue))

