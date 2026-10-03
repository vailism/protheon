"""
ML Lab Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton

class MLLabPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("ML ADVISORY LAB"))
        
        desc = QLabel("ADVISORY ONLY: Deterministic engine remains authoritative.")
        desc.setFont(Typography.metadata())
        desc.setStyleSheet(f"color: {Colors.AMBER};")
        card.addWidget(desc)
        
        self.btn_train = PrimaryButton("TRAIN K-NN")
        card.addWidget(self.btn_train)
        
        self.lbl_status = QLabel("Not trained.")
        self.lbl_status.setFont(Typography.metadata())
        card.addWidget(self.lbl_status)
        
        self.lbl_pred = QLabel("PREDICTION: —")
        self.lbl_pred.setFont(Typography.get_font(24, bold=True, mono=True))
        self.lbl_pred.setStyleSheet(f"color: {Colors.ACCENT};")
        card.addWidget(self.lbl_pred)
        
        layout.addWidget(card)
        layout.addStretch()
