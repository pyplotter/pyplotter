from PyQt5 import QtCore

from ..config import loadConfigCurrent

config = loadConfigCurrent()
from .. import labrad_datavault

dataType = "Labrad"
from typing import Dict, Tuple, List, Union, Optional


def getDependentSnapshotShapeFromRunId(
    databaseAbsPath: str, runId: int
) -> Tuple[list, dict, dict]:
    dv = labrad_datavault.switch_session_path(databaseAbsPath)
    data = dv.openDataset(runId)
    dependents = data.getDependents()
    independents = data.getIndependents()
    dependentList = []
    for dep in dependents:
        dependentList.append(
            {
                "name": labrad_datavault.dep_name(dep),
                "paramtype": dep.datatype,
                "label": labrad_datavault.dep_name(dep),
                "unit": dep.unit,
                "inferred_from": [],
                "depends_on": [indep.label for indep in independents],
            }
        )
    snapshotDict = data.getParamDict()
    shapesDict = {}
    for dep in dependents:
        shapesDict[labrad_datavault.dep_name(dep)] = [tuple(ind.shape) for ind in independents]
    return dependentList, snapshotDict, shapesDict


class LoadRunInfoSignal(QtCore.QObject):
    """
    Class containing the signal of the loadRunInfoThread, see below
    """

    # When the run method is done
    updateRunInfo = QtCore.pyqtSignal(int, list, dict, dict, str, str, str, str, bool)


class LoadRunInfoThread(QtCore.QRunnable):

    def __init__(
        self,
        databaseAbsPath: str,
        runId: int,
        experimentName: str,
        runName: str,
        doubleClicked: bool,
    ):
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
        self.runId = runId
        self.experimentName = experimentName
        self.runName = runName
        self.doubleClicked = doubleClicked

    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        """

        (dependentList, snapshotDict, shapesDict) = getDependentSnapshotShapeFromRunId(
            self.databaseAbsPath, self.runId
        )
        self.signal.updateRunInfo.emit(
            self.runId,
            dependentList,
            snapshotDict,
            shapesDict,
            self.experimentName,
            self.runName,
            self.databaseAbsPath,
            dataType,
            self.doubleClicked,
        )
