# This Python file uses the following encoding: utf-8

from PyQt5 import QtGui, QtCore
import numpy as np
import pyqtgraph.functions as fn
import pyqtgraph.debug as debug
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph.Point import Point
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients # List of colormaps
from pyqtgraph.colormap import ColorMap
from pyqtgraph import getConfigOption


class PColorMeshItem(GraphicsObject):
    """
    **Bases:** :class:`GraphicsObject <pyqtgraph.GraphicsObject>`
    """



    sigImageChanged = QtCore.Signal()
    sigRemoveRequested = QtCore.Signal(object)  # self; emitted when 'remove' is selected from context menu



    def __init__(self, *args, **kwargs):
        """
        Create a pseudocolor plot with convex polygons.

        Call signature:

        PColorMeshItem([x, y,] z, **kwargs)

        x and y can be used to specify the corners of the quadrilaterals.
        z must be used to specified to color of the quadrilaterals.

        Parameters
        ----------
        x, y : np.ndarray, optional, default None
            2D array containing the coordinates of the polygons
        z : np.ndarray
            2D array containing the value which will be maped into the polygons
            colors.
            If x and y is None, the polygons will be displaced on a grid
            otherwise x and y will be used as polygons vertices coordinates as::

                (x[i+1, j], y[i+1, j])           (x[i+1, j+1], y[i+1, j+1])
                                    +---------+
                                    | z[i, j] |
                                    +---------+
                    (x[i, j], y[i, j])           (x[i, j+1], y[i, j+1])
            "ASCII from: https://matplotlib.org/3.2.1/api/_as_gen/
                         matplotlib.pyplot.pcolormesh.html".
        cmap : str, default 'viridis
            Colormap used to map the z value to colors.
        edgecolors : dict , default None
            The color of the edges of the polygons.
            Default None means no edges.
            The dict may contains any arguments accepted by :func:`mkColor() <pyqtgraph.mkColor>.
            Example:
                mkPen(color='w', width=2)
        """
        GraphicsObject.__init__(self)

        self.qpicture = None  ## rendered picture for display
        self.lut = None
        self.levels = None  ## [min, max] or [[redMin, redMax], ...]
        self.autoDownsample = False


        self.axisOrder = getConfigOption('imageAxisOrder')
        
        if 'edgecolors' in kwargs.keys():
            self.edgecolors = kwargs['edgecolors']
        else:
            self.edgecolors = None
        
        if 'cmap' in kwargs.keys():
            if kwargs['cmap'] in Gradients.keys():
                self.cmap = kwargs['cmap']
            else:
                raise NameError('Undefined colormap, should be one of the following: '+', '.join(['"'+i+'"' for i in Gradients.keys()])+'.')
        else:
            self.cmap = 'viridis'
        
        # If some data have been sent we directly display it
        if len(args)>0:
            self.setData(*args)



    def _prepareData(self, args):
        """
        Check the shape of the data.
        Return a set of 2d array x, y, z ready to be used to draw the picture.
        """

        # # User didn't specified data
        # if len(args)==0:

        #     self.x = None
        #     self.y = None
        #     self.z = None
            
        # User only specified z
        if len(args)==1:
            # If x and y is None, the polygons will be displaced on a grid
            x = np.arange(0, args[0].shape[0]+1, 1)
            y = np.arange(0, args[0].shape[1]+1, 1)
            self.x, self.y = np.meshgrid(x, y, indexing='ij')
            self.z = args[0]

        # User specified x, y, z
        elif len(args)==3:

            # Shape checking
            if args[0].shape[0] != args[2].shape[0]+1 or args[0].shape[1] != args[2].shape[1]+1:
                raise ValueError('The dimension of x should be one greater than the one of z')
            
            if args[1].shape[0] != args[2].shape[0]+1 or args[1].shape[1] != args[2].shape[1]+1:
                raise ValueError('The dimension of y should be one greater than the one of z')
        
            self.x = args[0]
            self.y = args[1]
            self.z = args[2]

        else:
            ValueError('Data must been sent as (z) or (x, y, z)')



    def setData(self, *args, autoLevels=None):
        """
        Set the data to be drawn.

        Parameters
        ----------
        x, y : np.ndarray, optional, default None
            2D array containing the coordinates of the polygons
        z : np.ndarray
            2D array containing the value which will be maped into the polygons
            colors.
            If x and y is None, the polygons will be displaced on a grid
            otherwise x and y will be used as polygons vertices coordinates as:

            (x[i+1, j], y[i+1, j])           (x[i+1, j+1], y[i+1, j+1])
                                +---------+
                                | z[i, j] |
                                +---------+
                (x[i, j], y[i, j])           (x[i, j+1], y[i, j+1])
            "ASCII from: https://matplotlib.org/3.2.1/api/_as_gen/
                         matplotlib.pyplot.pcolormesh.html".

        """




        # Prepare data
        cd = self._prepareData(args)

        # Has the view bounds changed
        shapeChanged = False
        if self.qpicture is None:
            shapeChanged = True

        if len(args)==0 and self.z is None:
            print('return')
            return
        elif len(args)==0:
            print('x', self.x)
            pass
        elif len(args)==1:
            if args[0].shape[0] != self.x[:,1][-1] or args[0].shape[1] != self.y[0][-1]:
                shapeChanged = True
        elif len(args)==3:
            if np.any(self.x != args[0]) or np.any(self.y != args[1]):
                shapeChanged = True

        print(self.z.shape)

        if self.autoDownsample:
            print('Downsampling')
            # reduce dimensions of image based on screen resolution
            o = self.mapToDevice(QtCore.QPointF(0,0))
            x = self.mapToDevice(QtCore.QPointF(1,0))
            y = self.mapToDevice(QtCore.QPointF(0,1))

            print(o, x, y)
            # Check if graphics view is too small to render anything
            if o is None or x is None or y is None:
                return

            w = Point(x-o).length()
            h = Point(y-o).length()
            if w==0 or h==0:
                self.qpicture = None
                return
            xds = max(1, int(1.0 / w))
            yds = max(1, int(1.0 / h))
            axes = [1, 0] if self.axisOrder=='row-major' else [0, 1]
            z = fn.downsample(self.z, xds, axis=axes[0])
            z = fn.downsample(z, yds, axis=axes[1])
            self._lastDownsample = (xds, yds)

            # Check if downsampling reduced the z size to zero due to inf values.
            if z.size==0:
                return
        else:
            z = self.z

        print(z.shape)


        profile = debug.Profiler()

        self.qpicture = QtGui.QPicture()
        p = QtGui.QPainter(self.qpicture)
        
        # We set the pen of all polygons once
        if self.edgecolors is None:
            p.setPen(QtGui.QColor(0, 0, 0, 0))
        else:
            p.setPen(fn.mkPen(self.edgecolors))
        ## Prepare colormap
        # First we get the LookupTable
        pos   = [i[0] for i in Gradients[self.cmap]['ticks']]
        color = [i[1] for i in Gradients[self.cmap]['ticks']]
        cmap  = ColorMap(pos, color)
        lut   = cmap.getLookupTable(0.0, 1.0, 256)
        # Second we associate each z value, that we normalize, to the lut
        norm  = z - z.min()
        norm = norm/norm.max()
        norm  = (norm*(len(lut)-1)).astype(int)
        
        # Go through all the data and draw the polygons accordingly
        for xi in range(z.shape[0]):
            for yi in range(z.shape[1]):
                
                # Set the color of the polygon first
                # print(xi, yi, norm[xi][yi])
                c = lut[norm[xi][yi]]
                p.setBrush(QtGui.QColor(c[0], c[1], c[2]))

                polygon = QtGui.QPolygonF(
                    [QtCore.QPointF(self.x[xi][yi],     self.y[xi][yi]),
                     QtCore.QPointF(self.x[xi+1][yi],   self.y[xi+1][yi]),
                     QtCore.QPointF(self.x[xi+1][yi+1], self.y[xi+1][yi+1]),
                     QtCore.QPointF(self.x[xi][yi+1],   self.y[xi][yi+1])]
                )

                # DrawConvexPlygon is faster
                p.drawConvexPolygon(polygon)


        p.end()
        self.update()

        if shapeChanged:
            self.informViewBoundsChanged()



    def paint(self, p, *args):
        profile = debug.Profiler()
        if self.z is None:
            return

        profile('p.drawPicture')
        p.drawPicture(0, 0, self.qpicture)



    def setBorder(self, b):
        self.border = fn.mkPen(b)
        self.update()



    def width(self):
        if self.x is None:
            return None
        return np.max(self.x)



    def height(self):
        if self.y is None:
            return None
        return np.max(self.y)



    def boundingRect(self):
        if self.qpicture is None:
            return QtCore.QRectF(0., 0., 0., 0.)
        return QtCore.QRectF(0., 0., float(self.width()), float(self.height()))



    def setLookupTable(self, lut, update=True):
        """

        """
        if lut is not self.lut:
            self.lut = lut
            self._effectiveLut = None
            if update:
                self.updateImage()

    def updateImage(self, *args, **kargs):
        ## used for re-rendering qimage from self.image.

        ## can we make any assumptions here that speed things up?
        ## dtype, range, size are all the same?
        defaults = {
            'autoLevels': False,
        }
        defaults.update(kargs)
        return self.setData(*args, **defaults)


    def setLevels(self, levels, update=True):
        """
        Set image scaling levels. Can be one of:

        * [blackLevel, whiteLevel]
        * [[minRed, maxRed], [minGreen, maxGreen], [minBlue, maxBlue]]

        Only the first format is compatible with lookup tables. See :func:`makeARGB <pyqtgraph.makeARGB>`
        for more details on how levels are applied.
        """
        if levels is not None:
            levels = np.asarray(levels)
        if not fn.eq(levels, self.levels):
            self.levels = levels
            self._effectiveLut = None
            if update:
                self.updateImage()


    def getHistogram(self, bins='auto', step='auto', perChannel=False, targetImageSize=200,
                     targetHistogramSize=500, **kwds):
        """Returns x and y arrays containing the histogram values for the current image.
        For an explanation of the return format, see numpy.histogram().

        The *step* argument causes pixels to be skipped when computing the histogram to save time.
        If *step* is 'auto', then a step is chosen such that the analyzed data has
        dimensions roughly *targetImageSize* for each axis.

        The *bins* argument and any extra keyword arguments are passed to
        np.histogram(). If *bins* is 'auto', then a bin number is automatically
        chosen based on the image characteristics:

        * Integer images will have approximately *targetHistogramSize* bins,
          with each bin having an integer width.
        * All other types will have *targetHistogramSize* bins.

        If *perChannel* is True, then the histogram is computed once per channel
        and the output is a list of the results.

        This method is also used when automatically computing levels.
        """
        if self.z is None or self.z.size==0:
            return None, None
        if step=='auto':
            step = (max(1, int(np.ceil(self.z.shape[0] / targetImageSize))),
                    max(1, int(np.ceil(self.z.shape[1] / targetImageSize))))
        if np.isscalar(step):
            step = (step, step)
        stepData = self.z[::step[0], ::step[1]]

        if isinstance(bins, str) and bins=='auto':
            mn = np.nanmin(stepData)
            mx = np.nanmax(stepData)
            if mx==mn:
                # degenerate image, arange will fail
                mx += 1
            if np.isnan(mn) or np.isnan(mx):
                # the data are all-nan
                return None, None
            if stepData.dtype.kind in "ui":
                # For integer data, we select the bins carefully to avoid aliasing
                step = np.ceil((mx-mn) / 500.)
                bins = np.arange(mn, mx+1.01*step, step, dtype=np.int)
            else:
                # for float data, let numpy select the bins.
                bins = np.linspace(mn, mx, 500)

            if len(bins)==0:
                bins = [mn, mx]

        kwds['bins'] = bins

        if perChannel:
            hist = []
            for i in range(stepData.shape[-1]):
                stepChan = stepData[..., i]
                stepChan = stepChan[np.isfinite(stepChan)]
                h = np.histogram(stepChan, **kwds)
                hist.append((h[1][:-1], h[0]))
            return hist
        else:
            stepData = stepData[np.isfinite(stepData)]
            hist = np.histogram(stepData, **kwds)
            return hist[1][:-1], hist[0]