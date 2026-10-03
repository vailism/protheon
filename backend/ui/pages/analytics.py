"""
Analytics Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton

class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("ENGINEERING ANALYTICS"))
        
        self.btn_analyze = PrimaryButton("ANALYZE CURRENT SESSION")
        card.addWidget(self.btn_analyze)
        
        self.lbl_results = QLabel("Click analyze to view metrics.")
        self.lbl_results.setFont(Typography.metadata())
        card.addWidget(self.lbl_results)
        
        layout.addWidget(card)
        layout.addStretch()
