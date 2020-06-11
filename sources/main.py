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
from operator import attrgetter
sys.path.append('ui')
sys.path.append('sources')

from ui import main
from config import config
import data
from plot_1d_app import Plot1dApp
from plot_2d_app import Plot2dApp

pg.setConfigOption('background', config['pyqtgraphBackgroundColor'])


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

        

        # SMB connection object
        # self.conn = conn

        # Connect UI
        # self.btnBrowse.clicked.connect(self.folderClicked)
        # self.pushButtonUp.clicked.connect(self.goParentFolder)
        # self.pushButtonUp.setEnabled(False)
        self.listWidgetFolder.clicked.connect(self.itemClicked)
        # self.listWidgetFolder.currentItemChanged.connect(self.itemClicked)
        # self.listWidgetFolder.itemDoubleClicked.connect(self.itemDoubleClicked)
        
        # Resize the cell to the column content automatically
        self.tableWidgetDataBase.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # Select row instead of cell
        self.tableWidgetDataBase.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # Connect event
        self.tableWidgetDataBase.clicked.connect(self.runClicked)



        # # Resize the cell to the column content automatically
        # self.tableWidgetParameters.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # # Select row instead of cell
        # self.tableWidgetParameters.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # # Connect event
        # self.tableWidgetParameters.clicked.connect(self.parameterClicked)


        self.statusBar.showMessage('Ready')

        # Default folder is the data vault on varys except if we are on test mode
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
            # if file[-4:] == '.dir' or file[-4:] == '.csv':
            
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
                    item =  QtGui.QListWidgetItem(file)
                    item.setIcon(QtGui.QIcon('ui/pictures/file.png'))
                    self.listWidgetFolder.addItem(item)
                

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
            self.statusBar.showMessage('Update')

            # Get current item
            self.currentDatabase = self.listWidgetFolder.currentItem().text()

            nextPath = os.path.join(self.currentPath, self.currentDatabase)
            if os.path.isdir(nextPath):
                self.folderClicked(e=False, directory=nextPath)
            else:
                self.dataBaseClicked()
                # # We check of the user double click ir single click
                #                         self._itemClicked)

            # Job done, we restor the usual cursor 
            QtGui.QApplication.restoreOverrideCursor()
            self.statusBar.showMessage('Ready')
        
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
        self.labelCurrentDataBase.setText(self.currentDatabase)

        # Get database
        path_db = os.path.join(self.currentPath, self.currentDatabase)
        db = qc.initialise_or_create_database_at(path_db)

        datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id')
        )

        overview = {ds.run_id: self.get_ds_info(ds, get_structure=False)
                for ds in datasets}


        self.tableWidgetDataBase.setSortingEnabled(False)
        self.tableWidgetDataBase.setRowCount(0)
        self.tableWidgetDataBase.setSortingEnabled(True)
        for key, val in overview.items(): 
            rowPosition = self.tableWidgetDataBase.rowCount()

            self.tableWidgetDataBase.insertRow(rowPosition)


            self.tableWidgetDataBase.setItem(rowPosition, 0, MyTableWidgetItem(str(key)))
            self.tableWidgetDataBase.setItem(rowPosition, 1, QtGui.QTableWidgetItem(val['experiment']))
            self.tableWidgetDataBase.setItem(rowPosition, 2, QtGui.QTableWidgetItem(val['sample']))
            self.tableWidgetDataBase.setItem(rowPosition, 3, QtGui.QTableWidgetItem(val['name']))
            self.tableWidgetDataBase.setItem(rowPosition, 4, QtGui.QTableWidgetItem(val['started date']+' '+val['started time']))
            self.tableWidgetDataBase.setItem(rowPosition, 5, QtGui.QTableWidgetItem(val['completed date']+' '+val['completed time']))
            self.tableWidgetDataBase.setItem(rowPosition, 6, MyTableWidgetItem(str(val['records'])))



    def runClicked(self):
        """
        When clicked display the measured dependent parameters in the 
        tableWidgetPtableWidgetParameters
        """

        # Update label
        self.labelCurrentRun.setText(self.getRunId())

        # Update label
        self.labelCurrentMetadata.setText(self.getRunId())

        # Get parameters list without the independent parameters
        params = qc.load_by_id(self.getRunId()).get_parameters()[self.getNbIndependentParameters():]

        self.tableWidgetParameters.setSortingEnabled(False)
        self.tableWidgetParameters.setRowCount(0)
        self.tableWidgetParameters.setSortingEnabled(True)
        for param in params:
            rowPosition = self.tableWidgetParameters.rowCount()


            self.tableWidgetParameters.insertRow(rowPosition)

            cb = QtWidgets.QCheckBox()

            self.tableWidgetParameters.setCellWidget(rowPosition, 0, cb)
            self.tableWidgetParameters.setItem(rowPosition, 1, QtGui.QTableWidgetItem(param.name))
            self.tableWidgetParameters.setItem(rowPosition, 2, QtGui.QTableWidgetItem(param.unit))

            # Each checbox at its own event attached to eat
            cb.toggled.connect(lambda cb=cb,
                                      row=rowPosition,
                                      plotRef=self.getPlotTitle(): self.parameterClicked(cb, row, plotRef))



    def parameterClicked(self, cb, row, plotRef):
        """
        Handle event when user clicked on data line.
        Basically launch a plot
        """
        

        # If the checkbutton is checked, we downlad and plot the data
        params = qc.load_by_id(self.getRunId()).get_parameters()
        if cb:

            # Get parameters

            # When the user click to plot we disable the gui
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.statusBar.showMessage('Plotting')
            self.centralwidget.setEnabled(False)

            # Get data
            nbIndependent = self.getNbIndependentParameters()
            ds = qc.load_by_run_spec(captured_run_id=int(self.getRunId()))
            d = ds.get_parameter_data(params[row+nbIndependent].name)[params[row+nbIndependent].name]

            if nbIndependent==1:

                data = np.vstack((d[params[0].name], d[params[row+1].name])).T

                xLabel = params[0].name+' ['+params[0].unit+']'
                yLabel = params[row+1].name+' ['+params[row+1].unit+']'
                zLabel = None
            elif nbIndependent==2:

                data = np.vstack((d[params[0].name], d[params[1].name], d[params[row+2].name])).T

                xLabel = params[0].name+' ['+params[0].unit+']'
                yLabel = params[1].name+' ['+params[1].unit+']'
                zLabel = params[row+2].name+' ['+params[row+2].unit+']'
            else:
                self.statusBar.showMessage('Plotter does not handle data whose dim>2')
                raise ValueError('Plotter does not handle data whose dim>2')
            
            
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



    def getNbDependentParameters(self):

        ds = qc.load_by_run_spec(captured_run_id=int(self.getRunId()))
        return len(ds.dependent_parameters)



    def getNbIndependentParameters(self):

        ds = qc.load_by_run_spec(captured_run_id=int(self.getRunId()))
        return len(ds.paramspecs) - len(ds.dependent_parameters)



    def getRunId(self):

        currentRow = self.tableWidgetDataBase.currentIndex().row()
        return self.tableWidgetDataBase.model().index(currentRow, 0).data()



    def getRunExperience(self):

        currentRow = self.tableWidgetDataBase.currentIndex().row()
        return self.tableWidgetDataBase.model().index(currentRow, 1).data()



    def getWindowTitle(self):

        return self.currentDatabase



    def getPlotTitle(self):
        """
        Return a plot title in a normalize way displaying the folders and
        file name.
        """

        title = os.path.normpath(self.currentPath).split(os.path.sep)[2:]
        title = '/'.join(title)+'<br>'+self.getRunId()+' - '+self.getRunExperience()
        return title



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


