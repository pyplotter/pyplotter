# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import sys
import os

from sources.qcodesdatabase import QcodesDatabase



def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
# sys.excepthook = trap_exc_during_debug



class ImportDatabaseSignal(QtCore.QObject):
    """
    Class containing the signal of the ImportDatabaseThread, see below
    """


    # When the run method is done
    done = QtCore.pyqtSignal(bool)
    # Signal used to update the status bar
    setStatusBarMessage = QtCore.pyqtSignal(str, bool)  
    # Signal used to add a row in the database table
    addRow = QtCore.pyqtSignal(str, str, str, str, str, str, str, str, int)




class ImportDatabaseThread(QtCore.QRunnable):


    def __init__(self, runInfos):
        """
        Thread used to get all the run info of a database.
        !! Do not import the data !!

        Parameters
        ----------
        currentPath : str
            CurrentPath attribute of the main thread
        currentDatabase : str
            CurrentDatabase attribute of the main thread
        """

        super(ImportDatabaseThread, self).__init__()

        self.qcodesDatabase  = QcodesDatabase()
        self.runInfos        = runInfos
        
        self.signals = ImportDatabaseSignal() 



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        Go through the runs and send a signal for each new entry.
        Each signal is catch by the main thread to add a line in the database
        table displaying all the info of each run.
        """

        nbTotalRun = len(self.runInfos)

        # Going through the database here
        for key, val in self.runInfos.items(): 

            self.signals.addRow.emit(str(key),
                                     str(val['nb_independent_parameter']),
                                     val['experiment_name'],
                                     val['sample_name'],
                                     val['run_name'],
                                     val['started'],
                                     val['completed'],
                                     str(val['records']),
                                     key/nbTotalRun*100)

        # Signal that the whole database has been looked at
        self.signals.done.emit(False)



