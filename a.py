import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

pg.setConfigOptions(imageAxisOrder='row-major')
pg.setConfigOption('useOpenGL', True) # Set to False to get the expected behavior

data = np.random.random((20001,9))


app = QtGui.QApplication([])

win = QtGui.QMainWindow()
win.resize(800,800)

pw = pg.PlotWidget()
plotItem = pw.getPlotItem()

win.setCentralWidget(pw)

imageItem = pg.ImageItem()
imageItem.autoDownsample = True

imageView = pg.ImageView(imageItem=imageItem)
imageView.setImage(data)
imageView.autoRange()
imageView.view.invertY(False)
imageView.view.setAspectLocked(False)

plotItem.showGrid(x=True, y=True)
plotItem.vb.addItem(imageItem)

win.show()


if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()