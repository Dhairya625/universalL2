APP_STYLESHEET = """
QMainWindow, QWidget#Root, QWidget#Workspace {
    background: #101012;
    color: #E6E6E8;
}
QMenuBar {
    background: #161618;
    color: #A1A1AA;
    border-bottom: 1px solid #29292D;
    padding: 2px;
}
QMenuBar::item:selected, QMenu::item:selected { background: #2A2934; color: #FFFFFF; }
QMenu { background: #1C1C1F; color: #E6E6E8; border: 1px solid #343439; padding: 5px; }
QFrame#Sidebar { background: #171719; border-right: 1px solid #29292D; }
QLabel#Brand { color: #F4F4F5; font-size: 16px; font-weight: 700; padding: 5px 10px 0 10px; }
QLabel#BrandSub { color: #71717A; font-size: 10px; padding: 0 10px 8px 10px; }
QLabel#NavSection {
    color: #68686F; font-size: 10px; font-weight: 700;
    padding: 8px 10px 5px 10px; text-transform: uppercase;
}
QPushButton#NavButton {
    text-align: left; border: none; border-radius: 5px; padding: 7px 10px;
    color: #A1A1AA; background: transparent; font-size: 11px; font-weight: 500;
}
QPushButton#NavButton:hover { background: #202023; color: #E4E4E7; }
QPushButton#NavButton:checked { background: #2A2934; color: #F4F4F5; }
QFrame#Topbar { background: #161618; border-bottom: 1px solid #29292D; }
QLabel#Breadcrumb { color: #A1A1AA; font-size: 11px; font-weight: 600; }
QPushButton#CommandButton {
    color: #85858D; background: #202023; border: 1px solid #303035;
    border-radius: 5px; padding: 5px 10px; font-size: 10px; text-align: left;
}
QPushButton#CommandButton:hover { color: #E4E4E7; border-color: #48484F; }
QFrame#PrivacyCard { background: #1D1D20; border: 1px solid #29292D; border-radius: 6px; }
QLabel#PrivacyTitle { color: #86EFAC; font-size: 10px; font-weight: 600; }
QLabel#PrivacyBody { color: #71717A; font-size: 9px; }
QLabel#PageTitle { font-size: 21px; font-weight: 700; color: #F4F4F5; }
QLabel#PageSubtitle { font-size: 11px; color: #85858D; }
QFrame#Card { background: #18181B; border: 1px solid #29292D; border-radius: 7px; }
QLabel#CardLabel { color: #7B7B84; font-size: 9px; font-weight: 700; }
QLabel#MetricValue { color: #F4F4F5; font-size: 20px; font-weight: 700; }
QLabel#SectionTitle { color: #E4E4E7; font-size: 12px; font-weight: 650; }
QLabel#Muted { color: #85858D; font-size: 10px; }
QLabel#Notice {
    background: #1F1D2C; color: #B7A7FF; border: 1px solid #37314F;
    border-radius: 6px; padding: 8px 11px; font-size: 10px; font-weight: 600;
}
QPushButton#Primary {
    background: #5E5CE6; color: white; border: 1px solid #6F6DF2;
    border-radius: 5px; padding: 6px 11px; font-size: 10px; font-weight: 650;
}
QPushButton#Primary:hover { background: #6B69EA; }
QPushButton#Primary:disabled { background: #29292D; color: #62626A; border-color: #343439; }
QPushButton#Secondary {
    background: #202023; color: #B4B4BC; border: 1px solid #343439;
    border-radius: 5px; padding: 6px 10px; font-size: 10px; font-weight: 600;
}
QPushButton#Secondary:hover { background: #29292D; color: #F4F4F5; border-color: #48484F; }
QLineEdit, QComboBox {
    background: #1C1C1F; color: #E4E4E7; border: 1px solid #343439;
    border-radius: 5px; padding: 6px 8px; selection-background-color: #5E5CE6;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background: #202023; color: #E4E4E7; border: 1px solid #3F3F46; }
QListWidget, QTableWidget, QTextBrowser {
    background: #151517; color: #D4D4D8; border: 1px solid #29292D;
    border-radius: 6px; selection-background-color: #2C2940;
    selection-color: #F4F4F5; outline: none; gridline-color: #29292D;
}
QTextBrowser#DetailPanel { background: #18181B; border: none; border-radius: 4px; }
QListWidget::item { padding: 7px 9px; border-bottom: 1px solid #252528; }
QListWidget::item:hover { background: #1D1D20; }
QListWidget::item:selected { background: #292733; border-left: 2px solid #7C6EF6; }
QTableWidget::item { padding: 5px; border-bottom: 1px solid #252528; }
QTableWidget::item:hover { background: #1D1D20; }
QHeaderView::section {
    background: #18181B; color: #71717A; border: none;
    border-bottom: 1px solid #29292D; padding: 7px; font-size: 9px; font-weight: 700;
}
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical { background: #3A3A40; min-height: 26px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 9px; }
QScrollBar::handle:horizontal { background: #3A3A40; min-width: 26px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QProgressBar { border: none; background: #29292D; border-radius: 2px; height: 4px; text-align: center; }
QProgressBar::chunk { background: #7C6EF6; border-radius: 2px; }
QStatusBar { background: #161618; border-top: 1px solid #29292D; color: #71717A; font-size: 9px; }
QSplitter::handle { background: #29292D; width: 1px; height: 1px; }
QDialog#CommandPalette { background: #1B1B1E; color: #E4E4E7; border: 1px solid #3F3F46; }
QLineEdit#CommandSearch { font-size: 13px; padding: 10px 12px; background: #202023; }
QListWidget#CommandResults { border-radius: 5px; }
QListWidget#CommandResults::item { padding: 10px 12px; }
QLabel#CommandHint { color: #68686F; font-size: 9px; padding: 3px 5px; }
QToolTip { background: #252529; color: #E4E4E7; border: 1px solid #3F3F46; padding: 4px; }
"""
