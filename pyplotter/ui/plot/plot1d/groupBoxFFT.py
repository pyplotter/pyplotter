from PyQt5 import QtCore, QtWidgets
import numpy as np
from typing import Tuple

from .groupBoxFFTUi import Ui_QGroupBoxFFT
from ....sources.pyqtgraph import pg


class GroupBoxFFT(QtWidgets.QGroupBox):


    signalUpdateCurve = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
    signal2MainWindowAddPlot   = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)
    signalClose1dPlot  = QtCore.pyqtSignal(str)


    def __init__(self, parent: QtWidgets.QGroupBox,
                       config: dict,
                       databaseAbsPath: str,
                       plotItem: pg.PlotItem,
                       plotRef:str,
                       windowTitle: str) -> None:

        super(GroupBoxFFT, self).__init__(parent)

        # Build the UI
        self.ui = Ui_QGroupBoxFFT()
        self.ui.setupUi(self)

        self.config = config
        self.databaseAbsPath = databaseAbsPath
        self.plotItem = plotItem
        self.plotRef = plotRef
        self._windowTitle = windowTitle


        self.ui.checkBoxFFT.clicked.connect(self.clickFFT)
        self.ui.checkBoxFFTnoDC.clicked.connect(self.clickFFTnoDC)
        self.ui.checkBoxIFFT.clicked.connect(self.clickIFFT)



    ####################################
    #
    #           Slots
    #
    ####################################




    @QtCore.pyqtSlot(bool)
    def slotCheckBoxFFTSetChecked(self, state: bool):
        self.ui.checkBoxFFT.setChecked(state)
        del(self.fftPlotRef)
        del(self.fftCurveId)



    @QtCore.pyqtSlot(bool)
    def slotCheckBoxFFTnoDCSetChecked(self, state: bool):
        self.ui.checkBoxFFTnoDC.setChecked(state)
        del(self.fftNoDcPlotRef)
        del(self.fftNoDcCurveId)

    @QtCore.pyqtSlot(bool)
    def slotCheckBoxIFFTSetChecked(self, state: bool):
        self.ui.checkBoxIFFT.setChecked(state)
        del(self.ifftPlotRef)
        del(self.ifftCurveId)


    @QtCore.pyqtSlot(np.ndarray, str, str, np.ndarray, str, str)
    def slotGetSelectedData(self, selectedX,
                                  selectedXLabel,
                                  selectedXUnits,
                                  selectedY,
                                  selectedYLabel,
                                  selectedYUnits):
        self.selectedX = selectedX
        self.selectedXLabel = selectedXLabel
        self.selectedXUnits = selectedXUnits
        self.selectedY = selectedY
        self.selectedYLabel = selectedYLabel
        self.selectedYUnits = selectedYUnits


    ####################################
    #
    #           Slot to update plot
    #
    ####################################

    @QtCore.pyqtSlot()
    def slotFFTUpdate(self):
        self.fftUpdateCurve()

    @QtCore.pyqtSlot()
    def slotFFTNoDcUpdate(self):
        self.fftNoDcUpdateCurve()

    @QtCore.pyqtSlot()
    def slotIFFTUpdate(self):
        self.ifftUpdateCurve()


    ####################################
    #
    #           Slot to close plot
    #
    ####################################


    @QtCore.pyqtSlot()
    def slotFFTClosePlot(self):
        self.fftClosePlot()


    @QtCore.pyqtSlot()
    def slotFFTNoDcClosePlot(self):
        self.fftNoDcClosePlot()


    @QtCore.pyqtSlot()
    def slotIFFTClosePlot(self):
        self.ifftClosePlot()

    ####################################
    #
    #           Method to related to FFT
    #
    ####################################



    def fftGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
        y = np.abs(np.fft.fft(self.selectedY))[x>=0]
        x = x[x>=0]

        return x, y



    def fftUpdateCurve(self) -> None:
        if hasattr(self, 'fftPlotRef'):
            x, y = self.fftGetData()
            self.signalUpdateCurve.emit(self.fftPlotRef,
                                        self.fftCurveId,
                                        '',
                                        x,
                                        y,
                                        False,
                                        False)



    def clickFFT(self) -> None:

        if self.ui.checkBoxFFT.isChecked():

            self.fftCurveId = self.selectedYLabel+'fft'
            self.fftPlotRef = self.plotRef+'fft'
            xLabelText  = '1/'+self.selectedXLabel
            xLabelUnits = '1/'+self.selectedXUnits
            yLabelText  = 'FFT'+'( '+self.selectedYLabel+' )'
            yLabelUnits = self.selectedYUnits+'/'+self.selectedXUnits
            title       = self._windowTitle+' - '+'FFT'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.fftCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.fftPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.fftGetData(), # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:
            self.fftClosePlot()



    def fftClosePlot(self) -> None:
        if hasattr(self, 'fftPlotRef'):
            self.signalClose1dPlot.emit(self.fftPlotRef)



    def fftNoDcGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
        y = np.abs(np.fft.fft(self.selectedY))[x>=0][1:]
        x = x[x>=0][1:]

        return x, y



    def fftNoDcUpdateCurve(self) -> None:
        if hasattr(self, 'fftNoDcPlotRef'):
            x, y = self.fftNoDcGetData()
            self.signalUpdateCurve.emit(self.fftNoDcPlotRef,
                                        self.fftNoDcCurveId,
                                        '',
                                        x,
                                        y,
                                        False,
                                        False)



    def clickFFTnoDC(self) -> None:

        if self.ui.checkBoxFFTnoDC.isChecked():

            self.fftNoDcCurveId = self.selectedYLabel+'fftnodc'
            self.fftNoDcPlotRef = self.plotRef+'fftnodc'
            xLabelText  = '1/'+self.selectedXLabel
            xLabelUnits = '1/'+self.selectedXUnits
            yLabelText  = 'FFT NO DC'+'( '+self.selectedYLabel+' )'
            yLabelUnits = self.selectedYUnits+'/'+self.selectedXUnits
            title       = self._windowTitle+' - '+'FFT NO DC'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.fftNoDcCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.fftNoDcPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.fftNoDcGetData(), # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:
            self.fftNoDcClosePlot()



    def fftNoDcClosePlot(self) -> None:
        if hasattr(self, 'fftNoDcPlotRef'):
            self.signalClose1dPlot.emit(self.fftNoDcPlotRef)



    def ifftGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
        y = np.abs(np.fft.ifft(self.selectedY))[x>=0]
        x = x[x>=0]

        return x, y



    def ifftUpdateCurve(self) -> None:
        if hasattr(self, 'ifftPlotRef'):
            x, y = self.ifftGetData()
            self.signalUpdateCurve.emit(self.ifftPlotRef,
                                        self.ifftCurveId,
                                        '',
                                        x,
                                        y,
                                        False,
                                        False)


    def clickIFFT(self) -> None:

        if self.ui.checkBoxIFFT.isChecked():

            self.ifftCurveId = self.selectedYLabel+'ifft'
            self.ifftPlotRef = self.plotRef+'ifft'
            xLabelText  = '1/'+self.selectedXLabel
            xLabelUnits = '1/'+self.selectedXUnits
            yLabelText  = 'IFFT'+'( '+self.selectedYLabel+' )'
            yLabelUnits = self.selectedYUnits+'/'+self.selectedXUnits
            title       = self._windowTitle+' - '+'IFFT'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.ifftCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.ifftPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.ifftGetData(), # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:
            self.ifftClosePlot()



    def ifftClosePlot(self) -> None:
        if hasattr(self, 'ifftPlotRef'):
            self.signalClose1dPlot.emit(self.ifftPlotRef)

