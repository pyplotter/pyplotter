# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\plot1d\groupBoxFFT.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_QGroupBoxFFT(object):
    def setupUi(self, groupBoxFFT):
        groupBoxFFT.setObjectName("groupBoxFFT")
        groupBoxFFT.setEnabled(False)
        groupBoxFFT.setGeometry(QtCore.QRect(80, 0, 225, 44))
        groupBoxFFT.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        groupBoxFFT.setFont(font)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(groupBoxFFT)
        self.horizontalLayout_4.setContentsMargins(1, 5, 1, 1)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.checkBoxFFT = QtWidgets.QCheckBox(groupBoxFFT)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxFFT.setFont(font)
        self.checkBoxFFT.setObjectName("checkBoxFFT")
        self.horizontalLayout_4.addWidget(self.checkBoxFFT)
        self.checkBoxFFTnoDC = QtWidgets.QCheckBox(groupBoxFFT)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxFFTnoDC.setFont(font)
        self.checkBoxFFTnoDC.setObjectName("checkBoxFFTnoDC")
        self.horizontalLayout_4.addWidget(self.checkBoxFFTnoDC)
        self.checkBoxIFFT = QtWidgets.QCheckBox(groupBoxFFT)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxIFFT.setFont(font)
        self.checkBoxIFFT.setObjectName("checkBoxIFFT")
        self.horizontalLayout_4.addWidget(self.checkBoxIFFT)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)

        self.retranslateUi(groupBoxFFT)
        QtCore.QMetaObject.connectSlotsByName(groupBoxFFT)

    def retranslateUi(self, groupBoxFFT):
        _translate = QtCore.QCoreApplication.translate
        groupBoxFFT.setTitle(_translate("QGroupBoxFFT", "FFT"))
        self.checkBoxFFT.setText(_translate("QGroupBoxFFT", "FFT"))
        self.checkBoxFFTnoDC.setText(_translate("QGroupBoxFFT", "FFT (no DC)"))
        self.checkBoxIFFT.setText(_translate("QGroupBoxFFT", "IFFT"))
