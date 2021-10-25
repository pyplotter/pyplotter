# This Python file uses the following encoding: utf-8
from __future__ import annotations
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pyqtgraph as pg
from typing import List, Union, Callable, Optional
import inspect
from scipy.integrate import cumtrapz


from ..ui.plot1d import Ui_Dialog
from .config import config
from .plot_app import PlotApp
from . import fit
from . import filtering
from .DateAxisItem import DateAxisItem



class Plot1dApp(QtWidgets.QDialog, Ui_Dialog, PlotApp):
    """
    Class to handle ploting in 1d.
    """


    def __init__(self, x                  : np.ndarray,
                       y                  : np.ndarray,
                       title              : str,
                       xLabelText         : str,
                       xLabelUnits        : str,
                       yLabelText         : str,
                       yLabelUnits        : str,
                       windowTitle        : str,
                       runId              : int,
                       cleanCheckBox      : Callable[[str, str, int, Union[str, list]], None],
                       plotRef            : str,
                       addPlot            : Callable,
                       getPlotFromRef     : Callable,
                       linkedTo2dPlot     : bool=False,
                       curveId            : Optional[str]=None,
                       curveLegend        : Optional[str]=None,
                       timestampXAxis     : bool=False,
                       livePlot           : bool=False,
                       curveSlicePosition : Optional[float]=None,
                       parent             = None):
        """
        Class handling the plot of 1d data.
        Allow some quick data treatment.
        A plot can be a slice of a 2d plot.
        A Plot can be a livePlot, i.e. being currently measured.

        Parameters
        ----------
        x : np.ndarray
            Data along the x axis, 1d array.
        y : np.ndarray
            Data along the y axis, 1d array.
        title : str
            Plot title.
        xLabelText : str
            Label text along the x axis.
        xLabelUnits : str
            Label units along the x axis.
        yLabelText : str
            Label text along the y axis.
        yLabelUnits : str
            Label units along the y axis.
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
        getPlotFromRef : Callable
            Function from the mainApp used to remove 1d plot and keep plot
            reference updated.
        linkedTo2dPlot : bool, optional
            If the 1d plot is a slice from a 2d plot, by default False
        curveId : Optional[str], optional
            Id of the curve being plot, see getCurveId in the mainApp., by default None
        curveLegend : Optional[str], optional
            Label of the curve legend.
            If None, is the same as yLabelText, by default None
        timestampXAxis : bool, optional
            If yes, the x axis becomes a pyqtgraph DateAxisItem.
            See pyqtgraph doc about DateAxisItem, by default False
        livePlot : bool, optional
            If the plot is a livePlot one, by default False
        curveSlicePosition : Optional, float
            If the curve is a slice of a 2d map, contains its position if the
            slice axis
        parent : [type], optional
            [description], by default None
        """
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
        self.getPlotFromRef = getPlotFromRef

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
        
        # Initialize font size spin button with the config file
        self.spinBoxFontSize.setValue(config['axisLabelFontSize'])


        # Connect UI
        self.checkBoxLogX.stateChanged.connect(self.checkBoxLogState)
        self.checkBoxLogY.stateChanged.connect(self.checkBoxLogState)
        self.checkBoxSymbol.stateChanged.connect(self.checkBoxSymbolState)
        self.checkBoxSplitYAxis.stateChanged.connect(self.checkBoxSplitYAxisState)

        self.checkBoxDifferentiate.clicked.connect(self.clickDifferentiate)
        self.checkBoxIntegrate.clicked.connect(self.clickIntegrate)
        
        self.radioButtonFFT.clicked.connect(lambda:self.clickFFT(self.radioButtonFFT))
        self.radioButtonFFTnoDC.clicked.connect(lambda:self.clickFFT(self.radioButtonFFTnoDC))
        self.radioButtonIFFT.clicked.connect(lambda:self.clickFFT(self.radioButtonIFFT))

        self.spinBoxFontSize.valueChanged.connect(self.clickFontSize)

        # Add a radio button for each model of the list
        self.plotDataItemButtonGroup = QtWidgets.QButtonGroup()
        self.radioButtonFitNone.curveId = None
        self.plotDataItemButtonGroup.addButton(self.radioButtonFitNone, 0)
        self.radioButtonFitNone.clicked.connect(self.selectPlotDataItem)
        self.radioButtonFitNone.setChecked(True)


        self.setWindowTitle(windowTitle)

        self.plotItem.setTitle(title=title,
                               color=config['styles'][config['style']]['pyqtgraphTitleTextColor'])

        # To make the GUI faster
        self.plotItem.disableAutoRange()

        # Personalize the GUI
        if config['plot1dGrid']:
            self.plotItem.showGrid(x=True, y=True)

        self.plotItem.setLabel(axis='bottom',
                               text=xLabelText,
                               units=xLabelUnits,
                               **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(config['axisLabelFontSize'])+'pt'})
        self.plotItem.setLabel(axis='left',  
                               text=yLabelText,
                               units=yLabelUnits,
                               **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                      'font-size' : str(config['axisLabelFontSize'])+'pt'})


        font=QtGui.QFont()
        font.setPixelSize(config['tickLabelFontSize'])
        self.plotItem.getAxis('bottom').setTickFont(font)
        self.plotItem.getAxis('left').setTickFont(font)
        self.plotItem.getAxis('bottom').setPen(config['styles'][config['style']]['pyqtgraphxAxisTicksColor'])
        self.plotItem.getAxis('left').setPen(config['styles'][config['style']]['pyqtgraphyAxisTicksColor'])

        self.setStyleSheet("background-color: "+str(config['styles'][config['style']]['dialogBackgroundColor'])+";")
        self.setStyleSheet("color: "+str(config['styles'][config['style']]['dialogTextColor'])+";")


        # If the xaxis used timestamp, we use a dedicated axisItem
        if self.timestampXAxis:
            # This utc offset is unclear to me...
            self.plotItem.setAxisItems({'bottom' : DateAxisItem(utcOffset=0.)})

        # Display initial data curve
        if curveLegend is None:
            curveLegend = yLabelText

        self.addPlotDataItem(x                  = x,
                             y                  = y,
                             curveId            = curveId,
                             curveLabel         = yLabelText,
                             curveUnits         = yLabelUnits,
                             curveLegend        = curveLegend,
                             curveSlicePosition = curveSlicePosition)

        # AutoRange only after the first data item is added
        self.autoRange()

        # Should be initialize last
        PlotApp.__init__(self)



    ####################################
    #
    #           Properties
    #
    ####################################


    @property
    def xLabelText(self) -> str:

        if hasattr(self, 'plotItem'):
            return self.plotItem.axes['bottom']['item'].labelText
        else:
            return ''



    @property
    def yLabelText(self) -> str:

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

        if self.fitWindow is not None:
            self.fitWindow.close()

        if self.filteringWindow is not None:
            self.filteringWindow.close()

        for curveType in ['fft', 'derivative', 'primitive']:
            plot = self.getPlotFromRef(self.plotRef, curveType)
            if plot is not None:
                plot.close()
        
        self.cleanCheckBox(plotRef     = self.plotRef,
                           windowTitle = self.windowTitle,
                           runId       = self.runId,
                           label       = '')



    def o(self):
        if self.fitWindow is not None:
            self.fitWindow.close()
        self.close()



    ####################################
    #
    #           Method related to the plotDataItem
    #
    ####################################


    def getNotHiddenCurves(self) -> dict:
        """
        Obtain the dict of not hidden curves
        """
    
        curvesNotHidden = {}
        for curveId, plotDataItem in self.curves.items():
            if not plotDataItem.hidden:
                curvesNotHidden[curveId] = plotDataItem

        return curvesNotHidden



    def autoRange(self) -> None:
        """
        Autorange the plotItem based on the unHide plotDataItem.
        """
        
        curvesNotHidden = self.getNotHiddenCurves()
        
        xRange = [1e99, -1e99]
        yRange = [1e99, -1e99]
        
        for curveId, plotDataItem in curvesNotHidden.items():
            
            xRangeTemp = plotDataItem.dataBounds(0)
            yRangeTemp = plotDataItem.dataBounds(1)
            
            if xRangeTemp[0] is not None and xRangeTemp[1] is not None and yRangeTemp[0] is not None and yRangeTemp[1] is not None:
                
                if xRangeTemp[0]<xRange[0]:
                    xRange[0] = xRangeTemp[0]
                if yRangeTemp[0]<yRange[0]:
                    yRange[0] = yRangeTemp[0]
                
                if xRangeTemp[1]>xRange[1]:
                    xRange[1] = xRangeTemp[1]
                if yRangeTemp[1]>yRange[1]:
                    yRange[1] = yRangeTemp[1]

        self.plotItem.setRange(xRange=xRange, yRange=yRange)



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



    def updatePlotDataItem(self, x                  : np.ndarray,
                                 y                  : np.ndarray,
                                 curveId            : str,
                                 curveLegend        : Optional[str]=None,
                                 curveSlicePosition : Optional[str]=None,
                                 autoRange          : bool=False) -> None:
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
        curveSlicePosition : Optional, float
            If the curve is a slice of a 2d map, contains its position if the
            slice axis
        autoRange : bool
            If the view should perform an autorange after updating the data.
            Can be slow for heavy data array.
        """

        self.curves[curveId].setData(x=x, y=y)

        if curveLegend is not None:
            self.curves[curveId].curveLegend = curveLegend
            self.updateLegend()
        
        if curveSlicePosition is not None:
            self.curves[curveId].curveSlicePosition = curveSlicePosition

        if autoRange:
            self.autoRange()



    def addPlotDataItem(self, x                 : np.ndarray,
                              y                 : np.ndarray,
                              curveId           : str,
                              curveLabel        : str,
                              curveUnits        : str,
                              curveLegend       : str,
                              showInLegend      : bool=True,
                              hidden            : bool=False,
                              curveSlicePosition: Optional[float]=None) -> None:
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
        curveUnits : str
            y units of the curve.
        curveLegend : str
            Legend label of the curve.
        showInLegend : bool
            If the plotDataLegend should be shown in the legend.
            Default True.
        hidden : bool
            If the plotDataItem is hidden.
            Default False.
        curveSlicePosition : Optional, float
            If the curve is a slice of a 2d map, contains its position if the
            slice axis
        """

        # Get the dataPlotItem color
        colorIndex, mkpen = self.getLineColor()

        # Create plotDataItem and save its reference
        self.curves[curveId] = self.plotItem.plot(x, y, pen=mkpen)

        # Create usefull attribute
        self.curves[curveId].colorIndex         = colorIndex
        self.curves[curveId].curveLabel         = curveLabel
        self.curves[curveId].curveUnits         = curveUnits
        self.curves[curveId].curveLegend        = curveLegend
        self.curves[curveId].showInLegend       = showInLegend
        self.curves[curveId].hidden             = hidden
        self.curves[curveId].curveSlicePosition = curveSlicePosition
        self.curves[curveId].mkpen              = mkpen
        
        self.updateListDataPlotItem(curveId)



    def removePlotDataItem(self, curveId: str) -> None:
        """
        Remove a PlotDataItem identified via its "curveId".

        Parameters
        ----------
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        """

        # If no curve will be displayed, we close the QDialog
        if len(self.curves)==1:
            self.o()
        else:
            # Remove the curve
            self.plotItem.removeItem(self.curves[curveId])
            del(self.curves[curveId])

            self.updateListDataPlotItem(curveId)



    def updateyLabel(self) -> None:
        """
        Update the ylabel of the plotItem, only if linkedTo2dPlot is False.
        There are 4 cases depending of the number of dataPlotItem:
            1. If there is 1: the displayed ylabel is the data ylabel.
            2. If there are more than 1 with the same unit: the unit is displayed.
            3. If there are more than 1 with different unit: the unit "a.u" displayed.
            4. If there is 2 and one is the selection curve: we change nothing.
            5. If all curves are hidden, we display "None".
        """
        
        # Obtain the list of not hidden plotDataItem
        curvesNotHidden = self.getNotHiddenCurves()
        
        # The label is changed only of we are not display slices of a 2d plot
        if not self.linkedTo2dPlot:
            
            # If there are two curves and on is the selection one, we change nothing
            if len(curvesNotHidden)==2 and any(['selection' in curveId for curveId in curvesNotHidden.keys()]):
                pass
            # If there is more than one plotDataItem
            # We check of the share the same unit
            elif len(curvesNotHidden)>1 and len(set(curve.curveUnits for curve in curvesNotHidden.values()))==1:
                self.plotItem.setLabel(axis ='left',
                                       text ='',
                                       units=curvesNotHidden[list(curvesNotHidden.keys())[0]].curveUnits)
            # We check of the share the same label
            elif len(set(curve.curveLabel for curve in curvesNotHidden.values()))>1:
                self.plotItem.setLabel(axis ='left',
                                       text ='',
                                       units='a.u')
            # If there is only one plotDataItem or if the plotDataItems share the same label
            elif len(curvesNotHidden)==1:
                self.plotItem.setLabel(axis ='left',
                                       text =curvesNotHidden[list(curvesNotHidden.keys())[0]].curveLabel,
                                       units=curvesNotHidden[list(curvesNotHidden.keys())[0]].curveUnits)
            else:
                self.plotItem.setLabel(axis ='left',
                                       text ='None',
                                       units='')



    def updateLegend(self) -> None:
        """
        Update the legendItem of the plotItem.
        Only plotDataItem with showInLegend==True and hidden==False are shown
        To do so, we
        1. Clear the legendItem.
        2. Browse plotDataItem and add then to the freshly cleared legendItem.
        """

        self.legendItem.clear()
        
        # We do not add items in the legend when there is only one curve
        # except when the 1d plot is linked to a 2d plot
        if len(self.curves)==1:
            if self.linkedTo2dPlot:
                for curve in self.curves.values():
                    if curve.showInLegend and not curve.hidden:
                        self.legendItem.addItem(curve, curve.curveLegend)
        elif len(self.curves) > 1:
            for curve in self.curves.values():
                if curve.showInLegend and not curve.hidden:
                    self.legendItem.addItem(curve, curve.curveLegend)



    def updateListDataPlotItem(self, curveId: str) -> None:
        """
        Method called when a plotDataItem is added or removed to the plotItem.
        Add a radioButton to allow the user to select the plotDataItem.
        Add a checkBox to allow the user to hide the plotDataItem.

        Parameters
        ----------
        curveId : str
            Id of the curve.
            See getCurveId from MainApp
        """

        if len(self.curves)==2:
            self.checkBoxSplitYAxis.setEnabled(True)
        else:
            self.checkBoxSplitYAxis.setEnabled(False)

        # Update list of plotDataItem only if the plotDataItem is not a fit
        if curveId not in ['fit', 'filtering']:
            
            if 'selection' not in curveId:
                # Add a radioButton to allow the user to select the plotDataItem.
                # If there is already a button with curveId, we remove it
                createButton = True
                for radioButton in self.plotDataItemButtonGroup.buttons():
                    if radioButton.curveId==curveId:
                        self.plotDataItemButtonGroup.removeButton(radioButton)
                        radioButton.setParent(None)
                        createButton = False
                # Otherwise, we create it
                if createButton:
                    radioButton = QtWidgets.QRadioButton(self.curves[curveId].curveLabel)
                    radioButton.curveId = curveId
                    self.plotDataItemButtonGroup.addButton(radioButton, len(self.plotDataItemButtonGroup.buttons()))
                    radioButton.clicked.connect(self.selectPlotDataItem)
                    self.verticalLayoutPlotDataItem.addWidget(radioButton)
                
                # Add a checkBox to allow the user to hide the plotDataItem.
                # If there is already a button with curveId, we remove it
                createButton = True
                for i in range(self.verticalLayoutHide.count()):
                    if self.verticalLayoutHide.itemAt(i) is not None:
                        checkBox = self.verticalLayoutHide.itemAt(i).widget()
                        if checkBox.curveId==curveId:
                            self.verticalLayoutHide.removeWidget(checkBox)
                            checkBox.setParent(None)
                            createButton = False
                # Otherwise, we create it
                if createButton:
                    checkBox = QtWidgets.QCheckBox(self.curves[curveId].curveLabel)
                    checkBox.curveId = curveId
                    checkBox.stateChanged.connect(lambda : self.hidePlotDataItem(checkBox))

                    checkBox.setChecked(self.curves[curveId].hidden)
                    self.verticalLayoutHide.addWidget(checkBox)

        # We update displayed information
        self.updateLegend()
        self.updateyLabel()



    def nbPlotDataItemFromData(self) -> int:
        """
        Return the number of plotDataItem coming from real user data.
        That count does not take into account "selection", "fit" and
        "filtering" curves.
        """
        
        nb = 0
        for curveId in self.curves.keys():
            if curveId not in ['filtering', 'fit']:
                if 'selection' not in curveId:
                    nb += 1
                
        return nb


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
        
        Parameters
        ----------
        plots : List[Plot1dApp]
            List containing all the 1d plot window currently displayed.
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
                
                self.tabLayout = QtWidgets.QVBoxLayout()
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
                        label = plot.windowTitle+'\n'+\
                                plot.curves[curveId].curveLabel

                        cb.setText(label)

                        cb.toggled.connect(lambda state,
                                                  runId   = str(plot.runId),
                                                  curveId = str(curveId),
                                                  plot    = plot: self.toggleNewPlot(state, runId, curveId, plot))
                        
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
                del(self.tabCurves)



    def toggleNewPlot(self, state: bool,
                            runId: str,
                            curveId: str,
                            plot: Plot1dApp) -> None:
        """
        Called when user click on the checkbox of the curves tab.
        Add or remove curve in the plot window.

        Parameters
        ----------
        state : bool
            State of the checkbox button.
        runId : str
            Id of the qcodes run, 0 if the curve is not from qcodes.
        curveId : str
            Id of the curve related to the checkbox, see getCurveId in the mainApp.
        plot : Plot1dApp
            Plot1dApp where the curve comes from.
        """
        
        if state:
            self.addPlotDataItem(x           = plot.curves[curveId].xData,
                                 y           = plot.curves[curveId].yData,
                                 curveId     = curveId,
                                 curveLabel  = plot.curves[curveId].curveLabel,
                                 curveUnits  = plot.curves[curveId].curveUnits,
                                 curveLegend = '{} - {}'.format(runId, plot.curves[curveId].curveLabel))

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
        
        # If split y axis enable
        if hasattr(self, 'curveRight'):
            plotItems = [self.plotItem, self.curveRight]
        else:
            plotItems = [self.plotItem]
        
        if self.checkBoxLogX.isChecked():
            if self.checkBoxLogY.isChecked():
                [item.setLogMode(True, True) for item in plotItems]
            else:
                [item.setLogMode(True, False) for item in plotItems]
        else:
            if self.checkBoxLogY.isChecked():
                [item.setLogMode(False, True) for item in plotItems]
            else:
                [item.setLogMode(False, False) for item in plotItems]

        if hasattr(self, 'curveRight'):
            self.vbRight.autoRange()



    def checkBoxSymbolState(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user click on the Symbol checkBox.
        Put symbols on all plotDataItem except fit model.
        """
        
        if self.checkBoxSymbol.isChecked():
            
            for i, (key, curve) in enumerate(list(self.curves.items())):
                if key != 'fit':
                    curve.setSymbol(config['plot1dSymbol'][i%len(config['plot1dSymbol'])])
                    
                    # If split y axis enable
                    if hasattr(self, 'curveRight'):
                        self.curveRight.setSymbol(config['plot1dSymbol'][i%len(config['plot1dSymbol'])])
                        
        else:
            for i, (key, curve) in enumerate(list(self.curves.items())):
                if key != 'fit':
                    curve.setSymbol(None)
                
            # If split y axis enable
            if hasattr(self, 'curveRight'):
                self.curveRight.setSymbol(None)



    def splitAutoBtnClicked(self) -> None:
        """
        Method used to overwrite the standard "autoBtnClicked" of the PlotItem.
        Simply allow, in the split mode view (see checkBoxSplitYAxisState), to
        autorange the two viewbox at the same time.
        """
        if self.plotItem.autoBtn.mode == 'auto':
            self.vbRight.setYRange(self.vbRight.addedItems[0].yData.min(), self.vbRight.addedItems[0].yData.max())
            self.vbRight.setXRange(self.vbRight.addedItems[0].xData.min(), self.vbRight.addedItems[0].xData.max())
            self.plotItem.enableAutoRange()
            self.plotItem.autoBtn.hide()
        else:
            self.plotItem.disableAutoRange()



    def checkBoxSplitYAxisState(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user click on the Symbol checkBox.
        Put symbols on all plotDataItem except fit model.
        """
        
        # Only work for two plotDataItem
        if len(self.curves)==2:
            
            # Get the curveId for the curve linked to the left and right axis.
            leftCurveId  = list(self.curves.keys())[0]
            rightCurveId = list(self.curves.keys())[1]
            
            if self.checkBoxSplitYAxis.isChecked():
                
                self.groupBoxCurveInteraction.setEnabled(False)
            
                # Create an empty plotDataItem which will contain the right curve
                self.curveRight = pg.PlotDataItem(pen=self.curves[rightCurveId].mkpen)
                
                # Create and set links for a second viewbox which will contains the right curve
                self.vbRight = pg.ViewBox()
                self.vbRight.setXLink(self.plotItem)
                self.plotItem.scene().addItem(self.vbRight)
                self.plotItem.showAxis('right')
                self.plotItem.getAxis('right').linkToView(self.vbRight)
                
                # Remove the plotDataItem which will be on the second viewbox
                self.plotItem.removeItem(self.curves[rightCurveId])
                
                # Remove the legendItem, now obsolete with the right axis
                self.legendItem.clear()
                
                # Display the correct information on each axis about their curve
                self.plotItem.setLabel(axis='left',
                                    text=self.curves[leftCurveId].curveLabel,
                                    units=self.curves[leftCurveId].curveUnits,
                                    **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                        'font-size' : str(config['axisLabelFontSize'])+'pt'})
                self.plotItem.setLabel(axis='right',
                                    text=self.curves[rightCurveId].curveLabel,
                                    units=self.curves[rightCurveId].curveUnits,
                                    **{'color'     : config['styles'][config['style']]['pyqtgraphyLabelTextColor'],
                                        'font-size' : str(config['axisLabelFontSize'])+'pt'})

                # Add the plotDataItem in the right viewbox
                self.vbRight.addItem(self.curveRight)
                self.curveRight.setData(self.curves[rightCurveId].xData, self.curves[rightCurveId].yData)
                self.vbRight.setYRange(self.curves[rightCurveId].yData.min(), self.curves[rightCurveId].yData.max())
                
                # Sorcery to me, found here:
                # https://stackoverflow.com/questions/29473757/pyqtgraph-multiple-y-axis-on-left-side
                # If that's not here, the views are incorrect
                def updateViews():
                    self.vbRight.setGeometry(self.plotItem.getViewBox().sceneBoundingRect())
                    self.vbRight.linkedViewChanged(self.plotItem.getViewBox(), self.vbRight.XAxis)
                updateViews()
                self.plotItem.getViewBox().sigResized.connect(updateViews)
                
                # We overwrite the autoRange button to make it work with
                # both axis
                self.plotItem.autoBtn.clicked.disconnect(self.plotItem.autoBtnClicked)
                self.plotItem.autoBtn.clicked.connect(self.splitAutoBtnClicked)
            else:
                
                self.groupBoxCurveInteraction.setEnabled(True)
                
                # Restore the autoRange button original method
                self.plotItem.autoBtn.clicked.disconnect(self.splitAutoBtnClicked)
                self.plotItem.autoBtn.clicked.connect(self.plotItem.autoBtnClicked)
                
                # Remove the right viewbox and other stuff done for the right axis
                self.plotItem.hideAxis('right')
                self.plotItem.scene().removeItem(self.vbRight)
                self.plotItem.getViewBox().sigResized.disconnect()
                del(self.vbRight)
                del(self.curveRight)
                
                # Put back the left view box as it was before the split
                self.plotItem.addItem(self.curves[rightCurveId])
                
                self.updateLegend()
                self.updateyLabel()




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



    def hidePlotDataItem(self, cb : QtWidgets.QCheckBox) -> None:
        
        curveId      = cb.curveId
        plotDataItem = self.curves[curveId]
        
        # We get the interaction radioBox having the same curveId
        radioBox = [i for i in [self.verticalLayoutPlotDataItem.itemAt(i).widget() for i in range(self.verticalLayoutPlotDataItem.count())] if i.curveId==curveId][0]
        
        if cb.isChecked():
            
            # if checkBox.isChecked():
            plotDataItem.setAlpha(0, False)
            plotDataItem.hidden = True
            
            # When the curve is hidden, we do not allow interaction with it
            radioBox.setEnabled(False)
        else:
            # If the curve was previously hidden
            if plotDataItem.hidden:
                plotDataItem.hidden = False
                plotDataItem.setAlpha(1, False)
                
                radioBox.setEnabled(True)
        
        # Update the display
        self.updateyLabel()
        self.updateLegend()
        self.autoRange()



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

        xLabelText  = '1/'+self.plotItem.axes['bottom']['item'].labelText
        xLabelUnits = '1/'+self.plotItem.axes['bottom']['item'].labelUnits
        yLabelText  = text.upper()+'( '+self.selectedLabel+' )'
        yLabelUnits = self.selectedUnits+'/'+self.plotItem.axes['bottom']['item'].labelUnits
        title  = self.windowTitle+' - '+text.upper()

        fftPlot = self.getPlotFromRef(self.plotRef, 'fft')
        if fftPlot is not None:
            fftPlot.close()
        
        self.addPlot(plotRef        = self.plotRef+'fft',
                     data           = [x, y],
                     xLabelText     = xLabelText,
                     xLabelUnits    = xLabelUnits,
                     yLabelText     = yLabelText,
                     yLabelUnits    = yLabelUnits,
                     cleanCheckBox  = self.cleanCheckBox,
                     plotTitle      = title,
                     windowTitle    = title,
                     runId          = 1,
                     linkedTo2dPlot = False,
                     curveId        = yLabelText,
                     curveLegend    = yLabelText,
                     curveLabel     = yLabelText,
                     timestampXAxis = False,
                     livePlot       = False)



    ####################################
    #
    #           Method to related to calculus
    #
    ####################################



    def clickDifferentiate(self) -> None:
        """
        Method called when user click on the derivative checkbox.
        Add a plot containing the derivative of the chosen data.
        """
        
        # Get xLabel information
        xLabelText  = self.plotItem.axes['bottom']['item'].labelText
        xLabelUnits = self.plotItem.axes['bottom']['item'].labelUnits
        
        # Build new curve information
        yLabelText  = '∂('+self.selectedLabel+')/∂('+xLabelText+')'
        yLabelUnits = self.selectedUnits+'/'+xLabelUnits
        title       = self.windowTitle+' - derivative'
        curveId     = self.selectedLabel+'derivative'
        
        # If user wants to plot the derivative, we add a new plotWindow
        if self.checkBoxDifferentiate.isChecked():
            
            x = self.selectedX
            y = np.gradient(self.selectedY, self.selectedX)
            
            # Is there already a derivative plot associated to the plot1d
            plot = self.getPlotFromRef(self.plotRef, 'derivative')
            if plot is not None:
                plot.updatePlotDataItem(x         = x,
                                        y         = y,
                                        curveId   = curveId,
                                        autoRange = True)
            # If not, we create one
            else:
                
                def buffer(**kwargs):
                    """
                    Function called when a derivative plot is closed.
                    Uncheck its associated checkbox and called the usual close
                    function
                    """
                    
                    self.checkBoxDifferentiate.setChecked(False)
                    self.cleanCheckBox(**kwargs)
                    
                self.addPlot(plotRef        = self.plotRef+'derivative',
                             data           = [x, y],
                             xLabelText     = xLabelText,
                             xLabelUnits    = xLabelUnits,
                             yLabelText     = yLabelText,
                             yLabelUnits    = yLabelUnits,
                             cleanCheckBox  = buffer,
                             plotTitle      = title,
                             windowTitle    = title,
                             runId          = 1,
                             linkedTo2dPlot = False,
                             curveId        = curveId,
                             curveLegend    = yLabelText,
                             curveLabel     = yLabelText,
                             timestampXAxis = False,
                             livePlot       = False)
        # Otherwise, we close the existing one
        else:
            plot = self.getPlotFromRef(self.plotRef, 'derivative')
            if plot is not None:
                plot.close()



    def clickIntegrate(self) -> None:
        """
        Method called when user click on the integrate checkbox.
        Add a plot containing the primitive of the chosen data.
        """

        # Get xLabel information
        xLabelText  = self.plotItem.axes['bottom']['item'].labelText
        xLabelUnits = self.plotItem.axes['bottom']['item'].labelUnits
        
        # Build new curve information
        yLabelText  = '∫ '+self.selectedLabel+'  d '+xLabelText
        yLabelUnits = self.selectedUnits+' x '+xLabelUnits
        title   = self.windowTitle+' - primitive'
        curveId = self.selectedLabel+'primitive'
        

        # If user wants to plot the primitive, we add a new plotWindow
        if self.checkBoxIntegrate.isChecked():
            
            x = self.selectedX
            y = cumtrapz(self.selectedY, self.selectedX, initial=0)
            
            # Is there already a primitive plot associated to the plot1d
            plot = self.getPlotFromRef(self.plotRef, 'primitive')
            if plot is not None:
                plot.updatePlotDataItem(x         = x,
                                        y         = y,
                                        curveId   = curveId,
                                        autoRange = True)
            # If not, we create one
            else:
                
                def buffer(**kwargs):
                    """
                    Function called when a primitive plot is closed.
                    Uncheck its associated checkbox and called the usual close
                    function
                    """
                    
                    self.checkBoxIntegrate.setChecked(False)
                    self.cleanCheckBox(**kwargs)
                    
                    
                self.addPlot(plotRef        = self.plotRef+'primitive',
                             data           = [x, y],
                             xLabelText     = xLabelText,
                             xLabelUnits    = xLabelUnits,
                             yLabelText     = yLabelText,
                             yLabelUnits    = yLabelUnits,
                             cleanCheckBox  = buffer,
                             plotTitle      = title,
                             windowTitle    = title,
                             runId          = 1,
                             linkedTo2dPlot = False,
                             curveId        = curveId,
                             curveLegend    = yLabelText,
                             curveLabel     = yLabelText,
                             timestampXAxis = False,
                             livePlot       = False)
        # Otherwise, we close the existing one
        else:
            plot = self.getPlotFromRef(self.plotRef, 'primitive')
            if plot is not None:
                plot.close()



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
            
        # If a derivative curve is already displayed, we update it
        plot = self.getPlotFromRef(self.plotRef, 'derivative')
        if plot is not None:
            self.clickDifferentiate()
            
        # If a primitive curve is already displayed, we update it
        plot = self.getPlotFromRef(self.plotRef, 'primitive')
        if plot is not None:
            self.clickIntegrate()

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
            if 'a' in self.infiniteLines.keys():
                self.plotItem.removeItem(self.infiniteLines['a'])
            if 'b' in self.infiniteLines.keys():
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
            mkPen = pg.mkPen(color=config['plot1dColors'][curve.colorIndex],
                            style=QtCore.Qt.SolidLine ,
                            width=config['plotDataItemWidth'])
            mkShadowPen = pg.mkPen(color=config['plot1dColorsComplementary'][curve.colorIndex],
                            width=0)

            # Apply new style
            curve.setPen(mkPen)
            curve.setShadowPen(mkShadowPen)
        
        # Then we apply the selected style to only one of the plotDataItem
        if curveId is not None:
            # Create new style
            mkPen = pg.mkPen(color=config['plot1dColorsComplementary'][self.curves[curveId].colorIndex],
                            style=QtCore.Qt.SolidLine ,
                            width=config['plotDataItemWidth'])
            
            # Get data to display with a different style
            x, y = self.getSelectedData(curveId)

            self.addPlotDataItem(x            = x,
                                 y            = y,
                                 curveId      = curveId+'-selection',
                                 curveLabel   = self.curves[curveId].curveLabel,
                                 curveUnits   = self.curves[curveId].curveUnits,
                                 curveLegend  = 'Selection',
                                 showInLegend = True)

            # Apply new style
            self.curves[curveId+'-selection'].setPen(mkPen)



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

        self.updateSelectionInifiteLine(None)
        self.updatePlotDataItemStyle(None)
        checkBoxes = (self.verticalLayoutHide.itemAt(i).widget() for i in range(self.verticalLayoutHide.count()))
        for checkBox in checkBoxes:
            checkBox.setEnabled(True)

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


            fftplot = self.getPlotFromRef(self.plotRef, 'fft')
            if fftplot is not None:
                fftplot.close()

            self.enableWhenPlotDataItemSelected(False)

        else:

            checkBoxes = (self.verticalLayoutHide.itemAt(i).widget() for i in range(self.verticalLayoutHide.count()))
            for checkBox in checkBoxes:
                if checkBox.curveId==radioButton.curveId:
                    checkBox.setEnabled(False)

            self.selectedX     = self.curves[radioButton.curveId].xData
            self.selectedY     = self.curves[radioButton.curveId].yData
            self.selectedLabel = self.curves[radioButton.curveId].curveLabel
            self.selectedUnits = self.curves[radioButton.curveId].curveUnits

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

        self.groupBoxFFT.setEnabled(enable)
        self.groupBoxCalculus.setEnabled(enable)
        self.groupBoxFiltering.setEnabled(enable)
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
        obj = _class(self.selectedX, self.selectedY)

        # Do the fit
        x, y, params, self.fitWindow =  obj.ffit()

        # Plot fit curve
        self.addPlotDataItem(x           = x,
                             y           = y,
                             curveId     = 'fit',
                             curveLabel  = self.selectedLabel,
                             curveUnits  = self.selectedUnits,
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
                             curveUnits  = self.selectedUnits,
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

