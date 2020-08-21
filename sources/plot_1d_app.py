# This Python file uses the following encoding: utf-8
from __future__ import annotations
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pyqtgraph as pg
from typing import List, Union
import inspect


from ui.plot1d import Ui_Dialog
from sources.config import config
from sources.plot_app import PlotApp
import sources.fit as fit
import sources.filtering as filtering
from sources.DateAxisItem import DateAxisItem



class Plot1dApp(QtWidgets.QDialog, Ui_Dialog, PlotApp):
    """
    Class to handle ploting in 1d.
    """


    def __init__(self, x, y, title, xLabel, yLabel, windowTitle, runId,
                cleanCheckBox, plotRef, addPlot, getPlotFFTFromRef,
                linkedTo2dPlot=False, curveId=None, curveLegend=None,
                timestampXAxis=False,
                livePlot=False,
                parent=None):
        super(Plot1dApp, self).__init__(parent)
        
        self.setupUi(self)
        
        # Allow resize of the plot window
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)

        self.plotType       = '1d'
        self.windowTitle    = windowTitle
        self.runId          = runId
        self.cleanCheckBox  = cleanCheckBox
        self.plotRef        = plotRef

        self.addPlot        = addPlot
        self.getPlotFFTFromRef  = getPlotFFTFromRef

        # References of PlotDataItem 
        # Structures
        # self.curves = {'curveId' : pg.PlotDataItem}
        self.curves         = {}

        # If the x axis is a time axis
        # If True we use a special pyqtgraph item for time axis
        self.timestampXAxis = timestampXAxis

        # Is that 1d plot is linked to a 2d plot (slice of a 2d plot)
        self.linkedTo2dPlot = linkedTo2dPlot

        # If the plot is displaying a qcodes run that is periodically updated
        self.livePlot = livePlot

        # Keep reference of FFT
        # self.fftwindow = []

        # Reference to QDialog which will contains fit info
        self.fitWindow = None

        # Reference to QDialog which will contains filtering info
        self.filteringWindow = None

        # References of the infinietLines used to select data for the fit.
        # Structured
        # self.infiniteLines = {'a' : pg.InfiniteLine,
        #                       'b' : pg.InfiniteLine}
        self.infiniteLines = {}


        # Get plotItem from the widget
        self.plotItem = self.widget.getPlotItem()
        self.resize(*config['dialogWindowSize'])

        # Create legendItem
        self.legendItem = self.plotItem.addLegend()

        # Add fitting function to the GUI
        self.initFitGUI()
        # Add filtering function to the GUI
        self.initFilteringGUI()


        # Connect UI
        self.checkBoxLogX.stateChanged.connect(self.checkBoxLogState)
        self.checkBoxLogY.stateChanged.connect(self.checkBoxLogState)
        self.checkBoxSymbol.stateChanged.connect(self.checkBoxSymbolState)

        self.radioButtonFFT.clicked.connect(lambda:self.clickFFT(self.radioButtonFFT))
        self.radioButtonFFTnoDC.clicked.connect(lambda:self.clickFFT(self.radioButtonFFTnoDC))
        self.radioButtonIFFT.clicked.connect(lambda:self.clickFFT(self.radioButtonIFFT))


        # Add a radio button for each model of the list
        self.plotDataItemButtonGroup = QtWidgets.QButtonGroup()
        self.radioButtonFitNone.curveId = None
        self.plotDataItemButtonGroup.addButton(self.radioButtonFitNone, 0)
        self.radioButtonFitNone.clicked.connect(self.selectPlotDataItem)
        self.radioButtonFitNone.setChecked(True)


        self.setWindowTitle(str(windowTitle))

        self.plotItem.setTitle(title=str(title), color=config['pyqtgraphTitleTextColor'])

        # To make the GUI faster
        self.plotItem.disableAutoRange()

        if config['plot1dGrid']:
            self.plotItem.showGrid(x=True, y=True)

        self.plotItem.setLabel('bottom', xLabel, color=config['pyqtgraphxLabelTextColor'])
        self.plotItem.setLabel('left', yLabel, color=config['pyqtgraphyLabelTextColor'])

        self.plotItem.getAxis('bottom').setPen(config['pyqtgraphxAxisTicksColor'])
        self.plotItem.getAxis('left').setPen(config['pyqtgraphyAxisTicksColor'])

        self.setStyleSheet("background-color: "+str(config['dialogBackgroundColor'])+";")
        self.setStyleSheet("color: "+str(config['dialogTextColor'])+";")


        # If the xaxis used timestamp, we use a dedicated axisItem
        if self.timestampXAxis:
            # This utc offset is unclear to me...
            self.plotItem.setAxisItems({'bottom' : DateAxisItem(utcOffset=0.)})

        # Display initial data curve
        if curveLegend is None:
            curveLegend = yLabel

        self.addPlotDataItem(x           = x,
                             y           = y,
                             curveId     = curveId,
                             curveLabel  = yLabel,
                             curveLegend = curveLegend)

        # AutoRange only after the first data item is added
        self.plotItem.autoRange()

        # Should be initialize last
        PlotApp.__init__(self)



    ####################################
    #
    #           Properties
    #
    ####################################


    @property
    def xLabel(self) -> str:

        if hasattr(self, 'plotItem'):
            return self.plotItem.axes['bottom']['item'].labelText
        else:
            return ''



    @property
    def yLabel(self) -> str:

        if hasattr(self, 'plotItem'):
            return self.plotItem.axes['left']['item'].labelText
        else:
            return ''



    ####################################
    #
    #           Method to close, clean stuff
    #
    ####################################



    @staticmethod
    def clearLayout(layout: QtWidgets.QBoxLayout) -> None:
        """
        Clear a pyqt layout, from:
        https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()



    def closeEvent(self, evnt: QtGui.QCloseEvent) -> None:
        """
        Method called when use closed the plotWindow.
        We propagate that event to the mainWindow
        """
        
        self.cleanCheckBox(plotRef     = self.plotRef,
                           windowTitle = self.windowTitle,
                           runId       = self.runId,
                           label       = '')

        if self.fitWindow is not None:
            self.fitWindow.close()

        if self.filteringWindow is not None:
            self.filteringWindow.close()

        fftPlot = self.getPlotFFTFromRef(self.plotRef)
        if fftPlot is not None:
            fftPlot.close()



    def o(self):
        if self.fitWindow is not None:
            self.fitWindow.close()
        self.close()



    ####################################
    #
    #           Method to add, update, remove items
    #
    ####################################



    def getLineColor(self) -> None:
        """
        Return a pyqtgraph mKpen with the color of the next curve following
        the colors in config files
        """

        colors = [curve.colorIndex for curve in self.curves.values()]
        for i in range(50):
            if i not in colors:
                colorIndex = i%len(config['plot1dColors'])
                color = config['plot1dColors'][i%len(config['plot1dColors'])]
                break


        mkpen = pg.mkPen(color=color, width=config['plotDataItemWidth'])

        return colorIndex, mkpen



    def updatePlotDataItem(self, x           : np.ndarray,
                                 y           : np.ndarray,
                                 curveId     : str,
                                 curveLegend : str=None,
                                 autoRange   : bool=False) -> None:
        """
        Method called by a plot2d when use drag a sliceLine.
        Updating an existing plotDataItem and the plot legendItem

        Parameters
        ----------
        x : np.ndarray
            x data.
        y : np.ndarray
            y data.
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        curveLegend : str
            Legend label of the curve.
        autoRange : bool
            If the view should perform an autorange after updating the data.
            Can be slow for heavy data array.
        """

        self.curves[curveId].setData(x=x, y=y)

        if curveLegend is not None:
            self.curves[curveId].curveLegend = curveLegend
            self.updateLegend()

        if autoRange:
            self.plotItem.vb.autoRange()



    def addPlotDataItem(self, x            : np.ndarray,
                              y            : np.ndarray,
                              curveId      : str,
                              curveLabel   : str,
                              curveLegend  : str,
                              showInLegend : bool=True) -> None:
        """
        Method adding a plotDataItem to the plotItem.

        Parameters
        ----------
        x : np.ndarray
            x data.
        y : np.ndarray
            y data.
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        curveLabel : str
            y label of the curve.
        curveLegend : str
            Legend label of the curve.
        showInLegend : bool
            If data should be shown in the legend.
            Typically selected data for fitting are not displayed in the legend.
        """

        # Get the dataPlotItem color
        colorIndex, mkpen = self.getLineColor()

        # Create plotDataItem and save its reference
        self.curves[curveId] = self.plotItem.plot(x, y, pen=mkpen)

        # Create usefull attribute
        self.curves[curveId].colorIndex   = colorIndex
        self.curves[curveId].curveLabel   = curveLabel
        self.curves[curveId].curveLegend  = curveLegend
        self.curves[curveId].showInLegend = showInLegend

        # Update the display information
        self.updateLegend()
        self.updateLabel()
        self.updateListDataPlotItem(curveId)



    def removePlotDataItem(self, curveId: str) -> None:
        """
        Remove a PlotDataItem identified via its "curveId"
        """

        # If no curve will be displayed, we close the QDialog
        if len(self.curves) == 1:
            self.o()
        else:
            # Remove the curve
            self.plotItem.removeItem(self.curves[curveId])
            del(self.curves[curveId])

            # Update the display information
            self.updateLegend()
            self.updateLabel()

            # Update the list of plotDataItem
            for radioButton in self.plotDataItemButtonGroup.buttons():
                if radioButton.curveId == curveId:
                    self.plotDataItemButtonGroup.removeButton(radioButton)
                    radioButton.setParent(None)



    def updateLabel(self):
        """
        Update the ylabel of the plotItem.
        If there is one dataPlotItem the displayed ylabel is the data ylabel.
        If many dataPlotItem, the ylabel is "[a.u]".
        """
        
        # The label is changed only of we are not display slices of a 2d plot
        if not self.linkedTo2dPlot:
            
            # If there is more than one plotDataItem
            # We check of the share the same unit
            if len(self.curves)>1 and len(np.unique(np.array([curve.curveLabel[:-1].split('[')[-1] for curve in self.curves.values()])))==1:
                self.plotItem.setLabel('left',
                                        '['+self.curves[list(self.curves.keys())[0]].curveLabel[:-1].split('[')[-1]+']',
                                        color=config['pyqtgraphyLabelTextColor'])
            
            # We check of the share the same label
            elif len(np.unique(np.array([curve.curveLabel for curve in self.curves.values()])))>1:
                self.plotItem.setLabel('left',
                                        '[a.u]',
                                        color=config['pyqtgraphyLabelTextColor'])
                                        

            # If there is only one plotDataItem or if the plotDataItems share the same label
            else:
                self.plotItem.setLabel('left',
                                       self.curves[list(self.curves.keys())[0]].curveLabel,
                                       color=config['pyqtgraphyLabelTextColor'])



    def updateLegend(self) -> None:
        """
        Update the legendItem of the plotItem.
        """

        self.legendItem.clear()
        
        # We do not add items in the legend when there is only one curve
        # except when the 1d plot is linked to a 2d plot
        if len(self.curves)==1:
            if self.linkedTo2dPlot:
                for curve in self.curves.values():
                    if curve.showInLegend:
                        self.legendItem.addItem(curve, curve.curveLegend)
        elif len(self.curves) > 1:
            for curve in self.curves.values():
                if curve.showInLegend:
                    self.legendItem.addItem(curve, curve.curveLegend)



    def updateListDataPlotItem(self, curveId: str) -> None:
        """
        Method called when a plotDataItem is added to the plotItem.
        Add a radioButton to allow the user to select the plotDataItem.

        Parameters
        ----------
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        """

        # Update list of plotDataItem only if the plotDataItem is not a fit
        if curveId not in ['fit', 'filtering']:
            radioButton = QtWidgets.QRadioButton(self.curves[curveId].curveLabel)
            
            radioButton.curveId = curveId
            
            if 'selection' not in curveId:
                self.plotDataItemButtonGroup.addButton(radioButton, len(self.plotDataItemButtonGroup.buttons()))
                radioButton.clicked.connect(self.selectPlotDataItem)
                self.verticalLayoutPlotDataItem.addWidget(radioButton)



    ####################################
    #
    #           Method to add curves from other plot window in the plot
    #
    ####################################



    def updatePlottedCurvesList(self, plots: List[Plot1dApp]) -> None:
        """
        Is called by the Main object when the user plots a new 1d curve.
        Build a list of checkbox related to every already plotted curve and
        display it in the curve tab.
        """
        


        # Is there at least one another curve to be shown in the new tab
        isThere = False
        for plot in plots:
            for curveId in plot.curves.keys():

                # We do not add a checkbox button for the original curves of
                # the plot window
                if (self.windowTitle != plot.windowTitle or
                    plot.runId != self.runId or
                    curveId not in self.curves):
                    
                    isThere = True


        # If there is, we build the GUI
        if isThere:
            

            # Initialize GUI
            if not hasattr(self, 'tabCurves'):
                self.tabCurves = QtWidgets.QWidget()
                self.tabWidget.addTab(self.tabCurves, 'Add curves')
                
                self.tabLayout = QtGui.QVBoxLayout()
                self.tabCurves.setLayout(self.tabLayout)
            else:

                widgets = (self.tabLayout.itemAt(i).widget() for i in range(self.tabLayout.count())) 
                for widget in widgets:
                    if widget is not None:
                        widget.setChecked(False)

                self.clearLayout(self.tabLayout)


            # For each plot, build a checkbox of the available curves

            for plot in plots:
                for curveId in plot.curves.keys():

                    # We do not add a checkbox button for the original curves of
                    # the plot window
                    if (self.windowTitle != plot.windowTitle or
                        plot.runId != self.runId or
                        curveId not in self.curves):
                        cb = QtWidgets.QCheckBox()
                        label = plot.windowTitle+\
                                ' - '+str(plot.runId)+'\n'+\
                                plot.curves[curveId].curveLabel

                        cb.setText(label)

                        cb.toggled.connect(lambda state,
                                                  curveId = curveId,
                                                  plot    = plot: self.toggleNewPlot(state, curveId, plot))
                        
                        if curveId in self.curves.keys():
                            cb.setChecked(True)

                        self.tabLayout.addWidget(cb)


            verticalSpacer = QtWidgets.QSpacerItem(20, 40,
                                QtWidgets.QSizePolicy.Minimum,
                                QtWidgets.QSizePolicy.Expanding) 
            self.tabLayout.addItem(verticalSpacer)
        
        else:
            if hasattr(self, 'tabCurves'):
                self.tabWidget.removeTab(1)



    def toggleNewPlot(self, state: bool, curveId: str, plot: Plot1dApp) -> None:
        """
        Called when user click on the checkbox of the curves tab.
        Add or remove curve in the plot window.
        """
        
        if state:

            self.addPlotDataItem(x           = plot.curves[curveId].xData,
                                 y           = plot.curves[curveId].yData,
                                 curveId     = curveId,
                                 curveLabel  = plot.curves[curveId].curveLabel,
                                 curveLegend = plot.curves[curveId].curveLabel)

        else:
            self.removePlotDataItem(curveId)



    ####################################
    #
    #           Method to related to display
    #
    ####################################



    def checkBoxLogState(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user click on the log checkBoxes.
        Modify the scale, linear or logarithmic, of the plotItem following
        which checkbox are checked.
        """
        
        if self.checkBoxLogX.isChecked():
            if self.checkBoxLogY.isChecked():
                self.plotItem.setLogMode(x=True, y=True)
            else:
                self.plotItem.setLogMode(x=True, y=False)
        else:
            if self.checkBoxLogY.isChecked():
                self.plotItem.setLogMode(x=False, y=True)
            else:
                self.plotItem.setLogMode(x=False, y=False)



    def checkBoxSymbolState(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user click on the Symbol checkBox.
        Put symbols on all plotDataItem except fit model.
        """
        
        if self.checkBoxSymbol.isChecked():
            
            for i, (key, curve) in enumerate(list(self.curves.items())):
                if key != 'fit':
                    curve.setSymbol(config['plot1dSymbol'][i%len(config['plot1dSymbol'])])
        else:
            for dataPlotItem in self.plotItem.listDataItems():
                dataPlotItem.setSymbol(None)



    ####################################
    #
    #           Method to related to FFT
    #
    ####################################



    def clickFFT(self, button:QtWidgets.QRadioButton) -> None:
        """
        Method called when user click on the fft radio buttons.
        Add a plot containing the FFT/IFFT of the chosen data.
        """


        if self.radioButtonFFT.isChecked():
            
            x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
            y = np.abs(np.fft.fft(self.selectedY))[x>=0]
            x = x[x>=0]
            text = 'fft'

        elif self.radioButtonFFTnoDC.isChecked():
            
            x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
            y = np.abs(np.fft.fft(self.selectedY))[x>=0][1:]
            x = x[x>=0][1:]
            text = 'fft'

        elif self.radioButtonIFFT.isChecked():
            
            x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
            y = np.abs(np.fft.ifft(self.selectedY))[x>=0]
            x = x[x>=0]
            text = 'ifft'

        xLabel = '1/'+self.plotItem.axes['bottom']['item'].labelText
        yLabel = text.upper()+'( '+self.selectedLabel+' )'
        title  = self.windowTitle+' - '+text.upper()

        fftPlot = self.getPlotFFTFromRef(self.plotRef)
        if fftPlot is not None:
            fftPlot.close()
        
        self.addPlot(plotRef        = self.plotRef+'fft',
                     data           = [x, y],
                     xLabel         = xLabel,
                     yLabel         = yLabel,
                     cleanCheckBox  = self.cleanCheckBox,
                     plotTitle      = title,
                     windowTitle    = title,
                     runId          = 1,
                     linkedTo2dPlot = False,
                     curveId        = yLabel,
                     curveLegend    = yLabel,
                     curveLabel     = yLabel,
                     timestampXAxis = False,
                     livePlot       = False,
                     progressBarKey = None,
                     zLabel         = None)



    ####################################
    #
    #           Method to related to data selection
    #
    ####################################



    def getSelectedData(self, curveId: str) -> List[np.ndarray]:
        """
        Return the x and y data of the curve specified by its curve id troncated
        between the infiniteLines "a" and "b".
        It does not matter if a<b or a>b.

        Parameters
        ----------
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        """

        a = self.infiniteLines['a'].value()
        b = self.infiniteLines['b'].value()
        n = np.abs(self.curves[curveId].xData-a).argmin()
        m = np.abs(self.curves[curveId].xData-b).argmin()
        if a<b:
            x = self.curves[curveId].xData[n:m]
            y = self.curves[curveId].yData[n:m]
        else:
            x = self.curves[curveId].xData[m:n]
            y = self.curves[curveId].yData[m:n]

        return x, y



    def selectionInifiniteLineChangeFinished(self, lineItem: pg.InfiniteLine,
                                                   curveId: str) -> None:
        """
        Method call when user release a dragged selection line.
        Update the selected data and if a model is already being active, update
        the model as well.

        Parameters
        ----------
        lineItem : pg.InfiniteLine
            Pyqtgraph infiniteLine being dragged.
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        """

        # Update the style of the display plotDataItem
        self.updatePlotDataItemStyle(curveId)

        # Update data used for the fit
        self.selectedX, self.selectedY = self.getSelectedData(curveId)

        # If a fit curve is already displayed, we update it
        if 'fit' in list(self.curves.keys()):
            self.radioButtonFitState()
            
        # If a filtering curve is already displayed, we update it
        if 'filtering' in list(self.curves.keys()):
            self.radioButtonFilteringtState()

        # We overide a pyqtgraph attribute when user drag an infiniteLine
        lineItem.mouseHovering  = False



    def selectionInifiniteLineDragged(self, lineItem: pg.InfiniteLine) -> None:
        """
        Method call when an user is dragging a selection line.

        Parameters
        ----------
        lineItem : pg.InfiniteLine
            Pyqtgraph infiniteLine being dragged.
        """

        # We overide a pyqtgraph attribute when user drag an infiniteLine
        lineItem.mouseHovering  = True



    def updateSelectionInifiteLine(self, curveId: Union[str, None]) -> None:
        """
        Method call by selectPlotDataItem.
        Handle the creation or deletion of two infiniteLine items used to select
        data.
        The infiniteLine item  events are connected as follow:
            sigPositionChangeFinished -> selectionInifiniteLineChangeFinished
            sigDragged -> selectionInifiniteLineDragged

        Parameters
        ----------
        curveId : str
            Id of the curve.
            If None, we delete the infinite lines
            See getCurveId from MainApp
        """
        
        # If we want to remove the selection infinite line
        if curveId is None:
            self.plotItem.removeItem(self.infiniteLines['a'])
            self.plotItem.removeItem(self.infiniteLines['b'])
        else:
            pen = pg.mkPen(color=(255, 255, 255),
                           width=config['crossHairLineWidth'],
                           style=QtCore.Qt.SolidLine)
            hoverPen = pg.mkPen(color=(255, 255, 255),
                                width=config['crossHairLineWidth'],
                                style=QtCore.Qt.DashLine)

            angle = 90.
            pos = self.curves[curveId].xData[0]

            t = pg.InfiniteLine(angle=angle, movable=True, pen=pen, hoverPen=hoverPen)
            t.setPos(pos)

            self.plotItem.addItem(t)
            self.infiniteLines['a'] = t
            t.sigPositionChangeFinished.connect(lambda: self.selectionInifiniteLineChangeFinished(lineItem=t, curveId=curveId))
            t.sigDragged.connect(lambda: self.selectionInifiniteLineDragged(lineItem=t))

            pos = self.curves[curveId].xData[-1]

            t = pg.InfiniteLine(angle=angle, movable=True, pen=pen, hoverPen=hoverPen)
            t.setPos(pos)

            self.plotItem.addItem(t)
            self.infiniteLines['b'] = t
            t.sigPositionChangeFinished.connect(lambda: self.selectionInifiniteLineChangeFinished(lineItem=t, curveId=curveId))
            t.sigDragged.connect(lambda: self.selectionInifiniteLineDragged(lineItem=t))



    def updatePlotDataItemStyle(self, curveId: Union[str, None]) -> None:
        """
        Modify the style of a plotDataItem.
        Use to indicate which plotDataItem is currently selected

        Parameters
        ----------
        curveId : str
            Id of the curve.
            If None, put back the default plotDataItem style.
            See getCurveId from MainApp
        """

        curveIdToRemove = [i for i in list(self.curves.keys()) if 'selection' in i]
        if len(curveIdToRemove)>0:
            self.removePlotDataItem(curveIdToRemove[0])

        # By default we put back the default style to all plotDataItem
        for curve in self.curves.values():
            
            # Create new style
            lineStyle = QtCore.Qt.SolidLine 
            mkPen = pg.mkPen(color=config['plot1dColors'][curve.colorIndex],
                            style=lineStyle,
                            width=config['plotDataItemWidth'])
            mkShadowPen = pg.mkPen(color=config['plot1dColorsComplementary'][curve.colorIndex],
                            width=0)

            # Apply new style
            curve.setPen(mkPen)
            curve.setShadowPen(mkShadowPen)
        
        # Then we apply the selected style to only one of the plotDataItem
        if curveId is not None:
            # Create new style
            lineStyle = QtCore.Qt.DashLine
            mkPen = pg.mkPen(color=config['plot1dColors'][self.curves[curveId].colorIndex],
                            style=lineStyle,
                            width=config['plotDataItemWidth'])

            mkShadowPen = pg.mkPen(color=config['plot1dColorsComplementary'][self.curves[curveId].colorIndex],
                            width=config['plotDataItemShadowWidth'])
            
            # Get data to display with a different style
            x, y = self.getSelectedData(curveId)

            self.addPlotDataItem(x, y, curveId+'-selection', '', '', showInLegend=False)


            # Apply new style
            self.curves[curveId+'-selection'].setPen(mkPen)
            self.curves[curveId+'-selection'].setShadowPen(mkShadowPen)



    def selectPlotDataItem(self, rb: QtWidgets.QRadioButton) -> None:
        """
        Method called when user clicks on a radioButton of the list of
        plotDataItem.
        The method will put the curve data in memory and display which
        plotDataItem is currently selected.
        If the use clicked on the None button, we delete the selected data and
        all subsequent object created with it.
        Called the following method:
            updateSelectionInifiteLine
            updatePlotDataItemStyle
            enableWhenPlotDataItemSelected

        Parameters
        ----------
        rb : QtWidgets.QRadioButton
            Qt radio button being clicked.
        """
        radioButton = self.plotDataItemButtonGroup.checkedButton()

        # When user click None, we unselect everything
        if radioButton.curveId is None:

            # Remove fit curve if plotted
            if 'fit' in list(self.curves.keys()):
                self.removePlotDataItem('fit')
                self.fitWindow.close()

                for radioButton in self.fitModelButtonGroup.buttons():
                    radioButton.setCheckable(False)
                    radioButton.setCheckable(True)

            # Remove filtering curve if plotted
            if 'filtering' in list(self.curves.keys()):
                self.removePlotDataItem('filtering')
                self.filteringWindow.close()

                for radioButton in self.filteringModelButtonGroup.buttons():
                    radioButton.setCheckable(False)
                    radioButton.setCheckable(True)

            # Remove FFT curve
            for radioButton in [self.radioButtonFFT, self.radioButtonIFFT, self.radioButtonFFTnoDC]:
                radioButton.setCheckable(False)
                radioButton.setCheckable(True)


            fftplot = self.getPlotFFTFromRef(self.plotRef)
            if fftplot is not None:
                fftplot.close()

            self.updateSelectionInifiteLine(None)
            self.updatePlotDataItemStyle(None)
            self.enableWhenPlotDataItemSelected(False)

        else:

            self.selectedX     = self.curves[radioButton.curveId].xData
            self.selectedY     = self.curves[radioButton.curveId].yData
            self.selectedLabel = self.curves[radioButton.curveId].curveLabel

            # The addInfiniteLine method has be launched before the update
            self.updateSelectionInifiteLine(radioButton.curveId)
            self.updatePlotDataItemStyle(radioButton.curveId)
            self.enableWhenPlotDataItemSelected(True)



    def enableWhenPlotDataItemSelected(self, enable: bool) -> None:
        """
        Method called when user clicks on a radioButton of the list of
        plotDataItem.
        Make enable or disable the radioButton of models.

        Parameters
        ----------
        enable : bool
            Enable or not the GUI to interact with the selected curve.
        """

        self.groupBoxCurveInteraction.setEnabled(enable)
        self.groupBoxFFT.setEnabled(enable)
        self.groupBoxFit.setEnabled(enable)



    ####################################
    #
    #           Method to related to fit
    #
    ####################################



    def initFitGUI(self) -> None:
        """
        Method called at the initialization of the GUI.
        Make a list of radioButton reflected the available list of fitmodel.
        By default all radioButton are disabled and user should chose a plotDataItem
        to make them available.
        """
    
        # Get list of fit model
        listClasses = [m[0] for m in inspect.getmembers(fit, inspect.isclass) if 'getInitialParams' in [*m[1].__dict__.keys()]]
        # Add a radio button for each model of the list
        self.fitModelButtonGroup = QtWidgets.QButtonGroup()
        for i, j in enumerate(listClasses):

            _class = getattr(fit, j)

            if '2d' not in j:
                
                obj = _class([], [])
                rb = QtWidgets.QRadioButton(obj.displayedLabel())
                rb.fitModel = j
                rb.clicked.connect(self.radioButtonFitState)
                # rb.setEnabled(False)
                self.fitModelButtonGroup.addButton(rb, i)
                self.verticalLayoutFitModel.addWidget(rb)

        del(obj)



    def radioButtonFitState(self) -> None:
        """
        Method called when user click on a radioButton of a fitModel.
        Launch a fit of the data using the chosen model and display the results.
        """

        # If a fit curve is already plotted, we remove it before plotting a new
        # one
        if 'fit' in list(self.curves.keys()):
                self.removePlotDataItem('fit')
                self.fitWindow.close()
        
        radioButton = self.fitModelButtonGroup.checkedButton()

        # Find which model has been chosed and instance it
        _class = getattr(fit, radioButton.fitModel)
        obj = _class(self, self.selectedX, self.selectedY)

        # Do the fit
        x, y, params, self.fitWindow =  obj.ffit()

        # Plot fit curve
        self.addPlotDataItem(x           = x,
                             y           = y,
                             curveId     = 'fit',
                             curveLabel  = self.selectedLabel,
                             curveLegend = obj.displayedLegend(params))



    ####################################
    #
    #           Method to related to filtering
    #
    ####################################



    def radioButtonFilteringtState(self) -> None:
        """
        Method called when user click on a radioButton of a filteringModel.
        Launch a filering of the data using the chosen model and display the
        results.
        """

        # If a filtering curve is already plotted, we remove it before plotting
        # a new one
        if 'filtering' in list(self.curves.keys()):
                self.removePlotDataItem('filtering')
                self.filteringWindow.close()
        
        radioButton = self.filteringModelButtonGroup.checkedButton()

        # Find which model has been chosed and instance it
        _class = getattr(filtering, radioButton.filteringModel)
        obj = _class(self.selectedX, self.selectedY, self.updatePlotDataItem)

        # Do the filtering
        x, y, self.filteringWindow, legend =  obj.runFiltering()

        # Plot filtered curve
        self.addPlotDataItem(x           = x,
                             y           = y,
                             curveId     = 'filtering',
                             curveLabel  = self.selectedLabel,
                             curveLegend = legend)




    def initFilteringGUI(self) -> None:
        """
        Method called at the initialization of the GUI.
        Make a list of radioButton reflected the available list of filtering model.
        By default all radioButton are disabled and user should chose a plotDataItem
        to make them available.
        """
    
        # Get list of filtering model
        listClasses = [m[0] for m in inspect.getmembers(filtering, inspect.isclass) if 'runFiltering' in [*m[1].__dict__.keys()]]
        # Add a radio button for each model of the list
        self.filteringModelButtonGroup = QtWidgets.QButtonGroup()
        for i, j in enumerate(listClasses):

            _class = getattr(filtering, j)
            
            obj = _class(self, [], [])
            rb = QtWidgets.QRadioButton(obj.checkBoxLabel())
            rb.filteringModel = j
            rb.clicked.connect(self.radioButtonFilteringtState)
            # rb.setEnabled(False)
            self.filteringModelButtonGroup.addButton(rb, i)
            self.verticalLayoutFilteringModel.addWidget(rb)

        del(obj)

