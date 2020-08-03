# This Python file uses the following encoding: utf-8
import time
import sqlite3
import json
import sys
import os
import qcodes as qc
from typing import Callable


class QcodesDatabase:




    def __init__(self, setStatusBarMessage = Callable[[str, bool], None]):
        """
        Class to handle extraction of runs informations and runs data from qcodes
        database.
        """

        self.setStatusBarMessage = setStatusBarMessage


        super(QcodesDatabase).__init__()




    ############################################################################
    #
    #
    #                           Properties
    #
    #
    ############################################################################




    @property
    def databasePath(self) -> str:

        return self._databasePath




    @databasePath.setter
    def databasePath(self, databasePath : str) -> None:
        """

        Parameters
        ----------
        databasePath : str
            Path to the database file.
        """

        self._databasePath = databasePath




    ############################################################################
    #
    #
    #                           Open and close connection to database
    #
    #
    ############################################################################




    def openDatabase(self) -> None:
        """
        Open connection to database using qcodes functions.

        Return
        ------
        conn : Connection
            Connection to the db
        cur : Cursor
            Cursor to the db
        """
        
        conn =  qc.dataset.sqlite.database.connect(self.databasePath)
        cur = conn.cursor()

        return conn, cur




    def closeDatabase(self, conn : qc.dataset.sqlite.connection.ConnectionPlus,
                            cur : sqlite3.Cursor) -> None:
        """
        Close the connection to the database.

        Parameters
        ----------
        conn : Connection
            Connection to the db
        cur : Cursor
            Cursor to the db
        """
        
        cur.close()
        conn.close()




    ############################################################################
    #
    #
    #                           Others
    #
    #
    ############################################################################




    def timestamp2string(self, timestamp : int, fmt : str="%Y-%m-%d %H:%M:%S") -> str:
        """
        Returns timestamp in a human-readable format.
        """

        return time.strftime(fmt, time.localtime(timestamp))





    ############################################################################
    #
    #
    #                           Queries
    #
    #
    ############################################################################




    def getNbIndependentFromRow(self, row : sqlite3.Row) -> int:
        """
        Get the number of independent parameter from a row object of sqlite3.
        The row must come from a "runs" table.

        Parameters
        ----------
        row : sqlite3.Row
            Row of a "runs" database
        """

        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        return len([i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0])




    def getNbDependentFromRow(self, row : sqlite3.Row) -> int:
        """
        Get the number of dpendent parameter from a row object of sqlite3.
        The row must come from a "runs" table.

        Parameters
        ----------
        row : sqlite3.Row
            Row of a "runs" database
        """

        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        return len([i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0])




    def getExperimentSampleFromRow(self, rows : sqlite3.Row, exp_id : int) -> tuple:
        """
        Get the experiment name and the sample name from a row object of sqlite3.
        The row must come from a "experiments" table.

        Parameters
        ----------
        row : sqlite3.Row
            Row of a "experiments" database
        exp_id : int
            Experiment id from which the experiment name and the sample name are
            extracted
        """
        
        for row in rows:
            if row['exp_id'] == exp_id:
                return row['name'], row['sample_name']




    def getListIndependentFromRunId(self, runId : int) -> list:
        """
        Get the list of independent parameter from a runId.

        Parameters
        ----------
        runId : int
            id of the run
        """

        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        self.closeDatabase(conn, cur)

        return [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]




    def getListDependentFromRunId(self, runId : int) -> list:
        """
        Get the list of dependent parameter from a runId.

        Parameters
        ----------
        runId : int
            id of the run
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        self.closeDatabase(conn, cur)

        return [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]




    def getListIndependentDependentFromRunId(self, runId : int) -> list:
        """
        Get the list of independent and dependent parameter from a runId.

        Parameters
        ----------
        runId : int
            id of the run

        Return
        ------
        parameter : tuple
            ([independent], [dependents])
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        self.closeDatabase(conn, cur)
        
        return ([i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0],
                [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0])




    def getListParametersFromRunId(self, runId : int) -> tuple:
        """
        Get the list of independent and dependent parameters from a runId.
        Return a tuple of independent and dependent parameters, each parameter
        being a dict.

        Parameters
        ----------
        runId : int
            id of the run
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        self.closeDatabase(conn, cur)
        
        independent = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]
        dependent   = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]
        
        return independent, dependent




    def getIndependentDependentSnapshotFromRunId(self, runId : int) -> tuple:
        """
        Get the list of independent and dependent parameters from a runId.
        Return a tuple of independent and dependent parameters, each parameter
        being a dict.

        Parameters
        ----------
        runId : int
            id of the run
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description, snapshot FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        snapshotDict = json.loads(row['snapshot'])
        
        self.closeDatabase(conn, cur)

        independent = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]
        dependent   = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]

        return independent, dependent, snapshotDict




    def getRunInfos(self) -> dict:
        """
        Get a handfull of information about all the run of a database.
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_id, exp_id, name, completed_timestamp, run_timestamp, result_table_name, run_description FROM 'runs'")

        runInfos = cur.fetchall()
        result_table_names = [row['result_table_name'] for row in runInfos]
        runIds = [str(row['run_id']) for row in runInfos]


        # Get runs records
        request = 'SELECT '
        for result_table_name, runId in zip(result_table_names, runIds):
            request += '(SELECT MAX(id) FROM "'+result_table_name+'") AS runId'+runId+','

        cur.execute(request[:-1])
        records = cur.fetchall()[0]


        # Get experiments Infos
        cur.execute("SELECT  exp_id, name, sample_name FROM 'experiments'")
        experimentInfos = cur.fetchall()
        
        self.closeDatabase(conn, cur)

        infos = {}
        for runInfo, runRecords in zip(runInfos, records):
            infos[runInfo['run_id']] = {'nb_independent_parameter' : self.getNbIndependentFromRow(runInfo),
                                        'nb_dependent_parameter' : self.getNbDependentFromRow(runInfo),
                                        'experiment_name' : experimentInfos[runInfo['exp_id']-1]['name'],
                                        'sample_name' : experimentInfos[runInfo['exp_id']-1]['sample_name'],
                                        'run_name' : runInfo['name'],
                                        'started' : self.timestamp2string(runInfo['run_timestamp']),
                                        'completed' : self.timestamp2string(runInfo['completed_timestamp']),
                                        'records' : runRecords}

        return infos




    def getNbTotalRun(self) -> int:
        """
        Return the number of run in the currently opened database
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT MAX(run_id) FROM 'runs'")

        rows = cur.fetchall()
        nbTotalRun = rows[0]['max(run_id)']
        
        self.closeDatabase(conn, cur)
        
        return nbTotalRun




    def isRunCompleted(self, runId : int) -> bool:
        """
        Return the True if run completed False otherwise
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT is_completed FROM 'runs' WHERE run_id="+str(runId))

        rows = cur.fetchall()
        isCompleted = rows[0]['is_completed']
        
        self.closeDatabase(conn, cur)
        
        return isCompleted




    def getExperimentName(self, runId : int) -> str:
        """
        Return the name of the experiment
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT name FROM 'experiments' WHERE exp_id=(SELECT exp_id FROM 'runs' WHERE run_id="+str(runId)+")")

        rows = cur.fetchall()
        ExperimentName = rows[0]['name']
        
        self.closeDatabase(conn, cur)
        
        return ExperimentName




    def getExperimentNameLastId(self) -> str:
        """
        Return the name of the experiment of the last run_id
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT name FROM 'experiments' WHERE exp_id=(SELECT MAX(exp_id) FROM 'runs')")

        rows = cur.fetchall()
        ExperimentName = rows[0]['name']
        
        self.closeDatabase(conn, cur)
        
        return ExperimentName




    def getParameterData(self, runId : int, paramDependent : str) -> dict:

        conn, cur = self.openDatabase()
        
        ds =  qc.load_by_id(run_id=int(runId), conn=conn)
        d = ds.get_parameter_data(paramDependent)[paramDependent]

        self.closeDatabase(conn, cur)

        return d




# a = r"S:\132-PHELIQS\132.05-LATEQS\132.05.01-QuantumSilicon\edumur_test.db"
# # a = r"S:\132-PHELIQS\132.05-LATEQS\132.05.01-QuantumSilicon\experiments.db"
# q = QcodesDatabase()
# q.databasePath = a

# # d = q.getRunInfos(3)
# d = q.getParameterData(3, 'magnitude')

# print(q.getRunInfos2())

# print(qc.dataset.sqlite.queries.get_run_infos(q.conn))