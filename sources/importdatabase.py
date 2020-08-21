# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import sys
import os
from typing import Callable



class ImportDatabaseSignal(QtCore.QObject):
    """
    Class containing the signal of the ImportDatabaseThread, see below
    """


    # When the run method is done
    done = QtCore.pyqtSignal(str, bool, int)
    # Signal used to update the status bar
    setStatusBarMessage = QtCore.pyqtSignal(str, bool)  
    # Signal used to add a row in the database table
    addRow = QtCore.pyqtSignal(str, list, str, str, str, str, str, str, int, int, str)
    # Signal used to update the progress bar
    updateProgressBar = QtCore.pyqtSignal(str, int)




class ImportDatabaseThread(QtCore.QRunnable):


    def __init__(self, getRunInfos: Callable[[int], dict], progressBarKey: str):
        """
        Thread used to get all the run info of a database.
        !! Do not import data !!

        Parameters
        ----------
        getRunInfos : func
            Function which returns all infos of a database in a nice python dict.
        progressBarKey : str
            Key to the progress bar in the dict progressBars
        """

        super(ImportDatabaseThread, self).__init__()

        self.getRunInfos    = getRunInfos
        self.progressBarKey = progressBarKey
        
        self.signals = ImportDatabaseSignal() 



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        Go through the runs and send a signal for each new entry.
        Each signal is catch by the main thread to add a line in the database
        table displaying all the info of each run.
        """

        self.signals.setStatusBarMessage.emit('Gathered runs infos database', False)
        runInfos = self.getRunInfos(self.signals.updateProgressBar, self.progressBarKey)


        # Going through the database here
        self.signals.setStatusBarMessage.emit('Loading database', False)
        nbTotalRun = len(runInfos)
        for key, val in runInfos.items(): 

            self.signals.addRow.emit(str(key),
                                     val['nb_independent_parameter'],
                                     val['experiment_name'],
                                     val['sample_name'],
                                     val['run_name'],
                                     val['started'],
                                     val['completed'],
                                     str(val['records']),
                                     key/nbTotalRun*100,
                                     nbTotalRun,
                                     self.progressBarKey)

        # Signal that the whole database has been looked at
        self.signals.done.emit(self.progressBarKey, False, nbTotalRun)



