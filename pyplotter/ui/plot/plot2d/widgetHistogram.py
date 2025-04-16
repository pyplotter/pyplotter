from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np

from ....sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ....sources.pyqtgraph import pg
# File copy from bokeh: https://github.com/bokeh/bokeh/blob/7cc500601cdb688c4b6b2153704097f3345dd91c/bokeh/palettes.py
from ....sources import palettes
from ....sources.functions import hex_to_rgba



class WidgetHistogram(QtWidgets.QWidget):



    def __init__(self, parent: QtWidgets.QHBoxLayout,
                       imageItem: pg.ImageItem,
                       zLabelText: str,
                       zLabelUnits: str) -> None:

        super(WidgetHistogram, self).__init__()


        # Build the UI so that WidgetPlotContainer take all possible space in its
        # parent
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        # Build the UI with a
        # 1. a comboBox to chose the colormap
        # 2. a checkBox box to invert the colormap
        # 3. a pyqtgraph histogram linked to the imageItem
        # 4. a qlabel of the colormap

        self.colorMapComboBox = QtWidgets.QComboBox()

        self.colorMapInvertCheckBox = QtWidgets.QCheckBox()
        self.colorMapInvertCheckBox.setText('invert colormap')


        self.pgHist = pg.HistogramLUTWidget()
        self.pgHist.setMinimumSize(0, 0)
        self.pgHist.setAspectLocked(False)

        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        # self.label.setWordWrap(True)


        self.hLayout = QtWidgets.QVBoxLayout(self)
        self.hLayout.addWidget(self.colorMapComboBox)
        self.hLayout.addWidget(self.colorMapInvertCheckBox)
        self.hLayout.addWidget(self.pgHist)
        self.hLayout.addWidget(self.label)

        parent.addWidget(self)


        self.pgHist.item.axis.setPen(config['styles'][config['style']]['pyqtgraphzAxisTicksColor'])


        # Create a histogram item linked to the imageitem
        self.pgHist.setImageItem(imageItem)
        # self.pgHist.setFixedWidth(100)


        font = QtGui.QFont()
        font.setPixelSize(config['tickLabelFontSize'])
        self.pgHist.axis.setTickFont(font)


        # The only reliable way I have found to correctly display the zLabel
        # is by using a Qlabel from the GUI
        self.label.setText(zLabelText+' ('+zLabelUnits+')')
        self.label.setFont(font)

        # Connect signal
        self.colorMapInvertCheckBox.clicked.connect(self.cbcmInvert)
        self.colorMapComboBox.currentIndexChanged.connect(self.comboBoxcmChanged)


        # Done at the end
        self.colorMapInitialization()



    def colorMapInitialization(self):
        """
        Fill the comboBox with all the colormap available in the palette file.
        Chose the colormap defined in the config file.
        """

        # Build the colormap comboBox, the default one being from the config file
        index = 0
        indexViridis = 0
        for cm in [i for i in palettes.all_palettes.keys() if i[-2:] !='_r']:
            self.colorMapComboBox.addItem(cm)
            if cm==config['plot2dcm']:
                indexViridis = index

            index += 1

        self.colorMapInversed = False
        self.setColorMap(config['plot2dcm'])
        self.colorMapComboBox.setCurrentIndex(indexViridis)



    def comboBoxcmChanged(self, index: int) -> None:
        """
        Method called when user clicks on the colorbar comboBox
        """
        self.cbcmInvert(self.colorMapInvertCheckBox)



    def cbcmInvert(self, b: QtWidgets.QCheckBox) -> None:
        """
        Method called when user clicks the inverted colormap checkbox.
        """
        self.setColorMap(self.colorMapComboBox.currentText())



    def setColorMap(self, cm: str) -> None:
        """
        Set the colormap of the histogram from the colormap name.
        See the palettes file.

        Parameters
        ----------
        cm : str
            colormap name
        """

        if config['2dMapNbColorPoints'] in palettes.all_palettes[cm].keys():
            rgba_colors = [hex_to_rgba(i) for i in palettes.all_palettes[cm][config['2dMapNbColorPoints']]]
            pos = np.linspace(0, 1, config['2dMapNbColorPoints'])
        else:
            rgba_colors = [hex_to_rgba(i) for i in palettes.all_palettes[cm][5]]
            pos = np.linspace(0, 1, 5)

        if self.colorMapInvertCheckBox.isChecked():
            rgba_colors = [i for i in reversed(rgba_colors)]

        # Set the colormap
        pgColormap =  pg.ColorMap(pos, rgba_colors)
        self.pgHist.item.gradient.setColorMap(pgColormap)



    def autoHistogramRange(self) -> None:
        """
        Enable auto-scaling on the histogram plot.
        """
        self.pgHist.item.autoHistogramRange()



    def setLevels(self, min: float,
                        max: float) -> None:
        """
        Set the min and max evels of the histogram

        Args:
            min : Minimum level.
            max : Maximum level.
        """
        self.pgHist.item.setLevels(min=min,
                                   max=max)



    def setLabel(self, label: str) -> None:
        """
        Set the label of the histogram

        Args:
            label : the text to be used as label
        """

        self.label.setText(label)



    @QtCore.pyqtSlot(bool, pg.ImageView)
    def slotIsoCurve(self, isChecked: bool,
                           imageView: pg.ImageView) -> None:
        """
        Method called when user clicks on the Draw isocurve checkbox.

        Args:
            b : Draw isocurve checkbox
        """

        # When user check the box we create the items and the events
        if isChecked:

            # If items do not exist, we create them
            if not hasattr(self, 'isoCurve'):

                z = imageView.image

                self.penIsoLine = pg.mkPen(color='w', width=2)
                # Isocurve drawing
                self.isoCurve = pg.IsocurveItem(level=0.5, pen=self.penIsoLine)
                self.isoCurve.setParentItem(imageView.imageItem)
                self.isoCurve.setZValue(np.median(z[~np.isnan(z)]))
                # build isocurves
                zTemp = np.copy(z)
                # We can't have np.nan value in the isocurve so we replace
                # them by small value
                zTemp[np.isnan(zTemp)] = zTemp[~np.isnan(zTemp)].min()-1000
                self.isoCurve.setData(zTemp)


                # Draggable line for setting isocurve level
                self.isoLine = pg.InfiniteLine(angle=0,
                                               movable=True,
                                               pen=self.penIsoLine)
                self.pgHist.item.vb.addItem(self.isoLine)
                self.pgHist.item.vb.setMouseEnabled(y=False) # makes user interaction a little easier
                self.isoLine.setValue(np.median(z[~np.isnan(z)]))
                self.isoLine.setZValue(1000) # bring iso line above contrast controls

                # Connect event
                self.isoLine.sigDragged.connect(self.draggedIsoLine)
            else:

                self.isoCurve.show()
                self.isoLine.show()

        # If the user uncheck the box, we hide the items
        else:
            self.isoCurve.setParentItem(None)
            self.pgHist.item.vb.removeItem(self.isoLine)
            del(self.isoCurve)
            del(self.isoLine)



    @QtCore.pyqtSlot()
    def draggedIsoLine(self) -> None:
        """
        Method called when user drag the iso line display on the histogram.
        By simply updating the value of the isoCurve, the plotItem will update
        itself.
        """

        self.isoCurve.setLevel(self.isoLine.value())
