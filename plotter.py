# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
import sys

import qdarkstyle

# from sources.login_app import LoginApp
from sources.main import MainApp

def main():
    
    app = QtWidgets.QApplication(sys.argv)
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
