# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
import numpy as np
from typing import List

from .widgetTabCurveUi import Ui_widgetTabCurve
from ...sources.functions import (clearTableWidget,
                                  getDatabaseNameFromAbsPath)


class WidgetTabCurve(QtWidgets.QWidget, Ui_widgetTabCurve):


    signalAddPlotDataItem    = QtCore.pyqtSignal(np.ndarray, np.ndarray, str, str, str, str, str, str, bool, bool)
    signalUpdatePlotDataItem = QtCore.pyqtSignal(np.ndarray, np.ndarray, str, str, bool, bool)
    signalRemovePlotDataItem = QtCore.pyqtSignal(str, str)


    def __init__(self, tabWidget: QtWidgets.QTabWidget,
                       plotRef: str) -> None:

        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)

        self.tabWidget = tabWidget
        self.plotRef = plotRef

        ## Only used to propagate information
        # curveId
        self.tableWidgetCurves.setColumnHidden(0, True)

        self.tableWidgetCurves.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tableWidgetCurves.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)



    def updateList1dCurvesLabels(self, plotRef: str,
                                       plotCurvesId: List[str],
                                       plots: list) -> None:

        # Get all the curveId already built
        curveIdBuilts = []
        for row in range(self.tableWidgetCurves.rowCount()):
            curveIdBuilts.append(self.tableWidgetCurves.item(row, 0).text())


        # Get all the curveId plotted
        curveIdPlots = []
        for curveId in plotCurvesId:
            if 'add' in curveId:
                curveIdPlots.append(curveId)

        # We clean the tableWidget and remove the not needed curve
        clearTableWidget(self.tableWidgetCurves)

        # Get all the curveId to build
        curveId2Builds = []
        for plot in plots:
            for curveId in plot.curves.keys():
                if 'add' not in curveId:
                    if plotRef!=plot.plotRef:
                        curveId2Builds.append(curveId)

        # Get all the curveId to remove
        curveId2Removes = []
        for curveIdPlot in curveIdPlots:
            if curveIdPlot[:-3] not in curveId2Builds:
                curveId2Removes.append(curveIdPlot)


        # Rebuild the GUI
        if len(curveId2Builds)>0:

            self.tableWidgetCurves.setRowCount(len(curveId2Builds))

            for row, curveId2Build in enumerate(curveId2Builds):
                cb = QtWidgets.QCheckBox()

                for plot in plots:
                    for curveId in plot.curves.keys():
                        if curveId==curveId2Build:
                            currentPlot = plot

                curveId = curveId2Build+'add'

                if curveId in plotCurvesId:
                    cb.setChecked(True)

                x = currentPlot.curves[curveId2Build].xData
                y = currentPlot.curves[curveId2Build].yData
                curveXLabel = currentPlot.curves[curveId2Build].curveXLabel
                curveXUnits = currentPlot.curves[curveId2Build].curveXUnits
                curveYLabel = currentPlot.curves[curveId2Build].curveYLabel
                curveYUnits = currentPlot.curves[curveId2Build].curveYUnits
                curveLegend = '{} - {}'.format(currentPlot.runId, currentPlot.curves[curveId2Build].curveYLabel)

                cb.toggled.connect(lambda state,
                                          x=x,
                                          y=y,
                                          curveId=curveId,
                                          curveXLabel=curveXLabel,
                                          curveXUnits=curveXUnits,
                                          curveYLabel=curveYLabel,
                                          curveYUnits=curveYUnits,
                                          curveLegend=curveLegend: self.toggleNewPlot(state,
                                                                                      x,
                                                                                      y,
                                                                                      curveId,
                                                                                      curveXLabel,
                                                                                      curveXUnits,
                                                                                      curveYLabel,
                                                                                      curveYUnits,
                                                                                      curveLegend))

                databaseName = getDatabaseNameFromAbsPath(currentPlot.databaseAbsPath)

                self.tableWidgetCurves.setItem(row, 0, QtWidgets.QTableWidgetItem(curveId))
                self.tableWidgetCurves.setCellWidget(row, 1, cb)
                self.tableWidgetCurves.setItem(row, 2, QtWidgets.QTableWidgetItem(databaseName))
                self.tableWidgetCurves.setItem(row, 3, QtWidgets.QTableWidgetItem(str(currentPlot.runId)))
                self.tableWidgetCurves.setItem(row, 4, QtWidgets.QTableWidgetItem(currentPlot.curves[curveId2Build].curveYLabel))
                self.tableWidgetCurves.setItem(row, 5, QtWidgets.QTableWidgetItem(currentPlot.curves[curveId2Build].curveXLabel))
                self.tableWidgetCurves.setItem(row, 4, QtWidgets.QTableWidgetItem(currentPlot.curves[curveId2Build].curveYLabel))
                self.tableWidgetCurves.setItem(row, 5, QtWidgets.QTableWidgetItem(currentPlot.curves[curveId2Build].curveXLabel))

            self.tableWidgetCurves.setSortingEnabled(True)
            self.tableWidgetCurves.sortByColumn(3, QtCore.Qt.DescendingOrder)
            self.tableWidgetCurves.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.tableWidgetCurves.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

            # Remove the curve
            for curveId2Remove in curveId2Removes:
                self.signalRemovePlotDataItem.emit(plotRef,
                                                   curveId2Remove)

            if self.tabWidget.count()==1:
                self.tabWidget.addTab(self, 'Add curves')
        else:
            self.tabWidget.removeTab(1)



    def toggleNewPlot(self, state       : bool,
                            x           : np.ndarray,
                            y           : np.ndarray,
                            curveId     : str,
                            curveXLabel : str,
                            curveXUnits : str,
                            curveYLabel : str,
                            curveYUnits : str,
                            curveLegend : str) -> None:
        """
        Called when user click on the checkbox of the curves tab.
        Add or remove curve in the plot window.
        """

        if state:
            self.signalAddPlotDataItem.emit(x, # x
                                            y, # y
                                            curveId, # curveId
                                            curveXLabel, # curveXLabel
                                            curveXUnits, # curveXUnits
                                            curveYLabel, # curveYLabel
                                            curveYUnits, # curveYUnits
                                            curveLegend, # curveLegend
                                            True, # showInLegend
                                            False) # hidden

        else:
            self.signalRemovePlotDataItem.emit(self.plotRef, # plotRef
                                               curveId)# curveId

