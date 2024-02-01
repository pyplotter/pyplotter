# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\plot1d\groupBoxCalculus.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_groupBoxCalculus(object):
    def setupUi(self, groupBoxCalculus):
        groupBoxCalculus.setObjectName("groupBoxCalculus")
        groupBoxCalculus.setEnabled(False)
        groupBoxCalculus.resize(225, 56)
        groupBoxCalculus.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        groupBoxCalculus.setFont(font)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(groupBoxCalculus)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.checkBoxDifferentiate = QtWidgets.QCheckBox(groupBoxCalculus)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxDifferentiate.setFont(font)
        self.checkBoxDifferentiate.setObjectName("checkBoxDifferentiate")
        self.horizontalLayout_3.addWidget(self.checkBoxDifferentiate)
        self.checkBoxIntegrate = QtWidgets.QCheckBox(groupBoxCalculus)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxIntegrate.setFont(font)
        self.checkBoxIntegrate.setObjectName("checkBoxIntegrate")
        self.horizontalLayout_3.addWidget(self.checkBoxIntegrate)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)

        self.retranslateUi(groupBoxCalculus)
        QtCore.QMetaObject.connectSlotsByName(groupBoxCalculus)

    def retranslateUi(self, groupBoxCalculus):
        _translate = QtCore.QCoreApplication.translate
        groupBoxCalculus.setTitle(_translate("groupBoxCalculus", "Calculus"))
        self.checkBoxDifferentiate.setText(_translate("groupBoxCalculus", "differentiate"))
        self.checkBoxIntegrate.setText(_translate("groupBoxCalculus", "integrate"))
