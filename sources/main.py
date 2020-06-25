# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets
import os
import numpy as np
import pyqtgraph as pg
from matplotlib.pyplot import colormaps
from matplotlib import cm as plt_cm
import tempfile
import sys 
import qcodes as qc
from itertools import chain
from typing import Dict, List, Set, Union, TYPE_CHECKING
from operator import attrgetter
sys.path.append('ui')
sys.path.append('sources')

from ui import main
from config import config
from plot_1d_app import Plot1dApp
from plot_2d_app import Plot2dApp

pg.setConfigOption('background', config['pyqtgraphBackgroundColor'])
pg.setConfigOption('useOpenGL', config['pyqtgraphOpenGL'])
pg.setConfigOption('antialias', config['plot1dAntialias'])


class MyTableWidgetItem(QtWidgets.QTableWidgetItem):
    """
    Custom class to be able to sort numerical table column
    """

    def __lt__(self, other):
        if isinstance(other, QtWidgets.QTableWidgetItem):

            return int(self.data(QtCore.Qt.EditRole)) < int(other.data(QtCore.Qt.EditRole))

        return super(MyTableWidgetItem, self).__lt__(other)



class MainApp(QtWidgets.QMainWindow, main.Ui_MainWindow):



    def __init__(self, parent=None):

        super(MainApp, self).__init__(parent)
        self.setupUi(self)

        
        # Connect UI
        self.listWidgetFolder.clicked.connect(self.itemClicked)
        
        # Resize the cell to the column content automatically
        self.tableWidgetDataBase.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # Select row instead of cell
        self.tableWidgetDataBase.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # Connect event
        self.tableWidgetDataBase.clicked.connect(self.runClicked)

        self.tableWidgetParameters.cellClicked.connect(self.parameterCellClicked)
        
        self.checkBoxLivePlot.toggled.connect(self.livePlotToggle)
        self.spinBoxLivePlot.setValue(int(config['livePlotTimer']))
        self.spinBoxLivePlot.valueChanged.connect(self.livePlotSpinBoxChanged)


        self.statusBar.showMessage('Ready')

        # Default folder is the dataserver except if we are on test mode
        if 'test' in os.listdir('.'):
            self.currentPath = os.path.abspath(os.path.curdir)
            config['path'] = self.currentPath
            config['root'] = self.currentPath
        else:
            
            self.currentPath = os.path.normpath(config['path'])

        # References
        self._refs = {}

        # Attribute to control the display of data file info when user click of put focus on a item list
        self.folderUpdating  = False # To avoid calling the signal when updating folder content
        self.guiInitialized = True # To avoid calling the signal when starting the GUI

        # By default, we browse the root folder
        self.folderClicked(e=False, directory=self.currentPath)

        self.currentDatabase  = None
        self.oldTotalRun      = None
        self.livePlotMode     = False
        self.livePlotFetchData      = False
        self.livePlotTimer = None


    ###########################################################################
    #
    #
    #                           Folder browsing
    #
    #
    ###########################################################################



    def goParentFolder(self, e, directory=None):
        """
        Handle event when user click on the go up button.
        Change the current folder by the parent one.
        Stop when arrive in the root folder.
        """

        self.folderClicked(False, directory=os.path.join(*os.path.split(self.currentPath)[:-1]))



    def updateLabelPath(self):
        """
        Update the label path by creating a horizontal list of buttons to
        quickly browse back the folder arborescence.
        """

        self.clearLayout(self.labelPath)

        path = os.path.normpath(self.currentPath).split(os.sep)
        root = os.path.normpath(config['root']).split(os.sep)

        # Display path until root 
        for i, text in enumerate(path):

            # Build button text depending of where we are
            if text == root[-1]:
                bu_text = 'root'
            elif text not in root:
                bu_text = text
            else:
                bu_text = None

            # Create, append and connect buttons
            if bu_text is not None:
                bu = QtWidgets.QPushButton(bu_text)
                width = bu.fontMetrics().boundingRect(bu_text).width() + 15
                bu.setMaximumWidth(width)
                d = os.path.join(path[0], os.sep, *path[1:i+1])
                bu.clicked.connect(lambda e=False, directory=d : self.folderClicked(e, directory))
                self.labelPath.addWidget(bu)

        self.labelPath.setAlignment(QtCore.Qt.AlignLeft)



    def folderClicked(self, e, directory=None):
        """
        Basically display folder and csv file of the current folder.
        """
        
        # When signal the updating of the folder to prevent unwanted item events
        self.folderUpdating = True

        if directory is None:
            directory = QtGui.QFileDialog.getExistingDirectory(self, 'Pick a folder')

        self.currentPath = directory

        self.updateLabelPath()

        
        # Display the current dir content
        self.listWidgetFolder.clear()
        for file in sorted(os.listdir(self.currentPath), reverse=True): 
            
            abs_filename = os.path.join(self.currentPath, file)
            file_extension = os.path.splitext(abs_filename)[-1][1:]

            # Only display folder and Qcodes database
            # Add icon depending of the item type
            if os.path.isdir(abs_filename):
                item =  QtGui.QListWidgetItem(file)
                item.setIcon(QtGui.QIcon('ui/pictures/folder.png'))
                self.listWidgetFolder.addItem(item)
            else:
                if file_extension in config['authorized_extension']:

                    # We look if the file is already opened by someone else
                    already_opened = False
                    for subfile in os.listdir(self.currentPath): 
                        if subfile==file[:-2]+'db-wal':
                            already_opened = True

                    if already_opened:
                        item =  QtGui.QListWidgetItem(file)
                        item.setIcon(QtGui.QIcon('ui/pictures/fileOpened.png'))
                        item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                    else:
                        item =  QtGui.QListWidgetItem(file)
                        item.setIcon(QtGui.QIcon('ui/pictures/file.png'))
                    self.listWidgetFolder.addItem(item)
                

        # Disable live plot
        self.checkBoxLivePlot.setEnabled(False)
        self.spinBoxLivePlot.setEnabled(False)
        self.labelLivePlot.setEnabled(False)
        self.labelLivePlot2.setEnabled(False)
        self.labelLivePlotDataBase.setEnabled(False)
        self.labelLivePlotDataBase.setText('')

        # Allow item event again
        self.folderUpdating = False



    def itemClicked(self):
        """
        Handle event when user clicks on datafile.
        The user can either click on a folder or a file.
        If it is a folder, we launched the folderClicked method.
        If it is a file, we launched the dataBaseClicked method.
        """
        # We check if the signal is effectively called by user
        if not self.folderUpdating and self.guiInitialized:
            
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            # Get current item
            self.currentDatabase = self.listWidgetFolder.currentItem().text()

            nextPath = os.path.join(self.currentPath, self.currentDatabase)
            if os.path.isdir(nextPath):
                self.statusBar.showMessage('Update')
                self.folderClicked(e=False, directory=nextPath)
                self.statusBar.showMessage('Ready')
            else:
                
                self.dataBaseClicked()
                # # We check of the user double click ir single click
                #                         self._itemClicked)

            # Job done, we restor the usual cursor 
            QtGui.QApplication.restoreOverrideCursor()
        
        # When the signal has been called at least once
        if not self.guiInitialized:
            self.guiInitialized = True


    ###########################################################################
    #
    #
    #                           Database browsing
    #
    #
    ###########################################################################



    def dataBaseClicked(self):
        """
        Display the content of the clicked dataBase into a tableWidgetTable
        which will then contain all runs
        """

        # Update label
        self.labelCurrentDataBase.setText(self.currentDatabase[:-3])

        # Remove all previous row in the table
        self.tableWidgetDataBase.setSortingEnabled(False)
        self.tableWidgetDataBase.setRowCount(0)
        self.tableWidgetDataBase.setSortingEnabled(True)

        # If the database is already opened, we do not try to open it
        # Get database
        self.statusBar.showMessage('Load database')
        qc.initialise_or_create_database_at(os.path.join(self.currentPath, self.currentDatabase))

        self.statusBar.showMessage('Get database information')
        datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id'))

        self.overview = {ds.run_id: self.get_ds_info(ds, get_structure=False)
                for ds in datasets}

        self.statusBar.showMessage('Display database information')

        # Fill table with new information
        for key, val in self.overview.items(): 
            rowPosition = self.tableWidgetDataBase.rowCount()

            self.tableWidgetDataBase.insertRow(rowPosition)

            self.tableWidgetDataBase.setItem(rowPosition, 0, MyTableWidgetItem(str(key)))
            self.tableWidgetDataBase.setItem(rowPosition, 1, QtGui.QTableWidgetItem(val['experiment']))
            self.tableWidgetDataBase.setItem(rowPosition, 2, QtGui.QTableWidgetItem(val['sample']))
            self.tableWidgetDataBase.setItem(rowPosition, 3, QtGui.QTableWidgetItem(val['name']))
            self.tableWidgetDataBase.setItem(rowPosition, 4, QtGui.QTableWidgetItem(val['started date']+' '+val['started time']))
            self.tableWidgetDataBase.setItem(rowPosition, 5, QtGui.QTableWidgetItem(val['completed date']+' '+val['completed time']))
            self.tableWidgetDataBase.setItem(rowPosition, 6, MyTableWidgetItem(str(val['records'])))


        # Enable live plot
        self.checkBoxLivePlot.setEnabled(True)
        self.spinBoxLivePlot.setEnabled(True)
        self.labelLivePlot.setEnabled(True)
        self.labelLivePlot2.setEnabled(True)
        self.labelLivePlotDataBase.setEnabled(True)
        self.labelLivePlotDataBase.setText(self.currentDatabase[:-3])


        self.statusBar.showMessage('Ready')



    def runClicked(self):
        """
        When clicked display the measured dependent parameters in the 
        tableWidgetPtableWidgetParameters
        """


        self.statusBar.showMessage('Load run parameters')

        # When we fill the table, we need to check if there is already
        # a plotWindow of that file opened.
        # If it is the case, we need to checked the checkBox which are plotted
        # in the plotWindow.
        # Our aim is then to get the list of the checkBox which has to be checked.
        checkedDependents = []
        # If a plotWindow is already open
        if len(self._refs) > 0:
            # We iterate over all plotWindow
            for val in list(self._refs.values()):
                if val['plotType'] == '1d':
                    if self.currentDatabase == val['plot'].windowTitle:
                        if self.getRunId() == val['plot'].runId:
                            checkedDependents = list(val['plot'].curves.keys())
                else:
                    for subval in list(val['plots'].values()):
                        if self.currentItem == subval.windowTitle:
                            if self.getRunId() == val['plot'].runId:
                                checkedDependents.append(list(subval.curves.keys()[0]))
            

        # Update label
        self.labelCurrentRun.setText(str(self.getRunId()))

        # Update label
        self.labelCurrentMetadata.setText(str(self.getRunId()))

        # Quick fix to show plot dimension
        self.listWidgetMetadata.clear()
        self.listWidgetMetadata.addItem(QtGui.QListWidgetItem('Plot dimension: '+str(self.getNbIndependentParameters())))

        # Get parameters list without the independent parameters
        params = qc.load_by_id(int(self.getRunId())).get_parameters()[self.getNbIndependentParameters():]

        self.tableWidgetParameters.setSortingEnabled(False)
        self.tableWidgetParameters.setRowCount(0)
        self.tableWidgetParameters.setSortingEnabled(True)
        for param in params:
            rowPosition = self.tableWidgetParameters.rowCount()


            self.tableWidgetParameters.insertRow(rowPosition)

            cb = QtWidgets.QCheckBox()

            # We check if that parameter is already plotted
            if param.name+' ['+param.unit+']' in checkedDependents:
                cb.setChecked(True)

            self.tableWidgetParameters.setCellWidget(rowPosition, 0, cb)
            self.tableWidgetParameters.setItem(rowPosition, 1, QtGui.QTableWidgetItem(param.name))
            self.tableWidgetParameters.setItem(rowPosition, 2, QtGui.QTableWidgetItem(param.unit))

            # Each checbox at its own event attached to eat
            cb.toggled.connect(lambda cb=cb,
                                      row=rowPosition,
                                      plotRef=self.getPlotTitle(): self.parameterClicked(cb, row, plotRef))
        
        self.statusBar.showMessage('Ready')



    def parameterCellClicked(self, row, column):
        """
        Handle event when user click on the cell containing the checkbox.
        """
        
        # If user clicks on the cell containing the checkbox
        if column==0:
            cb = self.tableWidgetParameters.cellWidget(row, 0)
            cb.toggle()



    def parameterClicked(self, cb, row, plotRef):
        """
        Handle event when user clicked on data line.
        Basically launch a plot
        """
        
        
        # If the checkbutton is checked, we downlad and plot the data
        params = qc.load_by_id(int(self.getRunId())).get_parameters()
        if cb:
            

            # When the user click to plot we disable the gui
            self.statusBar.showMessage('Load run data')
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.centralwidget.setEnabled(False)
            # Get parameters


            # Get data
            nbIndependent = self.getNbIndependentParameters()
            ds = qc.load_by_id(int(self.getRunId()))
            d = ds.get_parameter_data(params[row+nbIndependent].name)[params[row+nbIndependent].name]

            if nbIndependent==1:

                self.statusBar.showMessage('Launch 1D plot')

                data = self.getData1d(row)

                xLabel = params[0].name+' ['+params[0].unit+']'
                yLabel = params[row+1].name+' ['+params[row+1].unit+']'
                zLabel = None
            elif nbIndependent==2:

                self.statusBar.showMessage('Launch 2D plot')
                data = np.vstack((d[params[0].name], d[params[1].name], d[params[row+2].name])).T

                xLabel = params[0].name+' ['+params[0].unit+']'
                yLabel = params[1].name+' ['+params[1].unit+']'
                zLabel = params[row+2].name+' ['+params[row+2].unit+']'
            else:
                self.statusBar.showMessage('Plotter does not handle data whose dim>2')
            
            
            # Reference
            if plotRef in self._refs:
                self._refs[plotRef]['nbCurve'] += 1
            else:
                self._refs[plotRef] = {'nbCurve': 1}
        
            self.startPlotting(plotRef, data, xLabel, yLabel, zLabel)
        # We remove the curve if the curve is a 1d plot, 
        elif self._refs[plotRef]['plotType'] == '1d':
            # If there is more than one curve, we remove one curve
            if self._refs[plotRef]['nbCurve'] > 1:
                yLabel = params[row+1].name+' ['+params[row+1].unit+']'
                self._refs[plotRef]['plot'].removePlotDataItem(curveId=yLabel)
                self._refs[plotRef]['nbCurve'] -= 1
            else:
                self._refs[plotRef]['plot'].o()
                del(self._refs[plotRef])
        else:
            yLabel = params[row+2].name+' ['+params[row+2].unit+']'
            self._refs[plotRef]['plots'][yLabel].o()
            del(self._refs[plotRef]['plots'][yLabel])


    ###########################################################################
    #
    #
    #                           GUI
    #
    #
    ###########################################################################



    def updateProgressBar(self, val):
        self.progressBar.setValue(val)



    def clearLayout(self, layout):
        """
        Clear a pyqt layout, from:
        https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()



    def closeEvent(self, evnt):
        """
        Method called when closing the main app.
        Close every 1d and 2d plot opened.
        """
        
        for key in self._refs.keys():
            if self._refs[key]['plotType']=='1d':
                self._refs[key]['plot'].o()
            else:
                for subkey in self._refs[key]['plots'].keys():
                    self._refs[key]['plots'][subkey].o()



    def cleanCheckBox(self, windowTitle, runId, dependent=None):
        """
        Method called by the QDialog plot when the user close the plot window.
        We propagate that event to the mainWindow to uncheck the checkbox.
        """
        # If the current displayed parameters correspond to the one which has
        # been closed, we uncheck all the checkbox listed in the table
        if self.currentDatabase == windowTitle and self.getRunId() == runId:
            
            for row in range(self.tableWidgetParameters.rowCount()):
                widget = self.tableWidgetParameters.cellWidget(row, 0)
                widget.setChecked(False)



    ###########################################################################
    #
    #
    #                           QCoDes data handling methods
    #
    #
    ###########################################################################



    # From plottr
    def _get_names_of_standalone_parameters(self, paramspecs: List['ParamSpec']
                                            ) -> Set[str]:
        all_independents = set(spec.name
                            for spec in paramspecs
                            if len(spec.depends_on_) == 0)
        used_independents = set(d for spec in paramspecs for d in spec.depends_on_)
        standalones = all_independents.difference(used_independents)
        return standalones



    # From plottr
    def get_ds_structure(self, ds: 'DataSet'):
        """
        Return the structure of the dataset, i.e., a dictionary in the form
            {
                'dependent_parameter_name': {
                    'unit': unit,
                    'axes': list of names of independent parameters,
                    'values': []
                },
                'independent_parameter_name': {
                    'unit': unit,
                    'values': []
                },
                ...
            }
        Note that standalone parameters (those which don't depend on any other
        parameter and no other parameter depends on them) are not included
        in the returned structure.
        """

        structure = {}

        paramspecs = ds.get_parameters()

        standalones = self._get_names_of_standalone_parameters(paramspecs)

        for spec in paramspecs:
            if spec.name not in standalones:
                structure[spec.name] = {'unit': spec.unit, 'values': []}
                if len(spec.depends_on_) > 0:
                    structure[spec.name]['axes'] = list(spec.depends_on_)

        return structure



    # From plottr
    def get_ds_info(self, ds: 'DataSet', get_structure: bool = True):
        """
        Get some info on a DataSet in dict.

        if get_structure is True: return the datastructure in that dataset
        as well (key is `structure' then).
        """
        ret = {}
        ret['experiment'] = ds.exp_name
        ret['sample'] = ds.sample_name
        ret['name'] = ds.name

        _complete_ts = ds.completed_timestamp()
        if _complete_ts is not None:
            ret['completed date'] = _complete_ts[:10]
            ret['completed time'] = _complete_ts[11:]
        else:
            ret['completed date'] = ''
            ret['completed time'] = ''

        _start_ts = ds.run_timestamp()
        if _start_ts is not None:
            ret['started date'] = _start_ts[:10]
            ret['started time'] = _start_ts[11:]
        else:
            ret['started date'] = ''
            ret['started time'] = ''

        if get_structure:
            ret['structure'] = get_ds_structure(ds)

        ret['records'] = ds.number_of_results

        return ret



    def getTotalRun(self, refresh_db=False):
        """
        Return the total number of run in current database
        """

        if refresh_db:
            qc.initialise_or_create_database_at(os.path.join(self.currentPath, self.currentDatabase))
            datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id'))

            self.overview = {ds.run_id: self.get_ds_info(ds, get_structure=False)
                    for ds in datasets}

        return len(self.overview)



    def getNbDependentParameters(self):
        
        ds = qc.load_by_id(int(self.getRunId()))
        return len(ds.dependent_parameters)



    def getNbIndependentParameters(self):

        ds = qc.load_by_id(int(self.getRunId()))
        return len(ds.paramspecs) - len(ds.dependent_parameters)



    def getRunId(self):
        """
        Return the current selectec run id.
        """

        
        if self.LivePlot:
            return self.getTotalRun()
        else:
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            return self.tableWidgetDataBase.model().index(currentRow, 0).data()



    def getRunExperiment(self):
        """
        Return the experiment of the current selected run
        """
        
        
        if self.LivePlot:
            return self.overview[self.getTotalRun()]['experiment']
        else:
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            return self.tableWidgetDataBase.model().index(currentRow, 1).data()



    def getWindowTitle(self):
        """
        Return a title which will be used as a plot window title.
        """

        return self.currentDatabase



    def getPlotTitle(self):
        """
        Return a plot title in a normalize way displaying the folders and
        file name.
        """

        title = os.path.normpath(self.currentPath).split(os.path.sep)[2:]
        title = '/'.join(title)+'<br>'+str(self.getRunId())+' - '+self.getRunExperiment()
        return title



    def getCompleted(self):
        """
        Return the completed date and time of a run.
        Empty string when the run is not done.
        """

        if self.LivePlot:
            return self.overview[self.getTotalRun()]['completed date']+' '+self.overview[self.getTotalRun()]['completed date']
        else:
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            return self.tableWidgetDataBase.model().index(currentRow, 5).data()



    def isRunCompleted(self):
        """
        Return True when run is done, false otherwise
        """

        if len(self.getCompleted())==1:
            return False
        else:
            return True



    ###########################################################################
    #
    #
    #                           Live plotting
    #
    #
    ###########################################################################
    


    def livePlotUpdate(self):

        # If user selected database
        if self.currentDatabase is not None:

            # Check if database has one more run
            # if there is a new run, we launch a plot
            if self.oldTotalRun is not None:
                if self.oldTotalRun != self.getTotalRun(True):
                    
                    # We refresh the database display
                    self.dataBaseClicked()

                    # We refresh the run display
                    self.runClicked()

                    # We click on the first parameter, which will launch a plot
                    self.parameterCellClicked(0,0)

                    # We update the total number of run
                    self.oldTotalRun = self.getTotalRun()

                    # We save the fact that we have to update an existing live plot
                    self.livePlotFetchData = True

            else:
                self.oldTotalRun = self.getTotalRun(True)

        
        # If we have to update the data of a livePlot
        if self.livePlotFetchData:
            data = self.getData1d(0)
            self.livePlotPlot.updatePlotDataItem(data[:,0], data[:,1],
                                                 curveId=self.livePlotCurveId,
                                                 curveLegend=None,
                                                 autoRange=True)

            # If the run is done, we cancel the need to update the plot
            if self.isRunCompleted():
                self.livePlotFetchData = False



    def livePlotToggle(self):
        """
        When the user click the checkbox launching the liveplot mode
        """

        if self.checkBoxLivePlot.isChecked():
            
            # Launch the liveplot mode
            self.livePlotMode = True
            
            # Disable browsing
            self.listWidgetFolder.setEnabled(False)
            widgets = (self.labelPath.itemAt(i).widget() for i in range(self.labelPath.count())) 
            for widget in widgets:
                widget.setEnabled(False)

            # Launch a Qt timer which will periodically check if a new run is
            # launched
            self.livePlotTimer = QtCore.QTimer()
            self.livePlotTimer.timeout.connect(self.livePlotUpdate)
            self.livePlotTimer.setInterval(self.spinBoxLivePlot.value()*1000)
            self.livePlotTimer.start()
        else:
            
            # Stop live plot mode
            self.livePlotMode = False

            # Enable browsing again
            self.listWidgetFolder.setEnabled(True)
            widgets = (self.labelPath.itemAt(i).widget() for i in range(self.labelPath.count())) 
            for widget in widgets:
                widget.setEnabled(True)

            # Stop the Q1 timer
            self.livePlotTimer.stop()
            self.livePlotTimer.deleteLater()
            self.livePlotTimer = None



    def livePlotSpinBoxChanged(self, val):
        """
        When user modify the the spin box associated to the live plot timer
        """

        # If a Qt timer is running, we modify it following the user input.
        if self.livePlotTimer is not None:
            
            self.livePlotTimer.setInterval(self.spinBoxLivePlot.value()*1000)



    ###########################################################################
    #
    #
    #                           Plotting
    #
    #
    ###########################################################################



    def startPlotting(self, plotRef, data, xLabel, yLabel, zLabel):
        """
        Methods called once the data are downloaded by the data thread.

        """

        self.centralwidget.setEnabled(True)

        nbIndependent = self.getNbIndependentParameters()
        # try:
        if nbIndependent == 1:
            
            # If nbCurve is 1, we create the plot QDialog
            if self._refs[plotRef]['nbCurve'] == 1:
                p  = Plot1dApp(x           = data[:,0],
                               y           = data[:,1],
                               title       = self.getPlotTitle(),
                               xLabel      = xLabel,
                               yLabel      = yLabel,
                               windowTitle = self.getWindowTitle(),
                               runId = self.getRunId(),
                               cleanCheckBox  = self.cleanCheckBox,
                               curveId=yLabel)
                self._refs[plotRef]['plotType'] = '1d'
                self._refs[plotRef]['plot'] = p
                self._refs[plotRef]['plot'].show()

                if self.livePlotMode:
                    self.livePlotCurveId = yLabel
                    self.livePlotPlot = self._refs[plotRef]['plot']
            else:
                self._refs[plotRef]['plot'].addPlotDataItem(x      = data[:, 0],
                                                             y      = data[:, 1],
                                                             curveId= yLabel,
                                                             curveLabel=yLabel,
                                                             curveLegend=yLabel)
            


        elif nbIndependent==2:

            x, y, z = self.shapeData2d(data)
            
            p = Plot2dApp(x              = x,
                          y              = y,
                          z              = z,
                          title          = self.getPlotTitle(),
                          xLabel         = xLabel,
                          yLabel         = yLabel,
                          zLabel         = zLabel,
                          windowTitle    = self.getWindowTitle(),
                          runId          = self.getRunId(),
                          cleanCheckBox  = self.cleanCheckBox)
            self._refs[plotRef]['plotType'] = '2d'
            
            if self._refs[plotRef]['nbCurve'] == 1:
                self._refs[plotRef]['plots'] = {zLabel : p}
            else:
                self._refs[plotRef]['plots'][zLabel] = p

            self._refs[plotRef]['plots'][zLabel].show()
        
        # Plot is done, we unable the gui
        QtGui.QApplication.restoreOverrideCursor()
        self.statusBar.showMessage('Ready')



    ###########################################################################
    #
    #
    #                           Data 
    #
    #
    ###########################################################################



    def getData1d(self, row):
        """
        Return a 2d np array containing the x and y axis to be plotted.

        Paramters
        ---------

        row : int
            Row in the parameter table associated with the dependent parameter
            to plot
        """

        # Get data
        params = qc.load_by_id(int(self.getRunId())).get_parameters()
        nbIndependent = self.getNbIndependentParameters()
        ds = qc.load_by_id(int(self.getRunId()))
        d = ds.get_parameter_data(params[row+nbIndependent].name)[params[row+nbIndependent].name]


        # We try to load data
        # if there is none, we return an empty array
        try:
            data = np.vstack((d[params[0].name], d[params[row+1].name])).T
        except:
            data = np.array([[np.nan, np.nan]])

        return data



    def shapeData2d(self, d):
        """
        Shape the data for a 2d plot but mainly handled all kind of data error/missing/...
        """

        # get axis
        x = d[:,0]
        y = d[:,1]
        z = d[:,2]

        # Nb points in the 1st dimension
        xn = len(np.unique(x))

        # Nb points in the 2nd dimension
        xx = np.array([])
        for i in np.unique(x):
            xx = np.append(xx, len(x[x==i]))
        yn = int(xx.max())

        # If interuption, we calculated the number of missing point and add them
        if len(np.unique(xx)) != 1:

            p = np.full(int(xx.max() - xx.min()), np.nan)

            x = np.append(x, p)
            y = np.append(y, p)
            z = np.append(z, p)
            
        # We create 2D arrays for each dimension
        x = x.reshape(xn, yn)
        y = y.reshape(xn, yn)
        z = z.reshape(xn, yn)

        # Once the shape is corrected, we sort the data
        m = x[:,0].argsort()
        x = x[m]
        y = y[m]
        z = z[m]


        # If the data has a rectangular shape (usual 2d measurement)
        if len(np.unique(y[:,0])) == 1:
            
            # Take a slice of x
            xx = x[:,0]

            # Find a row of y containing only non nan data
            i = 0
            for i in y:
                if not np.any(np.isnan(i)):
                    yy = i
                    break
                i+=1
            
            zz = z
        # If not (like a auto freq measurement )
        else:
            xx = x[:,0]
            # Create a bigger array containing sorted data in the same bases
            # New y axis containing all the previous y axes
            yy = np.arange(y[~np.isnan(y)].min(), y[~np.isnan(y)].max()+y[0][1]-y[0][0], y[0][1]-y[0][0])

            # For each z scan we create a new z array
            zz = np.array([])
            for i, j in zip(y, z):

                p = np.abs(yy-i[0]).argmin()
                
                v  = np.full(p, np.nan)
                vv = np.full(len(yy)-p-len(i), np.nan)

                zz = np.append(zz, np.concatenate((v, j, vv)))

            zz = zz.reshape(len(zz)/len(yy), len(yy))

        return xx, yy, zz


