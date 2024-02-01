from PyQt5 import QtCore
import multiprocess as mp

from ..config import loadConfigCurrent
config = loadConfigCurrent()
from ..qcodesDatabase import getRunInfosmp

class LoadDataBaseSignal(QtCore.QObject):
    """
    Class containing the signal of the loadDataBaseThread, see below
    """

    # Signal used to update the status bar
    sendStatusBarMessage = QtCore.pyqtSignal(str, str)
    # Signal used to add n rows in the database table
    addRows = QtCore.pyqtSignal(list, list, list, list, list, list, list, list, list, list, list, int, str)
    # Signal used to update the progress bar
    updateProgressBar = QtCore.pyqtSignal(int, float, str)
    # When the run method is done
    databaseClickDone = QtCore.pyqtSignal(int, bool, str, int)

class LoadDataBaseThread(QtCore.QRunnable):


    def __init__(self, databaseAbsPath:str,
                       progressBarId: int):
        """

        Parameters
        ----------
        databaseAbsPath : str
            Absolute path of the current database
        progressBarId : str
            Key to the progress bar in the dict progressBars
        """

        super(LoadDataBaseThread, self).__init__()

        self.signal = LoadDataBaseSignal()


        self.databaseAbsPath = databaseAbsPath
        self.progressBarId     = progressBarId

        # If set to True, stop the run
        self._stop = False



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        Go through the runs and send a signal for each new entry.
        Each signal is catch by the main thread to add a line in the database
        table displaying all the info of each run.
        """

        self.signal.sendStatusBarMessage.emit('Gathering runs informations', 'orange')

        # Queue will contain the numpy array of the run data
        queueData: mp.Queue = mp.Queue()
        # Queue will contain a float from 0 to 100 for the progress bar
        queueProgressBar: mp.Queue = mp.Queue()
        queueProgressBar.put(0)
        # Queue will contain 1 when the download is done
        queueDone: mp.Queue = mp.Queue()
        queueDone.put(False)

        self.worker = mp.Process(target=getRunInfosmp,
                                 args=(self.databaseAbsPath,
                                       queueData,
                                       queueProgressBar,
                                       queueDone))
        self.worker.start()

        # Here, we loop until the data transfer is done.
        # In each loop, we check the transfer progression and update the progress
        # bar
        done = False
        while not done:
            QtCore.QThread.msleep(config['delayBetweenProgressBarUpdate'])

            # We check if the thread ias being stopped
            if self._stop:
                return

            progressBar = queueProgressBar.get()
            queueProgressBar.put(progressBar)

            self.signal.updateProgressBar.emit(self.progressBarId, progressBar, 'Loading database: {:.0f}%'.format(progressBar))

            done = queueDone.get()
            queueDone.put(done)

        runInfos: dict = queueData.get()
        queueData.close()
        queueData.join_thread()
        queueProgressBar.close()
        queueProgressBar.join_thread()
        queueDone.close()
        queueDone.join_thread()

        self.worker.join()

        # We check if the thread ias being stopped
        if self._stop:
            return


        # If database is empty
        if runInfos is None:
            self.signal.sendStatusBarMessage.emit('Database empty', 'red')
            QtCore.QThread.msleep(1000) # To let user see the error message
            self.signal.databaseClickDone.emit(self.progressBarId, # progressBar
                                               True, #error
                                               '', # databaseAbsPath
                                               0) #nbTotalRun
            return

        # Going through the database here
        self.signal.sendStatusBarMessage.emit('Loading database', 'orange')
        nbTotalRun = len(runInfos)


        # We go through the runs info and build list to be transferred to the main
        # thread. Every config['NbRunEmit'] a signal is emitted and the list are
        # empty and the process starts again until all info have been stransferred.
        runId           = []
        dim             = []
        experimentName  = []
        sampleName      = []
        runName         = []
        captured_run_id = []
        guid            = []
        started         = []
        completed       = []
        duration        = []
        runRecords      = []
        for key, val in runInfos.items():

            runId.append(key)
            dim.append('-'.join(str(i) for i in val['nb_independent_parameter'])+'d')
            experimentName.append(val['experiment_name'])
            sampleName.append(val['sample_name'])
            runName.append(val['run_name'])
            captured_run_id.append(val['captured_run_id'])
            guid.append(val['guid'])
            started.append(val['started'])
            completed.append(val['completed'])
            duration.append(val['duration'])
            runRecords.append(str(val['records']))

            # If we reach enough data, we emit the signal.
            if key%config['NbRunEmit']==0:
                self.signal.addRows.emit(runId,
                                          dim,
                                          experimentName,
                                          sampleName,
                                          runName,
                                          captured_run_id,
                                          guid,
                                          started,
                                          completed,
                                          duration,
                                          runRecords,
                                          nbTotalRun,
                                          self.databaseAbsPath)
                self.signal.updateProgressBar.emit(self.progressBarId, runId[0]/nbTotalRun*100, 'Displaying database: run '+str(runId[0])+'/'+str(nbTotalRun))


                runId           = []
                dim             = []
                experimentName  = []
                sampleName      = []
                runName         = []
                captured_run_id = []
                guid            = []
                started         = []
                completed       = []
                duration        = []
                runRecords      = []

        # If there is still information to be transferred, we do so
        if len(runId)!=0:
            self.signal.addRows.emit(runId,
                                      dim,
                                      experimentName,
                                      sampleName,
                                      runName,
                                      captured_run_id,
                                      guid,
                                      started,
                                      completed,
                                      duration,
                                      runRecords,
                                      nbTotalRun,
                                      self.databaseAbsPath)
            self.signal.updateProgressBar.emit(self.progressBarId, runId[0]/nbTotalRun*100, 'Displaying database: run '+str(runId[0])+'/'+str(nbTotalRun))

        # Signal that the whole database has been looked at
        self.signal.databaseClickDone.emit(self.progressBarId, # progressBarId
                                           False, #error
                                           self.databaseAbsPath, # databaseAbsPath
                                           nbTotalRun) #nbTotalRun
