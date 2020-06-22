# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import os
import pyqtgraph as pg
import inspect
import sys 
sys.path.append('../ui')

import plot1d
from config import config
from plot_app import PlotApp
import fit

class Plot1dApp(QtWidgets.QDialog, plot1d.Ui_Dialog, PlotApp):
    """
    Class to handle ploting in 1d.
    """


    def __init__(self, x, y, title, xLabel, yLabel, windowTitle, runId, cleanCheckBox,
                linkedTo2dPlot=False, curveId=None, curveLegend=None, parent=None):
        super(Plot1dApp, self).__init__(parent)

        self.setupUi(self)
        
        # Allow resize of the plot window
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)

        self.plotType      = '1d'
        self.curves        = {}
        self.legend        = None
        self.windowTitle   = windowTitle
        self.runId         = runId
        self.cleanCheckBox = cleanCheckBox

        # Is that's 1d plot linked to a 2d plot (slice of a 2d plot)
        self.linkedTo2dPlot = linkedTo2dPlot

        # Keep reference of FFT
        self.fftwindow = []

        # Get plotItem from the widget
        self.plotItem = self.widget.getPlotItem()
        self.resize(*config['dialogWindowSize'])


        # Add fitting function to the GUI
        self.initFitGUI()

        # Reference to QDialog which will contains fit info
        self.fitWindow = None


        self.infiniteLines = {}

        # Connect UI
        self.checkBoxLogX.stateChanged.connect(self.checkBoxLogState)
        self.checkBoxLogY.stateChanged.connect(self.checkBoxLogState)
        self.checkBoxSymbol.stateChanged.connect(self.checkBoxSymbolState)

        self.pushButtonFFT.clicked.connect(lambda:self.clickFFT(self.pushButtonFFT))
        self.pushButtonFFTnoDC.clicked.connect(lambda:self.clickFFT(self.pushButtonFFTnoDC))
        self.pushButtonIFFT.clicked.connect(lambda:self.clickFFT(self.pushButtonIFFT))


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


        # Display initial data curve
        if curveLegend is None:
            curveLegend = yLabel
        self.addPlotDataItem(x = x,
                             y = y,
                             curveId = curveId,
                             curveLabel = yLabel,
                             curveLegend = curveLegend)

        # AutoRange only after the first data item is added
        self.plotItem.autoRange()

        # Should be initialize last
        PlotApp.__init__(self)



    def closeEvent(self, evnt):
        """
        Method called when use closed the plotWindow.
        We propagate that event to the mainWindow
        """

        self.cleanCheckBox(windowTitle=self.windowTitle, runId=self.runId)
        if self.fitWindow is not None:
            self.fitWindow.close()
        if len(self.fftwindow)>0:
            [window.close() for window in self.fftwindow]



    def o(self):
        if self.fitWindow is not None:
            self.fitWindow.close()
        self.close()



    def getLineColor(self):
        """
        Return a pyqtgraph mKpen with the color of the next curve following
        the colors in config files
        """

        colors = [curve.colorIndex for curve in self.curves.values()]
        for i in range(50):
            if i not in colors:
                colorIndex = i
                color = config['plot1dColors'][i]
                break


        mkpen = pg.mkPen(color=color, width=config['plotDataItemWidth'])

        return colorIndex, mkpen



    def updatePlotDataItem(self, x, y, curveId, curveLegend):
        """
        Method called by a plot2d when use drag a sliceLine.
        Updating an existing plotDataItem and the plot legendItem
        """

        self.curves[curveId].setData(x=x, y=y)
        self.curves[curveId].curveLegend = curveLegend
        self.updateLegend()



    def addPlotDataItem(self, x, y, curveId, curveLabel, curveLegend, showInLegend=True):
        """
        Method adding a plotDataItem to the plotItem.
        """

        # Get the dataPlotItem color
        colorIndex, mkpen = self.getLineColor()

        # Create plotDataItem and save its reference
        self.curves[curveId] = self.plotItem.plot(x, y, pen=mkpen)

        # Create attribute usefull
        self.curves[curveId].colorIndex   = colorIndex
        self.curves[curveId].curveLabel   = curveLabel
        self.curves[curveId].curveLegend  = curveLegend
        self.curves[curveId].showInLegend = showInLegend

        # Update the display information
        self.updateLegend()
        self.updateLabel()
        self.updateListDataPlotItem(curveId)



    def removePlotDataItem(self, curveId):
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
        If there is one dataPlotItem the ylabel is the label from the ini file.
        If many dataPlotItem, the ylabel is "[a.u]".
        """
        
        # The label is changed only of we are not display slices of a 2d plot
        if not self.linkedTo2dPlot:
            # If there is more than one plotDataItem
            # We chekc of the share the same label
            if len(np.unique(np.array([curve.curveLabel for curve in self.curves.values()])))>1:
                self.plotItem.setLabel('left',
                                        '[a.u]',
                                        color=config['pyqtgraphyLabelTextColor'])

            # If there is only one plotDataItem or if the plotDataItems share the same label
            else:
                self.plotItem.setLabel('left',
                                       self.curves[list(self.curves.keys())[0]].curveLabel,
                                       color=config['pyqtgraphyLabelTextColor'])



    def updateLegend(self):
        """
        Update the legendItem of the plotItem.
        If there is one dataPlotItem there is no legendItem.
        If many dataPlotItem, the legendItem contains the labels from the ini file.
        """
        
        if len(self.curves)==1:
            if self.linkedTo2dPlot:
                if self.legend is None:
                    self.legend = self.plotItem.addLegend()
                else:
                    # For an unknown reason we need the loop twice for windows...
                    for i, j in self.legend.items:
                        self.legend.removeItem(j.text)
                    for i, j in self.legend.items:
                        self.legend.removeItem(j.text)
            else:
                if self.legend is not None:
                    self.legend.scene().removeItem(self.legend)
                    self.legend = None
        elif len(self.curves) > 1:
            if self.legend is None:
                self.legend = self.plotItem.addLegend()
            else:

                # For an unknown reason we need the loop twice for windows...
                for i, j in self.legend.items:
                    self.legend.removeItem(j.text)
                for i, j in self.legend.items:
                    self.legend.removeItem(j.text)
        
        # If there is a displayed legendItem, we need to manually enter the info
        if self.legend is not None:
            for curve in self.curves.values():
                if curve.showInLegend:
                    self.legend.addItem(curve, curve.curveLegend)



####################################
#
#           Method to related to display
#
####################################



    def checkBoxLogState(self, b):
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



    def checkBoxSymbolState(self, b):
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



    def clickFFT(self, b):
        """
        Method called when user click on the
        """

        if b.text() == 'FFT':
            
            x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
            y = np.abs(np.fft.fft(self.selectedY))[x>=0]
            x = x[x>=0]
            text = 'fft'

        elif b.text() == 'FFT (no DC)':
            
            x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
            y = np.abs(np.fft.fft(self.selectedY))[x>=0][1:]
            x = x[x>=0][1:]
            text = 'fft'

        elif b.text() == 'IFFT':
            
            x = np.fft.fftfreq(len(self.selectedX), d=self.selectedX[1] - self.selectedX[0])
            y = np.abs(np.fft.ifft(self.selectedY))[x>=0]
            x = x[x>=0]
            text = 'ifft'

        
        self.fftwindow.append(new1dplot(x=x,
                                        y=y,
                                        title=self.windowTitle+' - '+text.upper(),
                                        xLabel='1/'+self.plotItem.axes['bottom']['item'].labelText,
                                        yLabel=text.upper()+'( '+self.selectedLabel+' )',
                                        windowTitle=self.windowTitle+' - '+text.upper(),
                                        cleanCheckBox=self.cleanCheckBox('ploploplo'),
                                        linkedTo2dPlot=False,
                                        curveId=text.upper()+'( '+self.selectedLabel+' )',
                                        curveLegend=None,
                                        parent=None))



####################################
#
#           Method to related to fit
#
####################################


    def getSelectedData(self, curveId):

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



    def selectionInifiniteLineChangeFinished(self, lineItem, curveId):
        """
        Method call when user release a dragged selection line.
        """

        # Update the style of the display plotDataItem
        self.updatePlotDataItemStyle(curveId)

        # Update data used for the fit
        self.selectedX, self.selectedY = self.getSelectedData(curveId)

        # If a fit curve is already displayed, we update it
        if 'fit' in list(self.curves.keys()):
            self.radioButtonFitState()

        # We overide a pyqtgraph attribute when user drag an infiniteLine
        lineItem.mouseHovering  = False



    def selectionInifiniteLineDragged(self, lineItem):
        """
        Method call when user drag a selection line.
        """

        # We overide a pyqtgraph attribute when user drag an infiniteLine
        lineItem.mouseHovering  = True



    def updateSelectionInifiteLine(self, curveId):
        """
        Method call when user start to fit a plotDataItem.
        Create two infiniteLine linked to the selected plotDataItem
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



    def updateListDataPlotItem(self, curveId):
        """
        Method called when a plotDataItem is added to the plotItem.
        Add a radioButton to allow user to chose the plotDataItem for fit.
        """

        # Update list of plotDataItem only if the plotDataItem is not a fit
        if curveId != 'fit':
            radioButton = QtWidgets.QRadioButton(self.curves[curveId].curveLabel)
            
            radioButton.curveId = curveId
            
            if 'selection' not in curveId:
                self.plotDataItemButtonGroup.addButton(radioButton, len(self.plotDataItemButtonGroup.buttons()))
                radioButton.clicked.connect(self.selectPlotDataItem)
                self.verticalLayoutPlotDataItem.addWidget(radioButton)



    def updatePlotDataItemStyle(self, curveId):
        """
        Modify the style of a plotDataItem.
        Use to indicate which plotDataItem is used for the fit
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



    def selectPlotDataItem(self, rb):
        """
        Method called when user clicks on a radioButton of the list of
        plotDataItem.
        The method will prepare the fit byt placing some data in memory and
        dispay to user which plotDataItem will be used for the fit.
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

            if len(self.fftwindow)>0:
                [window.close() for window in self.fftwindow]
                self.fftwindow = []

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
            



    def enableWhenPlotDataItemSelected(self, enable):
        """
        Method called when user clicks on a radioButton of the list of
        plotDataItem.
        Make enable or disable the radioButton of fitmodels.
        """

        # Enable fit 
        self.labelFit.setEnabled(enable)
        self.labelFitModel.setEnabled(enable)
        widgets = (self.verticalLayoutFitModel.itemAt(i).widget() for i in range(self.verticalLayoutFitModel.count())) 
        for w in widgets:
            w.setEnabled(enable)

        # Enable fft
        self.labelFFT.setEnabled(enable)
        self.pushButtonIFFT.setEnabled(enable)
        self.pushButtonFFT.setEnabled(enable)
        self.pushButtonFFTnoDC.setEnabled(enable)



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

            if '2d' not in j:
                
                obj = _class(self, [], [])
                rb = QtWidgets.QRadioButton(obj.checkBoxLabel())
                rb.fitModel = j
                rb.clicked.connect(self.radioButtonFitState)
                rb.setEnabled(False)
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
        self.addPlotDataItem(x = x,
                            y = y, 
                            curveId = 'fit',
                            curveLabel = self.selectedLabel,
                            curveLegend =  obj.legend2display(params))






















def new1dplot(x, y, title, xLabel, yLabel, windowTitle, cleanCheckBox,
                linkedTo2dPlot=False, curveId=None, curveLegend=None, parent=None):

    
    p = Plot1dApp(x              = x,
                  y              = y,
                  title          = title,
                  xLabel         = xLabel,
                  yLabel         = yLabel,
                  windowTitle    = windowTitle,
                  cleanCheckBox  = cleanCheckBox,
                  curveId        = curveId)

    p.show()

    return p