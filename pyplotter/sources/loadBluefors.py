# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtTest
import os
import numpy as np
import pandas as pd
from typing import Optional

from .config import loadConfigCurrent
config = loadConfigCurrent()
class LoadBlueFors:


    def __init__(self, mainObject):
        """
        Class handling the reading of the blueFors logging files.

        Parameters
        ----------
        mainObject : dict
            Instance of the main, see MainApp.
        """

        super(LoadBlueFors, self).__init__()

        self.main = mainObject



    @staticmethod
    def pandasTimestamp2Int(dates: np.ndarray) -> np.ndarray:

        return (dates - pd.Timestamp('1970-01-01'))//pd.Timedelta('1s')



    @staticmethod
    def isBlueForsFolder(folderName : Optional[str]=None) -> bool:
        """
        Return True if a string follow blueFors log folder name pattern.

        Parameters
        ----------
        folderName : str
            Name of the folder

        Returns
        -------
        bool
            Return True if a string follow blueFors log folder name pattern.
        """

        if folderName is None:
            return False
        else:
            return len(folderName.split('-'))==3 and all([len(i)==2 for i in folderName.split('-')])==True



    @staticmethod
    def clearTableWidget(tableWidget : QtWidgets.QTableWidget) -> None:
        """
        Method to remove all row from a table widget.
        When this function is called, it should be followed by:
        tableWidget.setSortingEnabled(True)
        to allowed GUI sorting
        """

        tableWidget.setSortingEnabled(False)
        tableWidget.setRowCount(0)



    def blueForsFolderClicked(self, directory : str) -> None:
        """
        When user click on a BlueFors folder while browsing files

        Parameters
        ----------
        directory : str
            Absolute path of the BlueFors log folder.
        """

        ## Update label
        self.main.labelCurrentRun.clear()
        self.main.labelCurrentMetadata.clear()

        self.main.setStatusBarMessage('Loading BlueFors log')

        ## Fill the tableWidgetParameters with the run parameters

        # Clean GUI
        self.clearTableWidget(self.main.tableWidgetDataBase)
        self.clearTableWidget(self.main.tableWidgetParameters)
        self.main.tableWidgetDataBase.setSortingEnabled(True)
        self.main.tableWidgetParameters.setSortingEnabled(True)
        self.main.lineEditFilterSnapshot.cleanSnapshot()


        # Fill the table parameters with BlueFors info
        for file in sorted(os.listdir(directory)):

            fileName = file[:-13]

            # We only show file handled by the plotter
            if fileName in config.keys():
                fakeParamDependent = {'depends_on' : [0],
                                      'name'  : config[fileName]['labelText'],
                                      'label' : config[fileName]['labelText']}

                rowPosition = self.main.tableWidgetParameters.rowCount()
                self.main.tableWidgetParameters.insertRow(rowPosition)

                cb = QtWidgets.QCheckBox()

                # We check if that parameter is already plotted
                if config[fileName]['labelText'] == 'Pressure Gauges':
                    fakeParamDependent['name']  = 'Vacuum can'
                    fakeParamDependent['label'] = 'Vacuum can'
                if self.main.isParameterPlotted(fakeParamDependent):
                    cb.setChecked(True)
                if config[fileName]['labelText'] == 'Pressure Gauges':
                    fakeParamDependent['name']  = config[fileName]['labelText']
                    fakeParamDependent['label'] = config[fileName]['labelText']


                # We put a fake runId of value 0
                self.main.tableWidgetParameters.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem('0'))
                self.main.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
                self.main.tableWidgetParameters.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(config[fileName]['labelText']))

                runId       = 0
                curveId     = self.main.getCurveId(name=fakeParamDependent['name'],
                                                   runId=runId)
                plotTitle   = self.main.getPlotTitle()
                windowTitle = self.main.getWindowTitle(runId=runId)
                plotRef     = self.main.getPlotRef(fakeParamDependent)

                databaseAbsPath = os.path.normpath(directory).replace("\\", "/")

                # Each checkbox at its own event attached to it
                cb.toggled.connect(lambda cb              = cb,
                                          filePath        = os.path.join(directory, file),
                                          runId           = runId,
                                          curveId         = curveId,
                                          plotTitle       = plotTitle,
                                          windowTitle     = windowTitle,
                                          plotRef         = plotRef,
                                          databaseAbsPath = databaseAbsPath: self.blueForsLogClicked(cb,
                                                                                         filePath,
                                                                                         runId,
                                                                                         curveId,
                                                                                         plotTitle,
                                                                                         windowTitle,
                                                                                         plotRef,
                                                                                         databaseAbsPath))

        self.main.setStatusBarMessage('Ready')



    def blueForsLogClicked(self, cb              : QtWidgets.QCheckBox,
                                 filePath        : str,
                                 runId           : int,
                                 curveId         : str,
                                 plotTitle       : str,
                                 windowTitle     : str,
                                 plotRef         : str,
                                 databaseAbsPath : str) -> None:
        """
        When user clicked on BF log file.
        Basically, launch a 1d plot window.
        Handle the different "type" of BlueFors log file.

        Parameters
        ----------
        cb : QtWidgets.QCheckBox
            Clicked checkbox.
        filePath : str
            Path of the datafile.
        runId : int
            Data run id in the current database
        curveId : str
            Id of the curve, see getCurveId.
        plotTitle : str
            Plot title, see getPlotTitle.
        windowTitle : str
            Window title, see getWindowTitle.
        plotRef : str
            Reference of the plot, see getplotRef.
        """

        # Disable widget received for qcodes database
        self.main.lineEditFilterSnapshot.setEnabled(False)
        self.main.labelFilter.setEnabled(False)

        fileName = os.path.basename(os.path.normpath(filePath))[:-13]

        if cb:
            self.main.setStatusBarMessage('Loading BlueFors data')

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

                timeAxis = self.pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S'))

                for i in range(1, 7):

                    name = 'ch'+str(i)+'_pressure'

                    self.main.addPlot(plotRef        = plotRef,
                                      data           = (timeAxis, df[name]*1e-3),
                                      xLabelText     = 'Time',
                                      xLabelUnits    = '',
                                      yLabelText     = config[fileName][name[:3]]['labelText'],
                                      yLabelUnits    = config[fileName][name[:3]]['labelUnits'],
                                      runId          = runId,
                                      curveId        = curveId+name,
                                      plotTitle      = plotTitle,
                                      windowTitle    = windowTitle,
                                      timestampXAxis = True)

                    # and we set y log mode True
                    QtTest.QTest.qWait(100) # To avoid an overflow error

                # Once all is plotting we autorange
                self.main._plotRefs[plotRef].plotItem.vb.autoRange()
                self.main._plotRefs[plotRef].checkBoxLogY.toggle()

            # Thermometers files
            else:
                df = pd.read_csv(filePath,
                                 delimiter = ',',
                                 names     = ['date', 'time', 'y'],
                                 header    = None)

                # There is a space before the day
                timeAxis = self.pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S'))

                self.main.addPlot(plotRef         = plotRef,
                                  data            = (timeAxis, df['y']*1e-3),
                                  xLabelText      = 'Time',
                                  xLabelUnits     = '',
                                  yLabelText      = config[fileName]['labelText'],
                                  yLabelUnits     = config[fileName]['labelUnits'],
                                  runId           = runId,
                                  curveId         = curveId,
                                  plotTitle       = plotTitle,
                                  windowTitle     = windowTitle,
                                  timestampXAxis  = True,
                                  databaseAbsPath = databaseAbsPath)

        else:

            if fileName=='maxigauge':
                for i in range(1, 7):
                    name = 'ch'+str(i)+'_pressure'
                    self.main.removePlot(plotRef = plotRef,
                                         curveId = curveId+name)
            else:
                self.main.removePlot(plotRef = plotRef,
                                     curveId = curveId)

