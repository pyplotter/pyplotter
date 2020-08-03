# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtTest
import os
import numpy as np
import pandas as pd

from sources.config import config

class ImportBlueFors:


    def __init__(self, mainObject):
        """
        Class handling the reading of the blueFors logging files
        """

        super(ImportBlueFors, self).__init__()

        self.main = mainObject



    @staticmethod
    def isBlueForsFolder(folderName : str) -> bool:
        """
        Return True if a string follow blueFors log folder name pattern.
        """
    
        return len(folderName.split('-'))==3 and all([len(i)==2 for i in folderName.split('-')]) == True



    def blueForsFolderClicked(self, directory : str) -> None:
        """
        When user click on a BlueFors folder while browsing files
        """
        
        self.main.setStatusBarMessage('Loading BlueFors log')

        # Get the BF folder name
        bfName = os.path.basename(os.path.normpath(directory))

        ## Update label
        self.main.labelCurrentRun.setText('BF log folder: '+bfName)
        self.main.labelPlotTypeCurrent.setText('1d')


        ## Fill the tableWidgetParameters with the run parameters

        # Clean GUI
        self.main.clearTableWidet(self.main.tableWidgetDataBase)
        self.main.clearTableWidet(self.main.tableWidgetParameters)
        self.main.tableWidgetDataBase.setSortingEnabled(True)
        self.main.tableWidgetParameters.setSortingEnabled(True)
        
        self.main.textEditMetadata.clear()


        for file in sorted(os.listdir(directory)):
            
            fileName = file[:-13]
            
            # We only show file handled by the plotter
            if fileName in config.keys():
                rowPosition = self.main.tableWidgetParameters.rowCount()
                self.main.tableWidgetParameters.insertRow(rowPosition)

                cb = QtWidgets.QCheckBox()

                # We check if that parameter is already plotted
                if self.main.isParameterPlotted(config[fileName]):
                    cb.setChecked(True)

                # We put a fake runId of value 0
                self.main.tableWidgetParameters.setItem(rowPosition, 0, QtGui.QTableWidgetItem('0'))
                self.main.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
                self.main.tableWidgetParameters.setItem(rowPosition, 3, QtGui.QTableWidgetItem(fileName))

                # Each checkbox at its own event attached to it
                cb.toggled.connect(lambda cb       = cb,
                                          filePath = os.path.join(directory, file),
                                          plotRef  = self.main.getPlotRef(): self.blueForsLogClicked(cb, filePath, plotRef))
            


        self.main.setStatusBarMessage('Ready')



    def blueForsLogClicked(self, cb : QtWidgets.QCheckBox,
                                 filePath : str,
                                 plotRef : str) -> None:
        """
        When user clicked on BF log file.
        Basically, launch a 1d plot window.
        """

        # Disable widget received for qcodes database
        self.main.lineEditFilter.setEnabled(False)
        self.main.labelFilter.setEnabled(False)

        fileName = os.path.basename(os.path.normpath(filePath))[:-13]

        if cb:
            self.main.setStatusBarMessage('Loading BlueFors data')
            
            # Maxigauges file (all pressure gauges)
            if fileName == 'maxigauge':

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
                    
                    self.main.startPlotting(plotRef = plotRef,
                                       data    = (df[name].index.astype(np.int64).values//1e9, df[name]),
                                       xLabel  = 'Time',
                                       yLabel  = config[fileName][name[:3]])
                
                # Once all is plotting we autorange
                self.main._refs[plotRef]['plot'].plotItem.vb.autoRange()

                # and we set y log mode True
                QtTest.QTest.qWait(100) # To avoid an overflow error
                self.main._refs[plotRef]['plot'].checkBoxLogY.toggle()

            # Thermometers files
            else:
                df = pd.read_csv(filePath,
                                 delimiter = ',',
                                 names     = ['date', 'time', 'y'],
                                 header    = None)

                # There is a space before the day
                df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')

                self.main.startPlotting(plotRef = plotRef,
                                   data    = (df['y'].index.astype(np.int64).values//1e9, df['y']),
                                   xLabel  = 'Time',
                                   yLabel  = config[fileName])


        else:

            # If there is more than one curve, we remove one curve
            if self.main._refs[plotRef]['nbCurve'] > 1:
                yLabel = config[fileName]

                # If maxigauge file, we have to remove all the curves at once
                if yLabel == config['maxigauge']:
                    for i in range(1, 7):
                        
                        curveId = config[fileName]['ch'+str(i)]
                        self.main._refs[plotRef]['plot'].removePlotDataItem(curveId=curveId)
                        self.main._refs[plotRef]['nbCurve'] -= 1
                else:
                    self.main._refs[plotRef]['plot'].removePlotDataItem(curveId=yLabel)
                    self.main._refs[plotRef]['nbCurve'] -= 1
            # If there is one curve we close the plot window
            else:
                self.main._refs[plotRef]['plot'].o()
                del(self.main._refs[plotRef])


