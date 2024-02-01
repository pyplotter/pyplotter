# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\plot1d\widgetTabCurve.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_widgetTabCurve(object):
    def setupUi(self, widgetTabCurve):
        widgetTabCurve.setObjectName("widgetTabCurve")
        widgetTabCurve.resize(293, 311)
        widgetTabCurve.setMinimumSize(QtCore.QSize(275, 0))
        widgetTabCurve.setMaximumSize(QtCore.QSize(293, 16777215))
        self.verticalLayout = QtWidgets.QVBoxLayout(widgetTabCurve)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidgetCurves = QtWidgets.QTableWidget(widgetTabCurve)
        self.tableWidgetCurves.setMinimumSize(QtCore.QSize(270, 0))
        self.tableWidgetCurves.setMaximumSize(QtCore.QSize(275, 16777215))
        self.tableWidgetCurves.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidgetCurves.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetCurves.setAlternatingRowColors(True)
        self.tableWidgetCurves.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidgetCurves.setShowGrid(False)
        self.tableWidgetCurves.setObjectName("tableWidgetCurves")
        self.tableWidgetCurves.setColumnCount(6)
        self.tableWidgetCurves.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidgetCurves.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidgetCurves.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidgetCurves.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidgetCurves.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidgetCurves.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidgetCurves.setHorizontalHeaderItem(5, item)
        self.tableWidgetCurves.horizontalHeader().setStretchLastSection(True)
        self.tableWidgetCurves.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableWidgetCurves)

        self.retranslateUi(widgetTabCurve)
        QtCore.QMetaObject.connectSlotsByName(widgetTabCurve)

    def retranslateUi(self, widgetTabCurve):
        _translate = QtCore.QCoreApplication.translate
        widgetTabCurve.setWindowTitle(_translate("widgetTabCurve", "Curve"))
        item = self.tableWidgetCurves.horizontalHeaderItem(0)
        item.setText(_translate("widgetTabCurve", "curveId"))
        item = self.tableWidgetCurves.horizontalHeaderItem(1)
        item.setText(_translate("widgetTabCurve", "plot"))
        item = self.tableWidgetCurves.horizontalHeaderItem(2)
        item.setText(_translate("widgetTabCurve", "db"))
        item = self.tableWidgetCurves.horizontalHeaderItem(3)
        item.setText(_translate("widgetTabCurve", "run id"))
        item = self.tableWidgetCurves.horizontalHeaderItem(4)
        item.setText(_translate("widgetTabCurve", "axis"))
        item = self.tableWidgetCurves.horizontalHeaderItem(5)
        item.setText(_translate("widgetTabCurve", "swept parameter"))
