from PyQt5 import QtGui, QtCore, QtWidgets
from math import log10
from typing import Union, Tuple, List, Generator
import os
import numpy as np
import pandas as pd

from .config import loadConfigCurrent
config = loadConfigCurrent()


def parse_number(number: float,
                 precision: int,
                 inverse: bool=False,
                 unified: bool=False) -> Union[str, Tuple[str, str]]:
    """
    Return a number parsed form human reading with SI prefix
    Example:
        parse_number(1.23456789e-7, 3) -> ('123.457', 'n')
        parse_number(1.23456789e-7, 3) -> ('123.5', 'n')
        parse_number(1.6978e-7, 3, True) -> ('169.78', 'G')

    Args:
        number:
            Number to be parsed
        precision:
            Precision to round the number after the decimal
        inverse:
            If True, returns the inverse of the SI prefix.
            Defaults to False.
        unified:
        If True, return an unique string such as
            parse_number(1.23456789e-7, 3) -> ('123.457 n')
            parse_number(1.23456789e-7, 3) -> ('123.5 n')
            parse_number(1.6978e-7, 3, True) -> ('169.78 G')
    """

    if number!=0:
        power_ten = int(log10(abs(number))//3*3)
    else:
        power_ten = 0

    if power_ten>=-24 and power_ten<=18 :

        prefix = {-24 : 'y',
                  -21 : 'z',
                  -18 : 'a',
                  -15 : 'p',
                  -12 : 'p',
                   -9 : 'n',
                   -6 : 'µ',
                   -3 : 'm',
                    0 : '',
                    3 : 'k',
                    6 : 'M',
                    9 : 'G',
                   12 : 'T',
                   15 : 'p',
                   18 : 'E'}

        if inverse:
            if unified:
                return '{} {}'.format(round(number*10.**-power_ten, precision), prefix[-power_ten])
            else:
                return str(round(number*10.**-power_ten, precision)), prefix[-power_ten]
        else:
            if unified:
                return '{} {}'.format(round(number*10.**-power_ten, precision), prefix[power_ten])
            else:
                return str(round(number*10.**-power_ten, precision)), prefix[power_ten]
    else:
        return str(round(number, precision)), ''


def pandasTimestamp2Int(dates: np.ndarray) -> np.ndarray:

    return (dates - pd.Timestamp('1970-01-01'))//pd.Timedelta('1s')


def clearTableWidget(tableWidget : QtWidgets.QTableWidget) -> None:
    """
    Method to remove all row from a table widget.
    When this function is called, it should be followed by:
    tableWidget.setSortingEnabled(True)
    to allowed GUI sorting
    """

    tableWidget.setSortingEnabled(False)
    tableWidget.setRowCount(0)


def clearLayout(layout: QtWidgets.QLayout) -> None:
    """
    Clear a pyqt layout, from:
    https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt

    Parameters
    ----------
    layout : QtWidgets.QLayout
        Qt layout to be cleared
    """
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


def isBlueForsFolder(folderName : str) -> bool:
    """
    Return True if a string follow blueFors log folder name pattern.
    """

    return len(folderName.split('-'))==3 and all([len(i)==2 for i in folderName.split('-')])


def isQcodesData(folderName: str) -> bool:
    """
    Return True if a string follow Qcodes database name pattern.
    """
    return '.db' in folderName


def isLabradFolder(folderName : str) -> bool:
    """
    Return True if a string follow Labrad data folder name pattern.
    """
    return folderName.split('.')[-1] == "dir"


def sizeof_fmt(num: float, suffix: str='B') -> str:
    """
    Return human readable number of Bytes
    Adapted from:
    https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size

    Parameters
    ----------
    num : float
        Size of a file to be transformed in human readable format
    suffix : str
        Suffix to be added after the unit size

    Return
    ------
    humanReadableSize : str
        Size of the file in an easily readable format.
    """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)


def getCurveColorIndex(colorIndexes: List[int],
                       config: dict) -> int:
    """
    Return a pyqtgraph mKpen with the color of the next curve following
    the colors in config files
    """

    for i in range(50):
        if i not in colorIndexes:
            colorIndex = i%len(config['plot1dColors'])
            break

    return colorIndex


def getCurveId(databaseAbsPath: str,
               name: str,
               runId: int) -> str:
    """
    Return an id for a curve in a plot.
    Should be unique for every curve.

    Parameters
    ----------
    name : str
        Parameter name from which the curveId is obtained.
    runId : int
        Id of the curve, see getCurveId.
    """

    return databaseAbsPath+str(runId)+str(name)


def getPlotRef(databaseAbsPath: str,
               paramDependent : dict,
               runId: int) -> str:
    """
    Return a reference for a plot window.
    Handle the difference between 1d plot and 2d plot.

    Parameters
    ----------
    paramDependent : dict
        qcodes dictionary of a dependent parameter

    Return
    ------
    plotRef : str
        Unique reference for a plot window.
    """

    currentPath  = os.path.dirname(databaseAbsPath)

    # If BlueFors log files
    if isBlueForsFolder(currentPath):
        dataPath = currentPath
    # If Labrad data folder
    elif isLabradFolder(databaseAbsPath):
        dataPath = databaseAbsPath+str(runId)
    # If csv or s2p files we return the filename without the extension
    elif databaseAbsPath[-3:].lower() in ('csv', 's2p'):
        dataPath = currentPath
    else:
        dataPath = currentPath+str(runId)


    if len(paramDependent['depends_on'])==2:
        return dataPath+paramDependent['name']
    else:
        return dataPath


def getPlotTitle(databaseAbsPath: str,
                 runId: int,
                 experimentName: str) -> str:
    """
    Return a plot title in a normalize way displaying the folders and
    file name.
    """

    databaseName = getDatabaseNameFromAbsPath(databaseAbsPath)

    # If no database have been selected ever
    if databaseAbsPath is None:
        return ''
    # If BlueFors log files
    elif isBlueForsFolder(os.path.basename(databaseAbsPath)):
        return os.path.basename(databaseAbsPath)
    # If csv or s2p files we return the filename without the extension
    elif databaseAbsPath[-3:].lower() in ['csv', 's2p']:
        return databaseAbsPath[:-4]
    else:
        # If user only wants the database path
        if config['displayOnlyDbNameInPlotTitle']:
            title = databaseName
        # If user wants the database path
        else:
            title = databaseAbsPath

        return '{}<br>{} - {}'.format(title, runId, experimentName)


def getDatabaseNameFromAbsPath(databaseAbsPath: str) -> str:
    if isQcodesData(os.path.split(databaseAbsPath)[-1]):
        return os.path.basename(databaseAbsPath)[:-3]
    elif isLabradFolder(os.path.split(databaseAbsPath)[-1]):
        return os.path.basename(databaseAbsPath)[:-4]
    else:
        return os.path.basename(databaseAbsPath)


def getWindowTitle(databaseAbsPath: str,
                   runId: int,
                   runName: str) -> str:
    """
    Return a title which will be used as a plot window title.
    """

    windowTitle = getDatabaseNameFromAbsPath(databaseAbsPath)

    if config['displayRunIdInPlotTitle']:
        windowTitle += ' - '+str(runId)

    if config['displayRunNameInPlotTitle']:
        windowTitle += ' - '+runName

    return windowTitle


def hex_to_rgba(value: str) -> Tuple[int, int, int, int]:
    """
    Convert hex color to rgba color.
    From: https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python/29643643

    Parameters
    ----------
    value : str
        hexagonal color to be converted in rgba.

    Returns
    -------
    Tuple[int]
        rgba calculated from the hex color.
    """
    value = value.lstrip('#')
    lv = len(value)
    r, g, b = [int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    return r, g, b, 255


def findXYIndex(y: np.ndarray) -> Tuple[int, int]:
    """
    Find effective "x" column
    The x column is defined as the column where the independent parameter
    is not modified while the y column independent parameter is.

    Parameters
    ----------
    y : np.ndarray
        Data of the original y axis

    Returns
    -------
    (xi, yi) : tuple
        Index of the the x and y axis.
    """

    if y[1]==y[0]:
        return 1, 0
    else:
        return 0, 1


def shapeData2d(x: np.ndarray,
                y: np.ndarray,
                z: np.ndarray,
                sendMessage: QtCore.pyqtSignal) -> Tuple[np.ndarray,
                                                                  np.ndarray,
                                                                  np.ndarray]:
    """
    Shape the data for a 2d plot but mainly handled all kind of data error/missing/...

    Return x and y as a 1d array, ready to be used for the 2d plot
    and z as a 2d array.
    In case of non regular grid, the y axis is approximated.
    """

    sendMessage.emit('Shapping 2d data for display', 'orange')

    # Nb points in the 1st dimension
    xn = len(np.unique(x))

    # Nb points in the 2nd dimension
    xx = np.array([])
    for i in np.unique(x):
        xx = np.append(xx, len(x[x==i]))
    yn = int(xx.max())

    # If interuption, we calculated the number of missing point and add them
    if len(np.unique(xx)) != 1:

        p = np.full(int(xx.max() - xx.min()), np.nan)

        x = np.append(x, p)
        y = np.append(y, p)
        z = np.append(z, p)

    # We create 2D arrays for each dimension
    x = x.reshape(xn, yn)
    y = y.reshape(xn, yn)
    z = z.reshape(xn, yn)

    # Once the shape is corrected, we sort the data
    m = x[:,0].argsort()
    x = x[m]
    y = y[m]
    z = z[m]

    # If the data has a rectangular shape (usual 2d measurement)
    if len(np.unique(y[:,0]))==1:

        # Take a slice of x
        xx = x[:,0]

        # Find a row of y containing only non nan data
        i = 0
        for i in y:
            if not np.any(np.isnan(i)):
                yy = i
                break
            i+=1

        zz = z
    else:

        sendMessage.emit('Irregular grid detected, shapping 2d data', 'orange')

        xx = x[:,0]

        # Create a bigger array containing sorted data in the same bases
        # New y axis containing all the previous y axes
        yd = np.gradient(np.sort(y[0])).min()
        yy = np.arange(y[~np.isnan(y)].min(), y[~np.isnan(y)].max()+yd, yd)

        # fit the z value to the new grid
        zz = np.full((len(xx), len(yy)), np.nan)
        for x_index in range(len(x)):
            for y_index in range(len(y.T)):
                zz[x_index,np.abs(yy-y[x_index, y_index]).argmin()] = z[x_index,y_index]



    # If there is only one point in x or y, we artificialy create more
    # moreThanOneColumn = True
    if len(xx)==1:
        xx = np.array([xx[0]-0.1, xx[0]+0.1])
        # moreThanOneColumn = False
    if len(yy)==1:
        yy = np.array([yy[0]-0.1, yy[0]+0.1])
        # moreThanOneColumn = False

    # We filtered out the npinf and -np.inf data and replaced them by np.nan
    # This is done to allow display by the pyqtgraph viewbox.
    zz[zz== np.inf] = np.nan
    zz[zz==-np.inf] = np.nan

    return xx, yy, zz


def make_grid(x: np.ndarray,
              y: np.ndarray,
              z: np.ndarray) -> Tuple[np.ndarray,
                                      np.ndarray,
                                      np.ndarray]:
    """
    Takes x, y, z values as lists and returns a 2D numpy array
    https://stackoverflow.com/questions/30764955/python-numpy-create-2d-array-of-values-based-on-coordinates
    """
    dx = abs(np.sort(np.unique(x))[1] - np.sort(np.unique(x))[0])
    dy = abs(np.sort(np.unique(y))[1] - np.sort(np.unique(y))[0])
    i = np.rint((x - min(x))/dx).astype(int)
    j = np.rint((y - min(y))/dy).astype(int)
    xx = np.nan * np.empty(len(np.unique(i)))
    yy = np.nan * np.empty(len(np.unique(j)))
    zz = np.nan * np.empty((len(np.unique(i)), len(np.unique(j))))
    xx[i] = x
    yy[j] = y
    zz[i, j] = z
    return xx, yy, zz


def shapeData2dPolygon(x : np.ndarray,
                       y : np.ndarray,
                       z : np.ndarray,
                       sendMessage: QtCore.pyqtSignal) -> Tuple[np.ndarray,
                                                                         np.ndarray,
                                                                         np.ndarray]:
    """
    Reshape 2d scan into a meshing.

    Return
    ------
        x2dVertices : 2d np.array
            Vertices along x of the polygons
        y2dVertices : 2d np.array
            Vertices along y of the polygons
        z2d : 2d np.array
            Value of the polygons
    """

    sendMessage.emit('Shapping 2d data for display', 'orange')

    ## Treat the data depending on their shape
    # We get the number of point in the x and y dimension
    # We add fake data (with np.nan value for the xaxis) for unfinished
    # measurements

    # Finished regular grid
    if len(np.unique([len(x[x==i])for i in np.unique(x)]))==1 and len(np.unique(y))==len(y[::len(np.unique(x))]):

        # Nb points in the 1st dimension
        xn = len(np.unique(x))

        # Nb points in the 2nd dimension
        yn = len(y[::xn])# Finished regular grid

    # Finished unregular grid
    elif len(np.unique([len(x[x==i])for i in np.unique(x)]))==1 :

        # Nb points in the 1st dimension
        xn = len(np.unique(x))

        # Nb points in the 2nd dimension
        yn = len(y[::xn])

    # Unfinished unregular grid
    elif y[0]!=y[len(x[x==x[0]])]:

        # Nb points in the 1st dimension
        xn = len(np.unique(x))

        # Nb points in the 2nd dimension
        yn = len(x[x==x[0]])

        ## Build "full" x, y and z

        # Find how many element a finished grid would have
        # Number of element per x value
        t = np.array([len(x[x==i])for i in np.unique(x)])
        tmax = max(t)
        # Number of element if the measurement was finished
        tFinished = (len(t[t==min(t)]) + len(t[t==tmax]))*tmax
        # Number of missing element
        nbMissing = tFinished - len(x)

        ## Interpolate last y value based on the last done scan
        # Last full y measured
        yLastFull = y[-2*tmax+nbMissing:-tmax+nbMissing]
        dyLastFull = np.gradient(yLastFull)
        dyinterp = np.gradient(yLastFull)[-nbMissing:]

        yMissing = np.array([y[-1]])
        for i in dyinterp:
            yMissing = np.append(yMissing, yMissing[-1] + i)


        x = np.concatenate((x, [x[-1]]*nbMissing))
        y = np.concatenate((y, yMissing[1:]))
        z = np.concatenate((z, [np.nan]*nbMissing))

    # Unfinished regular grid
    else:

        ## Build "full" x, y and z

        # Find how many element a finished grid would have
        # Number of element per x value
        t = np.array([len(x[x==i])for i in np.unique(x)])
        # Number of element if the measurement was finished
        tFinished = (len(t[t==min(t)]) + len(t[t==max(t)]))*max(t)
        # Number of missing element
        nbMissing = tFinished - len(x)

        # Nb points in the 1st dimension
        xn = len(np.unique(x))
        # Nb points in the 2nd dimension
        yn = len(np.unique(y))

        x = np.concatenate((x, [x[-1]]*nbMissing))
        y = np.concatenate((y, y[:yn][-nbMissing:]))
        z = np.concatenate((z, [np.nan]*nbMissing))



    ## Get the 2d matrices for x, y and z
    # x and y are the vertices of the polygon and their shape should be
    # x[i+1, j+1] and y[i+1, j+1] while z is the value of the polygon and
    # its shape should be z[i, j]

    x2d = x.reshape((xn, yn))
    dx = np.gradient(x2d, axis=0)/2.
    x2dVertices = np.concatenate((x2d - dx, [x2d[-1]+dx[-1]]))
    x2dVertices = np.concatenate((x2dVertices, np.array([x2dVertices[:,1]]).T), axis=1)


    y2d = y.reshape((xn, yn))
    dy = np.gradient(y2d, axis=1)/2.
    y2dVertices = np.concatenate((y2d - dy, np.array([y2d[:,-1]+dy[:,-1]]).T), axis=1)
    y2dVertices = np.concatenate((y2dVertices, np.array([y2dVertices[-1]*2 -y2dVertices[-2] ])))


    z2d = z.reshape((xn, yn))


    return x2dVertices, y2dVertices, z2d


def getDialogWidthHeight(nbDialog: int) -> Tuple[List[int]]:
    """
    Return the dialog position (x, y) and size (width, height) so that the given
    number of dialog windows tile the entire screen.

    Args:
        nbDialog: Number of dialog window we have to cover the screen

    Returns:
        tuple: dialogXs, dialogYs, dialogWidths, dialogHeights
    """

    screenSize = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    screenHeight = screenSize.height()
    screenWidth  = screenSize.width()

    if nbDialog==1:
        dialogWidth  = screenWidth
        dialogHeight = screenHeight
    # if even number of dialog
    elif nbDialog%2==0:
        dialogWidth  = screenWidth/2
        dialogHeight = screenHeight/(nbDialog//2)
    # if odd number of dialog
    else:
        dialogWidth  = screenWidth/2
        dialogHeight = screenHeight/(nbDialog//2+1)
    dialogWidths = [int(dialogWidth)]*nbDialog
    dialogHeights = [int(dialogHeight)]*nbDialog

    xs = [0]*nbDialog
    ys = [0]*nbDialog
    for i in range(nbDialog):
        if i%2==0:
            xs[i] = 0
        else:
            xs[i] = int(dialogWidth)

        ys[i] = int(i//2*dialogHeight)

    return xs, ys, dialogWidths, dialogHeights


####################################################################
#                       Live plot window support                   #
####################################################################


# Set the maximum number of LIVE windows that tiled over the screen (split into two columns).
# The oldest window will close automatically if a new window emerges.
MAX_LIVE_PLOTS = config["livePlotWindowNumber"]

# An "auto plot" dynamics window pops up if 1) a live plot is detected, 2) double click on a Labrad dataset
# The size of the auto opened plot window, [width, height]
LIVE_PLOT_WINDOW_SIZE = config["liveDialogWindowSize"]
# On which screen you are intend to show the auto plot window, 0 to n-1
LIVE_PLOT_SCREEN_INDEX = config["livePlotScreenIndex"]
# offset of the plot windows, defaults to [0, 0]
LIVE_PLOT_WINDOW_OFFSETS = config['liveDialogWindowOffsets']


def plotIdGenerator() -> Generator:
    """
    circular generator for the live plot index
    """
    num = 0
    while True:
        yield num % MAX_LIVE_PLOTS
        num += 1


def getTiledWindowWidthHeight(nbSubWindows: int, plotId: int) -> Tuple[List[int]]:
    """
    Return the positions and sizes of indexed windows that will tile the screen

    We want to create windows for live plot datasets, which currently tile over the screen by regions in two columns
    each region is for a dataset, indexed by the 'plotID'.

    For a 1D dataset, we just create a window that fill the region;
    For a 2D dataset with dependents of 'nbSubWindows', we create two columns of small sub windows to tile over the region

    Args:
        nbSubWindows: Number of tiled sub plot windows for the window of plotID
        plotId: Index of the region that tiled the screen, an int value within [0, MAX_LIVE_PLOTS - 1]

    Returns:
        tuple: dialogXs, dialogYs, dialogWidths, dialogHeights
    """

    # get user screen layout
    desktop = QtWidgets.QDesktopWidget()
    live_screen = desktop.screen(LIVE_PLOT_SCREEN_INDEX)
    screenSize = live_screen.geometry()
    screenWidth = LIVE_PLOT_WINDOW_SIZE[0]
    screenHeight = LIVE_PLOT_WINDOW_SIZE[1]
    x_offset, y_offset = np.array(screenSize.getCoords()[:2]) + np.array(LIVE_PLOT_WINDOW_OFFSETS)


    # for region of plotID

    _xs = [0] * MAX_LIVE_PLOTS
    _ys = [0] * MAX_LIVE_PLOTS
    for i in range(MAX_LIVE_PLOTS):
        if i % 2 == 0:
            _xs[i] = x_offset
        else:
            _xs[i] = int(screenWidth) + x_offset

        _ys[i] = int(i // 2 * screenHeight) + y_offset

    # for sub windows

    if nbSubWindows == 1:
        dialogWidth = screenWidth
        dialogHeight = screenHeight
    # if even number of dialog
    elif nbSubWindows % 2 == 0:
        dialogWidth = screenWidth / 2
        dialogHeight = screenHeight / (nbSubWindows // 2)
    # if odd number of dialog
    else:
        dialogWidth = screenWidth / 2
        dialogHeight = screenHeight / (nbSubWindows // 2 + 1)
    dialogWidths = [int(dialogWidth)] * nbSubWindows
    dialogHeights = [int(dialogHeight)] * nbSubWindows

    xs = [0] * nbSubWindows
    ys = [0] * nbSubWindows
    for i in range(nbSubWindows):
        if i % 2 == 0:
            xs[i] = 0
        else:
            xs[i] = int(dialogWidth)
        ys[i] = int(i // 2 * dialogHeight)

    xs = [x + _xs[plotId] for x in xs]
    ys = [y + _ys[plotId] for y in ys]
    return xs, ys, dialogWidths, dialogHeights

####################################################################
#                    End of Live plot window                       #
####################################################################

