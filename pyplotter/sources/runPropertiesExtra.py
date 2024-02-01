import os
import json
from typing import Optional

from .config import loadConfigCurrent
config = loadConfigCurrent()

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



    def jsonLoad(self, currentPath: str,
                       databaseName: Optional[str]=None) -> None:
        """
        Load the json file containing folder's database extra properties.
        If the json file doesn't exist it creates an empty dict instead.
        """

        self.jsonPath     = self.jsonGetPath(currentPath)
        self.databaseName = databaseName

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



    def jsonGetPath(self, currentPath: str) -> str:
        """
        Return the path of the current json file.
        """

        return os.path.join(currentPath, config['fileNameRunInfo']+'.json')



    def jsonRemoveStaredRun(self, runId : int) -> None:
        """
        Remove a runId from a database in a json file.
        Since the json has been modified, save the new json

        Parameters
        ----------
        runId : int
            Id of the run to be removed
        """

        self.json[self.databaseName]['stared'].remove(int(runId))

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

        self.json[self.databaseName]['hidden'].remove(int(runId))

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

        if self.isDatabaseInJson():
            if self.isHiddenRunInDatabase():

                self.json[self.databaseName]['hidden'].append(runId)
            else:

                self.json[self.databaseName]['hidden'] = [runId]
        else:

            self.json[self.databaseName] = {}
            self.json[self.databaseName]['hidden'] = [runId]

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

        if self.isDatabaseInJson():
            if self.isStaredRunInDatabase():

                self.json[self.databaseName]['stared'].append(runId)
            else:

                self.json[self.databaseName]['stared'] = [runId]
        else:

            self.json[self.databaseName] = {}
            self.json[self.databaseName]['stared'] = [runId]

        self.jsonSave()



    def jsonAddCommentRun(self, runId : int,
                                comment: str) -> None:
        """
        Add a comment from a database in a json file.
        Since the json has been modified, save the new json
        """

        if self.isDatabaseInJson():
            if self.isCommentedRunInDatabase():

                self.json[self.databaseName]['comments'][runId] = comment
            else:

                self.json[self.databaseName]['comments'] = {runId: comment}
        else:

            self.json[self.databaseName] = {'comments' : {runId: comment}}

        self.jsonSave()



    def jsonRemoveCommentRun(self, runId : int) -> None:
        """
        Remove a runId from a database in a json file.
        Since the json has been modified, save the new json
        """

        del(self.json[self.databaseName]['comments'][runId])

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
    #                           Get info from json
    #
    #
    ############################################################################



    def getDatabaseStared(self) -> list:
            """
            Return a list of all database of the current folder which contains
            at least one stared run.
            """

            databaseNames = []
            for key, val in self.json.items():
                if 'stared' in val:
                    if len(val['stared'])>0:
                        databaseNames.append(key)

            return [os.path.basename(os.path.normpath(databaseName)) for databaseName in databaseNames]



    def isDatabaseStared(self, databaseName: str) -> bool:
        """
        Return True if the databaseName has at least one run stared in
        the json file.
        False otherwise.
        """

        if databaseName in self.json:
            if 'stared' in self.json[databaseName]:
                if len(self.json[databaseName]['stared'])>0:

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

        if self.databaseName in self.json:
            return True
        else:
            return False



    def isStaredRunInDatabase(self) -> bool:
        """
        Return True if the current database hase a dict "stared" written in
        the database in Json file.
        False otherwise.
        """

        if 'stared' in self.json[self.databaseName]:
            return True
        else:
            return False



    def isHiddenRunInDatabase(self) -> bool:
        """
        Return True if the current database hase a dict "hidden" written in
        the database in Json file.
        False otherwise.
        """

        if 'hidden' in self.json[self.databaseName]:
            return True
        else:
            return False



    def isCommentedRunInDatabase(self) -> bool:
        """
        Return True if the current database hase a dict "comments" written in
        the database in Json file.
        False otherwise.
        """

        if 'comments' in self.json[self.databaseName]:
            return True
        else:
            return False



    def getRunStared(self) -> list:
        """
        Return the list of the stared run of the current database.
        """

        if self.isDatabaseInJson():
            if self.isStaredRunInDatabase():
                staredRun = self.json[self.databaseName]['stared']
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
                hiddenRun = self.json[self.databaseName]['hidden']
            else:
                hiddenRun = []
        else:
            hiddenRun = []

        return hiddenRun



    def isRunCommented(self, runId: int) -> bool:
        """
        Return True if the run has a comment in the json file, False otherwise
        """

        if self.isDatabaseInJson():
            if self.isCommentedRunInDatabase():
                if runId in self.json[self.databaseName]['comments'].keys():
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False



    def getRunComment(self, runId: int) -> str:
        """
        Return the comment of the run, '' if no comment
        """

        comment = ''
        if self.isDatabaseInJson():
            if self.isCommentedRunInDatabase():
                if str(runId) in self.json[self.databaseName]['comments'].keys():
                    comment = self.json[self.databaseName]['comments'][str(runId)]

        return comment