import os
import numpy as np
import multiprocess as mp
import copy
from typing import Tuple, List
from pathlib import Path
import h5py
import base64
from collections import namedtuple

DATA_URL_PREFIX = "data:application/labrad;base64,"

try:
    import labrad
except:
    print("Labrad not installed, you will not able to read labrad datasets!")

CXN = None
LOCAL_DATAVAULT = False
# maximum plot dependents to avoid opening to many 2D windows, if not specificed by the user
MAX_NUM_PLOT_DEPS = 8


def labrad_urldecode(data_url) -> any:
    """
    Labrad data are encoded as dataurl and then stored in hdf5 files,
    here we just decode these data using Labrad APIs.
    """

    from labrad import types as T

    if data_url.startswith(DATA_URL_PREFIX):
        all_bytes = base64.urlsafe_b64decode(data_url[len(DATA_URL_PREFIX) :])
        t, data_bytes = T.unflatten(all_bytes, "sy")
        data = T.unflatten(data_bytes, t)
        return data
    else:
        raise ValueError(
            "Trying to labrad_urldecode data that doesn't start "
            "with prefix: {}".format(DATA_URL_PREFIX)
        )


Independent = namedtuple("Independent", ["name", "shape", "datatype", "unit"])
Dependent = namedtuple("Dependent", ["name", "legend", "shape", "datatype", "unit"])


class LocalDatavault:
    """
    Manage the Labrad data with the local data vault,
    without connecting to the data_vault server.

    The goal is to substitute APIs provided by the data_vault server, so there are unused variables as spaceholders.
    """

    def __init__(self, root=None, session=None, absolute_path=None) -> None:
        if absolute_path is None:
            absolute_path = rootSession2absolutePath(root, session)
            self.root, self.session = root, session
        else:
            self.root, self.session = absolutePath2rootSession(absolute_path)
        self.path = Path(absolute_path)
        self.suffix = ".dir"
        self.file_name_loaded = None

    def context(self) -> None:
        return None

    def cd(self, session, context=None) -> None:
        self.path = Path(rootSession2absolutePath(self.root, session))

    def ls(self, onlyDir=False) -> Tuple[List[str]]:
        patterns = ["*" + self.suffix] if onlyDir else ["*" + self.suffix, "*.hdf5"]
        return tuple(
            [file.name.replace(pattern[1:], "") for file in self.path.glob(pattern)]
            for pattern in patterns
        )

    def dir(self, context=None) -> Tuple[List[str]]:
        return self.ls()

    def open(self, dataset, context=None) -> Tuple[any | List[str] | None, str]:
        self.filename = list(self.path.glob("{:05d}*.hdf5".format(dataset)))[0]
        self.dataset_name = self.filename.name.replace(".hdf5", "")
        return self.session, self.dataset_name

    def get_name(self, context=None) -> str:
        return self.dataset_name

    def _load(self) -> None:
        if self.filename != self.file_name_loaded:
            self.file_name_loaded = self.filename
            with h5py.File(self.filename, "r", swmr=True) as hdf5_file:
                datavault = hdf5_file["DataVault"]
                array_data = datavault[()]
                # self.array_data = array_data
                self.data = np.array(
                    [array_data["f" + str(idx)] for idx in range(len(array_data.dtype))]
                ).T
                self.attrs = dict(datavault.attrs)
                self.Independents = {}
                self.Dependents = {}
                self.param_list = []
                for key, value in datavault.attrs.items():
                    if key.startswith("Dependent"):
                        idx, raw_key = key[len("Dependent") :].split(".", maxsplit=1)
                        self.Dependents[idx] = self.Dependents.get(idx, {})
                        self.Dependents[idx][raw_key] = value
                    elif key.startswith("Independent"):
                        idx, raw_key = key[len("Independent") :].split(".", maxsplit=1)
                        self.Independents[idx] = self.Independents.get(idx, {})
                        self.Independents[idx][raw_key] = value
                    elif key.startswith("Param."):
                        self.param_list.append((key[len("Param.") :], labrad_urldecode(value)))
                self.inds_list = [
                    Independent(
                        name=d["label"],
                        shape=d["shape"],
                        datatype=d["datatype"],
                        unit=d["unit"],
                    )
                    for d in self.Independents.values()
                ]
                self.deps_list = [
                    Dependent(
                        name=d["label"],
                        legend=d["legend"],
                        shape=d["shape"],
                        datatype=d["datatype"],
                        unit=d["unit"],
                    )
                    for d in self.Dependents.values()
                ]

    def get_ex(self, context=None) -> np.ndarray[any, np.dtype[any]]:
        self._load()
        return self.data

    def variables_ex(self, context=None) -> Tuple[List[Independent] | List[Dependent]]:
        self._load()
        return self.inds_list, self.deps_list

    def get_parameters(self, context=None) -> List[any]:
        self._load()
        return self.param_list


def absolutePath2rootSession(absolute_path) -> Tuple[str | List[str]]:
    data_path_dir = str(absolute_path)
    session = [""]
    root, subdir = os.path.split(data_path_dir)
    session.insert(1, subdir.replace(".dir", ""))
    while root.endswith(".dir"):
        root, subdir = os.path.split(root)
        session.insert(1, subdir.replace(".dir", ""))
    return root, session


def rootSession2absolutePath(root, session) -> str:
    return Path(root).joinpath("/".join([folder + ".dir" for folder in session])).as_posix()


def get_datavault(absolute_path, cxn=None) -> LocalDatavault:  # any means labrad server object
    # access data through labrad server
    if cxn is not None:
        dv = cxn.data_vault
    # access data with local datavault
    else:
        dv = LocalDatavault(absolute_path=absolute_path)
    return dv


class LabradDataset(object):
    """get labrad data using absolute path"""

    def __init__(self, absolute_path, cxn=None, noisy=False):
        global CXN
        global LOCAL_DATAVAULT
        if LOCAL_DATAVAULT:
            try:
                CXN = labrad.connect()
                CXN.data_vault
                LOCAL_DATAVAULT = False
            except:
                CXN = None
                LOCAL_DATAVAULT = True
                print("Failed to connect to Labrad, read hdf5 files locally!")
                print(
                    "To enable liveplot, you might want to install Labrad, "
                    "run a data_vault server, and connect to it."
                )
        cxn = CXN if cxn is None else cxn

        self.dv = get_datavault(absolute_path, cxn=cxn)
        self._ctx = self.dv.context()
        if not isinstance(self.dv, LocalDatavault):
            root, session = absolutePath2rootSession(absolute_path)
            if noisy:
                print("####### Labrad datavault dir: ", root)
            try:
                self.dv.cd(session, context=self._ctx)
            except:
                raise Exception("cd session error!!!")
        self.noisy = noisy
        self._clear_data()

    def _clear_data(self) -> None:
        self.data: np.ndarray = None
        self.mat_cache: dict = {"mat": {}}
        self.data_shape: dict = {}
        self.dataset_num: int = None
        self.datasets_num: list = []
        self.dataset_name: str = None

    def listDatasets(self) -> List[str]:
        return self.dv.dir(context=self._ctx)[1]

    def loadDataset(self, dataset, load_data=True) -> None:
        assert isinstance(dataset, int)
        session, dataset_name = self.dv.open(dataset, context=self._ctx)
        self.dataset_num = int(dataset_name[0:5])
        self.datasets_num.append(self.dataset_num)
        self.dataset_name = dataset_name
        if self.noisy:
            print("#" * 40)
            print("Current Session: " + str(session))
            print("Current Dataset: " + str(self.dataset_name))
            print("#" * 40)
        if load_data:
            self.data = np.asarray(self.dv.get_ex(context=self._ctx))
        else:
            self.data = None

        inds, deps = self.dv.variables_ex(context=self._ctx)
        if isinstance(inds[0], Independent):
            self.inds = inds
        else:
            self.inds = [
                Independent(
                    name=inds_i[0],
                    shape=(1, len(self.data)),
                    datatype=inds_i[2],
                    unit=inds_i[3],
                )
                for inds_i in inds
            ]
        if isinstance(deps[0], Dependent):
            self.deps = deps
        else:
            self.deps = [
                Dependent(
                    name=deps_i[0],
                    legend=deps_i[1],
                    shape=deps_i[2],
                    datatype=deps_i[3],
                    unit=deps_i[4],
                )
                for deps_i in deps
            ]
        self.dim = len(self.inds)

    def _get_dataset_info(self) -> dict[str]:
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

    def _load_parameters(self) -> dict:
        self._parameters = dict(self.dv.get_parameters(context=self._ctx))
        return self._parameters

    @property
    def parameters(self) -> dict:
        if not hasattr(self, "_parameters"):
            return self._load_parameters()
        else:
            return self._parameters

    @property
    def name(self) -> str:
        return self.dataset_name

    def getIndependents(self) -> List[Independent]:
        return self.inds

    def getDependents(self) -> List[Dependent]:
        return self.deps

    def getPlotDependents(self) -> List[Dependent]:
        plotDepsNames = self.parameters.get("plot_dependents", None)
        plotDependents = []
        for dep in self.getDependents():
            if plotDepsNames is None or dep_label(dep) in plotDepsNames:
                plotDependents.append(dep)
        return plotDependents[:MAX_NUM_PLOT_DEPS]

    def getPlotData(self) -> np.ndarray:
        d = self.data
        num_inds = len(self.inds)
        sel_idx = np.arange(num_inds).tolist()
        plotDeps = self.getPlotDependents()
        sel_idx += [num_inds + self.deps.index(dep) for dep in plotDeps]
        return d[:, sel_idx]


def check_busy_datasets(session, dataset_names) -> List[bool]:
    # _, dataTags = session.getTags([], dataset_names)
    # return ["busy" in dataTag[1] for dataTag in dataTags]
    return [False] * len(dataset_names)


def dep_label(dep) -> str:
    """
    return unique label of dependents
    """
    if isinstance(dep, Dependent):
        legend = dep.legend
        name = dep.name
    else:
        legend = dep.legend
        name = dep.name
    if legend:
        return name + f"({legend})"
    else:
        return name


def getNbTotalRun(databaseAbsPath: str) -> int:
    dv = get_datavault(databaseAbsPath)
    nbTotalRun = len(dv.dir()[1])
    return nbTotalRun


def getNbTotalRunmp(databaseAbsPath: str, queueNbRun: mp.Queue) -> None:
    queueNbRun.put(getNbTotalRun(databaseAbsPath))


def getRunInfos(databaseAbsPath: str) -> dict[int, str]:
    dv = get_datavault(databaseAbsPath)
    allNames = dv.dir()[1]
    runInfos = dict((int(name.split(" - ")[0]), name) for name in allNames)
    return runInfos


def getDatabaseInfos(databaseAbsPath: str) -> Tuple:
    dv = get_datavault(databaseAbsPath)
    allNames = dv.dir()[1]
    runId = []
    experimentName = []
    for name in allNames:
        runId.append(int(name.split(" - ")[0]))
        experimentName.append(name)
    num = len(allNames)
    dim = ["-"] * num
    sampleName = runName = started = completed = duration = runRecords = ["-"] * num
    captured_run_id = guid = ["0"] * num
    return (
        runId,
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
    )


# def getRunInfosmp(
#     databaseAbsPath: str, queueData: mp.Queue, queueProgressBar: mp.Queue, queueDone: mp.Queue
# ) -> None:
#     print("len(runINfo):")
#     runInfos = getRunInfos(databaseAbsPath)
#     if not len(runInfos):
#         queueData.put(None)
#         queueDone.put(True)
#         return None
#     queueProgressBar.put(queueProgressBar.get() + 100)
#     queueData.put(runInfos)
#     queueDone.put(True)


def getDependentSnapshotShapeFromRunId(
    databaseAbsPath: str, runId: int
) -> Tuple[list, dict, dict]:
    data = LabradDataset(databaseAbsPath)
    data.loadDataset(runId)
    dependents = data.deps
    independents = data.inds
    dependentList = []
    for dep in dependents:
        dependentList.append(
            {
                "name": dep_label(dep),
                "label": dep_label(dep),
                "unit": dep.unit,
                "inferred_from": [],
                "depends_on": [dep_label(dep) for indep in independents],
            }
        )
    snapshotDict = data.parameters
    shapesDict = {}
    for dep in dependents:
        shapesDict[dep_label(dep)] = [tuple(ind.shape) for ind in independents]
    return dependentList, snapshotDict, shapesDict


def getParameterInfo(
    databaseAbsPath: str, runId: int, parameterName: str
) -> Tuple[dict, List[dict]]:
    data = LabradDataset(databaseAbsPath)
    data.loadDataset(runId)
    dependents = data.deps
    independents = data.inds
    dep_names = [dep_label(dep) for dep in dependents]
    dep = dependents[dep_names.index(parameterName)]
    dependences = {
        "name": dep_label(dep),
        "label": dep_label(dep),
        "unit": dep.unit,
        "inferred_from": [],
        "depends_on": [dep_label(dep) for indep in independents],
        "index": dep_names.index(parameterName),
    }
    param = []
    for indep in independents:
        param.append(
            {
                "name": dep_label(dep),
                "label": dep_label(dep),
                "unit": indep.unit,
                "inferred_from": [],
                "depends_on": [],
            }
        )
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
    dv = get_datavault(databaseAbsPath)
    dataset_names = dv.dir()[1]
    return len(dataset_names), dataset_names[-1]


def isRunCompletedLabrad(databaseAbsPath: str, runId: int) -> bool:
    """
    Return True if the run is marked as completed, False otherwise
    """
    data = LabradDataset(databaseAbsPath)
    try:
        data.loadDataset(runId)
        return True
    except:
        return False
