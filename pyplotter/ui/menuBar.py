# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any
import os

from ..sources.config import loadConfigCurrent, updateUserConfig
config = loadConfigCurrent()

from ..sources.dialogs.dialogFontsize import MenuDialogFontSize
from ..sources.dialogs.dialogColormap import DialogMenuColormap


class MenuBar(QtWidgets.QMenuBar):

    signalUpdateStyle        = QtCore.pyqtSignal(dict)
    signalOpenDialogLivePlot = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[Any]=None) -> None:
        super(MenuBar, self).__init__(parent)


        self.menuPreferences = self.addMenu('Preferences')

        self.menuStyle = self.menuPreferences.addMenu('Style')
        self.actionqb = self.menuStyle.addAction('qb')
        self.actionqdark = self.menuStyle.addAction('qdark')
        self.actionwhite = self.menuStyle.addAction('white')
        self.actionDefaultPath = self.menuPreferences.addAction('Select default folder')
        # self.menuPreferences.addAction(self.menuStyle.menuAction())

        self.menuPlot = self.menuPreferences.addMenu('Plot')
        self.actionAxisLabelColor = self.menuPlot.addAction('Axis label color')
        self.actionAxisTickLabelsColor = self.menuPlot.addAction('Axis tickLabels color')
        self.actionAxisTicksColor = self.menuPlot.addAction('Axis ticks color')
        self.actionTitleColor = self.menuPlot.addAction('Title color')
        self.actionFontsize = self.menuPlot.addAction('Fontsize')
        self.actionColormap = self.menuPlot.addAction('Colormap')
        self.menuPreferences.addAction(self.menuPlot.menuAction())

        self.menuLiveplot    = self.addMenu('Liveplot')
        self.actionOpenliveplot = self.menuLiveplot.addAction('Open liveplot')

        self.actionqb.triggered.connect(self.menuBackgroundQb)
        self.actionqdark.triggered.connect(self.menuBackgroundQdark)
        self.actionwhite.triggered.connect(self.menuBackgroundWhite)
        self.actionDefaultPath.triggered.connect(self.menuDefaultPath)
        self.actionAxisLabelColor.triggered.connect(self.menuAxisLabelColor)
        self.actionAxisTickLabelsColor.triggered.connect(self.menuAxisTickLabelsColor)
        self.actionAxisTicksColor.triggered.connect(self.menuAxisTicksColor)
        self.actionTitleColor.triggered.connect(self.menuTitleColor)
        self.actionFontsize.triggered.connect(self.menuFontsize)
        self.actionColormap.triggered.connect(self.menuColormap)
        self.actionOpenliveplot.triggered.connect(self.menuOpenLiveplot)

        if config['style']=='qbstyles':
            self.actionqb.setChecked(True)
            self.actionqb.setEnabled(False)
        elif config['style']=='qdarkstyle':
            self.actionqdark.setChecked(True)
            self.actionqdark.setEnabled(False)
        elif config['style']=='white':
            self.actionwhite.setChecked(True)
            self.actionwhite.setEnabled(False)



    def menuBackgroundQb(self, checked):

        self.actionqb.setChecked(True)
        self.actionqdark.setChecked(False)
        self.actionwhite.setChecked(False)

        self.actionqb.setEnabled(False)
        self.actionqdark.setEnabled(True)
        self.actionwhite.setEnabled(True)

        config['style'] = 'qbstyles'

        self.updateStyle(config)
        updateUserConfig('style', 'qbstyles')



    def menuBackgroundQdark(self, checked):

        self.actionqb.setChecked(False)
        self.actionqdark.setChecked(True)
        self.actionwhite.setChecked(False)

        self.actionqb.setEnabled(True)
        self.actionqdark.setEnabled(False)
        self.actionwhite.setEnabled(True)

        config['style'] = 'qdarkstyle'

        self.updateStyle(config)
        updateUserConfig('style', 'qdarkstyle')



    def menuBackgroundWhite(self, checked):

        self.actionqb.setChecked(False)
        self.actionqdark.setChecked(False)
        self.actionwhite.setChecked(True)

        self.actionqb.setEnabled(True)
        self.actionqdark.setEnabled(True)
        self.actionwhite.setEnabled(False)

        config['style'] = 'white'

        self.updateStyle(config)
        updateUserConfig('style', 'white')



    def menuDefaultPath(self):

        # Ask user to chose a path
        path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                          caption='Open folder',
                                                          directory=os.getcwd(),
                                                          options=QtWidgets.QFileDialog.ReadOnly|QtWidgets.QFileDialog.ShowDirsOnly)
        if path != '':

            updateUserConfig('path', os.path.abspath(path))
            updateUserConfig('root', os.path.splitdrive(path)[0])



    def menuAxisLabelColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            for label in ('pyqtgraphxLabelTextColor',
                          'pyqtgraphyLabelTextColor',
                          'pyqtgraphzLabelTextColor'):
                config['styles'][config['style']][label] = color.name()
                updateUserConfig(['styles', config['style'], label], color.name())

            self.updateStyle(config)



    def menuAxisTicksColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            for axis in ('pyqtgraphxAxisTicksColor',
                         'pyqtgraphyAxisTicksColor',
                         'pyqtgraphzAxisTicksColor'):
                config['styles'][config['style']][axis] = color.name()
                updateUserConfig(['styles', config['style'], axis], color.name())

            self.updateStyle(config)


    def menuAxisTickLabelsColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            for axis in ('pyqtgraphxAxisTickLabelsColor',
                         'pyqtgraphyAxisTickLabelsColor',
                         'pyqtgraphzAxisTickLabelsColor'):
                config['styles'][config['style']][axis] = color.name()
                updateUserConfig(['styles', config['style'], axis], color.name())

            self.updateStyle(config)



    def menuTitleColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            config['styles'][config['style']]['pyqtgraphTitleTextColor'] = color.name()
            updateUserConfig(['styles', config['style'], 'pyqtgraphTitleTextColor'], color.name())

            self.updateStyle(config)



    def menuFontsize(self):

        self.menuDialogFontSize = MenuDialogFontSize(config)
        self.menuDialogFontSize.signalUpdateStyle.connect(self.updateStyle)



    def menuColormap(self):

        self.DialogMenuColormap = DialogMenuColormap(config)
        self.DialogMenuColormap.signalUpdateStyle.connect(self.updateStyle)



    def menuOpenLiveplot(self):

        self.signalOpenDialogLivePlot.emit()


    QtCore.pyqtSlot(dict)
    def updateStyle(self, config: dict) -> None:

        self.signalUpdateStyle.emit(config)
