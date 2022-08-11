# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\dialogFontSize.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DialogFontsize(object):
    def setupUi(self, DialogFontsize):
        DialogFontsize.setObjectName("DialogFontsize")
        DialogFontsize.setWindowModality(QtCore.Qt.NonModal)
        DialogFontsize.resize(158, 47)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogFontsize.sizePolicy().hasHeightForWidth())
        DialogFontsize.setSizePolicy(sizePolicy)
        DialogFontsize.setModal(False)
        self.verticalLayoutWidget = QtWidgets.QWidget(DialogFontsize)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 158, 47))
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
        self.label.setMaximumSize(QtCore.QSize(16777215, 25))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.spinBoxFontSize = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBoxFontSize.sizePolicy().hasHeightForWidth())
        self.spinBoxFontSize.setSizePolicy(sizePolicy)
        self.spinBoxFontSize.setMinimumSize(QtCore.QSize(0, 0))
        self.spinBoxFontSize.setMaximumSize(QtCore.QSize(16777215, 25))
        self.spinBoxFontSize.setMinimum(1)
        self.spinBoxFontSize.setObjectName("spinBoxFontSize")
        self.horizontalLayout.addWidget(self.spinBoxFontSize)
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

        self.retranslateUi(DialogFontsize)
        self.buttonBox.accepted.connect(DialogFontsize.accept)
        self.buttonBox.rejected.connect(DialogFontsize.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogFontsize)

    def retranslateUi(self, DialogFontsize):
        _translate = QtCore.QCoreApplication.translate
        DialogFontsize.setWindowTitle(_translate("DialogFontsize", "Font size"))
        self.label.setText(_translate("DialogFontsize", "Font size:"))
        self.spinBoxFontSize.setSuffix(_translate("DialogFontsize", "pt"))
