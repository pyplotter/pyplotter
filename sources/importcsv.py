# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtGui
import os
import pandas as pd
from skrf import Touchstone # To easily read s2p file


class ImportCSV:


    def __init__(self, mainObject):
        """
        Class handling the reading of csv file.
        """

        super(ImportCSV, self).__init__()

        self.main = mainObject



    def csvFileClicked(self, filePath:str) -> None :
        """
        Call when user click on a csv file in the tableWidgetFolder.
        Load the csv file and display its information in the tableWidgetParameters.
        """
        
        # Disable widget received for qcodes database
        self.main.lineEditFilter.setEnabled(False)
        self.main.labelFilter.setEnabled(False)
        
        self.main.setStatusBarMessage('Loading '+filePath[-3:].lower()+' file')

        # Get the file name
        fileName = os.path.basename(os.path.normpath(filePath))


        ## Fill the tableWidgetParameters with the run parameters

        # Clean GUI
        self.main.clearTableWidet(self.main.tableWidgetDataBase)
        self.main.clearTableWidet(self.main.tableWidgetParameters)
        self.main.tableWidgetDataBase.setSortingEnabled(True)
        self.main.tableWidgetParameters.setSortingEnabled(True)
        
        self.main.textEditMetadata.clear()



        ## File parameters table

        # csv file
        if filePath[-3:].lower()=='csv':

            try:

                f = open(filePath, 'r')
                # Get the comment character
                c = f.readline()[0]
                f.close()

                df = pd.read_csv(filePath, comment=c)
                independentParameter = df.columns[0]
                columnsName = df.columns[1:]
                x = df.values[:,0]
                ys = df.values.T[1:]
            except Exception as e:
                fname = os.path.split(sys.exc_info()[2].tb_frame.f_code.co_filename)[1]
                nbLine = sys.exc_info()[2].tb_lineno
                exc_type = sys.exc_info()[0].__name__ 
                self.main.setStatusBarMessage("Can't open csv file: "+str(exc_type)+", "+str(e)+". File "+str(fname)+", line"+str(nbLine), error=True)
                return
        # s2p file
        else:

            try:
                ts = Touchstone(filePath)
                self.main.textEditMetadata.setText(ts.get_comments())
                independentParameter = 'Frequency'
                columnsName = list(ts.get_sparameter_data('db').keys())[1:]
                x = ts.get_sparameter_data('db')['frequency']
                ys = [ts.get_sparameter_data('db')[i] for i in list(ts.get_sparameter_data('db').keys())[1:]]
            except Exception as e:
                fname = os.path.split(sys.exc_info()[2].tb_frame.f_code.co_filename)[1]
                nbLine = sys.exc_info()[2].tb_lineno
                exc_type = sys.exc_info()[0].__name__ 
                self.main.setStatusBarMessage("Can't open s2p file: "+str(exc_type)+", "+str(e)+". File "+str(fname)+", line"+str(nbLine), error=True)
                return


        i = 1
        for columnName, y in zip(columnsName, ys):
            
            rowPosition = self.main.tableWidgetParameters.rowCount()
            self.main.tableWidgetParameters.insertRow(rowPosition)

            cb = QtWidgets.QCheckBox()

            # We check if that parameter is already plotted
            if self.main.isParameterPlotted(columnName):
                cb.setChecked(True)

            # We put a fake runId of value 0
            self.main.tableWidgetParameters.setItem(rowPosition, 0, QtGui.QTableWidgetItem('0'))
            self.main.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
            self.main.tableWidgetParameters.setItem(rowPosition, 3, QtGui.QTableWidgetItem(columnName))
            self.main.tableWidgetParameters.setItem(rowPosition, 5, QtGui.QTableWidgetItem(independentParameter))

            # Each checkbox at its own event attached to it
            cb.toggled.connect(lambda cb      = cb,
                                      xLabel  = independentParameter,
                                      yLabel  = columnName,
                                      data    = (x, y),
                                      plotRef = self.main.getDataRef(): self.csvParameterClicked(cb, xLabel, yLabel, data, plotRef))
            
            i += 1


        self.main.setStatusBarMessage('Ready')



    def csvParameterClicked(self, cb      : QtWidgets.QCheckBox,
                                  xLabel  : str,
                                  yLabel  : str,
                                  data    : tuple,
                                  plotRef : str) -> None:
        """
        Call when user click on a pameter from a csv file in the tableWidgetParameters.
        Launch a plot if user check a parameter and remove curve otherwise.
        """
        
        if cb:

            self.main.addPlot(plotRef        = plotRef,
                              data           = data,
                              xLabel         = xLabel,
                              yLabel         = yLabel)
            
        else:

            self.main.removePlot(plotRef, yLabel)


