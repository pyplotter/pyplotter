# This Python file uses the following encoding: utf-8
import time
import sqlite3
import json
from qcodes.dataset import load_by_id
from qcodes.dataset.sqlite.database import connect
from qcodes.dataset.sqlite.connection import ConnectionPlus
from typing import Callable, Tuple, List

from sources.config import config


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




    def openDatabase(self, callEvery: int=None) -> None:
        """
        Open connection to database using qcodes functions.

        Parameters
        ----------
        callEvery : int, default None
            Number of virtual machine instructions between each callback.


        Return
        ------
        conn : Connection
            Connection to the db
        cur : Cursor
            Cursor to the db
        """
        
        conn =  connect(self.databasePath)

        # ProgressHandler will be called every "callevery"
        if callEvery is not None:
            conn.set_progress_handler(self.progressHandler, callEvery)

        cur = conn.cursor()

        return conn, cur




    def closeDatabase(self, conn : ConnectionPlus,
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
    #                           Progress bar
    #
    #
    ############################################################################



    def progressHandler(self) -> None:
        """
        Is called by sql queries.

        Increment progressBarValue and display the progress through a pyqt signal.
        """
        
        self.progressBarValue += config['displayedDownloadQcodesPercentage']
        self.progressBarUpdate.emit(self.progressBarKey, self.progressBarValue)



    ############################################################################
    #
    #
    #                           Queries
    #
    #
    ############################################################################



    def getNbIndependentFromRow(self, row : sqlite3.Row) -> List[int]:
        """
        Get the numbers of independent parameter from a row object of sqlite3.
        The row must come from a "runs" table.
        Since dependent parameters can have different number of independent
        parameters they depends on, return a list.

        Parameters
        ----------
        row : sqlite3.Row
            Row of a "runs" database
        """

        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        return list({len(i['depends_on']) for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0})




    def getNbDependentFromRow(self, row : sqlite3.Row) -> int:
        """
        Get the number of dependent parameter from a row object of sqlite3.
        The row must come from a "runs" table.

        Parameters
        ----------
        row : sqlite3.Row
            Row of a "runs" database
        """

        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        return len([i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0])




    def getExperimentSampleFromRow(self, rows : sqlite3.Row, exp_id : int) -> Tuple[str, str]:
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




    def getListIndependentFromRunId(self, runId : int) -> List[dict]:
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




    def getListDependentFromRunId(self, runId : int) -> List[dict]:
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




    def getListIndependentDependentFromRunId(self, runId : int) -> Tuple[list, list]:
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




    def getListParametersFromRunId(self, runId : int) -> Tuple[list, dict]:
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




    def getDependentSnapshotFromRunId(self, runId : int) -> Tuple[list, dict]:
        """
        Get the list of dependent parameters from a runId.
        Return a tuple of dependent parameters, each parameter
        being a dict.

        Parameters
        ----------
        runId : int
            id of the run.

        Return
        ------
        (dependent, snapshotDict) : tuple
            dependents : list
                list of dict of all dependents parameters.
            snapshotDict : dict
                Snapshot of the run.
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description, snapshot FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]

        # Create nice dict object from a string
        d = json.loads(row['run_description'])

        # If there is no station, the snapshot is None
        if row['snapshot'] is None:
            snapshotDict = {'': config['defaultSnapshot']}
        else:
            snapshotDict = json.loads(row['snapshot'])
        
        self.closeDatabase(conn, cur)

        dependents = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]

        return dependents, snapshotDict



    def getParameterInfo(self, runId         : int,
                               parameterName : str) -> Tuple[dict, List[dict]]:
        """
        Get the dependent qcodes parameter dictionary and all the independent
        parameters dictionary it depends on.

        Parameters
        ----------
        runId : int
            id of the run.
        parameterName : str
            Name of the dependent parameter.

        Return
        ------
        (dependentParameter, independentParameter) : Tuple
            dependentParameter : dict
                Qcodes dependent parameter dictionnary.
            independentParameter : List[dict]
                List of qcodes independent parameters dictionnary.
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        
        self.closeDatabase(conn, cur)

        # Get parameter
        param = [i for i in d['interdependencies']['paramspecs'] if i['name']==parameterName][0]

        # Get its dependence
        l = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]
        dependences = [j for i in param['depends_on'] for j in d['interdependencies']['paramspecs'] if j['name']==i]

        return param, dependences






    def getIndependentDependentSnapshotFromRunId(self, runId : int) -> Tuple[list, list, dict]:
        """
        Get the list of independent and dependent parameters from a runId.
        Return a tuple of independent and dependent parameters, each parameter
        being a dict.

        Parameters
        ----------
        runId : int
            id of the run.

        Return
        ------
        (independents, dependent, snapshotDict) : tuple
            independents : list
                list of dict of all independents parameters.
            dependents : list
                list of dict of all dependents parameters.
            snapshotDict : dict
                Snapshot of the run.
        """
        
        conn, cur = self.openDatabase()

        # Get runs infos
        cur.execute("SELECT run_description, snapshot FROM 'runs' WHERE run_id="+str(runId))
        row = cur.fetchall()[0]
        # Create nice dict object from a string
        d = json.loads(row['run_description'])
        snapshotDict = json.loads(row['snapshot'])
        
        self.closeDatabase(conn, cur)

        independents = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]
        dependents   = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]

        return independents, dependents, snapshotDict




    def getRunInfos(self,
                    progressBarUpdate : Callable[[int], None]=None,
                    progressBarKey    : str=None) -> dict:
        """
        Get a handfull of information about all the run of a database.

        Parameters
        ----------
        progressBarUpdate : func
            Pyqt signal to update the progress bar in the main thread 
        progressBarKey : str
            Key to the progress bar in the dict progressBars.
        """

        # Initialized progress bar
        self.progressBarValue  = 0
        self.progressBarUpdate = progressBarUpdate
        self.progressBarKey    = progressBarKey


        # In order to display a progress of the info gathering, we need the
        # number of runs to be downloaded.
        conn, cur = self.openDatabase()

        cur.execute("SELECT MAX(run_id) FROM runs")
        rows = cur.fetchall()
        
        if progressBarUpdate is None:
            
            callEvery = None
        else:

            callEvery = int(rows[0]['max(run_id)']/100*6*config['displayedDownloadQcodesPercentage'])

        self.closeDatabase(conn, cur)



        # We download the run info while updating the progress bar
        conn, cur = self.openDatabase(callEvery=callEvery)

        # Get runs infos
        cur.execute("SELECT run_id, exp_id, name, completed_timestamp, run_timestamp, result_table_name, run_description FROM 'runs'")

        runInfos = cur.fetchall()
        result_table_names = [row['result_table_name'] for row in runInfos]
        runIds = [str(row['run_id']) for row in runInfos]

        self.closeDatabase(conn, cur)

        # Initialize again the progress bar for the second query
        self.progressBarValue  = 0

        if progressBarUpdate is None:
            
            callEvery = None
        else:
            callEvery = int(len(result_table_names)/100*6*config['displayedDownloadQcodesPercentage'])


        # We download the number of records per run while updating the progress bar
        conn, cur = self.openDatabase(callEvery=callEvery)


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




    def getParameterData(self, runId             : int,
                               paramDependent    : str,
                               progressBarUpdate : Callable[[int], None]=None,
                               progressBarKey    : str=None) -> dict:
        """
        Return the data of paramDependent of the runId as a qcodes dict.

        Parameters
        ----------
        runId : int
            Run from which data are downloaded
        paramDependent : str
            Dependent parameter name to extract sub dict from main dict
        progressBarUpdate : func
            Pyqt signal to update the progress bar in the main thread 
        progressBarKey : str
            Key to the progress bar in the dict progressBars.
        """

        # Initialized progress bar
        self.progressBarValue  = 0
        self.progressBarKey    = progressBarKey
        self.progressBarUpdate = progressBarUpdate

        # In order to display a progress of the data loading, we need the
        # number of point downloaded. This requires the two following queries.
        conn, cur = self.openDatabase()

        cur.execute("SELECT result_table_name FROM runs WHERE run_id="+str(runId))

        rows = cur.fetchall()
        table_name = rows[0]['result_table_name']

        cur.execute("SELECT MAX(id) FROM '"+table_name+"'")
        rows = cur.fetchall()
        
        if progressBarUpdate is None:
            
            callEvery = None
        else:
            # In case of a live plot, total may be None
            # In that case we return 0
            total = rows[0]['max(id)']
            if total is None:
                callEvery = 0
            else:
                callEvery = int(total/100*6*config['displayedDownloadQcodesPercentage'])
        
        self.closeDatabase(conn, cur)

        # We download the data while updating the progress bar
        conn, cur = self.openDatabase(callEvery=callEvery)
        
        ds =  load_by_id(run_id=int(runId), conn=conn)

        try:
            d = ds.get_parameter_data(paramDependent)[paramDependent]
        except sqlite3.OperationalError:
            d = None

        self.closeDatabase(conn, cur)

        return d




# # a = r"S:\132-PHELIQS\132.05-LATEQS\132.05.01-QuantumSilicon\edumur_test.db"
# a = r"S:\132-PHELIQS\132.05-LATEQS\132.05.01-QuantumSilicon\bluelagoon\2020\20200623_20200226_NbN01_A1\data\experiments.db"
# # a = r"S:\132-PHELIQS\132.05-LATEQS\132.05.01-QuantumSilicon\experiments.db"
# q = QcodesDatabase()
# q.databasePath = a

# # d = q.getRunInfos(3)
# # d = q.getIndependentDependentSnapshotFromRunId(3)
# d = q.getParameterData(103, 'vna1_TR1_Magnitude')

# # print(q.getRunInfos2())

# # print(qc.dataset.sqlite.queries.get_run_infos(q.conn))