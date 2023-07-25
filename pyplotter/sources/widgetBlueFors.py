# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtTest, QtWidgets, QtCore
import os
import numpy as np
import pandas as pd
from typing import Optional
from.functions import pandasTimestamp2Int, isBlueForsFolder, clearTableWidget

from .config import loadConfigCurrent
config = loadConfigCurrent()


class WidgetBlueFors(QtWidgets.QWidget):


    signalClearTableWidgetDatabase = QtCore.pyqtSignal()
    signalClearTableWidgetParameter = QtCore.pyqtSignal()
    signalClearSnapshot = QtCore.pyqtSignal()
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun = QtCore.pyqtSignal(str)
    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)

    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)

    signalUpdateProgressBar = QtCore.pyqtSignal(QtWidgets.QProgressBar, float, str)
    signalRemoveProgressBar = QtCore.pyqtSignal(QtWidgets.QProgressBar)
    signalFillTableWidgetParameter = QtCore.pyqtSignal(int, list, dict, dict, str, str, str, str, bool)
    signalLoadedDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str, bool)

    def __init__(self, parent):
        """
        Class handling the reading of csv file.
        """

        super(WidgetBlueFors, self).__init__(parent)



    @QtCore.pyqtSlot(str, bool, QtWidgets.QProgressBar)
    def blueForsLoad(self, absPath: str,
                           doubleClick: bool,
                           progressBar: QtWidgets.QProgressBar) -> None:

        folderName = os.path.basename(absPath)

        self.signalSendStatusBarMessage.emit('Loading {}'.format(folderName),
                                             'orange')

        # Clean GUI
        self.signalLineEditSnapshotEnabled.emit(False)
        self.signalLabelSnapshotEnabled.emit(False)
        self.signalClearTableWidgetDatabase.emit()
        self.signalClearTableWidgetParameter.emit()
        self.signalClearSnapshot.emit()
        self.signalUpdateLabelCurrentSnapshot.emit('')
        self.signalUpdateLabelCurrentRun.emit('')


        self.paramDependentList = []
        progress = 0.
        progressIteration = 1/22
        for file in sorted(os.listdir(absPath)):

            fileName = file[:-13]
            filePath = os.path.join(absPath, file)

            # We only show file handled by the plotter
            if fileName in config.keys():

                # Maxigauges file (all pressure gauges)
                if fileName=='maxigauge':

                    df = pd.read_csv(filePath,
                                     delimiter=',',
                                     names=['date', 'time',
                                         'ch1_name', 'ch1_void1', 'ch1_status', 'ch1_pressure', 'ch1_void2', 'ch1_void3',
                                         'ch2_name', 'ch2_void1', 'ch2_status', 'ch2_pressure', 'ch2_void2', 'ch2_void3',
                                         'ch3_name', 'ch3_void1', 'ch3_status', 'ch3_pressure', 'ch3_void2', 'ch3_void3',
                                         'ch4_name', 'ch4_void1', 'ch4_status', 'ch4_pressure', 'ch4_void2', 'ch4_void3',
                                         'ch5_name', 'ch5_void1', 'ch5_status', 'ch5_pressure', 'ch5_void2', 'ch5_void3',
                                         'ch6_name', 'ch6_void1', 'ch6_status', 'ch6_pressure', 'ch6_void2', 'ch6_void3',
                                         'void'],
                                     header=None)

                    x = pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S'))

                    for i in range(1, 7):

                        self.signalUpdateProgressBar.emit(progressBar, progress, 'Downloading data: {:.0f}%'.format(progress*100))
                        progress += progressIteration

                        name = 'ch'+str(i)+'_pressure'
                        y = df[name].to_numpy()*1e-3
                        self.paramDependentList.append({'depends_on' : ['time'],
                                                        'name'  : config[fileName][name[:3]]['labelText'],
                                                        'label' : config[fileName][name[:3]]['labelText'],
                                                        'x' : x,
                                                        'y' : y,
                                                        'unit' : config[fileName][name[:3]]['labelUnits']})
                else:

                    # Thermometers files
                    df = pd.read_csv(filePath,
                                     delimiter = ',',
                                     names     = ['date', 'time', 'y'],
                                     header    = None)

                    self.signalUpdateProgressBar.emit(progressBar, progress, 'Downloading data: {:.0f}%'.format(progress*100))
                    progress += progressIteration

                    # There is a space before the day
                    x = pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S'))
                    y = df['y'].to_numpy()*1e-3

                    self.paramDependentList.append({'depends_on' : ['time'],
                                                    'name'  : config[fileName]['labelText'],
                                                    'label' : config[fileName]['labelText'],
                                                    'x' : x,
                                                    'y' : y,
                                                    'unit' : config[fileName]['labelUnits']})


        self.signalFillTableWidgetParameter.emit(0, # runId
                                                 self.paramDependentList, # dependentList,
                                                 {}, # snapshotDict,
                                                 {i['name'] : None for i in self.paramDependentList}, # shapes
                                                 '', # experimentName
                                                 '', # runName
                                                 absPath, # fileAbsPath
                                                 'bluefors', # dataType
                                                 doubleClick) # doubleClick

        self.signalRemoveProgressBar.emit(progressBar)


    QtCore.pyqtSlot(str, str, str, str, str, int, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar)
    def loadData(self, curveId: str,
                       absPath: str,
                       dependentParamName: str,
                       plotRef: str,
                       plotTitle: str,
                       runId: int,
                       windowTitle: str,
                       cb: QtWidgets.QCheckBox,
                       progressBar: QtWidgets.QProgressBar) -> None:

        self.signalUpdateProgressBar.emit(progressBar, 100., 'Downloading data: 100%')

        xLabelText  = 'Time'
        xLabelUnits = ''
        zLabelText  = ''
        zLabelUnits = ''

        for paramDependent in self.paramDependentList:
            if paramDependent['name'] == dependentParamName:
                data = (paramDependent['x'], paramDependent['y'])
                yLabelText  = paramDependent['label']
                yLabelUnits = paramDependent['unit']

        self.signalLoadedDataFull.emit(runId,
                                       curveId,
                                       plotTitle,
                                       windowTitle,
                                       plotRef,
                                       absPath,
                                       cb,
                                       progressBar,
                                       data,
                                       xLabelText,
                                       xLabelUnits,
                                       yLabelText,
                                       yLabelUnits,
                                       zLabelText,
                                       zLabelUnits,
                                       True) # pg.DateAxisItem
