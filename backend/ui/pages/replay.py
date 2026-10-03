"""
Replay Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton, SecondaryButton

class ReplayPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("REPLAY ENGINE"))
        
        warn = QLabel("HARDWARE OUTPUT DISABLED DURING REPLAY")
        warn.setFont(Typography.metadata())
        warn.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
        card.addWidget(warn)
        
        row = QHBoxLayout()
        self.btn_start = PrimaryButton("START REPLAY")
        self.btn_stop = SecondaryButton("STOP REPLAY")
        
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addStretch()
        
        card.addLayout(row)
        
        layout.addWidget(card)
        layout.addStretch()
