# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import lmfit
from scipy.signal import hilbert
from typing import Tuple, Union

from .config import config
from .functions import _parse_number




class FitReportWindow(QtWidgets.QDialog):



    def __init__(self, report: str) -> None:
        """
        QDialog window launched when fit is done.
        Display lmfit report.

        Parameters
        ----------
        report : str
            lmfit report.
        """

        QtWidgets.QDialog.__init__(self)


        label = QtWidgets.QLabel(report)
        label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        label.installEventFilter(self)
        self.setMinimumSize(200, 200)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

        self.setGeometry(1000, 30, 300, 100)
        self.setWindowTitle('Fit results')
        label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.show()



    def eventFilter(self, obj  : QtWidgets.QLabel,
                          event: Union[QtGui.QHoverEvent,
                                 QtGui.QPaintEvent,
                                 QtCore.QEvent]) -> bool:
        """
        Filter event happening on the FitReportWindow.
        Return True when event is of the type QtCore.QEvent.Enter and False
        when of the type QtCore.QEvent.Leave

        Parameters
        ----------
        obj : QtWidgets.QLabel
            QLabel of the lmfit report.
        event : Union[QtGui.QHoverEvent, QtGui.QPaintEvent, QtCore.QEvent]
            Event happening on the QLabel
        """

        if event.type()==QtCore.QEvent.Enter:

            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
            return True
        elif event.type()==QtCore.QEvent.Leave:

            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        return False





####################################
#
#           1D
#
####################################



class Fit1d(object):



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:
        """

        Parameters
        ----------
        x_data : np.ndarray
            Selected data from the x axis.
        y_data : np.ndarray
            Selected data from the y axis.
        """

        self.x_data      = x_data
        self.y_data      = y_data
        self.x_units     = x_units
        self.y_units     = y_units



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

        return self.func(p, self.x_data) - self.y_data



    def ffit(self) -> Tuple[np.ndarray, np.ndarray, lmfit.parameter.Parameters, FitReportWindow]:
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
        fitReportWindow : QtWidgets.QDialog
            QDialog displaying lmfit report.
        """

        result = lmfit.minimize(self.residual, self.getInitialParams())
        dx = np.gradient(self.x_data)/2.
        x = np.sort(np.concatenate((self.x_data, self.x_data+dx)))

        self.fitReportWindow = FitReportWindow(lmfit.fit_report(result))

        return x, self.func(result.params, x), result.params, self.fitReportWindow



class T2Gaussian(Fit1d):



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:
        """

        Parameters
        ----------
        x_data : np.ndarray
            Selected data from the x axis.
        y_data : np.ndarray
            Selected data from the y axis.
        """


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'T2 gaussian'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # linearize the timescale
        x = np.linspace(self.x_data[0], self.x_data[-1], len(self.x_data))
        y = np.interp(x, self.x_data, self.y_data)

        # Guess initial value
        background = 0.
        amplitude = abs(np.max(y)-np.min(y))/2.
        phi = np.arccos(y[0]/(np.max(y) - np.min(y))/2.)
        i = 0
        while True:
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



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'T2'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """



        # linearize the timescale
        x = np.linspace(self.x_data[0], self.x_data[-1], len(self.x_data))
        y = np.interp(x, self.x_data, self.y_data)

        # Guess initial value
        background = 0.
        amplitude = abs(np.max(y)-np.min(y))/2.
        phi = np.arccos(y[0]/(np.max(y) - np.min(y))/2.)
        i = 0
        while True:
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



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'T1'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # linearize the timescale
        x = np.linspace(self.x_data[0], self.x_data[-1], len(self.x_data))
        y = np.interp(x, self.x_data, self.y_data)

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









class QubitZpa(Fit1d):



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'Qubit f0[GHz] zpa dependence'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('lq', 9e-9, True, None, None)
        params.add('cq', 90e-15, False, None, None)
        params.add('lga', 300e-12, False, None, None)
        params.add('qubit_mutual', 0.3, True, None, None)
        params.add('qubit_phi_offset', 0., True, None, None)

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


        def get_flux_from_qubit_pulse_amplitude(p, x):
            return x*p['qubit_mutual'] + p['qubit_phi_offset']

        def qubit_phase_drop(p, phi_ext):
            return np.pi*phi_ext

        def qubit_inductance(p, phi_ext):
            return p['lq']/np.abs(np.cos(phi_ext*np.pi))

        phi_qubit = get_flux_from_qubit_pulse_amplitude(p, x)
        lq = qubit_inductance(p, phi_qubit)

        return np.sqrt(1./(lq + p['lga'])/p['cq'])/2./np.pi/1e9



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


        x = np.linspace(-1, 1, 10000)
        fmax = np.max(self.func(p, x))

        return 'lga={:.{nbDecimal}e} pH<br/>lq={:.{nbDecimal}e} nH<br/>cq={:.{nbDecimal}e} fF<br/>mutual={:.{nbDecimal}e}<br/>phi offset={:.{nbDecimal}e}<br/>fmax(GHz)={:.{nbDecimal}e} GHz'.format(p['lga'].value, p['lq'].value, p['cq'].value, p['qubit_mutual'].value, p['qubit_phi_offset'].value, fmax, nbDecimal=config['fitParameterNbNumber'])












class ResonancePeakdB(Fit1d):



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'Resonance peak (dB)'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background = np.mean(np.sort(self.y_data)[-10:])
        f0 = self.x_data[np.argmax(self.y_data)]

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



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'Resonance dip (Barends paper) (dB)'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background = np.mean(self.y_data[-10:])
        f0 = self.x_data[np.argmin(self.y_data)]

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('background', background, True, None, None)
        params.add('f0', f0, True, None, None)
        params.add('qi', 1e3, True, None, None)
        params.add('qc', 1e3, True, None, None)
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
               'qc={}'.format(_parse_number(p['f0'].value, config['fitParameterNbNumber'], unified=True),
                                self.x_units,
                                _parse_number(p['qi'].value, config['fitParameterNbNumber'], unified=True),
                                _parse_number(p['qc'].value, config['fitParameterNbNumber'], unified=True))









class LorentzianPeak(Fit1d):



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'Lorentzian peak'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background   = np.mean(np.sort(self.y_data)[:10])
        center       = self.x_data[np.argmax(self.y_data)]
        height       = np.mean(np.sort(self.y_data)[-2:])
        intersection = (height+background)/2
        c1           = np.abs(self.y_data[:np.abs(self.y_data - height).argmin()]-intersection).argmin()
        c2           = np.abs(self.y_data[np.abs(self.y_data - height).argmin()+1:]-intersection).argmin()+np.abs(self.y_data - height).argmin()+1
        fwhm         = self.x_data[c2]-self.x_data[c1]
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
               'height    ={}{}'.format(_parse_number(p['background'].value, config['fitParameterNbNumber'], unified=True),
                                        self.y_units,
                                        _parse_number(p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        self.x_units,
                                        _parse_number(p['fwhm'].value, config['fitParameterNbNumber'], unified=True),
                                        self.x_units,
                                        _parse_number(p['height'].value, config['fitParameterNbNumber'], unified=True),
                                        self.y_units)







class LorentzianDip(Fit1d):



    def __init__(self, x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_units: str='',
                       y_units: str='') -> None:


        self.fitType = '1d'
        Fit1d.__init__(self, x_data, y_data, x_units, y_units)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'Lorentzian dip'



    def getInitialParams(self) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """


        # Guess initial value
        background   = np.mean(np.sort(self.y_data)[-10:])
        center       = self.x_data[np.argmin(self.y_data)]
        height       = np.mean(np.sort(self.y_data)[:2])
        intersection = (height+background)/2
        c1           = np.abs(self.y_data[:np.abs(self.y_data - height).argmin()]-intersection).argmin()
        c2           = np.abs(self.y_data[np.abs(self.y_data - height).argmin()+1:]-intersection).argmin()+np.abs(self.y_data - height).argmin()+1
        fwhm         = self.x_data[c2]-self.x_data[c1]
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
               'height    ={}{}'.format(_parse_number(p['background'].value, config['fitParameterNbNumber'], unified=True),
                                        self.y_units,
                                        _parse_number(p['center'].value, config['fitParameterNbNumber'], unified=True),
                                        self.x_units,
                                        _parse_number(p['fwhm'].value, config['fitParameterNbNumber'], unified=True),
                                        self.x_units,
                                        _parse_number(p['height'].value, config['fitParameterNbNumber'], unified=True),
                                        self.y_units)


####################################
#
#           2D
#           TODO: Make it work with the new plot2dApp
#
####################################



class Fit2d(object):



    def __init__(self, x_data, y_data, z_data):

        self.x_data      = x_data
        self.y_data      = y_data
        self.z_data      = z_data



    def getFitType(self) -> str:
        """
        Return the fitType, either 1d or 2d.
        """

        return self.fitType



    def residual(self, p: lmfit.parameter.Parameters,
                       x: np.ndarray,
                       y: np.ndarray) -> np.ndarray:
        """
        Return the error between the model and the data.

        Parameters
        ----------
        p : lmfit.parameter.Parameters
            Fit parameters
        x : np.ndarray
            Selected data from the x axis.
        y : np.ndarray
            Selected data from the y axis.

        Returns
        -------
        np.ndarray
            Error between the model and the data.
        """

        y_model = self.func(p, x)
        if np.any(np.isnan(y_model)):
            return np.ones_like(y)
        else:
            return y_model - y



    def ffit(self):
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
        fitReportWindow : QtWidgets.QDialog
            QDialog displaying lmfit report.
        """

        t1s = np.array([])
        for z in self.z_data:
            p0 = self.getInitialParams(z[~np.isnan(z)])

            result = lmfit.minimize(self.residual, p0, args=[self.y_data[~np.isnan(z)], z[~np.isnan(z)]])

            t1s = np.append(t1s, result.params['t1'].value)

        return self.x_data, t1s




class T12d(Fit2d):



    def __init__(self, x_data, y_data, z_data=None):


        self.fitType = '2d'
        Fit2d.__init__(self, x_data, y_data, z_data)



    def displayedLabel(self) -> str:
        """
        Fit model label shown in the Plot1dApp GUI.

        Returns
        -------
        label : str
            Fit model label shown in the Plot1dApp GUI.
        """

        return 'T1'



    def getInitialParams(self, z) -> lmfit.parameter.Parameters:
        """
        Guess fit initial parameter from the selected x and y data.

        Returns
        -------
        lmfit.parameter.Parameters
            Guest fit parameters
        """

        # linearize the timescale
        x = np.linspace(self.y_data[0], self.y_data[-1], len(self.y_data))
        y = np.interp(x, self.y_data, z)

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


    def yLabel(self):
        return 'T1'