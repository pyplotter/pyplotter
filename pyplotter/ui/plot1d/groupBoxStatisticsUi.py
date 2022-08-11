# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\plot1d\groupBoxStatistics.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_groupBoxStatistics(object):
    def setupUi(self, groupBoxStatistics):
        groupBoxStatistics.setObjectName("groupBoxStatistics")
        groupBoxStatistics.setEnabled(False)
        groupBoxStatistics.resize(226, 68)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        groupBoxStatistics.setFont(font)
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(groupBoxStatistics)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.verticalLayoutStatistics = QtWidgets.QVBoxLayout()
        self.verticalLayoutStatistics.setObjectName("verticalLayoutStatistics")
        self.horizontalLayoutStatistics = QtWidgets.QHBoxLayout()
        self.horizontalLayoutStatistics.setObjectName("horizontalLayoutStatistics")
        self.checkBoxStatistics = QtWidgets.QCheckBox(groupBoxStatistics)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxStatistics.setFont(font)
        self.checkBoxStatistics.setObjectName("checkBoxStatistics")
        self.horizontalLayoutStatistics.addWidget(self.checkBoxStatistics)
        self.spinBoxStatistics = QtWidgets.QSpinBox(groupBoxStatistics)
        self.spinBoxStatistics.setMaximumSize(QtCore.QSize(60, 16777215))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.spinBoxStatistics.setFont(font)
        self.spinBoxStatistics.setPrefix("")
        self.spinBoxStatistics.setMinimum(1)
        self.spinBoxStatistics.setMaximum(1000000)
        self.spinBoxStatistics.setProperty("value", 10)
        self.spinBoxStatistics.setObjectName("spinBoxStatistics")
        self.horizontalLayoutStatistics.addWidget(self.spinBoxStatistics)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutStatistics.addItem(spacerItem)
        self.verticalLayoutStatistics.addLayout(self.horizontalLayoutStatistics)
        self.statisticsLabel = QtWidgets.QLabel(groupBoxStatistics)
        self.statisticsLabel.setMaximumSize(QtCore.QSize(16777215, 0))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.statisticsLabel.setFont(font)
        self.statisticsLabel.setText("")
        self.statisticsLabel.setObjectName("statisticsLabel")
        self.verticalLayoutStatistics.addWidget(self.statisticsLabel)
        self.verticalLayout_11.addLayout(self.verticalLayoutStatistics)
        self.verticalLayout_10.addLayout(self.verticalLayout_11)

        self.retranslateUi(groupBoxStatistics)
        QtCore.QMetaObject.connectSlotsByName(groupBoxStatistics)

    def retranslateUi(self, groupBoxStatistics):
        _translate = QtCore.QCoreApplication.translate
        groupBoxStatistics.setTitle(_translate("groupBoxStatistics", "Statistics"))
        self.checkBoxStatistics.setText(_translate("groupBoxStatistics", "histogram"))
        self.spinBoxStatistics.setSuffix(_translate("groupBoxStatistics", "  bin"))
