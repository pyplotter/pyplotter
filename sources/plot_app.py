# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import pyqtgraph as pg
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
                self.labelCoordinate.setText('x : {:.3f}, y : {:.3f}'.format(self.mousePos[0], self.mousePos[1]))
            elif self.plotType == '2d':

                n = np.abs(self.x-self.mousePos[0]).argmin()
                m = np.abs(self.y-self.mousePos[1]).argmin()
                z = self.z[n,m]

                self.labelCoordinate.setText('x : {:.3f}, y : {:.3f}, z : {:.3f}'.format(self.mousePos[0], self.mousePos[1], z))
            else:
                raise ValueError('plotType unknown')



    def infiniteLineHovering(self, defaultCursor=QtCore.Qt.ArrowCursor):
        """
        Called when user cursor if hovering a infiniteLine
        """


        # If we are hovering at least one inifiteLine, the cursor is modified
        for line in self.infiniteLines.itervalues():
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
            for line in self.infiniteLines.itervalues():
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
