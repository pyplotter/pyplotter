# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import sys
import os
import numpy as np
from typing import Callable

from sources.qcodesdatabase import QcodesDatabase

def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
# sys.excepthook = trap_exc_during_debug



class LoadDataSignal(QtCore.QObject):
    """
    Class containing the signal of the LoadDataThread, see below
    """


    # When the run method is done
    done = QtCore.pyqtSignal(str, tuple, str, str, str)
    # Signal used to update the status bar
    setStatusBarMessage = QtCore.pyqtSignal(str, bool)  
    # Signal 
    updateProgressBar = QtCore.pyqtSignal(int)




class LoadDataThread(QtCore.QRunnable):


    def __init__(self, runId                                : int,
                       row                                  : int,
                       plotRef                              : str,
                       getParameterData                     : Callable[[int, str, Callable], dict],
                       getListIndependentDependentFromRunId : Callable[[int], list],
                       getDependentLabel                    : Callable[[dict], str]):
        """
        Thread used to get data for a 1d or 2d plot from a runId.

        Parameters
        ----------
        runId : int
            run id from which the data are downloaded
        row : int
            Row inside which the dependent parameter is displayed.
            Correspond to the index position of the dependent parameter in the
            getListDependentFromRunId method.
        plotRef : str
            Reference of the curve.
        getParameterData : func
            Method from QcodesDatabase class initialized in the main thread
            with the current database file location.
            See QcodesDatabase for more details. 
        getListIndependentDependentFromRunId : func
            Method from QcodesDatabase class initialized in the main thread
            with the current database file location.
            See QcodesDatabase for more details. 
        getDependentLabel : func
            Method from Main class.
            Return a label from a qcodes dependent parameter. 
        """

        super(LoadDataThread, self).__init__()

        self.qcodesDatabase = QcodesDatabase()

        self.runId   = runId
        self.row   = row
        self.getParameterData   = getParameterData
        self.plotRef   = plotRef
        self.getListIndependentDependentFromRunId   = getListIndependentDependentFromRunId
        self.getDependentLabel = getDependentLabel
        

        self.signals = LoadDataSignal() 



    @QtCore.pyqtSlot()
    def run(self):
        """
        Download the data and launch a plot
        """

        self.signals.setStatusBarMessage.emit('Extracting data from database', False)

        paramsIndependent, paramsDependent = self.getListIndependentDependentFromRunId(self.runId)
        
        d = self.getParameterData(self.runId, paramsDependent[self.row]['name'], self.signals.updateProgressBar)

        if d is None:
            data = None
        else:

            # 1d plot
            if len(paramsIndependent)==1:
                
                # We try to load data
                # if there is none, we return an empty array
                try:
                    data = d[paramsIndependent[0]['name']], d[paramsDependent[self.row]['name']]
                except:
                    data = np.array([np.nan]), np.array([np.nan])


                xLabel = self.getDependentLabel(paramsIndependent[0])
                yLabel = self.getDependentLabel(paramsDependent[self.row])
                zLabel = ''


            # 2d plot
            elif len(paramsIndependent)==2:

                # We try to load data
                # if there is none, we return an empty array
                try:
                    data = self.shapeData2d(d[paramsIndependent[0]['name']], d[paramsIndependent[1]['name']], d[paramsDependent[self.row]['name']])
                except:
                    # We have to send [0,1] for the z axis when no data to avoid bug with the histogram
                    data = np.array([0, 1]), np.array([0, 1]), np.array([[0, 1],[0, 1]])


                xLabel = self.getDependentLabel(paramsIndependent[0])
                yLabel = self.getDependentLabel(paramsIndependent[1])
                zLabel = self.getDependentLabel(paramsDependent[self.row])


        # Signal to launched a plot with the downloaded data
        self.signals.done.emit(self.plotRef, data, xLabel, yLabel, zLabel)



    def shapeData2d(self, x, y, z):
        """
        Intermediate method to catch "error" when user is inverting the x and y
        axis compare to what the algo is expecting.
        """
        
        try:
            x, y, z = self.shapeData2dSub(x, y, z)
        except ValueError:
            x, y, z = self.shapeData2dSub(y, x, z)
            t = y
            y = x
            x = t
            z = z.T

        return x, y, z



    def shapeData2dSub(self, x, y, z):
        """
        Shape the data for a 2d plot but mainly handled all kind of data error/missing/...

        Return x and y as a 1d array, ready to be used for the 2d plot
        and z as a 2d array.
        In case of non regular grid, the y axis is approximated.
        """
        
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
        if len(np.unique(y[:,0])) == 1:
            
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
        # If not (like a auto freq measurement )
        else:

            self.setStatusBarMessage('Irregular grid detexted, shapping 2d data')
            xx = x[:,0]
            # Create a bigger array containing sorted data in the same bases
            # New y axis containing all the previous y axes
            yd = np.gradient(np.sort(y[0])).min()
            yy = np.arange(y[~np.isnan(y)].min(), y[~np.isnan(y)].max()+yd*2, yd)


            # For each z scan we create a new z array
            zz = np.array([])
            for y_current, z_current in zip(y, z):
                
                # Find the index of the current y axis on the global y axis
                p = np.abs(yy-y_current[0]).argmin()
                
                # Find the number of nan to insert at the beginning
                v  = np.full(p, np.nan)

                # Find the number of nan to insert at the end
                vv = np.full(len(yy)-p-len(y_current), np.nan)

                # Build the new z axis
                zz = np.append(zz, np.concatenate((v, z_current, vv)))

            zz = zz.reshape(int(len(zz)/len(yy)), len(yy))
        
        # If there is only one point in x or we artificialy create more
        if len(xx)==1:
            xx = np.array([xx*0.9, xx*1.1])
        if len(yy)==1:
            yy = np.array([yy*0.9, yy*1.1])

        return xx, yy, zz



    def shapeData2dPolygon(self, x : np.array,
                                 y : np.array,
                                 z : np.array) -> tuple :
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
        
        self.setStatusBarMessage('Shapping 2d data for display')

        ## Find effective "x" column
        # The x column is defined as the column where the independent parameter
        # is not modified while the y column independet parameter is.

        if y[1]==y[0]:
            t = x
            x = y
            y = t


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