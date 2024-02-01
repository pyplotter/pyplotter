from PyQt5 import QtCore
import multiprocess as mp

from ..config import loadConfigCurrent
config = loadConfigCurrent()
from ..qcodesDatabase import exportRunmp

class ExportRunSignal(QtCore.QObject):
    """
    Class containing the signal of the ExportRunThread, see below
    """

    # Signal used to update the status bar
    sendStatusBarMessage = QtCore.pyqtSignal(str, str)
    # Signal used to update the progress bar
    updateProgressBar = QtCore.pyqtSignal(int, float, str)
    # Signal used to remove the progress bar
    removeProgressBar = QtCore.pyqtSignal(int)

class ExportRunThread(QtCore.QRunnable):


    def __init__(self, source_db_path: str,
                       target_db_path: str,
                       runId: int,
                       progressBarId: int):
        """

        Parameters
        ----------
        databaseAbsPath : str
            Absolute path of the current database
        progressBarId : int
            Key to the progress bar in the dict progressBars
        """

        super(ExportRunThread, self).__init__()

        self.signal = ExportRunSignal()

        self.source_db_path = source_db_path
        self.target_db_path = target_db_path
        self.runId          = runId
        self.progressBarId  = progressBarId



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        """

        self.signal.sendStatusBarMessage.emit('Exporting run', 'orange')

        # Queue will contain message to be displayed on the status bar
        queueMessage: mp.Queue = mp.Queue()
        message = None
        queueMessage.put(message)

        # Queue will contain 1 when the download is done
        queueDone: mp.Queue = mp.Queue()
        queueDone.put(False)


        self.worker = mp.Process(target=exportRunmp,
                                 args=(self.source_db_path,
                                       self.target_db_path,
                                       self.runId,
                                       queueMessage,
                                       queueDone))
        self.worker.start()


        self.signal.updateProgressBar.emit(self.progressBarId,
                                           0,
                                           'Exporting run: {:.0f}%'.format(0))

        # Here, we loop until the export is done.
        # In each loop, we check the export progression and update the progress
        # bar
        # We display information only if different than the previous iteration
        # to avoid blinking
        done = False
        while not done:
            QtCore.QThread.msleep(config['delayBetweenProgressBarUpdate'])

            messageNew = queueMessage.get()
            queueMessage.put(messageNew)
            if messageNew!=message:
                message = messageNew
                self.signal.sendStatusBarMessage.emit(message, 'orange')

            done = queueDone.get()
            queueDone.put(done)


        queueMessage.close()
        queueMessage.join_thread()

        queueDone.close()
        queueDone.join_thread()


        self.worker.join()

        self.signal.updateProgressBar.emit(self.progressBarId,
                                           100,
                                           'Exporting run: {:.0f}%'.format(100))

        self.signal.sendStatusBarMessage.emit('Export done', 'green')


        self.signal.removeProgressBar.emit(self.progressBarId)
