# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import inspect

from ...sources.pyqtgraph import pg
from . import dialogFiltering


class GroupBoxFiltering(QtWidgets.QGroupBox):


    signalAddPlotDataItem    = QtCore.pyqtSignal(np.ndarray, np.ndarray, str, str, str, str, str, str, bool, bool)
    signalUpdatePlotDataItem = QtCore.pyqtSignal(np.ndarray, np.ndarray, str, str, bool, bool)
    signalRemovePlotDataItem = QtCore.pyqtSignal(str, str)

    dialogRef: dict

    def __init__(self, parent: QtWidgets.QGroupBox,
                       plotRef: str,
                       plotItem: pg.PlotItem) -> None:

        QtWidgets.QGroupBox.__init__(self, parent)

        self.plotItem = plotItem
        self.plotRef = plotRef

        # Build GUI
        self.setEnabled(False)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.setFont(font)
        self.setTitle('Filtering')

        self.verticalLayoutFilteringModel = QtWidgets.QVBoxLayout(self)
        self.comboBoxFiltering = QtWidgets.QComboBox(self)

        # Get list of fit model
        listClasses = [m[0] for m in inspect.getmembers(dialogFiltering, inspect.isclass) if 'runFiltering' in [*m[1].__dict__.keys()]]

        self.comboBoxFiltering.addItem('None')
        for i, j in enumerate(listClasses):

            _class = getattr(dialogFiltering, j)
            font = QtGui.QFont()
            font.setPointSize(8)
            font.setBold(False)
            self.comboBoxFiltering.setFont(font)
            self.comboBoxFiltering.addItem(_class.comboBoxLabel,
                                           userData=j)

        self.comboBoxFiltering.currentIndexChanged.connect(self.comboBoxFilteringIndexChanched)
        self.verticalLayoutFilteringModel.addWidget(self.comboBoxFiltering)



    def comboBoxFilteringIndexChanched(self) -> None:
        """
        Method called when user click on a radioButton of a fitModel.
        Launch a fit of the data using the chosen model and display the results.
        """
        # If a fit curve is already plotted, we remove it before plotting a new
        # one without trigering new event
        currentIndex = self.comboBoxFiltering.currentIndex()
        if hasattr(self, 'dialogRef'):
            self.filteringClose()

        self.comboBoxFiltering.blockSignals(True)
        self.comboBoxFiltering.setCurrentIndex(currentIndex)
        self.comboBoxFiltering.blockSignals(False)

        # If the user want to remove all fit
        if self.comboBoxFiltering.currentText()=='None':
            return

        # Find which model has been chosed and instance it
        _class = getattr(dialogFiltering, self.comboBoxFiltering.currentData())
        self.dialog = _class(parent=self,
                        xData=self.selectedX,
                        yData=self.selectedY)

        self.dialog.signalCloseDialog.connect(self.slotCloseDialog)
        self.dialog.signalUpdateDialog.connect(self.slotUpdateDialog)
        self.dialogRef = {'dialog' : self.dialog,
                          'comboBox': self.comboBoxFiltering}
        self.curveIdFiltering = self.plotRef+'filtering'
        # We catch possible error occuring during the filtering procedure
        try:
            x, y, legend =  self.dialog.runFiltering()
            # Plot fit curve
            self.signalAddPlotDataItem.emit(x, # x
                                            y, # y
                                            self.curveIdFiltering, # curveId
                                            self.selectedXLabel, # curveXLabel
                                            self.selectedXUnits, # curveXUnits
                                            'Filtered: '+self.comboBoxFiltering.currentText(), # curveYLabel
                                            self.selectedYUnits, # curveYUnits
                                            legend, # curveLegend
                                            True, # showInLegend
                                            False) # hidden
        except:
            pass



    def filteringUpdate(self) -> None:

        if hasattr(self, 'curveIdFiltering'):
            # We catch possible error occuring during the filtering procedure
            try:
                x, y, legend =  self.dialog.runFiltering()
                self.signalUpdatePlotDataItem.emit(x, # x
                                                   y, # y
                                                   self.curveIdFiltering, # curveId
                                                   legend, # curveLegend
                                                   False, # autoRange
                                                   False) # interactionUpdateAll
            except:
                pass



    ####################################
    #
    #           Slots
    #
    ####################################



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

        if hasattr(self, 'dialog'):
            self.dialog.xData = self.selectedX
            self.dialog.yData = self.selectedY




    @QtCore.pyqtSlot()
    def slotFilteringUpdate(self):
        self.filteringUpdate()


    @QtCore.pyqtSlot()
    def slotFilteringClose(self):
        self.filteringClose()



    @QtCore.pyqtSlot()
    def slotUpdateDialog(self) -> None:
        self.filteringUpdate()



    @QtCore.pyqtSlot()
    def slotCloseDialog(self) -> None:
        self.filteringClose()



    def filteringClose(self) -> None:

        # We remove the curve
        if hasattr(self, 'curveIdFiltering'):

            self.signalRemovePlotDataItem.emit(self.plotRef,
                                               self.curveIdFiltering)

            # Delete the reference
            del(self.curveIdFiltering)

        # We close the dialog
        if hasattr(self, 'dialogRef'):
            # We reset the comboBox without triggering event
            self.dialogRef['comboBox'].blockSignals(True)
            self.dialogRef['comboBox'].setCurrentIndex(0)
            self.dialogRef['comboBox'].blockSignals(False)

            if self.dialogRef['dialog'].isVisible():
                self.dialogRef['dialog'].close()
            else:
            # Delete the reference
                del(self.dialogRef)
