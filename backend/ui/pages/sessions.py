"""
Sessions Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton, SecondaryButton

class SessionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("SESSION MANAGEMENT"))
        
        self.lbl_current = QLabel("NO SESSION")
        self.lbl_current.setFont(Typography.metadata())
        card.addWidget(self.lbl_current)
        
        btn_row = QHBoxLayout()
        self.btn_start = PrimaryButton("NEW SESSION")
        self.btn_stop = SecondaryButton("STOP SESSION")
        self.btn_export = SecondaryButton("EXPORT CSV")
        
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_export)
        btn_row.addStretch()
        
        card.addLayout(btn_row)
        
        layout.addWidget(card)
        layout.addStretch()
