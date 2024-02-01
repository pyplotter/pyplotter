from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np
from typing import Callable, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .plot1d.widgetPlot1d import WidgetPlot1d
    from .plot2d.widgetPlot2d import WidgetPlot2d

from ...sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..menuDb import MenuDb
from ...sources.pyqtgraph import pg



class QCheckBoxCrossHair(QtWidgets.QCheckBox):

    signalAddCrossHair = QtCore.pyqtSignal(bool)



    def __init__(self, parent=None):

        super(QCheckBoxCrossHair, self).__init__(parent)

        # # Crosshair lines
        # self.vLine = None
        # self.hLine = None

        # Help deciding when drawing crosshair
        # self.installEventFilter(self)
        # self.plotWidgetHovered = False
        # self.displayCrossHair = False


        # Shortcut
        # self.widget = parent.parent()

        self.clicked.connect(self.clicked_)


    def clicked_(self):

        self.signalAddCrossHair.emit(self.isChecked())


    # def checkBoxCrossHairState(self, b: int) -> None:
    #     """
    #     Method called when user click on the log checkBoxes.
    #     Modify the scale, linear or logarithmic, of the plotItem following
    #     which checkbox are checked.
    #     """

    #     if self.widget.checkBoxCrossHair.isChecked():
    #         self.displayCrossHair = True
    #     else:
    #         self.displayCrossHair = False


    # def checkBoxClicked(self, plotWidget: Union['WidgetPlot1d', 'WidgetPlot2d'],
    #                           defaultCursor : QtCore.Qt.CursorShape=QtCore.Qt.ArrowCursor) -> None:
    #     """
    #     Handle the crossHair draw on the viewbox.

    #     Parameters
    #     ----------
    #     remove : bool, default False
    #         If the crossHair should be removed.
    #     defaultCursor : QtCore.Qt.CursorShape, default QtCore.Qt.ArrowCursor
    #         Cursor to put back when the crosshair is removed.
    #     """

    #     # if the plot is a 2dplot, there is a possibility that the user mouse is
    #     # above an infiniteLine, if so, we remove the crosshair
    #     if plotWidget.plotType=='2d':
    #         for line in list(plotWidget.sliceItems.values()):
    #             if line.mouseHovering:
    #                 remove = True

    #     # If 'vline' is None it means the crosshair hasn't been created
    #     if self.vLine is None:

    #         # Build the crosshair style
    #         if config['crossHairLineStyle']=='solid':
    #             lineStyle = QtCore.Qt.SolidLine
    #         elif config['crossHairLineStyle']=='dashed':
    #             lineStyle = QtCore.Qt.DashLine
    #         elif config['crossHairLineStyle']=='dotted':
    #             lineStyle = QtCore.Qt.DotLine
    #         elif config['crossHairLineStyle']=='dashed-dotted':
    #             lineStyle = QtCore.Qt.DashDotLine
    #         else:
    #             raise ValueError('Config parameter "crossHairLineStyle" not recognize')


    #         penInfLine = pg.mkPen(config['crossHairLineColor'],
    #                               width=config['crossHairLineWidth'],
    #                               style=lineStyle)

    #         vLine = pg.InfiniteLine(angle=90, movable=False, pen=penInfLine)
    #         hLine = pg.InfiniteLine(angle=0,  movable=False, pen=penInfLine)
    #         plotWidget.plotItem.addItem(vLine, ignoreBounds=True)
    #         plotWidget.plotItem.addItem(hLine, ignoreBounds=True)
    #         self.vLine = vLine
    #         self.hLine = hLine

    #         QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))

    #     # If the crosshair exist, and we want to remove it
    #     elif remove and self.vLine is not None:

    #         plotWidget.plotItem.removeItem(self.vLine)
    #         plotWidget.plotItem.removeItem(self.hLine)
    #         self.vLine = None
    #         self.hLine = None

    #         QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(defaultCursor))



    # @QtCore.pyqtSlot(float, float)
    # def slotUpdateCrossHairPosition(self, x: float,
    #                                       y: float) -> None:


    #     if self.vLine is not None:

    #         self.vLine.setPos(self.mousePos[0])
    #         self.hLine.setPos(self.mousePos[1])
