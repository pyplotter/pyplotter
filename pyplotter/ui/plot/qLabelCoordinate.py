from PyQt5 import QtCore, QtWidgets
import datetime
import numpy as np
from typing import TYPE_CHECKING

from ...sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ...sources.pyqtgraph import pg

if TYPE_CHECKING:
    from .widgetPlotContainer import WidgetPlotContainer



class QLabelCoordinate(QtWidgets.QLabel):


    def __init__(self, parent: 'WidgetPlotContainer') -> None:
        """
        QLabel displaying the coordinate of the mouse in respect to the plotItem.
        Show: x, y or x, y, z depending on the plotItemp plotType.

        The label is displayed on top of the plotWidget1d or plotWidget2d.
        Its parent is widgetPlotContainer and it is placed on top-right of
        widgetPlotContainer
        """

        super(QLabelCoordinate, self).__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        # Shortcut
        self.widget = parent.parent()



    @QtCore.pyqtSlot()
    def slotPlaceLabel(self):
        self.placeLabel()


    def placeLabel(self):
        # Effectively move the coordinate label at the top-right of the

        self.adjustSize()
        self.move(self.parent().width()-self.width(), 0)



    @QtCore.pyqtSlot(float, float, bool)
    def slotUpdateCoordinate(self, x: float,
                                   y: float,
                                   blank: bool) -> None:
        """
        Called from plotWidget

        Display the mouse coodinate in respect to the plot view in the GUI.
        If the x axis is a time axis, we display coordinate in human readable
        format.
        For 1d plot we display :x, y.
        For 2d plot we display :x, y, z.

        Parameters
        ----------
        x : float
            Cursor position along the x axis
        y : float
            Cursor position along the y axis
        blank : bool
            If True, display an empty text, effectively erasing the previous
            entry. Used when the mouse leave the plotItem.
        """
        if blank:
            self.setText('')
        else:

            spaceX = ''
            spaceY = ''
            if x>0:
                spaceX = '&nbsp;'
            if y>0:
                spaceY = '&nbsp;'


            if self.widget.plotType=='1d':

                if isinstance(self.widget.plotItem.getAxis('bottom'), pg.DateAxisItem):
                    x = datetime.datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S')
                    self.setText('x: {:}<br/>y: {}{:.{nbDecimal}e}'.format(x, spaceY, y, nbDecimal=config['plotCoordinateNbNumber']))
                else:
                    # print(self)
                    # print('x: {}{:.{nbDecimal}e}<br/>y: {}{:.{nbDecimal}e}'.format(spaceX, x,spaceY, y, nbDecimal=config['plotCoordinateNbNumber']))
                    # self.setText('lol')
                    self.setText('x: {}{:.{nbDecimal}e}<br/>y: {}{:.{nbDecimal}e}'.format(spaceX, x,spaceY, y, nbDecimal=config['plotCoordinateNbNumber']))
            elif self.widget.plotType=='2d':

                n = np.abs(self.widget.xData-x).argmin()
                m = np.abs(self.widget.yData-y).argmin()
                z = self.widget.zData[n,m]

                spaceZ = ''
                if z>0:
                    spaceZ = '&nbsp;'

                self.setText('x: {}{:.{nbDecimal}e} z: {}{:.{nbDecimal}e}<br/>y: {}{:.{nbDecimal}e}<br/>'.format(spaceX, x, spaceY, y, spaceZ, z, nbDecimal=config['plotCoordinateNbNumber']))
            else:
                raise ValueError('plotType unknown')

        self.placeLabel()