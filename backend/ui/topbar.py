"""
Protheon UI Top Header.
"""
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from ui.theme import Colors, Typography

class Topbar(QFrame):
    estop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_BASE};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(32, 0, 32, 0)
        
        # Left side: Page Title and Description
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignVCenter)
        left_layout.setSpacing(2)
        
        self.title_lbl = QLabel("Dashboard")
        self.title_lbl.setFont(Typography.page_title())
        
        self.desc_lbl = QLabel("Live sensor telemetry and prosthetic state")
        self.desc_lbl.setFont(Typography.body())
        self.desc_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        
        left_layout.addWidget(self.title_lbl)
        left_layout.addWidget(self.desc_lbl)
        self.layout.addLayout(left_layout)
        
        self.layout.addStretch()
        
        # Right side: Context info & Estop
        right_layout = QHBoxLayout()
        right_layout.setAlignment(Qt.AlignVCenter)
        right_layout.setSpacing(16)
        
        self.session_lbl = QLabel("NO SESSION")
        self.session_lbl.setFont(Typography.metadata())
        self.session_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        right_layout.addWidget(self.session_lbl)
        
        self.estop_btn = QPushButton("EMERGENCY STOP")
        self.estop_btn.setCursor(Qt.PointingHandCursor)
        self.estop_btn.setFixedHeight(36)
        self.estop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: white;
                font-family: {Typography.FAMILY};
                font-weight: bold;
                border-radius: 4px;
                padding: 0 16px;
                border: 1px solid #CC0000;
            }}
            QPushButton:hover {{ background-color: #FF6666; }}
            QPushButton:pressed {{ background-color: #CC0000; }}
        """)
        self.estop_btn.clicked.connect(self.estop_requested.emit)
        right_layout.addWidget(self.estop_btn)
        
        self.layout.addLayout(right_layout)

    def update_page_info(self, title, description):
        self.title_lbl.setText(title)
        self.desc_lbl.setText(description)

    def update_session(self, session_id):
        if session_id:
            short_id = session_id.split('-')[0]
            self.session_lbl.setText(f"SESSION #{short_id.upper()}")
        else:
            self.session_lbl.setText("NO SESSION")
