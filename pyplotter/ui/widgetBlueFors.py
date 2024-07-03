from PyQt5 import QtWidgets, QtWidgets, QtCore
import os
import pandas as pd
from ..sources.functions import pandasTimestamp2Int

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()


class WidgetBlueFors(QtWidgets.QWidget):


    signalClearTableWidgetDatabase = QtCore.pyqtSignal()
    signalClearTableWidgetParameter = QtCore.pyqtSignal()
    signalClearSnapshot = QtCore.pyqtSignal()
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun = QtCore.pyqtSignal(str)
    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)

    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)

    signalUpdateProgressBar = QtCore.pyqtSignal(int, float, str)
    signalRemoveProgressBar = QtCore.pyqtSignal(int)
    signalFillTableWidgetParameter = QtCore.pyqtSignal(int, list, dict, dict, str, str, str, str, bool)
    signalLoadedDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QCheckBox, int, tuple, str, str, str, str, str, str, bool)

    def __init__(self, parent):
        """
        Class handling the reading of csv file.
        """

        super(WidgetBlueFors, self).__init__(parent)



    @QtCore.pyqtSlot(str, bool, int)
    def blueForsLoad(self, absPath: str,
                           doubleClick: bool,
                           progressBarId: int) -> None:

        folderName = os.path.basename(absPath)

        self.signalSendStatusBarMessage.emit('Loading {}'.format(folderName),
                                             'orange')

        # Clean GUI
        self.signalLineEditSnapshotEnabled.emit(False)
        self.signalLabelSnapshotEnabled.emit(False)
        self.signalClearTableWidgetDatabase.emit()
        self.signalClearTableWidgetParameter.emit()
        self.signalClearSnapshot.emit()
        self.signalUpdateLabelCurrentSnapshot.emit('')
        self.signalUpdateLabelCurrentRun.emit('')


        self.paramDependentList = []
        progress = 0.
        progressIteration = 1/22
        for file in sorted(os.listdir(absPath)):

            fileName = file[:-13]
            filePath = os.path.join(absPath, file)
            # We only show file handled by the plotter
            if fileName in config.keys():

                # Maxigauges file (all pressure gauges)
                if fileName=='maxigauge':

                    df = pd.read_csv(filePath,
                                     delimiter=',',
                                     names=['date', 'time',
                                         'ch1_name', 'ch1_void1', 'ch1_status', 'ch1_pressure', 'ch1_void2', 'ch1_void3',
                                         'ch2_name', 'ch2_void1', 'ch2_status', 'ch2_pressure', 'ch2_void2', 'ch2_void3',
                                         'ch3_name', 'ch3_void1', 'ch3_status', 'ch3_pressure', 'ch3_void2', 'ch3_void3',
                                         'ch4_name', 'ch4_void1', 'ch4_status', 'ch4_pressure', 'ch4_void2', 'ch4_void3',
                                         'ch5_name', 'ch5_void1', 'ch5_status', 'ch5_pressure', 'ch5_void2', 'ch5_void3',
                                         'ch6_name', 'ch6_void1', 'ch6_status', 'ch6_pressure', 'ch6_void2', 'ch6_void3',
                                         'void'],
                                     header=None)

                    x = pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S'))

                    for i in range(1, 7):

                        self.signalUpdateProgressBar.emit(progressBarId, progress, 'Downloading data: {:.0f}%'.format(progress*100))
                        progress += progressIteration

                        name = 'ch'+str(i)+'_pressure'
                        y = df[name].to_numpy()*1e-3
                        self.paramDependentList.append({'depends_on' : ['time'],
                                                        'name'  : config[fileName][name[:3]]['labelText'],
                                                        'label' : config[fileName][name[:3]]['labelText'],
                                                        'x' : x,
                                                        'y' : y,
                                                        'unit' : config[fileName][name[:3]]['labelUnits']})

                # Status file (compressor temperatures)
                elif fileName=='Status':

                    try:
                        # Old BlueFors log files
                        # 1. There is a space before the day
                        # 2. Column name are specific

                        df = pd.read_csv(
                            filePath,
                            delimiter=",",
                            names=[
                                "date",
                                "time",
                                "tvpower1_name",
                                "tvpower1_value",
                                "tvbearingtemp1_name",
                                "tvbearingtemp1_value",
                                "tvcontrollertemp1_name",
                                "tvcontrollertemp1_value",
                                "tvbodytemp1_name",
                                "tvbodytemp1_value",
                                "tvrot1_name",
                                "tvrot1_value",
                                "tvlife1_name",
                                "tvlife1_value",
                                "nxdsf_name",
                                "nxdsf_value",
                                "nxdsct_name",
                                "nxdsct_value",
                                "nxdst_name",
                                "nxdst_value",
                                "nxdsbs_name",
                                "nxdsbs_value",
                                "nxdstrs_name",
                                "nxdstrs_value",
                                "tc400errorcode_name",
                                "tc400errorcode_value",
                                "tc400ovtempelec_name",
                                "tc400ovtempelec_value",
                                "tc400ovtemppump_name",
                                "tc400ovtemppump_value",
                                "tc400setspdatt_name",
                                "tc400setspdatt_value",
                                "tc400pumpaccel_name",
                                "tc400pumpaccel_value",
                                "tc400commerr_name",
                                "tc400commerr_value",
                                "ctrl_pres_name",
                                "ctrl_pres_value",
                                "cpastate_name",
                                "cpastate_value",
                                "cparun_name",
                                "cparun_value",
                                "cpawarn_name",
                                "cpawarn_value",
                                "cpaerr_name",
                                "cpaerr_value",
                                "cpatempwi_name",
                                "cpatempwi_value",
                                "cpatempwo_name",
                                "cpatempwo_value",
                                "cpatempo_name",
                                "cpatempo_value",
                                "cpatemph_name",
                                "cpatemph_value",
                                "cpalp_name",
                                "cpalp_value",
                                "cpalpa_name",
                                "cpalpa_value",
                                "cpahp_name",
                                "cpahp_value",
                                "cpahpa_name",
                                "cpahpa_value",
                                "cpadp_name",
                                "cpadp_value",
                                "cpacurrent_name",
                                "cpacurrent_value",
                                "cpahours_name",
                                "cpahours_value",
                                "cpapscale_name",
                                "cpapscale_value",
                                "cpatscale_name",
                                "cpatscale_value",
                                "cpasn_name",
                                "cpasn_value",
                                "cpamodel_name",
                                "cpamodel_value",
                            ],
                            header=None,
                        )
                        x = pandasTimestamp2Int(
                            pd.to_datetime(
                                df["date"] + "-" + df["time"],
                                format=" %d-%m-%y-%H:%M:%S",
                            )
                        )
                    except ValueError:
                        # Recent BlueFors log files
                        # 1. There is no space before the day
                        # 2. Column name are specific
                        df = pd.read_csv(
                            filePath,
                            delimiter=",",
                            names=[
                                "date",
                                "time",
                                "tvpower1_name",
                                "tvpower1_value",
                                "tvbearingtemp1_name",
                                "tvbearingtemp1_value",
                                "tvcontrollertemp1_name",
                                "tvcontrollertemp1_value",
                                "tvbodytemp1_name",
                                "tvbodytemp1_value",
                                "tvrot1_name",
                                "tvrot1_value",
                                "tvlife1_name",
                                "tvlife1_value",
                                "nxdsf_name",
                                "nxdsf_value",
                                "nxdsct_name",
                                "nxdsct_value",
                                "nxdst_name",
                                "nxdst_value",
                                "nxdsbs_name",
                                "nxdsbs_value",
                                "nxdstrs_name",
                                "nxdstrs_value",
                                "tc400errorcode_name",
                                "tc400errorcode_value",
                                "tc400ovtempelec_name",
                                "tc400ovtempelec_value",
                                "tc400ovtemppump_name",
                                "tc400ovtemppump_value",
                                "tc400setspdatt_name",
                                "tc400setspdatt_value",
                                "tc400pumpaccel_name",
                                "tc400pumpaccel_value",
                                "tc400commerr_name",
                                "tc400commerr_value",
                                "ctrl_pres_name",
                                "ctrl_pres_value",
                                "cpastate_name",
                                "cpastate_value",
                                "cparun_name",
                                "cparun_value",
                                "cpawarn_name",
                                "cpawarn_value",
                                "cpaerr_name",
                                "cpaerr_value",
                                "cpatempwi_name",
                                "cpatempwi_value",
                                "cpatempwo_name",
                                "cpatempwo_value",
                                "cpatempo_name",
                                "cpatempo_value",
                                "cpatemph_name",
                                "cpatemph_value",
                                "cpalp_name",
                                "cpalp_value",
                                "cpalpa_name",
                                "cpalpa_value",
                                "cpahp_name",
                                "cpahp_value",
                                "cpahpa_name",
                                "cpahpa_value",
                                "cpadp_name",
                                "cpadp_value",
                                "cpacurrent_name",
                                "cpacurrent_value",
                                "cpahours_name",
                                "cpahours_value",
                                "cpapscale_name",
                                "cpapscale_value",
                                "cpatscale_name",
                                "cpatscale_value",
                                "cpasn_name",
                                "cpasn_value",
                                "cpamodel_name",
                                "cpamodel_value",
                            ],
                            header=None,
                        )
                        x = pandasTimestamp2Int(
                            pd.to_datetime(
                                df["date"] + "-" + df["time"],
                                format="%d-%m-%y-%H:%M:%S",
                            )
                        )
                    except TypeError:
                        # Even more recent BlueFors log files
                        # 1. There is no space before the day
                        # 2. Column name are specific
                        df = pd.read_csv(
                            filePath,
                            delimiter=",",
                            names=[
                                'date',
                                'time',
                                'ctrl_pres_ok_name',
                                'ctrl_pres_ok_value',
                                'ctrl_pres_name',
                                'ctrl_pres_value',
                                'cpastate_name',
                                'cpastate_value',
                                'cparun_name',
                                'cparun_value',
                                'cpawarn_name',
                                'cpawarn_value',
                                'cpaerr_name',
                                'cpaerr_value',
                                'cpatempwi_name',
                                'cpatempwi_value',
                                'cpatempwo_name',
                                'cpatempwo_value',
                                'cpatempo_name',
                                'cpatempo_value',
                                'cpatemph_name',
                                'cpatemph_value',
                                'cpalp_name',
                                'cpalp_value',
                                'cpalpa_name',
                                'cpalpa_value',
                                'cpahp_name',
                                'cpahp_value',
                                'cpahpa_name',
                                'cpahpa_value',
                                'cpadp_name',
                                'cpadp_value',
                                'cpacurrent_name',
                                'cpacurrent_value',
                                'cpahours_name',
                                'cpahours_value',
                                'cpascale_name',
                                'cpascale_value',
                                'cpasn_name',
                                'cpasn_value',
                                'ctr_pressure_ok_name',
                                'ctr_pressure_ok_value',
                                'el302p_v_name',
                                'el302p_v_value',
                                'el302p_i_name',
                                'el302p_i_value',
                                'el302p_on_name',
                                'el302p_on_value',
                                'el302p_vo_name',
                                'el302p_vo_value',
                                'el302p_io_name',
                                'el302p_io_value',
                                'tc400actualspd_name',
                                'tc400actualspd_value',
                                'tc400ovtempelec_name',
                                'tc400ovtempelec_value',
                                'tc400ovtemppum_name',
                                'tc400ovtemppum_value',
                                'tc400heating_name',
                                'tc400heating_value',
                                'tc400pumpaccel_name',
                                'tc400pumpaccel_value',
                                'tc400pumpstatn_name',
                                'tc400pumpstatn_value',
                                'tc400remoteprio_name',
                                'tc400remoteprio_value',
                                'tc400spdswptatt_name',
                                'tc400spdswptatt_value',
                                'tc400setspdatt_name',
                                'tc400setspdatt_value',
                                'tc400standby_name',
                                'tc400standby_value',
                                'tc400actualspd_2_name',
                                'tc400actualspd_2_value',
                                'tc400ovtempelec_2_name',
                                'tc400ovtempelec_2_value',
                                'tc400ovtemppum_2_name',
                                'tc400ovtemppum_2_value',
                                'tc400heating_2_name',
                                'tc400heating_2_value',
                                'tc400pumpaccel_2_name',
                                'tc400pumpaccel_2_value',
                                'tc400pumpstatn_2_name',
                                'tc400pumpstatn_2_value',
                                'tc400remoteprio_2_name',
                                'tc400remoteprio_2_value',
                                'tc400spdswptatt_2_name',
                                'tc400spdswptatt_2_value',
                                'tc400setspdatt_2_name',
                                'tc400setspdatt_2_value',
                                'tc400standby_2_name',
                                'tc400standby_2_value',
                            ],
                            header=None,
                        )
                        x = pandasTimestamp2Int(
                            pd.to_datetime(
                                df["date"] + "-" + df["time"],
                                format="%d-%m-%y-%H:%M:%S",
                            )
                        )

                    for key in config[fileName]:

                        self.signalUpdateProgressBar.emit(progressBarId, progress, 'Downloading data: {:.0f}%'.format(progress*100))
                        progress += progressIteration

                        df_column_name = key+'_value'
                        y = df[df_column_name].to_numpy()
                        self.paramDependentList.append({'depends_on' : ['time'],
                                                        'name'  : config[fileName][key]['labelText'],
                                                        'label' : config[fileName][key]['labelText'],
                                                        'x' : x,
                                                        'y' : y,
                                                        'unit' : config[fileName][key]['labelUnits']})

                else:

                    # Thermometers files
                    df = pd.read_csv(filePath,
                                     delimiter = ',',
                                     names     = ['date', 'time', 'y'],
                                     header    = None)

                    self.signalUpdateProgressBar.emit(progressBarId, progress, 'Downloading data: {:.0f}%'.format(progress*100))
                    progress += progressIteration

                    try:
                        # Old BlueFors log files
                        # There is a space before the day
                        x = pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S'))
                    except ValueError:
                        # Recent BlueFors log files
                        # There is no space before the day
                        x = pandasTimestamp2Int(pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S'))

                    y = df['y'].to_numpy()*1e-3

                    self.paramDependentList.append({'depends_on' : ['time'],
                                                    'name'  : config[fileName]['labelText'],
                                                    'label' : config[fileName]['labelText'],
                                                    'x' : x,
                                                    'y' : y,
                                                    'unit' : config[fileName]['labelUnits']})


        self.signalFillTableWidgetParameter.emit(0, # runId
                                                 self.paramDependentList, # dependentList,
                                                 {}, # snapshotDict,
                                                 {i['name'] : None for i in self.paramDependentList}, # shapes
                                                 '', # experimentName
                                                 '', # runName
                                                 absPath, # fileAbsPath
                                                 'bluefors', # dataType
                                                 doubleClick) # doubleClick

        self.signalRemoveProgressBar.emit(progressBarId)


    QtCore.pyqtSlot(str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)
    def loadData(self, curveId: str,
                       absPath: str,
                       dependentParamName: str,
                       plotRef: str,
                       plotTitle: str,
                       runId: int,
                       windowTitle: str,
                       cb: QtWidgets.QCheckBox,
                       progressBarId: int) -> None:

        self.signalUpdateProgressBar.emit(progressBarId, 100., 'Downloading data: 100%')

        xLabelText  = 'Time'
        xLabelUnits = ''
        zLabelText  = ''
        zLabelUnits = ''

        for paramDependent in self.paramDependentList:
            if paramDependent['name'] == dependentParamName:
                data = (paramDependent['x'], paramDependent['y'])
                yLabelText  = paramDependent['label']
                yLabelUnits = paramDependent['unit']

        self.signalLoadedDataFull.emit(runId,
                                       curveId,
                                       plotTitle,
                                       windowTitle,
                                       plotRef,
                                       absPath,
                                       cb,
                                       progressBarId,
                                       data,
                                       xLabelText,
                                       xLabelUnits,
                                       yLabelText,
                                       yLabelUnits,
                                       zLabelText,
                                       zLabelUnits,
                                       True) # pg.DateAxisItem
