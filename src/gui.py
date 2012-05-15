import sys
import re
import os.path
import ConfigParser

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, SLOT, Qt

from sipgate import *

CONFIG_FILE = "~/.pysipgate"

def errorbox(fun):
    def decorated(*args, **kargs):
        try:
            fun(*args, **kargs)
        except SipgateException as err:
            msg = "The error '%s' occured." % str(err)
            QtGui.QMessageBox.critical(None, "Error", msg)

    return decorated

class EndpointSelection(QtGui.QComboBox):

    def __init__(self, endpoints, parent=None):
        self.endpoints = endpoints

        QtGui.QComboBox.__init__(self, parent)

        for index, endpoint in enumerate(endpoints):
            self.addItem(endpoint.name())

            if endpoint.default:
                self.setCurrentIndex(index)

    def currentEndpoint(self):
        return self.endpoints[self.currentIndex()]

class CallWidget(QtGui.QWidget):

    def __init__(self, con, parent=None):
        self.con = con

        QtGui.QWidget.__init__(self, parent)

        self.setWindowFlags(Qt.Dialog)
        self.resize(250, 60)

        layout = QtGui.QGridLayout(self)

        self.number = number = QtGui.QLineEdit(self)
        layout.addWidget(number, 0, 0, 1, 2)

        self.endpoint = endpoint = EndpointSelection(con.voice_endpoints(), self)
        layout.addWidget(endpoint, 1, 0)

        button = QtGui.QPushButton("Call", self)
        layout.addWidget(button, 1, 1)

        self.connect(button, SIGNAL('clicked()'), self.call)
        self.connect(number, SIGNAL('returnPressed()'), self.call)

    def showEvent(self, event):
        clipped = QtGui.QApplication.clipboard().text()

        if re.match('[\d\s\-+]+$', clipped):
            self.number.setText(clipped)
        else:
            self.number.setText('')

        self.number.setFocus(Qt.ActiveWindowFocusReason)

    @errorbox
    def call(self):
        endpoint = self.endpoint.currentEndpoint()
        number = self.number.text()

        self.hide()

        endpoint.voice(str(number))

class Tray(QtGui.QSystemTrayIcon):

    def __init__(self, con, parent=None):
        self.con = con
        self.parent = parent

        icon = QtGui.QIcon("img/phone_icon.png")

        self.call = call = CallWidget(con)

        QtGui.QSystemTrayIcon.__init__(self, icon, parent)

        self.menu = menu = QtGui.QMenu()

        callAction = menu.addAction("Call")
        self.connect(callAction, SIGNAL('triggered()'), call.show)

        balanceAction = menu.addAction("Balance")
        self.connect(balanceAction, SIGNAL('triggered()'), self.balance)

        menu.addSeparator()

        exitAction = menu.addAction("Exit")
        self.connect(exitAction, SIGNAL('triggered()'), QtGui.QApplication.quit)

        self.setContextMenu(menu)

    @errorbox
    def balance(self):
        balance, unit = self.con.balance()
        msg = "Your account balance is {balance} {unit}".format(balance=balance, unit=unit)
        QtGui.QMessageBox.information(None, "Balance", msg)

def main():
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = ConfigParser.ConfigParser()
    config.read(os.path.expanduser(CONFIG_FILE))

    user = config.get('account', 'user')
    password = config.get('account', 'password')

    try:
        con = SipgateConnection(user, password)
    except SipgateAuthException:
        msg = "Could not authenticate with Sipgate server. Please adjust your account settings in '%s'" % CONFIG_FILE
        QtGui.QMessageBox.critical(None, "Authentication Error", msg)
        return 1
    except SipgateException as err:
        QtGui.QMessageBox.critical(None, "Error", str(err))
        return 1
    else:
        tray = Tray(con)
        tray.show()

        return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
