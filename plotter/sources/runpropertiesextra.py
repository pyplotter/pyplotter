# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtWidgets
import os
import json

from .config import config
from ..ui.myTableWidgetItem import MyTableWidgetItem

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../ui/pictures/')

class RunPropertiesExtra:


    def __init__(self):
        """
        Class handling the interaction between the user and the json file
        containing extra properties on the run.
        The run can be stared by pressing "s", meaning the run contains
        meaningfull data
        The run can be hidden by pressing "h", meaning the run should be hidden
        from the plotter.

        No data are modify by this class, only the extra json file.
        """


        super(RunPropertiesExtra, self).__init__()




    ############################################################################
    #
    #
    #                           Json
    #
    #
    ############################################################################



    def jsonLoad(self) -> None:
        """
        Load the json file containing folder's database extra properties.
        If the json file doesn't exist it creates an empty dict instead.
        """

        self.jsonPath = self.jsonGetPath()

        if os.path.exists(self.jsonPath):
            self.json   = json.load(open(self.jsonPath, 'r'))

            # Update of old database to make the database path independent
            # of the mounting point
            replaceDatabasePath = {}
            for databasePath in self.json.keys():
                mount, _ = os.path.splitdrive(databasePath)
                if mount!='':
                    replaceDatabasePath[databasePath] = os.path.basename(databasePath)

            isJsonModified = False
            for oldDatabasePath, newDatabasePath in replaceDatabasePath.items():
                self.json[newDatabasePath] = self.json[oldDatabasePath]
                del(self.json[oldDatabasePath])
                isJsonModified = True
            if isJsonModified:
                print('    Database extra properties updated.')
                self.jsonSave()
        else:
            self.json   = {}



    def jsonGetPath(self) -> str:
        """
        Return the path of the current json file.
        """

        return os.path.join(self.currentPath, config['fileNameRunInfo']+'.json')



    def jsonRemoveStaredRun(self, runId : int) -> None:
        """
        Remove a runId from a database in a json file.
        Since the json has been modified, save the new json

        Parameters
        ----------
        runId : int
            Id of the run to be removed
        """

        self.json[self.databaseGetPath()]['stared'].remove(int(runId))

        self.jsonSave()



    def jsonRemoveHiddenRun(self, runId : int) -> None:
        """
        Remove a runId from a database in a json file.
        Since the json has been modified, save the new json

        Parameters
        ----------
        runId : int
            Id of the run to be removed
        """

        self.json[self.databaseGetPath()]['hidden'].remove(int(runId))

        self.jsonSave()



    def jsonAddHiddenRun(self, runId : int) -> None:
        """
        Add a runId from a database in a json file.
        Since the json has been modified, save the new json

        Parameters
        ----------
        runId : int
            Id of the run to be added
        """

        runId = int(runId)
        databasePath = self.databaseGetPath()

        if self.isDatabaseInJson():
            if self.isHiddenRunInDatabase():

                self.json[databasePath]['hidden'].append(runId)
            else:

                self.json[databasePath]['hidden'] = [runId]
        else:

            self.json[databasePath] = {}
            self.json[databasePath]['hidden'] = [runId]

        self.jsonSave()



    def jsonAddStaredRun(self, runId : int) -> None:
        """
        Add a runId from a database in a json file.
        Since the json has been modified, save the new json

        Parameters
        ----------
        runId : int
            Id of the run to be added
        """

        runId = int(runId)
        databasePath = self.databaseGetPath()

        if self.isDatabaseInJson():
            if self.isStaredRunInDatabase():

                self.json[databasePath]['stared'].append(runId)
            else:

                self.json[databasePath]['stared'] = [runId]
        else:

            self.json[databasePath] = {}
            self.json[databasePath]['stared'] = [runId]

        self.jsonSave()



    def jsonSave(self, encoding : str='utf-8', ensure_ascii : bool=False, indent : int=4) -> None:
        """
        Save a json file
        """

        with open(self.jsonPath, 'w', encoding=encoding) as f:
            json.dump(self.json, f, ensure_ascii=ensure_ascii, indent=indent)
        f.close()



    ############################################################################
    #
    #
    #                           GUI
    #
    #
    ############################################################################



    def checkBoxHiddenState(self, cb : QtWidgets.QCheckBox) -> None:
        """
        Call when user clicks on the "Show hidden checkbox.
        When check, show all databse run.
        When unchecked, hide again the hidden run.
        """

        runHidden   = self.getRunHidden()
        nbTotalRow  = self.tableWidgetDataBase.rowCount()

        # If user wants to see hidden run
        if cb.isChecked():

            for row in range(nbTotalRow):

                if int(self.tableWidgetDataBase.item(row, 0).text()) in runHidden:
                    self.tableWidgetDataBase.setRowHidden(row, False)

        # Hide hidden run again
        else:

            for row in range(nbTotalRow):

                if int(self.tableWidgetDataBase.item(row, 0).text()) in runHidden:
                    self.tableWidgetDataBase.setRowHidden(row, True)
                else:
                    self.tableWidgetDataBase.setRowHidden(row, False)



    def tableWidgetDataBasekeyPress(self, key : str, row : int) -> None:
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

        runId = int(self.tableWidgetDataBase.item(row, 0).text())


        # If user wants to star a run
        if key==config['keyPressedStared'].lower():

            # If the run was already stared
            # We remove the star of the table
            # We remove the runId from the json
            if runId in self.getRunStared():

                # We remove the star from the row
                item = MyTableWidgetItem(str(runId))
                item.setIcon(QtGui.QIcon(PICTURESPATH+'empty.png'))
                self.tableWidgetDataBase.setItem(row, 0, item)

                # We update the json
                self.jsonRemoveStaredRun(runId)

                # If the database does not contain stared run anymore, we modify
                # its icon
                if len(self.getRunStared())==0:
                    for row in range(self.tableWidgetFolder.rowCount()):
                        if self._currentDatabase==self.tableWidgetFolder.item(row, 0).text():
                            self.tableWidgetFolder.item(row, 0).setIcon(QtGui.QIcon(PICTURESPATH+'database.png'))

            # If the user wants to stared the run
            else:

                # We put a star in the row
                item = MyTableWidgetItem(str(runId))
                item.setIcon(QtGui.QIcon(PICTURESPATH+'star.png'))
                item.setForeground(QtGui.QBrush(QtGui.QColor(*config['runStaredColor'])))
                self.tableWidgetDataBase.setItem(row, 0, item)

                # We update the json
                self.jsonAddStaredRun(runId)

                # If the database containing the stared run is displayed, we star it
                for row in range(self.tableWidgetFolder.rowCount()):
                    if self._currentDatabase==self.tableWidgetFolder.item(row, 0).text():
                        self.tableWidgetFolder.item(row, 0).setIcon(QtGui.QIcon(PICTURESPATH+'databaseStared.png'))




        # If user wants to hide a run
        elif key==config['keyPressedHide'].lower():

            # If the run was already hidden
            # We unhide the row
            # We remove the runId from the json
            if runId in self.getRunHidden():

                item = MyTableWidgetItem(str(runId))
                item.setIcon(QtGui.QIcon(PICTURESPATH+'empty.png'))
                item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                self.tableWidgetDataBase.setItem(row, 0, item)


                # We update the json
                self.jsonRemoveHiddenRun(runId)
            else:

                # We modify the item and hide the row
                item = MyTableWidgetItem(str(runId))
                item.setIcon(QtGui.QIcon(PICTURESPATH+'trash.png'))
                item.setForeground(QtGui.QBrush(QtGui.QColor(*config['runHiddenColor'])))
                self.tableWidgetDataBase.setItem(row, 0, item)

                if not self.checkBoxHidden.isChecked():
                    self.tableWidgetDataBase.setRowHidden(row, True)


                # We update the json
                self.jsonAddHiddenRun(runId)




    ############################################################################
    #
    #
    #                           Get info from json
    #
    #
    ############################################################################



    def databaseGetPath(self) -> str:
        """
        Return the path of the database without the mounting point
        """

        return self._currentDatabase



    def getDatabaseStared(self) -> list:
            """
            Return a list of all database of the current folder which contains
            at least one stared run.
            """

            databasePaths = []
            for key, val in self.json.items():
                if 'stared' in val:
                    if len(val['stared'])>0:
                        databasePaths.append(key)

            return [os.path.basename(os.path.normpath(databasePath)) for databasePath in databasePaths]



    def isDatabaseStared(self) -> bool:
        """
        Return True if the databasePath has at least one run stared in
        the json file.
        False otherwise.
        """

        databasePath = self.databaseGetPath()

        if databasePath in self.json:
            if 'stared' in self.json[databasePath]:
                if len(self.json[databasePath]['stared'])>0:

                    return True
                else:
                    return False
            else:
                return False
        else:
            return False



    def isDatabaseInJson(self) -> bool:
        """
        Return True if the current database is written inside the Json file.
        False otherwise.
        """

        if self.databaseGetPath() in self.json:
            return True
        else:
            return False



    def isStaredRunInDatabase(self) -> bool:
        """
        Return True if the current database hase a dict "stared" written in
        the database in Json file.
        False otherwise.
        """

        if 'stared' in self.json[self.databaseGetPath()]:
            return True
        else:
            return False



    def isHiddenRunInDatabase(self) -> bool:
        """
        Return True if the current database hase a dict "hidden" written in
        the database in Json file.
        False otherwise.
        """

        if 'hidden' in self.json[self.databaseGetPath()]:
            return True
        else:
            return False



    def getRunStared(self) -> list:
        """
        Return the list of the stared run of the current database.
        """

        if self.isDatabaseInJson():
            if self.isStaredRunInDatabase():
                staredRun = self.json[self.databaseGetPath()]['stared']
            else:
                staredRun = []
        else:
            staredRun = []

        return staredRun



    def getRunHidden(self) -> list:
        """
        Return the list of the hidden run of the current database.
        """

        if self.isDatabaseInJson():
            if self.isHiddenRunInDatabase():
                hiddenRun = self.json[self.databaseGetPath()]['hidden']
            else:
                hiddenRun = []
        else:
            hiddenRun = []

        return hiddenRun