"""
Gestures Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']

class GesturesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("CUSTOM GESTURE EDITOR"))
        
        name_row = QHBoxLayout()
        name_lbl = QLabel("NAME:")
        name_lbl.setFont(Typography.metadata())
        self.txt_name = QLineEdit()
        self.txt_name.setStyleSheet(f"background: {Colors.BG_BASE}; color: {Colors.TEXT_MAIN}; border: 1px solid {Colors.BORDER}; padding: 4px;")
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.txt_name)
        card.addLayout(name_row)
        
        self.combos = {}
        for f in FINGERS:
            row = QHBoxLayout()
            lbl = QLabel(f.upper())
            lbl.setFont(Typography.metadata())
            combo = QComboBox()
            combo.addItems(["IGNORE", "OPEN", "CLOSED"])
            combo.setStyleSheet(f"background: {Colors.BG_BASE}; color: {Colors.TEXT_MAIN};")
            row.addWidget(lbl)
            row.addWidget(combo)
            self.combos[f] = combo
            card.addLayout(row)
            
        self.btn_save = PrimaryButton("SAVE GESTURE")
        card.addWidget(self.btn_save)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setFont(Typography.metadata())
        card.addWidget(self.lbl_status)
        
        layout.addWidget(card)
        layout.addStretch()
