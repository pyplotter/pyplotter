# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
from typing import Tuple, Any, Optional
from scipy.signal import savgol_filter




class SavitzkyGolay(QtWidgets.QDialog):

    # For plot1d GUI
    checkBoxLabel = 'Savitzky-Golay'

    signalUpdate       = QtCore.pyqtSignal(np.ndarray, np.ndarray, str, str)
    signalCloseDialog  = QtCore.pyqtSignal(str)


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray) -> None:

        QtWidgets.QDialog.__init__(self, parent=parent)

        self.setMinimumSize(200, 200)

        # SavitzkyGolay needs two parameters
        self.windowLength       = 3
        self.polyorder          = 1

        self.xData = xData
        self.yData = yData

        spinBoxPolyorder = QtWidgets.QSpinBox()
        spinBoxPolyorder.setMinimum(1)
        spinBoxPolyorder.setMaximum(2)
        spinBoxPolyorder.setValue(self.polyorder)
        spinBoxPolyorder.valueChanged.connect(lambda value: self.polyorderChanged(value))

        labePolyorder = QtWidgets.QLabel('Polyorder: ')

        layoutPolyorder = QtWidgets.QHBoxLayout()
        layoutPolyorder.addWidget(labePolyorder)
        layoutPolyorder.addWidget(spinBoxPolyorder)



        spinBoxWindowLenght = QtWidgets.QSpinBox()
        spinBoxWindowLenght.setSingleStep(2)
        spinBoxWindowLenght.setMinimum(3)
        spinBoxWindowLenght.setMaximum(10000)
        spinBoxWindowLenght.setValue(self.windowLength)
        spinBoxWindowLenght.valueChanged.connect(lambda value,
                                                        spinBoxPolyorder=spinBoxPolyorder: self.windowLengthChanged(value, spinBoxPolyorder))

        labeWindowLength = QtWidgets.QLabel('Window length: ')

        layoutWindowLenght = QtWidgets.QHBoxLayout()
        layoutWindowLenght.addWidget(labeWindowLength)
        layoutWindowLenght.addWidget(spinBoxWindowLenght)



        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layoutWindowLenght)
        layout.addLayout(layoutPolyorder)

        self.setLayout(layout)

        self.setGeometry(1000, 30, 300, 100)
        self.setWindowTitle('Savitzky-Golay Filter')

        self.show()



    def legend2display(self) -> str:
        """
        Legend of the fitted curve displayed in the Plot1dApp.
        """

        return 'Savitzky-Golay: wl='+str(self.windowLength)+', po='+str(self.polyorder)



    def windowLengthChanged(self, value            : int,
                                   spinBoxPolyorder : QtWidgets.QSpinBox) -> None:
        """
        Method called when user press on the spinBoxPolyorder QSpinBox, see
        the SavitzkyGolayWindow class.
        Store the new window length value, take care that the polyorder
        parameter is always one less that the window length parameter and
        update the filtered plotDataItem.

        Parameters
        ----------
        value : int
            Value of the window length parameter.
        spinBoxPolyorder : QtWidgets.QSpinBox
            QSpinBox of the polyorder parameter.
        """

        self.windowLength = value
        spinBoxPolyorder.setMaximum(value-1)

        self.updateCurve()



    def polyorderChanged(self, value: int) -> None:
        """
        Method called when user press on the spinBoxPolyorder QSpinBox, see
        the SavitzkyGolayWindow class.
        Store the new polyorder value  and update the filtered plotDataItem.

        Parameters
        ----------
        value : int
            Value of the polyorder parameter.
        """

        self.polyorder = value

        self.updateCurve()



    def updateCurve(self, x: Optional[np.ndarray]=None,
                          y: Optional[np.ndarray]=None) -> None:

        if x is not None:
            self.xData = x
        if y is not None:
            self.yData = y

        self.signalUpdate.emit(self.xData,
                               savgol_filter(self.yData,
                                             self.windowLength,
                                             self.polyorder),
                                'filtering',
                                self.legend2display())



    def runFiltering(self) -> Tuple[np.ndarray, Any, str]:
        """
        Filter the data.

        Return
        ------
        xFiltered : np.ndarray
            Array of the x axis.
        yFiltered : np.ndarray
            Array of the y axis.
        legend : str
            Legend of the filtered curve.
        """

        return self.xData, savgol_filter(self.yData,
                                         self.windowLength,
                                         self.polyorder), self.legend2display()



    def closeEvent(self, evnt: QtGui.QCloseEvent) -> None:

        self.signalCloseDialog.emit('filtering')