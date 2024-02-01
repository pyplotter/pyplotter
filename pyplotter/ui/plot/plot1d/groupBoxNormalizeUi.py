# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\plot1d\groupBoxNormalize.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GroupBoxNormalize(object):
    def setupUi(self, groupBoxNormalize):
        groupBoxNormalize.setObjectName("groupBoxNormalize")
        groupBoxNormalize.setEnabled(False)
        groupBoxNormalize.setGeometry(QtCore.QRect(30, 190, 226, 57))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        groupBoxNormalize.setFont(font)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(groupBoxNormalize)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.checkBoxUnwrap = QtWidgets.QCheckBox(groupBoxNormalize)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxUnwrap.setFont(font)
        self.checkBoxUnwrap.setObjectName("checkBoxUnwrap")
        self.horizontalLayout_6.addWidget(self.checkBoxUnwrap)
        self.checkBoxRemoveSlope = QtWidgets.QCheckBox(groupBoxNormalize)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxRemoveSlope.setFont(font)
        self.checkBoxRemoveSlope.setObjectName("checkBoxRemoveSlope")
        self.horizontalLayout_6.addWidget(self.checkBoxRemoveSlope)
        self.verticalLayout_7.addLayout(self.horizontalLayout_6)
        self.verticalLayout_9.addLayout(self.verticalLayout_7)

        self.retranslateUi(groupBoxNormalize)
        QtCore.QMetaObject.connectSlotsByName(groupBoxNormalize)

    def retranslateUi(self, groupBoxNormalize):
        _translate = QtCore.QCoreApplication.translate
        groupBoxNormalize.setTitle(_translate("GroupBoxNormalize", "Normalize"))
        self.checkBoxUnwrap.setText(_translate("GroupBoxNormalize", "unwrap"))
        self.checkBoxRemoveSlope.setText(_translate("GroupBoxNormalize", "remove slop"))
