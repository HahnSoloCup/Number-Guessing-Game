import socket
import threading
import queue
import time
import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

Range = []
Range.append(1)
Range.append(100)

class HandleFromServer:
    Host = ""
    Port = -1
    Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Results = queue.Queue()

    def __init__(self, toIP, toPort):
        self.Host = toIP
        self.Port = toPort
        self.Socket.settimeout(1)

    def Connect(self):
        try:
            self.Socket.connect((self.Host, self.Port))
            return True
        except socket.timeout as e:
            print(e)

    def SendGuess(self, toServer):
        self.Socket.settimeout(1)
        try:
            toSend = json.dumps({"a":toServer, "b":Range[0], "c":Range[1]})
            self.Socket.sendall(toSend.encode())
        except socket.timeout as e:
            print(e)

    def WaitForResults(self):
        self.Socket.settimeout(None)
        toReturn = json.loads(self.Socket.recv(1024).decode())
        if toReturn:
            if toReturn.get("a") == 'Ack':
                pass
            if toReturn.get("a") == 'Winner' or toReturn.get("a") == 'Loser':
                self.Results.put(toReturn.get("a"))
            elif isinstance(toReturn.get("a"), int):
                self.Results.put(toReturn.get("a"))
                self.Results.put(toReturn.get("b"))
        else:
            pass

    def Close(self):
        self.Socket.close()

class GUIThread(QThread):
    update = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        self.update.emit()

class ClientGUI(QWidget):
    isSent = False

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.WelcomeText = QLabel(self)
        self.Picture = QPixmap('ClientGUI.png')
        self.WelcomeText.setPixmap(self.Picture)
        self.WelcomeText.move(82,35)
        self.StatusLabel1 = QLabel(self)
        self.StatusLabel1.setText('Status: ')
        self.StatusLabel1.move(150,75)
        self.StatusLabel2 = QLabel(self)
        self.StatusLabel2.setText('')
        self.StatusLabel2.move(190,75)

        #First Window
        self.SubButton1 = QPushButton('Connect', self)
        self.SubButton1.setCheckable(True)
        self.SubButton1.move(120, 150)
        self.SubButton1.clicked.connect(self.isConnectPressed)

        #Second Window
        self.NumberText3 = QLabel(self)
        self.NumberText3.setText('Guess a Number ' + '(' + str(Range[0])
                                 + '-' + str(Range[1]) + ')')
        self.NumberText3.move(75,108)
        self.NumberText3.hide()
        self.LineEdit3 = QLineEdit(self)
        self.LineEdit3.move(200, 105)
        self.LineEdit3.hide()
        self.SubButton2 = QPushButton('Submit Number', self)
        self.SubButton2.setCheckable(True)
        self.SubButton2.move(120, 150)
        self.SubButton2.clicked.connect(self.isNumberPressed)
        self.SubButton2.hide()

        self.ExitButton = QPushButton('Exit Game', self)
        self.ExitButton.setCheckable(True)
        self.ExitButton.move(210, 150)
        self.ExitButton.clicked.connect(self.CloseApp)

        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Client')
        self.resize(400, 200)
        self.setFixedSize(400,200)
        self.show()

    def isConnectPressed(self):
        self.Client = HandleFromServer('161.31.72.100', 8300) #Change this line to change host computer
        self.fromServer = self.Client.Connect()
        if self.fromServer:
            self.StatusLabel2.setText('Connected!')
            self.StatusLabel2.adjustSize()
            self.StatusLabel2.setStyleSheet('color: green')
            self.SubButton1.hide()
            self.DataThread = GUIThread()
            self.DataThread.update.connect(self.Waiting)
            self.DataThread.start()
        else:
            self.StatusLabel2.setText('Timed Out!')
            self.StatusLabel2.adjustSize()
            self.StatusLabel2.setStyleSheet('color: red')

    def isNumberPressed(self):
        if not self.isSent:
            toServer = self.LineEdit3.text()
            try:
                int(toServer)
            except ValueError:
                self.StatusLabel2.setText('Not a Number!')
                self.StatusLabel2.adjustSize()
                self.StatusLabel2.setStyleSheet('color: red')
            else:
                if int(toServer) > Range[1] or int(toServer) < Range[0]:
                    self.StatusLabel2.setText('Not in Range!')
                    self.StatusLabel2.adjustSize()
                    self.StatusLabel2.setStyleSheet('color: red')
                else:
                    self.isSent = True
                    self.Client.SendGuess(toServer)
                    self.StatusLabel2.setText('Waiting...')
                    self.StatusLabel2.adjustSize()
                    self.StatusLabel2.setStyleSheet('color: black')
                    self.NumberText3.hide()
                    self.SubButton2.hide()
                    self.LineEdit3.hide()
                    self.DataThread = GUIThread()
                    self.DataThread.update.connect(self.Waiting)
                    self.DataThread.start()
        else:
            pass

    def Waiting(self):
        self.ResultThread = threading.Thread(target=self.Client.WaitForResults)
        self.ResultThread.start()
        self.ResultThread.join()
        if not self.Client.Results.empty():
            if self.Client.Results.qsize() == 1:
                self.ServerMessage = self.Client.Results.get_nowait()
            elif self.Client.Results.qsize() == 2:
                self.ServerMessage = self.Client.Results.get_nowait()
                self.ServerMessage2 = self.Client.Results.get_nowait()

            if self.ServerMessage == 'Winner' or self.ServerMessage == 'Loser':
                self.ShowResults()
            else:
                self.StatusLabel2.setText("Guess Again!")
                self.StatusLabel2.adjustSize()
                self.StatusLabel2.setStyleSheet('color: black')
                Range[0] = self.ServerMessage
                Range[1] = self.ServerMessage2
                self.NumberText3.setText('Guess a Number ' + '(' + str(Range[0])
                                         + '-' + str(Range[1]) + ')')
                self.NumberText3.adjustSize()
                self.NumberText3.show()
                self.SubButton2.show()
                self.LineEdit3.show()
                self.isSent = False
        else:
            self.NumberText3.show()
            self.LineEdit3.show()
            self.SubButton2.show()

    def ShowResults(self):
        if self.ServerMessage == 'Winner':
            self.StatusLabel2.setText("You Win!")
            self.StatusLabel2.adjustSize()
            self.StatusLabel2.setStyleSheet('color: green')
            self.NumberText3.hide()
            self.SubButton2.hide()
            self.LineEdit3.hide()
        elif self.ServerMessage == 'Loser':
            self.StatusLabel2.setText("You Lost!")
            self.StatusLabel2.adjustSize()
            self.StatusLabel2.setStyleSheet('color: red')
            self.NumberText3.hide()
            self.SubButton2.hide()
            self.LineEdit3.hide()
        else:
            self.StatusLabel2.setText("Server Error!")
            self.StatusLabel2.adjustSize()
            self.StatusLabel2.setStyleSheet('color: red')
            self.NumberText3.hide()
            self.SubButton2.hide()
            self.LineEdit3.hide()
        self.Client.Close()

    def CloseApp(self):
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ClientGUI()
    sys.exit(app.exec_())
