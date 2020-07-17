# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import sys
import os
import qcodes as qc
from itertools import chain
from operator import attrgetter


from MyTableWidgetItem import MyTableWidgetItem

def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug



class ImportDatabaseSignal(QtCore.QObject):
    """
    Class containing the signal of the ImportDatabaseThread, see below
    """


    # When the run method is done
    done = QtCore.pyqtSignal()
    # Signal used to update the status bar
    setStatusBarMessage = QtCore.pyqtSignal(str, bool)  
    # Signal used to add a row in the database table
    addRow = QtCore.pyqtSignal(str, dict, str)




class ImportDatabaseThread(QtCore.QRunnable):


    def __init__(self, nbTotalRun, currentPath, currentDatabase, get_ds_info):
        """
        Thread used to get all the run info of a database.
        !! Do not import the data !!

        Parameters
        ----------
        nbTotalRun : str
            Total number of run in the database
        currentPath : str
            CurrentPath attribute of the main thread
        currentDatabase : str
            CurrentDatabase attribute of the main thread
        get_ds_info : func
            Method of the main thread to go through the QCoDeS database
        """

        super(ImportDatabaseThread, self).__init__()

        self.nbTotalRun           = str(nbTotalRun)
        self.currentPath          = currentPath
        self.currentDatabase      = currentDatabase
        self.get_ds_info          = get_ds_info
        
        self.signals = ImportDatabaseSignal() 



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        Go through the database and send a signal for each new entry.
        Each signal is catch by the main thread to add a line in the database
        table displaying all the info of each run.
        """
        
        # Catch error at the open of a db
        try:
            qc.initialise_or_create_database_at(os.path.join(self.currentPath, self.currentDatabase))
        except:
            self.signals.setStatusBarMessage.emit("Can't load database", True)
            return


        self.signals.setStatusBarMessage.emit('Getting database information', False)
        datasets = sorted(
            chain.from_iterable(exp.data_sets() for exp in qc.experiments()),
            key=attrgetter('run_id'))
        
        
        # Going through the database here
        for ds in datasets: 

            info = self.get_ds_info(ds, get_structure=False)
            self.signals.addRow.emit(str(ds.run_id), info, self.nbTotalRun)

        # Signal that the whole database has been looked at
        self.signals.done.emit()



