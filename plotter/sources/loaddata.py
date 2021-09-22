# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import numpy as np
from typing import Callable, Tuple

from .qcodesdatabase import QcodesDatabase
from .config import config



class LoadDataSignal(QtCore.QObject):
    """
    Class containing the signal of the LoadDataThread, see below
    """


    # When the run method is done
    # Signature
    # runId: int, curveId:str, plotTitle: str, windowTitle:str
    # plotRef: str, progressBarKey: str, data: tuple
    # xLabelText: str, xLabelUnits: str,
    # yLabelText: str, yLabelUnits: str,
    # zLabelText: str, zLabelUnits: str,
    updateDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)
    # Signal used to update the status bar
    setStatusBarMessage = QtCore.pyqtSignal(str, bool)  
    # Signal to update the progress bar
    updateProgressBar = QtCore.pyqtSignal(str, int)
    # Signal when the data download is done but the database is empty
    # Useful for the starting of the liveplot
    updateDataEmpty = QtCore.pyqtSignal()




class LoadDataThread(QtCore.QRunnable):


    def __init__(self, runId              : int,
                       curveId            : str,
                       plotTitle          : str,
                       windowTitle        : str,
                       dependentParamName : str,
                       plotRef            : str,
                       progressBarKey     : str,
                       getParameterData   : Callable[[int, str, Callable], dict],
                       getParameterInfo   : Callable[[int], list]) -> None:
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
        progressBarKey : str
            Key to the progress bar in the dict progressBars.
        getParameterData : func
            Method from QcodesDatabase class initialized in the main thread
            with the current database file location.
            See QcodesDatabase for more details. 
        getParameterInfo : func
            Method from QcodesDatabase class initialized in the main thread
            with the current database file location.
            See QcodesDatabase for more details.
        """

        super(LoadDataThread, self).__init__()

        self.qcodesDatabase = QcodesDatabase()

        self.runId              = runId
        self.curveId            = curveId
        self.plotTitle          = plotTitle
        self.windowTitle        = windowTitle
        self.dependentParamName = dependentParamName
        self.plotRef            = plotRef
        self.progressBarKey     = progressBarKey
        self.getParameterData   = getParameterData
        self.getParameterInfo   = getParameterInfo
        

        self.signals = LoadDataSignal() 



    @QtCore.pyqtSlot()
    def run(self) -> None:
        """
        Download the data and launch a plot
        """

        self.signals.setStatusBarMessage.emit('Extracting data from database', False)

        paramsDependent, paramsIndependent = self.getParameterInfo(self.runId, self.dependentParamName)
        
        d = self.getParameterData(self.runId, paramsDependent['name'], self.signals.updateProgressBar, self.progressBarKey)
        
        # If getParameterData failed, or the database is empty we emit a specific
        # signal which will flag the data download as done without launching a
        # new plot window
        if d is None or len(d)==0:
            self.signals.updateDataEmpty.emit()
        else:

            # 1d plot
            if len(paramsIndependent)==1:
                
                data = (np.ravel(d[paramsIndependent[0]['name']]),
                        np.ravel(d[paramsDependent['name']]))

                xLabelText  = paramsIndependent[0]['label']
                xLabelUnits = paramsIndependent[0]['unit']
                yLabelText  = paramsDependent['label']
                yLabelUnits = paramsDependent['unit']
                zLabelText  = ''
                zLabelUnits = ''


            # 2d plot
            elif len(paramsIndependent)==2:
                
                # for qcodes version >0.18, 2d data are return as a 2d array
                # to keep code backward compatible, we transform it back to
                # 1d array.
                if d[paramsIndependent[1]['name']].ndim==2 or d[paramsIndependent[1]['name']].ndim==3:
                    d[paramsIndependent[0]['name']] = np.ravel(d[paramsIndependent[0]['name']])
                    d[paramsIndependent[1]['name']] = np.ravel(d[paramsIndependent[1]['name']])
                    d[paramsDependent['name']]      = np.ravel(d[paramsDependent['name']])
                
                # Find the effective x and y axis, see findXYIndex
                xi, yi = self.findXYIndex(d[paramsIndependent[1]['name']])
                
                # We try to load data
                # if there is none, we return an empty array
                if config['2dGridInterpolation']=='grid':
                    data = self.make_grid(d[paramsIndependent[xi]['name']],
                                          d[paramsIndependent[yi]['name']],
                                          d[paramsDependent['name']])
                else:
                    data = self.shapeData2d(d[paramsIndependent[xi]['name']],
                                            d[paramsIndependent[yi]['name']],
                                            d[paramsDependent['name']])

                xLabelText  = paramsIndependent[xi]['label']
                xLabelUnits = paramsIndependent[xi]['unit']
                yLabelText  = paramsIndependent[yi]['label']
                yLabelUnits = paramsIndependent[yi]['unit']
                zLabelText  = paramsDependent['label']
                zLabelUnits = paramsDependent['unit']


            # Signal to launched a plot with the downloaded data
            self.signals.updateDataFull.emit(self.runId,
                                             self.curveId,
                                             self.plotTitle,
                                             self.windowTitle,
                                             self.plotRef,
                                             self.progressBarKey,
                                             data,
                                             xLabelText,
                                             xLabelUnits,
                                             yLabelText,
                                             yLabelUnits,
                                             zLabelText,
                                             zLabelUnits)



    @staticmethod
    def findXYIndex(y: np.ndarray) -> Tuple[int]:
        """
        Find effective "x" column
        The x column is defined as the column where the independent parameter
        is not modified while the y column independent parameter is.
        
        Parameters
        ----------
        y : np.ndarray
            Data of the original y axis

        Returns
        -------
        (xi, yi) : tuple
            Index of the the x and y axis.
        """
        
        if y[1]==y[0]:
            return 1, 0
        else:
            return 0, 1



    def shapeData2d(self, x: np.ndarray,
                          y: np.ndarray,
                          z: np.ndarray) -> Tuple[np.ndarray]:
        """
        Shape the data for a 2d plot but mainly handled all kind of data error/missing/...

        Return x and y as a 1d array, ready to be used for the 2d plot
        and z as a 2d array.
        In case of non regular grid, the y axis is approximated.
        """


        self.signals.setStatusBarMessage.emit('Shapping 2d data for display', False)


        # Nb points in the 1st dimension
        xn = len(np.unique(x))

        # Nb points in the 2nd dimension
        xx = np.array([])
        for i in np.unique(x):
            xx = np.append(xx, len(x[x==i]))
        yn = int(xx.max())

        # If interuption, we calculated the number of missing point and add them
        if len(np.unique(xx)) != 1:

            p = np.full(int(xx.max() - xx.min()), np.nan)

            x = np.append(x, p)
            y = np.append(y, p)
            z = np.append(z, p)
            
        # We create 2D arrays for each dimension
        x = x.reshape(xn, yn)
        y = y.reshape(xn, yn)
        z = z.reshape(xn, yn)

        # Once the shape is corrected, we sort the data
        m = x[:,0].argsort()
        x = x[m]
        y = y[m]
        z = z[m]

        # If the data has a rectangular shape (usual 2d measurement)
        if len(np.unique(y[:,0]))==1:
            
            # Take a slice of x
            xx = x[:,0]

            # Find a row of y containing only non nan data
            i = 0
            for i in y:
                if not np.any(np.isnan(i)):
                    yy = i
                    break
                i+=1
            
            zz = z
        else:

            self.signals.setStatusBarMessage.emit('Irregular grid detected, shapping 2d data', False)

            xx = x[:,0]
            
            # Create a bigger array containing sorted data in the same bases
            # New y axis containing all the previous y axes
            yd = np.gradient(np.sort(y[0])).min()
            yy = np.arange(y[~np.isnan(y)].min(), y[~np.isnan(y)].max()+yd, yd)
            
            # fit the z value to the new grid
            zz = np.full((len(xx), len(yy)), np.nan)
            for x_index in range(len(x)):
                for y_index in range(len(y.T)):
                    zz[x_index,np.abs(yy-y[x_index, y_index]).argmin()] = z[x_index,y_index]
                

        
        # If there is only one point in x or y, we artificialy create more
        # moreThanOneColumn = True
        if len(xx)==1:
            xx = np.array([xx[0]-0.1, xx[0]+0.1])
            # moreThanOneColumn = False
        if len(yy)==1:
            yy = np.array([yy[0]-0.1, yy[0]+0.1])
            # moreThanOneColumn = False

        # We filtered out the npinf and -np.inf data and replaced them by np.nan
        # This is done to allow display by the pyqtgraph viewbox.
        zz[zz== np.inf] = np.nan
        zz[zz==-np.inf] = np.nan
        
        return xx, yy, zz



    @staticmethod
    def make_grid(x, y, z):
        '''
        Takes x, y, z values as lists and returns a 2D numpy array
        https://stackoverflow.com/questions/30764955/python-numpy-create-2d-array-of-values-based-on-coordinates
        '''
        dx = abs(np.sort(np.unique(x))[1] - np.sort(np.unique(x))[0])
        dy = abs(np.sort(np.unique(y))[1] - np.sort(np.unique(y))[0])
        i = np.rint((x - min(x))/dx).astype(int)
        j = np.rint((y - min(y))/dy).astype(int)
        xx = np.nan * np.empty(len(np.unique(i)))
        yy = np.nan * np.empty(len(np.unique(j)))
        zz = np.nan * np.empty((len(np.unique(i)), len(np.unique(j))))
        xx[i] = x
        yy[j] = y
        zz[i, j] = z
        return xx, yy, zz



    def shapeData2dPolygon(self, x : np.array,
                                 y : np.array,
                                 z : np.array) -> Tuple[np.ndarray]:
        """
        Reshape 2d scan into a meshing.
        
        Return
        ------
            x2dVertices : 2d np.array
                Vertices along x of the polygons
            y2dVertices : 2d np.array
                Vertices along y of the polygons
            z2d : 2d np.array
                Value of the polygons
        """
        self.signals.setStatusBarMessage.emit('Shapping 2d data for display', False)


        ## Treat the data depending on their shape
        # We get the number of point in the x and y dimension
        # We add fake data (with np.nan value for the xaxis) for unfinished 
        # measurements

        # Finished regular grid
        if len(np.unique([len(x[x==i])for i in np.unique(x)]))==1 and len(np.unique(y))==len(y[::len(np.unique(x))]):
            
            # Nb points in the 1st dimension
            xn = len(np.unique(x))

            # Nb points in the 2nd dimension
            yn = len(y[::xn])# Finished regular grid
            
        # Finished unregular grid
        elif len(np.unique([len(x[x==i])for i in np.unique(x)]))==1 :
            
            # Nb points in the 1st dimension
            xn = len(np.unique(x))

            # Nb points in the 2nd dimension
            yn = len(y[::xn])

        # Unfinished unregular grid
        elif y[0]!=y[len(x[x==x[0]])]:
            
            # Nb points in the 1st dimension
            xn = len(np.unique(x))
            
            # Nb points in the 2nd dimension
            yn = len(x[x==x[0]])
            
            ## Build "full" x, y and z
            
            # Find how many element a finished grid would have
            # Number of element per x value
            t = np.array([len(x[x==i])for i in np.unique(x)])
            tmax = max(t)
            # Number of element if the measurement was finished
            tFinished = (len(t[t==min(t)]) + len(t[t==tmax]))*tmax
            # Number of missing element
            nbMissing = tFinished - len(x)
            
            ## Interpolate last y value based on the last done scan
            # Last full y measured
            yLastFull = y[-2*tmax+nbMissing:-tmax+nbMissing]
            dyLastFull = np.gradient(yLastFull)
            dyinterp = np.gradient(yLastFull)[-nbMissing:]

            yMissing = np.array([y[-1]])
            for i in dyinterp:
                yMissing = np.append(yMissing, yMissing[-1] + i)


            x = np.concatenate((x, [x[-1]]*nbMissing))
            y = np.concatenate((y, yMissing[1:]))
            z = np.concatenate((z, [np.nan]*nbMissing))
            
        # Unfinished regular grid
        else:
            
            ## Build "full" x, y and z
            
            # Find how many element a finished grid would have
            # Number of element per x value
            t = np.array([len(x[x==i])for i in np.unique(x)])
            # Number of element if the measurement was finished
            tFinished = (len(t[t==min(t)]) + len(t[t==max(t)]))*max(t)
            # Number of missing element
            nbMissing = tFinished - len(x)
            
            # Nb points in the 1st dimension
            xn = len(np.unique(x))
            # Nb points in the 2nd dimension
            yn = len(np.unique(y))
            
            x = np.concatenate((x, [x[-1]]*nbMissing))
            y = np.concatenate((y, y[:yn][-nbMissing:]))
            z = np.concatenate((z, [np.nan]*nbMissing))
            


        ## Get the 2d matrices for x, y and z
        # x and y are the vertices of the polygon and their shape should be
        # x[i+1, j+1] and y[i+1, j+1] while z is the value of the polygon and
        # its shape should be z[i, j]

        x2d = x.reshape((xn, yn))
        dx = np.gradient(x2d, axis=0)/2.
        x2dVertices = np.concatenate((x2d - dx, [x2d[-1]+dx[-1]]))
        x2dVertices = np.concatenate((x2dVertices, np.array([x2dVertices[:,1]]).T), axis=1)


        y2d = y.reshape((xn, yn))
        dy = np.gradient(y2d, axis=1)/2.
        y2dVertices = np.concatenate((y2d - dy, np.array([y2d[:,-1]+dy[:,-1]]).T), axis=1)
        y2dVertices = np.concatenate((y2dVertices, np.array([y2dVertices[-1]*2 -y2dVertices[-2] ])))


        z2d = z.reshape((xn, yn))


        return x2dVertices, y2dVertices, z2d