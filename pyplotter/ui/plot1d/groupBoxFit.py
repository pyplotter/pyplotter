# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import inspect

from ...sources.pyqtgraph import pg
from . import dialogFit


class GroupBoxFit(QtWidgets.QGroupBox):


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
        self.setTitle('Fit')

        self.verticalLayoutFitModel = QtWidgets.QVBoxLayout(self)
        self.comboBoxFit = QtWidgets.QComboBox(self)

        # Get list of fit model
        listClasses = [m[0] for m in inspect.getmembers(dialogFit, inspect.isclass) if 'getInitialParams' in [*m[1].__dict__.keys()]]

        self.comboBoxFit.addItem('None')
        for i, j in enumerate(listClasses):

            _class = getattr(dialogFit, j)
            font = QtGui.QFont()
            font.setPointSize(8)
            font.setBold(False)
            self.comboBoxFit.setFont(font)
            self.comboBoxFit.addItem(_class.displayedLabel,
                                     userData=j)

        self.comboBoxFit.currentIndexChanged.connect(self.comboBoxFitIndexChanched)
        self.verticalLayoutFitModel.addWidget(self.comboBoxFit)



    def comboBoxFitIndexChanched(self) -> None:
        """
        Method called when user click on a radioButton of a fitModel.
        Launch a fit of the data using the chosen model and display the results.
        """
        # If a fit curve is already plotted, we remove it before plotting a new
        # one without trigering new event
        currentIndex = self.comboBoxFit.currentIndex()
        if hasattr(self, 'dialogRef'):
            self.fitClose()

        self.comboBoxFit.blockSignals(True)
        self.comboBoxFit.setCurrentIndex(currentIndex)
        self.comboBoxFit.blockSignals(False)

        # If the user want to remove all fit
        if self.comboBoxFit.currentText()=='None':
            return

        # Find which model has been chosed and instance it
        _class = getattr(dialogFit, self.comboBoxFit.currentData())
        self.dialog = _class(parent=self,
                        xData=self.selectedX,
                        yData=self.selectedY,
                        xUnits=self.plotItem.axes['bottom']['item'].labelUnits,
                        yUnits=self.plotItem.axes['left']['item'].labelUnits)

        self.dialog.signalCloseDialog.connect(self.slotCloseDialog)
        self.dialog.signalUpdateDialog.connect(self.slotUpdateDialog)
        self.dialogRef = {'dialog' : self.dialog,
                          'comboBox': self.comboBoxFit}
        self.curveIdFit = self.plotRef+'fit'
        # We catch possible error occuring during the fiting procedure
        try:
            x, y, params =  self.dialog.ffit()
            # Plot fit curve
            self.signalAddPlotDataItem.emit(x, # x
                                            y, # y
                                            self.curveIdFit, # curveId
                                            self.selectedXLabel, # curveXLabel
                                            self.selectedXUnits, # curveXUnits
                                            'Fit: '+self.comboBoxFit.currentText(), # curveYLabel
                                            self.selectedYUnits, # curveYUnits
                                            self.dialog.displayedLegend(params), # curveLegend
                                            True, # showInLegend
                                            False) # hidden
        except Exception as e:
            print(e)
            self.dialog.fitError()



    def fitUpdate(self) -> None:

        if hasattr(self, 'curveIdFit'):
            # We catch possible error occuring during the fiting procedure
            try:
                x, y, params =  self.dialog.ffit()
                self.signalUpdatePlotDataItem.emit(x, # x
                                                   y, # y
                                                   self.curveIdFit, # curveId
                                                   self.dialog.displayedLegend(params), # curveLegend
                                                   False, # autoRange
                                                   False) # interactionUpdateAll
            except:
                self.dialog.fitError()



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
    def slotFitUpdate(self):
        self.fitUpdate()



    @QtCore.pyqtSlot()
    def slotFitClose(self):
        self.fitClose()



    @QtCore.pyqtSlot()
    def slotCloseDialog(self) -> None:
        self.fitClose()



    @QtCore.pyqtSlot()
    def slotUpdateDialog(self) -> None:
        self.fitUpdate()



    def fitClose(self) -> None:

        # We remove the curve
        if hasattr(self, 'curveIdFit'):

            self.signalRemovePlotDataItem.emit(self.plotRef,
                                               self.curveIdFit)

            # Delete the reference
            del(self.curveIdFit)

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
