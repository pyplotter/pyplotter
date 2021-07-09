# This Python file uses the following encoding: utf-8
import time
import sqlite3
import json
from qcodes.dataset import load_by_id
from qcodes.dataset.data_set import DataSet
from qcodes.dataset.sqlite.database import connect
from qcodes.dataset.sqlite.connection import ConnectionPlus
from typing import Callable, Tuple, List, Optional

from .config import config


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
        """

        Returns
        -------
        databasePath : str
            Path to the database file.
        """

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
                    progressBarKey    : str=None) -> Optional[dict]:
        """
        Get a handfull of information about all the run of a database.
        Return None if database is empty.
        
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
        
        # In case the database is empty, we return None
        if rows[0]['max(run_id)'] is None:
            self.progressBarUpdate.emit(self.progressBarKey, 100)
            return 
            
            
        if progressBarUpdate is None:
            callEvery = None
        else:
            # 25 is a magic number to get a progressBar close to 100%
            callEvery = int(rows[0]['max(run_id)']*25/100*config['displayedDownloadQcodesPercentage'])

        self.closeDatabase(conn, cur)
        # We download the run info while updating the progress bar
        conn, cur = self.openDatabase(callEvery=callEvery)


        ## Get runs infos
        cur.execute("SELECT run_id, exp_id, name, completed_timestamp, run_timestamp, result_table_name, run_description FROM 'runs'")
        runInfos = cur.fetchall()
        result_table_names = [row['result_table_name'] for row in runInfos]
        runIds = [str(row['run_id']) for row in runInfos]

        ## Get runs records
        # If there is more than maximumRunPerRequest runs in the database, we 
        # split the request in as many subrequests as necessary.
        # recors will then contains a list of sqlite3.Row object containing the
        # reply of each subrequest.
        records = []
        for slice in range(len(result_table_names)//config['maximumRunPerRequest']+1):
            request = 'SELECT '
            for result_table_name, runId in zip(result_table_names[slice*config['maximumRunPerRequest']:(slice+1)*config['maximumRunPerRequest']], runIds[slice*config['maximumRunPerRequest']:(slice+1)*config['maximumRunPerRequest']]):
                request += '(SELECT MAX(id) FROM "'+result_table_name+'") AS runId'+runId+','
            cur.execute(request[:-1])
            records.append(cur.fetchall()[0])


        ## Get experiments infos
        cur.execute("SELECT  exp_id, name, sample_name FROM 'experiments'")
        experimentInfos = cur.fetchall()
        self.closeDatabase(conn, cur)


        # Transform all previous sqlite3.Row object obtained previously into
        # a nice dict.
        # The dict is created be first going through all subrequests and then
        # through sqlite3.Row objects.
        infos = {}
        for slice in range(len(result_table_names)//config['maximumRunPerRequest']+1):
            for runInfo, runRecords in zip(runInfos[slice*config['maximumRunPerRequest']:(slice+1)*config['maximumRunPerRequest']], records[slice]):
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




    def load_by_id(self, runId: int) -> DataSet:
        
        # We download the data while updating the progress bar
        conn, cur = self.openDatabase()
        
        ds =  load_by_id(run_id=runId, conn=conn)

        
        conn.commit()
        # self.closeDatabase(conn, cur)

        return ds
