# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView
import numpy as np
# We remove warning from lmfit
import warnings
warnings.filterwarnings(
    action='ignore',
    module=r'lmfit',
)
warnings.filterwarnings(
    action='ignore',
    module=r'numpy',
)
import lmfit
import os
from typing import Tuple

from ...sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ...sources.functions import parse_number

LOC = os.path.join(os.path.dirname(os.path.realpath(__file__)))
JSPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'mathjax', 'tex-chtml.js')



class Fit2d(QtWidgets.QDialog):


    # To the fit groupBox
    signalCloseDialog = QtCore.pyqtSignal()
    signalFitResult = QtCore.pyqtSignal(np.ndarray, np.ndarray, np.ndarray, lmfit.Parameters)

    def __init__(self, parent: QtWidgets.QGroupBox) -> None:

        QtWidgets.QDialog.__init__(self, parent=parent)

        self.webView = QWebEngineView()
        self.webView.setHtml(self.defaultPageSource('1'),
                             baseUrl=QtCore.QUrl.fromLocalFile(LOC))
        self.webView.setMinimumHeight(100)
        self.webView.setMaximumHeight(100)
        self.webView.setMinimumWidth(500)
        self.label = QtWidgets.QLabel()
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label.installEventFilter(self)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.webView)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.setWindowTitle('Fit results')
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.show()



    def fitError(self, error:str) -> None:
        """
        Called when the fitting procedure failed
        """
        self.webView.setVisible(False)
        self.label.setText('<p style="color: red;">Fitting procedure failed</p><p>'+error+'</p>')



    def defaultPageSource(self, equation: str) -> str:

            return  '<html>'\
                        '<head>'\
                            '<script type="text/javascript" src="'+JSPATH+'?config=TeX-AMS-MML_HTMLorMML"></script>'\
                        '</head>'\
                        '<body>'\
                            '<p>'\
                                '<mathjax>$$'+equation+'$$</mathjax>'\
                            '</p>'\
                        '</body>'\
                    '</html>'



    def residual(self, p: lmfit.parameter.Parameters,
                       x: np.ndarray,
                       y: np.ndarray,
                       z: np.ndarray) -> np.ndarray:
        """
        Return the error between the model and the data.

        Parameters
        ----------
        p : lmfit.parameter.Parameters
            Fit parameters

        Returns
        -------
        np.ndarray
            Error between the model and the data.
        """

        resid = self.func(p, x, y) - z
        return resid.flatten()


    @QtCore.pyqtSlot(np.ndarray, np.ndarray, np.ndarray)
    def ffit(self, x: np.ndarray,
                   y: np.ndarray,
                   z: np.ndarray) -> Tuple[np.ndarray,
                                           np.ndarray,
                                           np.ndarray,
                                           lmfit.parameter.Parameters]:
        """
        Perform the fit through lmfit minimize function.

        Returns
        -------
        xSelected : np.ndarray
            Selected data from the x axis.
        ySelected : np.ndarray
            Selected data from the y ayis.
        zFit : np.ndarray
            Array of the z axis from the fit procedure.
        p : lmfit.parameter.Parameters
            lmfit parameters.
        """

        try :
            self.webView.setVisible(True)
            result = lmfit.minimize(fcn=self.residual,
                                    params=self.getInitialParams(x, y, z),
                                    args=(x, y, z))

            self.webView.setHtml(self.defaultPageSource(self.getLatexEquation),
                                baseUrl=QtCore.QUrl.fromLocalFile(LOC))
            self.label.setText(lmfit.fit_report(result))
            self.label.adjustSize()
            self.webView.adjustSize()

            self.signalFitResult.emit(x, y, self.func(result.params, x, y), result.params)

        except Exception as e:
            print(e)
            self.fitError(str(e))



    def closeEvent(self, evnt: QtGui.QCloseEvent) -> None:
        """
        Catch the closing of the dialog and propagate it to the fit groupBox.
        """

        self.signalCloseDialog.emit()





class RabiChevron(Fit2d):

    displayedLabel = 'Rabi chevron'

    def __init__(self, parent: QtWidgets.QGroupBox) -> None:
        """
        Suppose
            - x axis being the frequency detuning axis
            - y axis being the time delay axis

        Parameters
        ----------
        xData : np.ndarray
            Selected data from the x axis.
        yData : np.ndarray
            Selected data from the y axis.
        zData : np.ndarray
            Selected data from the z axis.
        """


        self.getLatexEquation = 'y = A \\frac{f_\\mathrm{rabi}^2}{f_\\mathrm{rabi}^2+\\left(f_\\mathrm{probe}-f_\\mathrm{qb}\\right)^2} \\sin^2\\left(\\pi t \\sqrt{f_\\mathrm{rabi}^2+\\left(f_\\mathrm{probe}-f_\\mathrm{qb}\\right)^2}  + \\varphi \\right ) \\exp\\left(-\\frac{t}{T_2^\\mathrm{rabi}} \\right) + B'

        Fit2d.__init__(self, parent=parent)



    def getInitialParams(self, x: np.ndarray,
                               y: np.ndarray,
                               z: np.ndarray) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """

        # Find the first column with not all 0 value
        i = 0
        while all(z[i]==0):
            i += 1

        # Guess initial value
        background = 0.
        amplitude = abs(np.nanmax(z[i])-np.nanmin(z[i]))/2.
        phi = np.arccos(z[i][0]/(np.nanmax(z[i]) - np.nanmin(z[i]))/2.)

        f = np.fft.fftfreq(len(y), d=y[1] - y[0])
        s = np.abs(np.fft.fft(z[i]))[f>=0]
        f = f[f>=0]
        f_rabi = f[np.nanargmax(s[2:])+2]



        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('amplitude',  amplitude, True, 0, None)
        params.add('f_rabi',     f_rabi, True, 0, None)
        params.add('f_qb',       np.nanmean(x), True, 0, None)
        params.add('t2_r',       np.nanmean(y), True, 1e-12, None)
        params.add('phi',        phi, True, -np.pi, np.pi)
        params.add('background', background, True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray,
                   y: np.ndarray) -> np.ndarray:
        """
        Fit model, see C. Cohen-Tannoudji, Vol. I, Complement F.IV, Eq. 27

        Parameters
        ----------
        p : lmfit.parameter.Parameters
            Current lmfit parameters.
        x : np.ndarray
            Selected data from the x axis.

        Returns
        -------
        y : np.ndarray
            Fit model result.
        """
        Y, X = np.meshgrid(y, x)

        df2 = (X - p['f_qb'])**2
        return p['amplitude']\
                *p['f_rabi']**2/(p['f_rabi']**2 + df2)\
                *np.sin(np.sqrt(p['f_rabi']**2 + df2)*np.pi*Y+p['phi'])**2\
                *np.exp(-Y/p['t2_r'])\
                + p['background']



    def displayedLegend(self, p: lmfit.parameter.Parameters) -> str:
        """
        Return the legend of the fit model

        Parameters
        ----------
        p : lmfit.parameter.Parameters
            lmfit parameters

        Returns
        -------
        legend : str
            Legend of the fit model
        """

        return 'f_rabi={:.{nbDecimal}e}<br/>'\
               'amplitude={:.{nbDecimal}e}<br/>'\
               'f_qb={:.{nbDecimal}e}<br/>'\
               't2_r={:.{nbDecimal}e}<br/>'\
               'phi={:.{nbDecimal}e}<br/>'\
               'background={:.{nbDecimal}e}<br/>'.format(
                   p['f_rabi'].value,
                   p['amplitude'].value,
                   p['f_qb'].value,
                   p['t2_r'].value,
                   p['phi'].value,
                   p['background'].value,
                    nbDecimal=config['fitParameterNbNumber'])