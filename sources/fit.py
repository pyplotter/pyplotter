# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import lmfit
from scipy.signal import hilbert






class SecondWindow(QtGui.QDialog):



    def __init__(self, parent, report):

        QtGui.QDialog.__init__(self, parent)

        
        label = QtWidgets.QLabel(report)
        label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        label.installEventFilter(self)
        self.setMinimumSize(200, 200)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

        self.setGeometry(1000, 30, 300, 100)
        self.setWindowTitle('Fit results')
        label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.show()



    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Enter:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
            return True
        elif event.type() == QtCore.QEvent.Leave:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        return False





####################################
#
#           1D
#
####################################



class Fit1d(object):



    def __init__(self, parent, x_data, y_data):

        self.parent      = parent
        self.x_data      = x_data
        self.y_data      = y_data



    def getFitType(self):
        return self.fitType



    def residual(self, p):

        return self.func(p, self.x_data) - self.y_data



    def ffit(self):

        result = lmfit.minimize(self.residual, self.get_initial_params())
        dx = np.gradient(self.x_data)/2.
        x = np.sort(np.concatenate((self.x_data, self.x_data+dx)))
        
        self.childWindow = SecondWindow(self.parent, lmfit.fit_report(result))

        return x, self.func(result.params, x), result.params, self.childWindow



class T2Gaussian(Fit1d):



    def __init__(self, parent, x_data, y_data):


        self.fitType = '1d'
        Fit1d.__init__(self, parent, x_data, y_data)



    def checkBoxLabel(self):
        return 'T2 gaussian'



    def get_initial_params(self):


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
        params.add('t2_g',       t2, True, None, None)
        params.add('phi',        phi, True, None, None)
        params.add('background', background, True, None, None)

        return params



    def func(self, p, x):

        return p['amplitude']*(1.-np.cos(2.*np.pi*x/p['period']+p['phi'])*np.exp(-x/p['t2']-(x/p['t2_g'])**2.)) + p['background']



    def legend2display(self, p):

        return 'T2='+str(round(p['t2'].value, 3))+', T2g='+str(round(p['t2_g'].value, 3))










class T2(Fit1d):



    def __init__(self, parent, x_data, y_data):


        self.fitType = '1d'
        Fit1d.__init__(self, parent, x_data, y_data)



    def checkBoxLabel(self):
        return 'T2'



    def get_initial_params(self):


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



    def func(self, p, x):

        return p['amplitude']*(1.-np.cos(2.*np.pi*x/p['period']+p['phi'])*np.exp(-x/p['t2'])) + p['background']



    def legend2display(self, p):

        return 'T2='+str(round(p['t2'].value, 3))










class T11d(Fit1d):



    def __init__(self, parent, x_data, y_data):


        self.fitType = '1d'
        Fit1d.__init__(self, parent, x_data, y_data)



    def checkBoxLabel(self):
        return 'T1'



    def get_initial_params(self):

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



    def func(self, p, x):
        return p['amplitude']*np.exp(-x/p['t1']) + p['background']



    def legend2display(self, p):

        return 'T1='+str(round(p['t1'].value, 3))










class QubitZpa(Fit1d):



    def __init__(self, parent, x_data, y_data):


        self.fitType = '1d'
        Fit1d.__init__(self, parent, x_data, y_data)



    def checkBoxLabel(self):
        return 'Qubit f0[GHz] zpa dependence'



    def get_initial_params(self):

        # Guess initial value

        params = lmfit.Parameters()
        # add with tuples: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
        params.add('lq', 9e-9, True, None, None)
        params.add('cq', 90e-15, False, None, None)
        params.add('lga', 300e-12, False, None, None)
        params.add('qubit_mutual', 0.3, True, None, None)
        params.add('qubit_phi_offset', 0., True, None, None)

        return params



    def func(self, p, x):

        def get_flux_from_qubit_pulse_amplitude(p, x):
            return x*p['qubit_mutual'] + p['qubit_phi_offset']

        def qubit_phase_drop(p, phi_ext):
            return np.pi*phi_ext

        def qubit_inductance(p, phi_ext):
            return p['lq']/np.abs(np.cos(phi_ext*np.pi))

        phi_qubit = get_flux_from_qubit_pulse_amplitude(p, x)
        lq = qubit_inductance(p, phi_qubit)

        return np.sqrt(1./(lq + p['lga'])/p['cq'])/2./np.pi/1e9

    def legend2display(self, p):
        
        x = np.linspace(-1, 1, 10000)
        fmax = np.max(self.func(p, x))

        return 'lga='+str(round(p['lga'].value*1e12, 0))+' pH, lq='+str(round(p['lq'].value*1e9, 2))+' nH, cq='+str(round(p['cq'].value*1e15, 0))+' fF, mutual='+str(round(p['qubit_mutual'].value, 3))+', phi offset='+str(round(p['qubit_phi_offset'].value, 3))+', fmax(GHz)='+str(round(fmax, 3))+' GHz'











class ResonancePeakdB(Fit1d):



    def __init__(self, parent, x_data, y_data):


        self.fitType = '1d'
        Fit1d.__init__(self, parent, x_data, y_data)



    def checkBoxLabel(self):
        return 'Purcell filter (dB)'



    def get_initial_params(self):

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



    def func(self, p, x):

        dx = (x - p['f0'])/p['f0']
        y = 1.-1./(1. + p['qi']/p['qc']*np.exp(1j*p['phi'])/(1. + 2j*p['qi']*dx))

        return 20.*np.log10(np.abs(y))+p['background']



    def legend2display(self, p):

        return 'f0='+str(round(p['f0'].value, 5))+', qi='+str(int(np.ceil(p['qi'].value)))+', qc='+str(int(np.ceil(p['qc'].value)))










class ResonanceDipdB(Fit1d):



    def __init__(self, parent, x_data, y_data):


        self.fitType = '1d'
        Fit1d.__init__(self, parent, x_data, y_data)



    def checkBoxLabel(self):
        return 'Resonance dip (Barends paper) (dB)'



    def get_initial_params(self):

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



    def func(self, p, x):

        dx = (x - p['f0'])/p['f0']
        y = 1./(1. + p['qi']/p['qc']*np.exp(1j*p['phi'])/(1. + 2j*p['qi']*dx))

        return 20.*np.log10(np.abs(y))+ p['background']



    def legend2display(self, p):

        return 'f0='+str(round(p['f0'].value, 5))+', qi='+str(int(np.ceil(p['qi'].value)))+', qc='+str(int(np.ceil(p['qc'].value)))



####################################
#
#           2D
#
####################################



class Fit2d(object):



    def __init__(self, parent, x_data, y_data, z_data):

        self.parent      = parent
        self.x_data      = x_data
        self.y_data      = y_data
        self.z_data      = z_data



    def getFitType(self):
        return self.fitType



    def residual(self, p, x, y):
        y_model = self.func(p, x)
        if np.any(np.isnan(y_model)):
            return np.ones_like(y)
        else:
            return y_model - y



    def ffit(self):

        t1s = np.array([])
        for z in self.z_data:
            p0 = self.get_initial_params(z[~np.isnan(z)])

            result = lmfit.minimize(self.residual, p0, args=[self.y_data[~np.isnan(z)], z[~np.isnan(z)]])

            t1s = np.append(t1s, result.params['t1'].value)

        return self.x_data, t1s




class T12d(Fit2d):



    def __init__(self, parent, x_data, y_data, z_data=None):


        self.fitType = '2d'
        Fit2d.__init__(self, parent, x_data, y_data, z_data)



    def checkBoxLabel(self):
        return 'T1'



    def get_initial_params(self, z):
        
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



    def func(self, p, x):
        return p['amplitude']*np.exp(-x/p['t1']) + p['background']



    def legend2display(self, p):

        return 'T1='+str(round(p['t1'].value, 3))

    def yLabel(self):
        return 'T1'