# This Python file uses the following encoding: utf-8
# Correct bug with pyqtgraph and python3.8 by replacing function name
import numpy as np
try:
    import pyqtgraph as pg
except AttributeError:
    import time
    time.clock = time.perf_counter # type: ignore
    import pyqtgraph as pg
from .config import loadConfigCurrent
config = loadConfigCurrent()

pg.setConfigOption('background', None)
pg.setConfigOption('useOpenGL', config['pyqtgraphOpenGL'])
pg.setConfigOption('antialias', config['plot1dAntialias'])

# Replace a pyqtgraph methods to solve a log plotting issue
def getData(self):
    if self.xData is None:
        return (None, None)

    if( self.xDisp is not None and
        not (self.property('xViewRangeWasChanged') and self.opts['clipToView']) and
        not (self.property('xViewRangeWasChanged') and self.opts['autoDownsample']) and
        not (self.property('yViewRangeWasChanged') and self.opts['dynamicRangeLimit'] is not None)
    ):
        return self.xDisp, self.yDisp
    x = self.xData
    y = self.yData
    if y.dtype == bool:
        y = y.astype(np.uint8)
    if x.dtype == bool:
        x = x.astype(np.uint8)
    view = self.getViewBox()
    if view is None:
        view_range = None
    else:
        view_range = self.getViewBox().viewRect() # this is always up-to-date
    if view_range is None:
        view_range = self.viewRect()

    if self.opts['fftMode']:
        x,y = self._fourierTransform(x, y)
        # Ignore the first bin for fft data if we have a logx scale
        if self.opts['logMode'][0]:
            x=x[1:]
            y=y[1:]

    if self.opts['derivativeMode']:  # plot dV/dt
        y = np.diff(self.yData)/np.diff(self.xData)
        x = x[:-1]
    if self.opts['phasemapMode']:  # plot dV/dt vs V
        x = self.yData[:-1]
        y = np.diff(self.yData)/np.diff(self.xData)

    with np.errstate(divide='ignore'):
        if self.opts['logMode'][0]:
            x = np.log10(np.abs(x))
        if self.opts['logMode'][1]:
            y = np.log10(np.abs(y))

    ds = self.opts['downsample']
    if not isinstance(ds, int):
        ds = 1

    if self.opts['autoDownsample']:
        # this option presumes that x-values have uniform spacing
        if view_range is not None and len(x) > 1:
            dx = float(x[-1]-x[0]) / (len(x)-1)
            if dx != 0.0:
                x0 = (view_range.left()-x[0]) / dx
                x1 = (view_range.right()-x[0]) / dx
                width = self.getViewBox().width()
                if width != 0.0:
                    ds = int(max(1, int((x1-x0) / (width*self.opts['autoDownsampleFactor']))))
                ## downsampling is expensive; delay until after clipping.

    if self.opts['clipToView']:
        if view is None or view.autoRangeEnabled()[0]:
            pass # no ViewBox to clip to, or view will autoscale to data range.
        else:
            # clip-to-view always presumes that x-values are in increasing order
            if view_range is not None and len(x) > 1:
                # print('search:', view_range.left(),'-',view_range.right() )
                # find first in-view value (left edge) and first out-of-view value (right edge)
                # since we want the curve to go to the edge of the screen, we need to preserve
                # one down-sampled point on the left and one of the right, so we extend the interval
                x0 = np.searchsorted(x, view_range.left()) - ds
                x0 = fn.clip_scalar(x0, 0, len(x)) # workaround
                # x0 = np.clip(x0, 0, len(x))

                x1 = np.searchsorted(x, view_range.right()) + ds
                x1 = fn.clip_scalar(x1, x0, len(x))
                # x1 = np.clip(x1, 0, len(x))
                x = x[x0:x1]
                y = y[x0:x1]

    if ds > 1:
        if self.opts['downsampleMethod'] == 'subsample':
            x = x[::ds]
            y = y[::ds]
        elif self.opts['downsampleMethod'] == 'mean':
            n = len(x) // ds
            # x = x[:n*ds:ds]
            stx = ds//2 # start of x-values; try to select a somewhat centered point
            x = x[stx:stx+n*ds:ds]
            y = y[:n*ds].reshape(n,ds).mean(axis=1)
        elif self.opts['downsampleMethod'] == 'peak':
            n = len(x) // ds
            x1 = np.empty((n,2))
            stx = ds//2 # start of x-values; try to select a somewhat centered point
            x1[:] = x[stx:stx+n*ds:ds,np.newaxis]
            x = x1.reshape(n*2)
            y1 = np.empty((n,2))
            y2 = y[:n*ds].reshape((n, ds))
            y1[:,0] = y2.max(axis=1)
            y1[:,1] = y2.min(axis=1)
            y = y1.reshape(n*2)

    if self.opts['dynamicRangeLimit'] is not None:
        if view_range is not None:
            data_range = self.dataRect()
            if data_range is not None:
                view_height = view_range.height()
                limit = self.opts['dynamicRangeLimit']
                hyst  = self.opts['dynamicRangeHyst']
                # never clip data if it fits into +/- (extended) limit * view height
                if ( # note that "bottom" is the larger number, and "top" is the smaller one.
                    not data_range.bottom() < view_range.top()     # never clip if all data is too small to see
                    and not data_range.top() > view_range.bottom() # never clip if all data is too large to see
                    and data_range.height() > 2 * hyst * limit * view_height
                ):
                    cache_is_good = False
                    # check if cached display data can be reused:
                    if self.yDisp is not None: # top is minimum value, bottom is maximum value
                        # how many multiples of the current view height does the clipped plot extend to the top and bottom?
                        top_exc =-(self._drlLastClip[0]-view_range.bottom()) / view_height
                        bot_exc = (self._drlLastClip[1]-view_range.top()   ) / view_height
                        # print(top_exc, bot_exc, hyst)
                        if (    top_exc >= limit / hyst and top_exc <= limit * hyst
                            and bot_exc >= limit / hyst and bot_exc <= limit * hyst ):
                            # restore cached values
                            x = self.xDisp
                            y = self.yDisp
                            cache_is_good = True
                    if not cache_is_good:
                        min_val = view_range.bottom() - limit * view_height
                        max_val = view_range.top()    + limit * view_height
                        if( self.yDisp is not None              # Do we have an existing cache?
                            and min_val >= self._drlLastClip[0] # Are we reducing it further?
                            and max_val <= self._drlLastClip[1] ):
                            # if we need to clip further, we can work in-place on the output buffer
                            # print('in-place:', end='')
                            # workaround for slowdown from numpy deprecation issues in 1.17 to 1.20+ :
                            # np.clip(self.yDisp, out=self.yDisp, a_min=min_val, a_max=max_val)
                            fn.clip_array(self.yDisp, min_val, max_val, out=self.yDisp)
                            self._drlLastClip = (min_val, max_val)
                            # print('{:.1e}<->{:.1e}'.format( min_val, max_val ))
                            x = self.xDisp
                            y = self.yDisp
                        else:
                            # if none of the shortcuts worked, we need to recopy from the full data
                            # print('alloc:', end='')
                            # workaround for slowdown from numpy deprecation issues in 1.17 to 1.20+ :
                            # y = np.clip(y, a_min=min_val, a_max=max_val)
                            y = fn.clip_array(y, min_val, max_val)
                            self._drlLastClip = (min_val, max_val)
                            # print('{:.1e}<->{:.1e}'.format( min_val, max_val ))
    self.xDisp = x
    self.yDisp = y
    self.setProperty('xViewRangeWasChanged', False)
    self.setProperty('yViewRangeWasChanged', False)
    return self.xDisp, self.yDisp

pg.PlotDataItem.getData = getData
