# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore
import numpy as np
import datetime
import pyqtgraph as pg
import pyqtgraph.functions as fn
import pyqtgraph.debug as debug
import sys 
sys.path.append('/daimyo/plotter/ui')

from config import config

class PlotApp(object):
    """
    Class to handle ploting in 1d.
    """


    def __init__(self):

        # Crosshair lines
        self.vLine = None
        self.hLine = None
        # self.crossHairRemove


        # Help deciding when drawing crosshair
        self.widget.installEventFilter(self)
        self.widgetHovered = False

        self.displayCrossHair = False

        # Connect signal
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)
        self.checkBoxCrossHair.stateChanged.connect(self.checkBoxCrossHairState)



    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Enter:
            self.widgetHovered = True
            return True
        elif event.type() == QtCore.QEvent.Leave:
            self.widgetHovered = False
        return False



    def checkBoxCrossHairState(self, b):
        """
        Method called when user click on the log checkBoxes.
        Modify the scale, linear or logarithmic, of the plotItem following
        which checkbox are checked.
        """
        
        if self.checkBoxCrossHair.isChecked():
            self.displayCrossHair = True
        else:
            self.displayCrossHair = False



    def isMouseOverView(self):
        """
        Return true is mouse is over the view of the plot
        """

        x = self.plotItem.getAxis('bottom').range
        y = self.plotItem.getAxis('left').range
        dx = (x[1]-x[0])/100.*config['plotShrinkActiveArea']
        dy = (y[1]-y[0])/100.*config['plotShrinkActiveArea']
        
        if self.mousePos[0] > x[0]+dx and self.mousePos[0] < x[1]-dx \
        and self.mousePos[1] > y[0]+dy and self.mousePos[1] < y[1]-dy \
        and self.widgetHovered:
            return True
        else:
            return False



    def mouseMoved(self, pos):
        """
        Handle the event when the mouse move hover the plotitem.
        Basically do two things:
            Display mouse coordinates
            Draw and undraw a crosshair instead of the mouse cursor
        """

        # Get mouse coordinates in "good" units
        pos = self.plotItem.vb.mapSceneToView(pos)
        # Save it
        self.mousePos = pos.x(), pos.y()

        # If mouse is over the viewbox, we change cursor in crosshair
        # If mouse is not over the viewbox, we change back the crosshair in cursor and remove the crosshair
        # Get displayed axes range
        if self.isMouseOverView():
            
            # Update the displayed mouse coordinates
            self.setMouseCoordinate()
            
            # Update cursor when hovering infiniteLine
            self.infiniteLineHovering()

            # Display the "crosshair"
            if self.displayCrossHair:
                self.crossHair()
        else:
            self.setMouseCoordinate(blank=True)
            
            if self.displayCrossHair:
                self.crossHair(remove=True)



    def setMouseCoordinate(self, blank=False):

        if blank:
            self.labelCoordinate.setText('')
        else:
            if self.plotType == '1d':

                if self.timestampXAxis:
                    x = datetime.datetime.utcfromtimestamp(self.mousePos[0]).strftime('%Y-%m-%d %H:%M:%S')
                    self.labelCoordinate.setText('x : {:}, y : {:.3e}'.format(x, self.mousePos[1]))
                else:
                    self.labelCoordinate.setText('x : {:.3e}, y : {:.3e}'.format(self.mousePos[0], self.mousePos[1]))
            elif self.plotType == '2d':

                n = np.abs(self.x-self.mousePos[0]).argmin()
                m = np.abs(self.y-self.mousePos[1]).argmin()
                z = self.z[n,m]

                self.labelCoordinate.setText('x : {:.3e}, y : {:.3e}, z : {:.3e}'.format(self.mousePos[0], self.mousePos[1], z))
            else:
                raise ValueError('plotType unknown')



    def infiniteLineHovering(self, defaultCursor=QtCore.Qt.ArrowCursor):
        """
        Called when user cursor if hovering a infiniteLine
        """


        # If we are hovering at least one inifiteLine, the cursor is modified
        for line in list(self.infiniteLines.values()):
            if line.mouseHovering:
                defaultCursor = QtCore.Qt.PointingHandCursor

        
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(defaultCursor))



    def crossHair(self, remove=False, defaultCursor=QtCore.Qt.ArrowCursor):
        """
        Handle the crossHair draw on the viewbox
        """

        # if the plot is a 2dplot, there is a possibility that the user mouse is
        # above an infiniteLine, if so, we remove the crosshair
        if self.plotType == '2d':
            for line in list(self.infiniteLines.values()):
                if line.mouseHovering:
                    remove = True

        # If 'vline' is None it means the crosshair hasn't been created
        if not remove and self.vLine is None:
            # Build the crosshair style

            if config['crossHairLineStyle'] == 'solid':
                lineStyle = QtCore.Qt.SolidLine 
            elif config['crossHairLineStyle'] == 'dashed':
                lineStyle = QtCore.Qt.DashLine  
            elif config['crossHairLineStyle'] == 'dotted':
                lineStyle = QtCore.Qt.DotLine  
            elif config['crossHairLineStyle'] == 'dashed-dotted':
                lineStyle = QtCore.Qt.DashDotLine
            else:
                raise ValueError('Config parameter "crossHairLineStyle" not recognize')

            
            penInfLine = pg.mkPen(config['crossHairLineColor'],
                                  width=config['crossHairLineWidth'],
                                  style=lineStyle)
                                  
            vLine = pg.InfiniteLine(angle=90, movable=False, pen=penInfLine)
            hLine = pg.InfiniteLine(angle=0,  movable=False, pen=penInfLine)
            self.plotItem.addItem(vLine, ignoreBounds=True)
            self.plotItem.addItem(hLine, ignoreBounds=True)
            self.vLine = vLine
            self.hLine = hLine

            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
            
        # If the crosshair exist, and we want to remove it
        elif remove and self.vLine is not None:

            self.plotItem.removeItem(self.vLine)
            self.plotItem.removeItem(self.hLine)
            self.vLine = None
            self.hLine = None

            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(defaultCursor))
            

        # Otherwise, we update its position
        elif self.vLine is not None:

            self.vLine.setPos(self.mousePos[0])
            self.hLine.setPos(self.mousePos[1])



# Replace current pyqtgraph function by a future release of pyqtgraph to 
# allow transparent pixel in the 2d plot. Usefull for non regular grid data
# https://github.com/pyqtgraph/pyqtgraph/pull/406/commits/70b76cd367eff01f70d8bb242b3daafaccba229d
def makeARGB(data, lut=None, levels=None, scale=None, useRGBA=False): 
    """ 
    Convert an array of values into an ARGB array suitable for building QImages,
    OpenGL textures, etc.
    
    Returns the ARGB array (unsigned byte) and a boolean indicating whether
    there is alpha channel data. This is a two stage process:
    
        1) Rescale the data based on the values in the *levels* argument (min, max).
        2) Determine the final output by passing the rescaled values through a
           lookup table.
   
    Both stages are optional.
    
    ============== ==================================================================================
    **Arguments:**
    data           numpy array of int/float types. If 
    levels         List [min, max]; optionally rescale data before converting through the
                   lookup table. The data is rescaled such that min->0 and max->*scale*::
                   
                      rescaled = (clip(data, min, max) - min) * (*scale* / (max - min))
                   
                   It is also possible to use a 2D (N,2) array of values for levels. In this case,
                   it is assumed that each pair of min,max values in the levels array should be 
                   applied to a different subset of the input data (for example, the input data may 
                   already have RGB values and the levels are used to independently scale each 
                   channel). The use of this feature requires that levels.shape[0] == data.shape[-1].
    scale          The maximum value to which data will be rescaled before being passed through the 
                   lookup table (or returned if there is no lookup table). By default this will
                   be set to the length of the lookup table, or 255 if no lookup table is provided.
    lut            Optional lookup table (array with dtype=ubyte).
                   Values in data will be converted to color by indexing directly from lut.
                   The output data shape will be input.shape + lut.shape[1:].
                   Lookup tables can be built using ColorMap or GradientWidget.
    useRGBA        If True, the data is returned in RGBA order (useful for building OpenGL textures). 
                   The default is False, which returns in ARGB order for use with QImage 
                   (Note that 'ARGB' is a term used by the Qt documentation; the *actual* order 
                   is BGRA).
    ============== ==================================================================================
    """
    profile = debug.Profiler()
    if data.ndim not in (2, 3):
        raise TypeError("data must be 2D or 3D")
    if data.ndim == 3 and data.shape[2] > 4:
        raise TypeError("data.shape[2] must be <= 4")
    
    if lut is not None and not isinstance(lut, np.ndarray):
        lut = np.array(lut)
    
    if levels is None:
        # automatically decide levels based on data dtype
        if data.dtype.kind == 'u':
            levels = np.array([0, 2**(data.itemsize*8)-1])
        elif data.dtype.kind == 'i':
            s = 2**(data.itemsize*8 - 1)
            levels = np.array([-s, s-1])
        elif data.dtype.kind == 'b':
            levels = np.array([0,1])
        else:
            raise Exception('levels argument is required for float input types')
    if not isinstance(levels, np.ndarray):
        levels = np.array(levels)
    if levels.ndim == 1:
        if levels.shape[0] != 2:
            raise Exception('levels argument must have length 2')
    elif levels.ndim == 2:
        if lut is not None and lut.ndim > 1:
            raise Exception('Cannot make ARGB data when both levels and lut have ndim > 2')
        if levels.shape != (data.shape[-1], 2):
            raise Exception('levels must have shape (data.shape[-1], 2)')
    else:
        raise Exception("levels argument must be 1D or 2D (got shape=%s)." % repr(levels.shape))

    profile()

    # Decide on maximum scaled value
    if scale is None:
        if lut is not None:
            scale = lut.shape[0] - 1
        else:
            scale = 255.

    # Decide on the dtype we want after scaling
    if lut is None:
        dtype = np.ubyte
    else:
        dtype = np.min_scalar_type(lut.shape[0]-1)

    # awkward, but fastest numpy native nan evaluation
    nanMask = None
    if data.dtype.kind == 'f' and np.isnan(data.min()):
        nanMask = np.isnan(data)
    # Apply levels if given
    if levels is not None:
        if isinstance(levels, np.ndarray) and levels.ndim == 2:
            # we are going to rescale each channel independently
            if levels.shape[0] != data.shape[-1]:
                raise Exception("When rescaling multi-channel data, there must be the same number of levels as channels (data.shape[-1] == levels.shape[0])")
            newData = np.empty(data.shape, dtype=int)
            for i in range(data.shape[-1]):
                minVal, maxVal = levels[i]
                if minVal == maxVal:
                    maxVal += 1e-16
                newData[...,i] = fn.rescaleData(data[...,i], scale/(maxVal-minVal), minVal, dtype=dtype)
            data = newData
        else:
            # Apply level scaling unless it would have no effect on the data
            minVal, maxVal = levels
            if minVal != 0 or maxVal != scale:
                if minVal == maxVal:
                    maxVal += 1e-16
                data = fn.rescaleData(data, scale/(maxVal-minVal), minVal, dtype=dtype)

    profile()
    # apply LUT if given
    if lut is not None:
        data = fn.applyLookupTable(data, lut)
    else:
        if data.dtype is not np.ubyte:
            data = np.clip(data, 0, 255).astype(np.ubyte)

    profile()

    # this will be the final image array
    imgData = np.empty(data.shape[:2]+(4,), dtype=np.ubyte)

    profile()

    # decide channel order
    if useRGBA:
        order = [0,1,2,3] # array comes out RGBA
    else:
        order = [2,1,0,3] # for some reason, the colors line up as BGR in the final image.
        
    # copy data into image array
    if data.ndim == 2:
        # This is tempting:
        #   imgData[..., :3] = data[..., np.newaxis]
        # ..but it turns out this is faster:
        for i in range(3):
            imgData[..., i] = data
    elif data.shape[2] == 1:
        for i in range(3):
            imgData[..., i] = data[..., 0]
    else:
        for i in range(0, data.shape[2]):
            imgData[..., i] = data[..., order[i]] 
        
    profile()
    
    # add opaque alpha channel if needed
    if data.ndim == 2 or data.shape[2] == 3:
        alpha = False
        imgData[..., 3] = 255
    else:
        alpha = True

    # apply nan mask through alpha channel
    if nanMask is not None:
        alpha = True
        imgData[nanMask, 3] = 0

    profile()
    return imgData, alpha


fn.makeARGB = makeARGB


# Add functions from future pyqtgraph release to easyli use DateAxisItem
def setAxisItems(self, axisItems=None):
    """
    Place axis items as given by `axisItems`. Initializes non-existing axis items.
    
    ==============  ==========================================================================================
    **Arguments:**
    *axisItems*     Optional dictionary instructing the PlotItem to use pre-constructed items
                    for its axes. The dict keys must be axis names ('left', 'bottom', 'right', 'top')
                    and the values must be instances of AxisItem (or at least compatible with AxisItem).
    ==============  ==========================================================================================
    """
    
            
    if axisItems is None:
        axisItems = {}
    
    # Array containing visible axis items
    # Also containing potentially hidden axes, but they are not touched so it does not matter
    visibleAxes = ['left', 'bottom']
    visibleAxes.append(axisItems.keys()) # Note that it does not matter that this adds
                                            # some values to visibleAxes a second time
    
    for k, pos in (('top', (1,1)), ('bottom', (3,1)), ('left', (2,0)), ('right', (2,2))):
        if k in self.axes:
            if k not in axisItems:
                continue # Nothing to do here
            
            # Remove old axis
            oldAxis = self.axes[k]['item']
            self.layout.removeItem(oldAxis)
            oldAxis.scene().removeItem(oldAxis)
            oldAxis.unlinkFromView()
        
        # Create new axis
        if k in axisItems:
            axis = axisItems[k]
            if axis.scene() is not None:
                if axis != self.axes[k]["item"]:
                    raise RuntimeError("Can't add an axis to multiple plots.")
        else:
            axis = AxisItem(orientation=k, parent=self)
        
        # Set up new axis
        axis.linkToView(self.vb)
        self.axes[k] = {'item': axis, 'pos': pos}
        self.layout.addItem(axis, *pos)
        axis.setZValue(-1000)
        axis.setFlag(axis.ItemNegativeZStacksBehindParent)
        
        axisVisible = k in visibleAxes
        self.showAxis(k, axisVisible)



def unlinkFromView(self):
    """Unlink this axis from a ViewBox."""
    oldView = self.linkedView()
    self._linkedView = None
    if self.orientation in ['right', 'left']:
        if oldView is not None:
            oldView.sigYRangeChanged.disconnect(self.linkedViewChanged)
    else:
        if oldView is not None:
            oldView.sigXRangeChanged.disconnect(self.linkedViewChanged)

    if oldView is not None:
        oldView.sigResized.disconnect(self.linkedViewChanged)



pg.PlotItem.setAxisItems = setAxisItems
pg.AxisItem.unlinkFromView = unlinkFromView
