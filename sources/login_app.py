# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
import os
import sys
from smb.SMBConnection import SMBConnection
import sys 
sys.path.append('ui')

import login
from config import config


class LoginApp(QtWidgets.QDialog, login.Ui_Dialog):

    def __init__(self, parent=None):
        """
        Handle the start of the app by asking username and password.
        If good ids are detected, launched the main app.
        """

        super(LoginApp, self).__init__(parent)
        self.setupUi(self)

        self.pushButtonLogin.clicked.connect(self.clickedLogin)

        # If we are in the test configuration
        if 'test' in os.listdir('.'):
            #  We disable all fields
            self.labelId.setDisabled(True)
            self.lineEditId.setDisabled(True)
            self.labelPwd.setDisabled(True)
            self.lineEditPwd.setDisabled(True)
            self.checkBoxCredentials.setDisabled(True)

            # We modify the default title to indicate the current mode
            self.checkBoxCredentials.parentWidget().setWindowTitle('Login - Test mode')
        
        # In "standard" mode
        else:
            # We check if the user decided to store his credentials
            if os.path.isfile('credentials'):
                f = open('credentials', 'r')
                i = f.readline().split(':')[1].strip()
                pwd = f.readline().split(':')[1].strip()
                self.lineEditId.setText(i)
                self.lineEditPwd.setText(pwd)
                self.checkBoxCredentials.setChecked(True)
                f.close()



    def clickedLogin(self):


        # If we are in the test configuration
        if 'test' in os.listdir('.'):
            
            self.conn = None
            self.accept()
        # In "standard" mode
        else:
            # create and establish connection
            self.conn = SMBConnection(self.lineEditId.text(),
                                    self.lineEditPwd.text(),
                                    config['local_machine_name'],
                                    config['server_machine_name'],
                                    use_ntlm_v2 = True)

            
            # Check ids by tempting a connection
            try:
                assert self.conn.connect(config['server_ip'], 139)
                self.conn.listPath(config['share_name'], os.path.join('shared', 'data_vault_server_file'))

                # If connection is accepted and user decided to store his credential
                if self.checkBoxCredentials.isChecked():
                    f = open('credentials', 'w')
                    f.write('id:'+self.lineEditId.text()+'\n')
                    f.write('pwd:'+self.lineEditPwd.text())
                    f.close()

                # If good ids we run this function which close the dialog
                self.accept()
            except:
                QtWidgets.QMessageBox.warning(
                    self, 'Error', 'Bad username or password')
