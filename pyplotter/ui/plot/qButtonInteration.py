from PyQt5 import QtCore, QtGui, QtWidgets
from typing import TYPE_CHECKING

from ...sources.config import loadConfigCurrent
config = loadConfigCurrent()

if TYPE_CHECKING:
    from .widgetPlotContainer import WidgetPlot


class QButtonInteraction(QtWidgets.QPushButton):


    def __init__(self, parent: "WidgetPlot") -> None:
        """
        """

        super(QButtonInteraction, self).__init__(parent)

        self.setToolTip('Click to close or open the interaction panel')
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        font.setPointSize(10)
        self.setFont(font)
        self.setText('⯇')
        self.resize(20, 20)


        # Shortcut
        self.tabWidget = parent.parent().ui.tabWidget

        self.clicked.connect(self.clicked_)

        if config['plotHideInteractionPanel']:
            self.clicked_()

    def clicked_(self):

        # First time the user click on the button
        # We create the animation
        if not hasattr(self, 'animGroup'):
            self.animGroup = QtCore.QParallelAnimationGroup(self)

            self.animMinWidth = QtCore.QPropertyAnimation(self.tabWidget, b'minimumWidth', self)
            self.animMaxWidth = QtCore.QPropertyAnimation(self.tabWidget, b'maximumWidth', self)

            self.animMinWidth.setDuration(350)
            self.animMinWidth.setEasingCurve(QtCore.QEasingCurve.InOutCubic)

            self.animMaxWidth.setDuration(350)
            self.animMaxWidth.setEasingCurve(QtCore.QEasingCurve.InOutCubic)


            self.animGroup.addAnimation(self.animMinWidth)
            self.animGroup.addAnimation(self.animMaxWidth)

            self.animGroup.finished.connect(self.animationFinished)

        # When we want to expand the tabWidget
        if self.tabWidget.width()==0:
            self.animMinWidth.setStartValue(0)
            self.animMinWidth.setEndValue(self._width)

            self.animMaxWidth.setStartValue(0)
            self.animMaxWidth.setEndValue(self._width)

        # When we want to contract the tabWidget
        else:
            self._width = self.tabWidget.width()
            self.animMinWidth.setStartValue(self._width)
            self.animMinWidth.setEndValue(0)

            self.animMaxWidth.setStartValue(self._width)
            self.animMaxWidth.setEndValue(0)

        self.animGroup.start()



    def animationFinished(self):

        if self.tabWidget.width()==0:
            self.setText('⯈')
        else:
            self.setText('⯇')
