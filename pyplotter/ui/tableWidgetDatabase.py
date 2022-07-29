# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import List
import os

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..sources.runpropertiesextra import RunPropertiesExtra
from .tableWidgetItemNumOrdered import TableWidgetItemNumOrdered
from ..sources.workers.loadDataBase import LoadDataBaseThread
from ..sources.workers.loadRunInfo import LoadRunInfoThread
from ..sources.functions import clearTableWidget

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')

class TableWidgetDatabase(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    signalSendStatusBarMessage     = QtCore.pyqtSignal(str, str)
    signalUpdateProgressBar        = QtCore.pyqtSignal(QtWidgets.QProgressBar, int, str)
    signalRemoveProgressBar        = QtCore.pyqtSignal(QtWidgets.QProgressBar)
    signalDatabaseClickDone        = QtCore.pyqtSignal()
    keyPressed                     = QtCore.pyqtSignal(str, int)
    signalRunClick                 = QtCore.pyqtSignal(int, list, dict, str, str, str, bool)
    signalDatabaseStars            = QtCore.pyqtSignal()
    signalDatabaseUnstars          = QtCore.pyqtSignal()
    signalCheckBoxHiddenHideRow    = QtCore.pyqtSignal(int)



    def __init__(self, parent=None) -> None:
        super(TableWidgetDatabase, self).__init__(parent)


        # When user wants to look at a run
        self.cellClicked.connect(self.runClick)
        self.doubleClicked.connect(self.runDoubleClick)

        # When user wants to hide or stars a run
        self.keyPressed.connect(self.tableWidgetDataBasekeyPress)

        # Flag
        self._dataDowloadingFlag = False

        # To avoid the opening of two databases as once
        self._databaseClicking = False

        self.properties = RunPropertiesExtra()
        self.threadpool = QtCore.QThreadPool()


    def first_call(self):
        # Only used to propagate information
        self.setColumnHidden(8, True)


    def keyPressEvent(self, event):
        super(TableWidgetDatabase, self).keyPressEvent(event)

        # Emit the pressed key in hum readable format in lower case
        self.keyPressed.emit(QtGui.QKeySequence(event.key()).toString().lower(), self.currentRow())



    @QtCore.pyqtSlot(str, QtWidgets.QProgressBar)
    def databaseClick(self, databaseAbsPath: str,
                              progressBar: QtWidgets.QProgressBar) -> None:

        self.currentPath  = os.path.dirname(databaseAbsPath)
        self.databaseName = os.path.basename(databaseAbsPath)

        # Load runs extra properties
        self.properties.jsonLoad(self.currentPath,
                                 self.databaseName)

        # Remove all previous row in the table
        clearTableWidget(self)

        # Modify the resize mode so that the initial view has an optimized
        # column width
        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)

        # self.qcodesDatabase.databasePath = os.path.join(self.currentPath, self._currentDatabase)

        # Create a thread which will read the database
        worker = LoadDataBaseThread(databaseAbsPath,
                                    progressBar)

        # Connect signals
        worker.signal.sendStatusBarMessage.connect(self.signalSendStatusBarMessage)
        worker.signal.addRows.connect(self.databaseClickAddRows)
        worker.signal.updateProgressBar.connect(self.signalUpdateProgressBar)
        worker.signal.databaseClickDone.connect(self.databaseClickDone)

        # Execute the thread
        self.threadpool.start(worker)



    def databaseClickAddRows(self, lrunId          : List[int],
                                     ldim            : List[str],
                                     lexperimentName : List[str],
                                     lsampleName     : List[str],
                                     lrunName        : List[str],
                                     lstarted        : List[str],
                                     lcompleted      : List[str],
                                     lrunRecords     : List[str],
                                     nbTotalRun      : int,
                                     databaseAbsPath : str) -> None:
        """
        Called by another thread to fill the database table.
        Each call add n rows into the table.
        """


        if lrunId[0]==1:
            # self.statusBarMain.clearMessage()
            self.setRowCount(nbTotalRun)

        # We go through all lists of parameters and for each list element, we add
        # a row in the table
        for (runId, dim, experimentName, sampleName, runName, started, completed,
             runRecords) in zip(lrunId,
             ldim, lexperimentName, lsampleName, lrunName, lstarted, lcompleted,
             lrunRecords):

            itemRunId = TableWidgetItemNumOrdered(str(runId))

            # If the run has been stared by an user
            if runId in self.properties.getRunStared():
                itemRunId.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'star.png')))
                itemRunId.setForeground(QtGui.QBrush(QtGui.QColor(*config['runStaredColor'])))
            # If the user has hidden a row
            elif runId in self.properties.getRunHidden():
                itemRunId.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'trash.png')))
                itemRunId.setForeground(QtGui.QBrush(QtGui.QColor(*config['runHiddenColor'])))
            else:
                itemRunId.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'empty.png')))

            self.setItem(runId-1, 0, itemRunId)
            self.setItem(runId-1, 1, QtWidgets.QTableWidgetItem(dim))
            self.setItem(runId-1, 2, QtWidgets.QTableWidgetItem(experimentName))
            self.setItem(runId-1, 3, QtWidgets.QTableWidgetItem(sampleName))
            self.setItem(runId-1, 4, QtWidgets.QTableWidgetItem(runName))
            self.setItem(runId-1, 5, QtWidgets.QTableWidgetItem(started))
            self.setItem(runId-1, 6, QtWidgets.QTableWidgetItem(completed))
            self.setItem(runId-1, 7, TableWidgetItemNumOrdered(runRecords))
            self.setItem(runId-1, 8, QtWidgets.QTableWidgetItem(databaseAbsPath))

            if runId in self.properties.getRunHidden():
                self.setRowHidden(runId-1, True)



    def databaseClickDone(self,progressBar    : QtWidgets.QProgressBar,
                               error          : bool,
                               nbTotalRun     : int) -> None:
        """
        Called when the database table has been filled

        Parameters
        ----------
        progressBar : str
            Key to the progress bar in the dict progressBars.
        error : bool

        nbTotalRun : int
            Total number of run in the current database.
            Simply stored for other purposes and to avoid other sql queries.
        """

        self.signalRemoveProgressBar.emit(progressBar)

        if not error:
            self.setSortingEnabled(True)
            self.sortItems(0, QtCore.Qt.DescendingOrder)
            self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)


            self.signalSendStatusBarMessage.emit('Ready', 'green')


        # We store the total number of run
        self.nbTotalRun = nbTotalRun

        # Done
        self._databaseClicking = False

        self.signalDatabaseClickDone.emit()

        # self.dataBaseCheckNbRun()



    def dataBaseCheckNbRun(self):
        """
        Method called by databaseClickDone.
        Launch a thread every config['delayBetweendataBaseNbRunCheck'] ms
        which will launch a process to get the nb of run in the database.
        If that number is the same as the database currently displayed, nothing
        happen, otherwise, the method databaseClick is called which will
        refresh the diaplayed database.
        """

        # From launch a thread which will periodically check if the database has
        # more run that what is currently displayed
        worker = dataBaseCheckNbRunThread(self.databaseAbsPath,
                                          self.nbTotalRun)

        # Connect signals
        worker.signals.dataBaseUpdate.connect(self.dataBaseUpdate)
        worker.signals.dataBaseCheckNbRun.connect(self.dataBaseCheckNbRun)

        # Execute the thread
        self.threadpool.start(worker)



    def dataBaseUpdate(self, databasePathToUpdate: str) -> None:
        """Method called by dataBaseCheckNbRunThread when the displayed database
        has not the same number of total run.
        Call databaseClick if the displayed database shares the same path
        as the database check by the thread.

        Args:
            databasePathToUpdate : path of the checked database
        """

        if databasePathToUpdate==self.databaseAbsPath:
            self.databaseClick()



    def runDoubleClick(self) -> None:
        """
        Called when user double click on the database table.
        Display the measured dependent parameters in the table Parameters.
        Simulate the user clicking on the first dependent parameter, effectively
        launching its plot.
        """

        # We simulate a single click while propagating the double-click info
        self.runClick(doubleClicked=True)



    def runClick(self, currentRow: int=0,
                       currentColumn: int=0,
                       previousRow: int=0,
                       previousColumn: int=0,
                       doubleClicked: bool=False) -> None:
        """
        When clicked display the measured dependent parameters in the
        tableWidgetPtableWidgetParameters.
        Database is accessed through a thread, see runClickFromThread.
        """

        # When the user click on another database while having already clicked
        # on a run, the runClick event is happenning even if no run have been clicked
        # This is due to the "currentCellChanged" event handler.
        # We catch that false event and return nothing
        if self._databaseClicking:
            return


        runId           = int(self.item(currentRow, 0).text())
        experimentName  = self.item(currentRow, 2).text()
        runName         = self.item(currentRow, 4).text()
        databaseAbsPath = self.item(currentRow, 8).text()

        self.signalSendStatusBarMessage.emit('Loading run parameters', 'orange')

        worker = LoadRunInfoThread(databaseAbsPath,
                                   runId,
                                   experimentName,
                                   runName,
                                   doubleClicked)
        worker.signal.updateRunInfo.connect(self.signalRunClick)

        # Execute the thread
        self.threadpool.start(worker)



    def tableWidgetDataBasekeyPress(self, key: str,
                                          row : int) -> None:
        """
        Call when user presses a key while having the focus on the database table.
        Towo keys are handle:
            "h" to hide/unhide a run
            "s" to star/unstar a run

        Parameters
        ----------
        key : str
            Pressed key in human readable format.
        row : int
            Row of the database table in which the key happened.
        """

        runId = int(self.item(row, 0).text())

        # If user wants to star a run
        if key==config['keyPressedStared'].lower():

            # If the run was already stared
            # We remove the star of the table
            # We remove the runId from the json
            if runId in self.properties.getRunStared():

                # We remove the star from the row
                item = TableWidgetItemNumOrdered(str(runId))
                item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'empty.png')))
                self.setItem(row, 0, item)

                # We update the json
                self.properties.jsonRemoveStaredRun(runId)

                # If the database does not contain stared run anymore, we modify
                # its icon
                if len(self.properties.getRunStared())==0:
                    self.signalDatabaseUnstars.emit()

            # If the user wants to stared the run
            else:

                # We put a star in the row
                item = TableWidgetItemNumOrdered(str(runId))
                item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'star.png')))
                item.setForeground(QtGui.QBrush(QtGui.QColor(*config['runStaredColor'])))
                self.setItem(row, 0, item)

                # We update the json
                self.properties.jsonAddStaredRun(runId)

                # If the database containing the stared run is displayed, we star it
                self.signalDatabaseStars.emit()


        # If user wants to hide a run
        elif key==config['keyPressedHide'].lower():

            # If the run was already hidden
            # We unhide the row
            # We remove the runId from the json
            if runId in self.properties.getRunHidden():

                item = TableWidgetItemNumOrdered(str(runId))
                item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'empty.png')))
                item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                self.setItem(row, 0, item)

                # We update the json
                self.properties.jsonRemoveHiddenRun(runId)
            else:

                # We modify the item and hide the row
                item = TableWidgetItemNumOrdered(str(runId))
                item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'trash.png')))
                item.setForeground(QtGui.QBrush(QtGui.QColor(*config['runHiddenColor'])))
                self.setItem(row, 0, item)

                # We hide the row only if the user didn't check the checkboxhidden
                self.signalCheckBoxHiddenHideRow.emit(row)

                # We update the json
                self.properties.jsonAddHiddenRun(runId)



    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################


    @QtCore.pyqtSlot(int)
    def checkBoxHiddenClick(self, state: int) -> None:
        """
        Call when user clicks on the "Show hidden checkbox.
        When check, show all databse run.
        When unchecked, hide again the hidden run.
        """

        runHidden   = self.properties.getRunHidden()
        nbTotalRow  = self.rowCount()

        # If user wants to see hidden run
        if state==2:

            for row in range(nbTotalRow):

                if int(self.item(row, 0).text()) in runHidden:
                    self.setRowHidden(row, False)

        # Hide hidden run again
        elif state==0:

            for row in range(nbTotalRow):

                if int(self.item(row, 0).text()) in runHidden:
                    self.setRowHidden(row, True)
                else:
                    self.setRowHidden(row, False)



    @QtCore.pyqtSlot(int, bool)
    def hideRow(self, row: int,
                      hide: bool) -> None:

        self.setRowHidden(row, hide)