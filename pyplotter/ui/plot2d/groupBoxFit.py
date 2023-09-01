# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import inspect
import lmfit

from ...sources.pyqtgraph import pg
from . import dialogFit
from ...sources.config import loadConfigCurrent


class GroupBoxFit(QtWidgets.QGroupBox):

    ## To the main
    # Add a new plot
    signal2MainWindowAddPlot = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)
    signalClose2dPlot = QtCore.pyqtSignal(str, str)

    ## To the 2d plot displaying the fit result
    # Update the data
    signalUpdate2dFitResult = QtCore.pyqtSignal(str, np.ndarray, np.ndarray, np.ndarray)

    # To the 2d widget plot
    signalAddROI = QtCore.pyqtSignal()
    signalRemoveROI = QtCore.pyqtSignal()

    # To the fit dialog
    signalFit = QtCore.pyqtSignal(np.ndarray, np.ndarray, np.ndarray)
    signalFitError = QtCore.pyqtSignal()


    def __init__(self, parent: QtWidgets.QGroupBox,
                       plotRef: str,
                       plotItem: pg.PlotItem,
                       xLabel: str,
                       yLabel: str,
                       zLabel: str,
                       xUnit: str,
                       yUnit: str,
                       zUnit: str,
                       windowTitle: str,
                       databaseAbsPath: str) -> None:

        QtWidgets.QGroupBox.__init__(self, parent)


        self.config = loadConfigCurrent()

        self.plotItem = plotItem
        self.plotRef = plotRef


        self.xLabel = xLabel
        self.yLabel = yLabel
        self.zLabel = zLabel

        self.xUnit = xUnit
        self.yUnit = yUnit
        self.zUnit = zUnit

        self._windowTitle = windowTitle
        self.databaseAbsPath = databaseAbsPath

        # Build GUI
        fontBold = QtGui.QFont()
        fontBold.setBold(True)
        fontBold.setWeight(75)
        self.setFont(fontBold)

        font = QtGui.QFont()
        font.setBold(False)
        font.setPointSize(8)

        self.setTitle('Fit')

        self.verticalLayoutFitModel = QtWidgets.QVBoxLayout(self)
        horizon = QtWidgets.QHBoxLayout()
        self.checkbox = QtWidgets.QCheckBox('Select data for fit')
        self.checkbox.stateChanged.connect(self.checkboxStateChanged)
        self.checkbox.setFont(font)
        # label = QtWidgets.QLabel('Select data for fit')
        horizon.addWidget(self.checkbox)
        # horizon.addWidget(label)
        horizon.addSpacerItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.verticalLayoutFitModel.addLayout(horizon)
        self.comboBoxFit = QtWidgets.QComboBox(self)
        self.comboBoxFit.setEnabled(False)

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



    def checkboxStateChanged(self):

        # If checked:
        #   - we add a ROI
        #   - we enable the fit comboBox
        if self.checkbox.isChecked():

            self.signalAddROI.emit()
            self.comboBoxFit.setEnabled(True)

        # If unchecked:
        #   - We remove the ROI
        #   - We disable the fit comboxBox
        #   - We close fit
        else:
            self.signalRemoveROI.emit()
            self.comboBoxFit.setEnabled(False)
            self.fitClose()



    def comboBoxFitIndexChanched(self) -> None:
        """
        Method called when user click on a fitModel.
        Launch a fit of the data using the chosen model and display the results.
        """

        # If a fit is already plotted, we remove it before plotting a new
        # one without trigering new event
        currentIndex = self.comboBoxFit.currentIndex()
        if hasattr(self, 'dialog'):
            self.fitClose()

        self.comboBoxFit.blockSignals(True)
        self.comboBoxFit.setCurrentIndex(currentIndex)
        self.comboBoxFit.blockSignals(False)

        # If the user want to remove all fit
        if self.comboBoxFit.currentText()=='None':
            return

        # Find which model has been chosed and instance it
        _class = getattr(dialogFit, self.comboBoxFit.currentData())
        self.dialog = _class(parent=self)

        # From groupBox to dialog
        self.signalFit.connect(self.dialog.ffit)
        self.signalFitError.connect(self.dialog.fitError)

        # To dialog to groupBox
        self.dialog.signalFitResult.connect(self.fitGetResult)
        self.dialog.signalCloseDialog.connect(self.slotCloseDialog)

        # Send signal to perform fit and send results to fitGetResult
        self.signalFit.emit(self.xData, self.yData, self.zData)



    ####################################
    #
    #           Slots
    #
    ####################################



    @QtCore.pyqtSlot(np.ndarray, np.ndarray, np.ndarray)
    def updateData(self, xData: np.ndarray,
                         yData: np.ndarray,
                         zData: np.ndarray,) -> None:
        """
        Called from the 2d plot when the data selected for fit has been changed.
        """

        self.xData = xData
        self.yData = yData
        self.zData = zData

        # If a fit is detected, we update it
        if hasattr(self, 'curveIdFit'):
            self.signalFit.emit(self.xData, self.yData, self.zData)



    QtCore.pyqtSlot(np.ndarray, np.ndarray, np.ndarray, lmfit.Parameters)
    def fitGetResult(self, x: np.ndarray,
                           y: np.ndarray,
                           z: np.ndarray,
                           p: lmfit.Parameters) -> None:
        """
        Called from the fit dialog when a fit has been succesful

        Args:
            x: Data used in the fit
            y: Data used in the fit
            z: Data used in the fit
            p: lmfit parameters after minimization
        """

        # If there is no fit plot, we create one
        if not hasattr(self, 'curveIdFit'):

            self.curveIdFit = self.yLabel+'2dfit'
            self.plotRefFit = self.plotRef+'2dfit'
            title           = self._windowTitle+' - 2dfit'

            # Show the 2d fit
            self.signal2MainWindowAddPlot.emit(1, # fake ruinId
                                               self.curveIdFit, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.plotRefFit, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               (x, y, z), # data
                                               self.xLabel, # xLabelText
                                               self.xUnit, # xLabelUnits
                                               self.yLabel, # yLabelText
                                               self.yUnit, # yLabelUnits
                                               self.zLabel, # zLabelText
                                               self.zUnit) # zLabelUnits
        else:
            self.signalUpdate2dFitResult.emit(self.plotRefFit,
                                              x,
                                              y,
                                              z)

    @QtCore.pyqtSlot()
    def slotCloseDialog(self) -> None:
        """
        Called when user close the fit dialog
        """
        self.fitClose()



    def fitClose(self) -> None:
        """
        Call when we close a fit.
        Take care of closing everything properly and to erase references.
        """

        # We remove the curve
        if hasattr(self, 'curveIdFit'):

            self.signalClose2dPlot.emit(self.plotRefFit,
                                        self.curveIdFit)

            # Delete the reference
            del(self.curveIdFit)
            del(self.plotRefFit)

        # We close the dialog
        if hasattr(self, 'dialog'):
            # We reset the comboBox without triggering event
            self.comboBoxFit.blockSignals(True)
            self.comboBoxFit.setCurrentIndex(0)
            self.comboBoxFit.blockSignals(False)

            if self.dialog.isVisible():
                self.dialog.close()
            else:
            # Delete the reference
                del(self.dialog)
