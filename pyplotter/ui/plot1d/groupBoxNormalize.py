# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
import numpy as np
from typing import Tuple

from .groupBoxNormalizeUi import Ui_GroupBoxNormalize
from ...sources.pyqtgraph import pg


class GroupBoxNormalize(QtWidgets.QGroupBox, Ui_GroupBoxNormalize):


    signalUpdateCurve = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
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

        self.checkBoxUnwrap.clicked.connect(self.clickUnwrap)
        self.checkBoxRemoveSlope.clicked.connect(self.clickRemoveSlope)

    ####################################
    #
    #           Easy access to plot labels
    #
    ####################################

    @property
    def xLabelText(self) -> str:
        return self.plotItem.axes['bottom']['item'].labelText

    @property
    def xLabelUnits(self) -> str:
        return self.plotItem.axes['bottom']['item'].labelUnits

    @property
    def yLabelText(self) -> str:
        return self.plotItem.axes['left']['item'].labelText

    @property
    def yLabelUnits(self) -> str:
        return self.plotItem.axes['left']['item'].labelUnits


    ####################################
    #
    #           Slots
    #
    ####################################




    @QtCore.pyqtSlot(bool)
    def slotCheckBoxUnwrapSetChecked(self, state: bool):
        self.checkBoxUnwrap.setChecked(state)
        del(self.unwrapPlotRef)
        del(self.unwrapCurveId)



    @QtCore.pyqtSlot(bool)
    def slotCheckBoxRemoveSlopeSetChecked(self, state: bool):
        self.checkBoxRemoveSlope.setChecked(state)
        del(self.removeSlopePlotRef)
        del(self.removeSlopeCurveId)



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
    def slotUnwrapUpdate(self):
        self.unwrapUpdateCurve()



    @QtCore.pyqtSlot()
    def slotRemoveSlopeUpdate(self):
        self.removeSlopeUpdateCurve()



    ####################################
    #
    #           Slot to close plot
    #
    ####################################


    @QtCore.pyqtSlot()
    def slotUnwrapClosePlot(self):
        self.unwrapClosePlot()



    @QtCore.pyqtSlot()
    def slotRemoveSlopeClosePlot(self):
        self.removeSlopeClosePlot()



    ####################################
    #
    #           Method to related to normalization
    #
    ####################################



    def unwrapGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        return self.selectedX, np.unwrap(self.selectedY)



    def unwrapUpdateCurve(self) -> None:
        if hasattr(self, 'unwrapPlotRef'):
            x, y = self.unwrapGetData()
            self.signalUpdateCurve.emit(self.unwrapPlotRef,
                                        self.unwrapCurveId,
                                        '',
                                        x,
                                        y,
                                        False,
                                        False)



    def clickUnwrap(self) -> None:

        # If user wants to plot the unwrap, we add a new plotWindow
        if self.checkBoxUnwrap.isChecked():

            yLabelText         = 'Unwrap({})'.format(self.yLabelText)
            title              = self._windowTitle+' - unwrap'
            self.unwrapCurveId = self.selectedYLabel+'unwrap'
            self.unwrapPlotRef = self.plotRef+'unwrap'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.unwrapCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.unwrapPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.unwrapGetData(), # data
                                               self.xLabelText, # xLabelText
                                               self.xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               self.yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        # Otherwise, we close the existing one
        else:
            self.unwrapClosePlot()



    def unwrapClosePlot(self) -> None:
        if hasattr(self, 'unwrapPlotRef'):
            self.signalClose1dPlot.emit(self.unwrapPlotRef)



    def removeSlopeGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        return (self.selectedX,
                self.selectedY-np.polyfit(self.selectedX, self.selectedY, 1)[0]*self.selectedX)



    def removeSlopeUpdateCurve(self) -> None:
        if hasattr(self, 'removeSlopePlotRef'):
            x, y = self.removeSlopeGetData()
            self.signalUpdateCurve.emit(self.removeSlopePlotRef,
                                        self.removeSlopeCurveId,
                                        '',
                                        x,
                                        y,
                                        False,
                                        False)



    def clickRemoveSlope(self) -> None:

        # If user wants to plot the unslop, we add a new plotWindow
        if self.checkBoxRemoveSlope.isChecked():

            yLabelText  = 'Unslop({})'.format(self.yLabelText)
            title       = self._windowTitle+' - unslop'
            self.removeSlopeCurveId     = self.selectedYLabel+'unslop'
            self.removeSlopePlotRef     = self.plotRef+'unslop'

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.removeSlopeCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.removeSlopePlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.removeSlopeGetData(), # data
                                               self.xLabelText, # xLabelText
                                               self.xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               self.yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        # Otherwise, we close the existing one
        else:
            self.removeSlopeClosePlot()



    def removeSlopeClosePlot(self) -> None:
        if hasattr(self, 'removeSlopePlotRef'):
            self.signalClose1dPlot.emit(self.removeSlopePlotRef)


