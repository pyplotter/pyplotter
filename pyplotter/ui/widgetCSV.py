from PyQt5 import QtWidgets, QtCore
import os
from typing import Union
import pandas as pd
from skrf import Touchstone # To easily read s2p file
import numpy as np

# There is a bug in the original Touchstone io function so while they accept our
# patch we override their function by ours.
def get_sparameter_data(self, format='ri'):
    """
    Get the data of the s-parameter with the given format.

    Parameters
    ----------
    format : str
        Format: ri, ma, db, orig

    supported formats are:
        orig:  unmodified s-parameter data
        ri:    data in real/imaginary
        ma:    data in magnitude and angle (degree)
        db:    data in log magnitude and angle (degree)

    Returns
    -------
    ret: list
        list of numpy.arrays

    """
    ret = {}
    if format == 'orig':
        values = self.sparameters
    else:
        values = self.sparameters.copy()
        # use frequency in hz unit
        values[:,0] = values[:,0]*self.frequency_mult
        if (self.format == 'db') and (format == 'ma'):
            values[:,1::2] = 10**(values[:,1::2]/20.0)
        elif (self.format == 'db') and (format == 'ri'):
            v_complex = ((10**values[:,1::2]/20.0)
                            * np.exp(1j*np.pi/180 * values[:,2::2]))
            values[:,1::2] = np.real(v_complex)
            values[:,2::2] = np.imag(v_complex)
        elif (self.format == 'ma') and (format == 'db'):
            values[:,1::2] = 20*np.log10(values[:,1::2])
        elif (self.format == 'ma') and (format == 'ri'):
            v_complex = (values[:,1::2] * np.exp(1j*np.pi/180 * values[:,2::2]))
            values[:,1::2] = np.real(v_complex)
            values[:,2::2] = np.imag(v_complex)
        elif (self.format == 'ri') and (format == 'ma'):
            v_complex = values[:,1::2] + 1j* values[:,2::2]
            values[:,1::2] = np.absolute(v_complex)
            values[:,2::2] = np.angle(v_complex)*(180/np.pi)
        elif (self.format == 'ri') and (format == 'db'):
            v_complex = values[:,1::2] + 1j* values[:,2::2]
            values[:,1::2] = 20*np.log10(np.absolute(v_complex))
            values[:,2::2] = np.angle(v_complex)*(180/np.pi)

    for i,n in enumerate(self.get_sparameter_names(format=format)):
        ret[n] = values[:,i]

    # transpose Touchstone V1 2-port files (.2p), as the order is (11) (21) (12) (22)
    file_name_ending = self.filename.split('.')[-1].lower()
    if self.rank == 2 and file_name_ending == "s2p":
        swaps = [ k for k in ret if '21' in k]
        for s in swaps:
            true_s = s.replace('21', '12')
            ret[s], ret[true_s] = ret[true_s], ret[s]

    return ret


Touchstone.get_sparameter_data = get_sparameter_data


class WidgetCSV(QtWidgets.QWidget):


    signalClearTableWidgetDatabase = QtCore.pyqtSignal()
    signalClearTableWidgetParameter = QtCore.pyqtSignal()
    signalClearSnapshot = QtCore.pyqtSignal()
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun = QtCore.pyqtSignal(str)
    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)

    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)
    signalAddSnapshot = QtCore.pyqtSignal(dict)

    signalUpdateProgressBar = QtCore.pyqtSignal(int, float, str)
    signalRemoveProgressBar = QtCore.pyqtSignal(int)
    signalFillTableWidgetParameter = QtCore.pyqtSignal(int, list, dict, dict, str, str, str, str, bool)
    signalLoadedDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QCheckBox, int, tuple, str, str, str, str, str, str, bool)

    def __init__(self, parent):
        """
        Class handling the reading of csv file.
        """

        super(WidgetCSV, self).__init__(parent)


    @QtCore.pyqtSlot(str, bool, int)
    def csvLoad(self, fileAbsPath: str,
                      doubleClick: bool,
                      progressBarId: int) -> None:

        fileName = os.path.basename(fileAbsPath)

        self.signalSendStatusBarMessage.emit('Loading {}'.format(fileName),
                                             'orange')

        # Clean GUI
        self.signalLineEditSnapshotEnabled.emit(False)
        self.signalLabelSnapshotEnabled.emit(False)
        self.signalClearTableWidgetDatabase.emit()
        self.signalClearTableWidgetParameter.emit()
        self.signalClearSnapshot.emit()
        self.signalUpdateLabelCurrentSnapshot.emit('')
        self.signalUpdateLabelCurrentRun.emit('')

        # csv file
        if fileAbsPath[-3:].lower()=='csv':

            try:

                ## Guess comment character
                # We check if there is no comment on the csv file by guessing
                # if the first character of the first line is part of a float
                # number.
                # If there is comment c will contain the comment character
                # otherwise it will return None.
                f = open(fileAbsPath, 'r')
                c = f.readline()[0]
                f.close()
                if c.isnumeric() or c=='+' or c=='-':
                    comment = None
                else:
                    comment = c


                ## Determine the csv file header
                header: Union[None, int]=None
                if c is None:
                    header = None
                else:
                    f = open(fileAbsPath, 'r')
                    header = 0
                    d = f.readline()
                    while d[0]==comment:
                        d = f.readline()
                        header += 1
                f.close()

                ## Guess delimiter character
                f = open(fileAbsPath, 'r')
                d = f.readline()
                for i in range(9):
                    d += f.readline()
                f.close()
                delimiter = None
                if ',' in d:
                    delimiter = ','
                elif ';' in d:
                    delimiter = ';'
                else:
                    delimiter = ' '

                # Get the data as panda dataframe
                df = pd.read_csv(fileAbsPath, comment=comment, sep=delimiter, header=header)

                # Get the column name as string
                self.independentParameter = str(df.columns[0])
                columnsName = df.columns[1:].astype(str)

                x = df.values[:,0]
                ys = df.values.T[1:]
            except Exception as e:
                self.signalSendStatusBarMessage.emit("Can't open csv file: {}".format(e),
                                                    'red')
                return
        # s2p file
        else:

            try:
                ts = Touchstone(fileAbsPath)
                self.signalAddSnapshot.emit({'comment': ts.get_comments()})
                self.independentParameter = 'Frequency'
                columnsName = list(ts.get_sparameter_data('db').keys())[1:]
                x = ts.get_sparameter_data('db')['frequency']
                ys = [ts.get_sparameter_data('db')[i] for i in list(ts.get_sparameter_data('db').keys())[1:]]
            except Exception as e:
                self.signalSendStatusBarMessage.emit("Can't open s2p file: {}".format(e),
                                                    'red')
                return

        self.paramDependentList = []
        for columnName, y in zip(columnsName, ys):
            self.paramDependentList.append({'depends_on' : [''],
                                            'label' : columnName,
                                            'x' : x,
                                            'y' : y,
                                            'unit' : '',
                                            'name' : columnName})

        self.signalFillTableWidgetParameter.emit(0, # runId
                                                 self.paramDependentList, # dependentList,
                                                 {}, # snapshotDict,
                                                 {i['name'] : None for i in self.paramDependentList}, # shapes
                                                 '', # experimentName
                                                 '', # runName
                                                 fileAbsPath, # fileAbsPath
                                                 'csv', # dataType
                                                 doubleClick) # doubleClick

        self.signalRemoveProgressBar.emit(progressBarId)


    QtCore.pyqtSlot(str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)
    def loadData(self, curveId: str,
                       fileAbsPath: str,
                       dependentParamName: str,
                       plotRef: str,
                       plotTitle: str,
                       runId: int,
                       windowTitle: str,
                       cb: QtWidgets.QCheckBox,
                       progressBarId: int) -> None:

        self.signalUpdateProgressBar.emit(progressBarId, 100., 'Downloading data: 100%')

        for paramDependent in self.paramDependentList:
            if paramDependent['name'] == dependentParamName:
                data = (paramDependent['x'], paramDependent['y'])

        xLabelText  = self.independentParameter
        xLabelUnits = ''
        yLabelText  = dependentParamName
        yLabelUnits = ''
        zLabelText  = ''
        zLabelUnits = ''

        self.signalLoadedDataFull.emit(runId,
                                        curveId,
                                        plotTitle,
                                        windowTitle,
                                        plotRef,
                                        fileAbsPath,
                                        cb,
                                        progressBarId,
                                        data,
                                        xLabelText,
                                        xLabelUnits,
                                        yLabelText,
                                        yLabelUnits,
                                        zLabelText,
                                        zLabelUnits,
                                        False) # pg.DateAxisItem