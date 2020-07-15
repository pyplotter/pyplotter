# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets
import os
import numpy as np
import ConfigParser
import pyqtgraph as pg
from matplotlib.pyplot import colormaps
from matplotlib import cm as plt_cm
import tempfile

from ui import main
from config import config
import data
from plot_1d_app import Plot1dApp
from plot_2d_app import Plot2dApp

pg.setConfigOption('background', config['pyqtgraphBackgroundColor'])


class MainApp(QtWidgets.QMainWindow, main.Ui_MainWindow):



    def __init__(self, conn=None, parent=None):

        super(MainApp, self).__init__(parent)
        self.setupUi(self)

        # SMB connection object
        self.conn = conn

        # Connect UI
        self.btnBrowse.clicked.connect(self.folderClicked)
        self.pushButtonUp.clicked.connect(self.goParentFolder)
        self.pushButtonUp.setEnabled(False)
        self.listWidget.clicked.connect(self.itemClicked)
        # self.listWidget.currentItemChanged.connect(self.itemClicked)
        # self.listWidget.itemDoubleClicked.connect(self.itemDoubleClicked)


        self.statusBar.showMessage('Ready')

        # Default folder is the data vault on varys except if we are on test mode
        if 'test' in os.listdir('.'):
            self.currentPath = os.path.join('test.dir')
        else:
            self.currentPath = os.path.join(*config['path'])

        # References
        self._refs = {}

        # Attribute to control the display of data file info when user click of put focus on a item list
        self.folderUpdating  = False # To avoid calling the signal when updating folder content
        self.guiInitialized = True # To avoid calling the signal when starting the GUI

        # By default, we browse the root folder
        self.folderClicked(e=False, directory=self.currentPath)



    ######
    #
    #
    # Browsing
    #
    #
    ######




    def goParentFolder(self, e, directory=None):
        """
        Handle event when user click on the go up button.
        Change the current folder by the parent one.
        Stop when arrive in the root folder.
        """

        self.folderClicked(False, directory=os.path.join(*os.path.split(self.currentPath)[:-1]))



    def checkSession(self):
        """
        Check if there is a session file in the current folder.
        If yes, return True and the list of stared files.
        """

        conf = ConfigParser.ConfigParser()
        if 'test' in os.listdir('.'):
            conf.read(os.path.join(self.currentPath, 'session.ini'))
        else:
            conf.readfp(self.getFile(os.path.join(self.currentPath, 'session.ini')))
        filesStared = conf.get('Tags', 'datasets')

        # If the file exist
        if len(filesStared) > 2:
            # Get the file number having stars
            filesStaredDict = eval(filesStared)
            filesStared = [int(k[1:6]) for k, v in filesStaredDict.iteritems() if str(v) == "set(['star'])"]

        return True, filesStared



    def getFile(self, filePath):
        """
        Return a file object through the SMB connection
        """
        if 'test' in os.listdir('.'):
            fileObj = open(filePath)
        else:
            try:
                fileObj = tempfile.NamedTemporaryFile()
                self.conn.retrieveFile(config['share_name'], filePath, fileObj)
                fileObj.seek(0)
            except:
                self.statusBar.showMessage('Failed to retrieve file')
                QtGui.QApplication.restoreOverrideCursor()
                raise ValueError('Failed to retrieve file')

        return fileObj



    def isFolder(self):
        """
        Return True if the cliked item is a folder
        """

        if 'test' in os.listdir('.'):
            files = os.listdir(self.currentPath)
            for item in files:
                if self.currentItem == item[:-4]:
                    if item[-3:] == 'dir':
                        folder = True
                    else:
                        folder = False

        else:
            files = self.conn.listPath(config['share_name'], self.currentPath)
            for item in files:
                if self.currentItem == item.filename[:-4]:
                    if item.filename[-3:] == 'dir':
                        folder = True
                    else:
                        folder = False
        
        return folder



    def dataClicked(self, cb, t, nbDependent, filePath):
        """
        Handle event when user clicked on data line.
        Basically launch a plot
        """

        # If the checkbutton is checked, we downlad and plot the data
        if cb:
            # When the user click to plot we disable the gui
            self.centralwidget.setEnabled(False)
            # self.loadingData = True
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            p = os.path.join(self.currentPath, self.currentItem+'.csv')

            self.statusBar.showMessage('Download data ('+str(self.fileSize/1e6)+' MB)')

            
            self.progressBar = QtWidgets.QProgressBar()
            self.statusBar.addPermanentWidget(self.progressBar)

            # Import data from another thread
            worker = data.ImportDataThread(conn        = self.conn,
                                           share_name  = config['share_name'],
                                           filePath    = p,
                                           fileSize    = self.fileSize,
                                           nbDependent = nbDependent)

            thread = QtCore.QThread()
            worker.moveToThread(thread)

            # Signal
            worker.sigDone.connect(self.startPlotting)
            worker.sigUpdateProgressBar.connect(self.updateProgressBar)

            # Start thread
            thread.started.connect(worker.work)
            thread.start()

            # Reference
            if filePath in self._refs:
                self._refs[filePath]['thread']   = thread
                self._refs[filePath]['worker']   = worker
                self._refs[filePath]['nbCurve'] += 1
            else:
                self._refs[filePath] = {'thread' : thread,
                                        'worker' : worker,
                                        'nbCurve': 1}
        
        # We remove the curve if the curve is a 1d plot, 
        elif self._refs[filePath]['plotType'] == '1d':
            # If there is more than one curve, we remove one curve
            if self._refs[filePath]['nbCurve'] > 1:
                self._refs[filePath]['plot'].removePlotDataItem(t)
                self._refs[filePath]['nbCurve'] -= 1
            else:
                self._refs[filePath]['plot'].o()
                del(self._refs[filePath])
        else:
            self._refs[filePath]['plots'][t].o()
            del(self._refs[filePath]['plots'][t])



    def updateProgressBar(self, val):
        self.progressBar.setValue(val)



    def itemDoubleClicked(self):
        
        # We update the display info of the file
        self.itemClicked()

        # We check the first checkbox of the layout
        checkBox = [self.verticalLayoutDependent.itemAt(i).widget() for i in range(self.verticalLayoutDependent.count()) if isinstance(self.verticalLayoutDependent.itemAt(i).widget(), QtWidgets.QCheckBox)][0]
        checkBox.setChecked(True)

        # Launch the plot of the first dependent axis
        filePathini = os.path.join(self.currentPath, self.currentItem+'.ini')
        filePathcsv = os.path.join(self.currentPath, self.currentItem+'.csv')

        # Get the init file
        conf = ConfigParser.ConfigParser()
        conf.readfp(self.getFile(filePathini))
        conf.get('General', 'created')

        indexSession = 1
        for section in conf.sections():
            if section[:9] == 'Dependent':
                
                t = conf.get('Dependent '+str(indexSession), 'label')
                t += ' '+conf.get('Dependent '+str(indexSession), 'category')
                t += ' ['+conf.get('Dependent '+str(indexSession), 'units')+']'

                break

        self.dataClicked(True, t, 0, filePathcsv)



    def itemClicked(self):
        """
        Handle event when user clicks on datafile.
        The user can either click on a folder or a file.
        If it is a folder, we launched the folderClicked method.
        If it is a file, we launched the fileClicked method.
        """

        # We check if the signal is effectively called by user
        if not self.folderUpdating and self.guiInitialized:
            
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.statusBar.showMessage('Update')

            # Get current item
            self.currentItem = self.cleanTitle(self.listWidget.currentItem().text(), reverse=True)

            if self.isFolder():
                self.folderClicked(e=False, directory=os.path.join(self.currentPath, self.currentItem+'.dir'))
            else:
                self.fileClicked()
                # # We check of the user double click ir single click
                #                         self._itemClicked)

            # Job done, we restor the usual cursor 
            QtGui.QApplication.restoreOverrideCursor()
            self.statusBar.showMessage('Ready')
        
        # When the signal has been called at least once
        if not self.guiInitialized:
            self.guiInitialized = True



    def clearLayout(self, layout):
        """
        Clear a pyqt layout, from:
        https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()



    def fileClicked(self):
        
        
        filePathini = os.path.join(self.currentPath, self.currentItem+'.ini')
        filePathcsv = os.path.join(self.currentPath, self.currentItem+'.csv')

        # Get the init file
        # If the download of the file fails, the error is handle in the getFile
        # method directly
        conf = ConfigParser.ConfigParser()
        conf.readfp(self.getFile(filePathini))
        conf.get('General', 'created')

        # Get the file size in MB
        if 'test' in os.listdir('.'):
            self.fileSize = os.path.getsize(filePathcsv)
        else:
            fileAttributes = self.conn.getAttributes(config['share_name'], filePathcsv)
            self.fileSize = float(fileAttributes.file_size) # In MB


        # Number of independent parameter in the dataset
        nbIndependent = 0
        for section in conf.sections():
            if section[:11] == 'Independent':
                nbIndependent += 1

        # Information
        self.clearLayout(self.verticalLayoutDependent)

        # If there is data in the datafile
        if self.fileSize > 0.:
            # When we fill the verticalLayout, we need to check if there is already
            # a plotWindow of that file opened.
            # If it is the case, we need to checked the checkBox which are plotted
            # in the plotWindow.
            # Our aim is then to get the list of the checkBox which has to be checked.
            checkedDependents = []
            # If a plotWindow is already open
            if len(self._refs) > 0:
                # We iterate over all plotWindow
                for val in self._refs.values():
                    if val['plotType'] == '1d':
                        if self.cleanTitle(self.currentItem) == val['plot'].windowTitle:
                            checkedDependents = val['plot'].curves.keys()
                    else:
                        for subval in val['plots'].values():
                            if self.cleanTitle(self.currentItem) == subval.windowTitle:
                                checkedDependents.append(subval.curves.keys()[0])
            
            indexSession = 1
            for section in conf.sections():
                if section[:9] == 'Dependent':
                    
                    t = conf.get('Dependent '+str(indexSession), 'label')
                    t += ' '+conf.get('Dependent '+str(indexSession), 'category')
                    t += ' ['+conf.get('Dependent '+str(indexSession), 'units')+']'
                    
                    cb = QtWidgets.QCheckBox(t)

                    # If that dependent is already plotted in a plotWindow
                    if t in checkedDependents:
                        cb.setChecked(True)

                    # Each checbox at its own event attached to eat
                    cb.toggled.connect(lambda cb=cb,
                                            t=t,
                                            nbDependent=indexSession-1,
                                            filePath=filePathcsv: self.dataClicked(cb, t, nbDependent, filePath))
                    self.verticalLayoutDependent.addWidget(cb)
                    
                    indexSession += 1
        else:
            label = QtWidgets.QLabel('Data file is empty')
            self.verticalLayoutDependent.addWidget(label)
        
        self.verticalLayoutDependent.setAlignment(QtCore.Qt.AlignTop)



        # Meta information
        self.clearLayout(self.verticalLayout_7)

        t = '<html><p>'
        t += '<b>General</b><br>'
        t += '&nbsp;&nbsp;&nbsp;&nbsp;File size : '+str(self.fileSize/1e6)+' MB<br>'
        for (key, val) in conf.items('General'):
            t += '&nbsp;&nbsp;&nbsp;&nbsp;'+key+' : '+val+'<br>'

        t += '</p><b>Parameters</b><p>'
        i = 1
        for section in conf.sections():
            if section[:9] == 'Parameter':
                tt = ''
                for (key, val) in conf.items('Parameter '+str(i)):
                    tt += val+' : '
                t += '&nbsp;&nbsp;&nbsp;&nbsp;'+tt[:-3]+'<br>'
                
                i += 1

        t += '</p></html>'
        label = QtWidgets.QLabel(t)
        label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.verticalLayout_7.setAlignment(QtCore.Qt.AlignTop)
        self.verticalLayout_7.addWidget(label)



    def updateLabelPath(self):
        """
        Update the label path by creating a line if button to quickly browse
        back the folder arborescence.
        """

        self.clearLayout(self.labelPath)

        path = os.path.normpath(self.currentPath).split(os.sep)

        for i, text in enumerate(path):
            # Due to varys configuration, we have to ignore the first folder which
            # is "shared"
            if text!=config['path'][0]:
                bu = QtWidgets.QPushButton(text[:-4])
                width = bu.fontMetrics().boundingRect(text).width() + 15
                bu.setMaximumWidth(width)
                d = os.path.join(*path[:i+1])
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
        
        # When user reached the "data_vault_server_file" we disable the button goes up
        if 'test' in os.listdir('.'):
            uFolder = 'test.dir'
        else:
            uFolder = 'data_vault_server_file'
        
        if os.path.basename(self.currentPath) == uFolder:
            self.pushButtonUp.setEnabled(False)
        else:
            self.pushButtonUp.setEnabled(True)
        
        # Check if we are in a folder containing datafile
        session, filesStared = self.checkSession()

        self.listWidget.clear()

        # Get list of files from smb
        if 'test' in os.listdir('.'):
            rep = os.listdir(self.currentPath)
        else:
            files = self.conn.listPath(config['share_name'], self.currentPath)
            rep = [item.filename for item in files]
        
        # Display list of files
        for file in sorted(rep, reverse=True): 
            if file[-4:] == '.dir' or file[-4:] == '.csv':

                item =  QtGui.QListWidgetItem(self.cleanTitle(file[:-4]))
                
                if file[-4:] == '.dir':
                    item.setIcon(QtGui.QIcon('ui/pictures/folder.png'))
                elif session:
                    if any([i for i in filesStared if i == int(file[0:5])]):
                        item.setIcon(QtGui.QIcon('ui/pictures/fileStared.png'))
                        item.setForeground(QtGui.QBrush(QtGui.QColor(config['fileStared'])))
                    else:
                        item.setIcon(QtGui.QIcon('ui/pictures/file.png'))

                self.listWidget.addItem(item)

        # Allow item event again
        self.folderUpdating = False



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



    def cleanCheckBox(self, windowTitle, dependent=None):
        """
        Method called by the QDialog plot when the use close the window.
        We propagate that event to the mainWindow to clean the checkbox
        """
        
        # The plotWindow correspond to the displayed
        # We uncheck all the checkbox listed in the vertical layout
        if self.cleanTitle(self.currentItem) == windowTitle:
            
            index = self.verticalLayoutDependent.count()-1
            while index >= 0:
                widget = self.verticalLayoutDependent.itemAt(index).widget()
                if dependent is None:
                    widget.setChecked(False)
                elif widget.text()==dependent:
                    widget.setChecked(False)
                index -=1



    def startPlotting(self, filePath, data, nbIndependent, nbDependent, xLabel, yLabel, zLabel):
        """
        Methods called once the data are downloaded by the data thread.

        """

        self.centralwidget.setEnabled(True)
        # Stop the thread used to download the data
        self._refs[filePath]['thread'].quit()
        self._refs[filePath]['thread'].wait()
        del(self._refs[filePath]['thread'])
        del(self._refs[filePath]['worker'])

        # The data are download, the plotting start
        self.statusBar.removeWidget(self.progressBar)
        self.statusBar.showMessage('Start plotting')

        # Update the status bar
        self.statusBar.showMessage('Plot data')

        # try:
        if nbIndependent == 1:
            
            # If nbCurve is 1, we create the plot QDialog
            if self._refs[filePath]['nbCurve'] == 1:
                p  = Plot1dApp(x           = data[:, 0],
                               y           = data[:, nbIndependent+nbDependent],
                               title       = self.getPlotTitle(),
                               xLabel      = xLabel,
                               yLabel      = yLabel,
                               windowTitle = self.getWindowTitle(),
                               cleanCheckBox  = self.cleanCheckBox,
                               curveId=yLabel)
                self._refs[filePath]['plotType'] = '1d'
                self._refs[filePath]['plot'] = p
                self._refs[filePath]['plot'].show()
            else:
                self._refs[filePath]['plot'].addPlotDataItem(x      = data[:, 0],
                                                             y      = data[:, nbIndependent+nbDependent],
                                                             curveId= yLabel,
                                                             curveLabel=yLabel,
                                                             curveLegend=yLabel)
            


        elif nbIndependent==2:

            x, y, z = self.shapeData2d(data, nbDependent, nbIndependent)

            p = Plot2dApp(x              = x,
                          y              = y,
                          z              = z,
                          title          = self.getPlotTitle(),
                          xLabel         = xLabel,
                          yLabel         = yLabel,
                          zLabel         = zLabel,
                          windowTitle    = self.getWindowTitle(),
                          cleanCheckBox  = self.cleanCheckBox)
            self._refs[filePath]['plotType'] = '2d'
            
            if self._refs[filePath]['nbCurve'] == 1:
                self._refs[filePath]['plots'] = {zLabel : p}
            else:
                self._refs[filePath]['plots'][zLabel] = p

            self._refs[filePath]['plots'][zLabel].show()
        
        else:
            self.statusBar.showMessage("Plot in higher than 2d not enabled.")
        
        # Plot is done, we unable the gui
        QtGui.QApplication.restoreOverrideCursor()
        self.statusBar.showMessage('Ready')



    def cleanTitle(self, a, reverse=False):
        """
        Clean title name
        If reverse, replace charactere as labrad coded them
        """

        if reverse:
            return a.replace('|', '%v').replace('>', '%g').replace(':', '%c')
        else:
            return a.replace('%v', '|').replace('%g', '>').replace('%c', ':')



    def getWindowTitle(self):

        return self.cleanTitle(self.currentItem)



    def getPlotTitle(self):
        """
        Return a plot title in a normalize way displaying the folders and
        file name.
        """

        title = os.path.normpath(self.currentPath.replace('.dir', '')).split(os.path.sep)[2:]
        title = '/'.join(title)+'<br>'+self.currentItem
        return self.cleanTitle(title)



    def shapeData2d(self, d, nbDependent, nbIndependent):
        """
        Shape the data for a 2d plot but mainly handled all kind of data error/missing/...
        """

        # get axis
        x = d[:,0]
        y = d[:,1]
        z = d[:,nbDependent+nbIndependent]

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


