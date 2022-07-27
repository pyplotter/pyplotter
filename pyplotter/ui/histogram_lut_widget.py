# This Python file uses the following encoding: utf-8
from..sources.pyqtgraph import pg

class HistogramLUTWidget(pg.HistogramLUTWidget):
    """
    Custom class used in QtDesigner.
    Allow its parent class to use HistogramLUTWidget
    """

    def __init__(self, parent=None, **kargs):

        pg.HistogramLUTWidget.__init__(self, **kargs)
        self.setParent(parent)