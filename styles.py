"""Client-friendly colors and Qt stylesheets."""

# Palette (clean office look)
SIDEBAR_BG = "#eef2ff"        # soft indigo
SIDEBAR_HOVER = "#e0e7ff"
SIDEBAR_SELECTED_BG = "#dbeafe"  # light blue selection

CONTENT_BG = "#f8fafc"       # very light gray-blue content area
CARD_BG = "#ffffff"          # panels/cards white

ACCENT = "#2563eb"          # office blue
ACCENT_DARK = "#1d4ed8"
ACCENT_TEXT = "#ffffff"

TEXT = "#0f172a"            # very dark slate
MUTED = "#475569"           # muted gray text
BORDER = "#cbd5e1"         # light border
HEADER_BG = "#e6f0ff"      # table header
HOVER_BG = "#f1f5f9"       # generic hover


def app_stylesheet() -> str:
    return f"""
    /* Global */
    QWidget {{
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
        color: {TEXT};
    }}

    /* Main background */
    QMainWindow, QWidget#contentRoot {{
        background-color: {CONTENT_BG};
    }}

    /* Sidebar */
    QListWidget#sidebar {{
        background-color: {SIDEBAR_BG};
        border: none;
        padding: 8px 0;
    }}
    QListWidget#sidebar::item {{
        padding: 12px 16px;
        border-left: 4px solid transparent;
        color: {TEXT};
    }}
    QListWidget#sidebar::item:hover {{
        background-color: {SIDEBAR_HOVER};
    }}
    QListWidget#sidebar::item:selected {{
        background-color: {SIDEBAR_SELECTED_BG};
        border-left: 4px solid {ACCENT};
        color: {TEXT};
    }}

    /* Titles / headings */
    QLabel#title {{
        font-size: 20px;
        font-weight: 700;
        color: {TEXT};
    }}

    /* Panels */
    QGroupBox {{
        font-weight: 700;
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 12px;
        background-color: {CARD_BG};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {TEXT};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {ACCENT};
        color: {ACCENT_TEXT};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_DARK};
    }}
    QPushButton:pressed {{
        background-color: #163a86;
    }}
    QPushButton#secondary {{
        background-color: #64748b;
    }}
    QPushButton#secondary:hover {{
        background-color: #556273;
    }}
    QPushButton#danger {{
        background-color: #ef4444;
    }}
    QPushButton#danger:hover {{
        background-color: #dc2626;
    }}

    /* Inputs */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 8px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
        border: 1px solid {ACCENT};
    }}

    /* Tables */
    QTableWidget {{
        background-color: {CARD_BG};
        gridline-color: #dbe4f0;
        border: 1px solid {BORDER};
        border-radius: 8px;
        color: {TEXT};
    }}
    QHeaderView::section {{
        background-color: {HEADER_BG};
        padding: 6px;
        border: none;
        font-weight: 800;
        color: {TEXT};
    }}
    QTableWidget::item {{
        color: {TEXT};
    }}
    QTableWidget::item:selected {{
        background-color: {HOVER_BG};
        color: {TEXT};
    }}
    """
