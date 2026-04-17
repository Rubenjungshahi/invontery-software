from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app import database as db
from app.login_dialog import LoginDialog
from app.main_window import MainWindow


def main() -> None:
    db.init_db()

    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)

    user = login.user()
    win = MainWindow(user)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

