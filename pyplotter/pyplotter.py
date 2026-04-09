from PyQt5.QtWidgets import (
    QApplication,
    QSplashScreen,
)
from PyQt5.QtGui import (
    QGuiApplication,
)
import sys
import os


from PyQt5.QtCore import Qt, QCoreApplication
# to solve this qt issue:
# QtWebEngineWidgets must be imported or Qt.AA_ShareOpenGLContexts must be set before a QCoreApplication instance is created
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
from PyQt5.uic import loadUi



# SplashScreen
class SplashScreen(QSplashScreen):

    def __init__(self) -> None:
        super().__init__()

        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'splashScreen.ui')
        loadUi(ui_path, self)


        self.setWindowFlags(
            Qt.FramelessWindowHint # Remove the frame added by Windows
            |Qt.SplashScreen, # Remove the app from the taskbar
            )

        # Put splashScreen in the middle of the screen
        splashWidth = self.frameGeometry().width()
        splashHeight = self.frameGeometry().height()
        center = QGuiApplication.screens()[0].availableGeometry().center()
        self.move(center.x()-int(splashWidth/2), center.y()-int(splashHeight/2))


    def setLabel(self, label: str) -> None:
        self.label.setText(label)


    def setProgressBar(self, value: int) -> None:
        self.progressBar.setValue(value)



def main():
    app = QApplication(sys.argv)

    # display the splashscreen
    splash = SplashScreen()
    splash.show()

    # Load libraries and show qualitatif progress

    # Init config file, to be done first
    splash.setLabel('Loading configuration')
    from .sources.config import initConfig, loadConfigCurrent
    initConfig()
    config = loadConfigCurrent()
    splash.setProgressBar(5)

    splash.setLabel('Loading numpy')
    import numpy
    splash.setProgressBar(14)

    splash.setLabel('Loading scipy')
    import scipy
    splash.setProgressBar(23)

    splash.setLabel('Loading pandas')
    import pandas
    splash.setProgressBar(32)

    splash.setLabel('Loading QcoDeS')
    import qcodes
    splash.setProgressBar(41)

    splash.setLabel('Loading WidgetPlot1d')
    from .ui.plot.plot1d.widgetPlot1d import WidgetPlot1d
    splash.setProgressBar(50)

    splash.setLabel('Loading WidgetPlot2d')
    from .ui.plot.plot2d.widgetPlot2d import WidgetPlot2d
    splash.setProgressBar(59)

    splash.setLabel('Loading WidgetCSV')
    from .ui.widgetCSV import WidgetCSV
    splash.setProgressBar(68)

    splash.setLabel('Loading WidgetNpz')
    from .ui.widgetNpz import WidgetNpz
    splash.setProgressBar(77)

    splash.setLabel('Loading WidgetBlueFors')
    from .ui.widgetBlueFors import WidgetBlueFors
    splash.setProgressBar(86)

    splash.setLabel('Loading browser')
    from .ui.mainWindow import MainApp
    splash.setProgressBar(95)


    splash.setLabel('Loading icon')
    from PyQt5.QtGui import QIcon
    app_icon = QIcon()
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'pictures', 'icon.png')
    app_icon.addFile(icon_path)
    app.setWindowIcon(app_icon)

    splash.setLabel('Applying style')
    if config['style']!='white':
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    main_app = MainApp(app)
    main_app.show()
    splash.finish(main_app)

    return app.exec_()


if __name__=='__main__':
    main()
