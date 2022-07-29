# This Python file uses the following encoding: utf-8
from __future__ import annotations
from PyQt5 import QtWidgets, QtCore, QtTest
import numpy as np
import os
from datetime import datetime

from ..workers.loadDataFromCache import LoadDataFromCacheThread
from ...ui.dialog_liveplot import Ui_LivePlot
from ..qcodesdatabase import getNbTotalRunAndLastRunName, isRunCompleted



class MenuDialogLiveplot(QtWidgets.QDialog, Ui_LivePlot):



    def __init__(self, config,
                       addPlot,
                       cleanCheckBox,
                       getLivePlotRef,
                       _plotRefs) -> None:

        super(MenuDialogLiveplot, self).__init__()
        self.setupUi(self)

        self.config           = config
        self.addPlot          = addPlot
        self.cleanCheckBox    = cleanCheckBox
        self.getLivePlotRef   = getLivePlotRef
        self._plotRefs        = _plotRefs


        # Connect events
        self.pushButtonLivePlot.clicked.connect(self.livePlotPushButton)
        self.spinBoxLivePlotRefreshRate.setValue(int(config['livePlotTimer']))
        self.spinBoxLivePlotRefreshRate.valueChanged.connect(self.livePlotSpinBoxChanged)

        # Will contain the timer updating the liveplot
        self._livePlotTimer      = None

        # Will contain the timer updating the "last time update" of the display
        self._livePlotClockTimer = None

        self.threadpool = QtCore.QThreadPool()

        self.show()



    ###########################################################################
    #
    #
    #                           Live plotting
    #
    #
    ###########################################################################



    def getPlotTitle(self):

        # If user only wants the database path
        if self.config['displayOnlyDbNameInPlotTitle']:
            title = os.path.basename(self._livePlotDatabasePath)
        # If user wants the database path
        else:
            title = os.path.basename(self._livePlotDatabasePath)
        return title+'<br>'+str(self._livePlotRunId)



    def getWindowTitle(self) -> str:
        """
        Return a title which will be used as a plot window title.
        """

        windowTitle = os.path.basename(self._livePlotDatabasePath)

        if self.config['displayRunIdInPlotTitle']:
            windowTitle += ' - '+str(self._livePlotRunId)

        if self.config['displayRunNameInPlotTitle']:
            windowTitle += ' - '+self._livePlotRunName

        return windowTitle



    def getPlotRef(self, paramDependent : dict) -> str:
        """
        Return a reference for a plot window.
        Handle the difference between 1d plot and 2d plot.

        Parameters
        ----------
        paramDependent : dict
            qcodes dictionary of a dependent parameter

        Return
        ------
        plotRef : str
            Unique reference for a plot window.
        """

        dataPath = self._livePlotDatabasePath + str(self._livePlotRunId)

        if len(paramDependent['depends_on'])==2:
            return dataPath+paramDependent['name']
        else:
            return dataPath



    def getCurveId(self, name: str,
                         runId: int) -> str:
        """
        Return an id for a curve in a plot.
        Should be unique for every curve.

        Parameters
        ----------
        name : str
            Parameter name from which the curveId is obtained.
        runId : int
            Id of the curve, see getCurveId.
        """

        return self._livePlotDatabasePath+str(runId)+str(name)



    def livePlotClockUpdate(self):

        ## Update displayed information
        # Last time since we interogated the dataCache
        if self.labelLivePlotLastRefreshInfo.text()!='None':
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
        if self.labelLivePlotLastUpdateInfo.text()!='None':
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



    def livePlotUpdatePlotData(self, plotRef        : str,
                                     data           : tuple,
                                     yParamName     : str,
                                     lastUpdate     : bool) -> None:
        """
        Methods called in live plot mode to update plot.
        This method must have the same signature as addPlot.

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

        # 1d plot
        if len(data)==2:
            # New data since last time we interogate the dataCache?
            if len(self._plotRefs[plotRef].curves[self.getCurveId(yParamName, self._livePlotRunId)].x)!=len(data[0]):
                self.labelLivePlotLastUpdateInfo.setText('{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            self._plotRefs[plotRef].updatePlotDataItem(x           = data[0],
                                                       y           = data[1],
                                                       curveId     = self.getCurveId(yParamName, self._livePlotRunId),
                                                       curveLegend = None,
                                                       autoRange   = True)
        # 2d plot
        elif len(data)==3:
            # New data since last time we interogate the dataCache?
            if len(self._plotRefs[plotRef].xData)!=len(data[0]):
                self.labelLivePlotLastUpdateInfo.setText('{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            self._plotRefs[plotRef].livePlotUpdate(x=data[0],
                                                   y=data[1],
                                                   z=data[2])

            # If there are slices, we update them as well
            # plotSlice = self.getPlotSliceFromRef(plotRef)
            # if plotSlice is not None:
            for curveId, lineItem in self._plotRefs[plotRef].sliceItems.items():

                # We find its orientation
                if lineItem.angle==90:
                    sliceOrientation = 'vertical'
                else:
                    sliceOrientation = 'horizontal'

                # We need the data of the slice
                sliceX, sliceY, sliceLegend = self._plotRefs[plotRef].getDataSlice(lineItem)

                # Get the 1d plot of the slice
                plotSlice = self._plotRefs[plotRef].getPlotRefFromSliceOrientation(sliceOrientation)

                # We update the slice data
                plotSlice.updatePlotDataItem(x           = sliceX,
                                             y           = sliceY,
                                             curveId     = curveId,
                                             curveLegend = sliceLegend,
                                             autoRange   = True)

        # We show to user the time of the last update
        if lastUpdate:
            # self.labelLivePlotLastUpdateInfo.setText('Measurement done: '+datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
            # We mark all completed livePlot as not livePlot anymore
            for plotRef in self.getLivePlotRef():
                self._plotRefs[plotRef].livePlot = False

            self.labelLivePlotInProgressState.setText('False')



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

                plotRefs.append(self.getPlotRef(paramDependent={'depends_on' : [0, 1], 'name': paramsDependent.name}))
                self._livePlotNbPlot += 1
            # For 1d plot
            else:
                yParamNames.append(paramsDependent.name)
                yParamLabels.append(paramsDependent.label)
                yParamUnits.append(paramsDependent.unit)

                zParamNames.append('')
                zParamLabels.append('')
                zParamUnits.append('')

                plotRefs.append(self.getPlotRef(paramDependent={'depends_on' : [0]}))
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

        #    1d.  We launch a plot window with all the dependent parameters
        #         plotted as plotDataItem.
        #    2d.  We launch as many plot window as dependent parameters.
        # Get dataset params
        paramsIndependent = [i for i in self._livePlotDataSet.get_parameters() if len(i.depends_on)==0]

        plotTitle   = self.getPlotTitle()
        windowTitle = self.getWindowTitle()

        databaseAbsPath = os.path.normpath(os.path.join(self._livePlotDatabasePath, self._livePlotDataBaseName)).replace("\\", "/")

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
                data = [[],[]]
            else:
                data = [np.array([0., 1.]),
                        np.array([0., 1.]),
                        np.array([[0., 1.],
                                  [0., 1.]])]

            self.addPlot(plotRef        = plotRef,
                         databaseAbsPath= databaseAbsPath,
                         data           = data,
                         xLabelText     = xParamLabel,
                         xLabelUnits    = xParamUnit,
                         yLabelText     = yParamLabel,
                         yLabelUnits    = yParamUnit,
                         zLabelText     = zParamLabel,
                         zLabelUnits    = zParamUnit,
                         cleanCheckBox  = self.cleanCheckBox,
                         plotTitle      = plotTitle,
                         windowTitle    = windowTitle,
                         runId          = self._livePlotRunId,
                         linkedTo2dPlot = False,
                         curveId        = self.getCurveId(name=yParamName, runId=self._livePlotRunId),
                         timestampXAxis = False,
                         livePlot       = True,
                         hidden         = hidden)



    def livePlotUpdatePlot(self, lastUpdate: bool=False) -> None:
        """
        Method called by livePlotUpdate.
        Obtain the info of the current live plot dataset cache, treat them and
        send them to the livePlotUpdatePlotData method.

        Parameters
        ----------
        lastUpdate : bool
            True if this is the last update of the livePlot, a.k.a. the run is
            marked as completed by qcodes.
        """

        # We show to user that the plot is being updated
        # self.livePlotUpdateMessage('Interrogating cache')

        for xParamName, xParamLabel, xParamUnit, yParamName, yParamLabel, yParamUnit, zParamName, zParamLabel, zParamUnit, plotRef in zip(*self._livePlotGetPlotParameters):
            worker = LoadDataFromCacheThread(plotRef,
                                             self._livePlotDataSet.cache.data(),
                                             xParamName,
                                             yParamName,
                                             zParamName,
                                             lastUpdate)

            worker.signals.dataLoaded.connect(self.livePlotUpdatePlotData)

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
        self._livePlotRunId, self._livePlotRunName = getNbTotalRunAndLastRunName(self._livePlotDatabasePath)

        # While the run is not completed, we update the plot
        if not isRunCompleted(self._livePlotDatabasePath, self._livePlotRunId):

            self.labelLivePlotInProgressState.setText('True')
            self.labelLivePlotRunidid.setText('{}'.format(self._livePlotRunId))
            self.labelLivePlotRunNameInfo.setText('{}'.format(self._livePlotRunName))
            self.labelLivePlotDatabasePathInfo.setText('{}'.format(self._livePlotDatabasePath))
            self.labelLivePlotDatabaseNameInfo.setText('{}'.format(self._livePlotDataBaseName))

            ## 1. We get the livePlot dataset
            # We access the db only once.
            # The next iteration will access the cache of the dataset.
            if not hasattr(self, '_livePlotDataSet'):
                self._livePlotDataSet = self.loadDataset(captured_run_id=self._livePlotRunId)
            ## 2. If we do not see the attribute attached to the launched plot
            if not hasattr(self, '_livePlotGetPlotParameters'):
                self.livePlotLaunchPlot()
            ## 2. If the user closed some or every liveplot windows
            elif len(self.getLivePlotRef())!=self._livePlotNbPlot:
                self.livePlotLaunchPlot()
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
        if self._livePlotTimer is not None:

            # If the timer is 0, we stopped the liveplot
            if val==0:
                self._livePlotTimer.stop()
                self._livePlotTimer.deleteLater()
                self._livePlotTimer = None

                self._livePlotClockTimer.stop()
                self._livePlotClockTimer.deleteLater()
                self._livePlotClockTimer = None

                # self.labelLivePlotDataBase.setText('')
                # self.groupBoxLivePlot.setStyleSheet('QGroupBox:title{color: white}')
                self.pushButtonLivePlot.setText('Select database')
                self.labelLivePlotInProgressState.setText('None')
                self.labelLivePlotRunidid.setText('None')
                self.labelLivePlotRunNameInfo.setText('None')
                self.labelLivePlotDatabasePathInfo.setText('None')
                self.labelLivePlotDatabaseNameInfo.setText('None')
                self.labelLivePlotLastUpdateInfo.setText('None')
                self.labelLivePlotSinceLastUpdateInfo.setText('None')
                self.labelLivePlotLastRefreshInfo.setText('None')
                self.labelLivePlotSinceLastRefresh.setText('None')
                if hasattr(self, '_livePlotDatabasePath'):
                    del(self._livePlotDatabasePath)
                if hasattr(self, '_livePlotDataBase'):
                    del(self._livePlotDataBase)
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
            self._livePlotDatabasePath = os.path.abspath(fname[0])
            self._livePlotDataBaseName = os.path.basename(fname[0])[:-3]

            self._livePlotDataBase = initialise_or_create_database_at(self._livePlotDatabasePath)

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
