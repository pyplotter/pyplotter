# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import inspect
import uuid
import palettes # File copy from bokeh: https://github.com/bokeh/bokeh/blob/7cc500601cdb688c4b6b2153704097f3345dd91c/bokeh/palettes.py
import sys
sys.path.append('../ui')

import plot2d
from plot_app import PlotApp
from plot_1d_app import Plot1dApp
from config import config
import fit



class Plot2dApp(QtWidgets.QDialog, plot2d.Ui_Dialog, PlotApp):
    """
    Class to handle ploting in 2d.
    """

    def __init__(self, x, y, z, title, xLabel, yLabel, zLabel, windowTitle,
                runId, cleanCheckBox, parent=None):
        super(Plot2dApp, self).__init__(parent)

        self.setupUi(self)
        
        # Allow resize of the plot window
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)

        self.plotType = '2d'

        self.x             = x
        self.y             = y
        self.z             = z
        self.xLabel        = xLabel
        self.yLabel        = yLabel
        self.zLabel        = zLabel
        self.title         = title
        self.windowTitle   = windowTitle
        self.runId         = runId
        self.cleanCheckBox = cleanCheckBox

        # Store references to infiniteLines
        self.infiniteLines = {}
        self.sliceOrientation = 'vertical'

        # Store the isoCurve and isoLine object
        self.isoCurve = None
        self.isoLine  = None

        # Store the references to linked 1d plots, object created when user
        # create a slice of data
        self.linked1dPlots = {'vertical'   : None,
                              'horizontal' : None}
        
        # Reference to the extracted window
        self.extractionWindow = None

        # Reference to the fit window
        self.extractiofitWindow = None




        # Get plotItem from the widget
        self.plotItem = self.widget.getPlotItem()
        self.resize(*config['dialogWindowSize'])


        # Create a Image item to host the image view
        self.imageItem = pg.ImageItem()
        self.imageView = pg.ImageView(imageItem=self.imageItem)

        # Embed the plot item in the graphics layout
        self.plotItem.vb.addItem(self.imageItem)


        # Create a hostogram item linked to the imageitem
        self.histWidget.setImageItem(self.imageItem)
        self.histWidget.item.setLevels(mn=z[~np.isnan(z)].min(), mx=z[~np.isnan(z)].max())


        # Set the image view
        xscale = (x[-1]-x[0])/len(x)
        yscale = (y[-1]-y[0])/len(y)
        self.imageView.setImage(z, pos=[x[0], y[0]], scale=[xscale, yscale])
        self.imageView.view.invertY(False)
        self.imageView.view.setAspectLocked(False)

        # Axes label
        self.plotItem.setTitle(title=title, color=config['pyqtgraphTitleTextColor'])
        self.plotItem.showGrid(x=True, y=True)
        self.plotItem.setLabel('bottom', xLabel, color=config['pyqtgraphxLabelTextColor'])
        self.plotItem.setLabel('left', yLabel, color=config['pyqtgraphyLabelTextColor'])
        
        # The only reliable way I have found to correctly display the zLabel
        # is by using a Qlabel from the GUI
        self.plot2dzLabel.setText(zLabel)

        # Style
        self.plotItem.getAxis('bottom').setPen(config['pyqtgraphxAxisTicksColor'])
        self.plotItem.getAxis('left').setPen(config['pyqtgraphyAxisTicksColor'])
        self.histWidget.item.axis.setPen(config['pyqtgraphzAxisTicksColor'])

        self.setWindowTitle(windowTitle)

        self.setStyleSheet("background-color: "+str(config['dialogBackgroundColor'])+";")
        self.setStyleSheet("color: "+str(config['dialogTextColor'])+";")


        # Connect UI
        self.checkBoxDrawIsoCurve.stateChanged.connect(self.cbIsoCurve)
        self.checkBoxInvert.stateChanged.connect(lambda : self.cbcmInvert(self.checkBoxInvert))
        self.checkBoxMaximum.stateChanged.connect(self.checkBoxExtractionState)
        self.checkBoxMinimum.stateChanged.connect(self.checkBoxExtractionState)
        self.checkBoxSwapxy.stateChanged.connect(self.checkBoxSwapxyState)
        self.checkBoxSubtractAverageX.stateChanged.connect(lambda : self.checkBoxSubtractAverageXState(self.checkBoxSubtractAverageX))
        self.checkBoxSubtractAverageY.stateChanged.connect(lambda : self.checkBoxSubtractAverageYState(self.checkBoxSubtractAverageY))
        self.checkBoxDerivativeX.stateChanged.connect(lambda : self.checkBoxDerivativeXState(self.checkBoxDerivativeX))
        self.checkBoxDerivativeY.stateChanged.connect(lambda : self.checkBoxDerivativeYState(self.checkBoxDerivativeY))
        self.checkBoxDerivativeXY.stateChanged.connect(lambda : self.checkBoxDerivativeXYState(self.checkBoxDerivativeXY))


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
            if cm == config['plot2dcm']:
                indexViridis = index
            
            index += 1
        
        self.colorMapInversed = False
        self.setColorMap(config['plot2dcm'])
        self.comboBoxcm.setCurrentIndex(indexViridis)
        self.comboBoxcm.currentIndexChanged.connect(self.comboBoxcmChanged)

        self.plotItem.scene().sigMouseClicked.connect(self.plotItemDoubleClicked)
        self.radioButtonSliceHorizontal.toggled.connect(self.radioBoxSliceChanged)
        self.radioButtonSliceVertical.toggled.connect(self.radioBoxSliceChanged)

        # Should be initialize last
        PlotApp.__init__(self)



    def closeEvent(self, evnt):
        """
        Method called when use closed the plotWindow.
        We propagate that event to the mainWindow
        """

        self.cleanCheckBox(windowTitle=self.windowTitle, runId=self.runId, dependent=self.zLabel)

        # If user created data slice, we close the linked 1d plot
        if self.linked1dPlots['vertical'] is not None:
            self.linked1dPlots['vertical'].close()
        if self.linked1dPlots['horizontal'] is not None:
            self.linked1dPlots['horizontal'].close()
        
        # If user extracted the maximum
        if self.extractionWindow is not None:
            self.extractionWindow.close()

        # If user fit the maximum
        if self.fitWindow is not None:
            self.fitWindow.close()


    def o(self):
        self.close()



    def updateImageItem(self, x, y, z):
        """
        Update the displayed colormap
        """

        self.x  = x
        self.y  = y
        self.z  = z

        # Set the image view
        xscale = (x[-1]-x[0])/len(x) if (x[-1]-x[0])/len(x) else 1.
        yscale = (y[-1]-y[0])/len(y)
        self.imageView.setImage(z, pos=[x[0], y[0]], scale=[xscale, yscale])
        self.histWidget.item.setLevels(mn=z[~np.isnan(z)].min(), mx=z[~np.isnan(z)].max())
        self.imageView.autoRange()



    def checkBoxSwapxyState(self, b):
        """
        When user want to swap the x and y axis
        """

        ## We swap the x and y axis of the colormap
        t = self.xLabel
        self.xLabel = self.yLabel
        self.yLabel = t
        
        # A bug happens when labels contain scientific notation, i.e. 1e9
        # That number does not follow the label, I didn't succeed to solve it
        self.plotItem.setLabel('bottom', self.xLabel, color=config['pyqtgraphxLabelTextColor'])
        self.plotItem.setLabel('left', self.yLabel, color=config['pyqtgraphyLabelTextColor'])

        self.updateImageItem(self.y, self.x, self.z.T)



        ## We rotate all infiniteLines
        for curveId, infLine in self.infiniteLines.items():
            pos = infLine.getPos()
            infLine.setAngle(infLine.angle + 90)
            infLine.setPos((pos[1], pos[0]))

            infLine.sigDragged.connect(lambda lineItem=infLine,
                                        curveId=curveId:
                                        self.dragSliceLine(lineItem,
                                                            curveId))


        t = self.linked1dPlots['vertical']
        self.linked1dPlots['vertical']    = self.linked1dPlots['horizontal']
        self.linked1dPlots['horizontal']  = t



        self.radioButtonSliceHorizontal.toggle()



    ####################################
    #
    #           InfinityLines
    #
    ####################################



    def getInfinityLineOrientation(self, lineItem):
        """
        Return the orientation of the infinityLine depending of its angle.
        """

        if lineItem.angle/90==0:
            lineOrientation = 'horizontal'
        else:
            lineOrientation = 'vertical'

        return lineOrientation




    def radioBoxSliceChanged(self, b):
        """
        Method called when user change the data slice orientation
        """

        if self.radioButtonSliceHorizontal.isChecked():
            self.sliceOrientation = 'horizontal'
        else:
            self.sliceOrientation = 'vertical'


    @staticmethod
    def getCurveId():
        """
        Create a unique id for every data slice
        """

        return str(uuid.uuid1())



    def dragSliceLine(self, lineItem, curveId):
        """
        Method call when user drag a slice line.

        Parameters
        ----------
        InfinitylineItem : 
            InfinitylineItem currently being dragged.
        curveId :
            ID of the curve associated to the slice being dragged
        """

        # We get the slice data from the 2d plot
        sliceX, sliceY, sliceLegend = self.getDataSlice(lineItem=lineItem)
        
        # We update the curve associated to the sliceLine
        self.linked1dPlots[self.getInfinityLineOrientation(lineItem)]\
        .updatePlotDataItem(x           = sliceX,
                            y           = sliceY,
                            curveId     = curveId,
                            curveLegend = sliceLegend)

        # We overide a pyqtgraph attribute when user drag an infiniteLine
        self.infiniteLines[curveId].mouseHovering  = True

        return 1



    def addInifiteLine(self, curveId):
        """
        Method call when user create a slice of the data.
        Create an infiniteLine on the 2d plot and connect a drag signal on it.

        Parameters
        ----------
        curveId :
            ID of the curve associated to the data slice
        """
        
        colorIndex = self.linked1dPlots[self.sliceOrientation].curves[curveId].colorIndex

        pen = pg.mkPen(color=config['plot1dColors'][colorIndex],
                       width=config['crossHairLineWidth'],
                       style=QtCore.Qt.SolidLine)
        hoverPen = pg.mkPen(color=config['plot1dColors'][colorIndex],
                       width=config['crossHairLineWidth'],
                       style=QtCore.Qt.DashLine)

        # When the user click we add a vertical and horizontale lines where he clicked.
        if self.sliceOrientation == 'vertical':
            angle = 90.
            pos = self.mousePos[0]
        else:
            angle = 0.
            pos = self.mousePos[1]

        t = pg.InfiniteLine(angle=angle, movable=True, pen=pen, hoverPen=hoverPen)
        t.setPos(pos)

        self.plotItem.addItem(t)

        # We attached a drag event to this line
        t.sigDragged.connect(lambda lineItem=t,
                                    curveId=curveId,
                                    lineOrientation=self.sliceOrientation:
                                    self.dragSliceLine(lineItem,
                                                        curveId))


        self.infiniteLines[curveId] = t
        
        return t



    def removeInifiteLine(self, curveId):
        self.plotItem.removeItem(self.infiniteLines[curveId])
        del self.infiniteLines[curveId]



    def cleanInfiniteLine(self, windowTitle, runId):
        """
        Called when a linked 1dPlot is closed
        """
        
        # We clean the reference of the linked 1d plot
        if 'vertical' in windowTitle:
            self.linked1dPlots['vertical'] = None
            searchedAngle = 90.
        else:
            self.linked1dPlots['horizontal'] = None
            searchedAngle =  0.

        # We remove all the associated infiniteLine
        keyToRemove = []
        for key, val in list(self.infiniteLines.items()):
            if val.angle == searchedAngle:
                keyToRemove.append(key)
        
        [self.removeInifiteLine(key) for key in keyToRemove]



    def getDataSlice(self, lineItem=None):
        """
        Return a vertical or horizontal data slice
        """

        xSlice = None
        ySlice = None

        # When lineItem is None, We are creating the dataSlice
        if lineItem is None:
            if self.sliceOrientation == 'vertical':
                xSlice = self.mousePos[0]
            else:
                ySlice = self.mousePos[1]
        # Otherwise the dataSlice exist and return its position depending of its
        # orientation
        else:
            if self.getInfinityLineOrientation(lineItem) == 'vertical':
                xSlice = lineItem.value()
            else:
                ySlice = lineItem.value()

        # Depending on the slice we return the x and y axis data and the legend
        # associated with the cut.
        if ySlice is None:
            n = np.abs(self.x-xSlice).argmin()
            sliceX      = self.y
            sliceY      = self.z[n]
            sliceLegend = self.x[n]
        else:
            n = np.abs(self.y-ySlice).argmin()
            sliceX      = self.x
            sliceY      = self.z[:,n]
            sliceLegend = self.y[n]

        return sliceX, sliceY, '{:.3e}'.format(sliceLegend)



    def plotItemDoubleClicked(self, e):
        """
        When a use double click on the 2D plot, we create a slice of the colormap
        """

        # If double click is detected and mouse is over the viewbox, we launch
        # a 1d plot corresponding to a data slice
        if e._double and self.isMouseOverView():
            
            # Get the data of the slice
            sliceX, sliceY, sliceLegend = self.getDataSlice()

            # If nbCurve is 1, we create the 1d plot window
            if self.linked1dPlots[self.sliceOrientation] is None:

                # The xLabel of the 1d plot depends on the slice orientation
                if self.sliceOrientation == 'vertical':
                    xLabel = self.yLabel
                else:
                    xLabel = self.xLabel

                curveId = self.getCurveId()
                p = Plot1dApp(x              = sliceX,
                              y              = sliceY,
                              title          = self.title,
                              xLabel         = xLabel,
                              yLabel         = self.zLabel,
                              windowTitle    = self.windowTitle+' - '+self.sliceOrientation+' slice',
                              runId          = self.runId,
                              cleanCheckBox  = self.cleanInfiniteLine,
                              curveId        = curveId,
                              linkedTo2dPlot = True,
                              curveLegend    = sliceLegend)
                p.show()
                self.linked1dPlots[self.sliceOrientation] = p

                # We linked the curve of the 1dplot to the infinite line display
                # on the 2d plot
                self.addInifiteLine(curveId)
            else:
                
                # We check if user double click on an infiniteLine
                clickedCurveId = None
                for curveId, curve in self.linked1dPlots[self.sliceOrientation].curves.items():
                    if curve.curveLegend == sliceLegend:
                        clickedCurveId = curveId

                # If the user add a new infiniteLine
                if clickedCurveId is None:
                    curveId = self.getCurveId()
                    self.linked1dPlots[self.sliceOrientation].addPlotDataItem(x           = sliceX,
                                                                              y           = sliceY,
                                                                              curveId     = curveId,
                                                                              curveLabel  = self.zLabel,
                                                                              curveLegend = sliceLegend)
                    self.addInifiteLine(curveId)

                # We remove a slice
                else:
                    # If there is more than one slice, we remove it and the associated curve
                    if len(self.infiniteLines)>1:
                        self.linked1dPlots[self.sliceOrientation].removePlotDataItem(clickedCurveId)
                        self.removeInifiteLine(clickedCurveId)
                    # If there is only one slice, we close the linked 1d plot
                    # which will remove the associated infiniteLine
                    else:
                        self.linked1dPlots[self.sliceOrientation].removePlotDataItem(clickedCurveId)



    ####################################
    #
    #           Derivative
    #
    ####################################



    def checkBoxDerivativeXState(self, cb):
        """
        Handle events when user wants to derivate along x.
        """
        
        if cb.isChecked():

            if self.checkBoxDerivativeY.isChecked():
                self.checkBoxDerivativeY.setChecked(False)
            if self.checkBoxDerivativeXY.isChecked():
                self.checkBoxDerivativeXY.setChecked(False)

            self.z_backupx = self.z
            self.z = np.gradient(self.z, self.x, axis=0)
        else: 
            self.z = self.z_backupx

        self.updateImageItem(self.x, self.y, self.z)



    def checkBoxDerivativeYState(self, cb):
        """
        Handle events when user wants to derivate along y.
        """
        
        if cb.isChecked():

            if self.checkBoxDerivativeX.isChecked():
                self.checkBoxDerivativeX.setChecked(False)
            if self.checkBoxDerivativeXY.isChecked():
                self.checkBoxDerivativeXY.setChecked(False)

            self.z_backupy = self.z
            self.z = np.gradient(self.z, self.y, axis=1)
        else: 
            self.z = self.z_backupy

        self.updateImageItem(self.x, self.y, self.z)



    def checkBoxDerivativeXYState(self, cb):
        """
        Handle events when user wants the gradient.
          ____________________
        \/ (d/dx)^2 + (d/dy)^2

        """
        
        if cb.isChecked():

            if self.checkBoxDerivativeX.isChecked():
                self.checkBoxDerivativeX.setChecked(False)
            if self.checkBoxDerivativeY.isChecked():
                self.checkBoxDerivativeY.setChecked(False)

            self.z_backupz = self.z
            self.z = np.sqrt(np.gradient(self.z, self.x, axis=0)**2. + np.gradient(self.z, self.y, axis=1)**2.)
        else: 
            self.z = self.z_backupz

        self.updateImageItem(self.x, self.y, self.z)




    ####################################
    #
    #           Subtraction
    #
    ####################################



    def checkBoxSubtractAverageXState(self, cb):
        """
        Handle events when user wants to subtract average alon x axis
        """
        
        if cb.isChecked():
            self.averageX = np.mean(self.z, axis=0)
            self.z -= self.averageX
        else: 
            self.z += self.averageX

        self.updateImageItem(self.x, self.y, self.z)



    def checkBoxSubtractAverageYState(self, cb):
        """
        Handle events when user wants to subtract average alon x axis
        """
        
        if cb.isChecked():
            self.averageY = np.mean(self.z, axis=1)
            self.z = (self.z.T -self.averageY).T
        else: 
            self.z = (self.z.T +self.averageY).T

        self.updateImageItem(self.x, self.y, self.z)



    ####################################
    #
    #           Colormap
    #
    ####################################



    def comboBoxcmChanged(self, index):
        """
        Method called when user clicked on the comboBox
        """
        
        self.cbcmInvert(self.checkBoxInvert)



    def cbcmInvert(self, b):
        """
        Handle the event of the user clicking the inverted button for the colorbar.
        """
        
        if b.isChecked():
            self.colorMapInversed = True
        else: 
            self.colorMapInversed = False
 
        self.setColorMap(self.comboBoxcm.currentText())



    def setColorMap(self, cm):
        """
        Set the colormap of the imageItem from the colormap name
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



    def cbIsoCurve(self, b):
        """
        Hande the event of the user clicking the inverted button for the colorbar.
        """

        # If the user uncheck the box, we hide the items
        if b == 0:

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



    def draggedIsoLine(self):
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



    def cleanCheckBoxExtraction(self, windowTitle, runId):

        self.checkBoxMaximum.setChecked(False)
        self.checkBoxMinimum.setChecked(False)



    def checkBoxExtractionState(self):
        """
        Called when user click on one of the extraction button
        Extract data and launch them in a dedicated 1d plot
        """
        
        ys     = []
        labels = []
        if self.checkBoxMaximum.isChecked() and self.checkBoxMinimum.isChecked():
            ys.append(self.y[np.nanargmin(self.z, axis=1)])
            ys.append(self.y[np.nanargmax(self.z, axis=1)])
            labels.append('minimum')
            labels.append('maximum')
        elif self.checkBoxMaximum.isChecked():
            ys.append(self.y[np.nanargmax(self.z, axis=1)])
            labels.append('maximum')
        elif self.checkBoxMinimum.isChecked():
            ys.append(self.y[np.nanargmin(self.z, axis=1)])
            labels.append('minimum')
        else:
            self.extractionWindow.close()
            self.extractionWindow = None
            return

        # First click, we launch a new window
        if self.extractionWindow is None:
            self.extractionWindow  = Plot1dApp(x              = self.x,
                                               y              = ys[0],
                                               title          = self.title,
                                               xLabel         = self.xLabel,
                                               yLabel         = self.yLabel,
                                               windowTitle    = self.windowTitle+' - Extraction',
                                               runId          = self.runId,
                                               cleanCheckBox  = self.cleanCheckBoxExtraction,
                                               curveId        = labels[0],
                                               linkedTo2dPlot = False,
                                               curveLegend    = labels[0])
            self.extractionWindow.show()
        elif len(self.extractionWindow.curves) == 1:
            
            if labels[0] != list(self.extractionWindow.curves.keys())[0]:
                
                self.extractionWindow.addPlotDataItem(x           = self.x,
                                                    y           = ys[0],
                                                    curveId     = labels[0],
                                                    curveLabel  = self.yLabel,
                                                    curveLegend = labels[0])
            else:
                
                self.extractionWindow.addPlotDataItem(x           = self.x,
                                                    y           = ys[1],
                                                    curveId     = labels[1],
                                                    curveLabel  = self.yLabel,
                                                    curveLegend = labels[1])

        elif len(self.extractionWindow.curves) == 2:
            
            if labels[0] == 'maximum':
                self.extractionWindow.removePlotDataItem('minimum')
            else:
                self.extractionWindow.removePlotDataItem('maximum')



    ####################################
    #
    #           Method to related to fit
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
        obj = _class(self, self.x, self.y, self.z)

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





def hex_to_rgba(value):
    """
    Convert hex color to rgba color
    From: https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python/29643643
    """
    value = value.lstrip('#')
    lv = len(value)
    r, g, b = [int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    return r, g, b, 255