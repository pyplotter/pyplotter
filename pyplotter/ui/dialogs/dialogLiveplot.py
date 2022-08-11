# This Python file uses the following encoding: utf-8
from __future__ import annotations
from PyQt5 import QtWidgets, QtCore, QtTest
import numpy as np
import os
from datetime import datetime
from typing import Tuple

from ...sources.workers.loadDataFromCache import LoadDataFromCacheThread
from .dialogLiveplotUi import Ui_LivePlot
from ...sources.qcodesDatabase import getNbTotalRunAndLastRunName, isRunCompleted
from ...sources.functions import (getDatabaseNameFromAbsPath,
                                  getCurveId,
                                  getWindowTitle,
                                  getPlotTitle,
                                  getPlotRef)


class DialogLiveplot(QtWidgets.QDialog, Ui_LivePlot):

    signal2MainWindowAddPlot = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)

    signalUpdateCurve = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
    signalUpdate2d = QtCore.pyqtSignal(str, np.ndarray, np.ndarray, np.ndarray)
    signalUpdatePlotProperty = QtCore.pyqtSignal(str, str, str)

    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)

    # Make mypy happy
    _livePlotRunId: int
    _livePlotPreviousDataLength: int
    _livePlotRunName: str
    _livePlotDatabaseAbsPath: str

    # We make mypy "happy" without loading qcodes lib (save time)
    _livePlotDataSet: DataSetProtocol # type: ignore

    def __init__(self, config: dict) -> None:

        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        # Allow resize of the plot window
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)

        self.config           = config

        # Connect events
        self.pushButtonLivePlot.clicked.connect(self.livePlotPushButton)
        self.spinBoxLivePlotRefreshRate.setValue(int(config['livePlotTimer']))
        self.spinBoxLivePlotRefreshRate.valueChanged.connect(self.livePlotSpinBoxChanged)

        self.threadpool = QtCore.QThreadPool()

        self.show()




    ###########################################################################
    #
    #
    #                           Live plotting
    #
    #
    ###########################################################################



    def livePlotClockUpdate(self):

        ## Update displayed information
        # Last time since we interogated the dataCache
        if self.labelLivePlotLastRefreshInfo.text()!='':
            datetimeLastUpdate = datetime.strptime(self.labelLivePlotLastRefreshInfo.text(), '%Y-%m-%d %H:%M:%S')
            t = ''
            hours, remainder = divmod((datetime.now()-datetimeLastUpdate).seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours>0:
                t += '{:02}H '.format(hours)
            if minutes>0:
                t += '{:02}min '.format(minutes)
            t += '{:02}s'.format(seconds)
            self.labelLivePlotSinceLastRefreshInfo.setText(t)


        # # New data since last time we interogate the dataCache?
        if self.labelLivePlotLastUpdateInfo.text()!='':
            datetimeLastUpdate = datetime.strptime(self.labelLivePlotLastUpdateInfo.text(), '%Y-%m-%d %H:%M:%S')
            t = ''
            hours, remainder = divmod((datetime.now()-datetimeLastUpdate).seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours>0:
                t += '{:02}H '.format(hours)
            if minutes>0:
                t += '{:02}min '.format(minutes)
            t += '{:02}s'.format(seconds)
            self.labelLivePlotSinceLastUpdateInfo.setText(t)



    @QtCore.pyqtSlot(str, str)
    def slotLiveplotMessage(self, message: str,
                                  color: str) -> None:

        self.labelLivePlotInfoInfo.setText('<span style="color: {};">{}</span>'.format(color, message))



    @QtCore.pyqtSlot(str, tuple, str, bool)
    def slotUpdatePlotData(self, plotRef        : str,
                                 data           : Tuple[np.ndarray, ...],
                                 yParamName     : str,
                                 lastUpdate     : bool) -> None:
        """
        Methods called in live plot mode to update plot.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getDataRef.
        data : tuple
            For 1d plot: (xData, yData)
            For 2d plot: (xData, yData, zData)
        yParamName : str
            Name of the y parameter.
        lastUpdate : bool
            True if this is the last update of the livePlot, a.k.a. the run is
            marked as completed by qcodes.
        """

        # Last time since we interogated the dataCache
        self.labelLivePlotLastRefreshInfo.setText('{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        # New data since last time we interogate the dataCache?
        if self._livePlotPreviousDataLength!=len(data[0]):

            self.labelLivePlotLastUpdateInfo.setText('{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            # 1d plot
            if len(data)==2:

                curveId = getCurveId(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                    name=yParamName,
                                    runId=self._livePlotRunId)

                self.signalUpdateCurve.emit(plotRef, # plotRef
                                            curveId, # curveId
                                            yParamName, # curveLegend
                                            data[0], # x
                                            data[1], # y
                                            self.checkBoxLiveplotAutorange.isChecked(), # autoRange
                                            True)  # interactionUpdateAll
            # 2d plot
            elif len(data)==3:

                self.signalUpdate2d.emit(plotRef,
                                         data[0],
                                         data[1],
                                         data[2])

        # If all curves have been updated
        for i, flag in enumerate(self._updatingFlag):
            if not flag:
                self._updatingFlag[i] = True
                break

        # We save the current data length for the next iteration
        if all(self._updatingFlag):
            if self._livePlotPreviousDataLength==len(data[0]):
                self.labelLivePlotInfoInfo.setText('<span style="color: red;">No new data in cache</span>')
            else:
                self.labelLivePlotInfoInfo.setText('<span style="color: green;">New data in cache plotted</span>')
            self._livePlotPreviousDataLength = len(data[0])

            # Display the current nb of data point
            if len(data)==2:
                nbPoint = len(data[0])
            elif len(data)==3:
                nbPoint = int(len(data[0])*len(data[1]))
            self.labelLivePlotNbPointInfo.setText(str(nbPoint))

        # We show to user the time of the last update
        if lastUpdate:
            # We mark all completed livePlot as not livePlot anymore
            plotTitle   = getPlotTitle(self._livePlotDatabaseAbsPath,
                                       self._livePlotRunId,
                                       self._livePlotRunName)
            self.signalUpdatePlotProperty.emit(plotRef, # plotRef
                                               'plotTitle', # property
                                               plotTitle) # value

            self.labelLivePlotInProgressState.setText('False')
            self.labelLivePlotRunidid.setText('')
            self.labelLivePlotRunNameInfo.setText('')
            self.labelLivePlotInfoInfo.setText('')
            self.labelLivePlotNbPointInfo.setText('')
            self.labelLivePlotLastUpdateInfo.setText('')
            self.labelLivePlotSinceLastUpdateInfo.setText('')
            self.labelLivePlotLastRefreshInfo.setText('')
            self.labelLivePlotSinceLastRefreshInfo.setText('')


    def livePlotGetPlotParameters(self) -> None:
        """
        Gather the information from the current live plot dataset and sort them
        into iterables.

        Each dependent parameters must be treated independently since they
        can each have a different number of independent parameters.
        """

        # Get dataset params
        paramsDependents   = [i for i in self._livePlotDataSet.get_parameters() if len(i.depends_on)!=0]

        xParamNames  = []
        xParamLabels = []
        xParamUnits  = []
        yParamNames  = []
        yParamLabels = []
        yParamUnits  = []
        zParamNames  = []
        zParamLabels = []
        zParamUnits  = []
        plotRefs     = []

        # We calculate how many livePlot we should have
        self._livePlotNbPlot  = 0
        plot1dNotAlreadyAdded = True

        for paramsDependent in paramsDependents:

            # For each dependent parameter we them the parameter(s) they depend
            # on.
            depends_on = [i for i in paramsDependent.depends_on.split(', ')]

            param_x = [param for param in self._livePlotDataSet.get_parameters() if param.name==depends_on[0]][0]
            xParamNames.append(param_x.name)
            xParamLabels.append(param_x.label)
            xParamUnits.append(param_x.unit)

            # For 2d plot
            if len(depends_on)>1:
                param_y = [param for param in self._livePlotDataSet.get_parameters() if param.name==depends_on[1]][0]
                yParamNames.append(param_y.name)
                yParamLabels.append(param_y.label)
                yParamUnits.append(param_y.unit)

                zParamNames.append(paramsDependent.name)
                zParamLabels.append(paramsDependent.label)
                zParamUnits.append(paramsDependent.unit)

                plotRefs.append(getPlotRef(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                           paramDependent={'depends_on' : [0, 1], 'name': paramsDependent.name},
                                           runId=self._livePlotRunId))
                self._livePlotNbPlot += 1
            # For 1d plot
            else:
                yParamNames.append(paramsDependent.name)
                yParamLabels.append(paramsDependent.label)
                yParamUnits.append(paramsDependent.unit)

                zParamNames.append('')
                zParamLabels.append('')
                zParamUnits.append('')

                plotRefs.append(getPlotRef(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                           paramDependent={'depends_on' : [0]},
                                           runId=self._livePlotRunId))
                # We only add 1 1dplot for all 1d curves
                if plot1dNotAlreadyAdded:
                    self._livePlotNbPlot += 1
                    plot1dNotAlreadyAdded = False

        self._livePlotGetPlotParameters = xParamNames, xParamLabels, xParamUnits, yParamNames, yParamLabels, yParamUnits, zParamNames, zParamLabels, zParamUnits, plotRefs



    def livePlotLaunchPlot(self) -> None:
        """
        Method called by the livePlotUpdate method.
        Obtain the info of the current live plot dataset cache, treat them and
        send them to the addPlot method.

        Each dependent parameters must be treated independently since they
        can each have a different number of independent parameters.
        """

        data: Tuple[np.ndarray, ...]

        #    1d.  We launch a plot window with all the dependent parameters
        #         plotted as plotDataItem.
        #    2d.  We launch as many plot window as dependent parameters.
        # Get dataset params
        paramsIndependent = [i for i in self._livePlotDataSet.get_parameters() if len(i.depends_on)==0]

        plotTitle   = getPlotTitle(self._livePlotDatabaseAbsPath,
                                   self._livePlotRunId,
                                   self._livePlotRunName) + self.config['livePlotTitleAppend']
        windowTitle = getWindowTitle(self._livePlotDatabaseAbsPath,
                                     self._livePlotRunId,
                                     self._livePlotRunName)

        # We get the liveplot parameters
        self.livePlotGetPlotParameters()

        for xParamName, xParamLabel, xParamUnit, yParamName, yParamLabel, yParamUnit, zParamName, zParamLabel, zParamUnit, plotRef in zip(*self._livePlotGetPlotParameters):
            # Only the first dependent parameter is displayed per default
            if yParamLabel==paramsIndependent[0].label:
                hidden = False
            else:
                hidden = True

            # Create empty data for the plot window launching
            if zParamLabel=='':
                data = (np.array([]),
                        np.array([]))
            else:
                data = (np.array([0., 1.]),
                        np.array([0., 1.]),
                        np.array([[0., 1.],
                                  [0., 1.]]))

            curveId = getCurveId(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                 name=yParamName,
                                 runId=self._livePlotRunId)

            self.signal2MainWindowAddPlot.emit(self._livePlotRunId, # runId
                                               curveId, # curveId
                                               plotTitle, # plotTitle
                                               windowTitle, # windowTitle
                                               plotRef, # plotRef
                                               self._livePlotDatabaseAbsPath, # databaseAbsPath
                                               data, # data
                                               xParamLabel, # xLabelText
                                               xParamUnit, # xLabelUnits
                                               yParamLabel, # yLabelText
                                               yParamUnit, # yLabelUnits
                                               zParamLabel, # zLabelText
                                               zParamUnit) # zLabelUnits



    def livePlotUpdatePlot(self, lastUpdate: bool=False) -> None:
        """
        Method called by livePlotUpdate.
        Obtain the info of the current live plot dataset cache, treat them and
        send them to the slotUpdatePlotData method.

        Parameters
        ----------
        lastUpdate : bool
            True if this is the last update of the livePlot, a.k.a. the run is
            marked as completed by qcodes.
        """

        # We show to user that the plot is being updated
        self.labelLivePlotInfoInfo.setText('<span style="color: orange;">Interrogating cache</span>')

        # Keep track of all the update we should do
        # The flags are False until the worker update them to True
        self._updatingFlag = []

        for xParamName, xParamLabel, xParamUnit, yParamName, yParamLabel, yParamUnit, zParamName, zParamLabel, zParamUnit, plotRef in zip(*self._livePlotGetPlotParameters):
            self._updatingFlag.append(False)
            worker = LoadDataFromCacheThread(plotRef,
                                             self._livePlotDataSet.cache.data(),
                                             xParamName,
                                             yParamName,
                                             zParamName,
                                             lastUpdate)

            worker.signal.dataLoaded.connect(self.slotUpdatePlotData)
            worker.signal.sendLivePlotInfoMessage.connect(self.slotLiveplotMessage)

            # Execute the thread
            self.threadpool.start(worker)



    def livePlotUpdate(self) -> None:
        """
        Method called periodically by a QTimer.
        1. Obtain the last runId of the livePlotDatabase
        2. If this run is not marked as completed, load its dataset and plot its
           parameters
        3. Update the plots until the run is marked completed
        4. When the run is completed, remove its dataset from memory
        """

        # We get the last run id of the database
        self._livePlotRunId, self._livePlotRunName = getNbTotalRunAndLastRunName(self._livePlotDatabaseAbsPath)

        # While the run is not completed, we update the plot
        if not isRunCompleted(self._livePlotDatabaseAbsPath, self._livePlotRunId):

            self.labelLivePlotInProgressState.setText('<span style="color: green;">True</span>')
            self.labelLivePlotRunidid.setText('{}'.format(self._livePlotRunId))
            self.labelLivePlotRunNameInfo.setText('{}'.format(self._livePlotRunName))
            self.labelLivePlotInfoInfo.setText('<span style="color: green;">New run detected</span>')

            ## 1. We get the livePlot dataset
            # We access the db only once.
            # The next iteration will access the cache of the dataset.
            if not hasattr(self, '_livePlotDataSet'):
                self._livePlotDataSet = self.loadDataset(captured_run_id=self._livePlotRunId)
            ## 2. If we do not see the attribute attached to the launched plot
            if not hasattr(self, '_livePlotGetPlotParameters'):

                self.livePlotLaunchPlot()
            ## 2. If the user closed some or every liveplot windows
            # elif len(self.getLivePlotRef())!=self._livePlotNbPlot:
            #     self.livePlotLaunchPlot()
            ## 3. If an active livePlot window is detected
            else:
                self.livePlotUpdatePlot()

        else:
            # If the livePlot has been completed since the last method's call
            if hasattr(self, '_livePlotDataSet'):

                self.livePlotUpdatePlot(lastUpdate=True)

                # Delete all liveplot attribute
                if hasattr(self, '_livePlotDataSet'):
                    del(self._livePlotDataSet)
                if hasattr(self, '_livePlotGetPlotParameters'):
                    del(self._livePlotGetPlotParameters)
                if hasattr(self, '_livePlotNbPlot'):
                    del(self._livePlotNbPlot)



    def livePlotSpinBoxChanged(self, val):
        """
        When user modify the spin box associated to the live plot timer.
        When val==0, stop the liveplot monitoring.
        """

        # If a Qt timer is running, we modify it following the user input.
        if hasattr(self, '_livePlotTimer'):

            # If the timer is 0, we stopped the liveplot
            if val==0:
                self._livePlotTimer.stop()
                self._livePlotTimer.deleteLater()
                del(self._livePlotTimer)

                self._livePlotClockTimer.stop()
                self._livePlotClockTimer.deleteLater()
                del(self._livePlotClockTimer)

                # self.labelLivePlotDataBase.setText('')
                # self.groupBoxLivePlot.setStyleSheet('QGroupBox:title{color: white}')
                self.pushButtonLivePlot.setText('Select database')
                self.labelLivePlotInProgressState.setText('')
                self.labelLivePlotRunidid.setText('')
                self.labelLivePlotRunNameInfo.setText('')
                self.labelLivePlotDatabasePathInfo.setText('')
                self.labelLivePlotDatabaseNameInfo.setText('')
                self.labelLivePlotLastUpdateInfo.setText('')
                self.labelLivePlotSinceLastUpdateInfo.setText('')
                self.labelLivePlotLastRefreshInfo.setText('')
                self.labelLivePlotSinceLastRefreshInfo.setText('')
                if hasattr(self, '_livePlotDatabaseAbsPath'):
                    del(self._livePlotDatabaseAbsPath)
                if hasattr(self, '_livePlotDataSet'):
                    del(self._livePlotDataSet)
            else:
                self._livePlotTimer.setInterval(val*1000)



    def livePlotPushButton(self) -> None:
        """
        Call when user click on the 'LivePlot' button.
        Allow user to chose any available qcodes database in his computer.
        This database will be monitored and any new run will be plotted.
        """

        self.pushButtonLivePlot.setText('Loading QCoDeS...')
        # self.setStatusBarMessage()
        QtTest.QTest.qWait(100)
        from qcodes import initialise_or_create_database_at, load_by_run_spec
        self.pushButtonLivePlot.setText('Select database...')
        self.loadDataset = load_by_run_spec
        # self.setStatusBarMessage('Ready')

        fname = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Open QCoDeS database',
                                                      self.config['path'],
                                                      'QCoDeS database (*.db).')

        if fname[0]!='':
            self._livePlotDatabaseAbsPath = os.path.abspath(fname[0])
            self._livePlotDataBaseName = getDatabaseNameFromAbsPath(fname[0])

            initialise_or_create_database_at(self._livePlotDatabaseAbsPath)
            self._livePlotPreviousDataLength = 0

            self.labelLivePlotDatabasePathInfo.setText('{}'.format(self._livePlotDatabaseAbsPath))
            self.labelLivePlotDatabaseNameInfo.setText('{}'.format(self._livePlotDataBaseName))

            # We call the liveplot function once manually to be sure it has been
            # initialized properly
            self.livePlotUpdate()

            # Launch a Qt timer which will periodically check if a new run is
            # launched
            # If the user disable the livePlot previously
            if self.spinBoxLivePlotRefreshRate.value()==0:
                self.spinBoxLivePlotRefreshRate.setValue(1)

            self._livePlotTimer = QtCore.QTimer()
            self._livePlotTimer.timeout.connect(self.livePlotUpdate)
            self._livePlotTimer.setInterval(self.spinBoxLivePlotRefreshRate.value()*1000)
            self._livePlotTimer.start()

            self._livePlotClockTimer = QtCore.QTimer()
            self._livePlotClockTimer.timeout.connect(self.livePlotClockUpdate)
            self._livePlotClockTimer.setInterval(1000)
            self._livePlotClockTimer.start()

        self.pushButtonLivePlot.setText('Modify database')
