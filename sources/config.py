# This Python file uses the following encoding: utf-8

# This file create a python dict containing all personalized parameters
config = {

# Do not put "/" after ":" in the two following paths
# The soft will not allowed to go above that path
'root' : 'S:/132-PHELIQS/132.05-LATEQS/132.05.01-QuantumSilicon',
# Default display path, should be at least the root
'path' : 'S:/132-PHELIQS/132.05-LATEQS/132.05.01-QuantumSilicon',
# Folder having these names will be colored, easier to browse
'enhancedFolder' : ['bluelagoon','Cryoconcept', 'RF4K_stick', 'smurf', 'Tritonito', 'data'],
# Other files will not appear in the plotter
'authorizedExtension' : ['db', 'csv', 's2p'], 
# Will not be displayed, usefull for some windows file
'forbiddenFile' : ['Thumbs.db'], 
# If False the path is displayed
'displayOnlyDbNameInPlotTitle' : False, 
'displayedDownloadQcodesPercentage' : 5, # int

# Message to display when station has not been defined in a qcodes experiment
'defaultSnapshot' : '<span style="color: red; font-weight: bold;">Station undefined, you fool</span>',

# Authorized OpenGL
# Make pyqtgraph faster but may cause issues on some computers
# If you encounter issues with opengl, set this to False.
'pyqtgraphOpenGL' : True,

# Live plot
'livePlotTimer' : 1, # In second

# Interactivity
'keyPressedStared' : 's', # To star a run
'keyPressedHide' : 'h', # To hide a run
'fileNameRunInfo' : 'runinfo', # Will be saved as a hidden json file
'runStaredColor' : (255, 255, 0),
'runHiddenColor' : (255, 0, 0),

## BlueFors
# Linked file name to plot y axis (x axis being a timestamp)
'CH1 P'     : 'Power 50K plate [W]',
'CH1 R'     : u'Resistance 50K plate [Ω]',
'CH1 T'     : 'Temperature 50K plate [K]',
'CH2 P'     : 'Power 4K plate [W]',
'CH2 R'     : u'Resistance 4K plate [Ω]',
'CH2 T'     : 'Temperature 4K plate [K]',
'CH3 P'     : 'Power magnet [W]',
'CH3 R'     : u'Resistance magnet [Ω]',
'CH3 T'     : 'Temperature magnet [K]',
'CH5 P'     : 'Power still [W]',
'CH5 R'     : u'Resistance still [Ω]',
'CH5 T'     : 'Temperature still [K]',
'CH6 P'     : 'Power mixing chamber [W]',
'CH6 R'     : u'Resistance mixing chamber [Ω]',
'CH6 T'     : 'Temperature mixing chamber [K]',
'Flowmeter' : 'Flow of mixture [mmol/s]',
'maxigauge' : {'ch1' : 'Vacuum can [mBar]',
               'ch2' : 'Pumping line [mBar]',
               'ch3' : 'Compressor outlet [mBar]',
               'ch4' : 'Compressor inlet [mBar]',
               'ch5' : 'Mixture tank [mBar]',
               'ch6' : 'Venting line [mBar]'},


# Layout parameters
'dialogWindowSize' : (1.618*500, 500),
'dialogBackgroundColor'    : '#272822',
'pyqtgraphBackgroundColor' : '#272822',
'dialogTextColor'          : '#ffffff',
'pyqtgraphTitleTextColor'  : '#ffffff',
'pyqtgraphxLabelTextColor' : '#ffffff',
'pyqtgraphyLabelTextColor' : '#ffffff',
'pyqtgraphzLabelTextColor' : '#ffffff',
'pyqtgraphxAxisTicksColor' : '#ffffff',
'pyqtgraphyAxisTicksColor' : '#ffffff',
'pyqtgraphzAxisTicksColor' : '#ffffff',
'sweptParameterSeparator' : " <span style='font-weight: bold; color: #eb272e;'>vs</span> ",


# Plot parameters
# To avoid heavy calculations and consequently lag, we limit the colormap to a
# certain number of points and realize a linear interpolation between those points
# The default is 8 (above 8 will make some colormap crash)
'2dMapNbColorPoints' : 8,
'2dDownSampling' : False,
'plotShrinkActiveArea' : 2, # In percentage
'plot1dGrid' : True,
'plot1dSymbol' : ['o', 's', 't', 'd', '+'],
'plot1dAntialias' : False,
'plot2dcm' : 'Viridis', # Default colormap
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
"plotCoordinateNbNumber" : '5', # str, how many decimal for coordinates

"fitParameterNbNumber" : '3', # str, how many decimal for the displayed fit parameters

# crosshair
'crossHairLineWidth' : 3,
'crossHairLineColor' : 'w',
'crossHairLineStyle' : 'solid', # solid, dashed, dotted, dashed-dotted
}
