from PyQt5 import QtWidgets, QtCore
import os
import numpy as np


class WidgetNpz(QtWidgets.QWidget):


    ## Bunch of signals to clean the main window when a user click on the npz
    ## file in the tableWidgetFolder
    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)
    signalClearTableWidgetDatabase   = QtCore.pyqtSignal()
    signalClearTableWidgetParameter  = QtCore.pyqtSignal()
    signalClearSnapshot              = QtCore.pyqtSignal()
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun      = QtCore.pyqtSignal(str)

    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)


    signalUpdateProgressBar = QtCore.pyqtSignal(int, float, str)
    signalRemoveProgressBar = QtCore.pyqtSignal(int)
    signalFillTableWidgetParameter = QtCore.pyqtSignal(int, list, dict, dict, str, str, str, str, bool)
    signalLoadedDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QCheckBox, int, tuple, str, str, str, str, str, str, bool)

    # Send to the tableWidgetParameter
    # Signal that the npz y parameter can't be plotter as function of the x one
    # since they do not share the same size
    signalNpzIncorrectSize = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        """
        Class handling the reading of npz file.
        """

        super(WidgetNpz, self).__init__(parent)


    @QtCore.pyqtSlot(str, bool, int)
    def npzLoad(self, fileAbsPath: str,
                      doubleClick: bool,
                      progressBarId: int) -> None:
        """
        Signal from the tableWidgetFolder when a user click on a npz file.
        The signal went trough the StatusBar to display a progressBar.

        Get the dependent and independent parameters from the npz file and
        send it to the tableWidgetParameter.

        Args:
            fileAbsPath: Absolute path of the npz file
            doubleClick: If the user double click on the file or not.
                If yes, the first dependent parameter is launched automatically.
            progressBarId:
        """

        fileName = os.path.basename(fileAbsPath)

        self.signalSendStatusBarMessage.emit('Loading {}'.format(fileName),
                                             'orange')

        # Clean GUI
        self.signalLineEditSnapshotEnabled.emit(False)
        self.signalLabelSnapshotEnabled.emit(False)
        self.signalClearTableWidgetDatabase.emit()
        self.signalClearTableWidgetParameter.emit()
        self.signalClearSnapshot.emit()
        self.signalUpdateLabelCurrentSnapshot.emit('')
        self.signalUpdateLabelCurrentRun.emit('')

        # Get info from the npz file
        self.paramDependentList = []
        with np.load(fileAbsPath) as file:
            self.independentParameter = list(file.keys())[0]
            x = list(file.values())[0]

            for name, y in list(file.items())[1:]:
                self.paramDependentList.append({'depends_on' : [self.independentParameter],
                                                'label' : name,
                                                'x' : x,
                                                'y' : y,
                                                'shape' : len(y),
                                                'unit' : '',
                                                'name' : name})

        # Send info to the tableWidgetParameter
        self.signalFillTableWidgetParameter.emit(0, # runId
                                                 self.paramDependentList, # dependentList,
                                                 {}, # snapshotDict,
                                                 {i['name'] : i['shape'] for i in self.paramDependentList}, # shapes
                                                 '', # experimentName
                                                 '', # runName
                                                 fileAbsPath, # fileAbsPath
                                                 'npz', # dataType
                                                 doubleClick) # doubleClick

        # Once all is done, we remove the progressBar
        self.signalRemoveProgressBar.emit(progressBarId)



    QtCore.pyqtSlot(str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)
    def loadData(self, curveId: str,
                       fileAbsPath: str,
                       dependentParamName: str,
                       plotRef: str,
                       plotTitle: str,
                       runId: int,
                       windowTitle: str,
                       cb: QtWidgets.QCheckBox,
                       progressBarId: int) -> None:
        """
        Called from the tableWidgetParameter when a user click on a dependent
        parameter.
        The signal went trough the StatusBar to display a progressBar.

        Get the asked dependent parameter data and send it to the mainWindow which
        will launch a 1d plot.

        Args:
            curveId: Id of the curve.
                See getCurveId from MainApp
            fileAbsPath: Absolute path of the npz file
            dependentParamName: name of the dependent parameter
            plotRef: Reference of the plot
            plotTitle: Plot title.
            runId: Id of the QCoDeS run.
            windowTitle: Window title.
            cb: TableWidgetParameter checkbox associated with the dependentParameter
            progressBarId: Id of the progress bar.
                See statusBar widget
        """

        # Since the data are already in memory
        self.signalUpdateProgressBar.emit(progressBarId, 100., 'Downloading data: 100%')

        # Get the data of the dependent parameter from memory
        for paramDependent in self.paramDependentList:
            if paramDependent['name'] == dependentParamName:
                data = (paramDependent['x'], paramDependent['y'])

        # Handle case where the x and y array doesn't have the same length
        if len(data[0])!=len(data[1]):
            self.signalSendStatusBarMessage.emit('x, y does not have the same length',
                                                 'red')
            self.signalRemoveProgressBar.emit(progressBarId)
            self.signalNpzIncorrectSize.emit(dependentParamName)
            return

        # Senfd
        xLabelText  = self.independentParameter
        xLabelUnits = ''
        yLabelText  = dependentParamName
        yLabelUnits = ''
        zLabelText  = ''
        zLabelUnits = ''

        # Send info to the mainWindow to launch 1d plot
        self.signalLoadedDataFull.emit(runId,
                                       curveId,
                                       plotTitle,
                                       windowTitle,
                                       plotRef,
                                       fileAbsPath,
                                       cb,
                                       progressBarId,
                                       data,
                                       xLabelText,
                                       xLabelUnits,
                                       yLabelText,
                                       yLabelUnits,
                                       zLabelText,
                                       zLabelUnits,
                                       False) # pg.DateAxisItem