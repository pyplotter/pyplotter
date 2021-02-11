# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
import sys


from .sources.main import MainApp
from .sources.config import config

def main():
    
    app = QtWidgets.QApplication(sys.argv)
    
    if config['style']!='white':
        
        import qdarkstyle
        
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    main_app = MainApp()
    main_app.show()
    app.exec_()


if __name__=='__main__':
    main()
