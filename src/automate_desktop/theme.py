APP_STYLESHEET = """
QMainWindow, QWidget#Root { background: #F4F6F8; color: #172033; }
QFrame#Sidebar { background: #0B1220; border: none; }
QLabel#Brand { color: white; font-size: 24px; font-weight: 700; }
QLabel#BrandSub { color: #7DD3FC; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QPushButton#NavButton {
    text-align: left; border: none; border-radius: 9px; padding: 11px 14px;
    color: #CBD5E1; background: transparent; font-weight: 600;
}
QPushButton#NavButton:hover { background: #1F2937; color: white; }
QPushButton#NavButton:checked { background: #172554; color: #E0F2FE; border-left: 3px solid #38BDF8; }
QFrame#PrivacyCard { background: #172033; border-radius: 10px; }
QLabel#PrivacyTitle { color: #D1FAE5; font-weight: 700; }
QLabel#PrivacyBody { color: #94A3B8; font-size: 10px; }
QLabel#PageTitle { font-size: 29px; font-weight: 750; color: #111827; }
QLabel#PageSubtitle { font-size: 14px; color: #64748B; }
QFrame#Card { background: white; border: 1px solid #E2E8F0; border-radius: 13px; }
QLabel#CardLabel { color: #64748B; font-size: 11px; font-weight: 600; }
QLabel#MetricValue { color: #111827; font-size: 25px; font-weight: 750; }
QLabel#SectionTitle { color: #111827; font-size: 15px; font-weight: 700; }
QLabel#Muted { color: #64748B; }
QLabel#Notice {
    background: #ECFEFF; color: #155E75; border: 1px solid #A5F3FC;
    border-radius: 9px; padding: 10px 13px; font-size: 11px; font-weight: 600;
}
QPushButton#Primary {
    background: #4F46E5; color: white; border: none; border-radius: 8px;
    padding: 9px 16px; font-weight: 700;
}
QPushButton#Primary:hover { background: #4338CA; }
QPushButton#Primary:disabled { background: #A5B4FC; }
QPushButton#Secondary {
    background: white; color: #334155; border: 1px solid #CBD5E1;
    border-radius: 8px; padding: 8px 14px; font-weight: 600;
}
QPushButton#Secondary:hover { background: #F8FAFC; }
QLineEdit, QComboBox {
    background: white; border: 1px solid #CBD5E1; border-radius: 7px;
    padding: 7px 9px; selection-background-color: #4F46E5;
}
QListWidget, QTableWidget, QTextBrowser {
    background: white; border: 1px solid #E2E8F0; border-radius: 10px;
    selection-background-color: #EEF2FF; selection-color: #1E1B4B;
    outline: none;
}
QTextBrowser#DetailPanel { background: #FAFBFC; border: none; border-radius: 6px; }
QListWidget::item { padding: 8px; border-bottom: 1px solid #F1F5F9; }
QListWidget::item:selected { border-left: 3px solid #4F46E5; }
QHeaderView::section { background: #F8FAFC; border: none; border-bottom: 1px solid #E2E8F0; padding: 9px; font-weight: 700; }
QProgressBar { border: none; background: #E2E8F0; border-radius: 3px; height: 6px; text-align: center; }
QProgressBar::chunk { background: #4F46E5; border-radius: 3px; }
QStatusBar { background: white; border-top: 1px solid #E2E8F0; color: #64748B; }
"""
