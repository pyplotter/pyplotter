from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
from typing import Union, Tuple, Optional, List, Dict
from scipy.ndimage import sobel
from math import atan2
import uuid

from .widgetPlot2dui import Ui_Dialog
from ....sources import palettes # File copy from bokeh: https://github.com/bokeh/bokeh/blob/7cc500601cdb688c4b6b2153704097f3345dd91c/bokeh/palettes.py
from ....sources.config import loadConfigCurrent
from ....sources.functions import getCurveColorIndex, hex_to_rgba
from ....sources.pyqtgraph import pg
from ....sources.functions import parse_number
from ..widgetPlotContainer import WidgetPlotContainer
from .widgetHistogram import WidgetHistogram

from .groupBoxFit import GroupBoxFit


class WidgetPlot2d(QtWidgets.QDialog):
    """
    Class to handle ploting in 2d.
    """

    signalRemovePlotFromRef      = QtCore.pyqtSignal(str, str)
    signal2MainWindowClosePlot   = QtCore.pyqtSignal(str)
    signalRemovePlotRef          = QtCore.pyqtSignal(str)

    signalClose1dPlot              = QtCore.pyqtSignal(str)
    signalClose2dPlot            = QtCore.pyqtSignal(str, str)

    signal2MainWindowAddPlot     = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)


    signalUpdateCurve  = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
    signalRemoveCurve  = QtCore.pyqtSignal(str, str)

    ## Fit
    # Update the 2d fit selected data
    signalUpdate2dFitData = QtCore.pyqtSignal(np.ndarray, np.ndarray, np.ndarray)
    signalUpdate2dFitResult = QtCore.pyqtSignal(str, np.ndarray, np.ndarray, np.ndarray)


    # Signal towards the histogram
    signalIsoCurve = QtCore.pyqtSignal(bool, pg.ImageView)


    def __init__(self, x              : np.ndarray,
                       y              : np.ndarray,
                       z              : np.ndarray,
                       title          : str,
                       xLabelText     : str,
                       xLabelUnits    : str,
                       yLabelText     : str,
                       yLabelUnits    : str,
                       zLabelText     : str,
                       zLabelUnits    : str,
                       windowTitle    : str,
                       runId          : int,
                       curveId        : str,
                       plotRef        : str,
                       databaseAbsPath: str,
                       dialogX         : Optional[int]=None,
                       dialogY         : Optional[int]=None,
                       dialogWidth     : Optional[int]=None,
                       dialogHeight    : Optional[int]=None) -> None:
        """
        Class handling the plot of 2d data, i.e. colormap.
        Since pyqtgraph does not handle non regular image, there could be funny
        stuff happening.
        The class allows interactivity with the colormap in particular some data
        treatment launch 1dplot through the main app to keep plot references
        updated, see WidgetPlot1d.

        Parameters
        ----------
        x : np.ndarray
            Data along the x axis, 1d array.
        y : np.ndarray
            Data along the y axis, 1d array.
        z : np.ndarray
            Data along the z axis, 2d array.
        title : str
            Plot title.
        xLabel : str
            Label along the x axis.
        yLabel : str
            Label along the y axis.
        zLabel : str
            Label along the z axis.
        windowTitle : str
            Window title.
        runId : int
            Id of the QCoDeS run.
        cleanCheckBox : Callable[[str, str, int, Union[str, list]], None]
            Function called when the window is closed.
        plotRef : str
            Reference of the plot
        addPlot : Callable
            Function from the mainApp used to launched 1d plot and keep plot
            reference updated.
        removePlot : Callable
            Function from the mainApp used to remove 1d plot and keep plot
            reference updated.
        getPlotFromRef : Callable
            Function from the mainApp used to access the different plots.
        parent : , optional
        """

        # Set parent to None to have "free" qdialog
        super(WidgetPlot2d, self).__init__(None)

        # Build the UI
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.plotWidgetContainer = WidgetPlotContainer(self)

        self._allowClosing = False

        self.config = loadConfigCurrent()

        # Shortcut to access the plot widget and item
        self.plotWidget = self.plotWidgetContainer.plotWidget
        self.plotItem = self.plotWidget.getPlotItem()

        # Must be set on False, see
        # https://github.com/pyqtgraph/pyqtgraph/issues/1371
        self.plotWidget.useOpenGL(False)

        # Allow resize of the plot window
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)
        self.plotType = '2d'

        self.xData           = x
        self.yData           = y
        self.zData           = z
        self.xDataRef        = x # To keep track of all operation done on the z data
        self.yDataRef        = y # To keep track of all operation done on the z data
        self.zDataRef        = z # To keep track of all operation done on the z data
        self._xLabelText     = xLabelText
        self._xLabelUnits    = xLabelUnits
        self._yLabelText     = yLabelText
        self._yLabelUnits    = yLabelUnits
        self._zLabelText     = zLabelText
        self._zLabelUnits    = zLabelUnits
        self.title           = title
        self._windowTitle    = windowTitle
        self.runId           = runId
        self.curveId         = curveId
        self.plotRef         = plotRef
        self.databaseAbsPath = databaseAbsPath


        # Will keep track of the axes swapping
        self._isAxesSwapped = False

        # Store references to infiniteLines creating by data slicing
        self.sliceItems = {}
        self.sliceOrientation = 'vertical'

        # Keep track of the sub-interaction plots launched fron that plot
        self.interactionRefs: Dict[str, dict] = {}

        # Create a Image item to host the image view
        self.imageItem = pg.ImageItem(image=np.array([[0,0],[0,0]]))
        self.imageItem.autoDownsample = self.config['2dDownSampling']
        self.imageView = pg.ImageView(imageItem=self.imageItem)

        # Embed the plot item in the graphics layout
        self.plotItem.vb.addItem(self.imageItem)

        # Allow ticklabels to be changed
        font=QtGui.QFont()
        font.setPixelSize(self.config['tickLabelFontSize'])
        self.plotItem.getAxis('bottom').setTickFont(font)
        self.plotItem.getAxis('left').setTickFont(font)
        self.plotItem.getAxis('bottom').setPen(self.config['styles'][self.config['style']]['pyqtgraphxAxisTicksColor'])
        self.plotItem.getAxis('left').setPen(self.config['styles'][self.config['style']]['pyqtgraphyAxisTicksColor'])
        self.plotItem.getAxis('bottom').setTextPen(self.config['styles'][self.config['style']]['pyqtgraphxAxisTickLabelsColor'])
        self.plotItem.getAxis('left').setTextPen(self.config['styles'][self.config['style']]['pyqtgraphyAxisTickLabelsColor'])


        # Histogram of the imageItem colormap
        self.hist = WidgetHistogram(parent=self.ui.horizontalLayout,
                                    imageItem=self.imageItem,
                                    zLabelText=zLabelText,
                                    zLabelUnits=zLabelUnits)
        self.hist.setLevels(min=z[~np.isnan(z)].min(),
                            max=z[~np.isnan(z)].max())
        self.signalIsoCurve.connect(self.hist.slotIsoCurve)

        self.setImageView()


        # Axes label
        self.plotItem.setTitle(title=title, color=self.config['styles'][self.config['style']]['pyqtgraphTitleTextColor'])
        self.plotItem.showGrid(x=True, y=True)
        self.plotItem.setLabel(axis='bottom',
                               text=self._xLabelText,
                               units=self._xLabelUnits,
                               **{'color'     : self.config['styles'][self.config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(self.config['axisLabelFontSize'])+'pt'})
        self.plotItem.setLabel(axis='left',
                               text=self._yLabelText,
                               units=self._yLabelUnits,
                               **{'color'     : self.config['styles'][self.config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(self.config['axisLabelFontSize'])+'pt'})

        self.setWindowTitle(windowTitle)


        # Initialize internal widget
        # self.initGroupBoxFit()

        self.setStyleSheet("background-color: "+str(self.config['styles'][self.config['style']]['dialogBackgroundColor'])+";")
        self.setStyleSheet("color: "+str(self.config['styles'][self.config['style']]['dialogTextColor'])+";")


        # # Connect UI
        self.ui.checkBoxFindSlope.clicked.connect(self.cbFindSlope)
        self.ui.checkBoxDrawIsoCurve.clicked.connect(self.isoCurveClicked)
        self.ui.checkBoxMaximum.clicked.connect(self.checkBoxMaximumClicked)
        self.ui.checkBoxMinimum.clicked.connect(self.checkBoxMinimumClicked)
        self.ui.checkBoxSwapxy.clicked.connect(self.checkBoxSwapxyState)
        self.ui.checkBoxAspectEqual.clicked.connect(self.checkBoxAspectEqualState)
        self.ui.checkBoxSubtractAverageX.clicked.connect(self.zDataTransformation)
        self.ui.checkBoxSubtractAverageY.clicked.connect(self.zDataTransformation)
        self.ui.spinBoxSubtractPolyX.valueChanged.connect(self.zDataTransformation)
        self.ui.spinBoxSubtractPolyY.valueChanged.connect(self.zDataTransformation)
        self.ui.checkBoxUnwrapX.clicked.connect(self.zDataTransformation)
        self.ui.checkBoxUnwrapY.clicked.connect(self.zDataTransformation)
        self.ui.pushButton3d.clicked.connect(self.launched3d)
        self.plotItem.scene().sigMouseClicked.connect(self.plotItemdoubleClick)
        self.ui.radioButtonSliceSingleAny.toggled.connect(self.radioBoxSliceChanged)
        self.ui.radioButtonSliceSingleHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.ui.radioButtonSliceSingleVertical.toggled.connect(self.radioBoxSliceChanged)
        self.ui.radioButtonSliceAveragedHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.ui.radioButtonSliceAveragedVertical.toggled.connect(self.radioBoxSliceChanged)


        # UI for the derivative combobox
        for label in self.config['plot2dDerivative']:
            self.ui.comboBoxDerivative.addItem(label)
        self.ui.comboBoxDerivative.activated.connect(self.zDataTransformation)


        self.resize(*self.config['dialogWindowSize'])

        self.show()


        # Connect the button to get a screenshot of the plot
        # Done here since we need a reference of the plotWidget
        self.ui.qButtonCopy.clicked.connect(lambda: self.ui.qButtonCopy.clicked_(self.plotWidget))
        # For unknown reason, I have to initialize the text here...
        self.ui.qButtonCopy.setText(self.ui.qButtonCopy._text)

        self.ui.qCheckBoxCrossHair.signalAddCrossHair.connect(self.plotWidget.slotAddCrossHair)


        # if the dialog size was given (usually meaning a live plot is done)
        if dialogWidth is not None and dialogHeight is not None:
            self.adjustSize()
            frameHeight = self.frameGeometry().height()-self.height()
            frameWidth = self.frameGeometry().width()-self.width()
            self.resize(dialogWidth-frameWidth, dialogHeight-frameHeight)
            self.move(dialogX, dialogY)



    ####################################
    #
    #           Method to close stuff
    #
    ####################################



    def closeEvent(self, evnt: QtGui.QCloseEvent) -> None:

        # # We catch the close event and ignore it
        if not self._allowClosing:
            evnt.ignore()

        # for sliceOrientation, interaction in self.interactionRefs.items():
        #         interaction['plotRef']
            # if curveId in list(self.curves.keys()):
            #     interaction['dialog'].close()

        # All the closing procedure of the plot is handle in the MainWindow
        self.signalClose2dPlot.emit(self.plotRef,
                                    self.curveId)



    ####################################
    #
    #           Method to launch a 3d plot
    #
    ####################################



    def launched3d(self):
        """
        Called when used click on pushButton3d.
        Launch a new pyqtgraph window with a OpenGL surfacePlotItem.

        This is just a funny feature.
        """

        ## Create a GL View widget to display data
        import pyqtgraph.opengl as gl
        pg.setConfigOption('background', (0, 0, 0))
        self.widget3d = gl.GLViewWidget()
        self.widget3d.show()
        self.widget3d.setWindowTitle(self._windowTitle)
        self.widget3d.setCameraPosition(distance=3)

        # Linearly scale all data from 0 to 1
        x = (self.xData - np.nanmin(self.xData))/(np.nanmax(self.xData) - np.nanmin(self.xData))
        y = (self.yData - np.nanmin(self.yData))/(np.nanmax(self.yData) - np.nanmin(self.yData))
        z = (self.zData - np.nanmin(self.zData))/(np.nanmax(self.zData) - np.nanmin(self.zData))

        p = gl.GLSurfacePlotItem(x=x,
                                 y=y,
                                 z=z,
                                 shader='shaded',
                                 smooth=False)
        self.widget3d.addItem(p)

        pg.setConfigOption('background', None)


    ####################################
    #
    #           livePlot
    #
    ####################################



    def updatePlotData(self, x: np.ndarray,
                             y: np.ndarray,
                             z: np.ndarray) -> None:
        """
        Update the displayed colormap

        Parameters
        ----------
        x : np.ndarray
            Data along the x axis, 1d array.
        y : np.ndarray
            Data along the y axis, 1d array.
        z : np.ndarray
            Data along the z axis, 2d array.
        """

        self.xData    = x
        self.yData    = y
        self.zData    = z
        self.xDataRef = x
        self.yDataRef = y
        self.zDataRef = z

        self.zDataTransformation()

        if self._isAxesSwapped:
            self.updateImageItem(self.yDataRef, self.xDataRef, self.imageView.image.T)




    ####################################
    #
    #           Method to set, update the image
    #
    ####################################



    def setImageView(self) -> None:
        """
        Set the image using the current x, y and z attributes of the object.
        If there is more than one column or row, recalculate the axis to center
        the colored rectangles.
        """
        # If there is more than one column, we center the colored rectangles
        if len(self.xData)>1:
            dx = np.gradient(self.xData)/2.
            x = np.linspace(self.xData[0]-dx[0], self.xData[-1]+dx[-1], len(self.xData))
        else:
            x = self.xData

        if len(self.yData)>1:
            dy = np.gradient(self.yData)/2.
            y = np.linspace(self.yData[0]-dy[0], self.yData[-1]+dy[-1], len(self.yData))
        else:
            y = self.yData

        # Set the image view
        xScale = (x[-1]-x[0])/len(x)
        yScale = (y[-1]-y[0])/len(y)
        self.imageView.setImage(img   = self.zData,
                                pos   = [x[0], y[0]],
                                scale = [xScale, yScale])
        self.imageView.view.invertY(False)
        self.imageView.view.setAspectLocked(False)
        self.imageView.autoRange()



    def updateImageItem(self, x: np.ndarray,
                              y: np.ndarray,
                              z: np.ndarray) -> None:
        """
        Update the displayed colormap.

        Parameters
        ----------
        x : np.ndarray
            Data along the x axis, 1d array.
        y : np.ndarray
            Data along the y axis, 1d array.
        z : np.ndarray
            Data along the z axis, 2d array.
        """

        self.xData  = x
        self.yData  = y
        self.zData  = z

        self.hist.setLevels(min=z[~np.isnan(z)].min(),
                            max=z[~np.isnan(z)].max())
        self.setImageView()

        self.interactionUpdateAll()



    ####################################
    #
    #           Method to related to display
    #
    ####################################



    def updatePlotProperty(self, prop: str,
                                 value: str) -> None:

        if prop=='plotTitle':
            self.plotItem.setTitle(title=value)



    def checkBoxAspectEqualState(self, b: int) -> None:
        """When user wants equal scaling on the x and y axis.

        Args:
            b (int): State of the box.
        """

        if self.ui.checkBoxAspectEqual.isChecked():
            self.plotItem.vb.setAspectLocked(True)
        else:
            self.plotItem.vb.setAspectLocked(False)



    def checkBoxSwapxyState(self, b: int) -> None:
        """
        When user want to swap the x and y axis

        Parameters
        ----------
        b : int
            State of the box.
        """


        # If user wants to swap axes
        if self.ui.checkBoxSwapxy.isChecked():
            # If axes are not already swapped
            if not self._isAxesSwapped:

                self.plotItem.setLabel(axis='bottom',
                                       text=self._yLabelText,
                                       units=self._yLabelUnits)
                self.plotItem.setLabel(axis='left',
                                       text=self._xLabelText,
                                       units=self._xLabelUnits)

                self.updateImageItem(self.yDataRef, self.xDataRef, self.imageView.image.T)
                self._isAxesSwapped = True
        # If user wants to unswap axes
        else:
            # If axes have been already swapped
            if self._isAxesSwapped:

                self.plotItem.setLabel(axis='bottom',
                                       text=self._xLabelText,
                                       units=self._xLabelUnits)
                self.plotItem.setLabel(axis='left',
                                       text=self._yLabelText,
                                       units=self._yLabelUnits)

                self.updateImageItem(self.xDataRef, self.yDataRef, self.imageView.image.T)
                self._isAxesSwapped = False



    ####################################
    #
    #           Method related to data slicing
    #
    ####################################



    def getCurrentSliceItem(self) -> str:
        """
        Return the type of slice the user want
        """

        if self.ui.radioButtonSliceSingleHorizontal.isChecked() or self.ui.radioButtonSliceSingleVertical.isChecked():
            sliceItem = 'InfiniteLine'
        elif self.ui.radioButtonSliceSingleAny.isChecked():
            sliceItem = 'LineSegmentROI'
        else:
            sliceItem = 'LinearRegionItem'

        return sliceItem



    def getSliceItemOrientation(self, sliceItem: Union[pg.InfiniteLine, pg.LineSegmentROI, pg.LinearRegionItem]) -> str:
        """
        Return the orientation of the sliceItem.

        Parameters
        ----------
        sliceItem : sliceItem currently being dragged.

        Return
        ------
        orientation : str
            Either "horizontal",  "vertical" or "any"
        """

        if isinstance(sliceItem, pg.InfiniteLine):
            if int(sliceItem.angle%180)==0:
                lineOrientation = 'horizontal'
            else:
                lineOrientation = 'vertical'
        elif isinstance(sliceItem, pg.LinearRegionItem):
            lineOrientation = sliceItem.orientation
        else:
            lineOrientation = 'any'

        return lineOrientation



    def radioBoxSliceChanged(self, b: int) -> None:
        """
        Method called when user change the data slice orientation.
        """

        if (self.ui.radioButtonSliceSingleHorizontal.isChecked()
            or self.ui.radioButtonSliceAveragedHorizontal.isChecked()):
            self.sliceOrientation = 'horizontal'
        elif (self.ui.radioButtonSliceSingleVertical.isChecked()
            or self.ui.radioButtonSliceAveragedVertical.isChecked()):
            self.sliceOrientation = 'vertical'
        else:
            self.sliceOrientation = 'any'



    @staticmethod
    def getCurveId() -> str:
        """
        Return a unique id for every data slice.
        """

        return str(uuid.uuid1())



    def dragSliceItem(self, sliceItem : Union[pg.InfiniteLine, pg.LineSegmentROI, pg.LinearRegionItem],
                            sliceOrientation  : str) -> None:
        """
        Method call when user drag a slice line.

        Parameters
        ----------
        sliceItem : pg.InfiniteLine
            sliceItem currently being dragged.
        sliceOrientation : str
            orientaton of the slice being dragged
        """

        # We get the slice data from the 2d plot
        sliceX, sliceY, sliceLegend, sliceLabel = self.getDataSlice(sliceItem=sliceItem)

        # We update the curve associated to the sliceLine
        if isinstance(sliceItem, pg.LineSegmentROI):
            self.signalUpdateCurve.emit(self.plotRef+sliceOrientation+'Horizontal', # plotRef
                                        sliceItem.curveId, # curveId
                                        sliceLegend, # curveLegend
                                        sliceX[0], # x
                                        sliceY, # y
                                        False, # autorange
                                        True) # interactionUpdateAll
            self.signalUpdateCurve.emit(self.plotRef+sliceOrientation+'Vertical', # plotRef
                                        sliceItem.curveId, # curveId
                                        sliceLegend, # curveLegend
                                        sliceX[1], # x
                                        sliceY, # y
                                        False, # autorange
                                        True) # interactionUpdateAll
        else:
            self.signalUpdateCurve.emit(self.plotRef+sliceOrientation, # plotRef
                                        sliceItem.curveId, # curveId
                                        sliceLegend, # curveLegend
                                        sliceX, # x
                                        sliceY, # y
                                        False, # autorange
                                        True) # interactionUpdateAll

        # We update the label of the infinity line with the value corresponding
        # to the cut
        if isinstance(sliceItem, pg.InfiniteLine):
            sliceItem.label.setFormat(sliceLabel)
        elif isinstance(sliceItem, pg.LinearRegionItem):
            sliceItem.labelmin.setFormat(sliceLabel[0])
            sliceItem.labelmax.setFormat(sliceLabel[1])
        else:
            pass



    def addSliceItem(self, curveId: str,
                           sliceOrientation: str,
                           sliceItem: str) -> None:
        """
        Method call when user create a slice of the data.
        Create an InfiniteLine or a LinearRegionItem on the 2d plot and connect
        a drag signal on it.

        Parameters
        ----------
        curveId : str
            ID of the curve associated to the data slice
        """

        # We get the current color index so that the sliceItem color match
        # with the sliceData one
        # if sliceItem=='LineSegmentROI':
        #     colorIndex = self.getPlotFromRef(self.plotRef, sliceOrientation+'horizontal').curves[curveId].colorIndex
        #     colorIndex = self.interactionRefs['any']['nbCurve']-1
        # else:
        #     colorIndex = self.getPlotFromRef(self.plotRef, sliceOrientation).curves[curveId].colorIndex
        # colorIndex = self.interactionRefs[sliceOrientation]['nbCurve']-1

        colorIndex = getCurveColorIndex(self.interactionRefs[sliceOrientation]['colorIndexes'],
                                        self.config)

        self.interactionRefs[sliceOrientation]['colorIndexes'].append(colorIndex)


        pen = pg.mkPen(color=self.config['plot1dColors'][colorIndex],
                       width=self.config['crossHairLineWidth'],
                       style=QtCore.Qt.SolidLine)
        hoverPen = pg.mkPen(color=self.config['plot1dColors'][colorIndex],
                       width=self.config['crossHairLineWidth'],
                       style=QtCore.Qt.DashLine)

        # We create the slice where the user clicked.
        if sliceOrientation=='vertical':
            angle    = 90.
            if sliceItem=='LinearRegionItem':
                dx = (self.xData[-1]-self.xData[0])/20
                position = (self.plotWidget.mousePos[0]-dx, self.plotWidget.mousePos[0]+dx)
            else:
                position = self.plotWidget.mousePos[0]
        elif sliceOrientation=='horizontal':
            angle    = 0.
            if sliceItem=='LinearRegionItem':
                dy = (self.yData[-1]-self.yData[0])/20
                position = (self.plotWidget.mousePos[1]-dy, self.plotWidget.mousePos[1]+dy)
            else:
                position = self.plotWidget.mousePos[1]
        else:
            position = (((self.plotWidget.mousePos[0]+self.xData[0])/2,  (self.plotWidget.mousePos[1]+self.yData[0])/2),
                        ((self.plotWidget.mousePos[0]+self.xData[-1])/2, (self.plotWidget.mousePos[1]+self.yData[-1])/2))


        # If we are adding an InfiniteLine
        if sliceItem=='InfiniteLine':
            if sliceOrientation=='vertical':
                angle = 90.
            else:
                angle = 0.
            # The label is empty for now
            t = pg.InfiniteLine(pos=position,
                                angle=angle,
                                movable=True,
                                pen=pen,
                                hoverPen=hoverPen,
                                label='',
                                labelOpts={'position' : 0.9,
                                           'movable' : True,
                                           'fill': self.config['plot1dColors'][colorIndex]})

            t.sigDragged.connect(lambda sliceItem=t,
                                        sliceOrientation=sliceOrientation:
                                        self.dragSliceItem(sliceItem,
                                                           sliceOrientation))
        # If we are adding an LinearRegionItem
        elif sliceItem=='LinearRegionItem':

            t = pg.LinearRegionItem(values=position,
                                    orientation=sliceOrientation,
                                    pen=pen,
                                    hoverPen=hoverPen,
                                    swapMode='push')
            t.labelmin = pg.InfLineLabel(line=t.lines[0],
                            text='',
                            movable=True,
                            position=0.9,
                            fill=self.config['plot1dColors'][colorIndex])
            t.labelmax = pg.InfLineLabel(line=t.lines[1],
                            text='',
                            movable=True,
                            position=0.9,
                            fill=self.config['plot1dColors'][colorIndex])

            t.sigRegionChanged.connect(lambda sliceItem=t,
                                              sliceOrientation=sliceOrientation:
                                              self.dragSliceItem(sliceItem,
                                                                 sliceOrientation))
        # If we are adding an LineSegmentROI
        elif sliceItem=='LineSegmentROI':
            t = pg.LineSegmentROI(positions=position,
                                  pen=pen,
                                  hoverPen=hoverPen)

            t.sigRegionChanged.connect(lambda sliceItem=t,
                                              sliceOrientation=sliceOrientation:
                                              self.dragSliceItem(sliceItem,
                                                                 sliceOrientation))


        # Add the slicing item
        self.plotItem.addItem(t)

        # Attached the curveId to its associated sliceItem
        t.curveId    = curveId
        t.colorIndex = colorIndex

        # We save a reference to the slicing item
        self.sliceItems[curveId] = t

        # We call the dragSliceLine method to update the label(s) of the slicing
        # item
        self.dragSliceItem(sliceItem=t,
                           sliceOrientation=sliceOrientation)



    def removeSliceItem(self, curveId: str) -> None:
        """
        Remove sliceItem from the plot and from memory.

        Parameters
        ----------
        curveId : str
            [description]
        """
        if curveId in self.sliceItems.keys():
            sliceOrientation = self.getSliceItemOrientation(self.sliceItems[curveId])

            self.interactionRefs[sliceOrientation]['nbCurve'] -= 1
            self.interactionRefs[sliceOrientation]['colorIndexes'].remove(self.sliceItems[curveId].colorIndex)

            self.plotItem.removeItem(self.sliceItems[curveId])
            del(self.sliceItems[curveId])


        if len(self.sliceItems)==0:
            # when we do not interact with the map, we allow swapping
            self.ui.checkBoxSwapxy.setEnabled(True)



    def getDataSlice(self, sliceItem: Optional[Union[pg.InfiniteLine, pg.LineSegmentROI, pg.LinearRegionItem]]=None) -> Tuple[Union[np.ndarray, Tuple[np.ndarray, np.ndarray]],
                                                                                                                              Union[np.ndarray, Tuple[np.ndarray, np.ndarray]],
                                                                                                                              Union[str, Tuple[str, str]],
                                                                                                                              Union[str, Tuple[str, str]]]:
        """
        Return a vertical or horizontal data slice

        Parameters
        ----------
        sliceItem :
            sliceItem to get the sliced data from.
            If None, return the sliced data from the mouse position (creation of
            a slice)
            If not None, return the sliced data from the sliceItem
            position (dragging of the slice).
        """

        sliceX: Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]
        sliceY: Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]
        sliceLegend: Union[str, Tuple[str, str]]
        sliceLabel: Union[str, Tuple[str, str]]

        # Determine if we are handling single of average slice
        if sliceItem is None:
            if (self.ui.radioButtonSliceSingleHorizontal.isChecked()
                or self.ui.radioButtonSliceAveragedHorizontal.isChecked()
                or self.ui.radioButtonSliceSingleAny.isChecked()):
                sliceType = 'single'
                if self.sliceOrientation=='vertical':
                    orientation = 'vertical'
                    xSlice = self.plotWidget.mousePos[0]
                elif self.sliceOrientation=='horizontal':
                    orientation = 'horizontal'
                    ySlice = self.plotWidget.mousePos[1]
                else:
                    orientation = 'any'
                    xSlice = ((self.plotWidget.mousePos[0]+self.xData[0])/2, (self.plotWidget.mousePos[0]+self.xData[-1])/2)
                    ySlice = ((self.plotWidget.mousePos[1]+self.yData[0])/2, (self.plotWidget.mousePos[1]+self.yData[-1])/2)
            else:
                sliceType = 'averaged'
                if self.sliceOrientation=='vertical':
                    orientation = 'vertical'
                    dx = (self.xData[-1]-self.xData[0])/20
                    xSlice = (self.plotWidget.mousePos[0]-dx, self.plotWidget.mousePos[0]+dx)
                elif self.sliceOrientation=='horizontal':
                    orientation = 'horizontal'
                    dy = (self.yData[-1]-self.yData[0])/20
                    ySlice = (self.plotWidget.mousePos[1]-dy, self.plotWidget.mousePos[1]+dy)
        else:
            if isinstance(sliceItem, pg.LinearRegionItem):
                sliceType = 'averaged'
                if self.getSliceItemOrientation(sliceItem)=='vertical':
                    orientation = 'vertical'
                    xSlice = sliceItem.getRegion()
                else:
                    orientation = 'horizontal'
                    ySlice = sliceItem.getRegion()
            else:
                sliceType = 'single'
                if self.getSliceItemOrientation(sliceItem)=='vertical':
                    orientation = 'vertical'
                    xSlice = sliceItem.value()
                elif self.getSliceItemOrientation(sliceItem)=='horizontal':
                    orientation = 'horizontal'
                    ySlice = sliceItem.value()
                else:
                    orientation = 'any'
                    pos0, pos1 = [self.plotItem.vb.mapSceneToView(i[1]) for i in sliceItem.getSceneHandlePositions()]
                    xSlice = (pos0.x(), pos1.x())
                    ySlice = (pos0.y(), pos1.y())


        if sliceType=='single':
            # Depending on the slice we return the x and y axis data and the legend
            # associated with the cut.
            if orientation=='vertical':

                n = np.abs(self.xData-xSlice).argmin()
                sliceX        = self.yData
                sliceY        = self.zData[n]
                sliceLegend   = '{} = {}{}'.format(self._xLabelText,
                                                   parse_number(self.xData[n], 3, unified=True),
                                                   self._xLabelUnits)
                sliceLabel = '{}{}'.format(parse_number(self.xData[n], 3, unified=True), self._xLabelUnits)
            elif orientation=='horizontal':

                n = np.abs(self.yData-ySlice).argmin()
                sliceX        = self.xData
                sliceY        = self.zData[:,n]
                sliceLegend   = '{} = {}{}'.format(self._yLabelText,
                                                   parse_number(self.yData[n], 3, unified=True),
                                                   self._yLabelUnits)
                sliceLabel = '{}{}'.format(parse_number(self.yData[n], 3, unified=True), self._yLabelUnits)
            else:
                # Greatly inspired from
                # https://stackoverflow.com/questions/7878398/how-to-extract-an-arbitrary-line-of-values-from-a-numpy-array

                # Get index min and max
                x0_index = np.abs(self.xData - xSlice[0]).argmin()
                x1_index = np.abs(self.xData - xSlice[1]).argmin()
                y0_index = np.abs(self.yData - ySlice[0]).argmin()
                y1_index = np.abs(self.yData - ySlice[1]).argmin()

                # Get the slice data
                nb_points = int(np.hypot(x1_index-x0_index, y1_index-y0_index))
                x_index = np.linspace(x0_index, x1_index, nb_points).astype(int)
                y_index = np.linspace(y0_index, y1_index, nb_points).astype(int)

                sliceX = (self.xData[x_index], self.yData[y_index])
                sliceY = self.zData[x_index,y_index]
                sliceLegend = 'From ({}{}, {}{}) to ({}{}, {}{})'.format(parse_number(xSlice[0], 3, unified=True), self._xLabelUnits,
                                                                         parse_number(ySlice[0], 3, unified=True), self._yLabelUnits,
                                                                         parse_number(xSlice[1], 3, unified=True), self._xLabelUnits,
                                                                         parse_number(ySlice[1], 3, unified=True), self._yLabelUnits,)
                sliceLabel = ''

        # If averaged  slice
        else:
            # Depending on the slice we return the x and y axis data and the legend
            # associated with the cut.
            if orientation=='vertical':
                nmin = np.abs(self.xData-xSlice[0]).argmin()
                nmax = np.abs(self.xData-xSlice[1]).argmin()
                if nmin==nmax:
                    if nmax<len(self.xData):
                        nmax=nmin+1
                    else:
                        nmin-=1
                        nmax=nmin+1
                sliceX        = self.yData
                sliceY        = np.mean(self.zData[nmin:nmax], axis=0)
                sliceLegend   = '{}: from {}{} to {}{}, mean: {}{}, nb samples: {}'.format(self._xLabelText,
                                                                                         parse_number(self.xData[nmin], 3, unified=True),
                                                                                         self._xLabelUnits,
                                                                                         parse_number(self.xData[nmax], 3, unified=True),
                                                                                         self._xLabelUnits,
                                                                                         parse_number((self.xData[nmin]+self.xData[nmax])/2, 3, unified=True),
                                                                                         self._xLabelUnits,
                                                                                         int(nmax-nmin))
                sliceLabel = ('{}{}'.format(parse_number(self.xData[nmin], 3, unified=True), self._xLabelUnits),
                              '{}{}'.format(parse_number(self.xData[nmax], 3, unified=True), self._xLabelUnits))
            else:

                nmin = np.abs(self.yData-ySlice[0]).argmin()
                nmax = np.abs(self.yData-ySlice[1]).argmin()
                if nmin==nmax:
                    if nmax<len(self.yData):
                        nmax=nmin+1
                    else:
                        nmin-=1
                        nmax=nmin+1
                sliceX        = self.xData
                sliceY        = np.mean(self.zData[:,nmin:nmax], axis=1)
                sliceLegend   = '{}: from {}{} to {}{}, mean: {}{}, nb samples: {}'.format(self._yLabelText,
                                                                                         parse_number(self.yData[nmin], 3, unified=True),
                                                                                         self._yLabelUnits,
                                                                                         parse_number(self.yData[nmax], 3, unified=True),
                                                                                         self._yLabelUnits,
                                                                                         parse_number((self.yData[nmin]+self.yData[nmax])/2, 3, unified=True),
                                                                                         self._yLabelUnits,
                                                                                         int(nmax-nmin))
                sliceLabel = ('{}{}'.format(parse_number(self.yData[nmin], 3, unified=True), self._yLabelUnits),
                              '{}{}'.format(parse_number(self.yData[nmax], 3, unified=True), self._yLabelUnits))

        return sliceX, sliceY, sliceLegend, sliceLabel



    def isThereSlicePlot(self) -> bool:
        """
        Return True if there is a 1d plot displaying a slice of sliceOrientation,
        False otherwise.
        """
        if self.sliceOrientation not in self.interactionRefs.keys():
            return False
        else:
            return True



    def plotItemdoubleClick(self, e) -> None:
        """
        When a use double click on the 2D plot, we create a slice of the colormap
        """

        # We check that the user mouse has already moved above the plotItem
        if not hasattr(self.plotWidget, 'mousePos'):
            return

        # If double click is detected and mouse is over the viewbox, we launch
        # a 1d plot corresponding to a data slice
        if e._double and self.plotWidget.isMouseOverView():

            # Get the data of the slice
            sliceX, sliceY, sliceLegend, sliceLabel = self.getDataSlice()

            # If there is no 1d plot already showing the slice
            if not self.isThereSlicePlot():

                self.addSliceItemAndPlot(data          = (sliceX, sliceY),
                                         sliceItem     = self.getCurrentSliceItem())
            # If there is already
            # 1. The user doubleClick on an sliceItem and we remove it
            # 2. The doubleClick somewhere else on the map and we create another slice
            else:
                # We check if user double click on an sliceItem
                clickedCurveId = self.sliceIdClickedOn()

                # If the user add a new sliceItem and its associated plot
                if clickedCurveId is None:
                    self.addSliceItemAndPlot(data         = (sliceX, sliceY),
                                             sliceItem    = self.getCurrentSliceItem())

                # We remove a sliceItem and its associated plot
                else:
                    self.removeSliceItemAndPlot(clickedCurveId)



    def removeSliceItemAndPlot(self, curveId: str) -> None:
        """
        Called when a used double click on a slice to remove it, see
        plotItemdoubleClick.
        Remove the sliceItem from the 2d plot and its associated slice from the
        attached 1d plot.

        Args:
            curveId: id of the slice.
        """

        sliceOrientation = self.getSliceItemOrientation(self.sliceItems[curveId])

        if sliceOrientation in ('vertical', 'horizontal'):
            # If there is more than one slice, we remove it and the associated curve
            if self.interactionRefs[sliceOrientation]['nbCurve']>1:
                self.signalRemoveCurve.emit(self.plotRef+sliceOrientation, curveId)
            # If there is only one slice, we close the linked 1d plot
            # which will remove the associated sliceItem
            else:
                self.signalClose1dPlot.emit(self.plotRef+sliceOrientation)
        else:
            for sliceOrientationTemp in  ('vertical', 'horizontal'):
                # If there is more than one slice, we remove it and the associated curve
                if self.interactionRefs['any']['nbCurve']>1:
                    self.signalRemoveCurve.emit(self.plotRef+'any'+sliceOrientationTemp, curveId)
                # If there is only one slice, we close the linked 1d plot
                # which will remove the associated sliceItem
                else:
                    self.signalClose1dPlot.emit(self.plotRef+'any'+sliceOrientationTemp)

        self.removeSliceItem(curveId)



    def sliceIdClickedOn(self) -> Optional[str]:
        """
        Return the curveId of the
            InfiniteLine, LinearRegionItem, LineSegmentROI
        that a user has clicked on.
        If the user didn't click on neither, return None

        Returns:
            Optional[str]: None or the id of the slice.
        """

        clickedCurveId = None

        for sliceItem in list(self.sliceItems.values()):
            if sliceItem.mouseHovering:
                clickedCurveId = sliceItem.curveId
                break

        return clickedCurveId



    def addSliceItemAndPlot(self, data: tuple,
                                  sliceItem: str,
                                  sliceOrientation: Optional[str]=None,
                                  plotRef: Optional[str]=None) -> None:

        # when we interact with the map, we do not allow swapping
        self.ui.checkBoxSwapxy.setEnabled(False)

        # If sliceOrientation is None, users just doubleClick on the plotItem
        # The sliceOrientation is the one given by the GUI
        if sliceOrientation is None:
            sliceOrientation = self.sliceOrientation

        yLabelText  = self._zLabelText
        yLabelUnits = self._zLabelUnits

        title = self.title+" <span style='color: red; font-weight: bold;'>Extrapolated data</span>"
        windowTitle = self._windowTitle+' - '+sliceOrientation+' slice'
        runId          = self.runId

        # Should be called once for both addplot and addSliceItem
        curveId = self.getCurveId()

        if sliceOrientation in ('vertical', 'horizontal'):

            if plotRef is None:
                plotRef = self.plotRef+sliceOrientation

            if sliceOrientation=='vertical':
                xLabelText  = self._yLabelText
                xLabelUnits = self._yLabelUnits

            elif sliceOrientation=='horizontal':
                xLabelText  = self._xLabelText
                xLabelUnits = self._xLabelUnits

            if sliceOrientation in self.interactionRefs.keys():
                self.interactionRefs[sliceOrientation]['nbCurve'] += 1
            else:
                self.interactionRefs[sliceOrientation] = {'plotRef' : plotRef,
                                                          'nbCurve' : 1,
                                                          'colorIndexes' : []}

            self.signal2MainWindowAddPlot.emit(runId, # runId
                                               curveId, # curveId
                                               title, # plotTitle
                                               windowTitle, # windowTitle
                                               plotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               data, # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:

            if plotRef is None:
                plotRefHorizontal = self.plotRef+sliceOrientation+'Horizontal'
                plotRefVertical   = self.plotRef+sliceOrientation+'Vertical'


                if 'any' in self.interactionRefs.keys():
                    self.interactionRefs['any']['nbCurve'] += 1
                else:
                    self.interactionRefs['any'] = {'plotRefHorizontal' : plotRefHorizontal,
                                                   'plotRefVertical' : plotRefVertical,
                                                   'nbCurve' : 1,
                                                   'colorIndexes' : []}

            self.signal2MainWindowAddPlot.emit(runId, # runId
                                               curveId, # curveId
                                               title, # plotTitle
                                               windowTitle, # windowTitle
                                               plotRefHorizontal, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               (data[0][0], data[1]), # data
                                               self._xLabelText, # xLabelText
                                               self._xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits

            self.signal2MainWindowAddPlot.emit(runId, # runId
                                               curveId, # curveId
                                               title, # plotTitle
                                               windowTitle, # windowTitle
                                               plotRefVertical, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               (data[0][1], data[1]), # data
                                               self._yLabelText, # xLabelText
                                               self._yLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits

        # To add a slice item, we need to keep track of
        self.addSliceItem(curveId          = curveId,
                          sliceOrientation = sliceOrientation,
                          sliceItem        = sliceItem)



    ####################################
    #
    #           Z data transformation
    #
    ####################################



    def zDataTransformation(self) -> None:
        """
        Handle all transformation of the displayed zData.
        Each time the method is called, a copy of the 2d array of the zData is
        done.
        """

        zData = np.copy(self.zDataRef)

        # global average removal
        if self.ui.checkBoxSubtractAverageX.isChecked():
            zData = zData - np.nanmean(zData, axis=0)
        if self.ui.checkBoxSubtractAverageY.isChecked():
            zData = (zData.T - np.nanmean(zData, axis=1)).T

        # Data unwrapping
        mask = ~np.isnan(zData)
        if self.ui.checkBoxUnwrapX.isChecked():
            for j in range(zData.shape[1]):
                zData[:, j][mask[:, j]] = np.unwrap(zData[:, j][mask[:, j]])
        if self.ui.checkBoxUnwrapY.isChecked():
            for i in range(zData.shape[0]):
                zData[i, :][mask[i, :]] = np.unwrap(zData[i, :][mask[i, :]])

        # Polynomial fit removal
        if self.ui.spinBoxSubtractPolyX.value()>0:
            for i, z in enumerate(zData):
                c = np.polynomial.Polynomial.fit(self.yData, z, self.ui.spinBoxSubtractPolyX.value())
                zData[i] = c(self.yData)
        if self.ui.spinBoxSubtractPolyY.value()>0:
            for i, z in enumerate(zData.T):
                c = np.polynomial.Polynomial.fit(self.xData, z, self.ui.spinBoxSubtractPolyY.value())
                zData[:,i] = c(self.xData)

        # Depending on the asked derivative, we calculate the new z data and
        # the new z label
        # Since only one derivative at a time is possible, we use elif here
        label = str(self.ui.comboBoxDerivative.currentText())
        if label=='∂z/∂x':
            zData = np.gradient(zData, self.xData, axis=0)
            self.hist.setLabel(self._zLabelText+' ('+self._zLabelUnits+'/'+self._xLabelUnits+')')
        elif label=='∂z/∂y':
            zData = np.gradient(zData, self.yData, axis=1)
            self.hist.setLabel(self._zLabelText+' ('+self._zLabelUnits+'/'+self._yLabelUnits+')')
        elif label=='√((∂z/∂x)² + (∂z/∂y)²)':
            zData = np.sqrt(np.gradient(zData, self.xData, axis=0)**2. + np.gradient(zData, self.yData, axis=1)**2.)
            self.hist.setLabel(self._zLabelText+' ('+self._zLabelUnits+' x √('+self._xLabelUnits+'² + '+self._yLabelUnits+'²)')
        elif label=='∂²z/∂x²':
            zData = np.gradient(np.gradient(zData, self.xData, axis=0), self.xData, axis=0)
            self.hist.setLabel(self._zLabelText+' ('+self._zLabelUnits+'/'+self._xLabelUnits+'²)')
        elif label=='∂²z/∂y²':
            zData = np.gradient(np.gradient(zData, self.yData, axis=1), self.yData, axis=1)
            self.hist.setLabel(self._zLabelText+' ('+self._zLabelUnits+'/'+self._yLabelUnits+'²)')
        elif label=='sobel':
            sx = sobel(zData, axis=0, mode='constant')
            sy = sobel(zData, axis=1, mode='constant')
            zData = np.hypot(sx, sy)
            self.hist.setLabel('Sobel('+self._zLabelText+') ('+self._zLabelUnits+')')
        else:
            self.hist.setLabel(self._zLabelText+' ('+self._zLabelUnits+')')

        self.updateImageItem(self.xData, self.yData, zData)



    ####################################
    #
    #           FindSlope
    #
    ####################################



    def cbFindSlope(self) -> None:
        """
        Method called when user clicks on the Find slope checkbox.
        Display a LineSegmentROI with information about its angle and length ratio.

        Parameters
        ----------
        b : QtWidgets.QCheckBox
            Draw isocurve checkbox
        """

        # Check
        if self.ui.checkBoxFindSlope.isChecked():
            # Add a spinBox in the GUI and create an empty list to keep track of
            # all the future findSlope widgets
            self.findSlopeLines: List[pg.LineSegmentROI]= []
            self.ui.findSlopesb = QtWidgets.QSpinBox()
            self.ui.findSlopesb.setValue(1)

            self.ui.findSlopesb.valueChanged.connect(self.findSlopesbChanged)
            self.ui.horizontalLayoutFindSlope.addWidget(self.ui.findSlopesb)

            self.findSlopesbChanged()

        # Uncheck
        else:
            self.findSlopeLineRemove(self.findSlopeLines[-1])
            del(self.findSlopeLines)
            self.ui.findSlopesb.deleteLater()
            self.ui.horizontalLayoutFindSlope.removeWidget(self.ui.findSlopesb)



    def findSlopesbChanged(self):
        """
        Method called when user clicks on the findSlope spinBox.
        Its value defines the number of findSlope widget displayed on the
        plotItem.
        """

        nbFindSlope = self.ui.findSlopesb.value()
        # If there is no findSlope widget to display, we remove the spinBox widget
        if nbFindSlope==0:
            self.ui.checkBoxFindSlope.setChecked(False)
            self.cbFindSlope()
        else:
            # Otherwise, we add or remove findSlope widget
            if len(self.findSlopeLines)<nbFindSlope:
                self.findSlopeLineAdd()
            else:
                self.findSlopeLineRemove(self.findSlopeLines[-1])



    def findSlopeLineAdd(self):
        """
        Add a findSlope widget.
        All findSlope widgets are store in the findSlopeLines attribute.
        """

        dx = self.xData[-1]-self.xData[0]
        dy = self.yData[-1]-self.yData[0]
        point1 = (self.xData[0]+dx/4,   self.yData[0]+dy/4)
        point2 = (self.xData[0]+dx*3/4, self.yData[0]+dy*3/4)

        slopeLineSegmentROI = pg.LineSegmentROI(positions=(point1, point2))

        textSlope1 = pg.TextItem(anchor=(0,0),
                                    color=(255, 255, 255),
                                    fill=self.config['plot1dColors'][0])

        textSlope2 = pg.TextItem(anchor=(0,0),
                                    color=(255, 255, 255),
                                    fill=self.config['plot1dColors'][1])

        slopeLineSegmentROI.textSlope1 = textSlope1
        slopeLineSegmentROI.textSlope2 = textSlope2

        slopeLineSegmentROI.sigRegionChanged.connect(lambda line=slopeLineSegmentROI:self.findSlopeDragged(line))

        self.plotItem.addItem(slopeLineSegmentROI.textSlope1)
        self.plotItem.addItem(slopeLineSegmentROI.textSlope2)
        self.plotItem.addItem(slopeLineSegmentROI)

        self.findSlopeDragged(slopeLineSegmentROI)

        self.imageView.autoRange()
        self.imageView.autoRange()

        self.findSlopeLines.append(slopeLineSegmentROI)



    def findSlopeLineRemove(self, line:pg.LineSegmentROI):
        """
        Remove the findSlope widget given in parameter from the plotItem and
        from the class memory.

        Args:
            line: the slopeWidget item that we want removed
        """

        self.plotItem.removeItem(line)
        self.plotItem.removeItem(line.textSlope1)
        self.plotItem.removeItem(line.textSlope2)

        self.findSlopeLines.remove(line)



    def findSlopeDragged(self, line:pg.LineSegmentROI):
        """
        Method called when user drags the findSlope LineSegmentROI in parameter.
        Compute the angle and length ratio of the LineSegmentROI and display it.
        """

        pos0, pos1 = [self.plotItem.vb.mapSceneToView(i[1]) for i in line.getSceneHandlePositions()]
        point1 = (pos0.x(), pos0.y())
        point2 = (pos1.x(), pos1.y())

        angle = atan2(point2[1]-point1[1], point2[0]-point1[0])*180/np.pi
        line.textSlope1.setPos(point1[0], point1[-1])
        line.textSlope1.setText('∡ = {:0.2e} deg'.format(angle))

        ratio = (point2[1]-point1[1])/(point2[0]-point1[0])
        line.textSlope2.setPos(point2[0], point2[-1])
        line.textSlope2.setHtml('<sup>y</sup>/<sub>x</sub> = {:0.2e}/{:0.2e} = {:0.2e}'.format(point2[1]-point1[1], point2[0]-point1[0], ratio))



    ####################################
    #
    #           Isocurve
    #
    ####################################



    def isoCurveClicked(self):
        """
        Method called when user clicks on the Draw isocurve checkbox.
        Send a signal to the histogram widget
        """
        self.signalIsoCurve.emit(self.ui.checkBoxDrawIsoCurve.isChecked(),
                                 self.imageView)



    ####################################
    #
    #           Method to related to extraction
    #
    ####################################


    def maximumGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        return self.xData, self.yData[np.nanargmax(self.zData, axis=1)]



    def checkBoxMaximumClicked(self) -> None:
        """
        Called when user click on one of the extraction button.
        Extract data and launch them in a dedicated 1d plot.
        """

        if self.ui.checkBoxMaximum.isChecked():
            self.maximumPlotRef = self.plotRef+'maximum'
            self.maximumCurveId = self.getCurveId()

            self.interactionRefs['maximum'] = {'plotRef' : self.maximumPlotRef,
                                               'nbCurve' : 1,
                                               'colorIndexes' : []}

            self.signal2MainWindowAddPlot.emit(self.runId, # runId
                                               self.maximumCurveId, # curveId
                                               self._windowTitle+' - maximum', # plotTitle
                                               self._windowTitle+' - maximum', # windowTitle
                                               self.maximumPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.maximumGetData(), # data
                                               self._xLabelText, # xLabelText
                                               self._xLabelUnits, # xLabelUnits
                                               self._yLabelText, # yLabelText
                                               self._yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:
            self.signalClose1dPlot.emit(self.plotRef+'maximum')



    def maximumUpdateCurve(self) -> None:
        if hasattr(self, 'maximumPlotRef'):
            x, y = self.maximumGetData()
            self.signalUpdateCurve.emit(self.maximumPlotRef, # plotRef
                                        self.maximumCurveId, # curveId
                                        '', # curveLegend
                                        x, # x
                                        y, # y
                                        False, # autorange
                                        True) # interactionUpdateAll



    def maximumClosePlot(self) -> None:
        if hasattr(self, 'maximumPlotRef'):
            self.signalClose1dPlot.emit(self.maximumPlotRef)



    def minimumGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        return self.xData, self.yData[np.nanargmax(self.zData, axis=1)]



    def checkBoxMinimumClicked(self) -> None:
        """
        Called when user click on one of the extraction button.
        Extract data and launch them in a dedicated 1d plot.
        """

        if self.ui.checkBoxMinimum.isChecked():
            self.minimumPlotRef = self.plotRef+'minimum'
            self.minimumCurveId = self.getCurveId()
            y = self.yData[np.nanargmax(self.zData, axis=1)]

            self.interactionRefs['minimum'] = {'plotRef' : self.minimumPlotRef,
                                               'nbCurve' : 1,
                                               'colorIndexes' : []}

            self.signal2MainWindowAddPlot.emit(self.runId, # runId
                                               self.minimumCurveId, # curveId
                                               self._windowTitle+' - minimum', # plotTitle
                                               self._windowTitle+' - minimum', # windowTitle
                                               self.minimumPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.minimumGetData(), # data
                                               self._xLabelText, # xLabelText
                                               self._xLabelUnits, # xLabelUnits
                                               self._yLabelText, # yLabelText
                                               self._yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:
            self.minimumClosePlot()



    def minimumClosePlot(self) -> None:
        if hasattr(self, 'minimumPlotRef'):
            self.signalClose1dPlot.emit(self.minimumPlotRef)



    def minimumUpdateCurve(self) -> None:
        if hasattr(self, 'minimumPlotRef'):
            x, y = self.minimumGetData()
            self.signalUpdateCurve.emit(self.minimumPlotRef, # plotRef
                                        self.minimumCurveId, # curveId
                                        '', # curveLegend
                                        x, # x
                                        y, # y
                                        False, # autorange
                                        True) # interactionUpdateAll



    def interactionCurveClose(self, curveId: str) -> None:
        """
        Called from MainWindow when sub-interaction plot is closed.
        Uncheck their associated checkBox
        """
        if 'minimum' in curveId:
            self.ui.checkBoxMinimum.setChecked(False)
            del(self.minimumPlotRef)
            del(self.minimumCurveId)
        elif 'maximumPlotRef' in curveId:
            self.ui.checkBoxMaximum.setChecked(False)
            del(self.maximumPlotRef)
            del(self.maximumCurveId)



    def interactionCloseAll(self) -> None:

        self.maximumClosePlot()
        self.minimumClosePlot()

        self.widget3d.close()



    def interactionUpdateAll(self) -> None:

        self.maximumUpdateCurve()
        self.minimumUpdateCurve()


        # If there are slices, we update them as well
        for sliceItem in self.sliceItems.values():
            sliceOrientation = self.getSliceItemOrientation(sliceItem)

            self.dragSliceItem(sliceItem,
                               sliceOrientation)

        # Update fit data only if roi is detected
        if hasattr(self, 'roi'):
            self.roiChangedFinished()



    ####################################
    #
    #           Fit GroupBox
    #
    ####################################



    def initGroupBoxFit(self) -> None:
        """
        Method called at the initialization of the GUI.
        Make a list of radioButton reflected the available list of fitmodel.
        By default all radioButton are disabled and user should chose a plotDataItem
        to make them available.
        """

        self.groupBoxFit  = GroupBoxFit(self.ui.groupBoxInteraction,
                                        self.plotRef,
                                        self.plotItem,
                                        self._xLabelText,
                                        self._yLabelText,
                                        self._zLabelText,
                                        self._xLabelUnits,
                                        self._yLabelUnits,
                                        self._zLabelUnits,
                                        self._windowTitle,
                                        self.databaseAbsPath,
                                        )

        # Event from groupBox to main
        self.groupBoxFit.signal2MainWindowAddPlot.connect(self.signal2MainWindowAddPlot.emit)
        self.groupBoxFit.signalClose2dPlot.connect(self.signalClose2dPlot.emit)

        # Event from groupBox to the 2d plot displaying the fit result
        self.groupBoxFit.signalUpdate2dFitResult.connect(self.signalUpdate2dFitResult.emit)

        # Event from groupBox to this 2d plot
        self.groupBoxFit.signalAddROI.connect(self.addROI)
        self.groupBoxFit.signalRemoveROI.connect(self.removeROI)

        # Events from the plot2d to the groupBox
        self.signalUpdate2dFitData.connect(self.groupBoxFit.updateData)

        # Add to GUI
        self.ui.verticalLayout_5.addWidget(self.groupBoxFit)



    QtCore.pyqtSlot()
    def removeROI(self):
        """
        Called by the fit groupBox.
        Remove the ROI from the plotItem.
        """
        self.plotItem.removeItem(self.roi)
        del(self.roi)



    QtCore.pyqtSlot()
    def addROI(self):
        """
        Called by fit groupBox.
        Add a ROI and connect it to roiChangedFinished.
        """

        pen = pg.mkPen(color=self.config['styles'][self.config['style']]['plot1dSelectionLineColor'],
                        width=3,
                        style=QtCore.Qt.SolidLine)
        hoverPen = pg.mkPen(color=self.config['styles'][self.config['style']]['plot1dSelectionLineColor'],
                            width=3,
                            style=QtCore.Qt.DashLine)
        self.roi = pg.RectROI(pos=(self.xData.min(), self.yData.min()),
                              size=(self.xData.max()-self.xData.min(), self.yData.max()-self.yData.min()),
                              pen=pen,
                              hoverPen=hoverPen)

        self.roi.sigRegionChangeFinished.connect(self.roiChangedFinished)

        self.plotItem.addItem(self.roi)
        self.roiChangedFinished()



    def roiChangedFinished(self):
        """
        Called when releasing the ROI.
        Get the selected data and send them to the fit groupBox
        """

        t = self.roi.getArrayRegion(data=self.zData,
                                    img=self.imageItem,
                                    returnMappedCoords=True)

        self.xSelected = t[1][0,:,0]
        self.ySelected = t[1][1,0,:]
        self.zSelected = t[0]

        self.signalUpdate2dFitData.emit(self.xSelected,
                                        self.ySelected,
                                        self.zSelected)
