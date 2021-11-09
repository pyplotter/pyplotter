# This Python file uses the following encoding: utf-8
# Inspired from: https://gist.github.com/markjay4k/da2f55e28514be7160a7c5fbf95bd243
from pyqtgraph.Qt import QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
import sys

pg.setConfigOption('background','white')

class Visualizer(object):
    def __init__(self):
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts['distance'] = 25

        self.w.setGeometry(0, 0, 250, 250)
        self.w.show()
        self.n = 40
        self.m = 1000
        self.y = np.linspace(-10, 10, self.n)
        self.x = np.linspace(-10, 10, self.m)
        self.phase = 0

        for i in range(self.n):
            yi = np.array([self.y[i]] * self.m)
            d = np.sqrt(self.x ** 2 + yi ** 2)*1.5
            z = 10 * np.cos(d + self.phase) / (d + 1)*1.8
            pts = np.vstack([self.x, yi, z]).transpose()
            self.traces[i] = gl.GLLinePlotItem(pos=pts, color=pg.glColor(
                (i, self.n * 1.3)), width=(i + 1) / 10, antialias=True)
            self.w.addItem(self.traces[i])

        QtGui.QApplication.instance().exec_()


# Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    v = Visualizer()