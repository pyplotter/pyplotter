# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
from typing import Union, Tuple, Optional, List, Dict
from math import atan2
import uuid

from ..ui.plot2dWidget import Ui_Dialog
from . import palettes # File copy from bokeh: https://github.com/bokeh/bokeh/blob/7cc500601cdb688c4b6b2153704097f3345dd91c/bokeh/palettes.py
from .plot_app import PlotApp
from .plot_1d_app import Plot1dApp
from .config import loadConfigCurrent
from ..sources.functions import getCurveColorIndex, hex_to_rgba
from .pyqtgraph import pg



class Plot2dApp(QtWidgets.QDialog, Ui_Dialog, PlotApp):
    """
    Class to handle ploting in 2d.
    """

    signalRemovePlotFromRef      = QtCore.pyqtSignal(str, str)
    signal2MainWindowClosePlot   = QtCore.pyqtSignal(str)
    signalRemovePlotRef          = QtCore.pyqtSignal(str)

    signalClose1dPlot              = QtCore.pyqtSignal(str)
    signalClose2dPlot            = QtCore.pyqtSignal(str, str)

    signal2MainWindowAddPlot     = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)


    # signalGet1dColorIndex     = QtCore.pyqtSignal(str, str, str, str, str)
    signalUpdateCurve  = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray)
    signalRemoveCurve  = QtCore.pyqtSignal(str, str)


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
                       databaseAbsPath: str):
        """
        Class handling the plot of 2d data, i.e. colormap.
        Since pyqtgraph does not handle non regular image, there could be funny
        stuff happening.
        The class allows interactivity with the colormap in particular some data
        treatment launch 1dplot through the main app to keep plot references
        updated, see Plot1dApp.

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
        QtWidgets.QDialog.__init__(self, parent=None)
        self.setupUi(self)

        self._allowClosing = False

        self.config = loadConfigCurrent()

        # Must be set on False, see
        # https://github.com/pyqtgraph/pyqtgraph/issues/1371
        self.plotWidget.useOpenGL(False)

        # Allow resize of the plot window
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)

        self.plotType = '2d'

        self.xData         = x
        self.yData         = y
        self.zData         = z
        self.xDataRef      = x # To keep track of all operation done on the z data
        self.yDataRef      = y # To keep track of all operation done on the z data
        self.zDataRef      = z # To keep track of all operation done on the z data
        self.xLabelText    = xLabelText
        self.xLabelUnits   = xLabelUnits
        self.yLabelText    = yLabelText
        self.yLabelUnits   = yLabelUnits
        self.zLabelText    = zLabelText
        self.zLabelUnits   = zLabelUnits
        self.title         = title
        self.windowTitle   = windowTitle
        self.runId         = runId
        self.curveId       = curveId
        self.plotRef       = plotRef

        # Store references to infiniteLines creating by data slicing
        self.sliceItems = {}
        self.sliceOrientation = 'vertical'

        # Store the isoCurve and isoLine object
        self.isoCurve = None
        self.isoLine  = None

        # Reference to the extracted window
        self.extractionWindow = None


        # Keep track of the sub-interaction plots launched fron that plot
        self.interactionRefs: Dict[str, dict] = {}

        # Get plotItem from the widget
        self.plotItem = self.plotWidget.getPlotItem()
        self.resize(*self.config['dialogWindowSize'])


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

        self.histWidget.item.axis.setPen(self.config['styles'][self.config['style']]['pyqtgraphzAxisTicksColor'])


        # Create a histogram item linked to the imageitem
        self.histWidget.setImageItem(self.imageItem)
        self.histWidget.autoHistogramRange()
        self.histWidget.setFixedWidth(100)
        self.histWidget.item.setLevels(min=z[~np.isnan(z)].min(), max=z[~np.isnan(z)].max())
        self.histWidget.axis.setTickFont(font)

        self.setImageView()


        # Axes label
        self.plotItem.setTitle(title=title, color=self.config['styles'][self.config['style']]['pyqtgraphTitleTextColor'])
        self.plotItem.showGrid(x=True, y=True)
        self.plotItem.setLabel(axis='bottom',
                               text=self.xLabelText,
                               units=self.xLabelUnits,
                               **{'color'     : self.config['styles'][self.config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(self.config['axisLabelFontSize'])+'pt'})
        self.plotItem.setLabel(axis='left',
                               text=self.yLabelText,
                               units=self.yLabelUnits,
                               **{'color'     : self.config['styles'][self.config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(self.config['axisLabelFontSize'])+'pt'})

        # The only reliable way I have found to correctly display the zLabel
        # is by using a Qlabel from the GUI
        self.plot2dzLabel.setText(zLabelText+' ('+zLabelUnits+')')
        self.plot2dzLabel.setFont(font)
        self.setWindowTitle(windowTitle)

        self.setStyleSheet("background-color: "+str(self.config['styles'][self.config['style']]['dialogBackgroundColor'])+";")
        self.setStyleSheet("color: "+str(self.config['styles'][self.config['style']]['dialogTextColor'])+";")


        # Connect UI
        self.checkBoxFindSlope.clicked.connect(self.cbFindSlope)
        self.checkBoxDrawIsoCurve.clicked.connect(self.cbIsoCurve)
        self.checkBoxInvert.clicked.connect(lambda : self.cbcmInvert(self.checkBoxInvert))
        self.checkBoxMaximum.clicked.connect(self.checkBoxMaximumClicked)
        self.checkBoxMinimum.clicked.connect(self.checkBoxMinimumClicked)
        self.checkBoxSwapxy.clicked.connect(self.checkBoxSwapxyState)
        self.checkBoxAspectEqual.clicked.connect(self.checkBoxAspectEqualState)
        self.checkBoxSubtractAverageX.clicked.connect(self.zDataTransformation)
        self.checkBoxSubtractAverageX.clicked.connect(self.zDataTransformation)
        self.spinBoxSubtractPolyX.valueChanged.connect(self.zDataTransformation)
        self.spinBoxSubtractPolyY.valueChanged.connect(self.zDataTransformation)
        self.checkBoxUnwrapX.clicked.connect(self.zDataTransformation)
        self.checkBoxUnwrapY.clicked.connect(self.zDataTransformation)
        self.pushButton3d.clicked.connect(self.launched3d)
        self.plotItem.scene().sigMouseClicked.connect(self.plotItemdoubleClick)
        self.radioButtonSliceSingleAny.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceSingleHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceSingleVertical.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceAveragedHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceAveragedVertical.toggled.connect(self.radioBoxSliceChanged)

        # UI for the derivative combobox
        for label in self.config['plot2dDerivative']:
            self.comboBoxDerivative.addItem(label)
        self.comboBoxDerivative.activated.connect(self.zDataTransformation)


        ## Colormap initialization

        # Build the colormap comboBox, the default one being from the config file
        index = 0
        indexViridis = 0
        for cm in [i for i in palettes.all_palettes.keys() if i[-2:] !='_r']:
            self.comboBoxcm.addItem(cm)
            if cm==self.config['plot2dcm']:
                indexViridis = index

            index += 1

        self.colorMapInversed = False
        self.setColorMap(self.config['plot2dcm'])
        self.comboBoxcm.setCurrentIndex(indexViridis)
        self.comboBoxcm.currentIndexChanged.connect(self.comboBoxcmChanged)

        # Should be initialize last
        PlotApp.__init__(self, databaseAbsPath)

        self.show()



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
        self.widget3d.setWindowTitle(self.windowTitle)
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



    def livePlotUpdate(self, x: np.ndarray,
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

        self.checkBoxSwapxyState(1)




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

        self.histWidget.item.setLevels(min=z[~np.isnan(z)].min(),
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

        if self.checkBoxAspectEqual.isChecked():
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
        if self.checkBoxSwapxy.isChecked():
            # If axes are not already swapped
            if self.xLabelText==self.plotItem.axes['bottom']['item'].labelText:

                self.plotItem.setLabel(axis='bottom',
                                    text=self.yLabelText,
                                    units=self.yLabelUnits)
                self.plotItem.setLabel(axis='left',
                                    text=self.xLabelText,
                                    units=self.xLabelUnits)

                self.updateImageItem(self.yDataRef, self.xDataRef, self.imageView.image.T)
        # If user wants to unswap axes
        else:
            # If axes are not already unswap
            if self.yLabelText==self.plotItem.axes['bottom']['item'].labelText:

                self.plotItem.setLabel(axis='bottom',
                                    text=self.xLabelText,
                                    units=self.xLabelUnits)
                self.plotItem.setLabel(axis='left',
                                    text=self.yLabelText,
                                    units=self.yLabelUnits)

                self.updateImageItem(self.xDataRef, self.yDataRef, self.imageView.image.T)



    ####################################
    #
    #           Method related to data slicing
    #
    ####################################



    def getCurrentSliceItem(self) -> str:
        """
        Return the type of slice the user want
        """

        if self.radioButtonSliceSingleHorizontal.isChecked() or self.radioButtonSliceSingleVertical.isChecked():
            sliceItem = 'InfiniteLine'
        elif self.radioButtonSliceSingleAny.isChecked():
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

        if self.radioButtonSliceSingleHorizontal.isChecked() or self.radioButtonSliceAveragedHorizontal.isChecked():
            self.sliceOrientation = 'horizontal'
        elif self.radioButtonSliceSingleVertical.isChecked() or self.radioButtonSliceAveragedVertical.isChecked():
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
            self.signalUpdateCurve.emit(self.plotRef+sliceOrientation+'horizontal', # plotRef
                                        sliceItem.curveId, # curveId
                                        sliceLegend, # curveLegend
                                        sliceX[0], # x
                                        sliceY) # y
            self.signalUpdateCurve.emit(self.plotRef+sliceOrientation+'vertical', # plotRef
                                        sliceItem.curveId, # curveId
                                        sliceLegend, # curveLegend
                                        sliceX[1], # x
                                        sliceY) # y
        else:
            self.signalUpdateCurve.emit(self.plotRef+sliceOrientation, # plotRef
                                        sliceItem.curveId, # curveId
                                        sliceLegend, # curveLegend
                                        sliceX, # x
                                        sliceY) # y

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
                           sliceItem: str,
                           position: Union[float, Tuple[float, float]]) -> None:
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

        # If the position has been given it means we are swapping the axes.
        # otherwise, we create the slice where the user clicked.
        if position is None:
            if sliceOrientation=='vertical':
                angle    = 90.
                if sliceItem=='LinearRegionItem':
                    dx = (self.xData[-1]-self.xData[0])/20
                    position = (self.mousePos[0]-dx, self.mousePos[0]+dx)
                else:
                    position = self.mousePos[0]
            elif sliceOrientation=='horizontal':
                angle    = 0.
                if sliceItem=='LinearRegionItem':
                    dy = (self.yData[-1]-self.yData[0])/20
                    position = (self.mousePos[1]-dy, self.mousePos[1]+dy)
                else:
                    position = self.mousePos[1]
            else:
                position = (((self.mousePos[0]+self.xData[0])/2,  (self.mousePos[1]+self.yData[0])/2),
                            ((self.mousePos[0]+self.xData[-1])/2, (self.mousePos[1]+self.yData[-1])/2))


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
            self.checkBoxSwapxy.setEnabled(True)



    def getDataSlice(self, sliceItem: Optional[Union[pg.InfiniteLine, pg.LineSegmentROI, pg.LinearRegionItem]]=None) -> Tuple[np.ndarray, np.ndarray, str, Union[str, Tuple[str, str]]]:
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

        # Determine if we are handling single of average slice
        if sliceItem is None:
            if self.radioButtonSliceSingleHorizontal.isChecked() or self.radioButtonSliceAveragedHorizontal.isChecked() or self.radioButtonSliceSingleAny.isChecked():
                sliceType = 'single'
                if self.sliceOrientation=='vertical':
                    orientation = 'vertical'
                    xSlice = self.mousePos[0]
                elif self.sliceOrientation=='horizontal':
                    orientation = 'horizontal'
                    ySlice = self.mousePos[1]
                else:
                    orientation = 'any'
                    xSlice = ((self.mousePos[0]+self.xData[0])/2, (self.mousePos[0]+self.xData[-1])/2)
                    ySlice = ((self.mousePos[1]+self.yData[0])/2, (self.mousePos[1]+self.yData[-1])/2)
            else:
                sliceType = 'averaged'
                if self.sliceOrientation=='vertical':
                    orientation = 'vertical'
                    dx = (self.xData[-1]-self.xData[0])/20
                    xSlice = (self.mousePos[0]-dx, self.mousePos[0]+dx)
                elif self.sliceOrientation=='horizontal':
                    orientation = 'horizontal'
                    dy = (self.yData[-1]-self.yData[0])/20
                    ySlice = (self.mousePos[1]-dy, self.mousePos[1]+dy)
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
                sliceLegend   = '{} = {}{}'.format(self.plotItem.axes['bottom']['item'].labelText,
                                                   self._parse_number(self.xData[n], 3, unified=True),
                                                   self.plotItem.axes['bottom']['item'].labelUnits)
                sliceLabel = '{}{}'.format(self._parse_number(self.xData[n], 3, unified=True), self.plotItem.axes['bottom']['item'].labelUnits)
            elif orientation=='horizontal':

                n = np.abs(self.yData-ySlice).argmin()
                sliceX        = self.xData
                sliceY        = self.zData[:,n]
                sliceLegend   = '{} = {}{}'.format(self.plotItem.axes['left']['item'].labelText,
                                                   self._parse_number(self.yData[n], 3, unified=True),
                                                   self.plotItem.axes['left']['item'].labelUnits)
                sliceLabel = '{}{}'.format(self._parse_number(self.yData[n], 3, unified=True), self.plotItem.axes['left']['item'].labelUnits)
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
                x_index = np.linspace(x0_index, x1_index, nb_points).astype(np.int)
                y_index = np.linspace(y0_index, y1_index, nb_points).astype(np.int)

                # sliceX = np.sqrt(self.xData[x_index]**2 + self.yData[y_index]**2)
                sliceX = (self.xData[x_index], self.yData[y_index])
                # sliceY =
                sliceY = self.zData[x_index,y_index]
                # print(sliceY.shape)
                # print(sliceX)

                # theta = np.angle(xSlice[1]-xSlice[0] + 1j*(ySlice[1]-ySlice[0]))
                # print(np.rad2deg(theta))

                # a = 1
                # b = (xSlice[1]-xSlice[0])/(self.xData[1]-self.xData[0])
                # c = (xSlice[1]-xSlice[0])/(self.xData[1]-self.xData[0])
                # d = 1

                # aa = d/(a*d-b*c)
                # bb = b/(b*c-a*d)
                # cc = c/(b*c-a*d)
                # dd = d/(a*d-b*c)

                # xx = self.xData[x_index]*aa + self.yData[y_index]*bb
                # yy = self.xData[x_index]*cc + self.yData[y_index]*dd

                # print(yy)
                # sliceX = yy

                sliceLegend = 'From ({}{}, {}{}) to ({}{}, {}{})'.format(self._parse_number(xSlice[0], 3, unified=True), self.plotItem.axes['bottom']['item'].labelUnits,
                                                                         self._parse_number(ySlice[0], 3, unified=True), self.plotItem.axes['left']['item'].labelUnits,
                                                                         self._parse_number(xSlice[1], 3, unified=True), self.plotItem.axes['bottom']['item'].labelUnits,
                                                                         self._parse_number(ySlice[1], 3, unified=True), self.plotItem.axes['left']['item'].labelUnits,)
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
                sliceLegend   = '{}: from {}{} to {}{}, mean: {}{}, nb samples: {}'.format(self.plotItem.axes['bottom']['item'].labelText,
                                                                                         self._parse_number(self.xData[nmin], 3, unified=True),
                                                                                         self.plotItem.axes['bottom']['item'].labelUnits,
                                                                                         self._parse_number(self.xData[nmax], 3, unified=True),
                                                                                         self.plotItem.axes['bottom']['item'].labelUnits,
                                                                                         self._parse_number((self.xData[nmin]+self.xData[nmax])/2, 3, unified=True),
                                                                                         self.plotItem.axes['bottom']['item'].labelUnits,
                                                                                         int(nmax-nmin))
                sliceLabel = ('{}{}'.format(self._parse_number(self.xData[nmin], 3, unified=True), self.plotItem.axes['bottom']['item'].labelUnits),
                              '{}{}'.format(self._parse_number(self.xData[nmax], 3, unified=True), self.plotItem.axes['bottom']['item'].labelUnits))
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
                sliceLegend   = '{}: from {}{} to {}{}, mean: {}{}, nb samples: {}'.format(self.plotItem.axes['left']['item'].labelText,
                                                                                         self._parse_number(self.yData[nmin], 3, unified=True),
                                                                                         self.plotItem.axes['left']['item'].labelUnits,
                                                                                         self._parse_number(self.yData[nmax], 3, unified=True),
                                                                                         self.plotItem.axes['left']['item'].labelUnits,
                                                                                         self._parse_number((self.yData[nmin]+self.yData[nmax])/2, 3, unified=True),
                                                                                         self.plotItem.axes['left']['item'].labelUnits,
                                                                                         int(nmax-nmin))
                sliceLabel = ('{}{}'.format(self._parse_number(self.yData[nmin], 3, unified=True), self.plotItem.axes['left']['item'].labelUnits),
                              '{}{}'.format(self._parse_number(self.yData[nmax], 3, unified=True), self.plotItem.axes['left']['item'].labelUnits))

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
        if not hasattr(self, 'mousePos'):
            return

        # If double click is detected and mouse is over the viewbox, we launch
        # a 1d plot corresponding to a data slice
        if e._double and self.isMouseOverView():

            # Get the data of the slice
            sliceX, sliceY, sliceLegend, sliceLabel = self.getDataSlice()

            # If there is no 1d plot already showing the slice
            if not self.isThereSlicePlot():

                self.addSliceItemAndPlot(data          = (sliceX, sliceY),
                                         curveLegend   = sliceLegend,
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
                                             curveLegend  = sliceLegend,
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
                                  curveLegend: str,
                                  sliceItem: str,
                                  sliceOrientation: Optional[str]=None,
                                  plotRef: Optional[str]=None,
                                  position: Optional[float]=None) -> None:

        # when we interact with the map, we do not allow swapping
        self.checkBoxSwapxy.setEnabled(False)

        # If sliceOrientation is None, users just doubleClick on the plotItem
        # The sliceOrientation is the one given by the GUI
        if sliceOrientation is None:
            sliceOrientation = self.sliceOrientation

        yLabelText  = self.zLabelText
        yLabelUnits = self.zLabelUnits

        title = self.title+" <span style='color: red; font-weight: bold;'>Extrapolated data</span>"
        windowTitle = self.windowTitle+' - '+sliceOrientation+' slice'
        runId          = self.runId

        # Should be called once for both addplot and addSliceItem
        curveId = self.getCurveId()

        if sliceOrientation in ('vertical', 'horizontal'):

            if plotRef is None:
                plotRef = self.plotRef+sliceOrientation

            if sliceOrientation=='vertical':
                xLabelText  = self.yLabelText
                xLabelUnits = self.yLabelUnits

            elif sliceOrientation=='horizontal':
                xLabelText  = self.xLabelText
                xLabelUnits = self.xLabelUnits

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
                plotRefHorizontal = self.plotRef+sliceOrientation+'horizontal'
                plotRefVertical   = self.plotRef+sliceOrientation+'vertical'


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
                                               self.xLabelText, # xLabelText
                                               self.xLabelUnits, # xLabelUnits
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
                                               self.yLabelText, # xLabelText
                                               self.yLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits

        # To add a slice item, we need to keep track of
        self.addSliceItem(curveId          = curveId,
                          sliceOrientation = sliceOrientation,
                          sliceItem        = sliceItem,
                          position         = position)



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
        if self.checkBoxSubtractAverageX.isChecked():
            zData = zData - np.nanmean(zData, axis=0)
        if self.checkBoxSubtractAverageY.isChecked():
            zData = (zData.T - np.nanmean(zData, axis=1)).T

        # Data unwrapping
        if self.checkBoxUnwrapX.isChecked():
            zData[~np.isnan(zData)] = np.unwrap(np.ravel(zData[~np.isnan(zData)], order='F'))
        if self.checkBoxUnwrapY.isChecked():
            zData[~np.isnan(zData)] = np.unwrap(np.ravel(zData[~np.isnan(zData)], order='C'))

        # Polynomial fit removal
        if self.spinBoxSubtractPolyX.value()>0:
            for i, z in enumerate(zData):
                c = np.polynomial.Polynomial.fit(self.yData, z, self.spinBoxSubtractPolyX.value())
                zData[i] = c(self.yData)
        if self.spinBoxSubtractPolyY.value()>0:
            for i, z in enumerate(zData.T):
                c = np.polynomial.Polynomial.fit(self.xData, z, self.spinBoxSubtractPolyY.value())
                zData[:,i] = c(self.xData)

        # Depending on the asked derivative, we calculate the new z data and
        # the new z label
        # Since only one derivative at a time is possible, we use elif here
        label = str(self.comboBoxDerivative.currentText())
        if label=='∂z/∂x':
            zData = np.gradient(zData, self.xData, axis=0)
            self.plot2dzLabel.setText(self.zLabelText+' ('+self.zLabelUnits+'/'+self.xLabelUnits+')')
        elif label=='∂z/∂y':
            zData = np.gradient(zData, self.yData, axis=1)
            self.plot2dzLabel.setText(self.zLabelText+' ('+self.zLabelUnits+'/'+self.yLabelUnits+')')
        elif label=='√((∂z/∂x)² + (∂z/∂y)²)':
            zData = np.sqrt(np.gradient(zData, self.xData, axis=0)**2. + np.gradient(zData, self.yData, axis=1)**2.)
            self.plot2dzLabel.setText(self.zLabelText+' ('+self.zLabelUnits+' x √('+self.xLabelUnits+'² + '+self.yLabelUnits+'²)')
        elif label=='∂²z/∂x²':
            zData = np.gradient(np.gradient(zData, self.xData, axis=0), self.xData, axis=0)
            self.plot2dzLabel.setText(self.zLabelText+' ('+self.zLabelUnits+'/'+self.xLabelUnits+'²)')
        elif label=='∂²z/∂y²':
            zData = np.gradient(np.gradient(zData, self.yData, axis=1), self.yData, axis=1)
            self.plot2dzLabel.setText(self.zLabelText+' ('+self.zLabelUnits+'/'+self.yLabelUnits+'²)')
        else:
            self.plot2dzLabel.setText(self.zLabelText+' ('+self.zLabelUnits+')')

        self.updateImageItem(self.xData, self.yData, zData)



    ####################################
    #
    #           Colormap
    #
    ####################################



    def comboBoxcmChanged(self, index:int) -> None:
        """
        Method called when user clicks on the colorbar comboBox

        Parameters
        ----------
        index : int
            index of the colorbar
        """

        self.cbcmInvert(self.checkBoxInvert)



    def cbcmInvert(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user clicks the inverted colormap checkbox.

        Parameters
        ----------
        b : QtWidgets.QCheckBox
            Invert colormap checkbox.
        """

        if b.isChecked():
            self.colorMapInversed = True
        else:
            self.colorMapInversed = False

        self.setColorMap(self.comboBoxcm.currentText())



    def setColorMap(self, cm: str) -> None:
        """
        Set the colormap of the imageItem from the colormap name.
        See the palettes file.

        Parameters
        ----------
        cm : str
            colormap name
        """

        rgba_colors = [hex_to_rgba(i) for i in palettes.all_palettes[cm][self.config['2dMapNbColorPoints']]]

        if self.colorMapInversed:
            rgba_colors = [i for i in reversed(rgba_colors)]

        pos = np.linspace(0, 1, self.config['2dMapNbColorPoints'])
        # Set the colormap
        pgColormap =  pg.ColorMap(pos, rgba_colors)
        self.histWidget.item.gradient.setColorMap(pgColormap)



    ####################################
    #
    #           FindSlope
    #
    ####################################



    def cbFindSlope(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user clicks on the Find slope checkbox.
        Display a LineSegmentROI with information about its angle and length ratio.

        Parameters
        ----------
        b : QtWidgets.QCheckBox
            Draw isocurve checkbox
        """

        # Uncheck
        if b==0:
            self.findSlopeLineRemove(self.findSlopeLines[-1])
            del(self.findSlopeLines)
            self.findSlopesb.deleteLater()
            self.horizontalLayoutFindSlope.removeWidget(self.findSlopesb)
        # Check
        else:

            # Add a spinBox in the GUI and create an empty list to keep track of
            # all the future findSlope widgets
            self.findSlopeLines: List[pg.LineSegmentROI]= []
            self.findSlopesb = QtWidgets.QSpinBox()
            self.findSlopesb.setValue(1)

            self.findSlopesb.valueChanged.connect(self.findSlopesbChanged)
            self.horizontalLayoutFindSlope.addWidget(self.findSlopesb)

            self.findSlopesbChanged()



    def findSlopesbChanged(self):
        """
        Method called when user clicks on the findSlope spinBox.
        Its value defines the number of findSlope widget displayed on the
        plotItem.
        """

        nbFindSlope = self.findSlopesb.value()
        # If there is no findSlope widget to display, we remove the spinBox widget
        if nbFindSlope==0:
            self.checkBoxFindSlope.setChecked(False)
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



    def cbIsoCurve(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user clicks on the Draw isocurve checkbox.

        Parameters
        ----------
        b : QtWidgets.QCheckBox
            Draw isocurve checkbox
        """

        # If the user uncheck the box, we hide the items
        if b==0:

            self.isoCurve.hide()
            self.isoLine.hide()
        # When user check the box we create the items and the events
        else:

            # If items do not exist, we create them
            if self.isoCurve is not None:

                self.isoCurve.show()
                self.isoLine.show()

            else:
                z = self.imageView.image

                self.penIsoLine = pg.mkPen(color='w', width=2)
                # Isocurve drawing
                self.isoCurve = pg.IsocurveItem(level=0.5, pen=self.penIsoLine)
                self.isoCurve.setParentItem(self.imageView.imageItem)
                self.isoCurve.setZValue(np.median(z[~np.isnan(z)]))
                # build isocurves
                zTemp = np.copy(z)
                # We can't have np.nan value in the isocurve so we replace
                # them by small value
                zTemp[np.isnan(zTemp)] = zTemp[~np.isnan(zTemp)].min()-1000
                self.isoCurve.setData(zTemp)


                # Draggable line for setting isocurve level
                self.isoLine = pg.InfiniteLine(angle=0, movable=True, pen=self.penIsoLine)
                self.histWidget.item.vb.addItem(self.isoLine)
                self.histWidget.item.vb.setMouseEnabled(y=False) # makes user interaction a little easier
                self.isoLine.setValue(np.median(z[~np.isnan(z)]))
                self.isoLine.setZValue(1000) # bring iso line above contrast controls

                # Connect event
                self.isoLine.sigDragged.connect(self.draggedIsoLine)



    def draggedIsoLine(self) -> None:
        """
        Method called when user drag the iso line display on the histogram.
        By simply updating the value of the isoCurve, the plotItem will update
        itself.
        """

        self.isoCurve.setLevel(self.isoLine.value())



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

        if self.checkBoxMaximum.isChecked():
            self.maximumPlotRef = self.plotRef+'maximum'
            self.maximumCurveId = self.getCurveId()

            self.interactionRefs['maximum'] = {'plotRef' : self.maximumPlotRef,
                                               'nbCurve' : 1,
                                               'colorIndexes' : []}

            self.signal2MainWindowAddPlot.emit(self.runId, # runId
                                               self.maximumCurveId, # curveId
                                               self.windowTitle+' - maximum', # plotTitle
                                               self.windowTitle+' - maximum', # windowTitle
                                               self.maximumPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.maximumGetData(), # data
                                               self.xLabelText, # xLabelText
                                               self.xLabelUnits, # xLabelUnits
                                               self.yLabelText, # yLabelText
                                               self.yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        else:
            self.signalClose1dPlot.emit(self.plotRef+'maximum')



    def maximumUpdateCurve(self) -> None:
        if hasattr(self, 'maximumPlotRef'):
            x, y = self.maximumGetData()
            self.signalUpdateCurve.emit(self.maximumPlotRef,
                                        self.maximumCurveId,
                                        '',
                                        x,
                                        y)



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

        if self.checkBoxMinimum.isChecked():
            self.minimumPlotRef = self.plotRef+'minimum'
            self.minimumCurveId = self.getCurveId()
            y = self.yData[np.nanargmax(self.zData, axis=1)]

            self.interactionRefs['minimum'] = {'plotRef' : self.minimumPlotRef,
                                               'nbCurve' : 1,
                                               'colorIndexes' : []}

            self.signal2MainWindowAddPlot.emit(self.runId, # runId
                                               self.minimumCurveId, # curveId
                                               self.windowTitle+' - minimum', # plotTitle
                                               self.windowTitle+' - minimum', # windowTitle
                                               self.minimumPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.minimumGetData(), # data
                                               self.xLabelText, # xLabelText
                                               self.xLabelUnits, # xLabelUnits
                                               self.yLabelText, # yLabelText
                                               self.yLabelUnits, # yLabelUnits
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
            self.signalUpdateCurve.emit(self.minimumPlotRef,
                                        self.minimumCurveId,
                                        '',
                                        x,
                                        y)



    def interactionCurveClose(self, curveId: str) -> None:
        """
        Called from MainWindow when sub-interaction plot is closed.
        Uncheck their associated checkBox
        """
        if 'minimum' in curveId:
            self.checkBoxMinimum.setChecked(False)
            del(self.minimumPlotRef)
            del(self.minimumCurveId)
        elif 'maximumPlotRef' in curveId:
            self.checkBoxMaximum.setChecked(False)
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