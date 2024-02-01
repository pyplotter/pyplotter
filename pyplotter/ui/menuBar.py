from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any
import os
import numpy as np

from ..sources.config import loadConfigCurrent, updateUserConfig
config = loadConfigCurrent()

from .dialogs.dialogFontsize import DialogFontSize
from .dialogs.dialogColormap import DialogMenuColormap
from .dialogs.dialogLiveplot import DialogLiveplot
from .dialogs.dialogMenuDatabaseDisplay import DialogMenuDatabaseDisplay


class MenuBar(QtWidgets.QMenuBar):

    signalUpdateStyle               = QtCore.pyqtSignal(dict)
    signalUpdateTableWidgetDatabase = QtCore.pyqtSignal(dict)


    ## Propagate signal from the livePlot dialog window to the mainWindow
    signalAddLivePlot        = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str, int, int, int, int)
    signalUpdate1d           = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
    signalUpdate2d           = QtCore.pyqtSignal(str, np.ndarray, np.ndarray, np.ndarray)
    signalUpdatePlotProperty = QtCore.pyqtSignal(str, str, str)



    def __init__(self, parent: Optional[Any]=None) -> None:
        super(MenuBar, self).__init__(parent)


        self.menuPreferences = self.addMenu('Preferences')

        self.menuStyle = self.menuPreferences.addMenu('Style')
        self.actionqb = self.menuStyle.addAction('qb')
        self.actionqdark = self.menuStyle.addAction('qdark')
        self.actionwhite = self.menuStyle.addAction('white')
        self.actionDefaultPath = self.menuPreferences.addAction('Select default folder')

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

        self.actionDatabase = self.menuPreferences.addAction('Database display')

        self.actionqb.triggered.connect(self.menuBackgroundQb)
        self.actionqdark.triggered.connect(self.menuBackgroundQdark)
        self.actionwhite.triggered.connect(self.menuBackgroundWhite)
        self.actionDefaultPath.triggered.connect(self.menuDefaultPath)
        self.actionDatabase.triggered.connect(self.menuDatabase)
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

        self.signalUpdateStyle.emit(config)
        updateUserConfig('style', 'qbstyles')



    def menuBackgroundQdark(self, checked):

        self.actionqb.setChecked(False)
        self.actionqdark.setChecked(True)
        self.actionwhite.setChecked(False)

        self.actionqb.setEnabled(True)
        self.actionqdark.setEnabled(False)
        self.actionwhite.setEnabled(True)

        config['style'] = 'qdarkstyle'

        self.signalUpdateStyle.emit(config)
        updateUserConfig('style', 'qdarkstyle')



    def menuBackgroundWhite(self, checked):

        self.actionqb.setChecked(False)
        self.actionqdark.setChecked(False)
        self.actionwhite.setChecked(True)

        self.actionqb.setEnabled(True)
        self.actionqdark.setEnabled(True)
        self.actionwhite.setEnabled(False)

        config['style'] = 'white'

        self.signalUpdateStyle.emit(config)
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



    def menuDatabase(self):

        self.dialogMenuDatabaseDisplay = DialogMenuDatabaseDisplay(self.parent(), config)
        self.dialogMenuDatabaseDisplay.signalUpdateTableWidgetDatabase.connect(self.signalUpdateTableWidgetDatabase.emit)
        self.dialogMenuDatabaseDisplay.signalUpdateStyle.connect(self.signalUpdateStyle.emit)



    def menuAxisLabelColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            for label in ('pyqtgraphxLabelTextColor',
                          'pyqtgraphyLabelTextColor',
                          'pyqtgraphzLabelTextColor'):
                config['styles'][config['style']][label] = color.name()
                updateUserConfig(['styles', config['style'], label], color.name())

            self.signalUpdateStyle.emit(config)



    def menuAxisTicksColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            for axis in ('pyqtgraphxAxisTicksColor',
                         'pyqtgraphyAxisTicksColor',
                         'pyqtgraphzAxisTicksColor'):
                config['styles'][config['style']][axis] = color.name()
                updateUserConfig(['styles', config['style'], axis], color.name())

            self.signalUpdateStyle.emit(config)


    def menuAxisTickLabelsColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            for axis in ('pyqtgraphxAxisTickLabelsColor',
                         'pyqtgraphyAxisTickLabelsColor',
                         'pyqtgraphzAxisTickLabelsColor'):
                config['styles'][config['style']][axis] = color.name()
                updateUserConfig(['styles', config['style'], axis], color.name())

            self.signalUpdateStyle.emit(config)



    def menuTitleColor(self):

        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():

            config['styles'][config['style']]['pyqtgraphTitleTextColor'] = color.name()
            updateUserConfig(['styles', config['style'], 'pyqtgraphTitleTextColor'], color.name())

            self.signalUpdateStyle.emit(config)



    def menuFontsize(self):

        self.dialogFontSize = DialogFontSize(self.parent(), config)
        self.dialogFontSize.signalUpdateStyle.connect(self.signalUpdateStyle.emit)



    def menuColormap(self):

        self.dialogMenuColormap = DialogMenuColormap(self.parent(), config)
        self.dialogMenuColormap.signalUpdateStyle.connect(self.signalUpdateStyle.emit)



    def menuOpenLiveplot(self):

        self.dialogLiveplot = DialogLiveplot(config)

        self.dialogLiveplot.signalAddLivePlot.connect(self.signalAddLivePlot.emit)
        self.dialogLiveplot.signalUpdate1d.connect(self.signalUpdate1d.emit)
        self.dialogLiveplot.signalUpdate2d.connect(self.signalUpdate2d.emit)
        self.dialogLiveplot.signalUpdatePlotProperty.connect(self.signalUpdatePlotProperty.emit)



    QtCore.pyqtSlot(dict)
    def updateStyle(self, config: dict) -> None:

        self.signalUpdateStyle.emit(config)
