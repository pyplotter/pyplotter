# This Python file uses the following encoding: utf-8
import time
import sqlite3
import json
import sys
import os
import qcodes as qc
from pprint import pformat
from typing import Callable


class QcodesDatabase:


    def __init__(self, setStatusBarMessage = Callable[[str, bool], None]):
        """
        Class to handle extraction of runs informations and runs data from qcodes
        database.
        """

        self.setStatusBarMessage = setStatusBarMessage


        super(QcodesDatabase).__init__()



    def closeDatabase(self):
        """
        Close the connection to the database.
        """
        
        self.conn.close()



    def connectDatabase(self, databasePath : str, signal=None) -> None:
        """
        Open connection to database using qcodes functions.

        Parameters
        ----------
        databasePath : str
            Path to the database file.
        signal
            Signal to be emitted if we can't open the database
        """
        
        try:
            self.databasePath = databasePath
            self.conn =  qc.dataset.sqlite.database.connect(self.databasePath)

            return True
        except Exception as e:
            fname = os.path.split(sys.exc_info()[2].tb_frame.f_code.co_filename)[1]
            nbLine = sys.exc_info()[2].tb_lineno
            exc_type = sys.exc_info()[0].__name__ 
            self.setStatusBarMessage("Can't open database file: "+str(exc_type)+", "+str(e)+". File "+str(fname)+", line"+str(nbLine), error=True)

            return False



    def getCursor(self) -> sqlite3.Cursor:
        """
        Try to open a cursor from existing database connection.
        Raise an error otherwise
        """

        try:
            cur = self.conn.cursor()
        except Exception as e:
            fname = os.path.split(sys.exc_info()[2].tb_frame.f_code.co_filename)[1]
            nbLine = sys.exc_info()[2].tb_lineno
            exc_type = sys.exc_info()[0].__name__ 
            self.setStatusBarMessage("Can't get cursor: "+str(exc_type)+", "+str(e)+". File "+str(fname)+", line"+str(nbLine), error=True)
            return


        return cur



    def timestamp2string(self, timestamp : int, fmt : str="%Y-%m-%d %H:%M:%S") -> str:
        """
        Returns timestamp in a human-readable format.
        """

        return time.strftime(fmt, time.localtime(timestamp))



    def getNdIndependentFromRow(self, row : sqlite3.Row) -> int:
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

        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])

        cur.close()

        return [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]



    def getListDependentFromRunId(self, runId : int) -> list:
        """
        Get the list of dependent parameter from a runId.

        Parameters
        ----------
        runId : int
            id of the run
        """

       
        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])

        cur.close()

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

       
        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])

        cur.close()
        
        
        return ([i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0],
                [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0])




    def getDatasetFromRunId(self, runId : int):
        """
        Get the dataset from a runId.

        Parameters
        ----------
        runId : int
            id of the run
        """

        try:
            a = qc.load_by_id(int(runId), self.conn)
        except:
            self.connectDatabase(self.databasePath)
            a = qc.load_by_id(int(runId), self.conn)

        return a




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

        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])

        cur.close()
        

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

        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT run_description, snapshot FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        snapshotDict = json.loads(row['snapshot'])

        cur.close()

        independent = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]
        dependent   = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]

        return independent, dependent, snapshotDict




    def getRunInfos(self) -> tuple:
        """
        Get a handfull of information about all the run of a database.
        """

        
        
        cur = self.getCursor()
        if cur is None:
            return 

        # Get runs infos
        cur.execute("SELECT run_id, exp_id, name, completed_timestamp, run_timestamp, result_table_name, run_description FROM 'runs'")

        runInfos = cur.fetchall()
        result_table_names = [row['result_table_name'] for row in runInfos]
        runIds = [str(row['run_id']) for row in runInfos]

        # Get runs records
        request = 'SELECT '
        for result_table_name, runId in zip(result_table_names, runIds):
            request += '(SELECT MAX(id) FROM "'+result_table_name+'") AS runId'+runId+','

        try:
            cur.execute(request[:-1])
            records = cur.fetchall()[0]
        
        # Sometimes this request doesn't work and doing the count one by one works
        except sqlite3.OperationalError:

            records = []
            for result_table_name, runId in zip(result_table_names, runIds):
                try:
                    request = 'SELECT MAX(id) FROM "'+result_table_name+'"'
                    cur.execute(request)
                    records.append(cur.fetchall()[0]['max(id)'])
                except sqlite3.OperationalError:
                    records.append('nan')



        # Get experiments Infos
        cur.execute("SELECT  exp_id, name, sample_name FROM 'experiments'")
        experimentInfos = cur.fetchall()
        
        cur.close()
        

        return runInfos, records, experimentInfos




    def getNbTotalRun(self) -> int:
        """
        Return the number of run in the currently opened database
        """
        
        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT MAX(run_id) FROM 'runs'")

        rows = cur.fetchall()
        nbTotalRun = rows[0]['max(run_id)']
        cur.close()
        

        return nbTotalRun




    def isRunCompleted(self, runId : int) -> bool:
        """
        Return the True if run completed False otherwise
        """
        
        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT is_completed FROM 'runs' WHERE run_id="+str(runId))

        rows = cur.fetchall()
        isCompleted = rows[0]['is_completed']
        cur.close()
        

        return isCompleted




    def getExperimentName(self, runId : int) -> str:
        """
        Return the name of the experiment
        """
        
        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT name FROM 'experiments' WHERE exp_id=(SELECT exp_id FROM 'runs' WHERE run_id="+str(runId)+")")

        rows = cur.fetchall()
        ExperimentName = rows[0]['name']
        cur.close()
        

        return ExperimentName




    def getExperimentNameLastId(self) -> str:
        """
        Return the name of the experiment of the last run_id
        """
        
        cur = self.getCursor()

        # Get runs infos
        cur.execute("SELECT name FROM 'experiments' WHERE exp_id=(SELECT MAX(exp_id) FROM 'runs')")

        rows = cur.fetchall()
        ExperimentName = rows[0]['name']
        cur.close()
        

        return ExperimentName




    def get_parameter_data(self, runId : int, paramDependent : str) -> dict:

        ds = self.getDatasetFromRunId(int(runId))

        try:
            d = ds.get_parameter_data(paramDependent)[paramDependent]
        except sqlite3.OperationalError:
            self.setStatusBarMessage("Can't load data: disk I/O error", error=True)
            d = None

        return d
            
# a = r"S:\132-PHELIQS\132.05-LATEQS\132.05.01-QuantumSilicon\edumur_test.db"
# q = QcodesDatabase()
# q.connectDatabase(a)

# print(q.getNbTotalRun())