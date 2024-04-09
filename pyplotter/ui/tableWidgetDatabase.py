from PyQt5 import QtCore, QtWidgets, QtGui
from typing import List
import os
from time import time
from typing import Optional

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..sources.runPropertiesExtra import RunPropertiesExtra
from .tableWidgetItemNumOrdered import TableWidgetItemNumOrdered
# from ..sources.workers.loadDataBase import LoadDataBaseThread
# from ..sources.workers.loadRunInfo import LoadRunInfoThread
# from ..sources.workers.checkNbRunDatabase import dataBaseCheckNbRunThread
from ..sources.workers import loadDataBase, loadRunInfo, checkNbRunDatabase
from ..sources.workers import loadLabradDataBase, loadLabradRunInfo, checkNbRunLabrad
from ..sources.workers.exportRun import ExportRunThread
from ..sources.functions import clearTableWidget, getDatabaseNameFromAbsPath, isLabradFolder, isQcodesData
from ..ui.dialogs.dialogComment import DialogComment
from ..ui.menuExportRun import MenuExportRun

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')


def LoadDataBaseThread(databaseAbsPath, progressBar):
    if isLabradFolder(databaseAbsPath):
        workerLoadDatabase = loadLabradDataBase.LoadDataBaseThread(
            databaseAbsPath, progressBar
        )
    elif isQcodesData(os.path.split(databaseAbsPath)[-1]):
        workerLoadDatabase = loadDataBase.LoadDataBaseThread(databaseAbsPath, progressBar)
    return workerLoadDatabase


def LoadRunInfoThread(
    databaseAbsPath,  # databaseAbsPath
    runId,  # runId
    experimentName,  # experimentName
    runName,  # runName
    doubleClicked,
):
    if isLabradFolder(databaseAbsPath):
        worker = loadLabradRunInfo.LoadRunInfoThread(
            databaseAbsPath, runId, experimentName, runName, doubleClicked
        )
    elif isQcodesData(os.path.split(databaseAbsPath)[-1]):
        worker = loadRunInfo.LoadRunInfoThread(
            databaseAbsPath, runId, experimentName, runName, doubleClicked
        )
    return worker


def dataBaseCheckNbRunThread(databaseAbsPath, nbTotalRun):
    if isLabradFolder(databaseAbsPath):
        workerCheck = checkNbRunLabrad.dataBaseCheckNbRunThread(databaseAbsPath, nbTotalRun)
    elif isQcodesData(os.path.split(databaseAbsPath)[-1]):
        workerCheck = checkNbRunDatabase.dataBaseCheckNbRunThread(databaseAbsPath, nbTotalRun)
    return workerCheck


class TableWidgetDatabase(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    # Propagated to statusBarMain
    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)
    signalAddStatusBarMessage  = QtCore.pyqtSignal(str, str)
    signalUpdateProgressBar    = QtCore.pyqtSignal(int, float, str)
    signalRemoveProgressBar    = QtCore.pyqtSignal(int)
    # Propagated to tableWidgetFolder, checkBoxHidden, checkBoxStared
    signalDatabaseClickDone = QtCore.pyqtSignal(str)
    # Propagated to tableWidgetFolder
    signalDatabaseLoadingStop = QtCore.pyqtSignal(str)
    # Propagated to labelCurrentDataBase
    signalUpdateCurrentDatabase = QtCore.pyqtSignal(str)
    # Propagated to tableWidgetParameter
    signalRunClick = QtCore.pyqtSignal(int, list, dict, dict, str, str, str, str, bool)
    # Propagated to tableWidgetFolder
    signalDatabaseStars   = QtCore.pyqtSignal()
    signalDatabaseUnstars = QtCore.pyqtSignal()
    # Propagated to checkBoxStared
    signalCheckBoxHiddenChecked = QtCore.pyqtSignal(bool)
    # Propagated to checkBoxHidden
    signalCheckBoxStaredChecked = QtCore.pyqtSignal(bool)
    signalCheckBoxHiddenHideRow = QtCore.pyqtSignal(int)

    # Propagated to statusBarMain which come back here to databaseClick
    signal2StatusBarDatabaseUpdate = QtCore.pyqtSignal(str)

    # Propagated to the statusBarMain which come back here to menuExportRun
    signalExportRunAddProgressBar = QtCore.pyqtSignal(str, str, int)


    # Internal event, see keyPressEvent
    keyPressed = QtCore.pyqtSignal(str, int)


    def __init__(self, parent=None) -> None:
        super(TableWidgetDatabase, self).__init__(parent)

        # Forbid editing of the cells
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # Use filter to detect right, left and double click
        self.viewport().installEventFilter(self)

        # When user wants to hide or stars a run
        self.keyPressed.connect(self.tableWidgetDataBasekeyPress)

        self.properties = RunPropertiesExtra()
        self.threadpool = QtCore.QThreadPool()



    def eventFilter(self, source,
                          event) -> Optional[bool]:
        """
        We use an event filter to detect
            right click -> display run parameter
            left click -> display menu to export run
            double click -> display run parameter and load plot of the 1st parameter
        """

        # Get the clicked row and column
        if event.type() == QtCore.QEvent.MouseButtonPress\
            or event.type() == QtCore.QEvent.MouseButtonDblClick:
            index = self.indexAt(event.pos())
            if index.isValid():
                currentRow = index.row()
                currentColumn = index.column()
            else:
                return

        if event.type() == QtCore.QEvent.MouseButtonPress:

            # right click -> display run parameter
            if event.button() == QtCore.Qt.LeftButton:
                self.runClick(currentRow)
            # left click -> display menu to export run
            elif event.button() == QtCore.Qt.RightButton:
                self.runClick(currentRow)
                self.exportRun(currentRow)
            # double click -> display run parameter and load plot of the 1st parameter
        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.runDoubleClick(currentRow,
                                currentColumn)

        return super().eventFilter(source, event)



    def first_call(self):
        """
        Call when the widget is initially display
        Build the columns foolowing the config file
        """
        self.setColumnCount(len(config['DatabaseDisplayColumn']))

        for val in config['DatabaseDisplayColumn'].values():

            # Add a column
            item = QtWidgets.QTableWidgetItem()

            # Set its header
            self.setHorizontalHeaderItem(val['index'], item)
            item.setText(val['name'])

            # Hide or display some column
            self.setColumnHidden(val['index'], False==val['visible'])



    def keyPressEvent(self, event):
        super(TableWidgetDatabase, self).keyPressEvent(event)

        # Emit the pressed key in human readable format in lower case
        self.keyPressed.emit(QtGui.QKeySequence(event.key()).toString().lower(), self.currentRow())



    @QtCore.pyqtSlot(str, int)
    def databaseClick(self, databaseAbsPath: str,
                            progressBar: int) -> None:
        """
        Called from the statusBarMain, when user clicks on a database.
        """

        # Load runs extra properties
        self.properties.jsonLoad(os.path.dirname(databaseAbsPath),
                                 os.path.basename(databaseAbsPath))

        # Remove all previous row in the table
        clearTableWidget(self)

        # Modify the resize mode so that the initial view has an optimized
        # column width
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Create a thread which will read the database
        self.workerLoadDatabase = LoadDataBaseThread(databaseAbsPath,
                                                     progressBar)

        # Connect signals
        self.workerLoadDatabase.signal.sendStatusBarMessage.connect(self.signalSendStatusBarMessage)
        self.workerLoadDatabase.signal.addRows.connect(self.databaseClickAddRows)
        self.workerLoadDatabase.signal.updateProgressBar.connect(self.signalUpdateProgressBar)
        self.workerLoadDatabase.signal.databaseClickDone.connect(self.databaseClickDone)

        # Execute the thread
        self.threadpool.start(self.workerLoadDatabase)



    QtCore.pyqtSlot(list, list, list, list, list, list, list, list, list, list, list, int, str)
    def databaseClickAddRows(self, lrunId           : List[int],
                                   ldim             : List[str],
                                   lexperimentName  : List[str],
                                   lsampleName      : List[str],
                                   lrunName         : List[str],
                                   lcaptured_run_id : List[str],
                                   lguid            : List[str],
                                   lstarted         : List[str],
                                   lcompleted       : List[str],
                                   lduration        : List[str],
                                   lrunRecords      : List[str],
                                   nbTotalRun       : int,
                                   databaseAbsPath  : str) -> None:
        """
        Called by another thread to fill the database table.
        Each call add n rows into the table.
        """


        if lrunId[0]==1:
            # self.statusBarMain.clearMessage()
            self.setRowCount(nbTotalRun)

        # We go through all lists of parameters and for each list element, we add
        # a row in the table
        for (runId, dim, experimentName, sampleName, runName, captured_run_id,
             guid, started, completed, duration, runRecords) in zip(lrunId,
             ldim, lexperimentName, lsampleName, lrunName, lcaptured_run_id,
             lguid, lstarted, lcompleted, lduration, lrunRecords):

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

            self.setItem(runId-1, config['DatabaseDisplayColumn']['databaseAbsPath']['index'], QtWidgets.QTableWidgetItem(databaseAbsPath))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['itemRunId']['index'],       itemRunId)
            self.setItem(runId-1, config['DatabaseDisplayColumn']['dimension']['index'],       QtWidgets.QTableWidgetItem(dim))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['experimentName']['index'],  QtWidgets.QTableWidgetItem(experimentName))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['sampleName']['index'],      QtWidgets.QTableWidgetItem(sampleName))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['runName']['index'],         QtWidgets.QTableWidgetItem(runName))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['captured_run_id']['index'], QtWidgets.QTableWidgetItem(captured_run_id))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['guid']['index'],            QtWidgets.QTableWidgetItem(guid))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['started']['index'],         QtWidgets.QTableWidgetItem(started))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['completed']['index'],       QtWidgets.QTableWidgetItem(completed))

            # All of that to get colored duration
            widgetText =  QtWidgets.QLabel()
            widgetText.setTextFormat(QtCore.Qt.RichText)
            widgetText.setText(duration)
            self.setCellWidget(runId-1, config['DatabaseDisplayColumn']['duration']['index'], widgetText)

            self.setItem(runId-1, config['DatabaseDisplayColumn']['runRecords']['index'],      TableWidgetItemNumOrdered(runRecords))
            self.setItem(runId-1, config['DatabaseDisplayColumn']['comment']['index'],         QtWidgets.QTableWidgetItem(self.properties.getRunComment(runId)))

            # Hide some run
            if runId in self.properties.getRunHidden():
                self.setRowHidden(runId-1, True)

            # Set vertical and horizontal alignment
            for i in range(config['DatabaseDisplayColumn']['comment']['index']):
                if i!=config['DatabaseDisplayColumn']['duration']['index']:
                    self.item(runId-1, i).setTextAlignment(QtCore.Qt.AlignVCenter)
                else:
                    self.cellWidget(runId-1, i).setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

            # Set some tooltip
            self.item(runId-1,    config['DatabaseDisplayColumn']['itemRunId']['index']).setToolTip('Type "s" to star a run and "h" to hide it.')
            self.item(runId-1, config['DatabaseDisplayColumn']['comment']['index']).setToolTip('Double-click on the "Comments" column to add or modify a comment attached to a run')


    @QtCore.pyqtSlot(int, bool, str, int)
    def databaseClickDone(self,progressBarId  : int,
                               error          : bool,
                               databaseAbsPath: str,
                               nbTotalRun     : int) -> None:
        """
        Called when the database table has been filled

        Parameters
        ----------
        progressBar : int
            Key to the progress bar in the dict progressBars.
        error : bool

        nbTotalRun : int
            Total number of run in the current database.
            Simply stored for other purposes and to avoid other sql queries.
        """

        self.signalRemoveProgressBar.emit(progressBarId)

        if not error:
            self.setSortingEnabled(True)
            self.sortItems(config['DatabaseDisplayColumn']['itemRunId']['index'], QtCore.Qt.DescendingOrder)
            self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)


            self.signalSendStatusBarMessage.emit('Ready', 'green')


        # We store the total number of run
        self.nbTotalRun = nbTotalRun

        # Done
        self.signalDatabaseClickDone.emit(databaseAbsPath)
        self.signalUpdateCurrentDatabase.emit(getDatabaseNameFromAbsPath(databaseAbsPath))

        # We periodically check if there is not a new run to display
        self.databaseAbsPath = databaseAbsPath
        self.dataBaseCheckNbRun(databaseAbsPath,
                                nbTotalRun)



    def dataBaseCheckNbRun(self, databaseAbsPath: str,
                                 nbTotalRun:  int):
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
        self.workerCheck = dataBaseCheckNbRunThread(databaseAbsPath,
                                                    nbTotalRun)

        # Connect signals
        self.workerCheck.signal.dataBaseUpdate.connect(self.signal2StatusBarDatabaseUpdate)
        self.workerCheck.signal.addStatusBarMessage.connect(self.signalAddStatusBarMessage)
        self.workerCheck.signal.dataBaseCheckNbRun.connect(self.slotDataBaseCheckNbRun)

        # Execute the thread
        self.threadpool.start(self.workerCheck)



    QtCore.pyqtSlot(str, int)
    def slotDataBaseCheckNbRun(self, databaseAbsPath: str,
                                     nbTotalRun:  int):
        # If we are style displaying the same database
        if self.databaseAbsPath==databaseAbsPath:
            self.nbTotalRun = nbTotalRun
            self.dataBaseCheckNbRun(databaseAbsPath,
                                    nbTotalRun)



    QtCore.pyqtSlot(str)
    def updateDatabasePath(self, databaseAbsPath: str):
        self.databaseAbsPath=databaseAbsPath
        if hasattr(self, 'workerCheck'):
            self.workerCheck._stop = True



    def runClick(self, currentRow: int=0) -> None:
        """
        When clicked display the measured dependent parameters in the
        tableWidgetPtableWidgetParameters.
        Database is accessed through a thread, see runClickFromThread.
        """

        databaseAbsPath = self.item(currentRow, config['DatabaseDisplayColumn']['databaseAbsPath']['index']).text()
        runId           = int(self.item(currentRow, config['DatabaseDisplayColumn']['itemRunId']['index']).text())
        experimentName  = self.item(currentRow, config['DatabaseDisplayColumn']['experimentName']['index']).text()
        runName         = self.item(currentRow, config['DatabaseDisplayColumn']['runName']['index']).text()

        self.signalSendStatusBarMessage.emit('Loading run parameters', 'orange')

        worker = LoadRunInfoThread(databaseAbsPath, # databaseAbsPath
                                   runId, # runId
                                   experimentName, # experimentName
                                   runName, # runName
                                   False) # doubleClicked
        worker.signal.updateRunInfo.connect(self.signalRunClick)

        # Execute the thread
        self.threadpool.start(worker)



    def runDoubleClick(self, currentRow: int=0,
                             currentColumn: int=0) -> None:

        databaseAbsPath = self.item(currentRow, config['DatabaseDisplayColumn']['databaseAbsPath']['index']).text()
        runId           = int(self.item(currentRow, config['DatabaseDisplayColumn']['itemRunId']['index']).text())
        experimentName  = self.item(currentRow, config['DatabaseDisplayColumn']['experimentName']['index']).text()
        runName         = self.item(currentRow, config['DatabaseDisplayColumn']['runName']['index']).text()

        # If we detect a double click on the "Comments" column
        # We do not launch a plot but open a comment dialog
        if currentColumn==config['DatabaseDisplayColumn']['comment']['index']:

            currentComment = self.item(currentRow, config['DatabaseDisplayColumn']['comment']['index']).text()
            savedComment = self.properties.getRunComment(runId)
            # Either the user just added a comment in this session
            if currentComment!=self.properties.getRunComment(runId):
                comment = currentComment
            # Or the current comment is the one saved in the json file
            else:
                comment = savedComment

            self.dialogComment = DialogComment(runId,
                                               comment)
            self.dialogComment.signalCloseDialogComment.connect(self.slotCloseCommentDialog)
            self.dialogComment.signalUpdateDialogComment.connect(self.slotUpdateCommentDialog)
        else:
            # When user doubleclick on a run, we disable the row to avoid
            # double data downloading of the same dataset
            self.disableRow(currentRow)
            self.doubleClickCurrentRow = currentRow
            self.doubleClickDatabaseAbsPath = databaseAbsPath

            self.signalSendStatusBarMessage.emit('Loading run parameters', 'orange')

            worker = LoadRunInfoThread(databaseAbsPath, # databaseAbsPath
                                    runId, # runId
                                    experimentName, # experimentName
                                    runName, # runName
                                    True) # doubleClicked
            worker.signal.updateRunInfo.connect(self.signalRunClick)

            # Execute the thread
            self.threadpool.start(worker)



    def disableRow(self, row: int) -> None:
        """
        Disable the given row.
        Used to avoid unwated click on a run.
        """

        for column in range(self.columnCount()):
            if self.item(row, column) is not None:
                self.item(row, column).setFlags(QtCore.Qt.ItemFlag(~(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)))



    def enableRow(self, row: int) -> None:
        """
        Enable the given row.
        Used to avoid unwated click on a run.
        """
        for column in range(self.columnCount()):
            if self.item(row, column) is not None:
                self.item(row, column).setFlags(QtCore.Qt.ItemFlag(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable))



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

        runId = int(self.item(row, config['DatabaseDisplayColumn']['itemRunId']['index']).text())

        # If user wants to star a run
        if key==config['keyPressedStared'].lower():

            # If the run was already stared
            # We remove the star of the table
            # We remove the runId from the json
            if runId in self.properties.getRunStared():

                # We remove the star from the row
                item = TableWidgetItemNumOrdered(str(runId))
                item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'empty.png')))
                self.setItem(row, config['DatabaseDisplayColumn']['itemRunId']['index'], item)

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
                self.setItem(row, config['DatabaseDisplayColumn']['itemRunId']['index'], item)

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
                self.setItem(row, config['DatabaseDisplayColumn']['itemRunId']['index'], item)

                # We update the json
                self.properties.jsonRemoveHiddenRun(runId)
            else:

                # We modify the item and hide the row
                item = TableWidgetItemNumOrdered(str(runId))
                item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'trash.png')))
                item.setForeground(QtGui.QBrush(QtGui.QColor(*config['runHiddenColor'])))
                self.setItem(row, config['DatabaseDisplayColumn']['itemRunId']['index'], item)

                # We update the json
                self.properties.jsonAddHiddenRun(runId)


            # We hide the row only if the user didn't check the checkboxhidden
            self.signalCheckBoxHiddenHideRow.emit()


    ############################################################################
    #
    #
    #                           Export run
    #
    #
    ############################################################################



    def exportRun(self, currentRow: int) -> None:
        """
        Call when user right click on a run.
        Display a menu to export a run towards another database

        Args:
            currentRow: clicked row
        """

        databaseAbsPath = self.item(currentRow, config['DatabaseDisplayColumn']['databaseAbsPath']['index']).text()
        runId           = int(self.item(currentRow, config['DatabaseDisplayColumn']['itemRunId']['index']).text())

        self.menu = MenuExportRun(databaseAbsPath,
                                  runId)

        if hasattr(self.menu, 'filePath'):
            if self.menu.filePath!='':
                # Signal propagated to the main to come back with a progress bar
                self.signalExportRunAddProgressBar.emit(databaseAbsPath,
                                                        self.menu.filePath,
                                                        runId)


    @QtCore.pyqtSlot(str, str, int, int)
    def exportRunLoad(self, source_db_path: str,
                            target_db_path: str,
                            runId: int,
                            progressBarId: int) -> None:
        """
        Called from the statusBar.
        Run a thread which will run a process to load qcodes and extract a run
        towards another database.

        Args:
            source_db_path: Path to the source DB file
            target_db_path: Path to the target DB file.
                The target DB file will be created if it does not exist.
            runId: The run_id of the run to copy into the target DB file
            progressBarId: id of the progress Bar
        """

        worker = ExportRunThread(source_db_path,
                                 target_db_path,
                                 runId,
                                 progressBarId)

        # Connect signals
        worker.signal.sendStatusBarMessage.connect(self.signalSendStatusBarMessage)
        worker.signal.updateProgressBar.connect(self.signalUpdateProgressBar)
        worker.signal.removeProgressBar.connect(self.signalRemoveProgressBar)

        # Execute the thread
        self.threadpool.start(worker)



    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot()
    def slotRunClickDone(self) -> None:
        """
        Called by MainWindow when user has doubleClicked on a row.
        Enable the row again if the use didn't change the database in the meantime.
        """

        if hasattr(self, 'doubleClickCurrentRow'):
            if self.doubleClickDatabaseAbsPath==self.item(self.doubleClickCurrentRow, config['DatabaseDisplayColumn']['databaseAbsPath']['index']).text():
                self.enableRow(self.doubleClickCurrentRow)
            del(self.doubleClickCurrentRow)
            del(self.doubleClickDatabaseAbsPath)



    @QtCore.pyqtSlot(int)
    def slotFromCheckBoxHiddenCheckBoxHiddenClick(self, state: int) -> None:
        """
        Call when user clicks on the "Show hidden checkbox.
        When check, show all databse run.
        When unchecked, hide again the hidden run.
        """

        runHidden   = self.properties.getRunHidden()
        nbTotalRow  = self.rowCount()

        # If user wants to see hidden run
        if state==2:

            self.signalCheckBoxHiddenChecked.emit(True)

            for row in range(nbTotalRow):

                if int(self.item(row, config['DatabaseDisplayColumn']['itemRunId']['index']).text()) in runHidden:
                    self.setRowHidden(row, False)

        # Hide hidden run again
        elif state==0:

            self.signalCheckBoxHiddenChecked.emit(False)

            for row in range(nbTotalRow):

                if int(self.item(row, config['DatabaseDisplayColumn']['itemRunId']['index']).text()) in runHidden:
                    self.setRowHidden(row, True)
                else:
                    self.setRowHidden(row, False)



    @QtCore.pyqtSlot(int)
    def slotFromCheckBoxStaredCheckBoxStaredClick(self, state: int) -> None:
        """
        Call when user clicks on the "Show only stared run" checkbox.
        When check, show only stared run.
        When unchecked, we show all run
        """

        runHidden   = self.properties.getRunHidden()
        runStared   = self.properties.getRunStared()
        nbTotalRow  = self.rowCount()

        # If user wants to see only stared run
        if state==2:

            self.signalCheckBoxStaredChecked.emit(True)

            for row in range(nbTotalRow):
                if int(self.item(row, config['DatabaseDisplayColumn']['itemRunId']['index']).text()) not in runStared:
                    self.setRowHidden(row, True)
                else:
                    self.setRowHidden(row, False)

        # Show all
        elif state==0:

            self.signalCheckBoxStaredChecked.emit(False)

            for row in range(nbTotalRow):
                if int(self.item(row, config['DatabaseDisplayColumn']['itemRunId']['index']).text()) in runHidden:
                    self.setRowHidden(row, True)
                else:
                    self.setRowHidden(row, False)



    @QtCore.pyqtSlot()
    def slotClearTable(self) -> None:

        clearTableWidget(self)



    @QtCore.pyqtSlot()
    def slotCloseCommentDialog(self) -> None:

        # We close the plot
        self.dialogComment._allowClosing = True
        self.dialogComment.deleteLater()
        del(self.dialogComment)



    @QtCore.pyqtSlot(dict)
    def slotUpdate(self, config: dict) -> None:
        """
        Called from DialogMenuDatabaseDisplay when user clicks on a checkbox
        Show or hide column dependending on the config dictionnary.

        Args:
            config: dict of the current config file
        """

        for val in config['DatabaseDisplayColumn'].values():

            # Hide or display some column
            self.setColumnHidden(val['index'], False==val['visible'])



    @QtCore.pyqtSlot(int, str)
    def slotUpdateCommentDialog(self, runId: int,
                                      comment: str) -> None:
        """
        Called from the dialogComment when user change its text

        Args:
            runId: Id of the commented run
            comment: comment to be added to the run
        """

        # Add the comment on the GUI
        for row in range(self.rowCount()):
            if int(self.item(row, config['DatabaseDisplayColumn']['itemRunId']['index']).text())==runId:
                self.setItem(row, config['DatabaseDisplayColumn']['comment']['index'], QtWidgets.QTableWidgetItem(comment))
                break

        # Save the comment in the json file
        self.properties.jsonAddCommentRun(runId,
                                          comment)
