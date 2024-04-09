from PyQt5 import QtCore, QtTest
import multiprocess as mp

from .. import labrad_datavault


def getNbTotalRunmp(databaseAbsPath: str, queueNbRun: mp.Queue) -> None:
    dv = labrad_datavault.switch_session_path(databaseAbsPath)
    nbTotalRun = len(dv.listDatasets())
    queueNbRun.put(nbTotalRun)


class dataBaseCheckNbRunSignal(QtCore.QObject):
    """
    Class containing the signal of the dataBaseCheckNbRunThread, see below
    """

    # When the main gui has to update the database
    dataBaseUpdate = QtCore.pyqtSignal(str)

    # When the nb of run didn't change
    dataBaseCheckNbRun = QtCore.pyqtSignal(str, int)

    addStatusBarMessage = QtCore.pyqtSignal(str, str)


class dataBaseCheckNbRunThread(QtCore.QRunnable):

    def __init__(self, databaseAbsPath: str, nbTotalRun: int) -> None:
        """

        Parameters
        ----------
        databaseAbsPath : str
            Absolute path of the current database
        nbTotalRun : int
            Total number of run in the current database.
        """

        super(dataBaseCheckNbRunThread, self).__init__()

        self.databaseAbsPath = databaseAbsPath
        self.nbTotalRun = nbTotalRun

        self.signal = dataBaseCheckNbRunSignal()

        self._stop = False

    @QtCore.pyqtSlot()
    def run(self):

        QtCore.QThread.msleep(1000)

        # We check if the thread ias being stopped
        if self._stop:
            return
        # Queue will contain the nb of run in the database
        queueNbRun: mp.Queue = mp.Queue()

        self.worker = mp.Process(target=getNbTotalRunmp, args=(self.databaseAbsPath, queueNbRun))
        self.worker.start()

        nbTotalRun: int = queueNbRun.get()

        queueNbRun.close()
        queueNbRun.join_thread()

        self.worker.join()

        # We check if the thread ias being stopped
        if self._stop:
            return

        if self.nbTotalRun < nbTotalRun:
            print("current nbTotalRun", nbTotalRun, "previous", self.nbTotalRun)
            self.signal.addStatusBarMessage.emit(" (New run detected)", "orange")
            QtCore.QThread.msleep(500)
            self.signal.dataBaseUpdate.emit(self.databaseAbsPath)
        else:
            self.signal.addStatusBarMessage.emit(" (No run detected)", "black")
            QtCore.QThread.msleep(500)
            # In any case, we rerun the thread
            self.signal.dataBaseCheckNbRun.emit(self.databaseAbsPath, nbTotalRun)
