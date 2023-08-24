    # This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtWidgets, QtCore
import os



class MenuExportRun(QtWidgets.QMenu):
    """
    Menu displayed when user right-click on a run
    """

    # Signal used to add a progress bar in the status bar
    signalExportRunAddProgressBar = QtCore.pyqtSignal(str, str, int)

    def __init__(self, databaseAbsPath : str,
                       runId: int) -> None:

        super(MenuExportRun, self).__init__()

        self.databaseAbsPath = databaseAbsPath
        self.runId = runId

        self.threadpool = QtCore.QThreadPool()

        self.menu = QtWidgets.QMenu()

        exportRun = QtWidgets.QAction('Export run', self)
        exportRun.triggered.connect(self.exportRun)
        self.menu.addAction(exportRun)

        self.menu.exec(QtGui.QCursor.pos())



    def exportRun(self, q:QtWidgets.QAction) -> None:
        """
        Open a QFileDialog asking where to export the run
        """

        self.filePath = QtWidgets.QFileDialog.getOpenFileName(self,
                                                     caption='Select database',
                                                     filter="qCoDeS database (*.db)",
                                                     directory=os.getcwd())[0]
