# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\scripts\pyplotter\pyplotter\ui\plot1d_widget.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.setEnabled(True)
        Dialog.resize(872, 453)
        Dialog.setSizeGripEnabled(True)
        Dialog.setModal(False)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = PlotWidget(Dialog)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.tabWidget = QtWidgets.QTabWidget(Dialog)
        self.tabWidget.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMinimumSize(QtCore.QSize(275, 0))
        self.tabWidget.setMaximumSize(QtCore.QSize(275, 16777215))
        self.tabWidget.setObjectName("tabWidget")
        self.tabInteraction = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabInteraction.sizePolicy().hasHeightForWidth())
        self.tabInteraction.setSizePolicy(sizePolicy)
        self.tabInteraction.setMinimumSize(QtCore.QSize(0, 0))
        self.tabInteraction.setMaximumSize(QtCore.QSize(275, 16777215))
        self.tabInteraction.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tabInteraction.setAutoFillBackground(False)
        self.tabInteraction.setObjectName("tabInteraction")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tabInteraction)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollAreaInteraction = QtWidgets.QScrollArea(self.tabInteraction)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaInteraction.sizePolicy().hasHeightForWidth())
        self.scrollAreaInteraction.setSizePolicy(sizePolicy)
        self.scrollAreaInteraction.setMaximumSize(QtCore.QSize(275, 16777215))
        self.scrollAreaInteraction.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollAreaInteraction.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scrollAreaInteraction.setLineWidth(0)
        self.scrollAreaInteraction.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollAreaInteraction.setWidgetResizable(True)
        self.scrollAreaInteraction.setObjectName("scrollAreaInteraction")
        self.scrollAreaWidgetInteraction = QtWidgets.QWidget()
        self.scrollAreaWidgetInteraction.setGeometry(QtCore.QRect(0, 0, 250, 615))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetInteraction.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetInteraction.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetInteraction.setMaximumSize(QtCore.QSize(275, 16777215))
        self.scrollAreaWidgetInteraction.setObjectName("scrollAreaWidgetInteraction")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetInteraction)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.verticalLayoutInteraction = QtWidgets.QVBoxLayout()
        self.verticalLayoutInteraction.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayoutInteraction.setObjectName("verticalLayoutInteraction")
        self.groupBoxDisplay = QtWidgets.QGroupBox(self.scrollAreaWidgetInteraction)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxDisplay.sizePolicy().hasHeightForWidth())
        self.groupBoxDisplay.setSizePolicy(sizePolicy)
        self.groupBoxDisplay.setMaximumSize(QtCore.QSize(230, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxDisplay.setFont(font)
        self.groupBoxDisplay.setObjectName("groupBoxDisplay")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBoxDisplay)
        self.verticalLayout_4.setContentsMargins(1, 5, 1, 1)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.pushButtonCopy = QtWidgets.QPushButton(self.groupBoxDisplay)
        self.pushButtonCopy.setObjectName("pushButtonCopy")
        self.verticalLayout_4.addWidget(self.pushButtonCopy)
        self.horizontalLayoutXAxis = QtWidgets.QHBoxLayout()
        self.horizontalLayoutXAxis.setObjectName("horizontalLayoutXAxis")
        self.labelXAxis = QtWidgets.QLabel(self.groupBoxDisplay)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.labelXAxis.setFont(font)
        self.labelXAxis.setObjectName("labelXAxis")
        self.horizontalLayoutXAxis.addWidget(self.labelXAxis)
        self.comboBoxXAxis = QtWidgets.QComboBox(self.groupBoxDisplay)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.comboBoxXAxis.setFont(font)
        self.comboBoxXAxis.setObjectName("comboBoxXAxis")
        self.horizontalLayoutXAxis.addWidget(self.comboBoxXAxis)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutXAxis.addItem(spacerItem)
        self.verticalLayout_4.addLayout(self.horizontalLayoutXAxis)
        self.horizontalLayoutLog = QtWidgets.QHBoxLayout()
        self.horizontalLayoutLog.setObjectName("horizontalLayoutLog")
        self.checkBoxLogX = QtWidgets.QCheckBox(self.groupBoxDisplay)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxLogX.setFont(font)
        self.checkBoxLogX.setObjectName("checkBoxLogX")
        self.horizontalLayoutLog.addWidget(self.checkBoxLogX)
        self.checkBoxLogY = QtWidgets.QCheckBox(self.groupBoxDisplay)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxLogY.setFont(font)
        self.checkBoxLogY.setObjectName("checkBoxLogY")
        self.horizontalLayoutLog.addWidget(self.checkBoxLogY)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutLog.addItem(spacerItem1)
        self.verticalLayout_4.addLayout(self.horizontalLayoutLog)
        self.checkBoxSymbol = QtWidgets.QCheckBox(self.groupBoxDisplay)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxSymbol.setFont(font)
        self.checkBoxSymbol.setObjectName("checkBoxSymbol")
        self.verticalLayout_4.addWidget(self.checkBoxSymbol)
        self.checkBoxCrossHair = QtWidgets.QCheckBox(self.groupBoxDisplay)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxCrossHair.setFont(font)
        self.checkBoxCrossHair.setChecked(False)
        self.checkBoxCrossHair.setObjectName("checkBoxCrossHair")
        self.verticalLayout_4.addWidget(self.checkBoxCrossHair)
        self.checkBoxSplitYAxis = QtWidgets.QCheckBox(self.groupBoxDisplay)
        self.checkBoxSplitYAxis.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxSplitYAxis.setFont(font)
        self.checkBoxSplitYAxis.setObjectName("checkBoxSplitYAxis")
        self.verticalLayout_4.addWidget(self.checkBoxSplitYAxis)
        self.verticalLayoutInteraction.addWidget(self.groupBoxDisplay)
        self.groupBoxCurveInteraction = QtWidgets.QGroupBox(self.scrollAreaWidgetInteraction)
        self.groupBoxCurveInteraction.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxCurveInteraction.sizePolicy().hasHeightForWidth())
        self.groupBoxCurveInteraction.setSizePolicy(sizePolicy)
        self.groupBoxCurveInteraction.setMaximumSize(QtCore.QSize(230, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxCurveInteraction.setFont(font)
        self.groupBoxCurveInteraction.setObjectName("groupBoxCurveInteraction")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBoxCurveInteraction)
        self.verticalLayout_2.setContentsMargins(1, 5, 1, 1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBoxHide = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxHide.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxHide.setFont(font)
        self.groupBoxHide.setObjectName("groupBoxHide")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.groupBoxHide)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayoutHide = QtWidgets.QVBoxLayout()
        self.verticalLayoutHide.setObjectName("verticalLayoutHide")
        self.verticalLayout_8.addLayout(self.verticalLayoutHide)
        self.verticalLayout_2.addWidget(self.groupBoxHide)
        self.groupBoxPlotDataItem = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBoxPlotDataItem.sizePolicy().hasHeightForWidth())
        self.groupBoxPlotDataItem.setSizePolicy(sizePolicy)
        self.groupBoxPlotDataItem.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxPlotDataItem.setFont(font)
        self.groupBoxPlotDataItem.setObjectName("groupBoxPlotDataItem")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBoxPlotDataItem)
        self.verticalLayout_3.setContentsMargins(1, 5, 1, 1)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayoutPlotDataItem = QtWidgets.QVBoxLayout()
        self.verticalLayoutPlotDataItem.setObjectName("verticalLayoutPlotDataItem")
        self.radioButtonFitNone = QtWidgets.QRadioButton(self.groupBoxPlotDataItem)
        self.radioButtonFitNone.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.radioButtonFitNone.setFont(font)
        self.radioButtonFitNone.setChecked(True)
        self.radioButtonFitNone.setObjectName("radioButtonFitNone")
        self.verticalLayoutPlotDataItem.addWidget(self.radioButtonFitNone)
        self.verticalLayout_3.addLayout(self.verticalLayoutPlotDataItem)
        self.verticalLayout_2.addWidget(self.groupBoxPlotDataItem)
        self.groupBoxCalculus = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxCalculus.setEnabled(False)
        self.groupBoxCalculus.setMaximumSize(QtCore.QSize(225, 16777215))
        self.groupBoxCalculus.setObjectName("groupBoxCalculus")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.groupBoxCalculus)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.checkBoxDifferentiate = QtWidgets.QCheckBox(self.groupBoxCalculus)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxDifferentiate.setFont(font)
        self.checkBoxDifferentiate.setObjectName("checkBoxDifferentiate")
        self.horizontalLayout_3.addWidget(self.checkBoxDifferentiate)
        self.checkBoxIntegrate = QtWidgets.QCheckBox(self.groupBoxCalculus)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxIntegrate.setFont(font)
        self.checkBoxIntegrate.setObjectName("checkBoxIntegrate")
        self.horizontalLayout_3.addWidget(self.checkBoxIntegrate)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.verticalLayout_2.addWidget(self.groupBoxCalculus)
        self.groupBoxStatistics = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxStatistics.setEnabled(False)
        self.groupBoxStatistics.setObjectName("groupBoxStatistics")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.groupBoxStatistics)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.verticalLayoutStatistics = QtWidgets.QVBoxLayout()
        self.verticalLayoutStatistics.setObjectName("verticalLayoutStatistics")
        self.horizontalLayoutStatistics = QtWidgets.QHBoxLayout()
        self.horizontalLayoutStatistics.setObjectName("horizontalLayoutStatistics")
        self.checkBoxStatistics = QtWidgets.QCheckBox(self.groupBoxStatistics)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxStatistics.setFont(font)
        self.checkBoxStatistics.setObjectName("checkBoxStatistics")
        self.horizontalLayoutStatistics.addWidget(self.checkBoxStatistics)
        self.spinBoxStatistics = QtWidgets.QSpinBox(self.groupBoxStatistics)
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
        self.verticalLayoutStatistics.addLayout(self.horizontalLayoutStatistics)
        self.verticalLayout_11.addLayout(self.verticalLayoutStatistics)
        self.verticalLayout_10.addLayout(self.verticalLayout_11)
        self.verticalLayout_2.addWidget(self.groupBoxStatistics)
        self.groupBoxNormalize = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxNormalize.setEnabled(False)
        self.groupBoxNormalize.setObjectName("groupBoxNormalize")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.groupBoxNormalize)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.checkBoxUnwrap = QtWidgets.QCheckBox(self.groupBoxNormalize)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxUnwrap.setFont(font)
        self.checkBoxUnwrap.setObjectName("checkBoxUnwrap")
        self.horizontalLayout_6.addWidget(self.checkBoxUnwrap)
        self.checkBoxRemoveSlop = QtWidgets.QCheckBox(self.groupBoxNormalize)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.checkBoxRemoveSlop.setFont(font)
        self.checkBoxRemoveSlop.setObjectName("checkBoxRemoveSlop")
        self.horizontalLayout_6.addWidget(self.checkBoxRemoveSlop)
        self.verticalLayout_7.addLayout(self.horizontalLayout_6)
        self.verticalLayout_9.addLayout(self.verticalLayout_7)
        self.verticalLayout_2.addWidget(self.groupBoxNormalize)
        self.groupBoxFFT = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxFFT.setEnabled(False)
        self.groupBoxFFT.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxFFT.setFont(font)
        self.groupBoxFFT.setObjectName("groupBoxFFT")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.groupBoxFFT)
        self.horizontalLayout_4.setContentsMargins(1, 5, 1, 1)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.radioButtonFFT = QtWidgets.QRadioButton(self.groupBoxFFT)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.radioButtonFFT.setFont(font)
        self.radioButtonFFT.setObjectName("radioButtonFFT")
        self.buttonGroup = QtWidgets.QButtonGroup(Dialog)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.radioButtonFFT)
        self.horizontalLayout_4.addWidget(self.radioButtonFFT)
        self.radioButtonFFTnoDC = QtWidgets.QRadioButton(self.groupBoxFFT)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.radioButtonFFTnoDC.setFont(font)
        self.radioButtonFFTnoDC.setObjectName("radioButtonFFTnoDC")
        self.buttonGroup.addButton(self.radioButtonFFTnoDC)
        self.horizontalLayout_4.addWidget(self.radioButtonFFTnoDC)
        self.radioButtonIFFT = QtWidgets.QRadioButton(self.groupBoxFFT)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.radioButtonIFFT.setFont(font)
        self.radioButtonIFFT.setObjectName("radioButtonIFFT")
        self.buttonGroup.addButton(self.radioButtonIFFT)
        self.horizontalLayout_4.addWidget(self.radioButtonIFFT)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem3)
        self.verticalLayout_2.addWidget(self.groupBoxFFT)
        self.groupBoxFiltering = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxFiltering.setEnabled(False)
        self.groupBoxFiltering.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxFiltering.setFont(font)
        self.groupBoxFiltering.setObjectName("groupBoxFiltering")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBoxFiltering)
        self.verticalLayout_6.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.verticalLayoutFilteringModel = QtWidgets.QVBoxLayout()
        self.verticalLayoutFilteringModel.setObjectName("verticalLayoutFilteringModel")
        self.verticalLayout_6.addLayout(self.verticalLayoutFilteringModel)
        self.verticalLayout_2.addWidget(self.groupBoxFiltering)
        self.groupBoxFit = QtWidgets.QGroupBox(self.groupBoxCurveInteraction)
        self.groupBoxFit.setEnabled(False)
        self.groupBoxFit.setMaximumSize(QtCore.QSize(225, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBoxFit.setFont(font)
        self.groupBoxFit.setObjectName("groupBoxFit")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBoxFit)
        self.verticalLayout_5.setContentsMargins(1, 5, 1, 1)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayoutFitModel = QtWidgets.QVBoxLayout()
        self.verticalLayoutFitModel.setObjectName("verticalLayoutFitModel")
        self.verticalLayout_5.addLayout(self.verticalLayoutFitModel)
        self.verticalLayout_2.addWidget(self.groupBoxFit)
        self.verticalLayoutInteraction.addWidget(self.groupBoxCurveInteraction)
        self.verticalLayout_12.addLayout(self.verticalLayoutInteraction)
        self.scrollAreaInteraction.setWidget(self.scrollAreaWidgetInteraction)
        self.verticalLayout.addWidget(self.scrollAreaInteraction)
        self.labelLivePlot = QtWidgets.QLabel(self.tabInteraction)
        self.labelLivePlot.setText("")
        self.labelLivePlot.setTextFormat(QtCore.Qt.RichText)
        self.labelLivePlot.setObjectName("labelLivePlot")
        self.verticalLayout.addWidget(self.labelLivePlot)
        self.labelCoordinate = QtWidgets.QLabel(self.tabInteraction)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelCoordinate.sizePolicy().hasHeightForWidth())
        self.labelCoordinate.setSizePolicy(sizePolicy)
        self.labelCoordinate.setMinimumSize(QtCore.QSize(0, 30))
        self.labelCoordinate.setObjectName("labelCoordinate")
        self.verticalLayout.addWidget(self.labelCoordinate)
        self.tabWidget.addTab(self.tabInteraction, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBoxDisplay.setTitle(_translate("Dialog", "Display"))
        self.pushButtonCopy.setText(_translate("Dialog", "Click to copie"))
        self.labelXAxis.setText(_translate("Dialog", "x axis:"))
        self.checkBoxLogX.setText(_translate("Dialog", "log x"))
        self.checkBoxLogY.setText(_translate("Dialog", "log y"))
        self.checkBoxSymbol.setText(_translate("Dialog", "symbol (fastest without)"))
        self.checkBoxCrossHair.setText(_translate("Dialog", "cross hair (fastest without)"))
        self.checkBoxSplitYAxis.setText(_translate("Dialog", "split y axis (only for 2 curves)"))
        self.groupBoxCurveInteraction.setTitle(_translate("Dialog", "Curve interaction"))
        self.groupBoxHide.setTitle(_translate("Dialog", "Hide curve"))
        self.groupBoxPlotDataItem.setTitle(_translate("Dialog", "Select curve"))
        self.radioButtonFitNone.setText(_translate("Dialog", "None"))
        self.groupBoxCalculus.setTitle(_translate("Dialog", "Calculus"))
        self.checkBoxDifferentiate.setText(_translate("Dialog", "differentiate"))
        self.checkBoxIntegrate.setText(_translate("Dialog", "integrate"))
        self.groupBoxStatistics.setTitle(_translate("Dialog", "Statistics"))
        self.checkBoxStatistics.setText(_translate("Dialog", "histogram"))
        self.spinBoxStatistics.setSuffix(_translate("Dialog", "  bin"))
        self.groupBoxNormalize.setTitle(_translate("Dialog", "Normalize"))
        self.checkBoxUnwrap.setText(_translate("Dialog", "unwrap"))
        self.checkBoxRemoveSlop.setText(_translate("Dialog", "remove slop"))
        self.groupBoxFFT.setTitle(_translate("Dialog", "FFT"))
        self.radioButtonFFT.setText(_translate("Dialog", "FFT"))
        self.radioButtonFFTnoDC.setText(_translate("Dialog", "FFT (no DC)"))
        self.radioButtonIFFT.setText(_translate("Dialog", "IFFT"))
        self.groupBoxFiltering.setTitle(_translate("Dialog", "Filtering"))
        self.groupBoxFit.setTitle(_translate("Dialog", "Fit"))
        self.labelCoordinate.setText(_translate("Dialog", "<html><head/><body><p>x:<br/>y:</p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabInteraction), _translate("Dialog", "Interaction"))
from .plotWidget import PlotWidget
