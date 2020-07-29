# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets, QtTest
import os
import json
from pprint import pformat
from typing import Generator
import numpy as np
import sys 
sys.path.append('ui')

# Correct bug with pyqtgraph and python3.8 by replacing function name
try:
    import pyqtgraph as pg
except AttributeError:
    import time
    time.clock = time.process_clock


from sources.csv import CSV
from sources.bluefors import BlueFors
from sources.qcodesdatabase import QcodesDatabase
from sources.runpropertiesextra import RunPropertiesExtra
from sources.mytablewidgetitem import MyTableWidgetItem
from sources.importDatabase import ImportDatabaseThread
from sources.config import config
from sources.plot_1d_app import Plot1dApp
from sources.plot_2d_app import Plot2dApp
from ui import main

pg.setConfigOption('background', config['pyqtgraphBackgroundColor'])
pg.setConfigOption('useOpenGL', config['pyqtgraphOpenGL'])
pg.setConfigOption('antialias', config['plot1dAntialias'])



class MainApp(QtWidgets.QMainWindow, main.Ui_MainWindow, RunPropertiesExtra):



    def __init__(self, parent=None):

        super(MainApp, self).__init__(parent)
        self.setupUi(self)

        
        # Connect UI
        self.tableWidgetFolder.clicked.connect(self.itemClicked)
        self.pushButtonOpenFolder.clicked.connect(self.openFolderClicked)
        
        # Resize the cell to the column content automatically
        self.tableWidgetDataBase.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tableWidgetParameters.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tableWidgetFolder.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tableWidgetParameters.setColumnHidden(0, True)
        self.tableWidgetParameters.setColumnHidden(1, True)

        # Connect event
        self.tableWidgetDataBase.currentCellChanged.connect(self.runClicked)
        self.tableWidgetDataBase.doubleClicked.connect(self.runDoubleClicked)
        self.tableWidgetDataBase.keyPressed.connect(self.tableWidgetDataBasekeyPress)
        self.tableWidgetParameters.cellClicked.connect(self.parameterCellClicked)
        
        self.checkBoxLivePlot.toggled.connect(self.livePlotToggle)
        self.spinBoxLivePlot.setValue(int(config['livePlotTimer']))
        self.spinBoxLivePlot.valueChanged.connect(self.livePlotSpinBoxChanged)
        self.checkBoxHidden.stateChanged.connect(lambda : self.checkBoxHiddenState(self.checkBoxHidden))

        self.lineEditFilter.textChanged.connect(self.lineEditFilterTextEdited)


        self.setStatusBarMessage('Ready')

        # Default folder is the dataserver except if we are on test mode
        if 'test' in os.listdir('.'):

            self.currentPath = os.path.abspath(os.path.curdir)
            config['path'] = self.currentPath
            config['root'] = self.currentPath
        # If we are unable to detect the config folder, we switch in local mode
        elif not os.path.isdir(os.path.normpath(config['path'])):
            
            # Ask user to chose a path
            self.currentPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                          caption='Open folder',
                                                                          directory=os.getcwd(),
                                                                          options=QtWidgets.QFileDialog.ReadOnly|QtWidgets.QFileDialog.ShowDirsOnly)

            # Set config parameter accordingly
            config['path'] = os.path.abspath(self.currentPath)
            config['root'] = os.path.splitdrive(self.currentPath)[0]
        else:
            
            self.currentPath = os.path.normpath(config['path'])

        # References
        self._refs = {}

        # Attribute to control the display of data file info when user click of put focus on a item list
        self.folderUpdating  = False # To avoid calling the signal when updating folder content
        self.guiInitialized = True # To avoid calling the signal when starting the GUI


        self.currentDatabase    = None
        self.oldTotalRun        = None
        self.livePlotMode       = False
        self.livePlotFetchData  = False
        self.livePlotTimer      = None

        # Handle connection and requests to qcodes database
        self.qcodesDatabase = QcodesDatabase(self.setStatusBarMessage)
        # Handle log files from bluefors fridges
        self.blueFors       = BlueFors(self)
        # Handle csv files
        self.csv            = CSV(self)


        # By default, we browse the root folder
        self.folderClicked(directory=self.currentPath)

        self.threadpool = QtCore.QThreadPool()



    ###########################################################################
    #
    #
    #                           Folder browsing
    #
    #
    ###########################################################################



    def openFolderClicked(self):
        """
        Call when user click on the 'Open folder' button.
        Allow user to chose any available folder in his computer.
        """

        # Ask user to chose a path
        self.currentPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                    caption='Open folder',
                                                                    directory=os.getcwd(),
                                                                    options=QtWidgets.QFileDialog.ReadOnly|QtWidgets.QFileDialog.ShowDirsOnly)
        if self.currentPath != '':
            # Set config parameter accordingly
            config['path'] = os.path.abspath(self.currentPath)
            config['root'] = os.path.splitdrive(self.currentPath)[0]

            self.folderClicked(directory=self.currentPath)



    def updateLabelPath(self):
        """
        Update the label path by creating a horizontal list of buttons to
        quickly browse back the folder arborescence.
        """

        self.clearLayout(self.labelPath)

        path = os.path.normpath(self.currentPath).split(os.sep)
        root = os.path.normpath(config['root']).split(os.sep)

        # Display path until root 
        for i, text in enumerate(path):

            # Build button text depending of where we are
            if text == root[-1]:
                bu_text = 'root'
            elif text not in root:
                bu_text = text
            else:
                bu_text = None

            # Create, append and connect buttons
            if bu_text is not None:
                bu = QtWidgets.QPushButton(bu_text)
                width = bu.fontMetrics().boundingRect(bu_text).width() + 15
                bu.setMaximumWidth(width)
                d = os.path.join(path[0], os.sep, *path[1:i+1])
                bu.clicked.connect(lambda bu, directory=d : self.folderClicked(directory))
                self.labelPath.addWidget(bu)

        self.labelPath.setAlignment(QtCore.Qt.AlignLeft)



    def folderClicked(self, directory=None):
        """
        Basically display folder and csv file of the current folder.
        """
        
        # When signal the updating of the folder to prevent unwanted item events
        self.folderUpdating = True
        self.currentPath = directory

        self.updateLabelPath()


        # Load runs extra properties
        self.jsonLoad()
        databaseStared = self.getDatabaseStared()

        ## Display the current dir content
        self.clearTableWidet(self.tableWidgetFolder)
        self.tableWidgetFolder.setSortingEnabled(True)
        row = 0
        for file in sorted(os.listdir(self.currentPath), reverse=True): 
            
            abs_filename = os.path.join(self.currentPath, file)
            file_extension = os.path.splitext(abs_filename)[-1][1:]

            
            

            # Only display folder and Qcodes database
            # Add icon depending of the item type

            # If folder
            if os.path.isdir(abs_filename):
                
                # If looks like a BlueFors log folder
                if self.blueFors.isBlueForsFolder(file):
                    item =  QtGui.QTableWidgetItem(file)
                    item.setIcon(QtGui.QIcon('ui/pictures/bluefors.png'))

                    self.tableWidgetFolder.insertRow(row)
                    self.tableWidgetFolder.setItem(row, 0, item)
                    row += 1
                # Other folders
                else:   
                    # If user wants to only display authorized setup
                    if config['display_only_authorized_setup']:
                        # Only setup listed in 'authorized_setup' will be shown
                        if directory in os.path.normpath(config['path']):
                            if file in config['authorized_setup']:
                                item =  QtGui.QTableWidgetItem(file)
                                item.setIcon(QtGui.QIcon('ui/pictures/folderSetup.png'))
                                self.tableWidgetFolder.insertRow(row)
                                self.tableWidgetFolder.setItem(row, 0, item)
                                row += 1

                        else:
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/folder.png'))
                            self.tableWidgetFolder.insertRow(row)
                            self.tableWidgetFolder.setItem(row, 0, item)
                            row += 1
                    # If not the authorized setup will only be colored
                    else:
                        item =  QtGui.QTableWidgetItem(file)
                        if file in config['authorized_setup']:
                            item.setIcon(QtGui.QIcon('ui/pictures/folderSetup.png'))
                        else:
                            item.setIcon(QtGui.QIcon('ui/pictures/folder.png'))
                        self.tableWidgetFolder.insertRow(row)
                        self.tableWidgetFolder.setItem(row, 0, item)
                        row += 1
            # If files
            else:
                if file not in config['forbidden_file']:
                    if file_extension.lower() in config['authorized_extension']:
                        

                        # We look if the file is already opened by someone else
                        DatabaseAlreadyOpened = False
                        for subfile in os.listdir(self.currentPath): 
                            if subfile==file[:-2]+'db-wal':
                                DatabaseAlreadyOpened = True

                        if file_extension.lower() == 'csv':
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/csv.png'))
                        elif file_extension.lower() == 's2p':
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/s2p.png'))
                        elif DatabaseAlreadyOpened and file in databaseStared:
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/databaseOpenedStared.png'))
                            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                        elif DatabaseAlreadyOpened:
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/databaseOpened.png'))
                            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                        elif file in databaseStared:
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/databaseStared.png'))
                        else:
                            item =  QtGui.QTableWidgetItem(file)
                            item.setIcon(QtGui.QIcon('ui/pictures/database.png'))
                        self.tableWidgetFolder.insertRow(row)
                        self.tableWidgetFolder.setItem(row, 0, item)
                        
                        # Get file size in hman readable format
                        fileSizeItem = QtGui.QTableWidgetItem(self.sizeof_fmt(os.path.getsize(abs_filename)))
                        fileSizeItem.setTextAlignment(QtCore.Qt.AlignRight)
                        fileSizeItem.setTextAlignment(QtCore.Qt.AlignVCenter)
                        self.tableWidgetFolder.setItem(row, 1, fileSizeItem)
                        row += 1
                    

        # Disable live plot
        self.checkBoxLivePlot.setEnabled(False)
        self.spinBoxLivePlot.setEnabled(False)
        self.labelLivePlot.setEnabled(False)
        self.labelLivePlot2.setEnabled(False)
        self.labelLivePlotDataBase.setEnabled(False)
        self.labelLivePlotDataBase.setText('')

        # Allow item event again
        self.folderUpdating = False



    def itemClicked(self):
        """
        Handle event when user clicks on datafile.
        The user can either click on a folder or a file.
        If it is a folder, we launched the folderClicked method.
        If it is a file, we launched the dataBaseClicked method.
        """
        # We check if the signal is effectively called by user
        if not self.folderUpdating and self.guiInitialized:
            
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            # Get current item
            currentRow = self.tableWidgetFolder.currentIndex().row()
            self.currentDatabase =  self.tableWidgetFolder.model().index(currentRow, 0).data()

            nextPath = os.path.join(self.currentPath, self.currentDatabase)

            # If the folder is a BlueFors folder
            if self.blueFors.isBlueForsFolder(self.currentDatabase):
                
                self.blueFors.blueForsFolderClicked(directory=nextPath)
                self.folderClicked(directory=self.currentPath)
            # If the folder is a regulat folder
            elif os.path.isdir(nextPath):
                self.statusBar.showMessage('Update')
                self.folderClicked(directory=nextPath)
                self.statusBar.showMessage('Ready')\
            # If it is a csv or a s2p file
            elif nextPath[-3:].lower() in ['csv', 's2p']:

                self.csv.csvFileClicked(nextPath)
                self.folderClicked(directory=self.currentPath)
            # If it is a QCoDeS database
            else:
                
                self.dataBaseClicked()
                self.folderClicked(directory=self.currentPath)
                # # We check of the user double click ir single click
                #                         self._itemClicked)

            # Job done, we restor the usual cursor 
            QtGui.QApplication.restoreOverrideCursor()
        
        # When the signal has been called at least once
        if not self.guiInitialized:
            self.guiInitialized = True



    ###########################################################################
    #
    #
    #                           Database browsing
    #
    #
    ###########################################################################



    def dataBaseClicked(self):
        """
        Display the content of the clicked dataBase into the database table
        which will then contain all runs.

        """
        self.databaseClicking = True
        # We show the database is now opened
        if self.isDatabaseStared():

            currentRow = self.tableWidgetFolder.currentIndex().row()
            item = self.tableWidgetFolder.item(currentRow, 0)
            item.setIcon(QtGui.QIcon('ui/pictures/databaseOpenedStared.png'))
        else:
            currentRow = self.tableWidgetFolder.currentIndex().row()
            item = self.tableWidgetFolder.item(currentRow, 0)
            item.setIcon(QtGui.QIcon('ui/pictures/databaseOpened.png'))

        # Disable interactivity
        self.checkBoxHidden.setChecked(False)
        self.checkBoxHidden.setEnabled(False)

        # Update label
        self.labelCurrentDataBase.setText(self.currentDatabase[:-3])

        # Remove all previous row in the table
        self.clearTableWidet(self.tableWidgetDataBase)

        # We try to connect to the database
        self.setStatusBarMessage('Connect to database')
        self.qcodesDatabase.databasePath = os.path.join(self.currentPath, self.currentDatabase)

        # Try to get info from the database
        self.setStatusBarMessage('Gathered runs infos database')
        runInfos = self.qcodesDatabase.getRunInfos()

        # Add a progress bar in the statusbar
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.addPermanentWidget(self.progressBar)


        self.nbTotalRun = len(runInfos)
        self.setStatusBarMessage('Loading database')
        
        # Create a thread which will read the database
        worker = ImportDatabaseThread(runInfos)

        # Connect signals
        worker.signals.setStatusBarMessage.connect(self.setStatusBarMessage)
        worker.signals.addRow.connect(self.dataBaseClickedAddRow)
        worker.signals.done.connect(self.dataBaseClickedDone)

        # Execute the thread
        self.threadpool.start(worker)



    def dataBaseClickedAddRow(self, runId : str,
                                    dim : str,
                                    experimentName : str,
                                    sampleName : str,
                                    runName : str,
                                    started : str,
                                    completed : str,
                                    runRecords : str,
                                    progress : int) -> None:
        """
        Called by another thread to fill the database table.
        Each call add one line in the table.
        """
        
        rowPosition = self.tableWidgetDataBase.rowCount()

        if rowPosition==0:
            self.statusBar.clearMessage()

        self.progressBar.setFormat('Getting database information: run '+runId+'/'+str(self.nbTotalRun))
        self.progressBar.setValue(progress)

        # Create new row
        self.tableWidgetDataBase.insertRow(rowPosition)
        
        itemRunId = MyTableWidgetItem(runId)
        
        # If the run has been stared by an user
        if int(runId) in self.getRunStared():
            itemRunId.setIcon(QtGui.QIcon('ui/pictures/star.png'))
            itemRunId.setForeground(QtGui.QBrush(QtGui.QColor(*config['runStaredColor'])))
        # If the user has hidden a row
        elif int(runId) in self.getRunHidden():
            itemRunId.setIcon(QtGui.QIcon('ui/pictures/trash.png'))
            itemRunId.setForeground(QtGui.QBrush(QtGui.QColor(*config['runHiddenColor'])))
        else:
            itemRunId.setIcon(QtGui.QIcon('ui/pictures/empty.png'))
        
        self.tableWidgetDataBase.setItem(rowPosition, 0, itemRunId)
        self.tableWidgetDataBase.setItem(rowPosition, 1, QtGui.QTableWidgetItem(dim))
        self.tableWidgetDataBase.setItem(rowPosition, 2, QtGui.QTableWidgetItem(experimentName))
        self.tableWidgetDataBase.setItem(rowPosition, 3, QtGui.QTableWidgetItem(sampleName))
        self.tableWidgetDataBase.setItem(rowPosition, 4, QtGui.QTableWidgetItem(runName))
        self.tableWidgetDataBase.setItem(rowPosition, 5, QtGui.QTableWidgetItem(started))
        self.tableWidgetDataBase.setItem(rowPosition, 6, QtGui.QTableWidgetItem(completed))
        self.tableWidgetDataBase.setItem(rowPosition, 7, MyTableWidgetItem(runRecords))

        if int(runId) in self.getRunHidden():
            self.tableWidgetDataBase.setRowHidden(rowPosition, True)



    def dataBaseClickedDone(self, error=False):
        """
        Called when the database table has been filled
        """

        self.statusBar.removeWidget(self.progressBar)
        
        if not error:
            self.tableWidgetDataBase.setSortingEnabled(True)

            # Enable live plot
            self.checkBoxLivePlot.setEnabled(True)
            self.spinBoxLivePlot.setEnabled(True)
            self.labelLivePlot.setEnabled(True)
            self.labelLivePlot2.setEnabled(True)
            self.labelLivePlotDataBase.setEnabled(True)
            self.labelLivePlotDataBase.setText(self.currentDatabase[:-3])

            # Enable database interaction
            self.checkBoxHidden.setEnabled(True)

            self.setStatusBarMessage('Ready')

        self.databaseClicking = False



    def runDoubleClicked(self):
        """
        Called when user double click on the database table.
        Display the measured dependent parameters in the table Parameters.
        Simulate the user clicking on the first dependent parameter, effectively
        launching its plot.
        """

        # We simulate a single click
        self.runClicked()

        # We click on the first parameter, which will launch a plot
        self.parameterCellClicked(0, 2)



    def runClicked(self):
        """
        When clicked display the measured dependent parameters in the 
        tableWidgetPtableWidgetParameters
        """
        
        # # When the user click on another database while having already clicked
        # # on a run, the runClicked event is happenning even if no run have been clicked
        # # This is due to the "currentCellChanged" event handler.
        # # We catch that false event and return nothing
        if self.databaseClicking:
            return

        
        runId = self.getRunId()
        experimentName = self.getRunExperimentName()

        if self.livePlotMode:
            runId = str(self.nbTotalRun)
        else:
            runId = str(self.getRunId())

        self.setStatusBarMessage('Loading run parameters')


        # Get independent parameters list without the independent parameters
        # Get parameters list without the independent parameters
        independentList, dependentList, snapshotDict = self.qcodesDatabase.getIndependentDependentSnapshotFromRunId(runId)
        independentString = config['sweptParameterSeparator'].join([independent['name'] for independent in independentList])


        # ds = self.qcodesDatabase.getDatasetFromRunId(int(self.getRunId()))

        ## Update label
        self.labelCurrentRun.setText(runId)
        self.labelCurrentMetadata.setText(runId)
        nbIndependentParameter = str(len(independentList))
        self.labelPlotTypeCurrent.setText(nbIndependentParameter+'d')



        ## Fill the tableWidgetParameters with the run parameters

        self.clearTableWidet(self.tableWidgetParameters)
        for dependent in dependentList:
            
            rowPosition = self.tableWidgetParameters.rowCount()

            self.tableWidgetParameters.insertRow(rowPosition)

            cb = QtWidgets.QCheckBox()

            # We check if that parameter is already plotted
            if self.isParameterPlotted(self.getDependentLabel(dependent)):
                cb.setChecked(True)

            self.tableWidgetParameters.setItem(rowPosition, 0, QtGui.QTableWidgetItem(str(runId)))
            self.tableWidgetParameters.setItem(rowPosition, 1, QtGui.QTableWidgetItem(str(experimentName)))
            self.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
            self.tableWidgetParameters.setItem(rowPosition, 3, QtGui.QTableWidgetItem(dependent['name']))
            self.tableWidgetParameters.setItem(rowPosition, 4, QtGui.QTableWidgetItem(dependent['unit']))
            self.tableWidgetParameters.setCellWidget(rowPosition, 5, QtWidgets.QLabel(independentString))

            # Each checkbox at its own event attached to it
            cb.toggled.connect(lambda state,
                                      cb=cb,
                                      row=rowPosition,
                                      plotRef=self.getPlotRef(): self.parameterClicked(state, cb, row, plotRef))
        

        self.tableWidgetParameters.setSortingEnabled(True)

        ## Fill the listWidgetMetada with the station snapshot
        self.textEditMetadata.clear()
        self.lineEditFilter.setEnabled(True)
        self.labelFilter.setEnabled(True)
        self.originalSnapshot = snapshotDict
        self.lineEditFilterTextEdited('')



        self.setStatusBarMessage('Ready')



    def parameterCellClicked(self, row, column):
        """
        Handle event when user click on the cell containing the checkbox.
        Basically toggle the checkbox and launch the event associated to the
        checkbox
        """
        
        # If user clicks on the cell containing the checkbox
        if column==2:
            cb = self.tableWidgetParameters.cellWidget(row, 2)
            cb.toggle()



    def parameterClicked(self, state, cb, row, plotRef):
        """
        Handle event when user clicked on data line.
        Basically launch a plot
        """
        
        # If the checkbutton is checked, we downlad and plot the data
        paramsIndependent, paramsDependent = self.qcodesDatabase.getListIndependentDependentFromRunId(self.getRunId())

        if state:
            
            # When the user click to plot we disable the gui
            self.setStatusBarMessage('Loading run data')
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.centralwidget.setEnabled(False)


            # Get data
            nbIndependent = int(self.labelPlotTypeCurrent.text()[0])
            
            if nbIndependent==1:


                self.setStatusBarMessage('Getting data')
                data = self.getData1d(row)
                if data is None:
                    # Plot is done, we unable the gui
                    QtGui.QApplication.restoreOverrideCursor()
                    cb.setChecked(False)
                    self.centralwidget.setEnabled(True)
                    return

                self.setStatusBarMessage('Launching 1D plot')

                xLabel = self.getDependentLabel(paramsIndependent[0])
                yLabel = self.getDependentLabel(paramsDependent[row])
                zLabel = None
            elif nbIndependent==2:


                self.setStatusBarMessage('Getting data')
                data = self.getData2d(row)
                if data is None:
                    # Plot is done, we unable the gui
                    QtGui.QApplication.restoreOverrideCursor()
                    cb.setChecked(False)
                    self.centralwidget.setEnabled(True)
                    return

                self.setStatusBarMessage('Launching 2D plot')

                xLabel = self.getDependentLabel(paramsIndependent[0])
                yLabel = self.getDependentLabel(paramsIndependent[1])
                zLabel = self.getDependentLabel(paramsDependent[row])
            else:
                self.setStatusBarMessage('Plotter does not handle data whose dim>2', error=True)

                # Plot will not be done, we unable the gui
                QtGui.QApplication.restoreOverrideCursor()
                self.centralwidget.setEnabled(True)

                return
            
            
            # Reference
            if plotRef in self._refs:
                self._refs[plotRef]['nbCurve'] += 1
            else:
                self._refs[plotRef] = {'nbCurve': 1}
        
            self.startPlotting(plotRef, data, xLabel, yLabel, zLabel)

        # If the checkbox is unchecked
        else:
            # We are dealing with 2d plot
            plotType = self.getPlotWindowType(plotRef)
            if plotType is None:
                return
            elif plotType == '2d':
                zLabel = self.getDependentLabel(paramsDependent[row])
                self._refs[plotRef]['plot'][zLabel].o()
                del(self._refs[plotRef]['plot'][zLabel])

            # We are dealing with 1d plot
            else:
                # If there is more than one curve, we remove one curve
                if self._refs[plotRef]['nbCurve'] > 1:
                    yLabel = self.getDependentLabel(paramsDependent[row])
                    self._refs[plotRef]['plot'].removePlotDataItem(curveId=yLabel)
                    self._refs[plotRef]['nbCurve'] -= 1
                # If there is one curve we close the plot window
                else:
                    self._refs[plotRef]['plot'].o()
                    del(self._refs[plotRef])



    ###########################################################################
    #
    #
    #                           GUI
    #
    #
    ###########################################################################



    def getDependentLabel(self, dependent : dict) -> str:
        """
        Return the label from a qcodes dependent parameter.
        """

        return dependent['name']+' ['+dependent['unit']+']'



    def isParameterPlotted(self, parameterLabel : str) -> bool:
        """
        Return True when the displayed parameter is currently plotted.
        """

        # checkedDependents = []
        # If a plotWindow is already open
        if len(self._refs) > 0:
            # We iterate over all plotWindow
            for key, val in self._refs.items():
                if key == self.getPlotRef():
                    # For 1d plot window
                    if self.getPlotWindowType(key) == '1d':
                        if parameterLabel in list(val['plot'].curves.keys()):
                            return True
                    # For 2d plot window
                    else:
                        for plot2d in val['plot'].values():
                            if parameterLabel == plot2d.zLabel:
                                return True
        
        return False



    def findKeyInDict(self, key : str, dictionary : dict) -> Generator:
        """
        Find all occurences of a key in nested python dictionaries and lists.
        Adapted from:
        https://gist.github.com/douglasmiranda/5127251

        Parameters
        ----------
        key : str
            Part of the text looked as key in the nested dict.
        dictionary : dict
            Dictionnary to be looked up
        
        Return
        ------
        list of all paired of {key : val} found
        """

        for k, v in dictionary.items():
            if key in k:
                yield {k: v}
            elif isinstance(v, dict):
                for result in self.findKeyInDict(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    if isinstance(d, dict):
                        for result in self.findKeyInDict(key, d):
                            yield result



    def lineEditFilterTextEdited(self, text : str) -> None:
        """
        Called when user types text in the filter lineEdit widget.
        Looked for the all keys which contains the entered string
        """

        if len(text) != 0:
            snapshotNew = list(self.findKeyInDict(text, self.originalSnapshot))
            
            self.textEditMetadata.setText(pformat(snapshotNew)
                                        .replace('{', '')
                                        .replace('}', '')
                                        .replace("'", '')
                                        .replace('\n', '<br>')
                                        .replace(' ', '&nbsp;')
                                        .replace(text, '<span style="font-weight: bold;color: red;">'+text+'</span>'))
        else:
            snapshotNew = self.originalSnapshot
            self.textEditMetadata.setText(pformat(snapshotNew)
                                        .replace('{', '')
                                        .replace('}', '')
                                        .replace("'", ''))


    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        """
        Return human readable number of Bytes
        Adapted from:
        https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
        """
        for unit in ['','K','M','G','T','P','E','Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)



    @staticmethod
    def clearTableWidet(tableWidget : QtWidgets.QTableWidget) -> None:
        """
        Method to remove all row from a table widget.
        When this function is called, it should be followed by:
        tableWidget.setSortingEnabled(True)
        to allowed GUI sorting
        """

        tableWidget.setSortingEnabled(False)
        tableWidget.setRowCount(0)



    def setStatusBarMessage(self, text, error=False):
        
        if error:
            self.statusBar.setStyleSheet('color: red; font-weight: bold;')
        elif text=='Ready':
            self.statusBar.setStyleSheet('color: green; font-weight: bold;')
        else:
            self.statusBar.setStyleSheet('color: '+config['dialogTextColor']+'; font-weight: normal;')

        self.statusBar.showMessage(text)



    def updateProgressBar(self, val):
        self.progressBarBar.setValue(val)


    @staticmethod
    def clearLayout(layout):
        """
        Clear a pyqt layout, from:
        https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()



    def closeEvent(self, evnt):
        """
        Method called when closing the main app.
        Close open database connection
        Close every 1d and 2d plot opened.
        """

        # If an open database connection is detected, we close it.
        if hasattr(self.qcodesDatabase, 'conn'):
            self.qcodesDatabase.closeDatabase()
        
        for key in list(self._refs.keys()):
            # For 2d plot
            if self.getPlotWindowType(key) == '2d':
                keyToDelete = list(self._refs[key]['plot'].keys())
                for subkey in keyToDelete:
                    self._refs[key]['plot'][subkey].o()
            # For 1d plot
            else:
                self._refs[key]['plot'].o()
    


    def cleanCheckBox(self, windowTitle, runId, dependent=None):
        """
        Method called by the QDialog plot when the user close the plot window.
        We propagate that event to the mainWindow to uncheck the checkbox.
        """

        if self.currentDatabase == windowTitle and self.getRunId() == runId:
            # If 1d plot
            if dependent is None:
                # If the current displayed parameters correspond to the one which has
                # been closed, we uncheck all the checkbox listed in the table
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 2)
                    widget.setChecked(False)
            # If 2d plot
            else:
                # We uncheck only the plotted parameter
                targetedZaxis = dependent.split('[')[0][:-1]
                for row in range(self.tableWidgetParameters.rowCount()):
                    if targetedZaxis == self.tableWidgetParameters.item(row, 3).text():
                        widget = self.tableWidgetParameters.cellWidget(row, 2)
                        widget.setChecked(False)



    ###########################################################################
    #
    #
    #                           QCoDes data handling methods
    #
    #
    ###########################################################################



    def getNbTotalRun(self, refresh_db=False):
        """
        Return the total number of run in current database
        """

        if refresh_db:
            self.nbTotalRun = self.qcodesDatabase.getNbTotalRun()

        return self.nbTotalRun



    def getRunId(self):
        """
        Return the current selected run id.
        if Live plot mode, return the total number of run.
        """

        if self.livePlotMode:
            return self.getNbTotalRun()
        else:
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            runId = self.tableWidgetDataBase.model().index(currentRow, 0).data()
            if runId is None:
                
                runId = self.tableWidgetParameters.item(0, 0).text()

            return int(runId)



    def getRunExperimentName(self):
        """
        Return the experiment name of the current selected run.
        if Live plot mode, return the experiment name of the last recorded run.
        """
        
        
        if self.livePlotMode:

            return self.qcodesDatabase.getExperimentNameLastId()
        else:
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            experimentName =  self.tableWidgetDataBase.model().index(currentRow, 2).data()
            if experimentName is None:
                
                experimentName = self.tableWidgetParameters.item(0, 1).text()

            return str(experimentName)



    def getWindowTitle(self):
        """
        Return a title which will be used as a plot window title.
        """

        return self.currentDatabase



    def getPlotTitle(self):
        """
        Return a plot title in a normalize way displaying the folders and
        file name.
        """

        # If BlueFors log files
        if self.blueFors.isBlueForsFolder(self.currentDatabase):
            return self.currentDatabase
        # If csv or s2p files we return the filename without the extension
        elif self.currentDatabase[-3:].lower() in ['csv', 's2p']:
            return self.currentDatabase[:-4]
        else:
            # If user only wants the database path
            if config['display_only_db_name_in_plot_title']:
                title = self.currentDatabase
            # If user wants the database path
            else:
                title = os.path.normpath(self.currentPath).split(os.path.sep)[2:]
                title = '/'.join(title)

            title = title+'<br>'+str(self.getRunId())+' - '+self.getRunExperimentName()
            return title



    def getPlotRef(self):
        """
        Return a reference for the plot window.
        This should be unique for a given set of data.
        """

        # If BlueFors log files
        if self.blueFors.isBlueForsFolder(self.currentDatabase):
            return os.path.abspath(self.currentDatabase)
        # If csv or s2p files we return the filename without the extension
        elif self.currentDatabase[-3:].lower() in ['csv', 's2p']:
            return os.path.abspath(self.currentDatabase)
        else:
            return os.path.abspath(self.currentDatabase)+str(self.getRunId())



    ###########################################################################
    #
    #
    #                           Live plotting
    #
    #
    ###########################################################################



    def getLivePlotRef(self):
        
        
        returnKey = None
        # We get which open plot window is the liveplot one
        for key, val in self._refs.items():
            if val['livePlot']:
                returnKey = key

        return returnKey



    def livePlotUpdate(self):

        # If user selected database
        if self.currentDatabase is not None:

            # Check if database has one more run
            # if there is a new run, we launch a plot
            if self.oldTotalRun is not None:

                nbtotalRun = self.getNbTotalRun(True)
                if self.oldTotalRun != nbtotalRun:
                    
                    # We refresh the database display
                    self.dataBaseClicked()
                    
                    databaseUpdated = False
                    while not databaseUpdated:
                        QtTest.QTest.qWait(500)
                        try:
                            self.runClicked()
                            databaseUpdated = True
                        except:
                            pass



                    # We click on the first parameter, which will launch a plot
                    self.parameterCellClicked(0,0)

                    # We update the total number of run
                    self.oldTotalRun = nbtotalRun

                    # We save the fact that we have to update an existing live plot
                    self.livePlotFetchData = True

            else:
                self.oldTotalRun = self.getNbTotalRun(True)


        # If we have to update the data of a livePlot
        if self.livePlotFetchData:

            runId = int(self.getNbTotalRun())
            
            self.setStatusBarMessage('Fetching data')

            # We get which open plot window is the liveplot one
            livePlotRef = self.getLivePlotRef()
            
            # If there is no live plot, because user closed it/them for example
            # We relaunch a live plot of the first parameters
            if livePlotRef is None:
                self.parameterCellClicked(0,2)
            
            # If the live plot is a 1d plot
            elif self.getPlotWindowType(livePlotRef) == '1d':
                
                # We get which parameters has to be updated
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 2)
                    
                    # For every checked parameter, we update the data
                    if widget.isChecked():
                        data = self.getData1d(row)

                        params = self.qcodesDatabase.getListDependentFromRunId(runId)
                        yLabel = self.getDependentLabel(params)

                        self._refs[livePlotRef]['plot'].updatePlotDataItem(data[0], data[1],
                                                        curveId=yLabel,
                                                        curveLegend=None,
                                                        autoRange=True)

            # If the live plot is a 2d plot
            else:
                # We get which parameters has to be updated
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 2)
                    
                    # For every checked parameter, we update the data
                    if widget.isChecked():

                        # We get the 2d plot reference only the plotted parameter
                        zLabel = self.tableWidgetParameters.item(row, 3).text()+ ' ['+\
                                 self.tableWidgetParameters.item(row, 4).text()+ ']'

                        # We get the colormap data
                        x, y, z = self.getData2d(row)

                        # We update the 2d plot data
                        self._refs[livePlotRef]['plot'][zLabel].updateImageItem(x, y, z)

                        # If there are slices, we update them as well
                        if len(self._refs[livePlotRef]['plot'][zLabel].infiniteLines)>0:
                            for curveId, lineItem in self._refs[livePlotRef]['plot'][zLabel].infiniteLines.items():
                                
                                # We need the data of the slice
                                sliceX, sliceY, sliceLegend = self._refs[livePlotRef]['plot'][zLabel].getDataSlice(lineItem)

                                # We find its orientation
                                if lineItem.angle == 90:
                                    sliceOrientation = 'vertical'
                                else:
                                    sliceOrientation = 'horizontal'

                                # We update the slice data
                                self._refs[livePlotRef]['plot'][zLabel]\
                                .linked1dPlots[sliceOrientation]\
                                .updatePlotDataItem(x           = sliceX,
                                                    y           = sliceY,
                                                    curveId     = curveId,
                                                    curveLegend = sliceLegend,
                                                    autoRange   = True)


            self.setStatusBarMessage('Plot updating')

            # If the run is done
            if self.qcodesDatabase.isRunCompleted(runId):

                self.setStatusBarMessage('Run done')

                # We remove the livePlotFlag attached to the plot window
                livePlotRef = self.getLivePlotRef()
                if livePlotRef in self._refs:
                    self._refs[livePlotRef]['livePlot'] = False

                # We cancel the need to update the plot
                self.livePlotFetchData = False

                # We update the database to display the completed and records info
                self.dataBaseClicked()



    def livePlotToggle(self):
        """
        When the user click the checkbox launching the liveplot mode
        """

        if self.checkBoxLivePlot.isChecked():
            
            # Launch the liveplot mode
            self.livePlotMode = True

            # We call the liveplot function once manually to be sure it has been
            # initialized properly
            self.livePlotUpdate()
            
            # Disable browsing
            self.tableWidgetFolder.setEnabled(False)
            self.tableWidgetDataBase.setEnabled(False)
            widgets = (self.labelPath.itemAt(i).widget() for i in range(self.labelPath.count())) 
            for widget in widgets:
                widget.setEnabled(False)

            # Launch a Qt timer which will periodically check if a new run is
            # launched
            self.livePlotTimer = QtCore.QTimer()
            self.livePlotTimer.timeout.connect(self.livePlotUpdate)
            self.livePlotTimer.setInterval(self.spinBoxLivePlot.value()*1000)
            self.livePlotTimer.start()
        else:
            
            # Stop live plot mode
            self.livePlotMode = False

            # Enable browsing again
            self.tableWidgetFolder.setEnabled(True)
            self.tableWidgetDataBase.setEnabled(True)
            widgets = (self.labelPath.itemAt(i).widget() for i in range(self.labelPath.count())) 
            for widget in widgets:
                widget.setEnabled(True)

            # Stop the Q1 timer
            self.livePlotTimer.stop()
            self.livePlotTimer.deleteLater()
            self.livePlotTimer = None



    def livePlotSpinBoxChanged(self, val):
        """
        When user modify the the spin box associated to the live plot timer
        """

        # If a Qt timer is running, we modify it following the user input.
        if self.livePlotTimer is not None:
            
            self.livePlotTimer.setInterval(self.spinBoxLivePlot.value()*1000)



    ###########################################################################
    #
    #
    #                           Plotting
    #
    #
    ###########################################################################



    def getPlotWindowType(self, ref):

        try:
            if isinstance(self._refs[ref]['plot'], dict):
                return '2d'
            else:
                return '1d'
        except KeyError:
            return None
        



    def startPlotting(self, plotRef, data, xLabel, yLabel, zLabel=None):
        """
        Methods called once the data are downloaded by the data thread.

        """

        self.centralwidget.setEnabled(True)

        # 1D plot
        if len(data) == 2:
            
            # If nbCurve is 1, we create the plot QDialog
            if self._refs[plotRef]['nbCurve'] == 1:

                p = Plot1dApp(x              = data[0],
                              y              = data[1],
                              title          = self.getPlotTitle(),
                              xLabel         = xLabel,
                              yLabel         = yLabel,
                              windowTitle    = self.getWindowTitle(),
                              runId          = int(self.getRunId()),
                              cleanCheckBox  = self.cleanCheckBox,
                              curveId        = yLabel,
                              timestampXAxis=self.blueFors.isBlueForsFolder(self.currentDatabase))

                self._refs[plotRef]['plot']     = p
                self._refs[plotRef]['livePlot'] = self.livePlotMode
                self._refs[plotRef]['plot'].show()

            # If the QDialog already exists, we add a curve to it
            else:
                self._refs[plotRef]['plot'].addPlotDataItem(x            = data[0],
                                                            y            = data[1],
                                                            curveId      = yLabel,
                                                            curveLabel   = yLabel,
                                                            curveLegend  = yLabel)
            


        # 2D plot
        elif len(data) == 3:
            
            p = Plot2dApp(x              = data[0],
                          y              = data[1],
                          z              = data[2],
                          title          = self.getPlotTitle(),
                          xLabel         = xLabel,
                          yLabel         = yLabel,
                          zLabel         = zLabel,
                          windowTitle    = self.getWindowTitle(),
                          runId          = int(self.getRunId()),
                          cleanCheckBox  = self.cleanCheckBox)

            self._refs[plotRef]['livePlot'] = self.livePlotMode

            # If user wants to plot more than one parameter we launch one plot
            # window per parameter
            if self._refs[plotRef]['nbCurve'] == 1:
                self._refs[plotRef]['plot'] = {zLabel : p}
            else:
                self._refs[plotRef]['plot'][zLabel] = p

            self._refs[plotRef]['plot'][zLabel].show()
        
        # Plot is done, we unable the gui
        QtGui.QApplication.restoreOverrideCursor()
        self.setStatusBarMessage('Ready')



    ###########################################################################
    #
    #
    #                           Data 
    #
    #
    ###########################################################################



    def getData1d(self, row):
        """
        Return a 2d np array containing the x and y axis to be plotted.

        Parameters
        ----------

        row : int
            Row in the parameter table associated with the dependent parameter
            to plot
        """

        # Get data
        paramIndependent = self.tableWidgetParameters.cellWidget(row, 5).text()
        paramDependent = self.tableWidgetParameters.item(row, 3).text()
        
        d = self.qcodesDatabase.getParameterData(self.getRunId(), paramDependent)
        if d is None:
            return

        # We try to load data
        # if there is none, we return an empty array
        try:
            data = d[paramIndependent], d[paramDependent]
        except:
            data = np.array([np.nan]), np.array([np.nan])

        return data



    def getData2d(self, row):
        """
        Return a 2d np array containing the x and y z axis to be plotted.

        Parameters
        ----------

        row : int
            Row in the parameter table associated with the dependent parameter
            to plot
        """

        # Get data
        paramsIndependent = self.tableWidgetParameters.cellWidget(row, 5).text().split(config['sweptParameterSeparator'])
        paramDependent = self.tableWidgetParameters.item(row, 3).text()

        d = self.qcodesDatabase.getParameterData(self.getRunId(), paramDependent)
        if d is None:
            return
        
        # We try to load data
        # if there is none, we return an empty array
        try:
            data = self.shapeData2d(d[paramsIndependent[0]], d[paramsIndependent[1]], d[paramDependent])
        except:
            # We have to send [0,1] for the z axis when no data to avoid bug with the histogram
            data = np.array([0, 1]), np.array([0, 1]), np.array([[0, 1],[0, 1]])

        return data



    def shapeData2d(self, x, y, z):
        """
        Intermediate method to catch "error" when user is inverting the x and y
        axis compare to what the algo is expecting.
        """
        
        try:
            x, y, z = self.shapeData2dSub(x, y, z)
        except ValueError:
            x, y, z = self.shapeData2dSub(y, x, z)
            t = y
            y = x
            x = t
            z = z.T

        return x, y, z



    def shapeData2dSub(self, x, y, z):
        """
        Shape the data for a 2d plot but mainly handled all kind of data error/missing/...

        Return x and y as a 1d array, ready to be used for the 2d plot
        and z as a 2d array.
        In case of non regular grid, the y axis is approximated.
        """
        
        # Nb points in the 1st dimension
        xn = len(np.unique(x))

        # Nb points in the 2nd dimension
        xx = np.array([])
        for i in np.unique(x):
            xx = np.append(xx, len(x[x==i]))
        yn = int(xx.max())

        # If interuption, we calculated the number of missing point and add them
        if len(np.unique(xx)) != 1:

            p = np.full(int(xx.max() - xx.min()), np.nan)

            x = np.append(x, p)
            y = np.append(y, p)
            z = np.append(z, p)
            
        # We create 2D arrays for each dimension
        x = x.reshape(xn, yn)
        y = y.reshape(xn, yn)
        z = z.reshape(xn, yn)

        # Once the shape is corrected, we sort the data
        m = x[:,0].argsort()
        x = x[m]
        y = y[m]
        z = z[m]


        # If the data has a rectangular shape (usual 2d measurement)
        if len(np.unique(y[:,0])) == 1:
            
            # Take a slice of x
            xx = x[:,0]

            # Find a row of y containing only non nan data
            i = 0
            for i in y:
                if not np.any(np.isnan(i)):
                    yy = i
                    break
                i+=1
            
            zz = z
        # If not (like a auto freq measurement )
        else:

            self.setStatusBarMessage('Irregular grid detexted, shapping 2d data')
            xx = x[:,0]
            # Create a bigger array containing sorted data in the same bases
            # New y axis containing all the previous y axes
            yd = np.gradient(np.sort(y[0])).min()
            yy = np.arange(y[~np.isnan(y)].min(), y[~np.isnan(y)].max()+yd*2, yd)


            # For each z scan we create a new z array
            zz = np.array([])
            for y_current, z_current in zip(y, z):
                
                # Find the index of the current y axis on the global y axis
                p = np.abs(yy-y_current[0]).argmin()
                
                # Find the number of nan to insert at the beginning
                v  = np.full(p, np.nan)

                # Find the number of nan to insert at the end
                vv = np.full(len(yy)-p-len(y_current), np.nan)

                # Build the new z axis
                zz = np.append(zz, np.concatenate((v, z_current, vv)))

            zz = zz.reshape(int(len(zz)/len(yy)), len(yy))
        
        # If there is only one point in x or we artificialy create more
        if len(xx)==1:
            xx = np.array([xx*0.9, xx*1.1])
        if len(yy)==1:
            yy = np.array([yy*0.9, yy*1.1])

        return xx, yy, zz



    ############################################################################
    #
    #
    #                           Replace faulty pyqtgraph function
    #
    #
    ############################################################################


def export(self, fileName=None, toBytes=False, copy=False):
    if fileName is None and not toBytes and not copy:
        if USE_PYSIDE:
            filter = ["*."+str(f) for f in QtGui.QImageWriter.supportedImageFormats()]
        else:
            filter = ["*."+bytes(f).decode('utf-8') for f in QtGui.QImageWriter.supportedImageFormats()]
        preferred = ['*.png', '*.tif', '*.jpg']
        for p in preferred[::-1]:
            if p in filter:
                filter.remove(p)
                filter.insert(0, p)
        self.fileSaveDialog(filter=filter)
        return
        
    targetRect = QtCore.QRect(0, 0, self.params['width'], self.params['height'])
    sourceRect = self.getSourceRect()
    
    
    #self.png = QtGui.QImage(targetRect.size(), QtGui.QImage.Format_ARGB32)
    #self.png.fill(pyqtgraph.mkColor(self.params['background']))
    w, h = self.params['width'], self.params['height']
    if w == 0 or h == 0:
        raise Exception("Cannot export image with size=0 (requested export size is %dx%d)" % (w,h))
    bg = np.empty((int(self.params['width']), int(self.params['height']), 4), dtype=np.ubyte)
    color = self.params['background']
    bg[:,:,0] = color.blue()
    bg[:,:,1] = color.green()
    bg[:,:,2] = color.red()
    bg[:,:,3] = color.alpha()
    self.png = fn.makeQImage(bg, alpha=True)
    
    ## set resolution of image:
    origTargetRect = self.getTargetRect()
    resolutionScale = targetRect.width() / origTargetRect.width()
    #self.png.setDotsPerMeterX(self.png.dotsPerMeterX() * resolutionScale)
    #self.png.setDotsPerMeterY(self.png.dotsPerMeterY() * resolutionScale)
    
    painter = QtGui.QPainter(self.png)
    #dtr = painter.deviceTransform()
    try:
        self.setExportMode(True, {'antialias': self.params['antialias'], 'background': self.params['background'], 'painter': painter, 'resolutionScale': resolutionScale})
        painter.setRenderHint(QtGui.QPainter.Antialiasing, self.params['antialias'])
        self.getScene().render(painter, QtCore.QRectF(targetRect), QtCore.QRectF(sourceRect))
    finally:
        self.setExportMode(False)
    painter.end()
    
    if copy:
        QtGui.QApplication.clipboard().setImage(self.png)
    elif toBytes:
        return self.png
    else:
        self.png.save(fileName)

from pyqtgraph.exporters.ImageExporter import ImageExporter
from pyqtgraph.Qt import USE_PYSIDE
import pyqtgraph.functions as fn
ImageExporter.export = export