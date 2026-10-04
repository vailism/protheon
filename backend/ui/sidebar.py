"""
Protheon UI Sidebar Navigation (Astra-style).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from ui.theme import Colors, Typography

class NavButton(QPushButton):
    def __init__(self, text, nav_id, parent=None):
        super().__init__(text, parent)
        self.nav_id = nav_id
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setStyleSheet(self._get_style(active=False))

    def set_active(self, active):
        self.setStyleSheet(self._get_style(active))

    def _get_style(self, active):
        bg = Colors.BG_PANEL_HOVER if active else "transparent"
        color = Colors.TEXT_MAIN if active else Colors.TEXT_MUTED
        border = f"border-left: 4px solid {Colors.ACCENT};" if active else "border-left: 4px solid transparent;"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                text-align: left;
                padding-left: 16px;
                {border}
                font-family: {Typography.FAMILY};
                font-weight: {'bold' if active else 'normal'};
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
        self.setFixedWidth(220)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_PANEL};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.nav_buttons = {}
        
        # Navigation Items based on Astra mockup
        self._add_nav_item("Dashboard", "dashboard")
        self._add_nav_item("Live Sensors", "sensors")
        self._add_nav_item("Virtual Hand", "virtual_hand")
        self._add_nav_item("Gestures", "gestures")
        self._add_nav_item("Calibration", "calibration")
        self._add_nav_item("Manual Control", "control")
        self._add_nav_item("Data Logger", "sessions")
        self._add_nav_item("Replay", "replay")
        self._add_nav_item("Analytics", "analytics")
        self._add_nav_item("ML Lab", "ml_lab")
        self._add_nav_item("Diagnostics", "diagnostics")
        self._add_nav_item("Settings", "settings")
        
        self.layout.addStretch()
        
        # Set default active
        self.set_active("dashboard")

    def _add_nav_item(self, text, nav_id):
        btn = NavButton(text, nav_id)
        btn.clicked.connect(lambda: self._on_nav_clicked(nav_id))
        self.layout.addWidget(btn)
        self.nav_buttons[nav_id] = btn

    def _on_nav_clicked(self, nav_id):
        self.set_active(nav_id)
        self.nav_requested.emit(nav_id)

    def set_active(self, nav_id):
        for nid, btn in self.nav_buttons.items():
            btn.set_active(nid == nav_id)
            
    def update_connection(self, state):
        pass # Moved to Topbar
        
    def update_mode(self, mode_str):
        pass # Moved to Topbar
