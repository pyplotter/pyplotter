import os
import numpy as np
import multiprocess as mp
import copy
import labrad
from typing import Tuple, List  # , Dict,  Union, Optional, final

CXN = labrad.connect()
# you might want to specify the correct labrad host and password


def name2idx(variables, name, default=np.nan):
    name = name if isinstance(name, list) else [name]
    names = [variable_i["name"] for variable_i in variables]
    for _name in name:
        if _name in names:
            return names.index(_name)
    else:
        return default


class DataLab(object):
    "wrapper for labrad data"

    def __init__(self, session=None, dv=None, dv_type="data_vault"):
        self.dv = dv
        self._ctx = self.dv.context()
        try:
            self.session = self.dv.cd(session, context=self._ctx)
        except:
            raise Exception("cd session error!!!")
        self._clear_data()

    def _clear_data(self):
        self.data: np.ndarray = None
        self.mat_cache: dict = {"mat": {}}
        self.data_shape: dict = {}
        self.dataset_num: int = None
        self.datasets_num: list = []
        self.dataset_name: str = None

    def _get_dataset_info(self):
        """
        Description:
        get dataset info for merge
        """
        info = {
            "inds": copy.deepcopy(self.inds),
            "deps": copy.deepcopy(self.deps),
            "data": copy.deepcopy(self.data),
        }
        return info

    def loadDataset(self, dataset, session=None, noisy=False, load_data=True):
        if session is not None:
            self.switch_session(session)
        dataset = dataset if dataset > 0 else self.dv.dir(context=self._ctx)[1][dataset]
        _, dataset_name = self.dv.open(dataset, context=self._ctx)
        self.dataset_num = int(dataset_name[0:5])
        self.datasets_num.append(self.dataset_num)
        self.dataset_name = dataset_name
        if noisy:
            print("#" * 40)
            print("Current Session: " + str(self.session))
            print("Current Dataset: " + str(self.dataset_name))
            print("#" * 40)
        if load_data:
            self.data = np.asarray(self.dv.get_ex(context=self._ctx))
        else:
            self.data = None

        inds, deps = self.dv.variables(context=self._ctx)

        self.inds = [
            {
                "name": inds_i[0],
                "units": inds_i[1],
                "shape": (1, len(self.data)),
            }
            for inds_i in inds
        ]
        self.deps = [
            {
                "name": deps_i[0],
                "legend": deps_i[1],
                "units": deps_i[2],
            }
            for deps_i in deps
        ]
        self.dim = len(self.inds)

    @property
    def parameters(self):
        if not hasattr(self, "_parameters"):
            return self._load_parameters()
        else:
            self._parameters

    def _load_parameters(self):
        self._parameters = dict(self.dv.get_parameters(context=self._ctx))
        return self._parameters


def switch_session_path(absolute_path, cxn=CXN):
    """get a datavault server using absolute path"""
    data_path_dir = str(absolute_path)
    session = [""]
    parent, subdir = os.path.split(data_path_dir)
    session.insert(1, subdir.replace(".dir", ""))
    while parent.endswith(".dir"):
        parent, subdir = os.path.split(parent)
        session.insert(1, subdir.replace(".dir", ""))
    dv = CXN.data_vault
    dv.cd(session)
    return dv


def check_busy_datasets(session, dataset_names):
    # _, dataTags = session.getTags([], dataset_names)
    # return ["busy" in dataTag[1] for dataTag in dataTags]
    return [False] * len(dataset_names)


def dep_name(dep):
    if dep["legend"]:
        return dep["name"] + f"({dep['legend']})"
    else:
        return dep["name"]


def getNbTotalRun(databaseAbsPath: str) -> None:
    dv = switch_session_path(databaseAbsPath)
    nbTotalRun = len(dv.dir()[1])
    return nbTotalRun


def getNbTotalRunmp(databaseAbsPath: str, queueNbRun: mp.Queue):
    queueNbRun.put(getNbTotalRun(databaseAbsPath))


def getRunInfos(databaseAbsPath: str):
    dv = switch_session_path(databaseAbsPath)
    allNames = dv.dir()[1]
    runInfos = dict((int(name.split(" - ")[0]), name) for name in allNames)
    return runInfos


def getRunInfosmp(
    databaseAbsPath: str, queueData: mp.Queue, queueProgressBar: mp.Queue, queueDone: mp.Queue
) -> None:
    print("len(runINfo):")
    runInfos = getRunInfos(databaseAbsPath)
    if not len(runInfos):
        queueData.put(None)
        queueDone.put(True)
        return None
    queueProgressBar.put(queueProgressBar.get() + 100)
    queueData.put(runInfos)
    queueDone.put(True)


def getDependentSnapshotShapeFromRunId(
    databaseAbsPath: str, runId: int
) -> Tuple[list, dict, dict]:
    dv = switch_session_path(databaseAbsPath)
    data = DataLab(dv.cd(), dv)
    data.loadDataset(runId)
    dependents = data.deps
    independents = data.inds
    dependentList = []
    for dep in dependents:
        dependentList.append(
            {
                "name": dep_name(dep),
                # "paramtype": dep['paramtype'],
                "label": dep_name(dep),
                "unit": dep["units"],
                "inferred_from": [],
                "depends_on": [indep["name"] for indep in independents],
            }
        )
    snapshotDict = data.parameters
    shapesDict = {}
    for dep in dependents:
        shapesDict[dep_name(dep)] = [tuple(ind["shape"]) for ind in independents]
    return dependentList, snapshotDict, shapesDict


def getParameterInfo(
    databaseAbsPath: str, runId: int, parameterName: str
) -> Tuple[dict, List[dict]]:
    dv = switch_session_path(databaseAbsPath)
    data = DataLab(dv.cd(), dv)
    data.loadDataset(runId)
    dependents = data.deps
    independents = data.inds
    dep_names = [dep_name(dep) for dep in dependents]
    dep = dependents[dep_names.index(parameterName)]
    dependences = {
        "name": dep_name(dep),
        # "paramtype": dep['paramtype'],
        "label": dep_name(dep),
        "unit": dep["units"],
        "inferred_from": [],
        "depends_on": [indep["name"] for indep in independents],
        "index": dep_names.index(parameterName),
    }
    param = []
    for indep in independents:
        param.append(
            {
                "name": indep["name"],
                # "paramtype": indep['paramtype'],
                "label": indep["name"],
                "unit": indep["units"],
                "inferred_from": [],
                "depends_on": [],
            }
        )
    # data = dv.open(runId)
    # val, dlen = data.getData(None, 0, None, None)
    dep_idx = dependences["index"]
    indep_len = len(param)
    d = np.concatenate(
        [
            data.data[:, :indep_len],
            data.data[:, indep_len + dep_idx : indep_len + dep_idx + 1],
        ],
        axis=1,
    )
    dependences["data"] = d
    return dependences, param


def getNbTotalRunAndLastRunNameLabrad(databaseAbsPath: str) -> Tuple[int, str]:
    """
    Return the number of run in the database and the name of the last run
    """
    dv = switch_session_path(databaseAbsPath)
    dataset_names = dv.dir()[1]
    return len(dataset_names), dataset_names[-1]


def isRunCompletedLabrad(databaseAbsPath: str, runId: int) -> bool:
    """
    Return True if the run is marked as completed, False otherwise
    """
    dv = switch_session_path(databaseAbsPath)
    # run_info = getRunInfos(databaseAbsPath)
    fileName = dv.fileName(runId)
    fileName = os.path.join(databaseAbsPath, fileName + ".hdf5")
    return False
    print("try to open file ", fileName)
    try:
        fd = h5py.File(fileName, "w")
        fd.close()
        return True
    except:
        return False
