import json
import os
from platformdirs import user_config_dir
from typing import List, Union, Any
# For python < 3.10
try:
    from collections import Mapping
except:
    from collections.abc import Mapping # type: ignore

# This file create a python dict containing all personalized parameters
configPackage = {

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
                         'npz',
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
# Number of decimal for the progress bar
'progressBarDecimal' : 100, # int
# The delay in ms between to check of a run download
'delayBetweenProgressBarUpdate' : 100, # int
# Number of runs to be transferred at the same time when displaying a database
'NbRunEmit' : 100, # int
# Delay between to consecutive check of the total nb of run in a database
'delayBetweendataBaseNbRunCheck' : 5, # in s
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
'livePlotTitleAppend' : ' <span style="color: green; font-weight: bold;">Measuring</span>',
# Default folder open when clicking on the select database of the liveplot dialog
'livePlotDefaultFolder' : 'C:/',
'liveDialogWindowSize': [720, 640],
'liveDialogWindowOffsets': [0, 0],
'livePlotWindowNumber': 1,
'livePlotScreenIndex': 0, # 0 to n-1


# Interactivity
'keyPressedStared' : 's', # To star a run
'keyPressedHide' : 'h', # To hide a run
'fileNameRunInfo' : 'runinfo', # Will be saved as a hidden json file
'runStaredColor' : (255, 0, 0),
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
'Status' : {'cpatempwi' : {'labelText'  : 'Compressor water temperature in',
                           'labelUnits' : u'°C'},
            'cpatempwo' : {'labelText'  : 'Compressor water temperature out',
                           'labelUnits' : u'°C'},
            'cpatempo'  : {'labelText'  : 'Compressor oil temperature',
                           'labelUnits' : u'°C'},
            'cpatemph'  : {'labelText'  : 'Compressor helium temperature',
                           'labelUnits' : u'°C'}},


# Layout parameters
'dialogWindowSize' : (1314, 500),
'sweptParameterSeparator' : " <span style='font-weight: bold; color: #eb272e;'>vs</span> ",

'style' : 'qbstyles', # Must match an available style below
'styles' : {'qdarkstyle' : {'dialogBackgroundColor'    : '#272822',
                            'pyqtgraphBackgroundColor' : '#272822',
                            'dialogTextColor'          : '#ffffff',
                            'plot1dSelectionLineColor' : '#ffffff',
                            'pyqtgraphTitleTextColor'  : '#ffffff',
                            'pyqtgraphxLabelTextColor' : '#ffffff',
                            'pyqtgraphyLabelTextColor' : '#ffffff',
                            'pyqtgraphzLabelTextColor' : '#ffffff',
                            'pyqtgraphxAxisTicksColor' : '#ffffff',
                            'pyqtgraphyAxisTicksColor' : '#ffffff',
                            'pyqtgraphzAxisTicksColor' : '#ffffff',
                            'pyqtgraphxAxisTickLabelsColor': '#ffffff',
                            'pyqtgraphyAxisTickLabelsColor': '#ffffff',
                            'pyqtgraphzAxisTickLabelsColor': '#ffffff',

                            # Font color for the duration column of the tableWidgetDatabase
                            'tableWidgetDatabaseDuration' : {
                                'hour'        : '#9292ff',
                                'minute'      : '#008080',
                                'second'      : '#a221de',
                                'millisecond' : '#e01f1f'
                                },
                           },
            'qbstyles' : {'dialogBackgroundColor'    : '#0c1c23',
                          'pyqtgraphBackgroundColor' : '#0c1c23',
                          'dialogTextColor'          : '#dadcdd',
                          'plot1dSelectionLineColor' : '#dadcdd',
                          'pyqtgraphTitleTextColor'  : '#dadcdd',
                          'pyqtgraphxLabelTextColor' : '#dadcdd',
                          'pyqtgraphyLabelTextColor' : '#dadcdd',
                          'pyqtgraphzLabelTextColor' : '#dadcdd',
                          'pyqtgraphxAxisTicksColor' : '#dadcdd',
                          'pyqtgraphyAxisTicksColor' : '#dadcdd',
                          'pyqtgraphzAxisTicksColor' : '#dadcdd',
                          'pyqtgraphxAxisTickLabelsColor': '#dadcdd',
                          'pyqtgraphyAxisTickLabelsColor': '#dadcdd',
                          'pyqtgraphzAxisTickLabelsColor': '#dadcdd',

                          # Font color for the duration column of the tableWidgetDatabase
                          'tableWidgetDatabaseDuration' : {
                              'hour'        : '#9292ff',
                              'minute'      : '#008080',
                              'second'      : '#a221de',
                              'millisecond' : '#e01f1f'
                              },
                         },
            'white' : {'dialogBackgroundColor'    : '#ffffff',
                       'pyqtgraphBackgroundColor' : '#ffffff',
                       'dialogTextColor'          : '#000000',
                       'plot1dSelectionLineColor' : '#000000',
                       'pyqtgraphTitleTextColor'  : '#000000',
                       'pyqtgraphxLabelTextColor' : '#000000',
                       'pyqtgraphyLabelTextColor' : '#000000',
                       'pyqtgraphzLabelTextColor' : '#000000',
                       'pyqtgraphxAxisTicksColor' : '#000000',
                       'pyqtgraphyAxisTicksColor' : '#000000',
                       'pyqtgraphzAxisTicksColor' : '#000000',
                       'pyqtgraphxAxisTickLabelsColor': '#000000',
                       'pyqtgraphyAxisTickLabelsColor': '#000000',
                       'pyqtgraphzAxisTickLabelsColor': '#000000',

                        # Font color for the duration column of the tableWidgetDatabase
                        'tableWidgetDatabaseDuration' : {
                            'hour'        : '#1111dd',
                            'minute'      : '#008080',
                            'second'      : '#a221de',
                            'millisecond' : '#e01f1f'
                            },
                      },
           },

# Columns of tableWidgetDatabase
'DatabaseDisplayColumn' : {
    'databaseAbsPath' : {
        'index' : 0,
        'name' : '',
        'visible' : False
    },
    'itemRunId' : {
        'index' : 1,
        'name' : 'run id',
        'visible' : True
    },
    'dimension' : {
        'index' : 2,
        'name' : 'dim',
        'visible' : True
    },
    'experimentName' : {
        'index' : 3,
        'name' : 'experiment',
        'visible' : True
    },
    'sampleName' : {
        'index' : 4,
        'name' : 'sample',
        'visible' : True
    },
    'runName' : {
        'index' : 5,
        'name' : 'name',
        'visible' : True
    },
    'captured_run_id' : {
        'index' : 6,
        'name' : 'captured_run_id',
        'visible' : True
    },
    'guid' : {
        'index' : 7,
        'name' : 'guid',
        'visible' : True
    },
    'started' : {
        'index' : 8,
        'name' : 'started',
        'visible' : True
    },
    'completed' : {
        'index' : 9,
        'name' : 'completed',
        'visible' : True
    },
    'duration' : {
        'index' : 10,
        'name' : 'duration',
        'visible' : True
    },
    'runRecords' : {
        'index' : 11,
        'name' : 'records',
        'visible' : True
    },
    'comment' : {
        'index' : 12,
        'name' : 'comment',
        'visible' : True
    },
},

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
'plotHideInteractionPanel': False,
# List of derivative for 2d plot
# Each new entry should also be coded in the comboBoxDerivativeActivated method
# see plot_2d_app.py.
'plot2dDerivative' : ['∂z/∂x',
                      '∂z/∂y',
                      '√((∂z/∂x)² + (∂z/∂y)²)',
                      '∂²z/∂x²',
                      '∂²z/∂y²',
                      'sobel'],
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
"plotDataItemWidth" : 1,
"plotDataItemShadowWidth" : 10,
"plotCoordinateNbNumber" : '2', # str, how many decimal for coordinates

"fitParameterNbNumber" : 3, # int, how many decimal for the displayed fit parameters

# crosshair
'crossHairLineWidth' : 3,
'crossHairLineColor' : ( 51, 160,  44),
'crossHairLineStyle' : 'solid', # solid, dashed, dotted, dashed-dotted
}



###########################################################################
#
#
#                           Current config file
#
#
###########################################################################



def getConfigCurrentPath() -> str:
    """
    Return the path of the current configuration file
    """

    return os.path.join(user_config_dir('pyplotter'), 'current_config.py')



def deep_update(source: dict,
                overrides: Any) -> dict:
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.

    From:
    https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """

    for key, value in overrides.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source



def saveConfigCurrent() -> None:
    """
    Save the current config file.
    """

    configCurrent = configPackage
    configUser    = json.load(open(getConfigUserPath(), 'r', encoding='utf-8'))

    configCurrent = deep_update(configCurrent, configUser)

    with open(getConfigCurrentPath(), 'w', encoding='utf-8') as f:
        json.dump(configCurrent, f, ensure_ascii=False, indent=4)
    f.close()



def loadConfigCurrent() -> dict:
    """
    Return the current configuration as a dictionnary.
    """

    with open(getConfigCurrentPath(), 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config



###########################################################################
#
#
#                           User config file
#
#
###########################################################################



def getConfigUserPath() -> str:
    """
    Return the path of the user configuration file
    """

    return os.path.join(user_config_dir('pyplotter'), 'user_config.py')



def nested_update(obj, keys, value):
    if len(keys)>1:
        nested_update(obj[keys[0]], keys[1:], value)
    else:
        obj[keys[0]]=value



def updateUserConfig(key: Union[str, List[str]],
                     val: Union[str, int]) -> None:
    """
    Update the user config file located in user_config_dir('pyplotter') directory.
    Usually C:/Users/.../AppData/Local/pyplotter/pyplotter on windows 10.

    Args:
        key: key(s) to be updated
        val: val to be updated
    """

    d = json.load(open(getConfigUserPath(), 'r', encoding='utf-8'))

    if isinstance(key, str):
        d[key] = val
    elif isinstance(key, list):
        temp = configPackage[key[0]]
        nested_update(temp, key[1:], val)
        d[key[0]] = temp

    with open(getConfigUserPath(), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
    f.close()

    saveConfigCurrent()



###########################################################################
#
#
#                           Current config file
#
#
###########################################################################



def initConfig() -> None:
    """
    Initialize the configuration file:
        1. load the default package config file.
        2. Load the user config file.
        3. Create the current config file by overwrite the package file by the
           user one.
    """

    # If there is no folder for the pyplotter package, we create one
    if not os.path.isdir(user_config_dir('pyplotter')):
        from pathlib import Path
        Path(user_config_dir('pyplotter')).mkdir(parents=True)

    # If there is no file for the user config, we create one
    if not os.path.isfile(getConfigUserPath()):
        with open(getConfigUserPath(), 'w', encoding='utf-8') as f:
            json.dump({'user' : True}, f, ensure_ascii=False, indent=4)
        f.close()

    # If there is no file for the current config, we create one
    if not os.path.isfile(getConfigCurrentPath()):
        with open(getConfigCurrentPath(), 'w', encoding='utf-8') as f:
            json.dump(configPackage, f, ensure_ascii=False, indent=4)
        f.close()

    # Overwrite the package file by the user one
    saveConfigCurrent()
