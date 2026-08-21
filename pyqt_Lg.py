from dataclasses import dataclass
from typing import Any

import requests

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import sys


USER_ID = "azerty123456"
BASE_URL = "https://backend-test-03e7.onrender.com"
# BASE_URL = "http://127.0.0.1:8000"


@dataclass
class APIResult:
    success: bool
    status: str
    data: Any = None
    status_code: int | None = None
    message: str | None = None


class APIClient:

    def __init__(
        self,
        base_url: str,
        user_id: str,
        timeout: int = 15,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.timeout = timeout

        self.session = requests.Session()

        self.access_token: str | None = None
        self.refresh_token: str | None = None
        
    @staticmethod
    def _json_response(response: requests.Response) -> dict:

        try:
            data = response.json()

            if isinstance(data, dict):
                return data

            return {
                "data": data
            }

        except ValueError:

            return {
                "status": "invalid_server_response",
                "message": response.text,
            }

    def login(
        self,
        username: str,
        password: str,
    ) -> APIResult:

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/login/{self.user_id}",
                data={
                    "username": username,
                    "password": password,
                },
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            return APIResult(
                success=False,
                status="network_error",
                message=str(exc),
            )

        data = self._json_response(response)

        # AUTHENTICATION FAILED

        if response.status_code == 401:

            self.clear_tokens()

            return APIResult(
                success=False,
                status="login_failed",
                message=data.get(
                    "text",
                    "username or password is invalid",
                ),
                status_code=401,
                data=data,
            )

        # OTHER HTTP ERRORS

        if not response.ok:

            return APIResult(
                success=False,
                status="server_error",
                status_code=response.status_code,
                data=data,
                message=data.get("detail"),
            )

        # VALIDATE RESPONSE

        access_token = data.get("access_token")

        if not access_token:

            return APIResult(
                success=False,
                status="invalid_login_response",
                data=data,
                message="Server did not return access_token.",
            )

        # SAVE TOKENS

        self.access_token = access_token
        self.refresh_token = data.get("refresh_token")

        return APIResult(
            success=True,
            status="login_success",
            message=data.get("text"),
            data=data,
            status_code=response.status_code,
        )
        
    def refresh_access_token(self) -> APIResult:

        if not self.refresh_token:

            return APIResult(
                success=False,
                status="no_refresh_token",
            )

        try:
            response = self.session.post(
                f"{self.base_url}/refresh",
                params={
                    "refresh_token": self.refresh_token,
                },
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            return APIResult(
                success=False,
                status="network_error",
                message=str(exc),
            )

        data = self._json_response(response)

        if response.status_code != 200:

            self.clear_tokens()

            return APIResult(
                success=False,
                status=data.get(
                    "status",
                    "refresh_token_expired",
                ),
                status_code=response.status_code,
                data=data,
                message=data.get("detail"),
            )

        new_access_token = data.get("access_token")

        if not new_access_token:

            self.clear_tokens()

            return APIResult(
                success=False,
                status="invalid_refresh_response",
                data=data,
            )

        self.access_token = new_access_token

        return APIResult(
            success=True,
            status="token_refreshed",
            data=data,
            status_code=response.status_code,
        )
    
    def request(
        self,
        method: str,
        endpoint: str,
        *,
        retry_on_401: bool = True,
        **kwargs,
    ) -> APIResult:

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = kwargs.pop("headers", {}).copy()

        if self.access_token:
            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )

        except requests.RequestException as exc:

            return APIResult(
                success=False,
                status="network_error",
                message=str(exc),
            )

        data = self._json_response(response)

        # TOKEN EXPIRED

        if (
            response.status_code == 401
            and retry_on_401
            and self.refresh_token
        ):

            refresh_result = self.refresh_access_token()

            if not refresh_result.success:
                return refresh_result

            # Update token
            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

            # Retry ONLY once
            return self.request(
                method,
                endpoint,
                retry_on_401=False,
                headers=headers,
                **kwargs,
            )

        # HTTP ERROR

        if not response.ok:

            return APIResult(
                success=False,
                status=data.get(
                    "status",
                    "request_failed",
                ),
                status_code=response.status_code,
                data=data,
                message=data.get("detail"),
            )

        # SUCCESS

        return APIResult(
            success=True,
            status="request_success",
            status_code=response.status_code,
            data=data,
        )

    def clear_tokens(self):
        self.access_token = None
        self.refresh_token = None

    def logout(self):
        self.clear_tokens()
        self.session.cookies.clear()


class ApiThread(QThread):

    status = pyqtSignal(str)
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

        self.status.emit("Running...")

        try:

            result = self.function(
                *self.args,
                **self.kwargs,
            )

            self.finished.emit(result)

        except Exception as exc:

            self.error.emit(exc)



apiRequest = APIClient(BASE_URL,USER_ID)


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dashboard")
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.btn_sold = QPushButton("Get Sold")
        self.label_status = QLabel("Ready")

        layout.addWidget(self.btn_sold)
        layout.addWidget(self.label_status)

        self.btn_sold.clicked.connect(self.get_sold)

    # GET SOLD
    
    def get_sold(self):

        self.btn_sold.setEnabled(False)

        self.thread_sold = ApiThread(
            apiRequest.request,
            "GET",
            "/api/v1/sold",
        )

        self.thread_sold.status.connect(self.label_status.setText)
        self.thread_sold.finished.connect(self.profile_received)
        self.thread_sold.error.connect(self.request_error)
        self.thread_sold.start()

    # RESPONSE
    
    def profile_received(
        self,
        result: APIResult,
    ):

        self.btn_sold.setEnabled(True)

        if not result.success:

            self.label_status.setText(
                result.message
                or result.status
            )

            return

        data = result.data

        sold = data.get("sold")

        if sold is not None:

            self.label_status.setText(
                f"You have: {sold} Credit"
            )

        else:

            self.label_status.setText(
                data.get(
                    "text",
                    result.status,
                )
            )

    # ERROR
    
    def request_error(self,error: Exception):
        self.btn_sold.setEnabled(True)
        self.label_status.setText(str(error))


class PasswordWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.resize(350, 220)

        layout = QVBoxLayout(self)

        self.text_username = QLineEdit()
        self.text_username.setPlaceholderText(
            "Username"
        )

        self.text_password = QLineEdit()
        self.text_password.setPlaceholderText("Password")

        self.text_password.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton("LOGIN")

        self.label_status = QLabel("Please login...")

        layout.addWidget(self.text_username)
        layout.addWidget(self.text_password)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.label_status)

        self.btn_login.clicked.connect(self.start_login)

    def start_login(self):

        username = self.text_username.text().strip()
        password = self.text_password.text()

        if not username:

            self.text_username.setFocus()
            return

        if not password:

            self.text_password.setFocus()
            return

        self.btn_login.setEnabled(False)
        self.label_status.setText("Logging in...")

        self.thread_login = ApiThread(
            apiRequest.login,
            username,
            password,
        )

        self.thread_login.status.connect(self.label_status.setText)
        self.thread_login.finished.connect(self.login_finished)
        self.thread_login.error.connect(self.login_error)
        self.thread_login.start()

    def login_finished(self, result: APIResult):
        if not result.success:
            self.btn_login.setEnabled(True)
            self.label_status.setText(result.message or result.status)
            return

        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
    
    def login_error(
        self,
        error: Exception,
    ):

        self.btn_login.setEnabled(True)
        self.label_status.setText(str(error))



if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = PasswordWindow()
    window.show()

    sys.exit(
        app.exec_()
    )