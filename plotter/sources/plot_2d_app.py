# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LinearRegionItem import LinearRegionItem
import pyqtgraph.opengl as gl
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
from typing import Union, Tuple, Callable, Optional
import inspect
import uuid

from ..ui.plot2d import Ui_Dialog
from . import palettes # File copy from bokeh: https://github.com/bokeh/bokeh/blob/7cc500601cdb688c4b6b2153704097f3345dd91c/bokeh/palettes.py
from .plot_app import PlotApp
from .config import config
from . import fit



class Plot2dApp(QtWidgets.QDialog, Ui_Dialog, PlotApp):
    """
    Class to handle ploting in 2d.
    """

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
                       cleanCheckBox  : Callable[[str, str, int, Union[str, list]], None],
                       plotRef        : str,
                       dataBaseName   : str,
                       dataBaseAbsPath: str,
                       addPlot        : Callable,
                       removePlot     : Callable,
                       getPlotFromRef : Callable,
                       livePlot       : bool=False,
                       parent         = None):
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
        livePlot : bool, optional
            Is the current plot a livePlot, by default False
        parent : , optional
        """
        super(Plot2dApp, self).__init__(parent)

        self.setupUi(self)

        # Must be set on False, see
        # https://github.com/pyqtgraph/pyqtgraph/issues/1371
        self.widget.useOpenGL(False)

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
        self.cleanCheckBox = cleanCheckBox
        self.plotRef       = plotRef

        # Method from the MainApp to add plot window
        # Used for data slicing
        self.addPlot         = addPlot
        self.removePlot      = removePlot
        self.getPlotFromRef = getPlotFromRef

        # If the plot is displaying a qcodes run that is periodically updated
        self.livePlot       = livePlot

        # Store references to infiniteLines creating by data slicing
        self.sliceItems = {}
        self.sliceOrientation = 'vertical'

        # Store the isoCurve and isoLine object
        self.isoCurve = None
        self.isoLine  = None

        self.axesIsSwapped = False

        # Store the references to linked 1d plots, object created when user
        # create a slice of data
        # self.linked1dPlots = {'vertical'   : None,
        #                       'horizontal' : None}

        # Reference to the extracted window
        self.extractionWindow = None

        # Reference to the fit window
        self.extractiofitWindow = None

        # Initialize font size spin button with the config file
        self.spinBoxFontSize.setValue(config['axisLabelFontSize'])


        # Get plotItem from the widget
        self.plotItem = self.widget.getPlotItem()
        self.resize(*config['dialogWindowSize'])


        # Create a Image item to host the image view
        self.imageItem = pg.ImageItem(image=np.array([[0,0],[0,0]]))
        self.imageItem.autoDownsample = config['2dDownSampling']
        self.imageView = pg.ImageView(imageItem=self.imageItem)

        # Embed the plot item in the graphics layout
        self.plotItem.vb.addItem(self.imageItem)

        # Allow ticklabels to be changed
        font=QtGui.QFont()
        font.setPixelSize(config['tickLabelFontSize'])

        # Create a histogram item linked to the imageitem
        self.histWidget.setImageItem(self.imageItem)
        self.histWidget.autoHistogramRange()
        self.histWidget.setFixedWidth(100)
        self.histWidget.item.setLevels(min=z[~np.isnan(z)].min(), max=z[~np.isnan(z)].max())
        self.histWidget.axis.setTickFont(font)

        self.setImageView()


        # Axes label
        self.plotItem.setTitle(title=title, color=config['styles'][config['style']]['pyqtgraphTitleTextColor'])
        self.plotItem.showGrid(x=True, y=True)
        self.plotItem.setLabel(axis='bottom',
                               text=self.xLabelText,
                               units=self.xLabelUnits,
                               **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                                'font-size' : str(config['axisLabelFontSize'])+'pt'})
        self.plotItem.setLabel(axis='left',
                               text=self.yLabelText,
                               units=self.yLabelUnits,
                               **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                                'font-size' : str(config['axisLabelFontSize'])+'pt'})

        # The only reliable way I have found to correctly display the zLabel
        # is by using a Qlabel from the GUI
        self.plot2dzLabel.setText(zLabelText+' ('+zLabelUnits+')')
        self.plot2dzLabel.setFont(font)

        # Style
        self.plotItem.getAxis('bottom').setTickFont(font)
        self.plotItem.getAxis('left').setTickFont(font)
        self.plotItem.getAxis('bottom').setPen(config['styles'][config['style']]['pyqtgraphxAxisTicksColor'])
        self.plotItem.getAxis('left').setPen(config['styles'][config['style']]['pyqtgraphyAxisTicksColor'])
        self.histWidget.item.axis.setPen(config['styles'][config['style']]['pyqtgraphzAxisTicksColor'])

        self.setWindowTitle(windowTitle)

        self.setStyleSheet("background-color: "+str(config['styles'][config['style']]['dialogBackgroundColor'])+";")
        self.setStyleSheet("color: "+str(config['styles'][config['style']]['dialogTextColor'])+";")


        # Connect UI
        self.checkBoxDrawIsoCurve.stateChanged.connect(self.cbIsoCurve)
        self.checkBoxInvert.stateChanged.connect(lambda : self.cbcmInvert(self.checkBoxInvert))
        self.checkBoxMaximum.stateChanged.connect(self.checkBoxExtractionState)
        self.checkBoxMinimum.stateChanged.connect(self.checkBoxExtractionState)
        self.checkBoxSwapxy.stateChanged.connect(self.checkBoxSwapxyState)
        self.checkBoxAspectEqual.stateChanged.connect(self.checkBoxAspectEqualState)
        self.checkBoxSubtractAverageX.stateChanged.connect(self.zDataTransformation)
        self.checkBoxSubtractAverageY.stateChanged.connect(self.zDataTransformation)
        self.checkBoxUnwrapX.stateChanged.connect(self.zDataTransformation)
        self.checkBoxUnwrapY.stateChanged.connect(self.zDataTransformation)
        self.pushButton3d.clicked.connect(self.launched3d)
        self.spinBoxFontSize.valueChanged.connect(self.clickFontSize)
        self.plotItem.scene().sigMouseClicked.connect(self.plotItemDoubleClicked)
        self.radioButtonSliceSingleHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceSingleVertical.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceAveragedHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceAveragedVertical.toggled.connect(self.radioBoxSliceChanged)

        # UI for the derivative combobox
        for label in config['plot2dDerivative']:
            self.comboBoxDerivative.addItem(label)
        self.comboBoxDerivative.activated.connect(self.zDataTransformation)


        # Add fitting function to the GUI
        self.initFitGUI()
        # Reference to QDialog which will contains fit info
        self.fitWindow = None


        ## Colormap initialization

        # Build the colormap comboBox, the default one being from the config file
        index = 0
        indexViridis = 0
        for cm in [i for i in palettes.all_palettes.keys() if i[-2:] !='_r']:
            self.comboBoxcm.addItem(cm)
            if cm==config['plot2dcm']:
                indexViridis = index

            index += 1

        self.colorMapInversed = False
        self.setColorMap(config['plot2dcm'])
        self.comboBoxcm.setCurrentIndex(indexViridis)
        self.comboBoxcm.currentIndexChanged.connect(self.comboBoxcmChanged)

        # Should be initialize last
        PlotApp.__init__(self, dataBaseName, dataBaseAbsPath)



    ####################################
    #
    #           Method to close stuff
    #
    ####################################



    def closeEvent(self, evnt):
        """
        Method called when use closed the plotWindow.
        We propagate that event to the mainWindow
        """

        self.cleanCheckBox(plotRef     = self.plotRef,
                           windowTitle = self.windowTitle,
                           runId       = self.runId,
                           label      = self.zLabelText)

        # If user created data slice, we close the linked 1d plot
        if self.getPlotRefFromSliceOrientation('vertical') is not None:
            self.getPlotRefFromSliceOrientation('vertical').close()
        if self.getPlotRefFromSliceOrientation('horizontal') is not None:
            self.getPlotRefFromSliceOrientation('horizontal').close()

        # If user extracted the maximum
        if self.extractionWindow is not None:
            self.extractionWindow.close()

        # If user fit the maximum
        if self.fitWindow is not None:
            self.fitWindow.close()


    def o(self):
        self.close()



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
        w = gl.GLViewWidget()
        w.show()
        w.setWindowTitle(self.windowTitle)
        w.setCameraPosition(distance=3)

        # Linearly scale all data from 0 to 1
        x = (self.xData - np.nanmin(self.xData))/(np.nanmax(self.xData) - np.nanmin(self.xData))
        y = (self.yData - np.nanmin(self.yData))/(np.nanmax(self.yData) - np.nanmin(self.yData))
        z = (self.zData - np.nanmin(self.zData))/(np.nanmax(self.zData) - np.nanmin(self.zData))

        p = gl.GLSurfacePlotItem(x=x, y=y, z=z, shader='shaded', smooth=False)
        w.addItem(p)



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


        self.checkBoxSubtractAverageXState()
        self.checkBoxSubtractAverageYState()

        self.comboBoxDerivativeActivated(None)

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



    ####################################
    #
    #           Method to related to display
    #
    ####################################


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
                self.swapSlices()
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
                self.swapSlices()



    def clickFontSize(self) -> None:
        """
        Called when user click on the spinBoxFontSize button.
        Modify the size of the label and ticks label accordingly to
        the button number.
        Modify the config file so that other plot window launched
        afterwards have the same fontsize.
        """


        config['axisLabelFontSize'] = int(self.spinBoxFontSize.value())
        config['tickLabelFontSize'] = int(self.spinBoxFontSize.value())

        self.plotItem.setLabel(axis='bottom',
                               text=self.plotItem.axes['bottom']['item'].labelText,
                               units=self.plotItem.axes['bottom']['item'].labelUnits,
                               **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(config['axisLabelFontSize'])+'pt'})
        self.plotItem.setLabel(axis='left',
                               text=self.plotItem.axes['left']['item'].labelText,
                               units=self.plotItem.axes['left']['item'].labelUnits,
                               **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(config['axisLabelFontSize'])+'pt'})

        font=QtGui.QFont()
        font.setPixelSize(config['tickLabelFontSize'])
        self.plotItem.getAxis('bottom').setTickFont(font)
        self.plotItem.getAxis('left').setTickFont(font)

        self.plot2dzLabel.setFont(font)
        self.histWidget.axis.setTickFont(font)



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
        else:
            sliceItem = 'LinearRegionItem'

        return sliceItem



    def getPlotRefFromSliceOrientation(self, sliceOrientation: str) -> Union[str, None]:
        """
        Return the 1d plot containing the slice data of this 2d plot.
        Is based on the getPlotFromRef from MainApp but swap orientation when
        checkBoxSwapxy is checked.

        Parameters
        ----------
        sliceOrientation : str
            Orientation of the slice we are interested in.
        """

        if self.checkBoxSwapxy.isChecked():
            if sliceOrientation=='vertical':
                return self.getPlotFromRef(self.plotRef, 'horizontal')
            else:
                return self.getPlotFromRef(self.plotRef, 'vertical')
        else:
            return self.getPlotFromRef(self.plotRef, sliceOrientation)



    def getSliceItemOrientation(self, sliceItem: Union[pg.InfiniteLine, pg.LinearRegionItem]) -> str:
        """
        Return the orientation of the sliceItem.

        Parameters
        ----------
        sliceItem : sliceItem currently being dragged.

        Return
        ------
        orientation : str
            Either "horizontal" or "vertical".
        """

        if isinstance(sliceItem, pg.InfiniteLine):
            if int(sliceItem.angle%180)==0:
                lineOrientation = 'horizontal'
            else:
                lineOrientation = 'vertical'
        else:
            lineOrientation = sliceItem.orientation

        return lineOrientation



    def radioBoxSliceChanged(self, b: int) -> None:
        """
        Method called when user change the data slice orientation.
        """

        if self.radioButtonSliceSingleHorizontal.isChecked() or self.radioButtonSliceAveragedHorizontal.isChecked():
            self.sliceOrientation = 'horizontal'
        else:
            self.sliceOrientation = 'vertical'


    @staticmethod
    def getCurveId() -> str:
        """
        Return a unique id for every data slice.
        """

        return str(uuid.uuid1())



    def dragSliceItem(self, sliceItem : Union[pg.InfiniteLine, pg.LinearRegionItem],
                            curveId          : str,
                            lineOrientation  : str) -> None:
        """
        Method call when user drag a slice line.

        Parameters
        ----------
        sliceItem : pg.InfiniteLine
            sliceItem currently being dragged.
        curveId : str
            ID of the curve associated to the slice being dragged
        """

        # We get the slice data from the 2d plot
        sliceX, sliceY, sliceLegend, slicePosition = self.getDataSlice(sliceItem=sliceItem)

        # We update the curve associated to the sliceLine
        self.getPlotFromRef(self.plotRef, lineOrientation)\
        .updatePlotDataItem(x                  = sliceX,
                            y                  = sliceY,
                            curveId            = curveId,
                            curveLegend        = sliceLegend,
                            curveSlicePosition = slicePosition)

        # We update the label of the infinity line with the value corresponding
        # to the cut
        if isinstance(sliceItem, pg.InfiniteLine):
            sliceItem.label.setFormat('{:0.2e}'.format(slicePosition))
        else:
            sliceItem.labelmin.setFormat('{:0.2e}'.format(slicePosition[0]))
            sliceItem.labelmax.setFormat('{:0.2e}'.format(slicePosition[1]))

        # We overide a pyqtgraph attribute when user drag an infiniteLine
        self.sliceItems[curveId].mouseHovering  = True



    def addSliceItem(self, curveId: str,
                           sliceOrientation: str,
                           sliceItem: str,
                           position: Optional[float]=None) -> None:
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
        colorIndex = self.getPlotFromRef(self.plotRef, sliceOrientation).curves[curveId].colorIndex
        pen = pg.mkPen(color=config['plot1dColors'][colorIndex],
                       width=config['crossHairLineWidth'],
                       style=QtCore.Qt.SolidLine)
        hoverPen = pg.mkPen(color=config['plot1dColors'][colorIndex],
                       width=config['crossHairLineWidth'],
                       style=QtCore.Qt.DashLine)

        # When the user click we add a vertical or horizontale sliceItem where he clicked.
        if sliceOrientation=='vertical':
            angle = 90.
            pos = self.mousePos[0]
        else:
            angle = 0.
            pos = self.mousePos[1]

        # If the position has been given it means we are swapping the axes.
        if position is not None:
            pos = position

        # If we are adding an InfiniteLine
        if sliceItem=='InfiniteLine':
            # The label is empty for now
            t = pg.InfiniteLine(pos=pos,
                                angle=angle,
                                movable=True,
                                pen=pen,
                                hoverPen=hoverPen,
                                label='',
                                labelOpts={'position' : 0.9,
                                        'movable' : True,
                                        'fill': config['plot1dColors'][colorIndex]})

            t.sigDragged.connect(lambda lineItem=t,
                                        curveId=curveId,
                                        lineOrientation=sliceOrientation:
                                        self.dragSliceItem(lineItem,
                                                           curveId,
                                                           lineOrientation))
        # If we are adding an LinearRegionItem
        else:
            t = pg.LinearRegionItem(values=[pos, pos],
                                    orientation=sliceOrientation,
                                    pen=pen,
                                    hoverPen=hoverPen,
                                    swapMode='push')
            t.labelmin = pg.InfLineLabel(line=t.lines[0],
                            text='',
                            movable=True,
                            position=0.9,
                            fill=config['plot1dColors'][colorIndex])
            t.labelmax = pg.InfLineLabel(line=t.lines[1],
                            text='',
                            movable=True,
                            position=0.9,
                            fill=config['plot1dColors'][colorIndex])

            # For both slicing itens we attached a drag event to it
            t.sigRegionChanged.connect(lambda lineItem=t,
                                        curveId=curveId,
                                        lineOrientation=sliceOrientation:
                                        self.dragSliceItem(lineItem,
                                                           curveId,
                                                           lineOrientation))

        # Add the slicing item
        self.plotItem.addItem(t)

        # We save a reference to the slicing item
        self.sliceItems[curveId] = t

        # We call the dragSliceLine method to update the label(s) of the slicing
        # item
        self.dragSliceItem(sliceItem=t,
                           curveId=curveId,
                           lineOrientation=sliceOrientation)



    def removeSliceItem(self, curveId: str) -> None:
        """
        Remove sliceItem from the plot and from memory.

        Parameters
        ----------
        curveId : str
            [description]
        """
        self.plotItem.removeItem(self.sliceItems[curveId])
        del(self.sliceItems[curveId])



    def cleanSliceItem(self, plotRef     : str,
                                windowTitle : str,
                                runId       : int,
                                label       : Union[str, list]) -> None:
        """
        Called when a linked 1dPlot is closed.
        Has to have the same signature as cleanCheckBox, see MainApp.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getplotRef.
        windowTitle : str
            Window title, see getWindowTitle.
        runId : int
            Data run id of the database.
        label : Union[str, list]
            Label of the dependent parameter.
            Will be empty for signal from Plot1dApp since this parameter is only
            usefull for Plot2dApp.
        """


        # We clean the reference of the linked 1d plot
        if 'vertical' in plotRef:
            searchedAngle = 90
            searchedOrientation = 'vertical'
        else:
            searchedAngle =  0
            searchedOrientation = 'horizontal'

        # Get all the curve Id to be removed
        curvesId = []
        for key, val in self.sliceItems.items():
            if isinstance(val, pg.InfiniteLine):
                if val.angle==searchedAngle:
                    curvesId.append(key)
            elif isinstance(val, pg.LinearRegionItem):
                if val.orientation==searchedOrientation:
                    curvesId.append(key)

        # Effectively remove the infinity line and the curve linked to it
        [self.removeSliceItem(curveId) for curveId in curvesId]
        [self.removePlot(plotRef, curveId) for curveId in curvesId]



    def getDataSlice(self, sliceItem: Optional[Union[pg.InfiniteLine, pg.LinearRegionItem]]=None) -> Tuple[np.ndarray, np.ndarray, str, float]:
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

        xSlice = None
        ySlice = None

        # When sliceItem is None, We are creating the dataSlice
        if sliceItem is None:
            if self.sliceOrientation=='vertical':
                xSlice = self.mousePos[0]
            else:
                ySlice = self.mousePos[1]
        # Otherwise the dataSlice exist and return its position depending of its
        # orientation
        else:
            if self.getSliceItemOrientation(sliceItem)=='vertical':
                if hasattr(sliceItem, 'value'):
                    xSlice = sliceItem.value()
                else:
                    xSlice = sliceItem.getRegion()
            else:
                if hasattr(sliceItem, 'value'):
                    ySlice = sliceItem.value()
                else:
                    ySlice = sliceItem.getRegion()

        if isinstance(xSlice, float) or isinstance(ySlice, float):
            # Depending on the slice we return the x and y axis data and the legend
            # associated with the cut.
            if ySlice is None:

                n = np.abs(self.xData-xSlice).argmin()
                sliceX        = self.yData
                sliceY        = self.zData[n]
                slicePosition = self.xData[n]
                sliceLegend   = '{} = {:.3e} {}'.format(self.plotItem.axes['bottom']['item'].labelText,
                                                        slicePosition,
                                                        self.plotItem.axes['bottom']['item'].labelUnits)
            else:

                n = np.abs(self.yData-ySlice).argmin()
                sliceX        = self.xData
                sliceY        = self.zData[:,n]
                slicePosition = self.yData[n]
                sliceLegend   = '{} = {:.3e} {}'.format(self.plotItem.axes['left']['item'].labelText,
                                                        slicePosition,
                                                        self.plotItem.axes['left']['item'].labelUnits)

            if isinstance(slicePosition, np.ndarray):
                slicePosition = slicePosition[0]

        else:
            # Depending on the slice we return the x and y axis data and the legend
            # associated with the cut.
            if ySlice is None:
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
                slicePosition = (self.xData[nmin], self.xData[nmax])
                # Legend written in html
                # &#60; means <
                # &#62; means >
                sliceLegend   = '{} ({}): {:.3e}, {:.3e}&#60;-&#62;{:.3e}, {}'.format(self.plotItem.axes['bottom']['item'].labelText,
                                                                                      self.plotItem.axes['bottom']['item'].labelUnits,
                                                                                      (slicePosition[0]+slicePosition[1])/2,
                                                                                      slicePosition[0],
                                                                                      slicePosition[1],
                                                                                      int(nmax-nmin))
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
                slicePosition = (self.yData[nmin], self.yData[nmax])
                # Legend written in html
                # &#60; means <
                # &#62; means >
                sliceLegend   = '{} ({}): {:.3e}, {:.3e}&#60;-&#62;{:.3e}, {}'.format(self.plotItem.axes['left']['item'].labelText,
                                                                                      self.plotItem.axes['left']['item'].labelUnits,
                                                                                      (slicePosition[0]+slicePosition[1])/2,
                                                                                      slicePosition[0],
                                                                                      slicePosition[1],
                                                                                      int(nmax-nmin))

        return sliceX, sliceY, sliceLegend, slicePosition



    def plotItemDoubleClicked(self, e) -> None:
        """
        When a use double click on the 2D plot, we create a slice of the colormap
        """

        # If double click is detected and mouse is over the viewbox, we launch
        # a 1d plot corresponding to a data slice
        if e._double and self.isMouseOverView():

            # Get the data of the slice
            sliceX, sliceY, sliceLegend, slicePosition = self.getDataSlice()

            # If nbCurve is 1, we create a sliceItem
            if self.getPlotRefFromSliceOrientation(self.sliceOrientation) is None:

                self.addSliceItemAndPlot(data         = [sliceX, sliceY],
                              curveLegend  = sliceLegend,
                              slicePosition= slicePosition,
                              sliceItem    = self.getCurrentSliceItem())
            # If not
            # 1. The user doubleClicked on an sliceItem and we remove it
            # 2. The doubleClicked somewhere else on the map and we create another slice
            else:
                # We check if user double click on an sliceItem
                clickedCurveId = self.sliceIdClickedOn(slicePosition)

                # If the user add a new sliceItem
                if clickedCurveId is None:
                    self.addSliceItemAndPlot(data         = [sliceX, sliceY],
                                  curveLegend  = sliceLegend,
                                  slicePosition= slicePosition,
                                  sliceItem    = self.getCurrentSliceItem())

                # We remove a slice
                else:
                    # If there is more than one slice, we remove it and the associated curve
                    if len(self.getPlotRefFromSliceOrientation(self.sliceOrientation).curves)>1:
                        self.getPlotRefFromSliceOrientation(self.sliceOrientation).removePlotDataItem(clickedCurveId)
                        self.removeSliceItem(clickedCurveId)
                    # If there is only one slice, we close the linked 1d plot
                    # which will remove the associated sliceItem
                    else:
                        self.getPlotRefFromSliceOrientation(self.sliceOrientation).removePlotDataItem(clickedCurveId)



    def sliceIdClickedOn(self, slicePosition:Union[float, Tuple[float, float]]) -> Optional[str]:
        """
        Return the id of the InfiniteLine or the LinearRegionItem that a user
        has clicked on.
        If the user didn't click on neither, return None

        Args:
            slicePosition ([float, tuple], optional):
                Position of a InfiniteLine.
                Positions of a LinearRegionItem.

        Returns:
            Optional[str]: None or the id of the slice.
        """

        clickedCurveId = None

        if self.getPlotRefFromSliceOrientation('vertical') is not None:
            for curveId, curve in self.getPlotRefFromSliceOrientation('vertical').curves.items():
                if isinstance(curve.curveSlicePosition, float):
                    if curve.curveSlicePosition==slicePosition:
                        clickedCurveId = curveId
                elif isinstance(curve.curveSlicePosition, tuple):
                    if curve.curveSlicePosition[0]<=slicePosition and curve.curveSlicePosition[1]>=slicePosition:
                        clickedCurveId = curveId
        if self.getPlotRefFromSliceOrientation('horizontal') is not None:
            for curveId, curve in self.getPlotRefFromSliceOrientation('horizontal').curves.items():
                if isinstance(curve.curveSlicePosition, float):
                    if curve.curveSlicePosition==slicePosition:
                        clickedCurveId = curveId
                elif isinstance(curve.curveSlicePosition, tuple):
                    if curve.curveSlicePosition[0]<=slicePosition and curve.curveSlicePosition[1]>=slicePosition:
                        clickedCurveId = curveId

        return clickedCurveId



    def addSliceItemAndPlot(self, data: list,
                                  curveLegend: str,
                                  slicePosition: float,
                                  sliceItem: str,
                                  sliceOrientation: Optional[str]=None,
                                  plotRef: Optional[str]=None,
                                  position: Optional[float]=None) -> None:

        if sliceOrientation is None:
            sliceOrientation = self.sliceOrientation
        if plotRef is None:
            plotRef = self.plotRef+sliceOrientation

        if sliceOrientation=='vertical':
            xLabelText  = self.yLabelText
            xLabelUnits = self.yLabelUnits
        else:
            xLabelText  = self.xLabelText
            xLabelUnits = self.xLabelUnits

        yLabelText  = self.zLabelText
        yLabelUnits = self.zLabelUnits

        title = self.title+" <span style='color: red; font-weight: bold;'>Extrapolated data</span>"
        windowTitle = self.windowTitle+' - '+sliceOrientation+' slice'
        cleanCheckBox  = self.cleanSliceItem
        runId          = self.runId

        # Should be called once for both addplot and addSliceItem
        curveId = self.getCurveId()

        self.addPlot(data           = data,
                     plotTitle      = title,
                     xLabelText     = xLabelText,
                     xLabelUnits    = xLabelUnits,
                     yLabelText     = yLabelText,
                     yLabelUnits    = yLabelUnits,
                     windowTitle    = windowTitle,
                     runId          = runId,
                     cleanCheckBox  = cleanCheckBox,
                     plotRef        = plotRef,
                     dataBaseName   = self.dataBaseName,
                     dataBaseAbsPath = self.dataBaseAbsPath,
                     curveId        = curveId,
                     linkedTo2dPlot = True,
                     curveSlicePosition  = slicePosition,
                     curveLegend    = curveLegend)


        self.addSliceItem(curveId=curveId,
                          sliceOrientation=sliceOrientation,
                          position=position,
                          sliceItem=sliceItem)



    def swapSlices(self) -> None:
        """
        1. Backup all slices information.
            a. infinite line
            b. plot1d attached to the slices
        2. Add all vertical slices to the horizontale one and vice-versa
        3. Remove all horizontale slices to vertical one and vice-versa
        """

        # Store infiniteLine
        inLineVerticals   = {}
        inLineHorizontals = {}
        sliceItemNatures   = {}
        for curveId, infLine in self.sliceItems.items():
            if self.getSliceItemOrientation(infLine)=='horizontal':
                if isinstance(infLine, pg.InfiniteLine):
                    sliceItemNatures[curveId] = 'InfiniteLine'
                    inLineHorizontals[curveId] = infLine.getPos()
                else:
                    sliceItemNatures[curveId] = 'LinearRegionItem'
                    inLineHorizontals[curveId] = (0, (infLine.getRegion()[0]+infLine.getRegion()[1])/2)
            else:
                if isinstance(infLine, pg.InfiniteLine):
                    sliceItemNatures[curveId] = 'InfiniteLine'
                    inLineVerticals[curveId] = infLine.getPos()
                else:
                    sliceItemNatures[curveId] = 'LinearRegionItem'
                    inLineVerticals[curveId] = ((infLine.getRegion()[0]+infLine.getRegion()[1])/2, 0)

        # Store associated 1d plot
        curvesHorizontals = {}
        plotHorizontal = self.getPlotFromRef(self.plotRef, 'horizontal')
        if plotHorizontal is not None:
            for curveId, plotDataItem in plotHorizontal.curves.items():

                curvesHorizontals[curveId] = {'x' : plotDataItem.xData,
                                              'y' : plotDataItem.yData,
                                              'curveLegend' : plotDataItem.curveLegend}

        curvesVerticals = {}
        plotVertical = self.getPlotFromRef(self.plotRef, 'vertical')
        if plotVertical is not None:
            for curveId, plotDataItem in plotVertical.curves.items():

                curvesVerticals[curveId] = {'x' : plotDataItem.xData,
                                            'y' : plotDataItem.yData,
                                            'curveLegend' : plotDataItem.curveLegend}

        # Plot all horizontal slice into the vertical plot and vice-versa
        if curvesHorizontals:
            for plotData, infLineData, sliceItemNature in zip(curvesHorizontals.values(), inLineHorizontals.values(), sliceItemNatures.values()):
                self.addSliceItemAndPlot(data=[plotData['x'], plotData['y']],
                              curveLegend=plotData['curveLegend'],
                              sliceOrientation='vertical',
                              sliceItem=sliceItemNature,
                              plotRef=self.plotRef+'vertical',
                              slicePosition=infLineData[1],
                              position=infLineData[1])
        if curvesVerticals:
            for plotData, infLineData, sliceItemNature in zip(curvesVerticals.values(), inLineVerticals.values(), sliceItemNatures.values()):
                self.addSliceItemAndPlot(data=[plotData['x'], plotData['y']],
                              curveLegend=plotData['curveLegend'],
                              sliceOrientation='horizontal',
                              sliceItem=sliceItemNature,
                              plotRef=self.plotRef+'horizontal',
                              slicePosition=infLineData[0],
                              position=infLineData[0])

        # Remove old infinite lines and curves
        if curvesHorizontals:
            for curveId in curvesHorizontals.keys():
                self.removeSliceItem(curveId)
                self.getPlotFromRef(self.plotRef, 'horizontal').removePlotDataItem(curveId)
        if curvesVerticals:
            for curveId in curvesVerticals.keys():
                self.removeSliceItem(curveId)
                self.getPlotFromRef(self.plotRef, 'vertical').removePlotDataItem(curveId)



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
        if self.checkBoxSubtractAverageX.isChecked():
            zData = zData - np.nanmean(zData, axis=0)
        if self.checkBoxSubtractAverageY.isChecked():
            zData = (zData.T - np.nanmean(zData, axis=1)).T
        if self.checkBoxUnwrapX.isChecked():
            zData[~np.isnan(zData)] = np.unwrap(np.ravel(zData[~np.isnan(zData)], order='F'))
        if self.checkBoxUnwrapY.isChecked():
            zData[~np.isnan(zData)] = np.unwrap(np.ravel(zData[~np.isnan(zData)], order='C'))

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

        rgba_colors = [hex_to_rgba(i) for i in palettes.all_palettes[cm][config['2dMapNbColorPoints']]]

        if self.colorMapInversed:
            rgba_colors = [i for i in reversed(rgba_colors)]

        pos = np.linspace(0, 1, config['2dMapNbColorPoints'])
        # Set the colormap
        pgColormap =  pg.ColorMap(pos, rgba_colors)
        self.histWidget.item.gradient.setColorMap(pgColormap)



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



    def cleanCheckBoxExtraction(self, plotRef     : str=None,
                                      windowTitle : str=None,
                                      runId       : int=None,
                                      label       : str=None) -> None:
        """
        Method called by the plot1d created with the extraction interaction.
        Uncheck the extraction checboxes.
        This method must follow the cleanCheckBox signature, see MainApp.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getplotRef.
        windowTitle : str
            Window title, see getWindowTitle.
        runId : int
            Data run id of the database.
        label : str
            Label of the dependent parameter.
        """

        self.checkBoxMaximum.setChecked(False)
        self.checkBoxMinimum.setChecked(False)



    def checkBoxExtractionState(self) -> None:
        """
        Called when user click on one of the extraction button.
        Extract data and launch them in a dedicated 1d plot.
        """

        ## Depending of the wanted extraction we get the data and labels
        # If no extraction is wanter the extraction plot window is closed and the
        # function stop there.
        ys     = []
        labels = []
        if self.checkBoxMaximum.isChecked() and self.checkBoxMinimum.isChecked():
            ys.append(self.yData[np.nanargmin(self.zData, axis=1)])
            ys.append(self.yData[np.nanargmax(self.zData, axis=1)])
            labels.append('minimum')
            labels.append('maximum')
        elif self.checkBoxMaximum.isChecked():
            ys.append(self.yData[np.nanargmax(self.zData, axis=1)])
            labels.append('maximum')
        elif self.checkBoxMinimum.isChecked():
            ys.append(self.yData[np.nanargmin(self.zData, axis=1)])
            labels.append('minimum')
        else:
            self.removePlot(plotRef=self.plotRef+'extraction', label='')
            return


        ## First click, we launch a new window
        plot = self.getPlotFromRef(self.plotRef, 'extraction')

        # If no existing extraction plot window, we launch one.
        if plot is None:

            self.addPlot(data           = [self.xData, ys[0]],
                         plotTitle      = self.title,
                         xLabelText     = self.xLabelText,
                         xLabelUnits    = self.xLabelUnits,
                         yLabelText     = self.yLabelText,
                         yLabelUnits    = self.yLabelUnits,
                         windowTitle    = self.windowTitle+' - Extraction',
                         runId          = self.runId,
                         cleanCheckBox  = self.cleanCheckBoxExtraction,
                         plotRef        = self.plotRef+'extraction',
                         dataBaseName   = self.dataBaseName,
                         dataBaseAbsPath = self.dataBaseAbsPath,
                         curveId        = labels[0],
                         linkedTo2dPlot = False,
                         curveLegend    = labels[0])
        elif len(plot.curves)==1:

            if labels[0] != list(plot.curves.keys())[0]:

                plot.addPlotDataItem(x           = self.xData,
                                     y           = ys[0],
                                     curveId     = labels[0],
                                     curveLabel  = self.yLabelText,
                                     curveLegend = labels[0])
            else:

                plot.addPlotDataItem(x           = self.xData,
                                     y           = ys[1],
                                     curveId     = labels[1],
                                     curveLabel  = self.yLabelText,
                                     curveLegend = labels[1])

        elif len(plot.curves)==2:

            if labels[0]=='maximum':
                plot.removePlotDataItem('minimum')
            else:
                plot.removePlotDataItem('maximum')



    ####################################
    #
    #           Method to related to fit
    #           TODO: . There is no fit model currently so the code
    #                   is most certainly not working..
    #
    ####################################



    def cleanCheckBoxFit(self, windowTitle, runId):

        pass



    def initFitGUI(self):
        """
        Method called at the initialization of the GUI.
        Make a list of radioButton reflected the available list of fitmodel.
        By default all radioButton are disabled and user should chose a plotDataItem
        to make them available.
        """

        # Get list of fit model
        listClasses = [m[0] for m in inspect.getmembers(fit, inspect.isclass) if 'get_initial_params' in [*m[1].__dict__.keys()]]

        # Add a radio button for each model of the list
        self.fitModelButtonGroup = QtWidgets.QButtonGroup()
        for i, j in enumerate(listClasses):

            _class = getattr(fit, j)

            if '2d' in j:

                obj = _class(self, [], [], [])
                rb = QtWidgets.QRadioButton(obj.checkBoxLabel())
                rb.fitModel = j
                rb.clicked.connect(self.radioButtonFitState)
                self.fitModelButtonGroup.addButton(rb, i)
                self.verticalLayoutFitModel.addWidget(rb)

                del(obj)



    def radioButtonFitState(self):
        """
        Method called when user click on a radioButton of a fitModel.
        Launch a fit of the data using the chosen model and display the results.
        """

        # If a fit curve is already plotted, we remove it before plotting a new
        # one

        radioButton = self.fitModelButtonGroup.checkedButton()

        # Find which model has been chosed and instance it
        _class = getattr(fit, radioButton.fitModel)
        obj = _class(self, self.xData, self.yData, self.zData)

        # Do the fit
        x, y =  obj.ffit()

        # Plot fit curve
        self.fitWindow  = Plot1dApp(x              = x,
                                    y              = y,
                                    title          = self.title+' - '+obj.checkBoxLabel(),
                                    xLabel         = self.xLabel,
                                    yLabel         = obj.yLabel()+' ['+self.zLabel.split('[')[-1].split(']')[0]+']',
                                    windowTitle    = self.windowTitle+' - Fit',
                                    cleanCheckBox  = self.cleanCheckBoxFit,
                                    curveId        = 'extracted',
                                    linkedTo2dPlot = False,
                                    curveLegend    = 'extracted')

        self.fitWindow.show()





def hex_to_rgba(value: str) -> Tuple[int]:
    """
    Convert hex color to rgba color.
    From: https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python/29643643

    Parameters
    ----------
    value : str
        hexagonal color to be converted in rgba.

    Returns
    -------
    Tuple[int]
        rgba calculated from the hex color.
    """
    value = value.lstrip('#')
    lv = len(value)
    r, g, b = [int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    return r, g, b, 255