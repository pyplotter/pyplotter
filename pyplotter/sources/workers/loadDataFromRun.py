# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtTest
import numpy as np
from typing import Tuple, Optional
import multiprocessing as mp

from ..qcodesdatabase import getParameterDatamp, getParameterInfo
from ..config import loadConfigCurrent
config = loadConfigCurrent()
from ..functions import findXYIndex, shapeData2d, make_grid




class LoadDataFromRunSignal(QtCore.QObject):
    """
    Class containing the signal of the LoadDataFromRunThread, see below
    """


    # When the run method is done
    # Signature
    # runId: int, curveId:str, plotTitle: str, windowTitle:str
    # plotRef: str, databaseAbsPath: str, progressBar: str, data: tuple
    # xLabelText: str, xLabelUnits: str,
    # yLabelText: str, yLabelUnits: str,
    # zLabelText: str, zLabelUnits: str,
    loadedDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str)
    # Signal used to update the status bar
    sendStatusBarMessage = QtCore.pyqtSignal(str, str)
    # Signal to update the progress bar
    updateProgressBar = QtCore.pyqtSignal(QtWidgets.QProgressBar, int, str)
    # Signal when the data download is done but the database is empty
    # Useful for the starting of the liveplot
    loadedDataEmpty = QtCore.pyqtSignal()




class LoadDataFromRunThread(QtCore.QRunnable):


    def __init__(self, curveId: str,
                       databaseAbsPath: str,
                       dependentParamName: str,
                       plotRef: str,
                       plotTitle: str,
                       runId: int,
                       windowTitle: str,
                       progressBar: QtWidgets.QProgressBar) -> None:
        """
        Thread used to get data for a 1d or 2d plot from a runId.

        Parameters
        ----------
        runId : int
            run id from which the data are downloaded
        curveId : str
            Id of the curve, see getCurveId.
        plotTitle : str
            Plot title, see getPlotTitle.
        windowTitle : str
            Window title, see getWindowTitle.
        dependentParamName : str
            Name of the dependent parameter from which data will be downloaded.
        plotRef : str
            Reference of the curve.
        progressBar : str
            Key to the progress bar in the dict progressBars.
        """

        super(LoadDataFromRunThread, self).__init__()

        self.curveId            = curveId
        self.databaseAbsPath    = databaseAbsPath
        self.dependentParamName = dependentParamName
        self.plotRef            = plotRef
        self.plotTitle          = plotTitle
        self.runId              = runId
        self.windowTitle        = windowTitle
        self.progressBar        = progressBar


        self.signal = LoadDataFromRunSignal()



    @QtCore.pyqtSlot()
    def run(self) -> None:
        """
        Download the data and launch a plot.
        Create another process with share memory through which the data are
        transfered.
        """

        self.signal.sendStatusBarMessage.emit('Extracting data from database', 'orange')

        paramsDependent, paramsIndependent = getParameterInfo(self.databaseAbsPath,
                                                              self.runId,
                                                              self.dependentParamName)

        # Queue will contain the numpy array of the run data
        queueData: mp.Queue = mp.Queue()
        # Queue will contain a float from 0 to 100 for the progress bar
        queueProgressBar: mp.Queue = mp.Queue()
        queueProgressBar.put(0)
        # Queue will contain 1 when the download is done
        queueDone: mp.Queue = mp.Queue()
        queueDone.put(False)

        self.worker = mp.Process(target=getParameterDatamp,
                                 args=(self.databaseAbsPath,
                                       self.runId,
                                       [paramIndependent['name'] for paramIndependent in paramsIndependent],
                                       paramsDependent['name'],
                                       queueData,
                                       queueProgressBar,
                                       queueDone))
        self.worker.start()

        # Here, we loop until the data transfer is done.
        # In each loop, we check the transfer progression and update the progress
        # bar
        done = False
        while not done:
            QtTest.QTest.qWait(config['delayBetweenProgressBarUpdate'])

            progressBar = queueProgressBar.get()
            queueProgressBar.put(progressBar)

            self.signal.updateProgressBar.emit(self.progressBar, progressBar, 'Downloading data: {:.0f}%'.format(progressBar))

            done = queueDone.get()
            queueDone.put(done)

        d: np.ndarray = queueData.get()
        queueData.close()
        queueData.join_thread()
        queueProgressBar.close()
        queueProgressBar.join_thread()
        queueDone.close()
        queueDone.join_thread()

        # If getParameterDatamp failed, or the database is empty we emit a specific
        # signal which will flag the data download as done without launching a
        # new plot window
        if d is None:
            self.signal.sendStatusBarMessage.emit('Extracting data failed...', 'red')
            self.signal.loadedDataEmpty.emit()
        elif len(d)==0:
            self.signal.sendStatusBarMessage.emit('Run empty', 'red')
            self.signal.loadedDataEmpty.emit()
        else:

            # 1d plot
            if len(paramsIndependent)==1:
                data: Tuple[np.ndarray, ...] = (d[:,0], d[:,1])

                xLabelText  = paramsIndependent[0]['label']
                xLabelUnits = paramsIndependent[0]['unit']
                yLabelText  = paramsDependent['label']
                yLabelUnits = paramsDependent['unit']
                zLabelText  = ''
                zLabelUnits = ''

            # 2d plot
            elif len(paramsIndependent)==2:

                # Find the effective x and y axis, see findXYIndex
                xi, yi = findXYIndex(d[:,1])

                # We try to load data
                # if there is none, we return an empty array
                if config['2dGridInterpolation']=='grid':
                    data = make_grid(d[:,xi],
                                     d[:,yi],
                                     d[:,2])
                else:
                    data = shapeData2d(d[:,xi],
                                       d[:,yi],
                                       d[:,2],
                                       self.signal.sendStatusBarMessage)

                xLabelText  = paramsIndependent[xi]['label']
                xLabelUnits = paramsIndependent[xi]['unit']
                yLabelText  = paramsIndependent[yi]['label']
                yLabelUnits = paramsIndependent[yi]['unit']
                zLabelText  = paramsDependent['label']
                zLabelUnits = paramsDependent['unit']


            # Signal to launched a plot with the downloaded data
            self.signal.loadedDataFull.emit(self.runId,
                                            self.curveId,
                                            self.plotTitle,
                                            self.windowTitle,
                                            self.plotRef,
                                            self.databaseAbsPath,
                                            self.progressBar,
                                            data,
                                            xLabelText,
                                            xLabelUnits,
                                            yLabelText,
                                            yLabelUnits,
                                            zLabelText,
                                            zLabelUnits)


