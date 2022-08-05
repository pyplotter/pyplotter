# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\dialogColormap.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DialogColormap(object):
    def setupUi(self, DialogColormap):
        DialogColormap.setObjectName("DialogColormap")
        DialogColormap.setWindowModality(QtCore.Qt.NonModal)
        DialogColormap.resize(158, 47)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogColormap.sizePolicy().hasHeightForWidth())
        DialogColormap.setSizePolicy(sizePolicy)
        DialogColormap.setModal(False)
        self.verticalLayoutWidget = QtWidgets.QWidget(DialogColormap)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 163, 47))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(0, 1, -1, -1)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setMinimumSize(QtCore.QSize(0, 0))
        self.label.setMaximumSize(QtCore.QSize(60, 25))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.comboBoxColormap = QtWidgets.QComboBox(self.verticalLayoutWidget)
        self.comboBoxColormap.setMaximumSize(QtCore.QSize(85, 16777215))
        self.comboBoxColormap.setObjectName("comboBoxColormap")
        self.horizontalLayout.addWidget(self.comboBoxColormap)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setMaximumSize(QtCore.QSize(16777215, 30))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(DialogColormap)
        self.buttonBox.accepted.connect(DialogColormap.accept)
        self.buttonBox.rejected.connect(DialogColormap.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogColormap)

    def retranslateUi(self, DialogColormap):
        _translate = QtCore.QCoreApplication.translate
        DialogColormap.setWindowTitle(_translate("DialogColormap", "Colormap"))
        self.label.setText(_translate("DialogColormap", "colormap:"))
