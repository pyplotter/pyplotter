from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np
from typing import Callable, Optional

from ...sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..menuDb import MenuDb
from ...sources.pyqtgraph import pg



class WidgetPlot(pg.PlotWidget):
    """
    Custom class used in QtDesigner.
    Allow its parent class to use plotWidget
    """


    signalUpdateCoordinate = QtCore.pyqtSignal(float, float, bool)
    signalUpdateCrossHairPosition = QtCore.pyqtSignal(float, float)



    def __init__(self, parent=None):
        # pg.PlotWidget.__init__(self)
        super(WidgetPlot, self).__init__()
        self.setParent(parent)

        # Shortcut
        self.plotItem = self.getPlotItem()

        self.installEventFilter(self)
        self.plotWidgetHovered = False


        # Help deciding when drawing crosshair
        # Is switched from a signal emited by qCheckBoxCrossHair
        self.displayCrossHair = False

        ## Crosshair lines
        self.vLine = None
        self.hLine = None

        self.plotItem.titleLabel.setToolTip('Right click for options')

        # Connect signal
        self.plotItem.titleLabel.mousePressEvent = self.clickTitle
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)



    ####################################
    #
    #           Easy access to plot labels
    #
    ####################################

    @property
    def xLabelText(self) -> str:
        return self.plotItem.axes['bottom']['item'].labelText

    @property
    def xLabelUnits(self) -> str:
        return self.plotItem.axes['bottom']['item'].labelUnits

    @property
    def yLabelText(self) -> str:
        return self.plotItem.axes['left']['item'].labelText

    @property
    def yLabelUnits(self) -> str:
        return self.plotItem.axes['left']['item'].labelUnits



    ####################################
    #
    #           Method related to style
    #
    ####################################


    def updateStyle(self) -> None:

        for qlabel in self.findChildren(QtWidgets.QLabel)+self.findChildren(QtWidgets.QCheckBox)+self.findChildren(QtWidgets.QGroupBox):
            qlabel.setStyleSheet("background-color: "+str(self.parent().parent().config['styles'][self.parent().parent().config['style']]['dialogBackgroundColor'])+";")
            qlabel.setStyleSheet("color: "+str(self.parent().parent().config['styles'][self.parent().parent().config['style']]['dialogTextColor'])+";")

        self.plotItem.getAxis('bottom')._updateLabel()
        font=QtGui.QFont()
        font.setPixelSize(self.parent().parent().config['tickLabelFontSize'])
        self.plotItem.getAxis('bottom').setTickFont(font)
        self.plotItem.getAxis('left').setTickFont(font)
        self.plotItem.getAxis('bottom').setPen(self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphxAxisTicksColor'])
        self.plotItem.getAxis('left').setPen(self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphyAxisTicksColor'])
        self.plotItem.getAxis('bottom').setTextPen(self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphxAxisTickLabelsColor'])
        self.plotItem.getAxis('left').setTextPen(self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphyAxisTickLabelsColor'])

        if self.parent().parent().plotType=='2d':
            self.parent().parent().ui.plot2dzLabel.setFont(font)
            self.parent().parent().ui.histWidget.axis.setTickFont(font)

        self.plotItem.setTitle(title=self.plotItem.titleLabel.text,
                               color=self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphTitleTextColor'])

        self.plotItem.setLabel(axis='bottom',
                               text=self.xLabelText,
                               units=self.xLabelUnits,
                               **{'color'     : self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphxLabelTextColor'],
                                  'font-size' : str(self.parent().parent().config['axisLabelFontSize'])+'pt'})
        self.plotItem.setLabel(axis='left',
                               text=self.yLabelText,
                               units=self.yLabelUnits,
                               **{'color'     : self.parent().parent().config['styles'][self.parent().parent().config['style']]['pyqtgraphyLabelTextColor'],
                                  'font-size' : str(self.parent().parent().config['axisLabelFontSize'])+'pt'})

        # Update colormap
        if self.parent().parent().plotType=='2d':
            index = self.parent().parent().ui.comboBoxcm.findText(self.parent().parent().config['plot2dcm'])
            self.parent().parent().ui.comboBoxcm.setCurrentIndex(index)


    ####################################
    #
    #           Method related to the title
    #
    ####################################


    def clickTitle(self, b: QtWidgets.QGraphicsSceneMouseEvent) -> None:

        # We open a homemade menu
        if b.button()==2:
            MenuDb(self.parent().parent().databaseAbsPath)



    def eventFilter(self, object,
                          event  : QtGui.QFocusEvent) -> bool:
        """
        Return True/False when the mouse enters/leaves by the PlotWidget.
        """

        if event.type()==QtCore.QEvent.Enter:
            self.plotWidgetHovered = True
            return True
        elif event.type()==QtCore.QEvent.Leave:
            self.plotWidgetHovered = False
        return False



    def isMouseOverView(self) -> bool:
        """
        Return true if mouse is over the view of the plot.
        """

        # We implement a workaround for the log mode of 1D plot.
        # See: https://github.com/pyqtgraph/pyqtgraph/issues/1470#issuecomment-864568004
        if self.parent().parent().plotType=='1d':
            if self.parent().parent().ui.checkBoxLogX.isChecked():
                xmin = 10**self.plotItem.axes['bottom']['item'].range[0]
                xmax = 10**self.plotItem.axes['bottom']['item'].range[1]
            else:
                xmin = self.plotItem.axes['bottom']['item'].range[0]
                xmax = self.plotItem.axes['bottom']['item'].range[1]
            if self.parent().parent().ui.checkBoxLogY.isChecked():
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
        and self.plotWidgetHovered:
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
        if self.parent().parent().plotType=='1d':
            if self.parent().parent().ui.checkBoxLogX.isChecked():
                x = 10**pos.x()
            else:
                x = pos.x()
            if self.parent().parent().ui.checkBoxLogY.isChecked():
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
            self.signalUpdateCoordinate.emit(x, y, False)

            # Update cursor when hovering infiniteLine
            self.sliceItemHovering()

            # Display the "crosshair"
            if self.displayCrossHair:
                self.crossHair()
        else:
            self.signalUpdateCoordinate.emit(x, y, True)

            if self.displayCrossHair:
                self.crossHair(remove=True)



    def sliceItemHovering(self, defaultCursor: QtCore.Qt.CursorShape=QtCore.Qt.ArrowCursor) -> None:
        """
        Called when user cursor if hovering a sliceItem.

        Parameters
        ----------
        defaultCursor : QtCore.Qt.CursorShape, default QtCore.Qt.ArrowCursor
            Cursor to put back when the mouse leave an sliceItem.
        """

        # If we are hovering at least one sliceItem, the cursor is modified
        for line in list(self.parent().parent().sliceItems.values()):
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
        if self.parent().parent().plotType=='2d':
            for line in list(self.parent().parent().sliceItems.values()):
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

        # If the crosshair exist, and we want to remove it
        elif remove and self.vLine is not None:

            self.plotItem.removeItem(self.vLine)
            self.plotItem.removeItem(self.hLine)
            self.vLine = None
            self.hLine = None


        # Otherwise, we update its position
        elif self.vLine is not None:

            self.vLine.setPos(self.mousePos[0])
            self.hLine.setPos(self.mousePos[1])


    @QtCore.pyqtSlot(bool)
    def slotAddCrossHair(self, addCrossHair: bool) -> None:

        self.displayCrossHair = addCrossHair