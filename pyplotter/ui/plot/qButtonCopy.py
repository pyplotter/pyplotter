from PyQt5 import QtCore, QtWidgets
from typing import Union

from ...sources.pyqtgraph import pg

class QButtonCopy(QtWidgets.QPushButton):

    def __init__(self, parent: QtWidgets.QGroupBox) -> None:
        """
        """

        super(QButtonCopy, self).__init__(parent)

        self._text = 'Copie figure to clipboard 📋'
        self.setText(self._text)


    ####################################
    #
    #           Copie plot to clipboard
    #
    ####################################



    def clicked_(self, plotWidget: pg.PlotWidget) -> None:
        """
        Called when user click on the qButtonCopy.
        Place a screenshot of the plotWidget in the clipboard.
        The event connection is done in the WidgetPlot1d and WidgetPlot2d to get
        the plotWidget reference.

        Args:
            plotWidget: Widget we want a screenshot of.
        """

        screen    = QtWidgets.QApplication.primaryScreen()
        clipboard = QtWidgets.QApplication.clipboard()

        # For 2d plot, we want the colormap
        if hasattr(plotWidget.parent, 'hist'):
            witdh = plotWidget.frameGeometry().width()\
                   +plotWidget.parent.hist.width()
        else:
            witdh = plotWidget.frameGeometry().width()

        pixmap = screen.grabWindow(plotWidget.winId(),
                                   x=0,
                                   y=0,
                                   width=witdh,
                                   height=plotWidget.frameGeometry().height())
        clipboard.setPixmap(pixmap)

        self.setText('Copied to clipboard !')

        self._clipboardTimer = QtCore.QTimer()
        self._clipboardTimer.timeout.connect(self.updateButton)
        self._clipboardTimer.setInterval(2000)
        self._clipboardTimer.start()



    def updateButton(self):
        """
        Called 2s after the user click on the pushButtonCopy.
        Update its text and delete the timer
        """

        self.setText(self._text)
        self._clipboardTimer.stop()
        self._clipboardTimer.deleteLater()
        self._clipboardTimer = None
