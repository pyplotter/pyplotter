# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import List
import os
from time import time

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..sources.runPropertiesExtra import RunPropertiesExtra
from .tableWidgetItemNumOrdered import TableWidgetItemNumOrdered
from ..sources.workers.loadDataBase import LoadDataBaseThread
from ..sources.workers.loadRunInfo import LoadRunInfoThread
from ..sources.workers.checkNbRunDatabase import dataBaseCheckNbRunThread
from ..sources.functions import clearTableWidget, getDatabaseNameFromAbsPath
from ..ui.dialogs.dialogComment import DialogComment

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')


class TableWidgetDatabase(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    # Propagated to statusBarMain
    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)
    signalAddStatusBarMessage  = QtCore.pyqtSignal(str, str)
    signalUpdateProgressBar    = QtCore.pyqtSignal(QtWidgets.QProgressBar, int, str)
    signalRemoveProgressBar    = QtCore.pyqtSignal(QtWidgets.QProgressBar)
    # Propagated to tableWidgetFolder, checkBoxHidden, checkBoxStared
    signalDatabaseClickDone = QtCore.pyqtSignal()
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

    # Internal event, see keyPressEvent
    keyPressed = QtCore.pyqtSignal(str, int)


    def __init__(self, parent=None) -> None:
        super(TableWidgetDatabase, self).__init__(parent)

        # Forbid editing of the cells
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # When user wants to look at a run
        self.cellClicked.connect(self.runClick)

        # When user wants to hide or stars a run
        self.keyPressed.connect(self.tableWidgetDataBasekeyPress)

        # Flag
        self._dataDowloadingFlag = False
        # Use to differentiate click to doubleClick
        self.lastClickTime = time()
        self.lastClickRow  = 100

        # To avoid the opening of two databases as once
        self._databaseClicking = False

        self.properties = RunPropertiesExtra()
        self.threadpool = QtCore.QThreadPool()



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



    @QtCore.pyqtSlot(str, QtWidgets.QProgressBar)
    def databaseClick(self, databaseAbsPath: str,
                            progressBar: QtWidgets.QProgressBar) -> None:
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
        worker = LoadDataBaseThread(databaseAbsPath,
                                    progressBar)

        # Connect signals
        worker.signal.sendStatusBarMessage.connect(self.signalSendStatusBarMessage)
        worker.signal.addRows.connect(self.databaseClickAddRows)
        worker.signal.updateProgressBar.connect(self.signalUpdateProgressBar)
        worker.signal.databaseClickDone.connect(self.databaseClickDone)

        # Execute the thread
        self.threadpool.start(worker)



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


    @QtCore.pyqtSlot(QtWidgets.QProgressBar, bool, str, int)
    def databaseClickDone(self,progressBar    : QtWidgets.QProgressBar,
                               error          : bool,
                               databaseAbsPath: str,
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
            self.sortItems(config['DatabaseDisplayColumn']['itemRunId']['index'], QtCore.Qt.DescendingOrder)
            self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)


            self.signalSendStatusBarMessage.emit('Ready', 'green')


        # We store the total number of run
        self.nbTotalRun = nbTotalRun

        # Done
        self._databaseClicking = False
        self.signalDatabaseClickDone.emit()
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



    def runClick(self, currentRow: int=0,
                       currentColumn: int=0,
                       previousRow: int=0,
                       previousColumn: int=0) -> None:
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

        databaseAbsPath = self.item(currentRow, config['DatabaseDisplayColumn']['databaseAbsPath']['index']).text()
        runId           = int(self.item(currentRow, config['DatabaseDisplayColumn']['itemRunId']['index']).text())
        experimentName  = self.item(currentRow, config['DatabaseDisplayColumn']['experimentName']['index']).text()
        runName         = self.item(currentRow, config['DatabaseDisplayColumn']['runName']['index']).text()

        # We check if use click or doubleClick
        doubleClick = False
        if currentRow==self.lastClickRow:
            if time() - self.lastClickTime<0.5:
                # If we detect a double click on the "Comments" column
                # We do not launch a plot but open a comment dialog
                if currentColumn==config['DatabaseDisplayColumn']['comment']['index']:
                    self.dialogComment = DialogComment(runId,
                                                       self.properties.getRunComment(runId))
                    self.dialogComment.signalCloseDialogComment.connect(self.slotCloseCommentDialog)
                    self.dialogComment.signalUpdateDialogComment.connect(self.slotUpdateCommentDialog)
                else:
                    doubleClick = True
                    # When user doubleclick on a run, we disable the row to avoid
                    # double data downloading of the same dataset
                    self.doubleClickCurrentRow = currentRow
                    self.doubleClickDatabaseAbsPath = databaseAbsPath
                    self.cellClicked.disconnect()


        # Keep track of the last click time
        self.lastClickTime = time()
        self.lastClickRow  = currentRow

        self.signalSendStatusBarMessage.emit('Loading run parameters', 'orange')

        worker = LoadRunInfoThread(databaseAbsPath,
                                   runId,
                                   experimentName,
                                   runName,
                                   doubleClick)
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
                self.cellClicked.connect(self.runClick)
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
