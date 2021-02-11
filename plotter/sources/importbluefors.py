# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtTest
import os
import numpy as np
import pandas as pd
from typing import Callable, Optional, List

from .config import config
from ..ui.qtablewidgetkey import QTableWidgetKey



class ImportBlueFors:


    def __init__(self, plotRefs              : dict,
                       lineEditFilter        : QtWidgets.QLineEdit,
                       labelFilter           : QtWidgets.QLabel,
                       tableWidgetDataBase   : QTableWidgetKey,
                       tableWidgetParameters : QtWidgets.QTableWidget,
                       textEditMetadata      : QtWidgets.QTextEdit,
                       setStatusBarMessage   : Callable[[str, bool], None],
                       addPlot               : Callable[[str, List[np.ndarray],
                                                         str, str,
                                                         Optional[Callable],
                                                         Optional[str],
                                                         Optional[str],
                                                         Optional[int],
                                                         Optional[bool],
                                                         Optional[str],
                                                         Optional[str],
                                                         Optional[str],
                                                         Optional[bool],
                                                         Optional[bool],
                                                         Optional[str],
                                                         Optional[str]], None],
                       removePlot            : Callable[[str, str], None],
                       isParameterPlotted    : Callable[[str], bool],
                       getDataRef            : Callable[[None], str]):
        """
        Class handling the reading of the blueFors logging files.
        
        Parameters
        ----------
        plotRefs : dict
            Contains references to all window, see addPlot
        lineEditFilter : QtWidgets.QLineEdit
            LineEdit for the filter interaction.
        labelFilter : QtWidgets.QLabel
            Label for the filter interaction.
        tableWidgetDataBase : QTableWidgetKey
            Table where database info are displayed.
        tableWidgetParameters : QtWidgets.QTableWidget
            Table where parameters info are displayed.
        textEditMetadata : QtWidgets.QTextEdit
            TextEdit widget where metadata are displayed.
        setStatusBarMessage : Callable[[str, bool], None]
            Method to write messages on the statusBar.
        addPlot : Callable
            Method to add a plot, see mainApp.
        removePlot : Callable
            Method to remove a plot, see mainApp.
        isParameterPlotted : Callable[[str], bool]
            Return True if a parameter is already plotter, see mainApp.
        getDataRef : Callable[[None], str]
            Return an unique id for a set of data, see mainApp.
        """

        super(ImportBlueFors, self).__init__()

        self._plotRefs             = plotRefs
        self.lineEditFilter        = lineEditFilter
        self.labelFilter           = labelFilter
        self.tableWidgetDataBase   = tableWidgetDataBase
        self.tableWidgetParameters = tableWidgetParameters
        self.textEditMetadata      = textEditMetadata
        self.setStatusBarMessage   = setStatusBarMessage
        self.addPlot               = addPlot
        self.removePlot            = removePlot
        self.isParameterPlotted    = isParameterPlotted
        self.getDataRef            = getDataRef



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
        
        self.setStatusBarMessage('Loading BlueFors log')

        # Get the BF folder name
        bfName = os.path.basename(os.path.normpath(directory))


        ## Fill the tableWidgetParameters with the run parameters

        # Clean GUI
        self.clearTableWidget(self.tableWidgetDataBase)
        self.clearTableWidget(self.tableWidgetParameters)
        self.tableWidgetDataBase.setSortingEnabled(True)
        self.tableWidgetParameters.setSortingEnabled(True)
        self.textEditMetadata.clear()


        # Fill the table parameters with BlueFors info
        for file in sorted(os.listdir(directory)):
            
            fileName = file[:-13]
            
            # We only show file handled by the plotter
            if fileName in config.keys():
                rowPosition = self.tableWidgetParameters.rowCount()
                self.tableWidgetParameters.insertRow(rowPosition)

                cb = QtWidgets.QCheckBox()

                # We check if that parameter is already plotted
                if self.isParameterPlotted(config[fileName]):
                    cb.setChecked(True)

                # We put a fake runId of value 0
                self.tableWidgetParameters.setItem(rowPosition, 0, QtGui.QTableWidgetItem('0'))
                self.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
                self.tableWidgetParameters.setItem(rowPosition, 3, QtGui.QTableWidgetItem(fileName))

                # Each checkbox at its own event attached to it
                cb.toggled.connect(lambda cb       = cb,
                                          filePath = os.path.join(directory, file),
                                          plotRef  = self.getDataRef(): self.blueForsLogClicked(cb, filePath, plotRef))
            


        self.setStatusBarMessage('Ready')



    def blueForsLogClicked(self, cb       : QtWidgets.QCheckBox,
                                 filePath : str,
                                 plotRef  : str) -> None:
        """
        When user clicked on BF log file.
        Basically, launch a 1d plot window.
        Handle the different "type" of BlueFors log file.

        Parameters
        ----------
        cb : QtWidgets.QCheckBox
            Clicked checbox.
        filePath : str
            Path of the datafile.
        plotRef : str
            Reference of the plot, see getplotRef.
        """

        # Disable widget received for qcodes database
        self.lineEditFilter.setEnabled(False)
        self.labelFilter.setEnabled(False)

        fileName = os.path.basename(os.path.normpath(filePath))[:-13]

        if cb:
            self.setStatusBarMessage('Loading BlueFors data')
            
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

                df.index = pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S')
                
                for i in range(1, 7):
                    
                    name = 'ch'+str(i)+'_pressure'
                    
                    self.addPlot(plotRef     = plotRef,
                                 data        = (df[name].index.astype(np.int64).values//1e9, df[name]*1e-3),
                                 xLabelText  = 'Time',
                                 xLabelUnits = '',
                                 yLabelText  = config[fileName][name[:3]]['labelText'],
                                 yLabelUnits = config[fileName][name[:3]]['labelUnits'])
                
                # Once all is plotting we autorange
                self._plotRefs[plotRef].plotItem.vb.autoRange()

                # and we set y log mode True
                QtTest.QTest.qWait(100) # To avoid an overflow error
                self._plotRefs[plotRef].checkBoxLogY.toggle()

            # Thermometers files
            else:
                df = pd.read_csv(filePath,
                                 delimiter = ',',
                                 names     = ['date', 'time', 'y'],
                                 header    = None)

                # There is a space before the day
                df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')

                self.addPlot(plotRef    = plotRef,
                             data       = (df['y'].index.astype(np.int64).values//1e9, df['y']*1e-3),
                             xLabelText = 'Time',
                             xLabelUnits = '',
                             yLabelText  = config[fileName]['labelText'],
                             yLabelUnits = config[fileName]['labelUnits'])


        else:
            
            if fileName=='maxigauge':
                for i in range(1, 7):
                    name = 'ch'+str(i)+'_pressure'
                    self.removePlot(plotRef = plotRef,
                                    label   = config[fileName][name[:3]])
            else:
                self.removePlot(plotRef = plotRef,
                                label   = config[fileName])

