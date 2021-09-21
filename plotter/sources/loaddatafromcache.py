# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import numpy as np
from typing import Tuple

from .config import config


class LoadDataFromCacheSignal(QtCore.QObject):
    """
    Class containing the signal of the LoadDataFromCacheThread, see below
    """

    dataLoaded = QtCore.pyqtSignal(str, tuple, str, bool)




class LoadDataFromCacheThread(QtCore.QRunnable):


    def __init__(self, plotRef    : str,
                       dataDict   : np.ndarray,
                       xParamName : str,
                       yParamName : str,
                       zParamName : str,
                       lastUpdate : bool) -> None:
        """

        Parameters
        ----------
        """

        super(LoadDataFromCacheThread, self).__init__()

        self.plotRef    = plotRef
        self.dataDict   = dataDict
        self.xParamName = xParamName
        self.yParamName = yParamName
        self.zParamName = zParamName
        self.lastUpdate = lastUpdate
        
        self.signals = LoadDataFromCacheSignal() 



    @QtCore.pyqtSlot()
    def run(self) -> None:
        """
        """
        
        # It takes some iteration for the cache to start having data
        # We check here if there is data in the cache
        if self.zParamName=='':
            if len(self.dataDict[self.yParamName])==0:
                data = ([],[])
            else:
                d = self.dataDict[self.yParamName]
                data = (d[self.xParamName], d[self.yParamName])
        else:
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
                    data = (d[self.xParamName],
                            d[self.yParamName],
                            d[self.zParamName])
                    
                    # Find the effective x and y axis, see findXYIndex
                    xi, yi = self.findXYAxesIndex(data[1])
                    
                    # Shapped the 2d Data
                    if config['2dGridInterpolation']:
                        data = self.make_grid(data[xi], data[yi], data[2])
                    else:
                        data = self.shapeData2d(data[xi], data[yi], data[2])

        self.signals.dataLoaded.emit(self.plotRef, data, self.yParamName, self.lastUpdate)



    @staticmethod
    def findXYAxesIndex(y: np.ndarray) -> Tuple[int]:
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


    @staticmethod
    def shapeData2d(x: np.ndarray,
                    y: np.ndarray,
                    z: np.ndarray) -> Tuple[np.ndarray]:
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
            xx = x[:,0]
            
            # Create a bigger array containing sorted data in the same bases
            # New y axis containing all the previous y axes
            yd = np.nanmin(np.gradient(np.sort(y[-1])))
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

        # We filtered out the np.inf and -np.inf data and replaced them by np.nan
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