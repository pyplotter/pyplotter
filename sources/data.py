# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import sys
import os
import time
import numpy as np
import pandas as pd
import ConfigParser
import tempfile


from config import config

def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print args


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class ProgressDataThread(QtCore.QObject):
    """
    Import data files in another thread to avoid the main app to freeze.
    Once the data are imported the data are in the d attribute and the configuration are in the
    conf attribute
    """

    def __init__(self, fileObj, fileSize, sigUpdateProgressBar):
        super(QtCore.QObject, self).__init__()

        self.fileObj     = fileObj
        self.fileSize    = fileSize
        self.sigUpdateProgressBar = sigUpdateProgressBar
        self.done        = False



    def run(self):
        while not self.done:
            
            # Calculate progress in percentage in integer
            val = int(os.fstat(self.fileObj.fileno()).st_size/self.fileSize*100)

            # Update the progress bar only when the progress are above 0
            if val > 0:
                # self.progressBar.setValue(val)
                self.sigUpdateProgressBar.emit(val)
                
            time.sleep(0.1)




class ImportDataThread(QtCore.QObject):
    """
    Import data files in another thread to avoid the main app to freeze.
    Once the data are imported the data are in the d attribute and the configuration are in the
    conf attribute
    """

    sigDone = QtCore.pyqtSignal(str, np.ndarray, int, int, str, str, str)  
    sigUpdateProgressBar = QtCore.pyqtSignal(int) 


    def __init__(self, conn, share_name, filePath, fileSize, nbDependent):

        super(QtCore.QObject, self).__init__()

        self.__abort     = False
        self.conn        = conn
        self.share_name  = share_name
        self.filePath    = filePath
        self.fileSize    = fileSize
        self.nbDependent = nbDependent
        self._threads    = []



    @QtCore.pyqtSlot()
    def work(self):
        
        # Get data metadata
        conf = ConfigParser.ConfigParser()
        conf.readfp(self.getFile(self.filePath[:-4]+'.ini'))
        conf.get('General', 'created')

        # Number of independent parameter in the dataset
        nbIndependent = 0
        for section in conf.sections():
            if section[:11] == 'Independent':
                nbIndependent += 1

        # Labels
        xLabel = conf.get('Independent 1', 'label')+' ['+conf.get('Independent 1', 'units')+']'

        if conf.has_section('Independent 2'):

            yLabel = conf.get('Independent 2', 'label')+' ['+conf.get('Independent 1', 'units')+']'
            zLabel = conf.get('Dependent '+str(self.nbDependent+1), 'label')+' '+conf.get('Dependent '+str(self.nbDependent+1), 'category')+' ['+conf.get('Dependent '+str(self.nbDependent+1), 'units')+']'
        else:
            yLabel = conf.get('Dependent '+str(self.nbDependent+1), 'label')+' '+conf.get('Dependent '+str(self.nbDependent+1), 'category')+' ['+conf.get('Dependent '+str(self.nbDependent+1), 'units')+']'
            zLabel = 'zLabel'

        # Get data
        file = self.getFile(self.filePath)
        d = pd.read_csv(file, header=None).values

        # Call startPlotting method
        self.sigDone.emit(self.filePath, d, nbIndependent, self.nbDependent, xLabel, yLabel, zLabel)



    def abort(self):
        self.__abort = True



    def getFile(self, filePath):
        """
        Return a file object through the SMB connection
        """

        # Create a temporary file which will contain the data file after download
        self.fileObj = tempfile.NamedTemporaryFile()

        # start thread for the progress barr
        worker = ProgressDataThread(self.fileObj, self.fileSize, self.sigUpdateProgressBar)

        thread = QtCore.QThread()
        worker.moveToThread(thread)

        # Start thread
        thread.started.connect(worker.run)
        thread.start()

        # Reference
        self._threads.append((thread, worker))
        

        # Download the data
        # If test mode, the data are local
        if 'test' in os.listdir('.'):
            a = open(filePath, 'r').read()
            self.fileObj.write(a)
        else:
            self.conn.retrieveFile(self.share_name, filePath, self.fileObj)

        # Come back to the start of the temporary file
        self.fileObj.seek(0)

        # Close the progress data transfert thread
        worker.done = True

        # Return the temporary file now full with data
        return self.fileObj



