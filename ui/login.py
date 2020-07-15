# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(277, 143)
        Dialog.setMaximumSize(QtCore.QSize(16777215, 143))
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelId = QtWidgets.QLabel(Dialog)
        self.labelId.setMinimumSize(QtCore.QSize(80, 0))
        self.labelId.setObjectName("labelId")
        self.horizontalLayout.addWidget(self.labelId)
        self.lineEditId = QtWidgets.QLineEdit(Dialog)
        self.lineEditId.setObjectName("lineEditId")
        self.horizontalLayout.addWidget(self.lineEditId)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.labelPwd = QtWidgets.QLabel(Dialog)
        self.labelPwd.setMinimumSize(QtCore.QSize(80, 0))
        self.labelPwd.setObjectName("labelPwd")
        self.horizontalLayout_2.addWidget(self.labelPwd)
        self.lineEditPwd = QtWidgets.QLineEdit(Dialog)
        self.lineEditPwd.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEditPwd.setObjectName("lineEditPwd")
        self.horizontalLayout_2.addWidget(self.lineEditPwd)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.checkBoxCredentials = QtWidgets.QCheckBox(Dialog)
        self.checkBoxCredentials.setObjectName("checkBoxCredentials")
        self.horizontalLayout_4.addWidget(self.checkBoxCredentials)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.pushButtonLogin = QtWidgets.QPushButton(Dialog)
        self.pushButtonLogin.setObjectName("pushButtonLogin")
        self.verticalLayout.addWidget(self.pushButtonLogin)
        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Login"))
        self.labelId.setText(_translate("Dialog", "username :"))
        self.labelPwd.setText(_translate("Dialog", "password: "))
        self.checkBoxCredentials.setText(_translate("Dialog", "Store your credential locally (uncrypted)"))
        self.pushButtonLogin.setText(_translate("Dialog", "Login"))

