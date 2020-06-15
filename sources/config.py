# This Python file uses the following encoding: utf-8

# This file create a python dict containing all personalized parameters
config = {

# Do not put "/" after ":" in the two following paths
# The soft will not allowed to go above that path
'root' : 'S:/132-PHELIQS/132.05-LATEQS/132.05.01-QuantumSilicon',
# Default display path
'path' : 'S:/132-PHELIQS/132.05-LATEQS/132.05.01-QuantumSilicon',
'authorized_setup' : ['bluelagoon'],
'authorized_extension' : ['db'],

# Authorized OpenGL
'pyqtgraphOpenGL' : True,

# Layout parameters
'dialogWindowSize' : (1.618*500, 500),
'dialogBackgroundColor'    : '#272822',
'pyqtgraphBackgroundColor' : '#272822',
'dialogTextColor'           : '#ffffff',
'pyqtgraphTitleTextColor'  : '#ffffff',
'pyqtgraphxLabelTextColor' : '#ffffff',
'pyqtgraphyLabelTextColor' : '#ffffff',
'pyqtgraphzLabelTextColor' : '#ffffff',
'pyqtgraphxAxisTicksColor' : '#ffffff',
'pyqtgraphyAxisTicksColor' : '#ffffff',
'pyqtgraphzAxisTicksColor' : '#ffffff',
'fileStared' : '#eb272e',


# Plot parameters
# To avoid heavy calculations and consequently lag, we limit the colormap to a
# certain number of points and realize a linear interpolation between those points
# The default is 10.
'2dMapNbColorPoints' : 10,
'plotShrinkActiveArea' : 2, # In percentage
'plot1dGrid' : True,
'plot1dSymbol' : ['o', 's', 't', 'd', '+'],
'plot1dAntialias' : False,
'plot2dcm' : 'viridis',
'colormaps' : ['viridis','tab20c','tab20b','tab10','rainbow','prism','plasma',
               'pink','ocean','nipy_spectral','magma','jet','inferno','hsv',
               'gnuplot2','gnuplot','gist_yarg','gist_ncar','gist_heat',
               'coolwarm','cividis','afmhot','YlOrRd','YlOrBr','YlGnBu','YlGn',
               'Spectral','Set3','Set1','Reds','RdYlGn','RdYlBu','RdPu','RdGy',
               'RdBu','Purples','PuRd','PuOr','PuBuGn','PuBu','PiYG','Pastel1',
               'Paired','PRGn','Oranges','Greys','Greens','GnBu','CMRmap',
               'BuPu','BuGn','BrBG','Blues'],
'plot1dColors': [(0,   191, 191), 
                 (0,   0,   255), 
                 (0,   128, 0), 
                 (191, 191, 0),
                 (0,   0,   0), 
                 (255, 0,   0), 
                 (191, 0,   191)],
'plot1dColorsComplementary': [(191, 0,   0), 
                              (255, 0,   0), 
                              (128, 0,   128), 
                              (0,   191, 0),
                              (255, 255, 255), 
                              (0,   255, 255), 
                              (0,   191, 0)],
"plotDataItemWidth" : 2,
"plotDataItemShadowWidth" : 10,

# crosshair
'crossHairLineWidth' : 3,
'crossHairLineColor' : 'w',
'crossHairLineStyle' : 'solid', # solid, dashed, dotted, dashed-dotted
}
