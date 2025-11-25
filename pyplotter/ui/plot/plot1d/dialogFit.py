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
from scipy.signal import hilbert
from typing import Tuple


from ....sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ....sources.functions import parse_number

LOC = os.path.join(os.path.dirname(os.path.realpath(__file__)))
JSPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'mathjax', 'tex-chtml.js')



class Fit1d(QtWidgets.QDialog):


    signalCloseDialog = QtCore.pyqtSignal()
    signalUpdateDialog = QtCore.pyqtSignal()


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='',
                       method: str='lbfgsb') -> None:

        QtWidgets.QDialog.__init__(self, parent=parent)

        self.xData      = xData
        self.yData      = yData
        self.xUnits     = xUnits
        self.yUnits     = yUnits

        self._method = method

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



    def fitError(self) -> None:
        """
        Called when the fitting procedure failed
        """

        self.layout.removeWidget(self.webView)
        self.label.setText('<span style="color: red;">Fitting procedure failed</span>')



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



    def getFitType(self) -> str:
        """
        Return the fitType, either 1d or 2d.
        """

        return self.fitType



    def residual(self, p: lmfit.parameter.Parameters) -> np.ndarray:
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

        return self.func(p, self.xData) - self.yData



    def ffit(self) -> Tuple[np.ndarray,
                            np.ndarray,
                            lmfit.parameter.Parameters]:
        """
        Perform the fit through lmfit minimize function.


        Returns
        -------
        xSelected : np.ndarray
            Selected data from the x axis.
        yFit : np.ndarray
            Array of the y axis from the fit procedure.
        p : lmfit.parameter.Parameters
            lmfit parameters.
        """

        result = lmfit.minimize(self.residual, self.getInitialParams(), method=self._method)
        # dx = np.gradient(self.xData)/2.
        # x = np.sort(np.concatenate((self.xData, self.xData+dx)))

        self.webView.setHtml(self.defaultPageSource(self.getLatexEquation),
                             baseUrl=QtCore.QUrl.fromLocalFile(LOC))
        self.label.setText(lmfit.fit_report(result))
        self.label.adjustSize()
        self.webView.adjustSize()

        return self.xData, self.func(result.params, self.xData), result.params



    def closeEvent(self, evnt: QtGui.QCloseEvent) -> None:

        self.signalCloseDialog.emit()



class Polynomial(Fit1d):

    displayedLabel = 'Polynomial'

    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:
        """

        Parameters
        ----------
        xData : np.ndarray
            Selected data from the x axis.
        yData : np.ndarray
            Selected data from the y axis.
        """


        self.fitType = '1d'
        self.getLatexEquation = r'y = \sum_{k=0}^n a_k x^k'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)

        layout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel('Polynomial coefficients:')
        layout.addWidget(label)

        self.spinBoxDeg = QtWidgets.QSpinBox()
        self.spinBoxDeg.setMinimum(0)
        self.spinBoxDeg.setMaximum(100)
        self.spinBoxDeg.setValue(1)
        self.spinBoxDeg.setSingleStep(1)
        self.spinBoxDeg.setFixedWidth(42)
        self.spinBoxDeg.valueChanged.connect(self.signalUpdateDialog.emit)
        layout.addWidget(self.spinBoxDeg)

        layout.addSpacerItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        self.layout.insertLayout(len(self.layout)-1, layout)
        self.layout.addSpacerItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))



    def getInitialParams(self) -> None:
        pass



    def getPolyOrder(self) -> int:

        return self.spinBoxDeg.value() + 1



    def ffit(self) -> Tuple[np.ndarray,
                            np.ndarray,
                            lmfit.parameter.Parameters]:
        """
        Perform the fit through lmfit minimize function.


        Returns
        -------
        xSelected : np.ndarray
            Selected data from the x axis.
        yFit : np.ndarray
            Array of the y axis from the fit procedure.
        p : lmfit.parameter.Parameters
            lmfit parameters.
        """

        p = lmfit.Parameters()

        self.polyFit = np.polynomial.polynomial.Polynomial.fit(self.xData, self.yData, self.getPolyOrder())

        self.webView.setHtml(self.defaultPageSource(self.getLatexEquation),
                             baseUrl=QtCore.QUrl.fromLocalFile(LOC))
        self.label.setText(self.displayedLegend(p))
        self.label.adjustSize()
        self.webView.adjustSize()

        return self.xData, self.polyFit(self.xData), p



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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

        return self.polyFit(x)



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

        legend = ''
        for i, j in zip(range(self.getPolyOrder()), self.polyFit.coef):
            legend += 'a{:.0f}={:.{nbDecimal}e}<br/>'.format(i, j, nbDecimal=config['fitParameterNbNumber'])
        return legend







class T2Gaussian(Fit1d):

    displayedLabel = 'T2 gaussian'

    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:
        """

        Parameters
        ----------
        xData : np.ndarray
            Selected data from the x axis.
        yData : np.ndarray
            Selected data from the y axis.
        """


        self.fitType = '1d'
        self.getLatexEquation = r'y = A \left( 1 - \cos \left( 2 \pi \frac{x}{T} + \varphi \right) \exp \left( - \frac{x}{T_2} - \left( \frac{x}{T_{2,g}} \right)^2 \right) \right) + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # linearize the timescale
        x = np.linspace(self.xData[0], self.xData[-1], len(self.xData))
        y = np.interp(x, self.xData, self.yData)

        # Guess initial value
        background = 0.
        amplitude = abs(np.max(y)-np.min(y))/2.
        phi = np.arccos(y[0]/(np.max(y) - np.min(y))/2.)
        i = 0
        while True and i<len(y)-1:
            if (y[i]-0.5)/np.abs(y[i]-0.5) != (y[i+1]-0.5)/np.abs(y[i+1]-0.5):
                break
            i += 1
        period = x[i]*4

        # Get envelope in log neperien scale
        y_hilbert = np.log(np.abs(hilbert(y-np.mean(y))))
        y_hilbert -= np.min(y_hilbert)
        y1 = np.max(y_hilbert)
        y2 = np.max(y_hilbert)/2.
        x1 = x[np.argmin(np.abs(y_hilbert-y1))]
        x2 = x[np.argmin(np.abs(y_hilbert-y2))]
        t2 = -(x1-x2)/(y1-y2)


        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('amplitude',  amplitude, True, None, None)
        params.add('period',     period, True, None, None)
        params.add('t2',         t2, True, None, None)
        params.add('t2_g',       t2, True, None, None)
        params.add('phi',        phi, True, None, None)
        params.add('background', background, True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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

        return p['amplitude']*(1.-np.cos(2.*np.pi*x/p['period']+p['phi'])*np.exp(-x/p['t2']-(x/p['t2_g'])**2.)) + p['background']



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

        return 'T2={:.{nbDecimal}e}<br/>T2g={:.{nbDecimal}e}'.format(p['t2'].value, p['t2_g'].value, nbDecimal=config['fitParameterNbNumber'])









class T2(Fit1d):


    displayedLabel = 'T2'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = A \left( 1 - \cos \left( 2 \pi \frac{x}{T} + \varphi \right) \exp \left( - \frac{x}{T_2} \right) \right) + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """



        # linearize the timescale
        x = np.linspace(self.xData[0], self.xData[-1], len(self.xData))
        y = np.interp(x, self.xData, self.yData)

        # Guess initial value
        background = 0.
        amplitude = abs(np.max(y)-np.min(y))/2.
        phi = np.arccos(y[0]/(np.max(y) - np.min(y))/2.)
        i = 0
        while True and i<len(y)-1:
            if (y[i]-0.5)/np.abs(y[i]-0.5) !=  (y[i+1]-0.5)/np.abs(y[i+1]-0.5):
                break
            i += 1
        period = x[i]*4

        # Get envelope in log neperien scale
        y_hilbert = np.log(np.abs(hilbert(y-np.mean(y))))
        y_hilbert -= np.min(y_hilbert)
        y1 = np.max(y_hilbert)
        y2 = np.max(y_hilbert)/2.
        x1 = x[np.argmin(np.abs(y_hilbert-y1))]
        x2 = x[np.argmin(np.abs(y_hilbert-y2))]
        t2 = -(x1-x2)/(y1-y2)


        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('amplitude',  amplitude, True, None, None)
        params.add('period',     period, True, None, None)
        params.add('t2',         t2, True, None, None)
        params.add('phi',        phi, True, None, None)
        params.add('background', background, True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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


        return p['amplitude']*(1.-np.cos(2.*np.pi*x/p['period']+p['phi'])*np.exp(-x/p['t2'])) + p['background']



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


        return 'T2={:.{nbDecimal}e}'.format(p['t2'].value, nbDecimal=config['fitParameterNbNumber'])








class T11d(Fit1d):


    displayedLabel = 'T1'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = A \exp \left( - \frac{x}{T_1} \right) + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # linearize the timescale
        x = np.linspace(self.xData[0], self.xData[-1], len(self.xData))
        y = np.interp(x, self.xData, self.yData)

        # Guess initial value
        background = np.mean(y[-10:])
        amplitude = abs(np.max(y)-np.min(y))
        # Get envelope in log neperien scale
        y = np.log(np.abs(y-background))
        y -= np.min(y)
        y1 = np.max(y)
        y2 = np.max(y)/2.
        x1 = x[np.argmin(np.abs(y-y1))]
        x2 = x[np.argmin(np.abs(y-y2))]
        t1 = -(x1-x2)/(y1-y2)

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('amplitude',  amplitude, True, 0., None)
        params.add('t1',         t1, True, 0., None)
        params.add('background', background, True, 0., None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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

        return p['amplitude']*np.exp(-x/p['t1']) + p['background']



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


        return 'T1={:.{nbDecimal}e}'.format(p['t1'].value, nbDecimal=config['fitParameterNbNumber'])








class ResonancePeakdB(Fit1d):

    displayedLabel = 'Resonance peak (dB)'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = 20 \log \left( \left\lVert 1-\left( 1+\frac{e^{i \phi } Q_\mathrm{i}}{Q_\mathrm{c} \left(1+\frac{2 i Q_\mathrm{i} (x-f_0)}{f_0}\right)}\right)^{-1} \right\rVert\right) + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)


    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background = np.mean(np.sort(self.yData)[-10:])
        f0 = self.xData[np.argmax(self.yData)]

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('f0', f0, True, None, None)
        params.add('qi', 1e3, True, None, None)
        params.add('qc', 20., True, None, None)
        params.add('phi', 0., True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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


        dx = (x - p['f0'])/p['f0']
        y = 1.-1./(1. + p['qi']/p['qc']*np.exp(1j*p['phi'])/(1. + 2j*p['qi']*dx))

        return 20.*np.log10(np.abs(y))+p['background']


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


        return 'f0={:.{nbDecimal}e}<br/>qi={:.{nbDecimal}e}<br/>qc={:.{nbDecimal}e}'.format(p['f0'].value, p['qi'].value, p['qc'].value, nbDecimal=config['fitParameterNbNumber'])








class ResonanceDipdB(Fit1d):

    displayedLabel = 'Resonance dip (dB)'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = 20 \log \left( \left\lVert \left( 1+\frac{e^{i \phi } Q_\mathrm{i}}{Q_\mathrm{c} \left(1+\frac{2 i Q_\mathrm{i} (x-f_0)}{f_0}\right)}\right)^{-1} \right\rVert\right) + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        ## Guess initial value

        # background in db
        background = np.mean(self.yData[-10:])


        # Find resonance frequency, unit does not matter (Hz or GHz)
        f0 = self.xData[np.argmin(self.yData)]

        ## Calculate Qi, Qc from f0, FWHM and height
        # find fwhm for Qc
        n0 = np.argmin(self.yData)
        n1 =      np.abs(self.yData[:n0] - (background-3)).argmin()
        n2 = n0 + np.abs(self.yData[n0:] - (background-3)).argmin()
        fwhm = self.xData[n2] - self.xData[n1]

        qc = np.sqrt(2)*f0/fwhm


        # find fwhm for Qi
        n0 = np.argmin(self.yData)
        n1 =      np.abs(self.yData[:n0] - (self.yData.min()+3)).argmin()
        n2 = n0 + np.abs(self.yData[n0:] - (self.yData.min()+3)).argmin()
        fwhm = self.xData[n2] - self.xData[n1]

        # Find height in linear scale for Qi
        height_db = background-abs(self.yData.min())
        height_lin = 10**(height_db/20)

        qi = f0/fwhm*np.sqrt(2/(1-height_lin))


        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('f0', f0, True, None, None)
        params.add('qi', qi, True, None, None)
        params.add('qc', qc, True, None, None)
        params.add('phi', 0., True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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


        dx = (x - p['f0'])/p['f0']
        y = 1./(1. + p['qi']/p['qc']*np.exp(1j*p['phi'])/(1. + 2j*p['qi']*dx))

        return 20.*np.log10(np.abs(y))+ p['background']



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

        return 'f0={}{}<br/>'\
               'qi={}<br/>'\
               'qc={}'.format(parse_number(p['f0'].value, config['fitParameterNbNumber'], unified=True),
                                self.xUnits,
                                parse_number(p['qi'].value, config['fitParameterNbNumber'], unified=True),
                                parse_number(p['qc'].value, config['fitParameterNbNumber'], unified=True))








class LorentzianPeak(Fit1d):

    displayedLabel = 'Lorentzian peak'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = \frac{I}{ 1+ \left(\frac{x-x_0}{\delta_\mathrm{FWHM}/2}\right)^2} + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background   = np.mean(np.sort(self.yData)[:10])
        center       = self.xData[np.argmax(self.yData)]
        height       = np.mean(np.sort(self.yData)[-2:])
        intersection = (height+background)/2
        c1           = np.abs(self.yData[:np.abs(self.yData - height).argmin()]-intersection).argmin()
        c2           = np.abs(self.yData[np.abs(self.yData - height).argmin()+1:]-intersection).argmin()+np.abs(self.yData - height).argmin()+1
        fwhm         = self.xData[c2]-self.xData[c1]
        height       -= background

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('center', center, True, None, None)
        params.add('fwhm', fwhm, True, 0, None)
        params.add('height', height, True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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

        # Unsure about the FWHM
        sigma = p['fwhm']/2
        a = p['height']*sigma
        dx = (x - p['center'])
        y = a*sigma/(dx**2 + sigma**2)

        return y+p['background']



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

        return 'background={}{}<br/>'\
               'center    ={}{}<br/>'\
               'fwhm      ={}{}<br/>'\
               'height    ={}{}'.format(parse_number(p['background'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits,
                                        parse_number(p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(p['fwhm'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(p['height'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits)






class LorentzianDip(Fit1d):

    displayedLabel = 'Lorentzian dip'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = 1 - \frac{I}{ 1+ \left(\frac{x-x_0}{\delta_\mathrm{FWHM}/2}\right)^2} + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background   = np.mean(np.sort(self.yData)[-10:])
        center       = self.xData[np.argmin(self.yData)]
        height       = np.mean(np.sort(self.yData)[:2])
        intersection = (height+background)/2
        c1           = np.abs(self.yData[:np.abs(self.yData - height).argmin()]-intersection).argmin()
        c2           = np.abs(self.yData[np.abs(self.yData - height).argmin()+1:]-intersection).argmin()+np.abs(self.yData - height).argmin()+1
        fwhm         = self.xData[c2]-self.xData[c1]
        height       = abs(height)
        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('center', center, True, None, None)
        params.add('fwhm', fwhm, True, 0, None)
        params.add('height', height, True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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

        # Unsure about the FWHM
        sigma = p['fwhm']/2
        a = p['height']*sigma
        dx = (x - p['center'])
        y = a*sigma/(dx**2 + sigma**2)

        return p['background'] - y



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

        return 'background={}{}<br/>'\
               'center    ={}{}<br/>'\
               'fwhm      ={}{}<br/>'\
               'height    ={}{}'.format(parse_number(p['background'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits,
                                        parse_number(p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(p['fwhm'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(p['height'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits)




class GaussianPeak(Fit1d):

    displayedLabel = 'Gaussian peak'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r'y = A \exp \left(-\frac{\left(x-x_0\right)^2}{2\sigma^2}\right) + B'

        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits)

    @staticmethod
    def fwhm2sigma(fwhm: lmfit.parameter.Parameters) -> float:
        """
        Return the FWHM from the standard deviation
        """
        return fwhm.value/2.3548


    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background   = np.mean(np.sort(self.yData)[:10])
        center       = self.xData[np.argmax(self.yData)]
        height       = np.mean(np.sort(self.yData)[-2:])
        intersection = (height+background)/2
        c1           = np.abs(self.yData[:np.abs(self.yData - height).argmin()]-intersection).argmin()
        c2           = np.abs(self.yData[np.abs(self.yData - height).argmin()+1:]-intersection).argmin()+np.abs(self.yData - height).argmin()+1
        fwhm         = self.xData[c2]-self.xData[c1]
        height      -= background

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('center', center, True, None, None)
        params.add('fwhm', fwhm, True, 0, None)
        params.add('height', height, True, None, None)

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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

        # Unsure about the FWHM
        sigma = self.fwhm2sigma(p['fwhm'])
        a = p['height']#/sigma/2.5066282746310002
        dx = (x - p['center'])
        y = a*np.exp(-dx**2/2/sigma**2)

        return y+p['background']



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

        return 'background={}{}<br/>'\
               'center    ={}{}<br/>'\
               'fwhm      ={}{}<br/>'\
               'sigma     ={}{}<br/>'\
               'SNR       ={}  <br/>'\
               'height    ={}{}'.format(parse_number(p['background'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits,
                                        parse_number(p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(p['fwhm'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(self.fwhm2sigma(p['fwhm']), config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(self.fwhm2sigma(p['fwhm'])/p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        parse_number(p['height'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits)

class InterdotTunnelingFit(Fit1d):

    displayedLabel = 'Interdot Tunneling fit'


    def __init__(self, parent: QtWidgets.QDialog,
                       xData: np.ndarray,
                       yData: np.ndarray,
                       xUnits: str='',
                       yUnits: str='') -> None:


        self.fitType = '1d'
        self.getLatexEquation = r's = s_0 + A \frac{\epsilon-\epsilon_0}{\sqrt{(\epsilon-\epsilon_0)^2+4t^2}}\tanh \left( \frac{\sqrt{(\epsilon-\epsilon_0)^2+4t^2}}{2k_BT_e} \right)'
        # Formula from DOI: 10.1103/PhysRevLett.92.226801
        Fit1d.__init__(self, parent=parent,
                             xData=xData,
                             yData=yData,
                             xUnits=xUnits,
                             yUnits=yUnits,
                             method = 'powell')


    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background          = np.mean(self.yData)
        center              = self.xData[round(len(self.xData)/2)] # interdot in the middle of the scan
        amplitude           = (np.max(self.yData)-np.min(self.yData))*(1 if self.yData[5]<self.yData[-5] else -1)
        lever_arm           = 0.2 # 0.2 Germanium lever
        tunneling           = 8e-6 # 10GHz tunneling initial guess
        temperature         = 50e-3 # 50mK effective temperature

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('center', center, True, None, None)
        params.add('amplitude', amplitude, True, None, None)
        params.add('tunneling', tunneling, True, 0, None)
        params.add('temperature', temperature, False, 10e-3, 100e-3)
        params.add('lever_arm', lever_arm, False, 0, 1) # lever arm bonding between 0 and 1

        return params



    def func(self, p: lmfit.parameter.Parameters,
                   x: np.ndarray) -> np.ndarray:
        """
        Fit model

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


        a_0         = p['background']
        a           = p['amplitude']
        e0          = p['center']
        t           = p['tunneling']
        Te          = p['temperature']
        alpha       = p['lever_arm']
        dx          = (x - e0)*alpha
        omega       = np.sqrt(dx**2+4*t**2)
        k_b         = 8.617e-5 # eV/K
        y = a_0 + a * dx/omega*np.tanh(omega/(2*k_b*Te))

        return y



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

        return 'background      ={}{}<br/>'\
               'center          ={}{}<br/>'\
               'amplitude       ={}{}<br/>'\
               'tunneling       ={}{}<br/>'\
               'temperature    ={}{}'.format(parse_number(p['background'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits,
                                        parse_number(p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        self.xUnits,
                                        parse_number(p['amplitude'].value, config['fitParameterNbNumber'], unified=True),
                                        self.yUnits,
                                        # 1e6/4 used to convert eV --> GHz
                                        parse_number(p['tunneling'].value*1e6/4, config['fitParameterNbNumber'], unified=True),
                                        'GHz',
                                        parse_number(p['temperature'].value, config['fitParameterNbNumber'], unified=True),
                                        'K')

