from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np
from typing import Callable, Optional

from ...sources.config import loadConfigCurrent
config = loadConfigCurrent()
# from ..plotWidget import PlotWidget
# from ..plot2d.histogramLUTWidget import HistogramLUTWidget
from ..menuDb import MenuDb
from .widgetPlot import WidgetPlot
from .qLabelCoordinate import QLabelCoordinate
from .qButtonInteration import QButtonInteraction
from ...sources.pyqtgraph import pg

class WidgetPlotContainer(QtWidgets.QWidget):


    signalResize = QtCore.pyqtSignal()


    def __init__(self, parent: QtWidgets.QDialog) -> None:
        """
        Widget use as a container to stack several widgets on top of each others.

        Widget containing
            plotWidget
            QLabelCoordinate
            QButtonInteraction
        """


        super(WidgetPlotContainer, self).__init__(parent)

        # Build the UI so that WidgetPlotContainer take all possible space in its
        # parent
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        # Same here, we want WidgetPlot to take all possible space in WidgetPlotContainer
        self.plotWidget = WidgetPlot(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotWidget.sizePolicy().hasHeightForWidth())
        self.plotWidget.setSizePolicy(sizePolicy)


        self.hLayout = QtWidgets.QHBoxLayout(self)
        self.hLayout.addWidget(self.plotWidget)

        parent.ui.horizontalLayout.addWidget(self)



        # We add a custom label to display the coordinate
        self.labelCoordinate = QLabelCoordinate(self)
        self.plotWidget.signalUpdateCoordinate.connect(self.labelCoordinate.slotUpdateCoordinate)
        self.signalResize.connect(self.labelCoordinate.slotPlaceLabel)


        # We add a custom button to hide or show the interaction tab
        self.buttonInteraction = QButtonInteraction(self)





    def resizeEvent(self, event):

        self.signalResize.emit()