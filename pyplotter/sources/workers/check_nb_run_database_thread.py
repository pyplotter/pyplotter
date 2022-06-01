# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtTest
import multiprocess as mp

from ..config import loadConfigCurrent
config = loadConfigCurrent()
from ..qcodesdatabase import getNbTotalRunmp

class dataBaseCheckNbRunSignal(QtCore.QObject):
    """
    Class containing the signal of the dataBaseCheckNbRunThread, see below
    """

    # When the main gui has to update the database
    dataBaseUpdate     = QtCore.pyqtSignal(str)

    # When the nb of run didn't change
    dataBaseCheckNbRun = QtCore.pyqtSignal()




class dataBaseCheckNbRunThread(QtCore.QRunnable):


    def __init__(self, databaseAbsPath:str,
                       nbTotalRun: int) -> None:
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
        self.nbTotalRun      = nbTotalRun

        self.signals = dataBaseCheckNbRunSignal()



    @QtCore.pyqtSlot()
    def run(self):

        QtTest.QTest.qWait(config['delayBetweendataBaseNbRunCheck'])

        # Queue will contain the nb of run in the database
        queueNbRun: mp.Queue = mp.Queue()

        self.worker = mp.Process(target=getNbTotalRunmp,
                                 args=(self.databaseAbsPath,
                                       queueNbRun))
        self.worker.start()


        nbTotalRun: int = queueNbRun.get()

        queueNbRun.close()
        queueNbRun.join_thread()

        if self.nbTotalRun<nbTotalRun:
            self.signals.dataBaseUpdate.emit(self.databaseAbsPath)
        else:
            self.signals.dataBaseCheckNbRun.emit()



