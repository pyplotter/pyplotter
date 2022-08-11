# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
import numpy as np
from typing import Tuple
from scipy.integrate import cumtrapz

from .groupBoxCalculusUi import Ui_groupBoxCalculus
from ...sources.pyqtgraph import pg


class GroupBoxCalculus(QtWidgets.QGroupBox, Ui_groupBoxCalculus):


    signalUpdateCurve = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool)
    signal2MainWindowAddPlot   = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)
    signalClose1dPlot  = QtCore.pyqtSignal(str)


    def __init__(self, parent: QtWidgets.QGroupBox,
                       config: dict,
                       databaseAbsPath: str,
                       plotItem: pg.PlotItem,
                       plotRef:str,
                       windowTitle: str) -> None:

        QtWidgets.QGroupBox.__init__(self, parent)
        self.setupUi(self)

        self.config = config
        self.databaseAbsPath = databaseAbsPath
        self.plotItem = plotItem
        self.plotRef = plotRef
        self._windowTitle = windowTitle

        self.checkBoxDifferentiate.clicked.connect(self.clickDifferentiate)
        self.checkBoxIntegrate.clicked.connect(self.clickIntegrate)



    ####################################
    #
    #           Slots
    #
    ####################################



    @QtCore.pyqtSlot(bool)
    def slotCheckBoxDifferentiateSetChecked(self, state: bool):
        self.checkBoxDifferentiate.setChecked(state)
        del(self.differentiatePlotRef)
        del(self.differentiateCurveId)



    @QtCore.pyqtSlot(bool)
    def slotCheckBoxIntegrateSetChecked(self, state: bool):
        self.checkBoxIntegrate.setChecked(state)
        del(self.integratePlotRef)
        del(self.integrateCurveId)



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


    @QtCore.pyqtSlot()
    def slotDifferentiateUpdate(self):
        self.differentiateUpdateCurve()


    @QtCore.pyqtSlot()
    def slotIntegrateUpdate(self):
        self.integrateUpdateCurve()


    @QtCore.pyqtSlot()
    def slotDifferentiateClosePlot(self):
        self.differentiateClosePlot()


    @QtCore.pyqtSlot()
    def slotIntegrateClosePlot(self):
        self.integrateClosePlot()



    ####################################
    #
    #           Internal methods
    #
    ####################################






    def differentiateGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        return self.selectedX, np.gradient(self.selectedY, self.selectedX)



    def differentiateUpdateCurve(self) -> None:
        if hasattr(self, 'differentiatePlotRef'):
            x, y = self.differentiateGetData()
            self.signalUpdateCurve.emit(self.differentiatePlotRef,
                                        self.differentiateCurveId,
                                        '',
                                        x,
                                        y,
                                        False)



    def clickDifferentiate(self) -> None:
        """
        Method called when user click on the derivative checkbox.
        Add a plot containing the derivative of the chosen data.
        """

        # If user wants to plot the derivative, we add a new plotWindow
        if self.checkBoxDifferentiate.isChecked():

            xLabelText  = self.plotItem.axes['bottom']['item'].labelText
            xLabelUnits = self.plotItem.axes['bottom']['item'].labelUnits
            yLabelText  = '∂('+self.selectedYLabel+')/∂('+xLabelText+')'
            yLabelUnits = self.selectedYUnits+'/'+xLabelUnits

            title       = self._windowTitle+' - derivative'
            self.differentiateCurveId     = self.selectedYLabel+'derivative'
            self.differentiatePlotRef     = self.plotRef+'derivative'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.differentiateCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.differentiatePlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.differentiateGetData(), # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits

        # Otherwise, we close the existing one
        else:
            self.differentiateClosePlot()



    def differentiateClosePlot(self) -> None:
        if hasattr(self, 'differentiatePlotRef'):
            self.signalClose1dPlot.emit(self.differentiatePlotRef)



    def integrateGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        return self.selectedX, cumtrapz(self.selectedY, self.selectedX, initial=0)



    def integrateUpdateCurve(self) -> None:
        if hasattr(self, 'integratePlotRef'):
            x, y = self.integrateGetData()
            self.signalUpdateCurve.emit(self.integratePlotRef,
                                        self.integrateCurveId,
                                        '',
                                        x,
                                        y,
                                        False)



    def clickIntegrate(self) -> None:
        """
        Method called when user click on the integrate checkbox.
        Add a plot containing the primitive of the chosen data.
        """

        # If user wants to plot the primitive, we add a new plotWindow
        if self.checkBoxIntegrate.isChecked():

            xLabelText  = self.plotItem.axes['bottom']['item'].labelText
            xLabelUnits = self.plotItem.axes['bottom']['item'].labelUnits
            yLabelText  = '∫ '+self.selectedYLabel+'  d '+xLabelText
            yLabelUnits = self.selectedYUnits+' x '+xLabelUnits

            title   = self._windowTitle+' - primitive'
            self.integrateCurveId = self.selectedYLabel+'primitive'
            self.integratePlotRef = self.plotRef+'primitive'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.integrateCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.integratePlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.integrateGetData(), # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        # Otherwise, we close the existing one
        else:
            self.integrateClosePlot()



    def integrateClosePlot(self) -> None:
        if hasattr(self, 'integratePlotRef'):
            self.signalClose1dPlot.emit(self.integratePlotRef)


