# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets, QtTest
import os
import json
from pprint import pformat
from typing import Generator, Union
import uuid
import numpy as np
import sys 
sys.path.append('ui')

# Correct bug with pyqtgraph and python3.8 by replacing function name
try:
    import pyqtgraph as pg
except AttributeError:
    import time
    time.clock = time.perf_counter
    import pyqtgraph as pg


from sources.importcsv import ImportCSV
from sources.importbluefors import ImportBlueFors
from sources.qcodesdatabase import QcodesDatabase
from sources.runpropertiesextra import RunPropertiesExtra
from sources.mytablewidgetitem import MyTableWidgetItem
from sources.importdatabase import ImportDatabaseThread
from sources.loaddata import LoadDataThread
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
        
        
        # Flag
        self.dataDowloading = False
        self.progressBars = {}

        self.currentDatabase    = None
        self.oldTotalRun        = None
        self.livePlotMode       = False
        self.livePlotFetchData  = False
        self.livePlotTimer      = None

        # Handle connection and requests to qcodes database
        self.qcodesDatabase = QcodesDatabase(self.setStatusBarMessage)
        # Handle log files from bluefors fridges
        self.importblueFors = ImportBlueFors(self)
        # Handle csv files
        self.importcsv      = ImportCSV(self)


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



    def openFolderClicked(self) -> None:
        """
        Call when user click on the 'Open folder' button.
        Allow user to chose any available folder in his computer.
        """

        # Ask user to chose a path
        path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                          caption='Open folder',
                                                          directory=os.getcwd(),
                                                          options=QtWidgets.QFileDialog.ReadOnly|QtWidgets.QFileDialog.ShowDirsOnly)
        if path != '':
            # Set config parameter accordingly
            self.currentPath = path
            config['path'] = os.path.abspath(self.currentPath)
            config['root'] = os.path.splitdrive(self.currentPath)[0]

            self.folderClicked(directory=self.currentPath)



    def updateLabelPath(self) -> None:
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



    def folderClicked(self, directory: str) -> None:
        """
        Basically display folder and csv file of the current folder.

        Parameters
        ----------
        directory : str
            Path of the folder to be browsed.
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
                if self.importblueFors.isBlueForsFolder(file):
                    item =  QtGui.QTableWidgetItem(file)
                    item.setIcon(QtGui.QIcon('ui/pictures/bluefors.png'))

                    self.tableWidgetFolder.insertRow(row)
                    self.tableWidgetFolder.setItem(row, 0, item)
                    row += 1
                # Other folders
                else:   
                    item =  QtGui.QTableWidgetItem(file)
                    if file in config['setup']:
                        item.setIcon(QtGui.QIcon('ui/pictures/folderSetup.png'))
                    else:
                        item.setIcon(QtGui.QIcon('ui/pictures/folder.png'))
                    self.tableWidgetFolder.insertRow(row)
                    self.tableWidgetFolder.setItem(row, 0, item)
                    row += 1
            # If files
            else:
                if file not in config['forbiddenFile']:
                    if file_extension.lower() in config['authorizedExtension']:
                        

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
                    

        self.enableLivePlot(False)

        # Allow item event again
        self.folderUpdating = False



    def itemClicked(self) -> None:
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
            if self.importblueFors.isBlueForsFolder(self.currentDatabase):
                
                self.importblueFors.blueForsFolderClicked(directory=nextPath)
                self.folderClicked(directory=self.currentPath)
            # If the folder is a regulat folder
            elif os.path.isdir(nextPath):
                self.statusBar.showMessage('Update')
                self.folderClicked(directory=nextPath)
                self.statusBar.showMessage('Ready')\
            # If it is a csv or a s2p file
            elif nextPath[-3:].lower() in ['csv', 's2p']:

                self.importcsv.csvFileClicked(nextPath)
                self.folderClicked(directory=self.currentPath)
            # If it is a QCoDeS database
            else:
                
                # folderClicked called after the worker is done
                self.dataBaseClicked()

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



    def dataBaseClicked(self) -> None:
        """
        Display the content of the clicked dataBase into the database table
        which will then contain all runs.
        """

        self.databaseClicking = True

        if not self.livePlotMode:
            
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

        self.qcodesDatabase.databasePath = os.path.join(self.currentPath, self.currentDatabase)

        # Add a progress bar in the statusbar
        progressBarKey = self.addProgressBarInStatusBar()

        # Create a thread which will read the database
        worker = ImportDatabaseThread(self.qcodesDatabase.getRunInfos, progressBarKey)

        # Connect signals
        worker.signals.setStatusBarMessage.connect(self.setStatusBarMessage)
        worker.signals.addRow.connect(self.dataBaseClickedAddRow)
        worker.signals.updateProgressBar.connect(self.updateProgressBar)
        worker.signals.done.connect(self.dataBaseClickedDone)

        # Execute the thread
        self.threadpool.start(worker)



    def dataBaseClickedAddRow(self, runId          : str,
                                    dim            : list,
                                    experimentName : str,
                                    sampleName     : str,
                                    runName        : str,
                                    started        : str,
                                    completed      : str,
                                    runRecords     : str,
                                    progress       : int,
                                    nbTotalRun     : int,
                                    progressBarKey : str) -> None:
        """
        Called by another thread to fill the database table.
        Each call add one line in the table.
        """
        
        rowPosition = self.tableWidgetDataBase.rowCount()

        if rowPosition==0:
            self.statusBar.clearMessage()

        self.updateProgressBar(progressBarKey, progress, text='Displaying database: run '+runId+'/'+str(nbTotalRun))

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
        self.tableWidgetDataBase.setItem(rowPosition, 1, QtGui.QTableWidgetItem('-'.join(str(i) for i in dim)+'d'))
        self.tableWidgetDataBase.setItem(rowPosition, 2, QtGui.QTableWidgetItem(experimentName))
        self.tableWidgetDataBase.setItem(rowPosition, 3, QtGui.QTableWidgetItem(sampleName))
        self.tableWidgetDataBase.setItem(rowPosition, 4, QtGui.QTableWidgetItem(runName))
        self.tableWidgetDataBase.setItem(rowPosition, 5, QtGui.QTableWidgetItem(started))
        self.tableWidgetDataBase.setItem(rowPosition, 6, QtGui.QTableWidgetItem(completed))
        self.tableWidgetDataBase.setItem(rowPosition, 7, MyTableWidgetItem(runRecords))

        if int(runId) in self.getRunHidden():
            self.tableWidgetDataBase.setRowHidden(rowPosition, True)



    def dataBaseClickedDone(self,
                            progressBarKey : str,
                            error          : bool,
                            nbTotalRun     : int) -> None:
        """
        Called when the database table has been filled

        Parameters
        ----------
        progressBarKey : str
            Key to the progress bar in the dict progressBars.
        error : bool

        nbTotalRun : int
            Total number of run in the current database.
            Simply stored for other purposes and to avoid other sql queries.
        """

        self.removeProgressBar(progressBarKey)
        
        if not error:
            self.tableWidgetDataBase.setSortingEnabled(True)

            # Enable database interaction
            self.checkBoxHidden.setEnabled(True)

            self.setStatusBarMessage('Ready')


        # We store the total number of run
        self.nbTotalRun = nbTotalRun

        # Done 
        self.databaseClicking = False


        # We show the database is now closed
        if self.isDatabaseStared():

            currentRow = self.tableWidgetFolder.currentIndex().row()
            item = self.tableWidgetFolder.item(currentRow, 0)
            item.setIcon(QtGui.QIcon('ui/pictures/databaseStared.png'))
        else:
            currentRow = self.tableWidgetFolder.currentIndex().row()
            item = self.tableWidgetFolder.item(currentRow, 0)
            item.setIcon(QtGui.QIcon('ui/pictures/database.png'))

        self.enableLivePlot(True)



    def runDoubleClicked(self) -> None:
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



    def runClicked(self) -> None:
        """
        When clicked display the measured dependent parameters in the 
        tableWidgetPtableWidgetParameters
        """
        
        # When the user click on another database while having already clicked
        # on a run, the runClicked event is happenning even if no run have been clicked
        # This is due to the "currentCellChanged" event handler.
        # We catch that false event and return nothing
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
        dependentList, snapshotDict = self.qcodesDatabase.getDependentSnapshotFromRunId(runId)


        # ds = self.qcodesDatabase.getDatasetFromRunId(int(self.getRunId()))

        ## Update label
        self.labelCurrentRun.setText(runId)
        self.labelCurrentMetadata.setText(runId)



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


            independentString = config['sweptParameterSeparator'].join(dependent['depends_on'])
            self.tableWidgetParameters.setCellWidget(rowPosition, 5, QtWidgets.QLabel(independentString))

            # Each checkbox at its own event attached to it
            cb.toggled.connect(lambda state,
                                      dependentParamName = dependent['name'],
                                      runId              = runId,
                                      dependent          = dependent,
                                      plotRef            = self.getPlotRef(): self.parameterClicked(state, dependentParamName, runId, dependent, plotRef))
        

        self.tableWidgetParameters.setSortingEnabled(True)

        ## Fill the listWidgetMetada with the station snapshot
        self.textEditMetadata.clear()
        self.lineEditFilter.setEnabled(True)
        self.labelFilter.setEnabled(True)
        self.originalSnapshot = snapshotDict
        self.lineEditFilterTextEdited('')

        self.setStatusBarMessage('Ready')



    def parameterCellClicked(self, row: int, column: int) -> None:
        """
        Handle event when user click on the cell containing the checkbox.
        Basically toggle the checkbox and launch the event associated to the
        checkbox

        Parameters
        ----------
            row, column : int, int
            Row and column where the user clicked
        """
        
        # If user clicks on the cell containing the checkbox
        if column==2:
            cb = self.tableWidgetParameters.cellWidget(row, 2)
            cb.toggle()



    def parameterClicked(self,
                         state              : bool,
                         dependentParamName : str,
                         runId              : int,
                         paramDependent     : dict,
                         plotRef            : str) -> None:
        """
        Handle event when user clicked on data line.
        Either get data and display them or remove the data depending on state.

        Parameters
        ----------
        state : bool
            State of the checkbox
        dependentParamName : str
            Name of the dependent parameter from which data will be downloaded.
        runId : int
            Data run id in the current database
        paramDependent : dict
            Dependent parameter the user wants to see the data.
            This should be a qcodes dependent parameter dict.
        plotRef : str
            Reference of the plot, see getPlotRef.
        """
        

        # If the checkbutton is checked, we downlad and plot the data
        if state:
            
            # If the dimension of the plot is greater then 2
            if len(paramDependent['depends_on'])>2:

                self.setStatusBarMessage('Plotter does not handle data whose dim>2', error=True)
                return
            else:
                self.getData(plotRef, dependentParamName)

        # If the checkbox is unchecked, we remove the plotted data
        else:
            
            label = self.getDependentLabel(paramDependent)
            self.removePlot(plotRef, label)
            



    ###########################################################################
    #
    #
    #                           Progress bar
    #
    #
    ###########################################################################



    def addProgressBarInStatusBar(self) -> str:
        """
        Add the progress bar in the status bar.
        Usually called before a thread is launched to load something.

        Return
        ------
        progressBarKey : str
            An unique key coming from uuid.uuid4().
        """


        # Add a progress bar in the statusbar
        progressBarKey = str(uuid.uuid4())
        self.progressBars[progressBarKey] = QtWidgets.QProgressBar(self)
        self.progressBars[progressBarKey].setAlignment(QtCore.Qt.AlignCenter)
        self.progressBars[progressBarKey].setValue(0)
        self.progressBars[progressBarKey].setTextVisible(True)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.addPermanentWidget(self.progressBars[progressBarKey])

        return progressBarKey



    def removeProgressBar(self, progressBarKey: str) -> None:
        """
        Remove the progress bar in the status bar.
        Usually called after a thread has loaded something.
        """

        self.statusBar.removeWidget(self.progressBars[progressBarKey])
        del self.progressBars[progressBarKey]



    def updateProgressBar(self, key: str, val: int, text: str=None) -> None:
        """
        Update the progress bar in the status bar

        Parameters
        ----------
        key : str
            key from addProgressBarInStatusBar.
        val : int
            Value of the progress.
            Must be an int between 0 and 100.
        text : str
            Text to be shown on the progress bar.
        """

        if text is not None:
            self.progressBars[key].setFormat(text)
        self.progressBars[key].setValue(val)



    ###########################################################################
    #
    #
    #                           Snapshot
    #
    #
    ###########################################################################



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

        Parameters
        ----------
        text : str
            Text to be found in the run snapshot
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



    ###########################################################################
    #
    #
    #                           GUI
    #
    #
    ###########################################################################



    def getDependentLabel(self, paramDependent : dict) -> str:
        """
        Return a label from a qcodes dependent parameter.

        Parameters
        ----------
        paramDependent : dict
            Qcodes dependent parameter.
        """

        return paramDependent['name']+' ['+paramDependent['unit']+']'



    def isParameterPlotted(self, parameterLabel : str) -> bool:
        """
        Return True when the displayed parameter is currently plotted.

        Parameters
        ----------
        parameterLabel : str
            Label of the dependent parameter.
        """

        curveId = self.getCurveId(parameterLabel)

        # If a plotWindow is already open
        if len(self._refs) > 0:
            # We iterate over all plotWindow
            for key, val in self._refs.items():
                if key == self.getPlotRef():
                    # For 1d plot window
                    if self.getPlotWindowType(key) == '1d':
                        if curveId in list(val['plot'].curves.keys()):
                            return True
                    # For 2d plot window
                    else:
                        for plot2d in val['plot'].values():
                            if parameterLabel == plot2d.zLabel:
                                return True
        
        return False


    @staticmethod
    def sizeof_fmt(num: float, suffix: str='B') -> str:
        """
        Return human readable number of Bytes
        Adapted from:
        https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size

        Parameters
        ----------
        num : float
            Size of a file to be transformed in human readable format
        suffix : str
            Suffix to be added after the unit size

        Return
        ------
        humanReadableSize : str
            Size of the file in an easily readable format.
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



    def setStatusBarMessage(self, text: str, error: bool=False) -> None:
        """
        Display message in the status bar.

        Parameters
        ----------
        text : str
            Text to be displayed.
            if text=='Ready', display the text in green and bold.
        error : bool, default False
            If true display the text in red and bold.
        """
        
        if error:
            self.statusBar.setStyleSheet('color: red; font-weight: bold;')
        elif text=='Ready':
            self.statusBar.setStyleSheet('color: green; font-weight: bold;')
        else:
            self.statusBar.setStyleSheet('color: '+config['dialogTextColor']+'; font-weight: normal;')

        self.statusBar.showMessage(text)


    @staticmethod
    def clearLayout(layout: QtWidgets.QLayout) -> None:
        """
        Clear a pyqt layout, from:
        https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt

        Parameters
        ----------
        layout : QtWidgets.QLayout
            Qt layout to be cleared
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()



    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Method called when closing the main app.
        Close every 1d and 2d plot opened.
        """

        for key in list(self._refs.keys()):
            # For 2d plot
            if self.getPlotWindowType(key) == '2d':
                keyToDelete = list(self._refs[key]['plot'].keys())
                for subkey in keyToDelete:
                    self._refs[key]['plot'][subkey].o()
            # For 1d plot
            else:
                self._refs[key]['plot'].o()
    


    def cleanCheckBox(self, plotRef     : str,
                            windowTitle : str,
                            runId       : int,
                            label       : Union[str, list]) -> None:
        """
        Method called by the QDialog plot when the user close the plot window.
        We propagate that event to the mainWindow to uncheck the checkbox and
        clean the reference, see self._refs.

        Parameters:
        plotRef : str
            Reference of the plot, see getPlotRef.
        windowTitle : str
            Window title, see getWindowTitle.
        runId : int
            Data run id of the database.
        label : str
            Label of the dependent parameter.
        """

        # If the closed curve is currently being displayed in the parameter table
        if self.currentDatabase == windowTitle and self.getRunId() == runId:
            # If 1d plot
            if isinstance(label, list):
                # If the current displayed parameters correspond to the one which has
                # been closed, we uncheck all the checkbox listed in the table
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 2)
                    widget.setChecked(False)
            # If 2d plot
            else:
                # We uncheck only the plotted parameter
                targetedZaxis = label.split('[')[0][:-1]
                for row in range(self.tableWidgetParameters.rowCount()):
                    if targetedZaxis == self.tableWidgetParameters.item(row, 3).text():
                        widget = self.tableWidgetParameters.cellWidget(row, 2)
                        widget.setChecked(False)

        # Unchecking the checkbox automatically called the removeplot method
        # However this method must be called even if the dependent parameter
        # closed was not in the parameter table
        else:
            self.removePlot(plotRef, label)



    ###########################################################################
    #
    #
    #                           QCoDes data handling methods
    #
    #
    ###########################################################################



    def getNbTotalRun(self, refresh_db: bool=False) -> int:
        """
        Return the total number of run in current database

        Parameters
        ----------
        refresh_db : bool, default False
            If False return the total number of run currently displayed.
            If True make a sql query to the db to get the total number of run.
        """

        if refresh_db:
            self.nbTotalRun = self.qcodesDatabase.getNbTotalRun()

        return self.nbTotalRun



    def getRunId(self) -> int:
        """
        Return the current selected run id.
        if Live plot mode, return the total number of run.
        """

        if self.livePlotMode:
            return self.getNbTotalRun()
        else:

            # If not in liveplot mode we get the runId from the gui to avoid
            # a sql call
            # First we try to get it from the database table
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            runId = self.tableWidgetDataBase.model().index(currentRow, 0).data()

            # If it doesn't exist, we try the parameter table
            if runId is None:
                
                item = self.tableWidgetParameters.item(0, 0)
                
                # This occurs when user is looking to csv, s2p of bluefors files
                # In this case the runid is 0
                if item is None:
                    runId = 0
                else:
                    runId = item.text()

            return int(runId)



    def getRunExperimentName(self) -> str:
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



    def getWindowTitle(self) -> str:
        """
        Return a title which will be used as a plot window title.
        """

        return self.currentDatabase



    def getPlotTitle(self) -> str:
        """
        Return a plot title in a normalize way displaying the folders and
        file name.
        """

        # If BlueFors log files
        if self.importblueFors.isBlueForsFolder(self.currentDatabase):
            return self.currentDatabase
        # If csv or s2p files we return the filename without the extension
        elif self.currentDatabase[-3:].lower() in ['csv', 's2p']:
            return self.currentDatabase[:-4]
        else:
            # If user only wants the database path
            if config['displayOnlyDbNameInPlotTitle']:
                title = self.currentDatabase
            # If user wants the database path
            else:
                title = os.path.normpath(self.currentPath).split(os.path.sep)[2:]
                title = '/'.join(title)

            title = title+'<br>'+str(self.getRunId())+' - '+self.getRunExperimentName()
            return title



    def getPlotRef(self) -> str:
        """
        Return a reference for the plot window.
        This should be unique for a given set of data.
        """

        # If BlueFors log files
        if self.importblueFors.isBlueForsFolder(self.currentDatabase):
            return os.path.abspath(self.currentDatabase)
        # If csv or s2p files we return the filename without the extension
        elif self.currentDatabase[-3:].lower() in ['csv', 's2p']:
            return os.path.abspath(self.currentDatabase)
        else:
            return os.path.abspath(self.currentDatabase)+str(self.getRunId())



    def getCurveId(self, label: str) -> str:
        """
        Return an id for a curve in a plot.
        Should be unique for every curve.

        Parameters
        ----------
        label : str
            Parameter label from which the curveId is obtained.
        """ 

        return os.path.abspath(self.currentDatabase)+str(self.getRunId())+str(label)



    def getPlotWindowType(self, plotRef: str ) -> Union[str, None]:
        """
        Handle the fact that the 1d and 2d plot reference are stored differently.
        Return the plot type either "1d" or "2d".

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getPlotRef.
        """

        try:
            if isinstance(self._refs[plotRef]['plot'], dict):
                return '2d'
            else:
                return '1d'
        except KeyError:
            return None



    ###########################################################################
    #
    #
    #                           Live plotting
    #
    #
    ###########################################################################


    def enableLivePlot(self, enable: bool) -> None:
        """
        Enable or disable GUI for the liveplotting mode
        Useful when the GUI is busy and we do not want user to go to liveplot
        mode.
        """

        if enable:
            self.checkBoxLivePlot.setEnabled(True)
            self.spinBoxLivePlot.setEnabled(True)
            self.labelLivePlot.setEnabled(True)
            self.labelLivePlot2.setEnabled(True)
            self.labelLivePlotDataBase.setEnabled(True)
            self.labelLivePlotDataBase.setText(self.currentDatabase[:-3])
        else:
            self.checkBoxLivePlot.setEnabled(False)
            self.spinBoxLivePlot.setEnabled(False)
            self.labelLivePlot.setEnabled(False)
            self.labelLivePlot2.setEnabled(False)
            self.labelLivePlotDataBase.setEnabled(False)
            self.labelLivePlotDataBase.setText('')



    def getLivePlotRef(self) -> Union[None, str]:
        """
        Return the reference of the live plot window.
        If no live plot are displayed, return None.
        """
        
        
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


                    # We click on the third parameter, which will launch a plot
                    self.parameterCellClicked(0,2)

                    # We update the total number of run
                    self.oldTotalRun = nbtotalRun

                    # We save the fact that we have to update an existing live plot
                    self.livePlotFetchData = True

            else:
                self.oldTotalRun = self.getNbTotalRun(True)


        # If we have to update the data of a livePlot
        # and if we are not already downlading data
        if self.livePlotFetchData and not self.dataDowloading:

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
                        
                        dependentParamName = self.tableWidgetParameters.item(row, 3).text()
                        data = self.getData(livePlotRef, dependentParamName)

            # If the live plot is a 2d plot
            else:
                # We get which parameters has to be updated
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 2)
                    
                    # For every checked parameter, we update the data
                    if widget.isChecked():

                        dependentParamName = self.tableWidgetParameters.item(row, 3).text()
                        data = self.getData(livePlotRef, dependentParamName)

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



    def updateList1dCurvesLabels(self) -> None:
        """
        Is called when the user add or delete a plot.
        See addPlot and removePlot
        The method creates a list of all displayed 1d plot window object and
        send it to all displayed 1d plot windows via the updatePlottedCurvesList
        method.
        """

        if len(self._refs) > 0:
            
            plotWindows = []
            for key, val in self._refs.items():

                # For 1d plot window
                if self.getPlotWindowType(key) == '1d':
                    plotWindows.append(val['plot'])
        
            for key, val in self._refs.items():
                # For 1d plot window
                if self.getPlotWindowType(key) == '1d':
                    val['plot'].updatePlottedCurvesList(plotWindows)



    def updatePlot(self, plotRef        : str,
                         progressBarKey : str,
                         data           : list,
                         xLabel         : str,
                         yLabel         : str,
                         zLabel         : str=None) -> None:
        """
        Methods called in live plot mode to update plot.
        This method must have the same signature as addPlot.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getPlotRef.
        progressBarKey : str
            Key to the progress bar in the dict progressBars.
        data : list
            For 1d plot: [xData, yData]
            For 2d plot: [xData, yData, zData]
        xLabel : str
            Label for the xAxis, see getDependentLabel for qcodes data.
        yxLabel : str
            Label for the yAxis, see getDependentLabel for qcodes data.
        zLabel : str, default None
            Only for 2d data.
            Label for the zAxis, see getDependentLabel for qcodes data.
        """
        
        
        if progressBarKey in self.progressBars:
            self.removeProgressBar(progressBarKey)


        # 1d plot
        if len(data)==2:

            self._refs[plotRef]['plot'].updatePlotDataItem(x           = data[0],
                                                           y           = data[1],
                                                           curveId     = self.getCurveId(yLabel),
                                                           curveLegend = None,
                                                           autoRange   = True)
        # 2d plot
        elif len(data)==3:

            # We update the 2d plot data
            self._refs[plotRef]['plot'][zLabel].updateImageItem(x=data[0],
                                                                y=data[1],
                                                                z=data[2])

            # If there are slices, we update them as well
            if len(self._refs[plotRef]['plot'][zLabel].infiniteLines)>0:
                for curveId, lineItem in self._refs[plotRef]['plot'][zLabel].infiniteLines.items():
                    
                    # We need the data of the slice
                    sliceX, sliceY, sliceLegend = self._refs[plotRef]['plot'][zLabel].getDataSlice(lineItem)

                    # We find its orientation
                    if lineItem.angle == 90:
                        sliceOrientation = 'vertical'
                    else:
                        sliceOrientation = 'horizontal'

                    # We update the slice data
                    self._refs[plotRef]['plot'][zLabel]\
                    .linked1dPlots[sliceOrientation]\
                    .updatePlotDataItem(x           = sliceX,
                                        y           = sliceY,
                                        curveId     = curveId,
                                        curveLegend = sliceLegend,
                                        autoRange   = True)

        self.setStatusBarMessage('Ready')

        # Flag
        self.dataDowloading = False



    def addPlot(self, plotRef        : str,
                      progressBarKey : str,
                      data           : list,
                      xLabel         : str,
                      yLabel         : str,
                      zLabel         : str=None) -> None:
        """
        Methods called once the data are downloaded to add a plot of the data.
        Discriminate between 1d and 2d plot through the length of data list.
        For 1d plot, data having the sample plotRef do not launch a new plot
        window but instead are plotted in the window sharing the same plotRef.
        Once the data are plotted, run updateList1dCurvesLabels.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getPlotRef.
        progressBarKey : str
            Key to the progress bar in the dict progressBars.
        data : list
            For 1d plot: [xData, yData]
            For 2d plot: [xData, yData, zData]
        xLabel : str
            Label for the xAxis, see getDependentLabel for qcodes data.
        yxLabel : str
            Label for the yAxis, see getDependentLabel for qcodes data.
        zLabel : str, default None
            Only for 2d data.
            Label for the zAxis, see getDependentLabel for qcodes data.
        """

        # The method is called when the data have been downloaded so we remove
        # the progress bar.
        
        if progressBarKey in self.progressBars:
            self.removeProgressBar(progressBarKey)
        
        if data is None:
            return
    
        self.setStatusBarMessage('Launching '+str(len(data)-1)+'d plot')


        # Add the curve reference to the reference dict
        # Usually to add a curve to an existing 1d plot window
        if plotRef in self._refs:
            self._refs[plotRef]['nbCurve'] += 1
        # Add the plot reference to the reference dict
        else:
            self._refs[plotRef] = {'nbCurve': 1}
        
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
                              plotRef        = plotRef,
                              curveId        = self.getCurveId(yLabel),
                              timestampXAxis=self.importblueFors.isBlueForsFolder(self.currentDatabase))

                self._refs[plotRef]['plot']     = p
                self._refs[plotRef]['livePlot'] = self.livePlotMode
                self._refs[plotRef]['plot'].show()

            # If the QDialog already exists, we add a curve to it
            else:
                self._refs[plotRef]['plot'].addPlotDataItem(x            = data[0],
                                                            y            = data[1],
                                                            curveId      = self.getCurveId(yLabel),
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
                          cleanCheckBox  = self.cleanCheckBox,
                          plotRef        = plotRef)

            self._refs[plotRef]['livePlot'] = self.livePlotMode

            # If user wants to plot more than one parameter we launch one plot
            # window per parameter
            if self._refs[plotRef]['nbCurve'] == 1:
                self._refs[plotRef]['plot'] = {zLabel : p}
            else:
                self._refs[plotRef]['plot'][zLabel] = p

            self._refs[plotRef]['plot'][zLabel].show()
        
        self.setStatusBarMessage('Ready')
        self.updateList1dCurvesLabels()

        # Flag
        self.dataDowloading = False



    def removePlot(self, plotRef: str, label: str) -> None:
        """
        Method call when data are remove from the GUI.
        If the data plot window is open, close it.
        Then remove the reference of the plot window from self._refs.
        
        Once the data are plotted, run updateList1dCurvesLabels.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getPlotRef.
        label : str
            Label of the data to be removed.
            See getDependentLabel for qcodes data
        """
        
        # We are dealing with 2d plot
        plotType = self.getPlotWindowType(plotRef)
        if plotType is None:
            return
        elif plotType == '2d':
            if len(self._refs[plotRef]['plot'])>1:
                self._refs[plotRef]['plot'][label].o()
                del(self._refs[plotRef]['plot'][label])
            else:
                self._refs[plotRef]['plot'][label].o()
                del(self._refs[plotRef])
        # We are dealing with 1d plot
        else:
            
            # If there is more than one curve, we remove one curve
            if self._refs[plotRef]['nbCurve'] > 1:
                
                curveId = [key for key in self._refs[plotRef]['plot'].curves.keys() if label in key][0]
                self._refs[plotRef]['plot'].removePlotDataItem(curveId=curveId)
                self._refs[plotRef]['nbCurve'] -= 1
            # If there is one curve we close the plot window
            else:
                self._refs[plotRef]['plot'].o()
                del(self._refs[plotRef])

            # Update the list of currently plotted dependent parametered on all
            # the plotted window
            self.updateList1dCurvesLabels()



    ###########################################################################
    #
    #
    #                           Data 
    #
    #
    ###########################################################################



    def getData(self, plotRef: str, dependentParamName: str) -> None:
        """
        Called when user wants to plot qcodes data.
        Create a progress bar in the status bar.
        Launched a thread which will download the data, display the progress in
        the progress bar and call addPlot when the data are downloaded.

        Parameters
        ----------
        row : int
            Current row of the parameters table
        dependentParamName : str
            Name of the dependent parameter from which data will be downloaded.
        """

        # Flag
        self.dataDowloading = True

        progressBarKey = self.addProgressBarInStatusBar()
        
        runId = self.getRunId()
        worker = LoadDataThread(runId,
                                dependentParamName,
                                plotRef,
                                progressBarKey,
                                self.qcodesDatabase.getParameterData,
                                self.qcodesDatabase.getParameterInfo,
                                self.getDependentLabel)
        # Connect signals
        worker.signals.setStatusBarMessage.connect(self.setStatusBarMessage)
        worker.signals.updateProgressBar.connect(self.updateProgressBar)

        # If the live plot mode is on, we have to update the plot instead
        # of adding a new plot
        if self.livePlotMode:
            if plotRef in self._refs.keys():
                paramsDependent = self.qcodesDatabase.getListDependentFromRunId(runId)
                dependentParamDict = [i for i in paramsDependent if i['name']==dependentParamName][0]
                curveId = self.getCurveId(self.getDependentLabel(dependentParamDict))

                if self.getPlotWindowType(plotRef)=='1d':
                    if curveId in self._refs[plotRef]['plot'].curves.keys():
                        worker.signals.done.connect(self.updatePlot)
                    else:
                        worker.signals.done.connect(self.addPlot)
                else:
                    if dependentParamName in [i.split('[')[0][:-1] for i in self._refs[plotRef]['plot'].keys()]:
                        worker.signals.done.connect(self.updatePlot)
                    else:
                        worker.signals.done.connect(self.addPlot)
            else:
                worker.signals.done.connect(self.addPlot)
        else:
            worker.signals.done.connect(self.addPlot)

        # Execute the thread
        self.threadpool.start(worker)

