"""
Control Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, SecondaryButton

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']

class ControlPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("MANUAL SERVO CONTROL"))
        
        top_row = QHBoxLayout()
        self.btn_arm = SecondaryButton("UNLOCK HARDWARE ARM")
        top_row.addWidget(self.btn_arm)
        
        self.lbl_status = QLabel("DISARMED")
        self.lbl_status.setFont(Typography.metadata())
        self.lbl_status.setStyleSheet(f"color: {Colors.GREEN};")
        top_row.addWidget(self.lbl_status)
        top_row.addStretch()
        
        card.addLayout(top_row)
        card.layout.addSpacing(24)
        
        self.sliders = {}
        for f in FINGERS:
            row = QHBoxLayout()
            lbl = QLabel(f.upper())
            lbl.setFont(Typography.metadata())
            lbl.setFixedWidth(80)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 180)
            slider.setValue(0)
            slider.setEnabled(False)
            
            val_lbl = QLabel("0°")
            val_lbl.setFont(Typography.metadata())
            val_lbl.setFixedWidth(40)
            val_lbl.setAlignment(Qt.AlignRight)
            
            row.addWidget(lbl)
            row.addWidget(slider)
            row.addWidget(val_lbl)
            
            self.sliders[f] = slider
            card.addLayout(row)
            
        layout.addWidget(card)
        layout.addStretch()
