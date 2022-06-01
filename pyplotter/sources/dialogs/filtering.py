# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
import numpy as np
from typing import Callable, Tuple, Any
from scipy.signal import savgol_filter





class SavitzkyGolayWindow(QtWidgets.QDialog):



    def __init__(self, windowsLength        : int,
                       polyorder            : int,
                       windowsLengthChanged : Callable[[int, int], None],
                       polyorderChanged     : Callable[[int], None]) -> None:
        """
        QDialog window launched when user filters its data with the
        Savitzky-Golay filter, see SavitzkyGolay class.
        Allow user to modify the filter parameters.
        When user modifies the filter parameter, the filtered data are
        automaticaly updated by means of the *Changed function.

        Parameters
        ----------
        windowsLength : int
            Initial value of the window length parameter.
            See SavitzkyGolay class.
        polyorder : int
            Initial value of the polyorder parameter.
            See SavitzkyGolay class.
        windowsLengthChanged : Callable[[int, int], None]
            Function called when the window length parameter is changed.
            See SavitzkyGolay class.
        polyorderChanged : Callable[[int], None]
            Function called when the polyorder parameter is changed.
            See SavitzkyGolay class.
        """

        QtWidgets.QDialog.__init__(self)


        self.setMinimumSize(200, 200)

        # SavitzkyGolay needs two parameters


        spinBoxPolyorder = QtWidgets.QSpinBox()
        spinBoxPolyorder.setMinimum(1)
        spinBoxPolyorder.setMaximum(2)
        spinBoxPolyorder.setValue(polyorder)
        spinBoxPolyorder.valueChanged.connect(lambda value: polyorderChanged(value))

        labePolyorder = QtWidgets.QLabel('Polyorder: ')

        layoutPolyorder = QtWidgets.QHBoxLayout()
        layoutPolyorder.addWidget(labePolyorder)
        layoutPolyorder.addWidget(spinBoxPolyorder)



        spinBoxWindowLenght = QtWidgets.QSpinBox()
        spinBoxWindowLenght.setSingleStep(2)
        spinBoxWindowLenght.setMinimum(3)
        spinBoxWindowLenght.setMaximum(10000)
        spinBoxWindowLenght.setValue(windowsLength)
        spinBoxWindowLenght.valueChanged.connect(lambda value,
                                                        spinBoxPolyorder=spinBoxPolyorder: windowsLengthChanged(value, spinBoxPolyorder))

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




class SavitzkyGolay:



    def __init__(self, xData: np.ndarray,
                       yData: np.ndarray,
                       updatePlotDataItem: Callable[[np.ndarray, np.ndarray, str, str, bool], None]=None) -> None:
        """
        Instanced when user wants to filter its data using a Savitzky-Golay filter.
        User can modify the filter parameter by the mean of a QDialog, see
        SavitzkyGolayWindow class.

        Parameters
        ----------
        xData: np.ndarray
            Array of the selected x axis data
        yData: np.ndarray
            Array of the selected y axis data
        updatePlotDataItem : Callable[[np.ndarray, np.ndarray, str, str, bool], None]
            Method from Plot1dApp
        """

        self.xData              = xData
        self.yData              = yData
        self.windowLength       = 3
        self.polyorder          = 1
        self.updatePlotDataItem = updatePlotDataItem



    def checkBoxLabel(self) -> str:
        """
        Name of the filter displayed in the Plot1dApp.
        """

        return 'Savitzky-Golay'



    def legend2display(self) -> str:
        """
        Legend of the fitted curve displayed in the Plot1dApp.
        """

        return 'Savitzky-Golay: wl='+str(self.windowLength)+', po='+str(self.polyorder)



    def windowsLengthChanged(self, value            : int,
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

        self.updateFiltering()



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

        self.updateFiltering()



    def updateFiltering(self) -> None:
        """
        Update the filtered plotDataItem through the Plot1DApp method
        updatePlotDataItem.
        """

        self.updatePlotDataItem(x           = self.xData,
                                y           = savgol_filter(self.yData,
                                                            self.windowLength,
                                                            self.polyorder),
                                curveId     = 'filtering',
                                curveLegend = self.legend2display()) # type: ignore



    def runFiltering(self) -> Tuple[np.ndarray, Any, SavitzkyGolayWindow, str]:
        """
        Filter the data.

        Return
        ------
        xFiltered : np.ndarray
            Array of the x axis.
        yFiltered : np.ndarray
            Array of the y axis.
        filteringWindow :QtWidgets.QDialog
            Window allowing user to modify filter parameters.
        legend : str
            Legend of the filtered curve.
        """

        filteringWindow  = SavitzkyGolayWindow(self.windowLength,
                                            self.polyorder,
                                            self.windowsLengthChanged,
                                            self.polyorderChanged)


        return self.xData, savgol_filter(self.yData,
                                         self.windowLength,
                                         self.polyorder), filteringWindow, self.legend2display()