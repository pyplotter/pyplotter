# This Python file uses the following encoding: utf-8
import time
import sqlite3
import json
import numpy as np
from typing import Callable, Tuple, List, Optional
import multiprocess as mp

from .config import config


def timestamp2string(timestamp :int,
                     fmt :str="%Y-%m-%d %H:%M:%S") -> str:
    """
    Returns timestamp in a human-readable format.
    """

    return time.strftime(fmt, time.localtime(timestamp))



def openDatabase(databaseAbsPath: str,
                 returnDict: bool=False):
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

    conn =  sqlite3.connect(databaseAbsPath)

    if returnDict:
        conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    return conn, cur




def closeDatabase(conn,
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







def getParameterInfo(databaseAbsPath: str,
                     runId         : int,
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

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    # Get runs infos
    cur.execute("SELECT run_description FROM 'runs' WHERE run_id="+str(runId))
    row = cur.fetchall()[0]

    # Create nice dict object from a string
    d = json.loads(row['run_description'])
    closeDatabase(conn, cur)

    # Get parameter
    param = [i for i in d['interdependencies']['paramspecs'] if i['name']==parameterName][0]

    # Get its dependence
    l = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])==0]
    dependences = [j for i in param['depends_on'] for j in d['interdependencies']['paramspecs'] if j['name']==i]

    return param, dependences




def getParameterData(databaseAbsPath: str,
                     runId: int,
                     paramIndependentName: List[str],
                     paramDependentName: str,
                     queue_data: mp.Queue,
                     queue_progressBar: mp.Queue,
                     queue_done: mp.Queue) -> None:
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

    # In order to display a progress of the data loading, we need the
    # number of point downloaded. This requires the two following queries.
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT result_table_name, run_description FROM runs WHERE run_id="+str(runId))
    row = cur.fetchall()[0]

    table_name = row['result_table_name']
    nbParamDependent = len(json.loads(row['run_description'])['interdependencies_']['dependencies'])

    cur.execute("SELECT MAX(id) FROM '"+table_name+"'")
    rows = cur.fetchall()

    total = int(rows[0]['max(id)']/nbParamDependent)
    callEvery = int(total/100*config['displayedDownloadQcodesPercentage'])

    closeDatabase(conn, cur)

    if len(paramIndependentName)==1:
        request = 'SELECT {0},{1} FROM "{2}" WHERE {1} IS NOT NULL'.format(paramIndependentName[0],
                                                                           paramDependentName,
                                                                           table_name)
    elif len(paramIndependentName)==2:
        request = 'SELECT {0},{1},{2} FROM "{3}" WHERE {2} IS NOT NULL'.format(paramIndependentName[0],
                                                                               paramIndependentName[1],
                                                                               paramDependentName,
                                                                               table_name)

    # We download the data while updating the progress bar
    conn, cur = openDatabase(databaseAbsPath)
    d = np.empty((total, len(paramIndependentName)+1))
    ids = np.arange(0, total, callEvery)
    if ids[-1]!=total:
        ids = np.append(ids, total)
    iteration = 100/len(ids)
    for i in range(len(ids)-1):
        cur.execute('{0} LIMIT {1} OFFSET {2}'.format(request,
                                                      callEvery,
                                                      ids[i]))
        d[ids[i]:ids[i+1],] = np.array(cur.fetchall())

        queue_progressBar.put(queue_progressBar.get() + iteration)

    closeDatabase(conn, cur)

    queue_data.put(d)
    queue_done.put(True)



def getNbIndependentFromRow(row : sqlite3.Row) -> List[int]:
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




def getNbDependentFromRow(row : sqlite3.Row) -> int:
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






def getRunInfos(databaseAbsPath: str,
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

    # # Initialized progress bar
    # progressBarValue  = 0
    # progressBarUpdate = progressBarUpdate
    # progressBarKey    = progressBarKey


    # In order to display a progress of the info gathering, we need the
    # number of runs to be downloaded.
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)
    cur.execute("SELECT MAX(run_id) FROM runs")
    rows = cur.fetchall()

    # In case the database is empty, we return None
    if rows[0]['max(run_id)'] is None:
        # progressBarUpdate.emit(progressBarKey, 100)
        return None


    # if progressBarUpdate is None:
    #     callEvery = None
    # else:
    #     # 25 is a magic number to get a progressBar close to 100%
    #     callEvery = int(rows[0]['max(run_id)']*25/100*config['displayedDownloadQcodesPercentage'])

    closeDatabase(conn, cur)
    # We download the run info while updating the progress bar
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)#callEvery=callEvery)


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
    closeDatabase(conn, cur)


    # Transform all previous sqlite3.Row object obtained previously into
    # a nice dict.
    # The dict is created be first going through all subrequests and then
    # through sqlite3.Row objects.
    infos = {}
    for slice in range(len(result_table_names)//config['maximumRunPerRequest']+1):
        for runInfo, runRecords in zip(runInfos[slice*config['maximumRunPerRequest']:(slice+1)*config['maximumRunPerRequest']], records[slice]):
            infos[runInfo['run_id']] = {'nb_independent_parameter' : getNbIndependentFromRow(runInfo),
                                        'nb_dependent_parameter' : getNbDependentFromRow(runInfo),
                                        'experiment_name' : experimentInfos[runInfo['exp_id']-1]['name'],
                                        'sample_name' : experimentInfos[runInfo['exp_id']-1]['sample_name'],
                                        'run_name' : runInfo['name'],
                                        'started' : timestamp2string(runInfo['run_timestamp']),
                                        'completed' : timestamp2string(runInfo['completed_timestamp']),
                                        'records' : runRecords}


    return infos





def getDependentSnapshotFromRunId(databaseAbsPath: str,
                                  runId : int) -> Tuple[list, dict]:
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

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

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

    closeDatabase(conn, cur)

    dependents = [i for i in d['interdependencies']['paramspecs'] if len(i['depends_on'])!=0]

    return dependents, snapshotDict


