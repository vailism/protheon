"""
Protheon UI Top Header (Astra-style).
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from ui.theme import Colors, Typography

class Topbar(QWidget):
    estop_requested = Signal()
    scan_requested = Signal()
    connect_requested = Signal()
    disconnect_requested = Signal()
    rescan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Top Row ---
        top_row = QWidget()
        top_row.setFixedHeight(50)
        top_row.setStyleSheet(f"background-color: {Colors.BG_BASE}; border-bottom: 1px solid {Colors.BORDER};")
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(16, 0, 16, 0)
        
        self.title_lbl = QLabel("PROTHEON / SIMULATION")
        font = Typography.get_font(16, bold=True)
        self.title_lbl.setFont(font)
        self.title_lbl.setStyleSheet(f"color: {Colors.ACCENT}; border: none;")
        
        top_layout.addWidget(self.title_lbl)
        top_layout.addStretch()
        
        self.estop_btn = QPushButton("EMERGENCY STOP")
        self.estop_btn.setCursor(Qt.PointingHandCursor)
        self.estop_btn.setFixedHeight(32)
        self.estop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: white;
                font-family: {Typography.FAMILY};
                font-weight: bold;
                border-radius: 3px;
                padding: 0 16px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #e65565; }}
            QPushButton:pressed {{ background-color: #b03544; }}
        """)
        self.estop_btn.clicked.connect(self.estop_requested.emit)
        top_layout.addWidget(self.estop_btn)
        
        # --- Bottom Row (Connection Bar) ---
        bottom_row = QWidget()
        bottom_row.setFixedHeight(46)
        bottom_row.setStyleSheet(f"background-color: {Colors.BG_PANEL}; border-bottom: 1px solid {Colors.BORDER};")
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(16, 0, 16, 0)
        bottom_layout.setSpacing(8)
        
        combo_style = f"""
            QComboBox, QLineEdit {{
                background-color: {Colors.BG_BASE};
                color: {Colors.TEXT_MAIN};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                height: 24px;
            }}
        """
        btn_style = f"""
            QPushButton {{
                background-color: {Colors.GRAY};
                color: {Colors.TEXT_MAIN};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                height: 24px;
            }}
            QPushButton:hover {{ background-color: {Colors.BG_PANEL_HOVER}; }}
        """
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["SIMULATION", "REAL HARDWARE"])
        self.mode_combo.setStyleSheet(combo_style)
        
        self.combo_ports = QComboBox()
        self.combo_ports.setMinimumWidth(200)
        self.combo_ports.setStyleSheet(combo_style)
        
        self.btn_scan = QPushButton("Scan ports")
        self.btn_scan.setStyleSheet(btn_style)
        self.btn_scan.clicked.connect(self.scan_requested.emit)
        
        self.btn_rescan = QPushButton("Auto-Discover")
        self.btn_rescan.setStyleSheet(btn_style)
        self.btn_rescan.clicked.connect(self.rescan_requested.emit)
        
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setStyleSheet(btn_style)
        self.btn_connect.clicked.connect(self.connect_requested.emit)
        
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setStyleSheet(btn_style)
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)
        
        bottom_layout.addWidget(self.mode_combo)
        bottom_layout.addWidget(self.combo_ports)
        bottom_layout.addWidget(self.btn_scan)
        bottom_layout.addWidget(self.btn_rescan)
        bottom_layout.addWidget(self.btn_connect)
        bottom_layout.addWidget(self.btn_disconnect)
        bottom_layout.addStretch()
        
        # Status Label below it
        status_row = QWidget()
        status_row.setFixedHeight(30)
        status_row.setStyleSheet(f"background-color: {Colors.BG_BASE}; border-bottom: 1px solid {Colors.BORDER};")
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(16, 0, 16, 0)
        self.conn_status_lbl = QLabel("DISCONNECTED - controls locked")
        self.conn_status_lbl.setFont(Typography.metadata())
        self.conn_status_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none;")
        status_layout.addWidget(self.conn_status_lbl)
        
        main_layout.addWidget(top_row)
        main_layout.addWidget(bottom_row)
        main_layout.addWidget(status_row)
        
    def update_page_info(self, title, description):
        # We don't have a page title in topbar anymore, handled by layout
        pass

    def update_session(self, session_id):
        # Session ID not displayed in Astra topbar
        pass

    def update_mode(self, mode_str):
        self.title_lbl.setText(f"PROTHEON / {mode_str.upper()}")
        
    def update_status(self, is_connected, is_armed):
        if not is_connected:
            self.conn_status_lbl.setText("DISCONNECTED - controls locked")
            self.conn_status_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none;")
        elif not is_armed:
            self.conn_status_lbl.setText("CONNECTED - controls locked (DISARMED)")
            self.conn_status_lbl.setStyleSheet(f"color: {Colors.AMBER}; border: none;")
        else:
            self.conn_status_lbl.setText("CONNECTED - controls UNLOCKED")
            self.conn_status_lbl.setStyleSheet(f"color: {Colors.ACCENT}; border: none;")
