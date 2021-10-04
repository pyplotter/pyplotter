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
        
        ## Update label
        self.main.labelCurrentRun.clear()
        self.main.labelCurrentMetadata.clear()
        
        self.main.setStatusBarMessage('Loading '+filePath[-3:].lower()+' file')

        ## Fill the tableWidgetParameters with the run parameters

        # Clean GUI
        self.main.clearTableWidget(self.main.tableWidgetDataBase)
        self.main.clearTableWidget(self.main.tableWidgetParameters)
        self.main.tableWidgetDataBase.setSortingEnabled(True)
        self.main.tableWidgetParameters.setSortingEnabled(True)
        
        self.main.removeSnapshot()



        ## File parameters table

        # csv file
        if filePath[-3:].lower()=='csv':

            try:
                
                ## Guess comment character
                # We check if there is no comment on the csv file by guessing
                # if the first character of the first line is part of a float
                # number.
                # If there is comment c will contain the comment character
                # otherwise it will return None.
                f = open(filePath, 'r')
                c = f.readline()[0]
                f.close()
                if c.isnumeric() or c=='+' or c=='-':
                    c = None
                
                ## Determine the csv file header
                if c is None:
                    header = None
                else:
                    f = open(filePath, 'r')
                    header = 0
                    d = f.readline()
                    while d[0]==c:
                        d = f.readline()
                        header += 1
                f.close()
                
                ## Guess delimiter character
                f = open(filePath, 'r')
                for i in range(10):
                    d = f.readline()
                f.close()
                delimiter = None
                if ',' in d:
                    delimiter = ','
                else:
                    delimiter = ' '

                # Get the data as panda dataframe
                df = pd.read_csv(filePath, comment=c, sep=delimiter, header=header)
                
                # Get the column name as string
                independentParameter = str(df.columns[0])
                columnsName = df.columns[1:].astype(str)
                
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
                self.main.addSnapshot({'comment': ts.get_comments()})
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
            
            fakeParamDependent = {'depends_on' : [0],
                                  'label' : columnName}
            
            rowPosition = self.main.tableWidgetParameters.rowCount()
            self.main.tableWidgetParameters.insertRow(rowPosition)

            cb = QtWidgets.QCheckBox()

            # We check if that parameter is already plotted
            if self.main.isParameterPlotted(fakeParamDependent):
                cb.setChecked(True)

            # We put a fake runId of value 0
            self.main.tableWidgetParameters.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem('0'))
            self.main.tableWidgetParameters.setCellWidget(rowPosition, 2, cb)
            self.main.tableWidgetParameters.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(columnName))
            self.main.tableWidgetParameters.setItem(rowPosition, 5, QtWidgets.QTableWidgetItem(independentParameter))

            runId       = 0
            curveId     = self.main.getCurveId(name=columnName,
                                               runId=runId,
                                               livePlot=False)
            plotTitle   = self.main.getPlotTitle(livePlot=False)
            windowTitle = self.main.getWindowTitle(runId=runId, livePlot=False)
            
            # Each checkbox at its own event attached to it
            cb.toggled.connect(lambda cb          = cb,
                                      xLabelText  = independentParameter,
                                      xLabelUnits = '',
                                      yLabelText  = columnName,
                                      yLabelUnits = '',
                                      data        = (x, y),
                                      runId       = runId,
                                      curveId     = curveId,
                                      plotTitle   = plotTitle,
                                      windowTitle = windowTitle,
                                      plotRef     = self.main.getPlotRef(fakeParamDependent): self.csvParameterClicked(cb,
                                                                                                                       xLabelText,
                                                                                                                       xLabelUnits,
                                                                                                                       yLabelText,
                                                                                                                       yLabelUnits,
                                                                                                                       data,
                                                                                                                       runId,
                                                                                                                       curveId,
                                                                                                                       plotTitle,
                                                                                                                       windowTitle,
                                                                                                                       plotRef))
            
            i += 1

        self.main.setStatusBarMessage('Ready')



    def csvParameterClicked(self, cb          : QtWidgets.QCheckBox,
                                  xLabelText  : str,
                                  xLabelUnits : str,
                                  yLabelText  : str,
                                  yLabelUnits : str,
                                  data        : tuple,
                                  runId       : int,
                                  curveId     : str,
                                  plotTitle   : str,
                                  windowTitle : str,
                                  plotRef     : str) -> None:
        """
        Call when user click on a parameter from a csv file in the tableWidgetParameters.
        Launch a plot if user check a parameter and remove curve otherwise.

        Args:
            cb (QtWidgets.QCheckBox):  Clicked checkbox.
            xLabelText (str): Label text for the xAxix.
            xLabelUnits (str): Label units for the xAxix.
            yLabelText (str): Label text for the yAxix.
            yLabelUnits (str): Label units for the yAxix.
            data (tuple): For 1d plot: [xData, yData]
            runId (int): Data run id in the current database
            curveId (str): Id of the curve, see getCurveId.
            plotTitle (str): Plot title, see getPlotTitle.
            windowTitle (str): Window title, see getWindowTitle.
            plotRef (str): Reference of the plot, see getplotRef.
        """
        
        if cb:

            self.main.addPlot(plotRef     = plotRef,
                              data        = data,
                              xLabelText  = xLabelText,
                              xLabelUnits = xLabelUnits,
                              yLabelText  = yLabelText,
                              yLabelUnits = yLabelUnits,
                              runId       = runId,
                              curveId     = curveId,
                              plotTitle   = plotTitle,
                              windowTitle = windowTitle)
            
        else:

            self.main.removePlot(plotRef = plotRef,
                                 curveId = curveId)


