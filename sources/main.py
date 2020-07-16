# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets, QtTest
import os
import numpy as np
import pandas as pd
from matplotlib.pyplot import colormaps
from matplotlib import cm as plt_cm
import tempfile
import sys 
import qcodes as qc
from itertools import chain
from pprint import pformat 
from typing import Dict, List, Set
from operator import attrgetter
sys.path.append('ui')
sys.path.append('sources')

# Correct bug with pyqtgraph and python3.8 by replacing function name
try:
    import pyqtgraph as pg
except AttributeError:
    import time
    time.clock = time.perf_counter
    import pyqtgraph as pg


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
        # Connect event
        self.tableWidgetDataBase.currentCellChanged.connect(self.runClicked)

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

        self.currentDatabase    = None
        self.oldTotalRun        = None
        self.livePlotMode       = False
        self.livePlotFetchData  = False
        self.livePlotTimer      = None


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

            # If folder
            if os.path.isdir(abs_filename):
                
                # If looks like a BlueFors log folder
                if self.isBlueForsFolder(file):
                    item =  QtGui.QListWidgetItem(file)
                    item.setIcon(QtGui.QIcon('ui/pictures/bluefors.png'))
                    self.listWidgetFolder.addItem(item)
                # Other folders
                else:
                    item =  QtGui.QListWidgetItem(file)
                    item.setIcon(QtGui.QIcon('ui/pictures/folder.png'))
                    self.listWidgetFolder.addItem(item)
            # If files
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

            # If the folder is a BlueFors folder
            if self.isBlueForsFolder(self.currentDatabase):
                
                self.blueForsFolderClicked(directory=nextPath)
            # If the folder is a regulat folder
            elif os.path.isdir(nextPath):
                self.statusBar.showMessage('Update')
                self.folderClicked(e=False, directory=nextPath)
                self.statusBar.showMessage('Ready')
            # If it is a database
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
    #                           BlueFors log browsing
    #
    #
    ###########################################################################



    @staticmethod
    def isBlueForsFolder(folderName:str) -> bool:
        """
        Return True if a string follow blueFors log folder name pattern.
        """
    
        return len(folderName.split('-'))==3 and all([len(i)==2 for i in folderName.split('-')]) == True



    def blueForsFolderClicked(self, directory):
        """
        When user click on a BlueFors folder while browsing files
        """
        
        self.statusBar.showMessage('Load BlueFors log')

        # Get the BF folder name
        bfName = os.path.basename(os.path.normpath(directory))

        ## Update label
        self.labelCurrentRun.setText('BF log folder: '+bfName)
        self.labelPlotTypeCurrent.setText('1d')


        ## Fill the tableWidgetParameters with the run parameters

        # When we fill the table, we need to check if there is already
        # a plotWindow of that file opened.
        # If it is the case, we need to checked the checkBox which are plotted
        # in the plotWindow.
        # Our aim is then to get the list of the checkBox which has to be checked.
        checkedDependents = []
        # If a plotWindow is already open
        if len(self._refs) > 0:
            # We iterate over all plotWindow
            for key, val in self._refs.items():
                # For 1d plot window
                if self.getPlotWindowType(key) == '1d':
                    if self.currentDatabase == val['plot'].windowTitle:
                        checkedDependents = val['plot'].curves.keys()


        # Clean GUI
        self.tableWidgetDataBase.setSortingEnabled(False)
        self.tableWidgetDataBase.setRowCount(0)
        self.tableWidgetDataBase.setSortingEnabled(True)

        self.tableWidgetParameters.setSortingEnabled(False)
        self.tableWidgetParameters.setRowCount(0)
        self.tableWidgetParameters.setSortingEnabled(True)
        
        self.textEditMetadata.clear()


        for file in sorted(os.listdir(directory)):
            
            fileName = file[:-13]
            
            # We only show file handled by the plotter
            if fileName in config.keys():
                rowPosition = self.tableWidgetParameters.rowCount()
                self.tableWidgetParameters.insertRow(rowPosition)

                cb = QtWidgets.QCheckBox()

                # We check if that parameter is already plotted
                if config[fileName] in checkedDependents:
                    cb.setChecked(True)

                self.tableWidgetParameters.setCellWidget(rowPosition, 0, cb)
                self.tableWidgetParameters.setItem(rowPosition, 1, QtGui.QTableWidgetItem(fileName))

                # Each checkbox at its own event attached to it
                cb.toggled.connect(lambda cb=cb,
                                        filePath=os.path.join(directory, file),
                                        plotRef=self.getPlotTitle(): self.blueForsLogClicked(cb, filePath, plotRef))
            


        self.statusBar.showMessage('Ready')



    def blueForsLogClicked(self, cb, filePath, plotRef):
        """
        When user clicked on BF log file.
        Basically, launch a 1d plot window.
        """


        fileName = os.path.basename(os.path.normpath(filePath))[:-13]
        if cb:
            self.statusBar.showMessage('Load BlueFors data')
            
            # Maxigauges file (all pressure gauges)
            if fileName == 'maxigauge':

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

                df.index = pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S')
                
                for i in range(1, 7):
                    
                    # Reference
                    if plotRef in self._refs:
                        self._refs[plotRef]['nbCurve'] += 1
                    else:
                        self._refs[plotRef] = {'nbCurve': 1}

                    name = 'ch'+str(i)+'_pressure'
                    
                    self.statusBar.showMessage('Launch 1D plot')
                    self.startPlotting(plotRef=plotRef,
                                       data=(df[name].index.astype(np.int64).values//1e9, df[name]),
                                       xLabel='Time',
                                       yLabel=config[fileName][name[:3]])
                
                # Once all is plotting we autorange
                self._refs[plotRef]['plot'].plotItem.vb.autoRange()

                # and we set y log mode True
                QtTest.QTest.qWait(100) # To avoid an overflow error
                self._refs[plotRef]['plot'].checkBoxLogY.toggle()

            # Thermometers files
            else:
                df = pd.read_csv(filePath,
                                delimiter=',',
                                names=['date', 'time', 'y'],
                                header=None)

                # There is a space before the day
                df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')


                # Reference
                if plotRef in self._refs:
                    self._refs[plotRef]['nbCurve'] += 1
                else:
                    self._refs[plotRef] = {'nbCurve': 1}


                self.statusBar.showMessage('Launch 1D plot')
                self.startPlotting(plotRef=plotRef,
                                   data=(df['y'].index.astype(np.int64).values//1e9, df['y']),
                                   xLabel='Time',
                                   yLabel=config[fileName])


        else:

            # If there is more than one curve, we remove one curve
            if self._refs[plotRef]['nbCurve'] > 1:
                yLabel = config[fileName]

                # If maxigauge file, we have to remove all the curves at once
                if yLabel == config['maxigauge']:
                    for i in range(1, 7):
                        
                        curveId = config[fileName]['ch'+str(i)]
                        self._refs[plotRef]['plot'].removePlotDataItem(curveId=curveId)
                        self._refs[plotRef]['nbCurve'] -= 1
                else:
                    self._refs[plotRef]['plot'].removePlotDataItem(curveId=yLabel)
                    self._refs[plotRef]['nbCurve'] -= 1
            # If there is one curve we close the plot window
            else:
                self._refs[plotRef]['plot'].o()
                del(self._refs[plotRef])



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
        
        # Catch error at the open of a db
        try:
            qc.initialise_or_create_database_at(os.path.join(self.currentPath, self.currentDatabase))
        except:
            self.statusBar.showMessage("Can't load database")
            return


        self.statusBar.showMessage('Get database information')
        datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id'))


        # Fill table with new information
        totalRun = self.getTotalRun()
        for ds in datasets: 
            rowPosition = self.tableWidgetDataBase.rowCount()

            
            self.statusBar.showMessage('Get database information: run '+str(ds.run_id)+'/'+str(totalRun))

            self.tableWidgetDataBase.insertRow(rowPosition)

            info = self.get_ds_info(ds, get_structure=False)
            
            self.tableWidgetDataBase.setItem(rowPosition, 0, MyTableWidgetItem(str(ds.run_id)))
            self.tableWidgetDataBase.setItem(rowPosition, 1, QtGui.QTableWidgetItem(info['experiment']))
            self.tableWidgetDataBase.setItem(rowPosition, 2, QtGui.QTableWidgetItem(info['sample']))
            self.tableWidgetDataBase.setItem(rowPosition, 3, QtGui.QTableWidgetItem(info['name']))
            self.tableWidgetDataBase.setItem(rowPosition, 4, QtGui.QTableWidgetItem(info['started date']+' '+info['started time']))
            self.tableWidgetDataBase.setItem(rowPosition, 5, QtGui.QTableWidgetItem(info['completed date']+' '+info['completed time']))
            self.tableWidgetDataBase.setItem(rowPosition, 6, MyTableWidgetItem(str(info['records'])))


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
        
        # When the user click on another database while having already clicked
        # on a run, the runClicked event is happened even if no run have been clicked
        # This is due to the "currentCellChanged" event handler.
        # We catch that false event and return nothing
        if self.getRunId() is None:
            return

        self.statusBar.showMessage('Load run parameters')

        ## Update label
        self.labelCurrentRun.setText(str(self.getRunId()))
        self.labelCurrentMetadata.setText(str(self.getRunId()))
        self.labelPlotTypeCurrent.setText(str(self.getNbIndependentParameters())+'d')



        ## Fill the tableWidgetParameters with the run parameters

        # When we fill the table, we need to check if there is already
        # a plotWindow of that file opened.
        # If it is the case, we need to checked the checkBox which are plotted
        # in the plotWindow.
        # Our aim is then to get the list of the checkBox which has to be checked.
        checkedDependents = []
        # If a plotWindow is already open
        if len(self._refs) > 0:
            # We iterate over all plotWindow
            for key, val in self._refs.items():
                # For 1d plot window
                if self.getPlotWindowType(key) == '1d':
                    if self.currentDatabase == val['plot'].windowTitle:
                        if self.getRunId() == val['plot'].runId:
                            checkedDependents = list(val['plot'].curves.keys())
                # For 2d plot window
                else:
                    for plot2d in val['plot'].values():
                        if self.currentDatabase == plot2d.windowTitle:
                            if self.getRunId() == plot2d.runId:
                                checkedDependents.append(plot2d.zLabel)
            

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

            # Each checkbox at its own event attached to it
            cb.toggled.connect(lambda cb=cb,
                                      row=rowPosition,
                                      plotRef=self.getPlotTitle(): self.parameterClicked(cb, row, plotRef))
        


        ## Fill the listWidgetMetada with the station snapshot
        self.textEditMetadata.clear()
        ds = qc.load_by_id(int(self.getRunId()))
        self.textEditMetadata.setText(pformat(ds.snapshot).replace('{', '').replace('}', '').replace("'", ''))



        self.statusBar.showMessage('Ready')



    def parameterCellClicked(self, row, column):
        """
        Handle event when user click on the cell containing the checkbox.
        Basically toggle the checkbox and launch the event associated to the
        checkbox
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

                data = self.getData2d(row)

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

        # If the checkbox is unchecked
        else:
            # We are dealing with 2d plot
            if self.getPlotWindowType(plotRef) == '2d':
                zLabel = params[row+2].name+' ['+params[row+2].unit+']'
                self._refs[plotRef]['plot'][zLabel].o()
                del(self._refs[plotRef]['plot'][zLabel])

            # We are dealing with 1d plot
            else:
                # If there is more than one curve, we remove one curve
                if self._refs[plotRef]['nbCurve'] > 1:
                    yLabel = params[row+1].name+' ['+params[row+1].unit+']'
                    self._refs[plotRef]['plot'].removePlotDataItem(curveId=yLabel)
                    self._refs[plotRef]['nbCurve'] -= 1
                # If there is one curve we close the plot window
                else:
                    self._refs[plotRef]['plot'].o()
                    del(self._refs[plotRef])



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
            # For 2d plot
            if self.getPlotWindowType(key) == '2d':
                keyToDelete = list(self._refs[key]['plot'].keys())
                for subkey in keyToDelete:
                    self._refs[key]['plot'][subkey].o()
            # For 1d plot
            else:
                self._refs[key]['plot'].o()
    


    def cleanCheckBox(self, windowTitle, runId, dependent=None):
        """
        Method called by the QDialog plot when the user close the plot window.
        We propagate that event to the mainWindow to uncheck the checkbox.
        """

        if self.currentDatabase == windowTitle and self.getRunId() == runId:
            # If 1d plot
            if dependent is None:
                # If the current displayed parameters correspond to the one which has
                # been closed, we uncheck all the checkbox listed in the table
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 0)
                    widget.setChecked(False)
            # If 2d plot
            else:
                # We uncheck only the plotted parameter
                targetedZaxis = dependent.split('[')[0][:-1]
                for row in range(self.tableWidgetParameters.rowCount()):
                    if targetedZaxis == self.tableWidgetParameters.item(row, 1).text():
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

        return len(datasets)



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

        if self.livePlotMode:
            return self.getTotalRun()
        else:
            currentRow = self.tableWidgetDataBase.currentIndex().row()
            return self.tableWidgetDataBase.model().index(currentRow, 0).data()



    def getRunExperiment(self):
        """
        Return the experiment of the current selected run
        """
        
        
        if self.livePlotMode:

            datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id'))
            
            info = self.get_ds_info(datasets[-1], get_structure=False)
            return info['experiment']
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

        # If BlueFors log files
        if self.isBlueForsFolder(self.currentDatabase):
            return self.currentDatabase
        else:
            title = os.path.normpath(self.currentPath).split(os.path.sep)[2:]
            title = '/'.join(title)+'<br>'+str(self.getRunId())+' - '+self.getRunExperiment()
            return title



    def getCompleted(self):
        """
        Return the completed date and time of a run.
        Empty string when the run is not done.
        """

        if self.livePlotMode:

            datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id'))
            
            info = self.get_ds_info(datasets[-1], get_structure=False)
            return info['completed date']+' '+info['completed date']
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



    def getLivePlotRef(self):
        
        
        returnKey = None
        # We get which open plot window is the liveplot one
        for key, val in self._refs.items():
            if val['livePlot']:
                returnKey = key

        return returnKey



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
            
            self.statusBar.showMessage('Fetching data')

            # We get which open plot window is the liveplot one
            livePlotRef = self.getLivePlotRef()
            
            if self.getPlotWindowType(livePlotRef) == '1d':
                
                # We get which parameters has to be updated
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 0)
                    
                    # For every checked parameter, we update the data
                    if widget.isChecked():
                        data = self.getData1d(row)

                        params = qc.load_by_id(int(self.getRunId())).get_parameters()
                        yLabel = params[row+1].name+' ['+params[row+1].unit+']'

                        self._refs[livePlotRef]['plot'].updatePlotDataItem(data[0], data[1],
                                                        curveId=yLabel,
                                                        curveLegend=None,
                                                        autoRange=True)

            else:
                # We get which parameters has to be updated
                for row in range(self.tableWidgetParameters.rowCount()):
                    widget = self.tableWidgetParameters.cellWidget(row, 0)
                    
                    # For every checked parameter, we update the data
                    if widget.isChecked():

                        # We get the 2d plot reference only the plotted parameter
                        zLabel = self.tableWidgetParameters.item(row, 1).text()+ ' ['+\
                                 self.tableWidgetParameters.item(row, 2).text()+ ']'

                        # We get the colormap data
                        x, y, z = self.getData2d(row)

                        # We update the 2d plot data
                        self._refs[livePlotRef]['plot'][zLabel].updateImageItem(x, y, z)

                        # If there are slices, we update them as well
                        if len(self._refs[livePlotRef]['plot'][zLabel].infiniteLines)>0:
                            for curveId, lineItem in self._refs[livePlotRef]['plot'][zLabel].infiniteLines.items():
                                
                                # We need the data of the slice
                                sliceX, sliceY, sliceLegend = self._refs[livePlotRef]['plot'][zLabel].getDataSlice(lineItem)

                                # We find its orientation
                                if lineItem.angle == 90:
                                    sliceOrientation = 'vertical'
                                else:
                                    sliceOrientation = 'horizontal'

                                # We update the slice data
                                self._refs[livePlotRef]['plot'][zLabel]\
                                .linked1dPlots[sliceOrientation]\
                                .updatePlotDataItem(x           = sliceX,
                                                    y           = sliceY,
                                                    curveId     = curveId,
                                                    curveLegend = sliceLegend,
                                                    autoRange   = True)


            self.statusBar.showMessage('Plot updated')

            # If the run is done
            if self.isRunCompleted():

                self.statusBar.showMessage('Run done')

                # We remove the livePlotFlag attached to the plot window
                livePlotRef = self.getLivePlotRef()
                self._refs[livePlotRef]['livePlot'] = False

                # We cancel the need to update the plot
                self.livePlotFetchData = False

                # We update the database to display the completed and records info
                self.dataBaseClicked()


    def livePlotToggle(self):
        """
        When the user click the checkbox launching the liveplot mode
        """

        if self.checkBoxLivePlot.isChecked():
            
            # Launch the liveplot mode
            self.livePlotMode = True
            
            # Disable browsing
            self.listWidgetFolder.setEnabled(False)
            self.tableWidgetDataBase.setEnabled(False)
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
            self.tableWidgetDataBase.setEnabled(True)
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



    def getPlotWindowType(self, ref):

        if isinstance(self._refs[ref]['plot'], dict):
            return '2d'
        else:
            return '1d'
        



    def startPlotting(self, plotRef, data, xLabel, yLabel, zLabel=None):
        """
        Methods called once the data are downloaded by the data thread.

        """

        self.centralwidget.setEnabled(True)

        # 1D plot
        if len(data) == 2:
            
            # If nbCurve is 1, we create the plot QDialog
            if self._refs[plotRef]['nbCurve'] == 1:

                p = Plot1dApp(x              = data[0],
                              y              = data[1],
                              title          = self.getPlotTitle(),
                              xLabel         = xLabel,
                              yLabel         = yLabel,
                              windowTitle    = self.getWindowTitle(),
                              runId          = self.getRunId(),
                              cleanCheckBox  = self.cleanCheckBox,
                              curveId        = yLabel,
                              timestampXAxis=self.isBlueForsFolder(self.currentDatabase))

                self._refs[plotRef]['plot']     = p
                self._refs[plotRef]['livePlot'] = self.livePlotMode
                self._refs[plotRef]['plot'].show()

            # If the QDialog already exists, we add a curve to it
            else:
                self._refs[plotRef]['plot'].addPlotDataItem(x            = data[0],
                                                            y            = data[1],
                                                            curveId      = yLabel,
                                                            curveLabel   = yLabel,
                                                            curveLegend  = yLabel)
            


        # 2D plot
        elif len(data) == 3:
            
            p = Plot2dApp(x              = data[0],
                          y              = data[1],
                          z              = data[2],
                          title          = self.getPlotTitle(),
                          xLabel         = xLabel,
                          yLabel         = yLabel,
                          zLabel         = zLabel,
                          windowTitle    = self.getWindowTitle(),
                          runId          = self.getRunId(),
                          cleanCheckBox  = self.cleanCheckBox)

            self._refs[plotRef]['livePlot'] = self.livePlotMode

            # If user wants to plot more than one parameter we launch one plot
            # window per parameter
            if self._refs[plotRef]['nbCurve'] == 1:
                self._refs[plotRef]['plot'] = {zLabel : p}
            else:
                self._refs[plotRef]['plot'][zLabel] = p

            self._refs[plotRef]['plot'][zLabel].show()
        
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

        Parameters
        ----------

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
            # data = np.vstack((d[params[0].name], d[params[row+1].name])).T
            data = d[params[0].name], d[params[row+1].name]
        except:
            data = np.array([np.nan]), np.array([np.nan])

        return data



    def getData2d(self, row):
        """
        Return a 2d np array containing the x and y z axis to be plotted.

        Parameters
        ----------

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
            data = self.shapeData2d(d[params[0].name], d[params[1].name], d[params[row+2].name])
        except:
            # We have to send [0,1] for the z axis when no data to avoid bug with the histogram
            data = np.array([0, 1]), np.array([0, 1]), np.array([[0, 1],[0, 1]])

        return data



    def shapeData2d(self, x, y, z):
        """
        Shape the data for a 2d plot but mainly handled all kind of data error/missing/...

        Return x and y as a 1d array, ready to be used for the 2d plot
        and z as a 2d array.
        In case of non regular grid, the y axis is approximated.
        """
        
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
            yd = np.gradient(np.sort(y[0])).min()
            yy = np.arange(y[~np.isnan(y)].min(), y[~np.isnan(y)].max()+yd*2, yd)


            # For each z scan we create a new z array
            zz = np.array([])
            for y_current, z_current in zip(y, z):
                
                # Find the index of the current y axis on the global y axis
                p = np.abs(yy-y_current[0]).argmin()
                
                # Find the number of nan to insert at the beginning
                v  = np.full(p, np.nan)

                # Find the number of nan to insert at the end
                vv = np.full(len(yy)-p-len(y_current), np.nan)

                # Build the new z axis
                zz = np.append(zz, np.concatenate((v, z_current, vv)))

            zz = zz.reshape(int(len(zz)/len(yy)), len(yy))
        
        return xx, yy, zz


