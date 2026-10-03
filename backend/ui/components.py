"""
Protheon Reusable UI Components.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from ui.theme import Colors, Typography

class Card(QFrame):
    """A standard panel container."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        
    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def addLayout(self, layout):
        self.layout.addLayout(layout)

class MetricCard(Card):
    """A compact card displaying a metric."""
    def __init__(self, title, value, unit="", parent=None):
        super().__init__(parent)
        
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setFont(Typography.metadata())
        self.title_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        
        val_layout = QHBoxLayout()
        val_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        
        self.val_lbl = QLabel(value)
        self.val_lbl.setFont(Typography.get_font(24, bold=True, mono=True))
        val_layout.addWidget(self.val_lbl)
        
        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setFont(Typography.metadata())
            unit_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; padding-bottom: 4px;")
            val_layout.addWidget(unit_lbl)
            
        self.addWidget(self.title_lbl)
        self.addLayout(val_layout)

    def set_value(self, value):
        self.val_lbl.setText(str(value))

class PrimaryButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: #000000;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: #66B2FF; }}
            QPushButton:pressed {{ background-color: #3399FF; }}
            QPushButton:disabled {{ background-color: {Colors.GRAY}; color: {Colors.TEXT_MUTED}; }}
        """)

class SecondaryButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_MAIN};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                font-weight: bold;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: {Colors.BG_PANEL_HOVER}; }}
            QPushButton:pressed {{ background-color: {Colors.BORDER}; }}
            QPushButton:disabled {{ color: {Colors.TEXT_MUTED}; }}
        """)

class DangerButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: #FF6666; }}
            QPushButton:pressed {{ background-color: #CC0000; }}
            QPushButton:disabled {{ background-color: {Colors.GRAY}; color: {Colors.TEXT_MUTED}; }}
        """)

class StatusBadge(QLabel):
    def __init__(self, text, color=Colors.GREEN, parent=None):
        super().__init__(text, parent)
        self.setFont(Typography.metadata())
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.set_color(color)
        
    def set_color(self, color):
        self.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                color: {color};
                border: 1px solid {color};
                border-radius: 4px;
                padding: 0 8px;
                font-weight: bold;
            }}
        """)

class SectionHeader(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(Typography.section_title())
        self.setStyleSheet(f"color: {Colors.TEXT_MAIN}; margin-bottom: 8px;")

class EmptyState(QWidget):
    def __init__(self, title, description, action_text=None, action_callback=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(Typography.section_title())
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_desc = QLabel(description)
        lbl_desc.setFont(Typography.body())
        lbl_desc.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        lbl_desc.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        
        if action_text and action_callback:
            btn = PrimaryButton(action_text)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.clicked.connect(action_callback)
            h_layout = QHBoxLayout()
            h_layout.setAlignment(Qt.AlignCenter)
            h_layout.addWidget(btn)
            layout.addLayout(h_layout)
            
        layout.addStretch()
