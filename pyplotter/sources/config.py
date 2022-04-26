# This Python file uses the following encoding: utf-8

# This file create a python dict containing all personalized parameters
config = {

# Do not put "/" after ":" in the two following paths
# The soft will not allowed to go above that path
'root' : 'C:/',
# Default display path, should be at least the root
'path' : 'C:/',
# Folder having these names will be colored, easier to browse
'enhancedFolder' : ['bluelagoon',
                    'Cryoconcept',
                    'RF4K_stick',
                    'smurf',
                    'Tritonito',
                    'triton',
                    'data',
                    '2021'],
# Other files will not appear in the plotter
'authorizedExtension' : ['db',
                         'csv',
                         's2p'],
# Will not be displayed, usefull for some windows file
'forbiddenFile' : ['thumbs.db',
                   'Thumbs.db'],

# If False the path is displayed in the plot title
'displayOnlyDbNameInPlotTitle' : True,
# If True the run id is added to the window title
'displayRunIdInPlotTitle' : True,
# If True the run name is added to the window title
'displayRunNameInPlotTitle' : True,

# Maximum number of runs being treated on the same SQL request
# Should be somwhere below 2020
'maximumRunPerRequest' : 2000, # int

# Gives the downloading file percentage must progressed to be displayed
'displayedDownloadQcodesPercentage' : 5, # int

# Number of runs to be transferred at the same time when displaying a database
'NbRunEmit' : 100, # int

# Message to display when station has not been defined in a qcodes experiment
'defaultSnapshot' : '<span style="color: red; font-weight: bold;">Station undefined, you fool</span>',

# Authorized OpenGL
# Make pyqtgraph faster but may cause issues on some computers
# If you encounter issues with opengl, set this to False.
'pyqtgraphOpenGL' : True,

# Live plot
'livePlotTimer' : 1, # In second
# Added to the plot title while a live plot is still measured.
# Removed once the measurement is done.
'livePlotMessageStart' : '<div style="color: green; font-weight: bold; text-align: center;">LivePlot</div><br>',
# 'livePlotTitleAppend' : ' <span style="color: green; font-weight: bold;">Measuring</span>',

# Interactivity
'keyPressedStared' : 's', # To star a run
'keyPressedHide' : 'h', # To hide a run
'fileNameRunInfo' : 'runinfo', # Will be saved as a hidden json file
'runStaredColor' : (255, 255, 0),
'runHiddenColor' : (255, 0, 0),

## BlueFors
# Linked file name to plot y axis (x axis being a timestamp)
'CH1 P'     : {'labelText'  : 'Power 50K plate',
               'labelUnits' : 'W'},
'CH1 R'     : {'labelText'  : 'Resistance 50K plate',
               'labelUnits' : u'Ω'},
'CH1 T'     : {'labelText'  : 'Temperature 50K plate',
               'labelUnits' : 'K'},
'CH2 P'     : {'labelText'  : 'Power 4K plate',
               'labelUnits' : 'W'},
'CH2 R'     : {'labelText'  : 'Resistance 4K plate',
               'labelUnits' : u'Ω'},
'CH2 T'     : {'labelText'  : 'Temperature 4K plate',
               'labelUnits' : 'K'},
'CH3 P'     : {'labelText'  : 'Power magnet',
               'labelUnits' : 'W'},
'CH3 R'     : {'labelText'  : 'Resistance magnet',
               'labelUnits' : u'Ω'},
'CH3 T'     : {'labelText'  : 'Temperature magnet',
               'labelUnits' : 'K'},
'CH5 P'     : {'labelText'  : 'Power still',
               'labelUnits' : 'W'},
'CH5 R'     : {'labelText'  : 'Resistance still',
               'labelUnits' : u'Ω'},
'CH5 T'     : {'labelText'  : 'Temperature still',
               'labelUnits' : 'K'},
'CH6 P'     : {'labelText'  : 'Power mixing chamber',
               'labelUnits' : 'W'},
'CH6 R'     : {'labelText'  : 'Resistance mixing chamber',
               'labelUnits' : u'Ω'},
'CH6 T'     : {'labelText'  :'Temperature mixing chamber',
               'labelUnits' : 'K'},
'Flowmeter' : {'labelText' : 'Flow of mixture',
               'labelUnits' : 'mol/s'},
'maxigauge' : {'labelText' : 'Pressure Gauges',
               'ch1' : {'labelText'  : 'Vacuum can',
                        'labelUnits' : 'Bar'},
               'ch2' : {'labelText'  : 'Pumping line',
                        'labelUnits' : 'Bar'},
               'ch3' : {'labelText'  : 'Compressor outlet',
                        'labelUnits' : 'Bar'},
               'ch4' : {'labelText'  : 'Compressor inlet',
                        'labelUnits' : 'Bar'},
               'ch5' : {'labelText'  : 'Mixture tank',
                        'labelUnits' : 'Bar'},
               'ch6' : {'labelText'  : 'Venting line',
                        'labelUnits' : 'Bar'}},


# Layout parameters
'dialogWindowSize' : (1.618*750, 500),
'sweptParameterSeparator' : " <span style='font-weight: bold; color: #eb272e;'>vs</span> ",

'style' : 'qbstyles', # Must match an available style below
'styles' : {'qdarkstyle' : {'dialogBackgroundColor'    : '#272822',
                            'pyqtgraphBackgroundColor' : '#272822',
                            'dialogTextColor'          : '#ffffff',
                            'pyqtgraphTitleTextColor'  : '#ffffff',
                            'pyqtgraphxLabelTextColor' : '#ffffff',
                            'pyqtgraphyLabelTextColor' : '#ffffff',
                            'pyqtgraphzLabelTextColor' : '#ffffff',
                            'pyqtgraphxAxisTicksColor' : '#ffffff',
                            'pyqtgraphyAxisTicksColor' : '#ffffff',
                            'pyqtgraphzAxisTicksColor' : '#ffffff'},
            'qbstyles' : {'dialogBackgroundColor'    : '#0c1c23',
                            'pyqtgraphBackgroundColor' : '#0c1c23',
                            'dialogTextColor'          : '#dadcdd',
                            'pyqtgraphTitleTextColor'  : '#dadcdd',
                            'pyqtgraphxLabelTextColor' : '#dadcdd',
                            'pyqtgraphyLabelTextColor' : '#dadcdd',
                            'pyqtgraphzLabelTextColor' : '#dadcdd',
                            'pyqtgraphxAxisTicksColor' : '#dadcdd',
                            'pyqtgraphyAxisTicksColor' : '#dadcdd',
                            'pyqtgraphzAxisTicksColor' : '#dadcdd'},
            'white' : {'dialogBackgroundColor'    : '#ffffff',
                       'pyqtgraphBackgroundColor' : '#ffffff',
                       'dialogTextColor'          : '#000000',
                       'pyqtgraphTitleTextColor'  : '#000000',
                       'pyqtgraphxLabelTextColor' : '#000000',
                       'pyqtgraphyLabelTextColor' : '#000000',
                       'pyqtgraphzLabelTextColor' : '#000000',
                       'pyqtgraphxAxisTicksColor' : '#000000',
                       'pyqtgraphyAxisTicksColor' : '#000000',
                       'pyqtgraphzAxisTicksColor' : '#000000'}},
# Font size of the axis and tick labels
# Handy if user wants to have larger font
'axisLabelFontSize' : 12,
'tickLabelFontSize' : 12,

# Plot parameters
# To avoid heavy calculations and consequently lag, we limit the colormap to a
# certain number of points and realize a linear interpolation between those points
# The default is 8 (above 8 will make some colormap crash)
'2dMapNbColorPoints' : 8,
'2dDownSampling' : False,
'2dGridInterpolation' : 'shape',
'plot1dGrid' : True,
'plot1dSymbol' : ['o', 's', 't', 'd', '+'],
'plot1dAntialias' : False,
'plot2dcm' : 'Viridis', # Default colormap
# List of derivative for 2d plot
# Each new entry should also be coded in the comboBoxDerivativeActivated method
# see plot_2d_app.py.
'plot2dDerivative' : ['∂z/∂x',
                      '∂z/∂y',
                      '√((∂z/∂x)² + (∂z/∂y)²)',
                      '∂²z/∂x²',
                      '∂²z/∂y²'],
'plot1dColors': [(227,  26,  28),
                 ( 51, 160,  44),
                 (255, 127,   0),
                 ( 31, 120, 180),
                 (106, 61,  154),
                 (251, 154, 153),
                 (178, 223, 138),
                 (253, 191, 111),
                 (166, 206, 227),
                 (202, 178, 214)],
'plot1dColorsComplementary': [( 58, 119, 118),
                              (204,  95, 211),
                              (  0, 128, 255),
                              (224, 135,  75),
                              (149, 194, 101),
                              (  4, 101, 102),
                              ( 77,  32, 117),
                              (  2,  64, 144),
                              ( 89,  49,  28),
                              ( 53,  77,  41)],
"plotDataItemWidth" : 2,
"plotDataItemShadowWidth" : 10,
"plotCoordinateNbNumber" : '5', # str, how many decimal for coordinates

"fitParameterNbNumber" : 3, # int, how many decimal for the displayed fit parameters

# crosshair
'crossHairLineWidth' : 3,
'crossHairLineColor' : 'w',
'crossHairLineStyle' : 'solid', # solid, dashed, dotted, dashed-dotted
}
