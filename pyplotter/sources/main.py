# This Python file uses the following encoding: utf-8
import os
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
import time
from typing import Union, Callable, List, Optional
import uuid

from ..ui.hBoxLayoutLabelPath import HBoxLayoutLabelPath

from .loadCSV import LoadCSV
from .loadBluefors import LoadBlueFors
# from .workers.loadDataBase import LoadDataBaseThread
# from .workers.loadDataFromRun import LoadDataFromRunThread
# from .workers.check_nb_run_database_thread import dataBaseCheckNbRunThread
# from .workers.loadRunInfo import loadRunInfoThread
from .config import loadConfigCurrent
config = loadConfigCurrent()
from .plot_1d_app import Plot1dApp
from .plot_2d_app import Plot2dApp
from ..ui import main
from ..ui.db_menu_widget import dbMenuWidget
# from ..ui.tableWidgetItemNumOrdered import TableWidgetItemNumOrdered
from ..sources.dialogs.dialog_liveplot import MenuDialogLiveplot
from .pyqtgraph import pg

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../ui/pictures/')


class MainApp(QtWidgets.QMainWindow, main.Ui_MainWindow, dbMenuWidget):

    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)
    signalRemoveProgressBar    = QtCore.pyqtSignal(QtWidgets.QProgressBar)


    def __init__(self, QApplication,
                       parent=None):

        super(MainApp, self).__init__(parent)
        self.setupUi(self)

        self.qapp = QApplication

        # Can't promote layout on qtdesigner...

        self.hBoxLayoutPath = HBoxLayoutLabelPath()
        self.verticalLayout_12.addLayout(self.hBoxLayoutPath)


        self.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        # Connect UI

        # Resize the cell to the column content automatically
        # self.tableWidgetDataBase.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # self.tableWidgetParameters.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # self.tableWidgetParameters.setColumnHidden(0, True)
        # self.tableWidgetParameters.setColumnHidden(1, True)

        # Connect event
        # self.tableWidgetDataBase.currentCellChanged.connect(self.runClicked)
        # self.tableWidgetDataBase.doubleClicked.connect(self.runDoubleClicked)
        # self.tableWidgetDataBase.keyPressed.connect(self.tableWidgetDataBasekeyPress)
        # self.tableWidgetParameters.cellClicked.connect(self.parameterCellClicked)

        # self.checkBoxHidden.stateChanged.connect(lambda : self.checkBoxHiddenClick(self.checkBoxHidden))

        self.lineEditFilterSnapshot.signallineEditFilterSnapshotTextEdited.connect(self.treeViewSnapshot.searchItem)

        self.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)

        # Connect menuBar signal
        self.menuBarMain.signalUpdateStyle.connect(self.updateStyle)
        self.menuBarMain.signalOpenDialogLivePlot.connect(self.openDialogLiveplot)

        self.hBoxLayoutPath.signalButtonClick.connect(self.tableWidgetFolder.folderOpened)

        self.treeViewSnapshot.signalLineEditSnapshotClean.connect(self.lineEditFilterSnapshot.clean)
        self.checkBoxHidden.signalcheckBoxHiddenClick.connect(self.tableWidgetDataBase.checkBoxHiddenClick)

        self.pushButtonOpenFolder.signalFolderOpened.connect(self.tableWidgetFolder.folderOpened)

        self.statusBarMain.signalDatabaseClick.connect(self.tableWidgetDataBase.databaseClick)
        self.statusBarMain.signalParameterClick.connect(self.tableWidgetParameter.getData)

        self.tableWidgetFolder.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.tableWidgetFolder.signalDatabaseClick.connect(self.statusBarMain.databaseClick)
        self.tableWidgetFolder.signalDatabaseClick.connect(self.checkBoxHidden.databaseClick)
        self.tableWidgetFolder.signalUpdateLabelPath.connect(self.hBoxLayoutPath.updateLabelPath)
        self.tableWidgetFolder.first_call()

        self.tableWidgetDataBase.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.tableWidgetDataBase.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.tableWidgetDataBase.signalUpdateProgressBar.connect(self.statusBarMain.updateProgressBar)
        self.tableWidgetDataBase.signalDatabaseClickDone.connect(self.tableWidgetFolder.databaseClickDone)
        self.tableWidgetDataBase.signalDatabaseClickDone.connect(self.checkBoxHidden.databaseClickDone)
        self.tableWidgetDataBase.signalRunClick.connect(self.tableWidgetParameter.runClick)
        self.tableWidgetDataBase.signalDatabaseStars.connect(self.tableWidgetFolder.databaseStars)
        self.tableWidgetDataBase.signalDatabaseUnstars.connect(self.tableWidgetFolder.databaseUnstars)
        self.tableWidgetDataBase.signalCheckBoxHiddenHideRow.connect(self.checkBoxHidden.hideRow)
        self.tableWidgetDataBase.first_call()

        self.tableWidgetParameter.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.tableWidgetParameter.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.tableWidgetParameter.signalUpdateProgressBar.connect(self.statusBarMain.updateProgressBar)
        self.tableWidgetParameter.signalParameterClick.connect(self.statusBarMain.parameterClick)
        self.tableWidgetParameter.signalCleanSnapshot.connect(self.treeViewSnapshot.cleanSnapshot)
        self.tableWidgetParameter.signalAddSnapshot.connect(self.treeViewSnapshot.addSnapshot)
        self.tableWidgetParameter.signalLineEditSnapshotEnabled.connect(self.lineEditFilterSnapshot.enabled)
        self.tableWidgetParameter.signalLabelSnapshotEnabled.connect(self.labelSnapshot.enabled)
        self.tableWidgetParameter.signalAddPlotToRefs.connect(self.addPlotToRefs)
        self.tableWidgetParameter.signalLoadedDataFull.connect(self.loadedDataFull)
        self.tableWidgetParameter.first_call()
        # self.tableWidgetParameter.signalAddCurveToRefs.connect(self.addCurveToRefs)

        # self.tableWidgetParameter.signalClosePlot.connect(self.closePlot)



        # References of all opened plot window.
        # Structure:
        # {plotRef : plotApp}
        self._plotRefs = {}

        # {curveRefs : curve}
        self._curveRefs = {}

        # Attribute to control the display of data file info when user click of put focus on a item list
        self._folderUpdating  = False # To avoid calling the signal when updating folder content
        self._guiInitialized = True # To avoid calling the signal when starting the GUI


        # Flag
        self._dataDowloadingFlag = False
        # self._progressBars = {}
        self._databaseClicking = False  # To avoid the opening of two database as once

        self._currentDatabase    = None

        # Handle connection and requests to qcodes database
        # self.qcodesDatabase = QcodesDatabase(self.setStatusBarMessage)
        # Handle log files from bluefors fridges
        self.LoadBlueFors = LoadBlueFors(self)
        # Handle csv files
        self.LoadCSV      = LoadCSV(self)

        self.threadpool = QtCore.QThreadPool()

        self.signalSendStatusBarMessage.emit('Ready', 'green')


    ###########################################################################
    #
    #
    #                           Folder browsing
    #
    #
    ###########################################################################


    @QtCore.pyqtSlot(dict)
    def updateStyle(self, newConfig: dict) -> None:
        """
        Update the style of the full app.

        Args:
            newConfig: New configuration dict containing the style to be applied.
        """

        if newConfig['style']!=config['style']:
            if newConfig['style']=='qdarkstyle':
                import qdarkstyle
                self.qapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            elif newConfig['style']=='qbstyles':
                import qdarkstyle
                self.qapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            elif newConfig['style']=='white':
                self.qapp.setStyleSheet(self.qapp.setStyle('Oxygen'))

        if len(self._plotRefs) > 0:

            for plot in self._plotRefs.values():
                plot.config = newConfig
                plot.updateStyle()







    ###########################################################################
    #
    #
    #                           Database browsing
    #
    #
    ###########################################################################



    # def databaseClick(self) -> None:
    #     """
    #     Display the content of the clicked dataBase into the database table
    #     which will then contain all runs.
    #     """

    #     if self._databaseClicking:
    #         return

    #     self._databaseClicking = True

    #     # We show the database is now opened
    #     if self.isDatabaseStared():

    #         currentRow = self.tableWidgetFolder.currentIndex().row()
    #         item = self.tableWidgetFolder.item(currentRow, 0)
    #         item.setIcon(QtGui.QIcon(PICTURESPATH+'databaseOpenedStared.png'))
    #     else:
    #         currentRow = self.tableWidgetFolder.currentIndex().row()
    #         item = self.tableWidgetFolder.item(currentRow, 0)
    #         item.setIcon(QtGui.QIcon(PICTURESPATH+'databaseOpened.png'))

    #     # Disable interactivity
    #     self.checkBoxHidden.setChecked(False)
    #     self.checkBoxHidden.setEnabled(False)

    #     # Update label
    #     self.labelCurrentDataBase.setText(self._currentDatabase[:-3])

    #     # Remove all previous row in the table
    #     self.clearTableWidget(self.tableWidgetDataBase)

    #     # Modify the resize mode so that the initial view has an optimized
    #     # column width
    #     self.tableWidgetDataBase.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)
    #     self.tableWidgetDataBase.verticalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)

    #     # self.qcodesDatabase.databasePath = os.path.join(self.currentPath, self._currentDatabase)

    #     # Add a progress bar in the statusbar
    #     progressBarKey = self.addProgressBarInStatusBar()
    #     self.databaseAbsPath = os.path.normpath(os.path.join(self.currentPath, self._currentDatabase)).replace("\\", "/")

    #     # Create a thread which will read the database
    #     worker = LoadDataBaseThread(self.databaseAbsPath,
    #                                 progressBarKey)

    #     # Connect signals
    #     worker.signals.setStatusBarMessage.connect(self.setStatusBarMessage)
    #     worker.signals.addRows.connect(self.databaseClickAddRows)
    #     worker.signals.updateProgressBar.connect(self.updateProgressBar)
    #     worker.signals.updateDatabase.connect(self.databaseClickDone)

    #     # Execute the thread
    #     self.threadpool.start(worker)



    # def databaseClickAddRows(self, lrunId          : List[int],
    #                                  ldim            : List[str],
    #                                  lexperimentName : List[str],
    #                                  lsampleName     : List[str],
    #                                  lrunName        : List[str],
    #                                  lstarted        : List[str],
    #                                  lcompleted      : List[str],
    #                                  lrunRecords     : List[str],
    #                                  nbTotalRun     : int,
    #                                  progressBarKey : str) -> None:
    #     """
    #     Called by another thread to fill the database table.
    #     Each call add n rows into the table.
    #     """


    #     if lrunId[0]==1:
    #         self.statusBarMain.clearMessage()
    #         self.tableWidgetDataBase.setRowCount(nbTotalRun)
    #     self.updateProgressBar(progressBarKey, int(lrunId[0]/nbTotalRun*100), text='Displaying database: run '+str(lrunId[0])+'/'+str(nbTotalRun))

    #     # We go through all lists of parameters and for each list element, we add
    #     # a row in the table
    #     for (runId, dim, experimentName, sampleName, runName, started, completed,
    #          runRecords) in zip(lrunId,
    #          ldim, lexperimentName, lsampleName, lrunName, lstarted, lcompleted,
    #          lrunRecords):

    #         itemRunId = TableWidgetItemNumOrdered(str(runId))

    #         # If the run has been stared by an user
    #         if runId in self.getRunStared():
    #             itemRunId.setIcon(QtGui.QIcon(PICTURESPATH+'star.png'))
    #             itemRunId.setForeground(QtGui.QBrush(QtGui.QColor(*config['runStaredColor'])))
    #         # If the user has hidden a row
    #         elif runId in self.getRunHidden():
    #             itemRunId.setIcon(QtGui.QIcon(PICTURESPATH+'trash.png'))
    #             itemRunId.setForeground(QtGui.QBrush(QtGui.QColor(*config['runHiddenColor'])))
    #         else:
    #             itemRunId.setIcon(QtGui.QIcon(PICTURESPATH+'empty.png'))

    #         self.tableWidgetDataBase.setItem(runId-1, 0, itemRunId)
    #         self.tableWidgetDataBase.setItem(runId-1, 1, QtWidgets.QTableWidgetItem(dim))
    #         self.tableWidgetDataBase.setItem(runId-1, 2, QtWidgets.QTableWidgetItem(experimentName))
    #         self.tableWidgetDataBase.setItem(runId-1, 3, QtWidgets.QTableWidgetItem(sampleName))
    #         self.tableWidgetDataBase.setItem(runId-1, 4, QtWidgets.QTableWidgetItem(runName))
    #         self.tableWidgetDataBase.setItem(runId-1, 5, QtWidgets.QTableWidgetItem(started))
    #         self.tableWidgetDataBase.setItem(runId-1, 6, QtWidgets.QTableWidgetItem(completed))
    #         self.tableWidgetDataBase.setItem(runId-1, 7, TableWidgetItemNumOrdered(runRecords))

    #         if runId in self.getRunHidden():
    #             self.tableWidgetDataBase.setRowHidden(runId-1, True)



    # def databaseClickDone(self,
    #                         progressBarKey : str,
    #                         error          : bool,
    #                         nbTotalRun     : int) -> None:
    #     """
    #     Called when the database table has been filled

    #     Parameters
    #     ----------
    #     progressBarKey : str
    #         Key to the progress bar in the dict progressBars.
    #     error : bool

    #     nbTotalRun : int
    #         Total number of run in the current database.
    #         Simply stored for other purposes and to avoid other sql queries.
    #     """

    #     self.removeProgressBar(progressBarKey)

    #     if not error:
    #         self.tableWidgetDataBase.setSortingEnabled(True)
    #         self.tableWidgetDataBase.sortItems(0, QtCore.Qt.DescendingOrder)
    #         self.tableWidgetDataBase.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
    #         self.tableWidgetDataBase.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    #         # Enable database interaction
    #         self.checkBoxHidden.setEnabled(True)

    #         self.setStatusBarMessage('Ready')


    #     # We store the total number of run
    #     self.nbTotalRun = nbTotalRun

    #     # Done
    #     self._databaseClicking = False

    #     # We show the database is now closed
    #     if self.isDatabaseStared():

    #         currentRow = self.tableWidgetFolder.currentIndex().row()
    #         item = self.tableWidgetFolder.item(currentRow, 0)
    #         item.setIcon(QtGui.QIcon(PICTURESPATH+'databaseStared.png'))
    #     else:
    #         currentRow = self.tableWidgetFolder.currentIndex().row()
    #         item = self.tableWidgetFolder.item(currentRow, 0)
    #         item.setIcon(QtGui.QIcon(PICTURESPATH+'database.png'))

    #     self.dataBaseCheckNbRun()



    # def dataBaseCheckNbRun(self):
    #     """
    #     Method called by databaseClickDone.
    #     Launch a thread every config['delayBetweendataBaseNbRunCheck'] ms
    #     which will launch a process to get the nb of run in the database.
    #     If that number is the same as the database currently displayed, nothing
    #     happen, otherwise, the method databaseClick is called which will
    #     refresh the diaplayed database.
    #     """

    #     # From launch a thread which will periodically check if the database has
    #     # more run that what is currently displayed
    #     worker = dataBaseCheckNbRunThread(self.databaseAbsPath,
    #                                       self.nbTotalRun)

    #     # Connect signals
    #     worker.signals.dataBaseUpdate.connect(self.dataBaseUpdate)
    #     worker.signals.dataBaseCheckNbRun.connect(self.dataBaseCheckNbRun)

    #     # Execute the thread
    #     self.threadpool.start(worker)



    # def dataBaseUpdate(self, databasePathToUpdate: str) -> None:
    #     """Method called by dataBaseCheckNbRunThread when the displayed database
    #     has not the same number of total run.
    #     Call databaseClick if the displayed database shares the same path
    #     as the database check by the thread.

    #     Args:
    #         databasePathToUpdate : path of the checked database
    #     """

    #     if databasePathToUpdate==self.databaseAbsPath:
    #         self.databaseClick()



    # def runDoubleClicked(self) -> None:
    #     """
    #     Called when user double click on the database table.
    #     Display the measured dependent parameters in the table Parameters.
    #     Simulate the user clicking on the first dependent parameter, effectively
    #     launching its plot.
    #     """

    #     # We simulate a single click while propagating the double-click info
    #     self.runClicked(doubleClicked=True)



    # def runClicked(self, currentRow: int=0,
    #                      currentColumn: int=0,
    #                      previousRow: int=0,
    #                      previousColumn: int=0,
    #                      doubleClicked: bool=False) -> None:
    #     """
    #     When clicked display the measured dependent parameters in the
    #     tableWidgetPtableWidgetParameters.
    #     Database is accessed through a thread, see runClickedFromThread.
    #     """

    #     # When the user click on another database while having already clicked
    #     # on a run, the runClicked event is happenning even if no run have been clicked
    #     # This is due to the "currentCellChanged" event handler.
    #     # We catch that false event and return nothing
    #     if self._databaseClicking:
    #         return

    #     runId          = self.getRunId()
    #     experimentName = self.getRunExperimentName()
    #     runName        = self.getRunName()

    #     self.setStatusBarMessage('Loading run parameters')

    #     worker = loadRunInfoThread(self.databaseAbsPath,
    #                                runId,
    #                                experimentName,
    #                                runName,
    #                                doubleClicked)
    #     worker.signals.updateRunInfo.connect(self.runClickedFromThread)
    #     # Execute the thread
    #     self.threadpool.start(worker)



    # def runClickedFromThread(self, runId: int,
    #                                dependentList: list,
    #                                snapshotDict: dict,
    #                                experimentName: str,
    #                                runName: str,
    #                                doubleClicked: bool):

    #     runIdStr = str(runId)

    #     ## Update label
    #     self.labelCurrentRun.setText(runIdStr)
    #     self.labelCurrentMetadata.setText(runIdStr)

    #     ## Fill the tableWidgetParameters with the run parameters

    #     self.clearTableWidget(self.tableWidgetParameters)
    #     self.tableWidgetParameters.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)
    #     self.tableWidgetParameters.verticalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)

    #     for dependent in dependentList:

    #         rowPosition = self.tableWidgetParameters.rowCount()

    #         self.tableWidgetParameters.insertRow(rowPosition)

    #         cb = QtWidgets.QCheckBox()

    #         # We check if that parameter is already plotted
    #         if self.isParameterPlotted(dependent):
    #             cb.setChecked(True)

    #         self.tableWidgetParameters.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(runIdStr))
    #         self.tableWidgetParameters.setItem(rowPosition, 1, QtWidgets.QTableWidgetItem(str(experimentName)))
    #         self.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
    #         self.tableWidgetParameters.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(dependent['label']))
    #         self.tableWidgetParameters.setItem(rowPosition, 4, QtWidgets.QTableWidgetItem(dependent['unit']))


    #         independentString = config['sweptParameterSeparator'].join(dependent['depends_on'])
    #         self.tableWidgetParameters.setCellWidget(rowPosition, 5, QtWidgets.QLabel(independentString))

    #         # Get info specific to the run
    #         curveId         = self.getCurveId(name=dependent['name'], runId=runId)
    #         plotRef         = self.getPlotRef(paramDependent=dependent)
    #         plotTitle       = self.getPlotTitle()
    #         windowTitle     = self.getWindowTitle(runId=runId, runName=runName)
    #         databaseAbsPath = os.path.normpath(os.path.join(self.currentPath, self._currentDatabase)).replace("\\", "/")

    #         # Each checkbox at its own event attached to it
    #         cb.toggled.connect(lambda state,
    #                                   dependentParamName    = dependent['name'],
    #                                   runId                 = runId,
    #                                   curveId               = curveId,
    #                                   plotTitle             = plotTitle,
    #                                   windowTitle           = windowTitle,
    #                                   dependent             = dependent,
    #                                   plotRef               = plotRef,
    #                                   databaseAbsPath       = databaseAbsPath: self.parameterClicked(state,
    #                                                                                                  dependentParamName,
    #                                                                                                  runId,
    #                                                                                                  curveId,
    #                                                                                                  plotTitle,
    #                                                                                                  windowTitle,
    #                                                                                                  dependent,
    #                                                                                                  plotRef,
    #                                                                                                  databaseAbsPath))


    #     self.tableWidgetParameters.setSortingEnabled(True)
    #     self.tableWidgetParameters.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
    #     self.tableWidgetParameters.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    #     ## Fill the listWidgetMetada with the station snapshot
    #     self.lineEditFilterSnapshot.setEnabled(True)
    #     self.labelFilter.setEnabled(True)

    #     # Update the run snapshot
    #     self.lineEditFilterSnapshot.cleanSnapshot()
    #     self.lineEditFilterSnapshot.addSnapshot(snapshotDict)


    #     self.setStatusBarMessage('Ready')

    #     # If a double click is detected, we launch a plot of the first parameter
    #     if doubleClicked:
    #         self.parameterCellClicked(0, 2)



    # def parameterCellClicked(self, row: int, column: int) -> None:
    #     """
    #     Handle event when user click on the cell containing the checkbox.
    #     Basically toggle the checkbox and launch the event associated to the
    #     checkbox

    #     Parameters
    #     ----------
    #         row, column : int, int
    #         Row and column where the user clicked
    #     """

    #     # If user clicks on the cell containing the checkbox
    #     if column==2:
    #         cb = self.tableWidgetParameters.cellWidget(row, 2)
    #         cb.toggle()



    # def parameterClicked(self,
    #                      state              : bool,
    #                      dependentParamName : str,
    #                      runId              : int,
    #                      curveId            : str,
    #                      plotTitle          : str,
    #                      windowTitle        : str,
    #                      paramDependent     : dict,
    #                      plotRef            : str,
    #                      databaseAbsPath    : str) -> None:
    #     """
    #     Handle event when user clicked on data line.
    #     Either get data and display them or remove the data depending on state.

    #     Parameters
    #     ----------
    #     state : bool
    #         State of the checkbox
    #     dependentParamName : str
    #         Name of the dependent parameter from which data will be downloaded.
    #     runId : int
    #         Data run id in the current database
    #     curveId : str
    #         Id of the curve, see getCurveId.
    #     plotTitle : str
    #         Plot title, see getPlotTitle.
    #     windowTitle : str
    #         Window title, see getWindowTitle.
    #     paramDependent : dict
    #         Dependent parameter the user wants to see the data.
    #         This should be a qcodes dependent parameter dict.
    #     plotRef : str
    #         Reference to a plot window, see getPlotRef.
    #     """

    #     # If the checkbutton is checked, we downlad and plot the data
    #     if state:

    #         if len(paramDependent['depends_on'])>2:

    #             self.setStatusBarMessage('Plotter does not handle data whose dim>2', error=True)
    #             return
    #         else:
    #             self.getData(runId              = runId,
    #                          curveId            = curveId,
    #                          plotTitle          = plotTitle,
    #                          windowTitle        = windowTitle,
    #                          plotRef            = plotRef,
    #                          databaseAbsPath    = databaseAbsPath,
    #                          dependentParamName = dependentParamName)

    #     # If the checkbox is unchecked, we remove the plotted data
    #     else:

    #         self.removePlot(plotRef = plotRef,
    #                         curveId = curveId)



    ###########################################################################
    #
    #
    #                           Progress bar
    #
    #
    ###########################################################################



    # def addProgressBarInStatusBar(self) -> str:
    #     """
    #     Add the progress bar in the status bar.
    #     Usually called before a thread is launched to load something.

    #     Return
    #     ------
    #     progressBarKey : str
    #         An unique key coming from uuid.uuid4().
    #     """

    #     # Add a progress bar in the statusbar
    #     progressBarKey = str(uuid.uuid4())
    #     self._progressBars[progressBarKey] = QtWidgets.QProgressBar(self)
    #     self._progressBars[progressBarKey].decimal = 100
    #     self._progressBars[progressBarKey].setAlignment(QtCore.Qt.AlignCenter)
    #     self._progressBars[progressBarKey].setValue(0)
    #     # setting maximum value for 2 decimal points
    #     self._progressBars[progressBarKey].setMaximum(100*self._progressBars[progressBarKey].decimal)
    #     self._progressBars[progressBarKey].setTextVisible(True)
    #     self.statusBarMain.setSizeGripEnabled(False)
    #     self.statusBarMain.addPermanentWidget(self._progressBars[progressBarKey])

    #     return progressBarKey



    # def removeProgressBar(self, progressBarKey: str) -> None:
    #     """
    #     Remove the progress bar in the status bar.
    #     Usually called after a thread has loaded something.
    #     """

    #     self.statusBarMain.removeWidget(self._progressBars[progressBarKey])
    #     del self._progressBars[progressBarKey]



    # def updateProgressBar(self, key: str, val: int, text: str=None) -> None:
    #     """
    #     Update the progress bar in the status bar

    #     Parameters
    #     ----------
    #     key : str
    #         key from addProgressBarInStatusBar.
    #     val : int
    #         Value of the progress.
    #         Must be an int between 0 and 100.
    #     text : str
    #         Text to be shown on the progress bar.
    #     """

    #     if text is not None:
    #         self._progressBars[key].setFormat(text)
    #     self._progressBars[key].setValue(int(val*self._progressBars[key].decimal))



    ###########################################################################
    #
    #
    #                           GUI
    #
    #
    ###########################################################################



    def isParameterPlotted(self, paramDependent: dict) -> bool:
        """
        Return True when the displayed parameter is currently plotted.

        Parameters
        ----------
        paramDependent : dict
            qcodes dictionary of a dependent parameter
        """

        if len(self._plotRefs) > 0:

            plotRef = self.getPlotRef(paramDependent)

            # We iterate over all plotWindow
            for plot in self._plotRefs.values():

                if plot.plotType=='1d':
                    if plotRef in plot.plotRef:
                        if paramDependent['label'] in [curve.curveYLabel for curve in plot.curves.values()]:
                            return True
                if plot.plotType=='2d':
                    if plotRef in plot.plotRef:
                        if plot.zLabelText==paramDependent['label']:
                            return True

        return False



    # @staticmethod
    # def clearLayout(layout: QtWidgets.QLayout) -> None:
    #     """
    #     Clear a pyqt layout, from:
    #     https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt

    #     Parameters
    #     ----------
    #     layout : QtWidgets.QLayout
    #         Qt layout to be cleared
    #     """
    #     while layout.count():
    #         child = layout.takeAt(0)
    #         if child.widget():
    #             child.widget().deleteLater()



    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Method called when closing the main app.
        Close every 1d and 2d plot opened.
        """

        plotRefs = [plot for plot in self._plotRefs.keys()]
        # plot1d window open from a plo1d window are taken care by the plot1d itself
        # we so remove them from the selection
        plotRefs = [plotRef for plotRef in plotRefs if 'fft' not in plotRef]
        plotRefs = [plotRef for plotRef in plotRefs if 'derivative' not in plotRef]
        plotRefs = [plotRef for plotRef in plotRefs if 'primitive' not in plotRef]
        plotRefs = [plotRef for plotRef in plotRefs if 'histogram' not in plotRef]

        # Close everything
        [self._plotRefs[plotRef].o() for plotRef in plotRefs]



    # def cleanCheckBox(self, plotRef     : str,
    #                         windowTitle : str,
    #                         runId       : int,
    #                         label       : str) -> None:
    #     """
    #     Method called by the plot1d or plot2d plot when the user close the plot
    #     window. We propagate that event to the mainWindow to uncheck the
    #     checkbox and clean the reference, see self._plotRefs.

    #     Parameters:
    #     plotRef : str
    #         Reference of the plot, see getplotRef.
    #     windowTitle : str
    #         Window title, see getWindowTitle.
    #     runId : int
    #         Data run id of the database.
    #     label : str
    #         Label of the dependent parameter.
    #         Will be empty for signal from Plot1dApp since this parameter is only
    #         usefull for Plot2dApp.
    #     """

    #     # If the close plot window is a liveplot one
    #     if plotRef in self.getLivePlotRef():
    #         # if hasattr(self, '_livePlotDataSet'):
    #         if self._plotRefs[plotRef].plotType=='1d':
    #             curveIds = list(self._plotRefs[plotRef].curves.keys())
    #             [self.removePlot(plotRef, curveId) for curveId in curveIds]
    #         else:
    #             self.removePlot(plotRef, '')
    #         # del(self._livePlotDataSet)
    #     else:
    #         if self.getWindowTitle(runId=runId, runName=self.getRunName())==windowTitle and self.getRunId()==runId:

    #             # If 1d plot
    #             if self._plotRefs[plotRef].plotType=='1d':

    #                 # If the current displayed parameters correspond to the one which has
    #                 # been closed, we uncheck all the checkbox listed in the table
    #                 for row in range(self.tableWidgetParameters.rowCount()):
    #                     widget = self.tableWidgetParameters.cellWidget(row, 2)
    #                     widget.setChecked(False)
    #             # If 2d plot
    #             else:
    #                 # We uncheck only the plotted parameter
    #                 for row in range(self.tableWidgetParameters.rowCount()):
    #                     if label==self.tableWidgetParameters.item(row, 3).text():
    #                         widget = self.tableWidgetParameters.cellWidget(row, 2)
    #                         widget.setChecked(False)



    ###########################################################################
    #
    #
    #                           QCoDes data handling methods
    #
    #
    ###########################################################################



    # def getRunId(self) -> int:
    #     """
    #     Return the current selected run id.
    #     """

    #     # First we try to get it from the database table
    #     currentRow = self.tableWidgetDataBase.currentIndex().row()
    #     runId = self.tableWidgetDataBase.model().index(currentRow, 0).data()

    #     # If it doesn't exist, we try the parameter table
    #     if runId is None:

    #         item = self.tableWidgetParameters.item(0, 0)

    #         # This occurs when user is looking to csv, s2p of bluefors files
    #         # In this case the runid is 0
    #         if item is None:
    #             runId = 0
    #         else:
    #             runId = item.text()

    #     return int(runId)



    # def getCurveId(self, name: str,
    #                      runId: int) -> str:
    #     """
    #     Return an id for a curve in a plot.
    #     Should be unique for every curve.

    #     Parameters
    #     ----------
    #     name : str
    #         Parameter name from which the curveId is obtained.
    #     runId : int
    #         Id of the curve, see getCurveId.
    #     """

    #     return self._currentDatabase+str(runId)+str(name)



    # def getRunExperimentName(self) -> str:
    #     """
    #     Return the experiment name of the current selected run.
    #     if Live plot mode, return the experiment name of the last recorded run.
    #     """

    #     currentRow = self.tableWidgetDataBase.currentIndex().row()
    #     experimentName =  self.tableWidgetDataBase.model().index(currentRow, 2).data()
    #     if experimentName is None:
    #         experimentName = self.tableWidgetParameters.item(0, 1).text()

    #     return str(experimentName)



    # def getRunName(self) -> str:
    #     """
    #     Return the name of the current selected run.
    #     if Live plot mode, return the run name of the last recorded run.
    #     """

    #     currentRow = self.tableWidgetDataBase.currentIndex().row()
    #     runName =  self.tableWidgetDataBase.model().index(currentRow, 4).data()
    #     if runName is None:
    #         runName = self.tableWidgetParameters.item(0, 1).text()

    #     return str(runName)



    # def getWindowTitle(self, runId: int=None,
    #                          runName: str='') -> str:
    #     """
    #     Return a title which will be used as a plot window title.
    #     """

    #     windowTitle = str(self._currentDatabase)

    #     if config['displayRunIdInPlotTitle']:
    #         windowTitle += ' - '+str(runId)

    #     if config['displayRunNameInPlotTitle']:
    #         windowTitle += ' - '+runName

    #     return windowTitle



    # def getPlotTitle(self) -> str:
    #     """
    #     Return a plot title in a normalize way displaying the folders and
    #     file name.
    #     """

    #     # If no database have been selected ever
    #     if self._currentDatabase is None:
    #         return ''
    #     # If BlueFors log files
    #     elif self.LoadBlueFors.isBlueForsFolder(self._currentDatabase):
    #         return self._currentDatabase
    #     # If csv or s2p files we return the filename without the extension
    #     elif self._currentDatabase[-3:].lower() in ['csv', 's2p']:
    #         return self._currentDatabase[:-4]
    #     else:
    #         # If user only wants the database path
    #         if config['displayOnlyDbNameInPlotTitle']:
    #             title = self._currentDatabase
    #         # If user wants the database path
    #         else:
    #             title = os.path.normpath(self.currentPath).split(os.path.sep)[2:]
    #             title = '/'.join(title)

    #         title = title+'<br>'+str(self.getRunId())+' - '+self.getRunExperimentName()
    #         return title



    # def getPlotRef(self, paramDependent : dict) -> str:
    #     """
    #     Return a reference for a plot window.
    #     Handle the difference between 1d plot and 2d plot.

    #     Parameters
    #     ----------
    #     paramDependent : dict
    #         qcodes dictionary of a dependent parameter

    #     Return
    #     ------
    #     plotRef : str
    #         Unique reference for a plot window.
    #     """

    #     path = os.path.abspath(self._currentDatabase)

    #     # If BlueFors log files
    #     if self.LoadBlueFors.isBlueForsFolder(self._currentDatabase):
    #         dataPath = path
    #     # If csv or s2p files we return the filename without the extension
    #     elif self._currentDatabase[-3:].lower() in ['csv', 's2p']:
    #         dataPath = path
    #     else:
    #         dataPath = path+str(self.getRunId())


    #     if len(paramDependent['depends_on'])==2:
    #         return dataPath+paramDependent['name']
    #     else:
    #         return dataPath



    # def getLivePlotRef(self) -> list:
    #     """
    #     Return a list of the live plot windows references.
    #     Return an empty list if no liveplot window
    #     """
    #     refs = []
    #     # We get which open plot window is the liveplot one
    #     for ref, plot in self._plotRefs.items():
    #         if plot.livePlot:
    #             refs.append(ref)

    #     return refs



    ###########################################################################
    #
    #
    #                           Menu Signal
    #
    #
    ###########################################################################


    @QtCore.pyqtSlot()
    def openDialogLiveplot(self):

        self.menuDialogLiveplot = MenuDialogLiveplot(config,
                                                     self.addPlot,
                                                     self.cleanCheckBox,
                                                     self.getLivePlotRef,
                                                     self._plotRefs)



    ###########################################################################
    #
    #
    #                           Plotting
    #
    #
    ###########################################################################



    @QtCore.pyqtSlot(int, str, str, str, str, str, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str)
    def loadedDataFull(self, runId          : int,
                      curveId        : str,
                      plotTitle      : str,
                      windowTitle    : str,
                      plotRef        : str,
                      databaseAbsPath: str,
                      progressBar    : QtWidgets.QProgressBar,
                      data           : List[np.ndarray],
                      xLabelText     : str,
                      xLabelUnits    : str,
                      yLabelText     : str,
                      yLabelUnits    : str,
                      zLabelText     : str,
                      zLabelUnits    : str) -> None:
        """
        Call from loaddata thread.
        Just past the argument to the addPlot method.
        Usefull because progressBar is an optional parameter
        """

        self.signalRemoveProgressBar.emit(progressBar)

        self.addPlot(plotRef        = plotRef,
                     databaseAbsPath= databaseAbsPath,
                     data           = data,
                     xLabelText     = xLabelText,
                     xLabelUnits    = xLabelUnits,
                     yLabelText     = yLabelText,
                     yLabelUnits    = yLabelUnits,
                     zLabelText     = zLabelText,
                     zLabelUnits    = zLabelUnits,
                     runId          = runId,
                     curveId        = curveId,
                     plotTitle      = plotTitle,
                     windowTitle    = windowTitle)




    def addPlot(self, plotRef            : str,
                      databaseAbsPath    : str,
                      data               : List[np.ndarray],
                      xLabelText         : str,
                      xLabelUnits        : str,
                      yLabelText         : str,
                      yLabelUnits        : str,
                      runId              : int,
                      curveId            : str,
                      plotTitle          : str,
                      windowTitle        : str,
                      linkedTo2dPlot     : bool=False,
                      curveLegend        : Optional[str]=None,
                      hidden             : bool=False,
                      curveLabel         : Optional[str]=None,
                      curveUnits         : Optional[str]=None,
                      timestampXAxis     : Optional[bool]=None,
                      livePlot           : bool=False,
                      zLabelText         : Optional[str]=None,
                      zLabelUnits        : Optional[str]=None,
                      histogram          : Optional[bool]=False) -> None:
        """
        Methods called once the data are downloaded to add a plot of the data.
        Discriminate between 1d and 2d plot through the length of data list.
        For 1d plot, data having the sample plotRef do not launch a new plot
        window but instead are plotted in the window sharing the same plotRef.
        Once the data are plotted, run updateList1dCurvesLabels.

        Parameters
        ----------
        plotRef : str
            Reference of the plot.
        progressBar : str
            Key to the progress bar in the dict progressBars.
        data : list
            For 1d plot: [xData, yData]
            For 2d plot: [xData, yData, zData]
        xLabelText : str
            Label text for the xAxix.
        xLabelUnits : str
            Label units for the xAxix.
        yLabelText : str
            Label text for the yAxix.
        yLabelUnits : str
            Label units for the yAxix.
        runId : int
            Data run id in the current database
        curveId : str
            Id of the curve, see getCurveId.
        plotTitle : str
            Plot title, see getPlotTitle.
        windowTitle : str
            Window title, see getWindowTitle.
        zLabelText : str, default None
            Only for 2d data.
            Label text for the zAxis.
        zLabelUnits : str, default None
            Only for 2d data.
            Label units for the zAxis.
        """

        # If the method is called from a thread with a progress bar, we remove
        # it

        # If data is None it means the data download encounter an error.
        # We do not add plot
        if data is None:
            return

        self.signalSendStatusBarMessage.emit('Launching '+str(len(data)-1)+'d plot', 'orange')


        # If some parameters are not given, we find then from the GUI
        # if cleanCheckBox is None:
        #     cleanCheckBox = self.cleanCheckBox


        # 1D plot
        if len(data)==2:

            # Specific 1d optional parameter
            # print(timestampXAxis)
            # if timestampXAxis is None:
            #     timestampXAxis = self.LoadBlueFors.isBlueForsFolder(self._currentDatabase)
            # print(self.LoadBlueFors.isBlueForsFolder(self._currentDatabase))
            # print(timestampXAxis)
            # If the plotRef is not stored we launched a new window
            # Otherwise we add a new PlotDataItem on an existing plot1dApp
            if plotRef not in self._plotRefs:


                p = Plot1dApp(x                  = data[0],
                              y                  = data[1],
                              title              = plotTitle,
                              xLabelText         = xLabelText,
                              xLabelUnits        = xLabelUnits,
                              yLabelText         = yLabelText,
                              yLabelUnits        = yLabelUnits,
                              windowTitle        = windowTitle,
                              runId              = runId,
                              plotRef            = plotRef,
                              databaseAbsPath    = databaseAbsPath,
                              curveId            = curveId,
                              curveLegend        = curveLegend,
                              linkedTo2dPlot     = linkedTo2dPlot,
                              livePlot           = livePlot,
                              timestampXAxis     = timestampXAxis,
                              histogram          = histogram)

                self._plotRefs[plotRef] = p
                self._plotRefs[plotRef].show()
            else:

                self._plotRefs[plotRef].addPlotDataItem(x                  = data[0],
                                                        y                  = data[1],
                                                        curveId            = curveId,
                                                        curveXLabel        = xLabelText,
                                                        curveXUnits        = xLabelUnits,
                                                        curveYLabel        = yLabelText,
                                                        curveYUnits        = yLabelUnits,
                                                        curveLegend        = yLabelText,
                                                        hidden             = hidden)


        # 2D plot
        elif len(data)==3:

            # Determine if we should open a new Plot2dApp
            if plotRef not in self._plotRefs:
                p = Plot2dApp(x               = data[0],
                              y               = data[1],
                              z               = data[2],
                              title           = plotTitle,
                              xLabelText      = xLabelText,
                              xLabelUnits     = xLabelUnits,
                              yLabelText      = yLabelText,
                              yLabelUnits     = yLabelUnits,
                              zLabelText      = zLabelText,
                              zLabelUnits     = zLabelUnits,
                              windowTitle     = windowTitle,
                              runId           = runId,
                              plotRef         = plotRef,
                              databaseAbsPath = databaseAbsPath,
                              livePlot        = livePlot)

                self._plotRefs[plotRef] = p
                self._plotRefs[plotRef].show()

        self.signalSendStatusBarMessage.emit('Ready', 'green')

        p.signalClosePlot.connect(self.closePlot)
        # self.signalAddCurveToRefs.emit(plotRef, self._plotRefs[plotRef].curves[curveId])
        # self.updateList1dCurvesLabels()

        # Flag
        self._dataDowloadingFlag = False




    # @QtCore.pyqtSlot(str, pg.PlotDataItem)
    # def addCurveToRefs(self, plotRef: str,
    #                          curve: pg.PlotDataItem) -> None:
    #     # print(curve)
    #     # self._curveRefs[plotRef] = curve
    #     print(self._plotRefs[plotRef].curves)

    def lol(self, plotRef: str):

        if plotRef not in self._plotRefs:
            self.signalAddPlot.emit()
        else:
            self.signalAddCurveToPlot.emit()





    @QtCore.pyqtSlot(str, Plot1dApp)
    def addPlotToRefs(self, plotRef: str,
                            plot: Plot1dApp) -> None:

        self._plotRefs[plotRef] = plot





    @QtCore.pyqtSlot(str)
    def closePlot(self, plotRef: str) -> None:


        # When the plot is closed, we need to uncheck the visible checkbox
        # in the tableWidgetParameter.
        windowTitle = self._plotRefs[plotRef].windowTitle
        for curveId, curve in self._plotRefs[plotRef].curves.items():


        if self.getWindowTitle(runId=runId, runName=self.getRunName())==windowTitle and self.getRunId()==runId:

            # If 1d plot
            if self._plotRefs[plotRef].plotType=='1d':

                # If the current displayed parameters correspond to the one which has
                # been closed, we uncheck all the checkbox listed in the table
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 2)
                    widget.setChecked(False)
            # If 2d plot
            else:
                # We uncheck only the plotted parameter
                for row in range(self.tableWidgetParameters.rowCount()):
                    if label==self.tableWidgetParameters.item(row, 3).text():
                        widget = self.tableWidgetParameters.cellWidget(row, 2)
                        widget.setChecked(False)

        # if self.fitWindow is not None:
        #     self.fitWindow.close()

        # if self.filteringWindow is not None:
        #     self.filteringWindow.close()

        # for curveType in ['fft',
        #                   'derivative',
        #                   'primitive',
        #                   'unwrap',
        #                   'unslop',
        #                   'histogram']:
        #     plot = self.getPlotFromRef(self.plotRef, curveType)
        # for curveId in self._plotRefs[plotRef].curves.keys():
        #     self.removeCurvefromPlotRefs(plotRef, curveId)
        # # for ref in self._plotRefs.items()
        #     # if plot is not None:
        #     #     [self.signalremoveCurvefromPlotRefs.emit(self.plotRef+curveType, curveId) for curveId in plot.curves.keys()]

        # self.cleanCheckBox(plotRef     = self.plotRef,
        #                    windowTitle = self.windowTitle,
        #                    runId       = self.runId,
        #                    label       = '')



    @QtCore.pyqtSlot(str, str)
    def removeCurvefromPlotRefs(self, plotRef: str,
                                 curveId: str) -> None:

        if self._plotRefs[plotRef].plotType=='1d':
            # If there is more than one curve, we remove one curve
            if self._plotRefs[plotRef].nbPlotDataItemFromData()>1:
                self._plotRefs[plotRef].removePlotDataItem(curveId=curveId)
            # If there is one curve we close the plot window
            else:
                self._plotRefs[plotRef].o()
                del(self._plotRefs[plotRef])

            # Update the list of currently plotted dependent parametered on all
            # the plotted window
            self.updateList1dCurvesLabels()
        elif self._plotRefs[plotRef].plotType=='2d':
            self._plotRefs[plotRef].o()
            del(self._plotRefs[plotRef])



    @QtCore.pyqtSlot(str, str)
    def removeCurvefromPlotRefs(self, plotRef: str,
                                 curveId: str) -> None:

        if self._plotRefs[plotRef].plotType=='1d':
            # If there is more than one curve, we remove one curve
            if self._plotRefs[plotRef].nbPlotDataItemFromData()>1:
                self._plotRefs[plotRef].removePlotDataItem(curveId=curveId)
            # If there is one curve we close the plot window
            else:
                self._plotRefs[plotRef].o()
                del(self._plotRefs[plotRef])

            # Update the list of currently plotted dependent parametered on all
            # the plotted window
            self.updateList1dCurvesLabels()
        elif self._plotRefs[plotRef].plotType=='2d':
            self._plotRefs[plotRef].o()
            del(self._plotRefs[plotRef])



    def updateList1dCurvesLabels(self) -> None:
        """
        Is called when the user add or delete a plot.
        See addPlot and removePlot
        The method creates a list of all displayed 1d plot window object and
        send it to all displayed 1d plot windows via the updatePlottedCurvesList
        method.
        """

        if len(self._plotRefs) > 0:

            # Build the list of 1d plot windows
            plots = [plot for plot in self._plotRefs.values() if plot.plotType=='1d']

            # Send the list to every 1d plot windows
            [plot.updatePlottedCurvesList(plots) for plot in plots]



    # def addPlotFromThread(self, runId          : int,
    #                             curveId        : str,
    #                             plotTitle      : str,
    #                             windowTitle    : str,
    #                             plotRef        : str,
    #                             databaseAbsPath: str,
    #                             progressBarKey : str,
    #                             data           : List[np.ndarray],
    #                             xLabelText     : str,
    #                             xLabelUnits    : str,
    #                             yLabelText     : str,
    #                             yLabelUnits    : str,
    #                             zLabelText     : str,
    #                             zLabelUnits    : str) -> None:
    #     """
    #     Call from loaddata thread.
    #     Just past the argument to the addPlot method.
    #     Usefull because progressBarKey is an optional parameter
    #     """

    #     self.addPlot(plotRef        = plotRef,
    #                  databaseAbsPath= databaseAbsPath,
    #                  data           = data,
    #                  xLabelText     = xLabelText,
    #                  xLabelUnits    = xLabelUnits,
    #                  yLabelText     = yLabelText,
    #                  yLabelUnits    = yLabelUnits,
    #                  zLabelText     = zLabelText,
    #                  zLabelUnits    = zLabelUnits,
    #                  runId          = runId,
    #                  curveId        = curveId,
    #                  plotTitle      = plotTitle,
    #                  windowTitle    = windowTitle,
    #                  progressBarKey = progressBarKey)



    # def addPlot(self, plotRef            : str,
    #                   databaseAbsPath    : str,
    #                   data               : List[np.ndarray],
    #                   xLabelText         : str,
    #                   xLabelUnits        : str,
    #                   yLabelText         : str,
    #                   yLabelUnits        : str,
    #                   runId              : int,
    #                   curveId            : str,
    #                   plotTitle          : str,
    #                   windowTitle        : str,
    #                   cleanCheckBox      : Callable[[str, str, int, Union[str, list]], None]=None,
    #                   linkedTo2dPlot     : bool=False,
    #                   curveLegend        : Optional[str]=None,
    #                   hidden             : bool=False,
    #                   curveLabel         : Optional[str]=None,
    #                   curveUnits         : Optional[str]=None,
    #                   timestampXAxis     : Optional[bool]=None,
    #                   livePlot           : bool=False,
    #                   progressBarKey     : Optional[str]=None,
    #                   zLabelText         : Optional[str]=None,
    #                   zLabelUnits        : Optional[str]=None,
    #                   histogram          : Optional[bool]=False) -> None:
    #     """
    #     Methods called once the data are downloaded to add a plot of the data.
    #     Discriminate between 1d and 2d plot through the length of data list.
    #     For 1d plot, data having the sample plotRef do not launch a new plot
    #     window but instead are plotted in the window sharing the same plotRef.
    #     Once the data are plotted, run updateList1dCurvesLabels.

    #     Parameters
    #     ----------
    #     plotRef : str
    #         Reference of the plot.
    #     progressBarKey : str
    #         Key to the progress bar in the dict progressBars.
    #     data : list
    #         For 1d plot: [xData, yData]
    #         For 2d plot: [xData, yData, zData]
    #     xLabelText : str
    #         Label text for the xAxix.
    #     xLabelUnits : str
    #         Label units for the xAxix.
    #     yLabelText : str
    #         Label text for the yAxix.
    #     yLabelUnits : str
    #         Label units for the yAxix.
    #     runId : int
    #         Data run id in the current database
    #     curveId : str
    #         Id of the curve, see getCurveId.
    #     plotTitle : str
    #         Plot title, see getPlotTitle.
    #     windowTitle : str
    #         Window title, see getWindowTitle.
    #     zLabelText : str, default None
    #         Only for 2d data.
    #         Label text for the zAxis.
    #     zLabelUnits : str, default None
    #         Only for 2d data.
    #         Label units for the zAxis.
    #     """

    #     # If the method is called from a thread with a progress bar, we remove
    #     # it
    #     if progressBarKey is not None:
    #         if progressBarKey in self._progressBars:
    #             self.removeProgressBar(progressBarKey)

    #     # If data is None it means the data download encounter an error.
    #     # We do not add plot
    #     if data is None:
    #         return

    #     self.setStatusBarMessage('Launching '+str(len(data)-1)+'d plot')


    #     # If some parameters are not given, we find then from the GUI
    #     if cleanCheckBox is None:
    #         cleanCheckBox = self.cleanCheckBox


    #     # 1D plot
    #     if len(data)==2:

    #         # Specific 1d optional parameter
    #         # print(timestampXAxis)
    #         # if timestampXAxis is None:
    #         #     timestampXAxis = self.LoadBlueFors.isBlueForsFolder(self._currentDatabase)
    #         # print(self.LoadBlueFors.isBlueForsFolder(self._currentDatabase))
    #         # print(timestampXAxis)
    #         # If the plotRef is not stored we launched a new window
    #         # Otherwise we add a new PlotDataItem on an existing plot1dApp
    #         if plotRef not in self._plotRefs:


    #             p = Plot1dApp(x                  = data[0],
    #                           y                  = data[1],
    #                           title              = plotTitle,
    #                           xLabelText         = xLabelText,
    #                           xLabelUnits        = xLabelUnits,
    #                           yLabelText         = yLabelText,
    #                           yLabelUnits        = yLabelUnits,
    #                           windowTitle        = windowTitle,
    #                           runId              = runId,
    #                           cleanCheckBox      = cleanCheckBox,
    #                           plotRef            = plotRef,
    #                           databaseAbsPath    = databaseAbsPath,
    #                           addPlot            = self.addPlot,
    #                           removePlot         = self.removePlot,
    #                           getPlotFromRef     = self.getPlotFromRef,
    #                           curveId            = curveId,
    #                           curveLegend        = curveLegend,
    #                           linkedTo2dPlot     = linkedTo2dPlot,
    #                           livePlot           = livePlot,
    #                           timestampXAxis     = timestampXAxis,
    #                           histogram          = histogram)

    #             self._plotRefs[plotRef] = p
    #             self._plotRefs[plotRef].show()
    #         else:

    #             self._plotRefs[plotRef].addPlotDataItem(x                  = data[0],
    #                                                     y                  = data[1],
    #                                                     curveId            = curveId,
    #                                                     curveXLabel        = xLabelText,
    #                                                     curveXUnits        = xLabelUnits,
    #                                                     curveYLabel        = yLabelText,
    #                                                     curveYUnits        = yLabelUnits,
    #                                                     curveLegend        = yLabelText,
    #                                                     hidden             = hidden)


    #     # 2D plot
    #     elif len(data)==3:

    #         # Determine if we should open a new Plot2dApp
    #         if plotRef not in self._plotRefs:
    #             p = Plot2dApp(x               = data[0],
    #                           y               = data[1],
    #                           z               = data[2],
    #                           title           = plotTitle,
    #                           xLabelText      = xLabelText,
    #                           xLabelUnits     = xLabelUnits,
    #                           yLabelText      = yLabelText,
    #                           yLabelUnits     = yLabelUnits,
    #                           zLabelText      = zLabelText,
    #                           zLabelUnits     = zLabelUnits,
    #                           windowTitle     = windowTitle,
    #                           runId           = runId,
    #                           cleanCheckBox   = cleanCheckBox,
    #                           plotRef         = plotRef,
    #                           databaseAbsPath = databaseAbsPath,
    #                           addPlot         = self.addPlot,
    #                           removePlot      = self.removePlot,
    #                           getPlotFromRef  = self.getPlotFromRef,
    #                           livePlot        = livePlot)

    #             self._plotRefs[plotRef] = p
    #             self._plotRefs[plotRef].show()

    #     self.setStatusBarMessage('Ready')
    #     self.updateList1dCurvesLabels()

    #     # Flag
    #     self._dataDowloadingFlag = False



    # def removePlot(self, plotRef: str,
    #                      curveId: str) -> None:
    #     """
    #     Method call when data are remove from the GUI.
    #     If the data plot window is open, close it.
    #     Then remove the reference of the plot window from self._plotRefs.

    #     Once the data are closed, run updateList1dCurvesLabels.

    #     Parameters
    #     ----------
    #     plotRef : str
    #         Reference of the plot, see getPlotRef.
    #     curveId : str
    #         reference of the curve, see getCurveId
    #     """

    #     if self._plotRefs[plotRef].plotType=='1d':
    #         # If there is more than one curve, we remove one curve
    #         if self._plotRefs[plotRef].nbPlotDataItemFromData()>1:
    #             self._plotRefs[plotRef].removePlotDataItem(curveId=curveId)
    #         # If there is one curve we close the plot window
    #         else:
    #             self._plotRefs[plotRef].o()
    #             del(self._plotRefs[plotRef])

    #         # Update the list of currently plotted dependent parametered on all
    #         # the plotted window
    #         self.updateList1dCurvesLabels()
    #     elif self._plotRefs[plotRef].plotType=='2d':
    #         self._plotRefs[plotRef].o()
    #         del(self._plotRefs[plotRef])



    # def getPlotSliceFromRef(self, plotRef          : str,
    #                               sliceOrientation : str) -> Union[Plot1dApp, None]:
    #     """
    #     Return the 1d plot containing the slice data of a 2d plot.

    #     Parameters
    #     ----------
    #     plotRef : str
    #         Reference of the 2d plot from which the data comes from.
    #     sliceOrientation : str
    #         Orientation of the slice we are interested in.
    #     """

    #     ref = plotRef+sliceOrientation

    #     if ref in self._plotRefs.keys():
    #         return self._plotRefs[ref]
    #     else:
    #         return None



    # def getPlotFromRef(self, plotRef   : str,
    #                          curveType : str) -> Union[Plot1dApp, None]:
    #     """
    #     Return the 1d plot containing the FFT of a 1d plot.

    #     Parameters
    #     ----------
    #     plotRef : str
    #         Reference of the 1d plot from which the data comes from.
    #     curveType : str ['fft', 'derivative']
    #         curveType of the data looked for
    #     """

    #     ref = plotRef+curveType

    #     if ref in self._plotRefs.keys():
    #         return self._plotRefs[ref]
    #     else:
    #         return None



    ###########################################################################
    #
    #
    #                           Data
    #
    #
    ###########################################################################



    # def getData(self, runId              : int,
    #                   curveId            : str,
    #                   plotTitle          : str,
    #                   windowTitle        : str,
    #                   plotRef            : str,
    #                   databaseAbsPath    : str,
    #                   dependentParamName : str) -> None:
    #     """
    #     Called when user wants to plot qcodes data.
    #     Create a progress bar in the status bar.
    #     Launched a thread which will download the data, display the progress in
    #     the progress bar and call addPlot when the data are downloaded.

    #     Parameters
    #     ----------
    #     runId : int
    #         Data run id in the current database
    #     curveId : str
    #         Id of the curve, see getCurveId.
    #     plotTitle : str
    #         Plot title, see getPlotTitle.
    #     windowTitle : str
    #         Window title, see getWindowTitle.
    #     plotRef : str
    #         Reference of the plot window.
    #     dependentParamName : str
    #         Name of the dependent parameter from which data will be downloaded.
    #     """

    #     # Flag
    #     self._dataDowloadingFlag = True

    #     progressBarKey = self.addProgressBarInStatusBar()

    #     worker = LoadDataFromRunThread(runId,
    #                                    curveId,
    #                                    plotTitle,
    #                                    windowTitle,
    #                                    dependentParamName,
    #                                    plotRef,
    #                                    databaseAbsPath,
    #                                    progressBarKey)
    #     # Connect signals
    #     # To update the status bar
    #     worker.signals.setStatusBarMessage.connect(self.setStatusBarMessage)
    #     # To update the progress bar
    #     worker.signals.updateProgressBar.connect(self.updateProgressBar)
    #     # If data download failed
    #     worker.signals.updateDataEmpty.connect(self.updateDataEmpty)
    #     # When data download is done
    #     worker.signals.updateDataFull.connect(self.addPlotFromThread)

    #     # Execute the thread
    #     self.threadpool.start(worker)



    # def updateDataEmpty(self) -> None:
    #     """
    #     Method called by LoadDataFromRunThread when the data download is done but the
    #     database is empty.
    #     We signal the data downloading being done by setting the flag False.
    #     This will allow the next live plot iteration to try downloading the data
    #     again.
    #     """

    #     self._dataDowloadingFlag = False
