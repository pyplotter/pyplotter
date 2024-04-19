from __future__ import annotations
from PyQt5 import QtWidgets, QtCore
from idna import check_bidi
import numpy as np
import os
from datetime import datetime
from typing import Tuple

from ...sources.workers.loadDataFromCache import LoadDataFromCacheThread
from ...sources.workers.loadLabradDataFromCache import LoadLabradDataFromCacheThread
from .dialogLiveplotUi import Ui_LivePlot
from ...sources.qcodesDatabase import getNbTotalRunAndLastRunName, isRunCompleted
from ...sources.labradDatavault import (
    dep_name,
    switch_session_path,
    getNbTotalRunAndLastRunNameLabrad,
    isRunCompletedLabrad,
    check_busy_datasets,
)
from ...sources.functions import (
    getDatabaseNameFromAbsPath,
    getCurveId,
    getWindowTitle,
    getPlotTitle,
    getPlotRef,
    getDialogWidthHeight,
    getParallelDialogWidthHeight,
    MAX_LIVE_PLOTS,
    isLabradFolder,
    plotIdGenerator,
)

class DialogLiveplot(QtWidgets.QDialog, Ui_LivePlot):

    ## Signal to the mainWindow to
    # Add plot
    signalAddLivePlot = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str, int, int, int, int)
    signalCloseLivePlot = QtCore.pyqtSignal(tuple, bool, tuple)

    # Update a 1d plotDataItem
    signalUpdate1d = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
    # Update a 2d ImageView
    signalUpdate2d = QtCore.pyqtSignal(str, np.ndarray, np.ndarray, np.ndarray)
    # Update the plot dialog title when the measurement is done
    signalUpdatePlotProperty = QtCore.pyqtSignal(str, str, str)

    # Make mypy happy
    _livePlotRunId: int
    _livePlotPreviousDataLength: int
    _livePlotRunName: str
    _livePlotDatabaseAbsPath: str

    # list for parallel live plots
    # aims to tile the screen with MAX_LIVE_PLOTS windows that show recent new runs
    livePlotRunIds: list
    livePlotPreviousDataLengths: list
    livePlotRunNames: list

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
        self.pushButtonMenu = QtWidgets.QMenu()
        self.pushButtonMenu.addAction('Database File', self.livePlotPushButton)
        self.pushButtonMenu.addAction('Database Folder', self.livePlotPushButtonFolder)
        self.pushButtonLivePlot.setMenu(self.pushButtonMenu)
        # self.pushButtonLivePlot.clicked.connect(self.livePlotPushButton)
        self.spinBoxLivePlotRefreshRate.setValue(int(config['livePlotTimer']))
        self.spinBoxLivePlotRefreshRate.valueChanged.connect(self.livePlotSpinBoxChanged)

        self.threadpool = QtCore.QThreadPool()
        self.threadpools = [QtCore.QThreadPool() for i in range(MAX_LIVE_PLOTS)]
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


    def slotUpdatePlot(self,     plotRef        : str,
                                 data           : Tuple[np.ndarray, ...],
                                 yParamName     : str,
                                 lastUpdate     : bool,
                                 lastDependent  : bool=False,
                                 plotId         : int=-1) -> None:
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
        if plotId != -1:
            self._livePlotRunId =  self.livePlotRunIds[plotId]
            self._livePlotRunName = self.livePlotRunNames[plotId]
            self._livePlotPreviousDataLength = self.livePlotPreviousDataLengths[plotId]

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

                self.signalUpdate1d.emit(plotRef, # plotRef
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

        if lastDependent and plotId != -1:
            self.livePlotPreviousDataLengths[plotId] = len(data[0])

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


    def is2dPlot(self, livePlotGetPlotParameter)  :
        if livePlotGetPlotParameter[6][0]:
            return True
        else:
            return False


    def genCurveIds(self, livePlotGetPlotParameter, livePlotRunIds):
        curveIds = []
        for yParamName in livePlotGetPlotParameter[3]:
            curveId = getCurveId(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                 name=yParamName,
                                 runId=livePlotRunIds)
            curveIds.append(curveId)
        return curveIds


    def isDataBusy(self, livePlotRunName):
        if isLabradFolder(self._livePlotDatabaseAbsPath):
            if not hasattr(self, 'session'):
                self.session = switch_session_path(self._livePlotDatabaseAbsPath)
            return check_busy_datasets(self.session, [livePlotRunName])[0]
        elif isMongoDBFolder(self._livePlotDatabaseAbsPath):
            return False
        

    ###########################################################################
    #                           Qcodes plotting
    ###########################################################################


    @QtCore.pyqtSlot(str, tuple, str, bool)
    def slotUpdatePlotData(self, 
                           plotRef        : str,
                           data           : Tuple[np.ndarray, ...],
                           yParamName     : str,
                           lastUpdate     : bool) -> None:
        self.slotUpdatePlot(plotRef, data, yParamName, lastUpdate)


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

        # We get the dialog position and size to tile the screen
        dialogTilings = getDialogWidthHeight(nbDialog=len(self._livePlotGetPlotParameters[0]))

        for (xParamName, xParamLabel, xParamUnit,
             yParamName, yParamLabel, yParamUnit,
             zParamName, zParamLabel, zParamUnit,
             plotRef,
             dialogX, dialogY,
             dialogWidth, dialogHeight) in zip(*self._livePlotGetPlotParameters,
                                                 *dialogTilings):
            # Only the first dependent parameter is displayed per default
            if yParamLabel==paramsIndependent[0].label:
                hidden = False
            else:
                hidden = True

            # Create empty data for the plot window launching
            if zParamName=='':
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

            self.signalAddLivePlot.emit(self._livePlotRunId, # runId
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
                                        zParamUnit, # zLabelUnits
                                        dialogX, # dialog position x
                                        dialogY, # dialog position y
                                        dialogWidth, # dialog width
                                        dialogHeight) # dialog height


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


    def livePlotPushButton(self) -> None:
        """
        Call when user click on the 'LivePlot' button.
        Allow user to chose any available qcodes database in his computer.
        This database will be monitored and any new run will be plotted.
        """

        self.pushButtonLivePlot.setText('Loading QCoDeS...')
        self.pushButtonLivePlot.repaint()

        QtCore.QThread.msleep(100)
        from qcodes import initialise_or_create_database_at, load_by_run_spec
        self.pushButtonLivePlot.setText('Select database...')
        self.loadDataset = load_by_run_spec

        fname = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Open QCoDeS database',
                                                      self.config['livePlotDefaultFolder'],
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


    ###########################################################################
    #                           Labrad plotting
    ###########################################################################


    @QtCore.pyqtSlot(str, tuple, str, bool, bool, int)
    def slotUpdatePlotLabradData(self, 
                                 plotRef        : str,
                                 data           : Tuple[np.ndarray, ...],
                                 yParamName     : str,
                                 lastUpdate     : bool,
                                 lastDependent  : bool,
                                 plotId         : int) -> None:
        self.slotUpdatePlot(plotRef, data, yParamName, lastUpdate, lastDependent, plotId)


    def livePlotGetLabradPlotParameters(self, plotId: int) -> None:
        """
        Gather the information from the current live plot dataset and sort them
        into iterables.

        Each dependent parameters must be treated independently since they
        can each have a different number of independent parameters.
        """

        # Get dataset params
        paramsDependents   = [i for i in self.livePlotDataSets[plotId].getPlotDependents()]

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

            # # For each dependent parameter we them the parameter(s) they depend
            # # on.
            # depends_on = [i for i in paramsDependent.depends_on.split(', ')]

            depends_on = [i for i in self.livePlotDataSets[plotId].getIndependents()]

            param_x = depends_on[0]
            xParamNames.append(param_x.label + ' (name)')
            xParamLabels.append(param_x.label)
            xParamUnits.append(param_x.unit)

            # For 2d plot
            if len(depends_on)>1:
                param_y = depends_on[1]
                yParamNames.append(param_y.label + ' (name)')
                yParamLabels.append(param_y.label)
                yParamUnits.append(param_y.unit)

                zParamNames.append(dep_name(paramsDependent))
                zParamLabels.append(paramsDependent.label)
                zParamUnits.append(paramsDependent.unit)

                plotRefs.append(getPlotRef(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                           paramDependent={'depends_on' : [0, 1], 'name': dep_name(paramsDependent)},
                                           runId=self.livePlotRunIds[plotId]))
                self._livePlotNbPlot += 1
            # For 1d plot
            else:
                yParamNames.append(dep_name(paramsDependent))
                yParamLabels.append(paramsDependent.label)
                yParamUnits.append(paramsDependent.unit)

                zParamNames.append('')
                zParamLabels.append('')
                zParamUnits.append('')

                plotRefs.append(getPlotRef(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                           paramDependent={'depends_on' : [0]},
                                           runId=self.livePlotRunIds[plotId]))
                # We only add 1 1dplot for all 1d curves
                if plot1dNotAlreadyAdded:
                    self._livePlotNbPlot += 1
                    plot1dNotAlreadyAdded = False

        return xParamNames, xParamLabels, xParamUnits, yParamNames, yParamLabels, yParamUnits, zParamNames, zParamLabels, zParamUnits, plotRefs


    def livePlotLaunchLabradPlot(self, plotId) -> None:
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
        paramsIndependent = [i for i in self.livePlotDataSets[plotId].getIndependents()]

        plotTitle   = getPlotTitle(self._livePlotDatabaseAbsPath,
                                   self.livePlotRunIds[plotId],
                                   self.livePlotRunNames[plotId]) + self.config['livePlotTitleAppend']
        windowTitle = getWindowTitle(self._livePlotDatabaseAbsPath,
                                     self.livePlotRunIds[plotId],
                                     self.livePlotRunNames[plotId])

        # We get the liveplot parameters
        self.livePlotGetPlotParameterList[plotId] = self.livePlotGetLabradPlotParameters(plotId)

        for tile_idx, (xParamName, xParamLabel, xParamUnit,
             yParamName, yParamLabel, yParamUnit,
             zParamName, zParamLabel, zParamUnit,
             plotRef) in enumerate(zip(*self.livePlotGetPlotParameterList[plotId])):

            # We get the dialog position and size to tile the screen
            if zParamName == '':
                dialogTilings = getParallelDialogWidthHeight(nbDialog=1, plotId=plotId)
                dialogX, dialogY, dialogWidth, dialogHeight = [tile[0] for tile in dialogTilings]
            else:
                # tile 3D plot with plot windows
                num_2d_plots = len(self.livePlotGetPlotParameterList[plotId][0])
                dialogTilings = getParallelDialogWidthHeight(num_2d_plots, plotId=plotId)
                dialogX, dialogY, dialogWidth, dialogHeight = [tile[tile_idx] for tile in dialogTilings]

            # Only the first dependent parameter is displayed per default
            if yParamLabel==paramsIndependent[0].label:
                hidden = False
            else:
                hidden = True

            # Create empty data for the plot window launching
            if zParamName=='':
                data = (np.array([]),
                        np.array([]))
            else:
                data = (np.array([0., 1.]),
                        np.array([0., 1.]),
                        np.array([[0., 1.],
                                  [0., 1.]]))

            curveId = getCurveId(databaseAbsPath=self._livePlotDatabaseAbsPath,
                                 name=yParamName,
                                 runId=self.livePlotRunIds[plotId])
            self.signalAddLivePlot.emit(self.livePlotRunIds[plotId], # runId
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
                                        zParamUnit, # zLabelUnits
                                        dialogX, # dialog position x
                                        dialogY, # dialog position y
                                        dialogWidth, # dialog width
                                        dialogHeight) # dialog height


    def livePlotUpdateLabradPlot(self, plotId: int, lastUpdate: bool=False) -> None:
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

        self.livePlotDataSets[plotId].data.dataset.refresh()
        d = self.livePlotDataSets[plotId].getPlotData()[0]
        
        for dep_idx, [xParamName, xParamLabel, xParamUnit, yParamName, yParamLabel, yParamUnit, zParamName, zParamLabel, zParamUnit, plotRef] in enumerate(zip(*self.livePlotGetPlotParameterList[plotId])):
            self._updatingFlag.append(False)

            dataDict = {}
            dataDict[xParamName] =  d[:,0]
            if zParamName:
                dataDict[yParamName] = d[:,1]
                dataDict[zParamName] = {zParamName: d[:,2 + dep_idx],
                                        yParamName: dataDict[yParamName],
                                        xParamName: dataDict[xParamName]}
            elif yParamName:
                dataDict[yParamName] = {yParamName: d[:,1 + dep_idx],
                                        xParamName: dataDict[xParamName]}
            else:
                raise ValueError
            
            lastDependent = (dep_idx == len(self.livePlotGetPlotParameterList[plotId][0]) - 1)
            worker = LoadLabradDataFromCacheThread(plotRef,
                                                   dataDict,
                                                   xParamName,
                                                   yParamName,
                                                   zParamName,
                                                   lastUpdate,
                                                   lastDependent,
                                                   plotId)

            worker.signal.dataLoaded.connect(self.slotUpdatePlotLabradData)
            worker.signal.sendLivePlotInfoMessage.connect(self.slotLiveplotMessage)

            # Execute the thread
            self.threadpools[plotId].start(worker)


    def livePlotUpdateLabrad(self) -> None:
        """
        Method called periodically by a QTimer.
        1. Obtain the last runId of the livePlotDatabase
        2. If this run is not marked as completed, load its dataset and plot its
           parameters
        3. Update the plots until the run is marked completed
        4. When the run is completed, remove its dataset from memory
        """

        # We get the last run id of the database
        # self._livePlotRunId = getNbTotalRunmp(self._livePlotDatabaseAbsPath)
        self._livePlotRunId, self._livePlotRunName = getNbTotalRunAndLastRunNameLabrad(self._livePlotDatabaseAbsPath)
        num_live_plots = min(self._livePlotRunId, MAX_LIVE_PLOTS)
        updateIds = np.arange(self.plotId, self.plotId + num_live_plots) % MAX_LIVE_PLOTS
        currPlotId = self.plotId
        
        isBusy = self.isDataBusy(self._livePlotRunName)
        if isBusy:
            print(f'WARNING: dataset {self._livePlotRunName} is busy, please set swmr mode!')
            return

        for ii, _plotId in enumerate(updateIds):
            # fist run and setup
            if self.livePlotRunIds[_plotId] is None:
                # set new
                dataset = self.loadDataset(self._livePlotRunId - ii)
                self.livePlotRunIds[_plotId] = self._livePlotRunId - ii
                self.livePlotPreviousDataLengths[_plotId] = 0
                self.livePlotDataSets[_plotId] = dataset
                self.livePlotRunNames[_plotId] = dataset.name
                self.livePlotLaunchLabradPlot(_plotId)

            # While the run is not completed, we update the plot
            if not isRunCompletedLabrad(
                self._livePlotDatabaseAbsPath, self.livePlotRunIds[_plotId]
            ):
                self.labelLivePlotInProgressState.setText(
                    '<span style="color: green;">True</span>'
                )
                self.labelLivePlotRunidid.setText("{}".format(self.livePlotRunIds[_plotId]))
                self.labelLivePlotRunNameInfo.setText("{}".format(self.livePlotRunNames[_plotId]))
                self.labelLivePlotInfoInfo.setText(
                    '<span style="color: green;">New run detected</span>'
                )
                self.livePlotUpdateLabradPlot(_plotId)

            # new RunId detected, replace the first plotID
            if _plotId == currPlotId and (
                self._livePlotRunId != self.livePlotRunIds[_plotId]
            ):
                # move to the next plot window for new data
                self.plotId = next(self.plotIdGenerator)
                # plotRefs are the same in one live dataset
                plotRefs = self.livePlotGetPlotParameterList[self.plotId][-1]
                is2Dplot = self.is2dPlot(self.livePlotGetPlotParameterList[self.plotId])
                curveIds = self.genCurveIds(self.livePlotGetPlotParameterList[self.plotId], 
                                            self.livePlotRunIds[self.plotId])
                self.signalCloseLivePlot.emit(tuple(plotRefs), is2Dplot, tuple(curveIds))
                # remove old
                self.livePlotRunIds.pop(self.plotId)
                self.livePlotPreviousDataLengths.pop(self.plotId)
                self.livePlotRunNames.pop(self.plotId)
                old_dataset = self.livePlotDataSets.pop(self.plotId)
                old_dataset.close()
                # set new
                self.livePlotRunIds.insert(self.plotId, self._livePlotRunId)
                self.livePlotPreviousDataLengths.insert(self.plotId, 0)
                self.livePlotDataSets.insert(self.plotId, self.loadDataset(self._livePlotRunId))
                self.livePlotRunNames.insert(self.plotId, self.livePlotDataSets[self.plotId].name)
                self.livePlotLaunchLabradPlot(self.plotId)


    def livePlotPushButtonFolder(self) -> None:

        """
        Call when user click on the 'LivePlot' button.
        Allow user to chose any available qcodes database in his computer.
        This database will be monitored and any new run will be plotted.
        """
        self.pushButtonLivePlot.setText('Loading Labrad...')
        self.pushButtonLivePlot.repaint()

        QtCore.QThread.msleep(100)
        self.pushButtonLivePlot.setText('Select database...')
        fname = QtWidgets.QFileDialog.getExistingDirectory(self, 
                                                           'Open Labrad database',
                                                           self.config['livePlotDefaultFolder'])
        if fname:
            self._livePlotDatabaseAbsPath = fname
            self._livePlotDataBaseName = os.path.split(fname)[-1]

            self._livePlotPreviousDataLength = 0
            self.plotIdGenerator = plotIdGenerator()
            self.plotId = next(self.plotIdGenerator)  # the idx of live plot, changes to create new window
            self.livePlotRunIds = [None] * MAX_LIVE_PLOTS
            self.livePlotPreviousDataLengths = [None] * MAX_LIVE_PLOTS
            self.livePlotRunNames = [None] * MAX_LIVE_PLOTS
            self.livePlotDataSets = [None] * MAX_LIVE_PLOTS
            self.livePlotGetPlotParameterList = [None] * MAX_LIVE_PLOTS

            self.session = switch_session_path(self._livePlotDatabaseAbsPath)

            def load_by_run_spec(idx):
                # noisy=false to turn off the open message
                return self.session.openDataset(idx, noisy=False)  

            self.loadDataset = load_by_run_spec

            self.labelLivePlotDatabasePathInfo.setText('{}'.format(self._livePlotDatabaseAbsPath))
            self.labelLivePlotDatabaseNameInfo.setText('{}'.format(self._livePlotDataBaseName))

            # We call the liveplot function once manually to be sure it has been
            # initialized properly
            self.livePlotUpdateLabrad()

            # Launch a Qt timer which will periodically check if a new run is
            # launched
            # If the user disable the livePlot previously
            if self.spinBoxLivePlotRefreshRate.value()==0:
                self.spinBoxLivePlotRefreshRate.setValue(1)

            self._livePlotTimer = QtCore.QTimer()
            self._livePlotTimer.timeout.connect(self.livePlotUpdateLabrad)
            self._livePlotTimer.setInterval(self.spinBoxLivePlotRefreshRate.value()*1000)
            self._livePlotTimer.start()

            self._livePlotClockTimer = QtCore.QTimer()
            self._livePlotClockTimer.timeout.connect(self.livePlotClockUpdate)
            self._livePlotClockTimer.setInterval(1000)
            self._livePlotClockTimer.start()

        self.pushButtonLivePlot.setText('Modify database')


    def livePlotPushButtonFolder(self, fname=None) -> None:

        """
        Call when user click on the 'LivePlot' button.
        Allow user to chose any available qcodes database in his computer.
        This database will be monitored and any new run will be plotted.
        """
        self.pushButtonLivePlot.setText('Loading Labrad...')
        self.pushButtonLivePlot.repaint()

        QtCore.QThread.msleep(100)
        self.pushButtonLivePlot.setText('Select database...')
        if fname is None:
            fname = QtWidgets.QFileDialog.getExistingDirectory(self, 
                                                           'Open Labrad database',
                                                           self.config['livePlotDefaultFolder'])
        if fname:
            self._livePlotDatabaseAbsPath = fname
            self._livePlotDataBaseName = os.path.split(fname)[-1]

            self._livePlotPreviousDataLength = 0
            self.plotIdGenerator = plotIdGenerator()
            self.plotId = next(self.plotIdGenerator)  # the idx of live plot, changes to create new window
            self.livePlotRunIds = [None] * MAX_LIVE_PLOTS
            self.livePlotPreviousDataLengths = [None] * MAX_LIVE_PLOTS
            self.livePlotRunNames = [None] * MAX_LIVE_PLOTS
            self.livePlotDataSets = [None] * MAX_LIVE_PLOTS
            self.livePlotGetPlotParameterList = [None] * MAX_LIVE_PLOTS

            self.session = switch_session_path(self._livePlotDatabaseAbsPath)
            def load_by_run_spec(idx):
                dv = switch_session_path(self._livePlotDatabaseAbsPath)
                return dv.openDataset(idx, noisy=False)  # noisy=false to turn off the open message

            self.loadDataset = load_by_run_spec

            self.labelLivePlotDatabasePathInfo.setText('{}'.format(self._livePlotDatabaseAbsPath))
            self.labelLivePlotDatabaseNameInfo.setText('{}'.format(self._livePlotDataBaseName))

            # We call the liveplot function once manually to be sure it has been
            # initialized properly
            self.livePlotUpdateLabrad()

            # Launch a Qt timer which will periodically check if a new run is
            # launched
            # If the user disable the livePlot previously
            if self.spinBoxLivePlotRefreshRate.value()==0:
                self.spinBoxLivePlotRefreshRate.setValue(1)

            self._livePlotTimer = QtCore.QTimer()
            self._livePlotTimer.timeout.connect(self.livePlotUpdateLabrad)
            self._livePlotTimer.setInterval(self.spinBoxLivePlotRefreshRate.value()*1000)
            self._livePlotTimer.start()

            self._livePlotClockTimer = QtCore.QTimer()
            self._livePlotClockTimer.timeout.connect(self.livePlotClockUpdate)
            self._livePlotClockTimer.setInterval(1000)
            self._livePlotClockTimer.start()

        self.pushButtonLivePlot.setText('Modify database')
