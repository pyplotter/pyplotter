# This Python file uses the following encoding: utf-8
import pyqtgraph as pg

class PlotWidget(pg.PlotWidget):
    """
    Custom class used in QtDesigner.
    Allow its parent class to use plotWidget
    """

    def __init__(self, parent=None, **kargs):

        pg.PlotWidget.__init__(self, **kargs)
        self.setParent(parent)