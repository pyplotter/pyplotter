# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore

from ..config import loadConfigCurrent
config = loadConfigCurrent()
from ..qcodesdatabase import getDependentSnapshotFromRunId


class LoadRunInfoSignal(QtCore.QObject):
    """
    Class containing the signal of the loadRunInfoThread, see below
    """

    # When the run method is done
    updateRunInfo = QtCore.pyqtSignal(int, list, dict, str, str, str, bool)

class LoadRunInfoThread(QtCore.QRunnable):



    def __init__(self, databaseAbsPath: str,
                       runId: int,
                       experimentName: str,
                       runName: str,
                       doubleClicked: bool):
        """
        Thread used to get all the run info of a database.

        Parameters
        ----------
        databaseAbsPath : str
            Absolute path of the current database
        runId : int
            Id of the current run
        experimentName : str
            Name of the current experiment
        runName : str
            Name of the current run
        """

        super(LoadRunInfoThread, self).__init__()

        self.signal = LoadRunInfoSignal()

        self.databaseAbsPath = databaseAbsPath
        self.runId           = runId
        self.experimentName  = experimentName
        self.runName         = runName
        self.doubleClicked   = doubleClicked



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        """

        dependentList, snapshotDict = getDependentSnapshotFromRunId(self.databaseAbsPath,
                                                                    self.runId)

        self.signal.updateRunInfo.emit(self.runId,
                                       dependentList,
                                       snapshotDict,
                                       self.experimentName,
                                       self.runName,
                                       self.databaseAbsPath,
                                       self.doubleClicked)
