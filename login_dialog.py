"""Login dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from app import database as db
from app.styles import ACCENT, CONTENT_BG


class LoginDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Inventory — Sign in")
        self.setModal(True)
        self.resize(400, 260)
        self._user: dict | None = None

        self.setStyleSheet(
            f"""
            QDialog {{ background-color: {CONTENT_BG}; }}
            QLabel#head {{ font-size: 18px; font-weight: 700; color: #1e293b; }}
            QLineEdit {{ min-height: 28px; }}
            """
        )

        head = QLabel("Inventory Management")
        head.setObjectName("head")
        sub = QLabel("Sign in with your account")
        sub.setStyleSheet("color: #64748b;")

        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("Username")
        self._user_edit.setText(db.DEFAULT_USERNAME)

        self._pass_edit = QLineEdit()
        self._pass_edit.setPlaceholderText("Password")
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_edit.setText(db.DEFAULT_PASSWORD)

        form = QFormLayout()
        form.addRow("Username", self._user_edit)
        form.addRow("Password", self._pass_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._try_login)
        buttons.rejected.connect(self.reject)
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText("Sign in")
            ok_btn.setStyleSheet(
                f"background-color: {ACCENT}; color: white; padding: 8px 20px; "
                "border-radius: 4px; font-weight: 600;"
            )

        layout = QVBoxLayout(self)
        layout.addWidget(head)
        layout.addWidget(sub)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(buttons)

    def user(self) -> dict:
        assert self._user is not None
        return self._user

    def _try_login(self) -> None:
        u = db.verify_login(self._user_edit.text(), self._pass_edit.text())
        if u is None:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Login failed", "Invalid username or password.")
            return
        self._user = u
        db.log_action(u["id"], u["username"], "Login", "User signed in")
        self.accept()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._try_login()
        else:
            super().keyPressEvent(event)
