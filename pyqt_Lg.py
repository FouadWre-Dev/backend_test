

from PyQt5.QtWidgets import (
    QApplication,QPushButton,QVBoxLayout,QHBoxLayout,
    QLabel,QLineEdit,QTextEdit,QWidget
                             )
from PyQt5.QtCore import Qt,QThread,pyqtSignal
import os,sys,requests


user_id = "azerty123456"
webhock = "https://backend-test-03e7.onrender.com" #"http://127.0.0.1:8000"






class APIClient:

    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()

        self.access_token: str | None = None
        self.refresh_token: str | None = None

    def login(self, username: str, password: str) -> dict:

        response = self.session.post(
            f"{self.base_url}/api/v1/login/{user_id}",
            data={
                "username": username,
                "password": password,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        if not access_token or not refresh_token:
            raise RuntimeError("Invalid login response.")

        self.access_token = access_token
        self.refresh_token = refresh_token

        return data

    def refresh_access_token(self) -> dict:

        if not self.refresh_token:
            raise RuntimeError("No refresh token available.")

        response = self.session.post(
            f"{self.base_url}/refresh",
            params={
                "refresh_token": self.refresh_token,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            self.clear_tokens()

            raise RuntimeError(
                "Refresh token expired. Login again."
            )

        data = response.json()

        new_access_token = data.get("access_token")

        if not new_access_token:
            self.clear_tokens()

            raise RuntimeError(
                "Server returned an invalid access token."
            )

        self.access_token = new_access_token

        return data

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        retry_on_401: bool = True,
        **kwargs,
    ) -> requests.Response:

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = kwargs.pop("headers", {}).copy()

        if self.access_token:
            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )

        # --------------------------------------------------
        # ACCESS TOKEN EXPIRED
        # --------------------------------------------------

        if (
            response.status_code == 401
            and retry_on_401
            and self.refresh_token
        ):

            self.refresh_access_token()

            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

            # Prevent infinite refresh loop.
            return self.request(
                method,
                endpoint,
                retry_on_401=False,
                headers=headers,
                **kwargs,
            )

        return response

    def clear_tokens(self):

        self.access_token = None
        self.refresh_token = None

    def logout(self):

        self.clear_tokens()
        self.session.cookies.clear()

class ApiThread(QThread):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(
        self,
        function,
        *args,
        **kwargs,
    ):
        super().__init__()

        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):

        try:
            result = self.function(
                *self.args,
                **self.kwargs,
            )

            self.finished.emit(result)

        except Exception as exc:
            self.error.emit(exc)


apiRequest = APIClient(webhock)






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

        self.Tsold = ApiThread(
            apiRequest.request,
            "GET",
            "/api/v1/sold",
        )
        self.Tsold.finished.connect(self.profile_received)
        self.Tsold.error.connect(self.labelstatus.setText)
        self.Tsold.start()

    def profile_received(self,response):
        pass




class passwordwindow(QWidget):
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

        self.thread_login = ApiThread(
            apiRequest.login,
            self.username,
            self.password,
        )
        self.thread_login.finished.connect(self.login_finished)
        self.thread_login.error.connect(self.labelstatus.setText)
        self.thread_login.start()

    def login_finished(self,result):

        self.close()
        self.mwindow = mainwindow()
        self.mwindow.show()














if __name__ == "__main__":
    app = QApplication(sys.argv)

    w= passwordwindow()
    w.show()

    app.exec_()
