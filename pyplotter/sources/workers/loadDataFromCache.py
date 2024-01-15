# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import numpy as np
from typing import Tuple

from ..config import loadConfigCurrent
config = loadConfigCurrent()
from ..functions import findXYIndex, shapeData2d, make_grid


class LoadDataFromCacheSignal(QtCore.QObject):
    """
    Class containing the signal of the LoadDataFromCacheThread, see below
    """

    dataLoaded = QtCore.pyqtSignal(str, # plotRef
                                   tuple, # data
                                   str, # yParamName
                                   bool) # lastUpdate

    # Signal used to update the status bar
    sendLivePlotInfoMessage = QtCore.pyqtSignal(str,
                                                str)



class LoadDataFromCacheThread(QtCore.QRunnable):


    def __init__(self, plotRef    : str,
                       dataDict   : dict,
                       xParamName : str,
                       yParamName : str,
                       zParamName : str,
                       lastUpdate : bool) -> None:
        """

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getDataRef.
        dataDict : dict
            qcodes cache data dictionnary
        xParamName : str
            Name of the x parameter.
        yParamName : str
            Name of the y parameter.
        zParamName : str
            Name of the z parameter.
        lastUpdate : bool
            True if this is the last update of the livePlot, a.k.a. the run is
            marked as completed by qcodes.
        """

        super(LoadDataFromCacheThread, self).__init__()

        self.plotRef    = plotRef
        self.dataDict   = dataDict
        self.xParamName = xParamName
        self.yParamName = yParamName
        self.zParamName = zParamName
        self.lastUpdate = lastUpdate

        self.signal = LoadDataFromCacheSignal()



    @QtCore.pyqtSlot()
    def run(self) -> None:
        """
        """
        # It takes some iteration for the cache to start having data
        # We check here if there is data in the cache
        if self.zParamName=='':
            if len(self.dataDict[self.yParamName])==0:
                data: Tuple[np.ndarray, ...] = (np.array([]), np.array([]))
            else:
                d = self.dataDict[self.yParamName]
                data = (d[self.xParamName], d[self.yParamName])
        else:
            # The data in the cache may be empty, we handle that by sending fake data
            if len(self.dataDict[self.zParamName])==0:
                data = (np.array([0., 1.]),
                        np.array([0., 1.]),
                        np.array([[0., 1.],
                                  [0., 1.]]))
            else:

                d = self.dataDict[self.zParamName]

                # For qcodes version >0.20, 2d data are return as a 2d array
                # the z data are then returned as given by qcodes.
                # We however have to find a x and y 1d array for the imageItem
                # This is done by a simple linear interpolation between the
                # max and minimum value of the x, y 2d array returned by qcodes.
                # WILL NOT WORK for NON-LINEAR SPACED DATA
                if d[self.zParamName].ndim==2 or d[self.zParamName].ndim==3:

                    fx = np.ravel(d[self.xParamName][~np.isnan(d[self.xParamName])])
                    fy = np.ravel(d[self.yParamName][~np.isnan(d[self.yParamName])])

                    xx = np.linspace(fx.min(), fx.max(), d[self.zParamName].shape[0])
                    yy = np.linspace(fy.min(), fy.max(), d[self.zParamName].shape[1])
                    zz = d[self.zParamName]

                    # we take care of data taken along decreasing axes
                    if fx[1]<fx[0]:
                        zz = zz[::-1,:]
                    if fy[1]<fy[0]:
                        zz = zz[:,::-1]

                    data = (xx,
                            yy,
                            zz)

                else:

                    # If there is less that 2 data points, we can't build a 2d map
                    # We handle that by returning fake data
                    if len(d[self.yParamName])<2:
                        data = (np.array([0., 1.]),
                                np.array([0., 1.]),
                                np.array([[0., 1.],
                                          [0., 1.]]))
                    else:
                        data = (d[self.xParamName],
                                d[self.yParamName],
                                d[self.zParamName])

                        # Find the effective x and y axis, see findXYIndex
                        xi, yi = findXYIndex(data[1])

                        # Shapped the 2d Data
                        if config['2dGridInterpolation']=='grid':
                            data = make_grid(data[xi],
                                             data[yi],
                                             data[2])
                        else:
                            data = shapeData2d(data[xi],
                                               data[yi],
                                               data[2],
                                               self.signal.sendLivePlotInfoMessage)

        self.signal.dataLoaded.emit(self.plotRef, # plotRef
                                    data, # data
                                    self.yParamName, # yParamName
                                    self.lastUpdate) # lastUpdate
