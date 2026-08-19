

from PyQt5.QtWidgets import (
    QApplication,QPushButton,QVBoxLayout,QHBoxLayout,
    QLabel,QLineEdit,QTextEdit,QWidget
                             )
from PyQt5.QtCore import Qt,QThread,pyqtSignal
import os,sys,requests


user_id = "azerty123456"

class generalInfo:
    def __init__(self):
        self.accesstoken = None


generalInfoManager = generalInfo()


class mainwindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DashBoad Main")
        self.resize(600,600)

        mainlayout = QVBoxLayout(self) ; mainlayout.setAlignment(Qt.AlignCenter)

        btn_1 = QPushButton("Get Sold")
        self.labelstatus = QLabel("status")

        mainlayout.addWidget(btn_1)
        mainlayout.addWidget(self.labelstatus)

        btn_1.clicked.connect(self.get_sold)

    def get_sold(self):
        self.Tsold = thread_sold()
        self.Tsold.status.connect(self.labelstatus.setText)
        self.Tsold.start()




class mainPassKey(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("test my server")
        self.resize(300,200)

        mainlayout = QVBoxLayout(self);mainlayout.setAlignment(Qt.AlignVCenter)

        btn_1 = QPushButton("LOGIN")
        self.text1 = QLineEdit();self.text1.setPlaceholderText("username")
        self.text2 = QLineEdit();self.text2.setPlaceholderText("password")
        self.labelstatus = QLabel("status ...")

        mainlayout.addStretch()
        mainlayout.addWidget(self.text1)
        mainlayout.addWidget(self.text2)
        mainlayout.addWidget(btn_1,alignment=Qt.AlignLeft)
        mainlayout.addStretch()
        mainlayout.addWidget(self.labelstatus,alignment=Qt.AlignCenter)

        btn_1.clicked.connect(self.Set_to_login)


    def Set_to_login(self):
        self.username = self.text1.text()
        self.password = self.text2.text()

        if not self.username : self.text1.setFocus();return
        if not self.password : self.text2.setFocus();return

        self.thread_login = threadlogin(
            self.username,
            self.password
        )
        self.thread_login.status.connect(self.labelstatus.setText)
        self.thread_login.accessToken.connect(self.set_access)
        self.thread_login.start()

    def set_access(self,accesstoken):
        generalInfoManager.accesstoken = accesstoken

        self.close()
        self.mwindow = mainwindow()
        self.mwindow.show()





class threadlogin(QThread):
    status = pyqtSignal(str)
    accessToken = pyqtSignal(str)
    def __init__(self,username:str ,password:str):
        super().__init__()

        self.username = username
        self.password = password

    def run(self):
        self.status.emit("Loading ...")
        self.msleep(300)
        try:
            rs = requests.post(f"http://127.0.0.1:8000/api/v1/login/{user_id}",
                            data={
                                "username" : self.username,
                                "password" : self.password,
                            },
                            timeout=4
                            )
            response = rs.json()

            _status = response.get("status")
            if _status:
                accesstoken = response.get("accesstoken")
                self.accessToken.emit(accesstoken)

            self.status.emit(response.get("text"))


        except Exception as e:
            self.status.emit(f"{e}")



class thread_sold(QThread):
    status = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.token = generalInfoManager.accesstoken

    def run(self):
        self.status.emit("Loading ...")
        self.msleep(150)
        try:
            rs = requests.get(f"http://127.0.0.1:8000/api/v1/sold",
                            headers={
                                "Authorization" : f"Bearer {self.token}",
                            },
                            timeout=4
                            )
            response = rs.json()

            _status = response.get("status")
            if _status:
                sold = response.get("sold")
                self.status.emit(f"u have : {sold} Credit")
                return

            self.status.emit(response.get("text"))


        except Exception as e:
            self.status.emit(f"{e}")





if __name__ == "__main__":
    app = QApplication(sys.argv)

    w= mainPassKey()
    w.show()

    app.exec_()
