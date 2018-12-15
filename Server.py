import socket
import threading
import queue
import random
import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class TCPServer():
    Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Host = socket.gethostname()
    Server_Address = ''
    Connections = []
    Client_Data = []
    RandomNum = -1

    def __init__(self, Port, RandomNum):
        try:
            self.Server_Address = ('161.31.72.232', Port)
            self.RandomNum = RandomNum
            self.Socket.bind(self.Server_Address)
            self.Socket.listen(2)
        except Exception as e:
            print(e)
            sys.exit()

    def GetConnections(self):
        Connection, Client_Address = self.Socket.accept()
        self.Connections.append(Connection)

    def HandleIncomingClientData(self, Connection):
        Data = json.loads(Connection.recv(1024).decode())
        if Data:
            self.Client_Data.append(Data)

    def SendUpdate(self, Index, Data):
        if isinstance(Data, str):
            toSend = json.dumps({'a':Data})
            self.Connections[Index].sendall(toSend.encode())
        else:
            toSend = json.dumps({"a":Data[0], "b":Data[1]})
            self.Connections[Index].sendall(toSend.encode())

    def DetermineIfWinner(self):
        toReturn = []
        for y in range(0,len(self.Client_Data)):
            if int(self.Client_Data[y].get("a")) > self.RandomNum:
                toReturn.append([False, int(self.Client_Data[y].get("b")), int(self.Client_Data[y].get("a"))])
            elif int(self.Client_Data[y].get("a")) < self.RandomNum:
                toReturn.append([False, int(self.Client_Data[y].get("a")), int(self.Client_Data[y].get("c"))])
            else:
                toReturn.append([True])
        return toReturn

    def SendDeclerationOfWinnerToAll(self, Winner):
        for x in range(0,len(self.Connections)):
            if x == Winner:
                toSend = json.dumps({"a":"Winner"})
                self.Connections[x].sendall(toSend.encode())
            elif not x == Winner:
                toSend = json.dumps({"a":"Loser"})
                self.Connections[x].sendall(toSend.encode())

class ServerGUI(QWidget):
    isServerRunning = False

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.ServerStatus = QLabel(self)
        self.ServerStatus.setText('Server Status: ')
        self.ServerStatus.move(120,15)
        self.ServerColor = QLabel(self)
        self.ServerColor.setText('Offline')
        self.ServerColor.move(200,15)
        self.ServerColor.setStyleSheet('color: red')

        self.NumStatus = QLabel(self)
        self.NumStatus.setText('Number Generated: ')
        self.NumStatus.move(120,40)
        self.Number = QLabel(self)
        self.Number.setText('N/A')
        self.Number.move(225,40)

        self.NumberText2 = QLabel(self)
        self.NumberText2.setText('Port Number:')
        self.NumberText2.move(90,75)
        self.LineEditPort = QLineEdit(self)
        self.LineEditPort.move(160, 72)

        self.ServerText = QLabel(self)
        self.ServerText.setText('Server Log')
        self.ServerText.move(158,110)

        self.LogEdit = QPlainTextEdit(self)
        self.LogEdit.setReadOnly(True)
        self.ScrollArea = QScrollArea(self)
        self.ScrollArea.setWidget(self.LogEdit)
        self.ScrollArea.move(60, 145)

        self.SubButton = QPushButton('Start Server', self)
        self.SubButton.setCheckable(True)
        self.SubButton.move(147, 360)
        self.SubButton.clicked.connect(self.isStartedPressed)

        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Server')
        self.resize(375,410)
        self.setFixedSize(375,410)
        self.show()

    def isStartedPressed(self):
        Port = self.LineEditPort.text()
        if not self.isServerRunning and (Port is not ""):
            self.ServerColor.setText('Online')
            self.ServerColor.setStyleSheet('color: green')
            self.isServerRunning = True
            self.randomNumber = random.randint(1,100)
            self.Number.setText(str(self.randomNumber))
            self.Server = TCPServer(int(Port), self.randomNumber)
            self.LogEdit.appendPlainText('Server Started on ' + self.Server.Host + ":" + Port)
            self.ServerThread = threading.Thread(target=self.StartAccepting)
            self.ServerThread.start()
        elif Port is "":
            self.LogEdit.appendPlainText('Port Missing!')
        elif self.isServerRunning:
            self.LogEdit.appendPlainText('Server is Running!')

    def StartAccepting(self):
        Decider = False
        DData = []
        for x in range(0, 2):
            CommThread = threading.Thread(target=self.Server.GetConnections)
            CommThread.start()
            CommThread.join()
        for x in range(0, len(self.Server.Connections)):
            self.Server.SendUpdate(x, "Ack")
        while not Decider:
            for x in range(0, len(self.Server.Connections)):
                ClientThread = threading.Thread(target=self.Server.HandleIncomingClientData, args=(self.Server.Connections[x],))
                ClientThread.start()
                ClientThread.join()
            DData = self.Server.DetermineIfWinner()
            Winners = -1
            for y in range(0, len(DData)):
                if DData[y][0] is True:
                    Decider = True
                    Winners = y
            for z in range(0, len(DData)):
                if DData[z][0] is False and Decider is False:
                    toPass = [DData[z][1], DData[z][2]]
                    self.Server.SendUpdate(z, toPass)
            self.Server.Client_Data.clear()
        self.Server.SendDeclerationOfWinnerToAll(Winners)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ServerGUI()
    sys.exit(app.exec_())
