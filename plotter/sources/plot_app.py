# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np
import datetime
import pyqtgraph as pg

from .config import config
from ..ui.plot_widget import PlotWidget



class PlotApp(object):
    """
    Class to handle ploting in 1d.
    """


    def __init__(self) -> None:

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



    def eventFilter(self, object : PlotWidget,
                          event  : QtGui.QFocusEvent) -> bool:
        """
        Return True/False when the mouse enters/leaves by the PlotWidget.
        """
        
        if event.type()==QtCore.QEvent.Enter:
            self.widgetHovered = True
            return True
        elif event.type()==QtCore.QEvent.Leave:
            self.widgetHovered = False
        return False



    def checkBoxCrossHairState(self, b: int) -> None:
        """
        Method called when user click on the log checkBoxes.
        Modify the scale, linear or logarithmic, of the plotItem following
        which checkbox are checked.
        """
        
        if self.checkBoxCrossHair.isChecked():
            self.displayCrossHair = True
        else:
            self.displayCrossHair = False



    def isMouseOverView(self) -> bool:
        """
        Return true if mouse is over the view of the plot.
        """

        # We implement a workaround for the log mode of 1D plot.
        # See: https://github.com/pyqtgraph/pyqtgraph/issues/1470#issuecomment-864568004
        if self.plotType=='1d':
            if self.checkBoxLogX.isChecked():
                xmin = 10**self.plotItem.axes['bottom']['item'].range[0]
                xmax = 10**self.plotItem.axes['bottom']['item'].range[1]
            else:
                xmin = self.plotItem.axes['bottom']['item'].range[0]
                xmax = self.plotItem.axes['bottom']['item'].range[1]
            if self.checkBoxLogY.isChecked():
                ymin = 10**self.plotItem.axes['left']['item'].range[0]
                ymax = 10**self.plotItem.axes['left']['item'].range[1]
            else:
                ymin = self.plotItem.axes['left']['item'].range[0]
                ymax = self.plotItem.axes['left']['item'].range[1]
        else:
            xmin = self.plotItem.axes['bottom']['item'].range[0]
            xmax = self.plotItem.axes['bottom']['item'].range[1]

            ymin = self.plotItem.axes['left']['item'].range[0]
            ymax = self.plotItem.axes['left']['item'].range[1]
        
        xmax -= (xmax-xmin)/100
        ymax -= (ymax-ymin)/100
        
        if self.mousePos[0] > xmin and self.mousePos[0] < xmax \
        and self.mousePos[1] > ymin and self.mousePos[1] < ymax \
        and self.widgetHovered:
            return True
        else:
            return False



    def mouseMoved(self, pos: QtCore.QPointF) -> None:
        """
        Handle the event when the mouse move hover the plotitem.
        Basically do two things:
            Display mouse coordinates
            Draw and undraw a crosshair instead of the mouse cursor

        Parameters
        ----------
        pos : QtCore.QPointF
            Position of the mouse in the scene.
            Will be converted in View unit using mapSceneToView.
        """

        # Get mouse coordinates in "good" units
        pos = self.plotItem.vb.mapSceneToView(pos)
        
        # We implement a workaround for the log mode of 1D plot.
        # See: https://github.com/pyqtgraph/pyqtgraph/issues/1470#issuecomment-864568004
        if self.plotType=='1d':
            if self.checkBoxLogX.isChecked():
                x = 10**pos.x()
            else:
                x = pos.x()
            if self.checkBoxLogY.isChecked():
                y = 10**pos.y()
            else:
                y = pos.y()
        else:
            x = pos.x()
            y = pos.y()
        
        # Save it
        self.mousePos = x, y

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



    def setMouseCoordinate(self, blank: bool=False) -> None:
        """
        Display the mouse coodinate in respect to the plot view in the GUI.
        If the x axis is a time axis, we display coordinate in human readable
        format.
        For 1d plot we display :x, y.
        For 2d plot we display :x, y, z.

        Parameters
        ----------
        blank : bool
            If True, display an empty text, effectively erasing the previous
            entry. Used when the mouse leave the plotItem.
        """

        if blank:
            self.labelCoordinate.setText('')
        else:
            
            spaceX = ''
            spaceY = ''
            if self.mousePos[0]>0:
                spaceX = '&nbsp;'
            if self.mousePos[1]>0:
                spaceY = '&nbsp;'
            
            
            if self.plotType=='1d':

                if self.timestampXAxis:
                    x = datetime.datetime.utcfromtimestamp(self.mousePos[0]).strftime('%Y-%m-%d %H:%M:%S')
                    self.labelCoordinate.setText('x: {:}<br/>y: {}{:.{nbDecimal}e}'.format(spaceX, x, spaceY, self.mousePos[1], nbDecimal=config['plotCoordinateNbNumber']))
                else:
                    self.labelCoordinate.setText('x: {}{:.{nbDecimal}e}<br/>y: {}{:.{nbDecimal}e}'.format(spaceX, self.mousePos[0],spaceY, self.mousePos[1], nbDecimal=config['plotCoordinateNbNumber']))
            elif self.plotType=='2d':

                n = np.abs(self.xData-self.mousePos[0]).argmin()
                m = np.abs(self.yData-self.mousePos[1]).argmin()
                z = self.zData[n,m]
                
                spaceZ = ''
                if z>0:
                    spaceZ = '&nbsp;'

                self.labelCoordinate.setText('x: {}{:.{nbDecimal}e}<br/>y: {}{:.{nbDecimal}e}<br/>z: {}{:.{nbDecimal}e}'.format(spaceX, self.mousePos[0], spaceY, self.mousePos[1], spaceZ, z, nbDecimal=config['plotCoordinateNbNumber']))
            else:
                raise ValueError('plotType unknown')



    def infiniteLineHovering(self, defaultCursor: QtCore.Qt.CursorShape=QtCore.Qt.ArrowCursor) -> None:
        """
        Called when user cursor if hovering a infiniteLine.

        Parameters
        ----------
        defaultCursor : QtCore.Qt.CursorShape, default QtCore.Qt.ArrowCursor
            Cursor to put back when the mouse leave an infiniteLine.
        """

        # If we are hovering at least one infiniteLine, the cursor is modified
        for line in list(self.infiniteLines.values()):
            if line.mouseHovering:
                defaultCursor = QtCore.Qt.PointingHandCursor

        
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(defaultCursor))



    def crossHair(self, remove        : bool=False,
                        defaultCursor : QtCore.Qt.CursorShape=QtCore.Qt.ArrowCursor) -> None:
        """
        Handle the crossHair draw on the viewbox.

        Parameters
        ----------
        remove : bool, default False
            If the crossHair should be removed.
        defaultCursor : QtCore.Qt.CursorShape, default QtCore.Qt.ArrowCursor
            Cursor to put back when the crosshair is removed.
        """

        # if the plot is a 2dplot, there is a possibility that the user mouse is
        # above an infiniteLine, if so, we remove the crosshair
        if self.plotType=='2d':
            for line in list(self.infiniteLines.values()):
                if line.mouseHovering:
                    remove = True

        # If 'vline' is None it means the crosshair hasn't been created
        if not remove and self.vLine is None:
            # Build the crosshair style

            if config['crossHairLineStyle']=='solid':
                lineStyle = QtCore.Qt.SolidLine 
            elif config['crossHairLineStyle']=='dashed':
                lineStyle = QtCore.Qt.DashLine  
            elif config['crossHairLineStyle']=='dotted':
                lineStyle = QtCore.Qt.DotLine  
            elif config['crossHairLineStyle']=='dashed-dotted':
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

            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
            
        # If the crosshair exist, and we want to remove it
        elif remove and self.vLine is not None:

            self.plotItem.removeItem(self.vLine)
            self.plotItem.removeItem(self.hLine)
            self.vLine = None
            self.hLine = None

            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(defaultCursor))
            

        # Otherwise, we update its position
        elif self.vLine is not None:

            self.vLine.setPos(self.mousePos[0])
            self.hLine.setPos(self.mousePos[1])
