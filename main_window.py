from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import database as db
from app.pages.products_page import ProductsPage
from app.pages.services_page import ServicesPage
from app.pages.sales_page import SalesPage
from app.pages.purchase_page import PurchasePage
from app.pages.stock_page import StockPage
from app.styles import app_stylesheet


class MainWindow(QMainWindow):
    def __init__(self, user: dict) -> None:
        super().__init__()
        self._user = user
        self.setWindowTitle("Inventory Management")
        self.resize(1100, 700)

        root = QWidget()
        root.setObjectName("contentRoot")
        self.setCentralWidget(root)

        # Sidebar menu
        self._sidebar = QListWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(210)
        for text in [
            "Dashboard",
            "Products",
            "Services",
            "Sales",
            "Purchase",
            "Stock update",
            "Reports",
            "Activity log",
        ]:
            QListWidgetItem(text, self._sidebar)
        self._sidebar.currentRowChanged.connect(self._on_menu_changed)

        # Stacked pages
        self._stack = QStackedWidget()

        # 0 Dashboard
        dash = QWidget()
        v = QVBoxLayout(dash)
        title = QLabel("Dashboard")
        title.setObjectName("title")
        hello = QLabel(f"Welcome, {user.get('full_name') or user['username']}")
        hello.setStyleSheet("color: #64748b;")
        v.addWidget(title)
        v.addWidget(hello)
        v.addStretch()
        self._stack.addWidget(dash)

        # 1 Products
        self._stack.addWidget(ProductsPage(user))

        # 2 Services
        self._stack.addWidget(ServicesPage(user))

        # 3 Sales
        self._stack.addWidget(SalesPage(user))

        # 4 Purchase
        self._stack.addWidget(PurchasePage(user))

        # 5 Stock update
        self._stack.addWidget(StockPage(user))

        # 6 Reports
        self._stack.addWidget(self._reports_page())

        # 7 Activity log
        self._stack.addWidget(self._activity_page())

        layout = QVBoxLayout()
        # simple manual split: sidebar + stack
        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        # Use a simple nested widget to keep QVBoxLayout; in PyQt6 a QHBoxLayout could be used,
        # but keeping it minimal here.
        from PyQt6.QtWidgets import QHBoxLayout

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._sidebar)
        h.addWidget(self._stack, 1)
        row_layout.addLayout(h)
        layout.addWidget(row)

        root.setLayout(layout)

        self.setStyleSheet(app_stylesheet())
        self._sidebar.setCurrentRow(0)

    def _placeholder(self, text: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        title = QLabel(text)
        title.setObjectName("title")
        v.addWidget(title)
        v.addStretch()
        return w

    def _reports_page(self) -> QWidget:
        data = db.report_summary()
        w = QWidget()
        v = QVBoxLayout(w)
        title = QLabel("Reports")
        title.setObjectName("title")
        v.addWidget(title)
        v.addSpacing(10)

        def line(label: str, value: str) -> QLabel:
            lbl = QLabel(f"{label}: {value}")
            lbl.setStyleSheet("font-size: 14px;")
            return lbl

        v.addWidget(line("Total products", str(data["product_count"])))
        v.addWidget(line("Inventory value", f"{data['inventory_value']:.2f}"))
        v.addWidget(line("Total services", str(data["service_count"])))
        v.addWidget(line("Sales count", str(data["sale_count"])))
        v.addWidget(line("Sales total", f"{data['sales_total']:.2f}"))
        v.addWidget(line("Purchase count", str(data["purchase_count"])))
        v.addWidget(line("Purchase total", f"{data['purchases_total']:.2f}"))
        v.addStretch()
        return w

    def _activity_page(self) -> QWidget:
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

        rows = db.list_activity_log(limit=300)
        w = QWidget()
        v = QVBoxLayout(w)
        title = QLabel("Activity log")
        title.setObjectName("title")
        v.addWidget(title)

        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(
            ["Time", "User", "Action", "Detail", "ID"]
        )
        table.setSelectionMode(table.SelectionMode.NoSelection)
        table.horizontalHeader().setStretchLastSection(True)
        for r0, row in enumerate(rows):
            table.insertRow(r0)
            vals = [
                row["ts"],
                row["username"] or "",
                row["action"],
                (row["detail"] or "")[:120],
                row["id"],
            ]
            for c, value in enumerate(vals):
                it = QTableWidgetItem(str(value))
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r0, c, it)
        v.addWidget(table)
        return w

    def _on_menu_changed(self, index: int) -> None:
        if index < 0:
            return
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

