# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
import sys


from sources.main import MainApp
from sources.config import config

def main():
    
    app = QtWidgets.QApplication(sys.argv)
    
    if config['style']=='qdarkstyle':
        
        import qdarkstyle
        
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    # First we launch the login app to ask ids
    # login = LoginApp()
    # if login.exec_() == QtWidgets.QDialog.Accepted:
    # We open the main app with the open connection object
    main_app = MainApp()
    main_app.show()
    app.exec_()


if __name__ == '__main__':
    main()
