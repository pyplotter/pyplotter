# This Python file uses the following encoding: utf-8
import io
import time
import sqlite3
import json
import numpy as np
from typing import Tuple, List, Union, Optional
import multiprocess as mp
try:
    from importlib.metadata import version
except ImportError: # for Python<3.8
    from importlib_metadata import version

from .config import loadConfigCurrent
config = loadConfigCurrent()


def timestamp2string(timestamp :int,
                     fmt :str="%Y-%m-%d %H:%M:%S") -> str:
    """
    Returns timestamp in a human-readable format.
    """

    return time.strftime(fmt, time.localtime(timestamp))



def timestamps2duration(timestamp_after: Optional[int],
                        timestamp_before: Optional[int]) -> str:
    """
    Returns duration between two timestamps in a human-readable format.
    """

    if timestamp_before is None or timestamp_after is None:
        return ''

    s = timestamp_after - timestamp_before
    hours, remainder = divmod(s, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours!=0:
        return '<span style="color:{};">{:02.0f}h</span>'\
               '<span style="color:{};">{:02.0f}m</span>'\
               '<span style="color:{};">{:02.0f}s</span>'\
               '<span style="color:{};">{:03.0f}ms</span>'.format(config['styles'][config['style']]['tableWidgetDatabaseDuration']['hour'],
                                                                  hours,
                                                                  config['styles'][config['style']]['tableWidgetDatabaseDuration']['minute'],
                                                                  minutes,
                                                                  config['styles'][config['style']]['tableWidgetDatabaseDuration']['second'],
                                                                  seconds,
                                                                  config['styles'][config['style']]['tableWidgetDatabaseDuration']['millisecond'],
                                                                  (seconds-int(seconds))*1000)
    elif minutes!=0:
        return '<span style="color:{};">{:02.0f}m</span>'\
               '<span style="color:{};">{:02.0f}s</span>'\
               '<span style="color:{};">{:03.0f}ms</span>'.format(config['styles'][config['style']]['tableWidgetDatabaseDuration']['minute'],
                                                                  minutes,
                                                                  config['styles'][config['style']]['tableWidgetDatabaseDuration']['second'],
                                                                  seconds,
                                                                  config['styles'][config['style']]['tableWidgetDatabaseDuration']['millisecond'],
                                                                  (seconds-int(seconds))*1000)
    elif seconds!=0:
        return '<span style="color:{};">{:02.0f}s</span>'\
               '<span style="color:{};">{:03.0f}ms</span>'.format(config['styles'][config['style']]['tableWidgetDatabaseDuration']['second'],
                                                                  seconds,
                                                                  config['styles'][config['style']]['tableWidgetDatabaseDuration']['millisecond'],
                                                                  (seconds-int(seconds))*1000)
    else:
        return '<span style="color:{};">{:03.0f}ms</span>'.format(config['styles'][config['style']]['tableWidgetDatabaseDuration']['millisecond'],
                                                                  (seconds-int(seconds))*1000)



def openDatabase(databaseAbsPath: str,
                 returnDict: bool=False) -> Tuple[sqlite3.Connection,
                                                  sqlite3.Cursor]:
    """
    Open connection to database using qcodes functions.

    Args:
        databaseAbsPath: Absolute path of the current database
        returnDict: If true, used row_factory = sqlite3.Row
            Defaults to False.

    Returns:
        conn: Connection to the db
        cur: Cursor to the db
    """

    conn =  sqlite3.connect(databaseAbsPath)

    if returnDict:
        conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    return conn, cur



def closeDatabase(conn: sqlite3.Connection,
                  cur: sqlite3.Cursor) -> None:
    """
    Close the connection to the database.

    Args:
        conn: Connection to the db
        cur: Cursor to the db
    """

    cur.close()
    conn.close()



def getParameterInfo(databaseAbsPath: str,
                     runId: int,
                     parameterName: str) -> Tuple[dict, List[dict]]:
    """
    Get the dependent qcodes parameter dictionary and all the independent
    parameters dictionary it depends on.

    Parameters
    ----------
    databaseAbsPath: str
        Absolute path of the current database
    runId: int
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



def getNbIndependentFromRow(row : Union[dict, sqlite3.Row]) -> List[int]:
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



def getNbDependentFromRow(row : Union[dict, sqlite3.Row]) -> int:
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



def getDependentSnapshotFromRunId(databaseAbsPath: str,
                                  runId: int) -> Tuple[list, dict]:
    """
    Get the list of dependent parameters from a runId.
    Return a tuple of dependent parameters, each parameter
    being a dict.

    Parameters
    ----------
    runId: int
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



def getNbTotalRun(databaseAbsPath: str) -> int:
    """
    Return the number of run in the database
    """

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT MAX(run_id) FROM 'runs'")

    rows = cur.fetchall()
    nbTotalRun = rows[0]['max(run_id)']

    closeDatabase(conn, cur)

    return nbTotalRun



def getRunName(databaseAbsPath: str,
               runId: int) -> str:
    """
    Return the name of the run
    """

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT name FROM 'runs' WHERE run_id="+str(runId)+")")

    rows = cur.fetchall()
    runName = rows[0]['name']

    closeDatabase(conn, cur)

    return runName



def getNbTotalRunAndLastRunName(databaseAbsPath: str) -> Tuple[int, str]:
    """
    Return the number of run in the database and the name of the last run
    """

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT MAX(run_id) FROM 'runs'")

    rows = cur.fetchall()
    nbTotalRun = rows[0]['max(run_id)']
    cur.execute("SELECT name FROM 'runs' WHERE run_id='{}'".format(nbTotalRun))

    rows = cur.fetchall()
    runName = rows[0]['name']

    closeDatabase(conn, cur)

    return nbTotalRun, runName



def isRunCompleted(databaseAbsPath: str,
                   runId: int) -> bool:
    """
    Return True if the run is marked as completed, False otherwise
    """

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT is_completed FROM 'runs' WHERE run_id="+str(runId))

    rows = cur.fetchall()
    isCompleted = rows[0]['is_completed']

    closeDatabase(conn, cur)

    return isCompleted



###########################################################################
#
#
#                           Function not returning anything
#                           but placing them in mutiprocessing queue
#
#
###########################################################################



def getParameterDbRow(databaseAbsPath: str,
                      table_name: str,
                      param_name: str) -> int:
    """
    Get the total number of not-null values of a parameter

    Args:
        conn: Connection to the database
        table_name: Name of the table that holds the data
        param_name: Name of the parameter to get the setpoints of

    Returns:
        The total number of not-null values
    """
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)
    sql = f"""
           SELECT COUNT({param_name}) FROM "{table_name}"
           WHERE {param_name} IS NOT NULL
           """
    cur.execute(sql)
    rows = cur.fetchall()
    closeDatabase(conn, cur)

    return rows[0][f'COUT({param_name})']



def getTableMaxId(databaseAbsPath: str,
                     table_name: str) -> int:
    """
    Get the max id of a table

    Args:
        databaseAbsPath: database absolute path
        table_name: Name of the table that holds the data

    Returns:
        The max id of a table
    """
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)
    sql = f"""
           SELECT MAX(run_id)
           FROM "{table_name}"
           """
    cur.execute(sql)
    rows = cur.fetchall()

    return rows[0]['max(run_id)']



def getOffsetLimitForCallback(databaseAbsPath: str,
                              table_name: str,
                              param_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Since sqlite3 does not allow to keep track of the data loading progress,
    we compute how many sqlite request correspond to a progress of
    config['displayedDownloadQcodesPercentage'].
    This function return a list of offset and a integer value of limit to
    be used to run such SQL requests.

    Args:
        conn: Connection to the database
        table_name: Name of the table that holds the data
        param_name: Name of the parameter to get the setpoints of

    Returns:
        offset: list of SQL offset corresponding to a progress of
            config['displayedDownloadQcodesPercentage']
        limit: SQL limit corresponding to a progress of
            config['displayedDownloadQcodesPercentage']
    """

    # First, we get the number of row to be downloaded for the wanted
    # dependent parameter
    nb_row = getParameterDbRow(databaseAbsPath,
                               table_name,
                               param_name)

    # Second, we get the max id of the table
    max_id = getTableMaxId(databaseAbsPath,
                           table_name)

    # Third, we create a list of offset corresponding to a progress of
    # config['displayedDownloadQcodesPercentage']
    if nb_row >= 100:

        # Using linspace with dtype=int ensure of having an array finishing
        # by max_id
        offset = np.linspace(0, max_id, int(100 / config['displayedDownloadQcodesPercentage']) + 1, dtype=int)

    else:
        # If there is less than 100 row to be downloaded, we overwrite the
        # config['displayedDownloadQcodesPercentage'] to avoid many calls for small download
        offset = np.array([0, nb_row // 2, nb_row])

    # The number of row downloaded between two iterations may vary
    # We compute the limit corresponding to each offset
    limit = offset[1:] - offset[:-1]

    return offset, limit




def getRunInfosmp(databaseAbsPath: str,
                  queueData: mp.Queue,
                  queueProgressBar: mp.Queue,
                  queueDone: mp.Queue) -> None:
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
    # start = time.time()
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)
    cur.execute("SELECT MAX(run_id) FROM runs")
    rows = cur.fetchall()

    # stop = time.time()
    # print(stop-start)
    # start = time.time()
    # If empty database
    if rows[0]['max(run_id)'] is None:
        queueData.put(None)
        queueDone.put(True)
        return None

    total = int(rows[0]['max(run_id)'])
    callEvery = int(total/100*config['displayedDownloadQcodesPercentage'])

    # For small database
    if callEvery==0:
        callEvery = total

    ## Get runs infos
    request = "SELECT run_id, exp_id, name, completed_timestamp, run_timestamp, result_table_name, run_description FROM 'runs'"
    runInfos: List[dict] = [{}]*total
    ids = np.arange(0, total, callEvery)
    if ids[-1]!=total:
        ids = np.append(ids, total)
    iteration = 100/len(ids)
    for i in range(len(ids)-1):
        cur.execute('{0} LIMIT {1} OFFSET {2}'.format(request,
                                                      callEvery,
                                                      ids[i]))

        runInfos[ids[i]:ids[i+1]] = list(cur.fetchall())

        queueProgressBar.put(queueProgressBar.get() + iteration)


    # stop = time.time()
    # print(stop-start)
    # start = time.time()
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


    # stop = time.time()
    # print(stop-start)
    # start = time.time()

    ## Get experiments infos
    cur.execute("SELECT  exp_id, name, sample_name FROM 'experiments'")
    experimentInfos = cur.fetchall()
    closeDatabase(conn, cur)


    # stop = time.time()
    # print(stop-start)
    # start = time.time()

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
                                        'duration'  : timestamps2duration(runInfo['completed_timestamp'], runInfo['run_timestamp']),
                                        'records' : runRecords}


    # stop = time.time()
    # print(stop-start)
    # start = time.time()
    queueData.put(infos)
    queueDone.put(True)



def getParameterDatamp(databaseAbsPath: str,
                       runId: int,
                       paramIndependentName: List[str],
                       paramDependentName: str,
                       queueData: mp.Queue,
                       queueProgressBar: mp.Queue,
                       queueMessage: mp.Queue,
                       queueDone: mp.Queue) -> None:
    """
    Return the data of paramDependent of the runId as a qcodes dict.

    Parameters
    ----------
    databaseAbsPath
        Absolute path of the current database
    runId
        Run from which data are downloaded
    paramIndependentName
        Independent parameter name
    paramDependentName
        Dependent parameter name
    queueData
        Queue containing the numpy array of the run data
    queueProgressBar
        Queue containing a float from 0 to 100 for the progress bar
    queueMessage
        Queue containing a string to be displayed on the statusbar
    queueDone
        Queue containing 1 when the download is done
    """

    # In order to display a progress of the data loading, we need the
    # number of point downloaded. This requires the two following queries.
    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT result_table_name, run_description FROM runs WHERE run_id="+str(runId))
    row = cur.fetchall()[0]

    table_name = row['result_table_name']
    temp = json.loads(row['run_description'])
    if 'interdependencies_' in temp.keys():
        nbParamDependent = len(temp['interdependencies_']['dependencies'])
    else:
        nbParamDependent = len([i for i in temp['interdependencies']['paramspecs'] if i['name']==paramDependentName][0]['depends_on'])

    cur.execute("SELECT MAX(id) FROM '"+table_name+"'")
    rows = cur.fetchall()
    maxId = rows[0]['max(id)']

    if maxId is None:
        queueData.put(None)
        queueDone.put(True)
        return

    nbPoint = int(maxId/nbParamDependent)
    callEvery = int(nbPoint/100*config['displayedDownloadQcodesPercentage'])

    closeDatabase(conn, cur)

    # Depending if we are downloading 1d or 2d data
    # for 1d
    if len(paramIndependentName)==1:
        request = 'SELECT {0},{1} FROM "{2}" WHERE {1} IS NOT NULL'.format(paramIndependentName[0],
                                                                           paramDependentName,
                                                                           table_name)
    # for 2d
    elif len(paramIndependentName)==2:
        request = 'SELECT {0},{1},{2} FROM "{3}" WHERE {2} IS NOT NULL'.format(paramIndependentName[0],
                                                                               paramIndependentName[1],
                                                                               paramDependentName,
                                                                               table_name)

    # First, we try to download the data ourself
    try:
        conn, cur = openDatabase(databaseAbsPath)
        # For small run, we download all at once
        if nbPoint<=100:
            cur.execute(request)
            d = np.array(cur.fetchall())

            queueProgressBar.put(queueProgressBar.get() + 100)
        else:
            # We download the data while updating the progress bar
            # First, we compute the id limits to download the data in
            # 100/config['displayedDownloadQcodesPercentage'] request
            d = np.empty((nbPoint, len(paramIndependentName)+1))
            ids = np.arange(0, nbPoint, callEvery)
            if ids[-1]!=nbPoint:
                ids = np.append(ids, nbPoint)
            iteration = 100/len(ids)
            for i in range(len(ids)-1):
                cur.execute('{0} LIMIT {1} OFFSET {2}'.format(request,
                                                            callEvery,
                                                            ids[i]))
                d[ids[i]:ids[i+1],] = np.array(cur.fetchall())

                queueProgressBar.put(queueProgressBar.get() + iteration)

        queueProgressBar.get()
        queueProgressBar.put(100)

        closeDatabase(conn, cur)

        # We do not handle bytes data yet
        if isinstance(d[0][0], np.bytes_):

            queueProgressBar.get()
            queueProgressBar.put(0)
            queueMessage.get()
            queueMessage.put('Binary data detected, give me time here...')

            # We transform the binary data to float
            for i in range(d.shape[1]):
                out = io.BytesIO(d[0][i])
                out.seek(0)
                if i==0:
                    t = np.load(out)
                else:
                    t = np.vstack((t, np.load(out))).T
            d = t
            queueProgressBar.get()
            queueProgressBar.put(100)
    # If error, we load qcodes (slow)
    except:
        # If the callack argument is available on qcodes
        if int(version('qcodes').split('.')[1])>=36:
            def callback(progress):
                queueProgressBar.get()
                queueProgressBar.put(progress)
                return callback

            from qcodes import initialise_or_create_database_at, load_by_id
            initialise_or_create_database_at(databaseAbsPath)
            ds = load_by_id(runId).get_parameter_data(paramDependentName,
                                                      callback=callback)[paramDependentName]

            # for empty dataset
            if len(ds)==0:
                d = np.array([])
            # for 1d
            elif len(paramIndependentName)==1:
                d = np.vstack((np.ravel(ds[paramIndependentName[0]]),
                               np.ravel(ds[paramDependentName]))).T
            # for 2d
            elif len(paramIndependentName)==2:
                d = np.vstack((np.ravel(ds[paramIndependentName[0]]),
                               np.ravel(ds[paramIndependentName[1]]),
                               np.ravel(ds[paramDependentName]))).T
        else:
            queueProgressBar.get()
            queueProgressBar.put(0)
            queueMessage.get()
            queueMessage.put('Format not handled, have to load QCoDeS...')

            from qcodes import initialise_or_create_database_at, load_by_id
            initialise_or_create_database_at(databaseAbsPath)

            queueProgressBar.get()
            queueProgressBar.put(50)
            ds = load_by_id(runId).get_parameter_data()[paramDependentName]

            # for empty dataset
            if len(ds)==0:
                d = np.array([])
            # for 1d
            elif len(paramIndependentName)==1:
                d = np.vstack((np.ravel(ds[paramIndependentName[0]]),
                               np.ravel(ds[paramDependentName]))).T
            # for 2d
            elif len(paramIndependentName)==2:
                d = np.vstack((np.ravel(ds[paramIndependentName[0]]),
                               np.ravel(ds[paramIndependentName[1]]),
                               np.ravel(ds[paramDependentName]))).T
            queueProgressBar.get()
            queueProgressBar.put(100)


    queueData.put(d)
    queueDone.put(True)



def getNbTotalRunmp(databaseAbsPath: str,
                    queueNbRun: mp.Queue) -> None:
    """
    Return the number of run in the database
    """

    conn, cur = openDatabase(databaseAbsPath,
                             returnDict=True)

    cur.execute("SELECT MAX(run_id) FROM 'runs'")

    rows = cur.fetchall()
    nbTotalRun = rows[0]['max(run_id)']

    closeDatabase(conn, cur)

    queueNbRun.put(nbTotalRun)
