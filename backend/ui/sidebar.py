"""
Protheon UI Sidebar Navigation.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from ui.theme import Colors, Typography

class NavButton(QPushButton):
    def __init__(self, text, nav_id, parent=None):
        super().__init__(text, parent)
        self.nav_id = nav_id
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(self._get_style(active=False))

    def set_active(self, active):
        self.setStyleSheet(self._get_style(active))

    def _get_style(self, active):
        bg = Colors.BG_PANEL_HOVER if active else "transparent"
        color = Colors.TEXT_MAIN if active else Colors.TEXT_MUTED
        border = f"border-left: 3px solid {Colors.ACCENT};" if active else "border-left: 3px solid transparent;"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                text-align: left;
                padding-left: 12px;
                {border}
                font-weight: {'bold' if active else 'normal'};
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                border-top: none;
                border-right: none;
                border-bottom: none;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_PANEL_HOVER};
                color: {Colors.TEXT_MAIN};
            }}
        """

class Sidebar(QFrame):
    nav_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_BASE};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 24, 0, 24)
        self.layout.setSpacing(4)
        
        self._build_header()
        self.layout.addSpacing(24)
        
        self.nav_buttons = {}
        
        self._add_section("CONTROL")
        self._add_nav_item("Dashboard", "dashboard")
        self._add_nav_item("Virtual Hand", "virtual_hand")
        self._add_nav_item("Control", "control")
        
        self.layout.addSpacing(16)
        self._add_section("DATA")
        self._add_nav_item("Sessions", "sessions")
        self._add_nav_item("Replay", "replay")
        self._add_nav_item("Analytics", "analytics")
        
        self.layout.addSpacing(16)
        self._add_section("DEVELOPMENT")
        self._add_nav_item("Calibration", "calibration")
        self._add_nav_item("Gestures", "gestures")
        self._add_nav_item("Experiments", "experiments")
        self._add_nav_item("ML Lab", "ml_lab")
        
        self.layout.addSpacing(16)
        self._add_section("SYSTEM")
        self._add_nav_item("Diagnostics", "diagnostics")
        
        self.layout.addStretch()
        
        self._build_footer()
        
        # Set default active
        self.set_active("dashboard")

    def _build_header(self):
        lbl = QLabel("PROTHEON")
        lbl.setFont(Typography.app_title())
        lbl.setStyleSheet(f"color: {Colors.TEXT_MAIN}; padding-left: 16px; letter-spacing: 2px;")
        self.layout.addWidget(lbl)

    def _add_section(self, title):
        lbl = QLabel(title)
        lbl.setFont(Typography.metadata())
        lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; padding-left: 16px; padding-bottom: 4px;")
        self.layout.addWidget(lbl)

    def _add_nav_item(self, text, nav_id):
        btn = NavButton(text, nav_id)
        btn.clicked.connect(lambda: self._on_nav_clicked(nav_id))
        self.layout.addWidget(btn)
        self.nav_buttons[nav_id] = btn

    def _build_footer(self):
        self.conn_lbl = QLabel("● DISCONNECTED")
        self.conn_lbl.setFont(Typography.metadata())
        self.conn_lbl.setStyleSheet(f"color: {Colors.RED}; padding-left: 16px;")
        
        self.mode_lbl = QLabel("SIMULATION")
        self.mode_lbl.setFont(Typography.metadata())
        self.mode_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; padding-left: 16px;")
        
        self.layout.addWidget(self.conn_lbl)
        self.layout.addWidget(self.mode_lbl)

    def _on_nav_clicked(self, nav_id):
        self.set_active(nav_id)
        self.nav_requested.emit(nav_id)

    def set_active(self, nav_id):
        for nid, btn in self.nav_buttons.items():
            btn.set_active(nid == nav_id)

    def update_connection(self, state):
        if state == "CONNECTED":
            self.conn_lbl.setText("● CONNECTED")
            self.conn_lbl.setStyleSheet(f"color: {Colors.GREEN}; padding-left: 16px;")
        elif state == "ERROR":
            self.conn_lbl.setText("● ERROR")
            self.conn_lbl.setStyleSheet(f"color: {Colors.RED}; padding-left: 16px;")
        else:
            self.conn_lbl.setText("● DISCONNECTED")
            self.conn_lbl.setStyleSheet(f"color: {Colors.RED}; padding-left: 16px;")

    def update_mode(self, mode_str):
        self.mode_lbl.setText(mode_str)
