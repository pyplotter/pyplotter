# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import Union
import os
from time import time

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..ui.menuDb import MenuDb
from ..sources.runPropertiesExtra import RunPropertiesExtra
from ..sources.functions import clearTableWidget, isBlueForsFolder, sizeof_fmt

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')

class TableWidgetFolder(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)
    signalDatabaseClick    = QtCore.pyqtSignal(str)
    signalCSVClick         = QtCore.pyqtSignal(str, bool)
    signalBlueForsClick         = QtCore.pyqtSignal(str, bool)
    signalDatabasePathUpdate         = QtCore.pyqtSignal(str)
    signalUpdateLabelPath    = QtCore.pyqtSignal(str)



    def __init__(self, parent=None) -> None:
        super(TableWidgetFolder, self).__init__(parent)

        self.cellClicked.connect(self.itemClicked)
        self.customContextMenuRequested.connect(self.itemClicked)

        self.properties = RunPropertiesExtra()


        # Flag
        self._dataDowloadingFlag = False
        # To avoid the opening of two databases as once
        self._flagDatabaseClicking = False


        # Use to differentiate click to doubleClick
        self.lastClickTime = time()
        self.lastClickRow  = 100



    def first_call(self):

        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # If we are unable to detect the config folder, we switch in local mode
        if not os.path.isdir(os.path.normpath(config['path'])):

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

        # By default, we browse the root folder
        self.folderClicked(directory=self.currentPath)

        # To avoid calling the signal when updating folder content
        self._folderUpdating  = False
        # To avoid calling the signal when starting the GUI
        self._guiInitialized = True



    def folderClicked(self, directory: str) -> None:
        """
        Basically display folder and csv file of the current folder.

        Parameters
        ----------
        directory : str
            Path of the folder to be browsed.
        """

        # When signal the updating of the folder to prevent unwanted item events
        self._folderUpdating = True
        self.currentPath = directory

        self.signalUpdateLabelPath.emit(directory)


        # Load runs extra properties
        self.properties.jsonLoad(self.currentPath)
        databaseStared = self.properties.getDatabaseStared()

        ## Display the current dir content
        clearTableWidget(self)
        row = 0
        for file in sorted(os.listdir(self.currentPath), reverse=True):

            # We do not display files and folders starting with a "."
            if file[0]=='.':
                continue

            abs_filename = os.path.join(self.currentPath, file)
            file_extension = os.path.splitext(abs_filename)[-1][1:]

            # Only display folder and Qcodes database
            # Add icon depending of the item type

            # If folder
            if os.path.isdir(abs_filename):

                item =  QtWidgets.QTableWidgetItem(file)
                # If looks like a BlueFors log folder
                if isBlueForsFolder(file):
                    item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'bluefors.png')))
                # Other folders
                else:
                    if file in config['enhancedFolder']:
                        item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'folderEnhanced.png')))
                    else:
                        item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'folder.png')))
                self.insertRow(row)
                self.setItem(row, 0, item)
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

                        item =  QtWidgets.QTableWidgetItem(file)
                        if file_extension.lower()=='csv':
                            item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'csv.png')))
                        elif file_extension.lower()=='s2p':
                            item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 's2p.png')))
                        elif DatabaseAlreadyOpened and file in databaseStared:
                            item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'databaseOpenedStared.png')))
                            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                        elif DatabaseAlreadyOpened:
                            item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'databaseOpened.png')))
                            item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                        elif file in databaseStared:
                            item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'databaseStared.png')))
                        else:
                            item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'database.png')))
                        self.insertRow(row)
                        self.setItem(row, 0, item)

                        # Get file size in hman readable format
                        fileSizeItem = QtWidgets.QTableWidgetItem(sizeof_fmt(os.path.getsize(abs_filename)))
                        fileSizeItem.setTextAlignment(QtCore.Qt.AlignRight)
                        fileSizeItem.setTextAlignment(QtCore.Qt.AlignVCenter)
                        self.setItem(row, 1, fileSizeItem)
                        row += 1

        self.setSortingEnabled(True)
        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        # Allow item event again
        self._folderUpdating = False



    def itemClicked(self, b: Union[int, QtCore.QPoint]) -> None:
        """
        Handle event when user clicks on datafile.
        The user can either click on a folder or a file.
        If it is a folder, we launched the folderClicked method.
        If it is a file, we launched the databaseClick method.
        """

        # We check if the signal is effectively called by user
        if not self._folderUpdating and self._guiInitialized:

            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            # Get current item
            currentRow  = self.currentIndex().row()
            currentItem =  self.model().index(currentRow, 0).data()

            nextPath = os.path.join(self.currentPath, currentItem)
            self.databaseAbsPath = os.path.normpath(os.path.join(self.currentPath, currentItem)).replace("\\", "/")

            # If the folder is a BlueFors folder
            if isBlueForsFolder(currentItem):
                self.blueForsClick()
            # If it is a csv or a s2p file
            elif nextPath[-3:].lower() in ['csv', 's2p']:
                self.csvClick()
            # If the folder is a regulat folder
            elif os.path.isdir(nextPath):
                self.signalSendStatusBarMessage.emit('Updating', 'orange')
                self.folderClicked(directory=nextPath)
                self.signalSendStatusBarMessage.emit('Ready', 'green')
            # If it is a QCoDeS database
            else:
                # If right clicked
                if isinstance(b, QtCore.QPoint):
                    # Job done, we restor the usual cursor
                    QtWidgets.QApplication.restoreOverrideCursor()

                    # We open a homemade menu
                    MenuDb(self.databaseAbsPath)
                else:
                    self.databaseClick()

            # Job done, we restor the usual cursor
            QtWidgets.QApplication.restoreOverrideCursor()

        # When the signal has been called at least once
        if not self._guiInitialized:
            self._guiInitialized = True



    def blueForsClick(self, currentRow: int=0,
                            currentColumn: int=0,
                            previousRow: int=0,
                            previousColumn: int=0) -> None:

        doubleClick = False
        if currentRow==self.lastClickRow:
            if time() - self.lastClickTime<0.5:
                doubleClick = True

        # We inform the tableWidgetDatabase of the the databasePath
        self.signalDatabasePathUpdate.emit(self.databaseAbsPath)
        self.signalBlueForsClick.emit(self.databaseAbsPath,
                                      doubleClick)



    def csvClick(self, currentRow: int=0,
                       currentColumn: int=0,
                       previousRow: int=0,
                       previousColumn: int=0) -> None:

        doubleClick = False
        if currentRow==self.lastClickRow:
            if time() - self.lastClickTime<0.5:
                doubleClick = True

        # We inform the tableWidgetDatabase of the the databasePath
        self.signalDatabasePathUpdate.emit(self.databaseAbsPath)
        self.signalCSVClick.emit(self.databaseAbsPath,
                                 doubleClick)


    def databaseClick(self) -> None:
        """
        Display the content of the clicked dataBase into the database table
        which will then contain all runs.
        """

        # We inform the tableWidgetDatabase of the the databasePath
        self.signalDatabasePathUpdate.emit(self.databaseAbsPath)

        self.currentPath  = os.path.dirname(self.databaseAbsPath)
        self.databaseName = os.path.basename(self.databaseAbsPath)

        # Load runs extra properties
        self.properties.jsonLoad(self.currentPath,
                                 self.databaseName)

        # To avoid the opening of two databases as once
        if self._flagDatabaseClicking:
            return
        self._flagDatabaseClicking = True

        # We show the database is now opened
        if self.properties.isDatabaseStared():
            self.databaseUpdateIcon('databaseOpenedStared.png')
        else:
            self.databaseUpdateIcon('databaseOpened.png')


        self.signalDatabaseClick.emit(self.databaseAbsPath)



    @QtCore.pyqtSlot()
    def databaseClickDone(self) -> None:
        """
        Display the content of the clicked dataBase into the database table
        which will then contain all runs.
        """

        # We show the database is now closed
        if self.properties.isDatabaseStared():
            self.databaseUpdateIcon('databaseStared.png')
        else:
            self.databaseUpdateIcon('database.png')

        # To avoid the opening of two databases as once
        self._flagDatabaseClicking = False



    def databaseUpdateIcon(self, iconName: str) -> None:

        item = self.item(self.currentIndex().row(), 0)
        item.setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, iconName)))




    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot(str)
    def folderOpened(self, directory: str) -> None:

        self.folderClicked(directory)



    @QtCore.pyqtSlot()
    def slotFromTableWidgetDataBaseDatabaseStars(self):

        databaseName = os.path.basename(self.databaseAbsPath)

        for row in range(self.rowCount()):
            if databaseName==self.item(row, 0).text():
                self.item(row, 0).setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'databaseStared.png')))



    @QtCore.pyqtSlot()
    def slotFromTableWidgetDataBaseDatabaseUnstars(self):

        databaseName = os.path.basename(self.databaseAbsPath)

        for row in range(self.rowCount()):
            if databaseName==self.item(row, 0).text():
                self.item(row, 0).setIcon(QtGui.QIcon(os.path.join(PICTURESPATH, 'database.png')))
