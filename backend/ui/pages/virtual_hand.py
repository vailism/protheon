"""
Virtual Hand Page
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader
from phip.virtual_hand import VirtualHandWidget

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']

class VirtualHandPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # Left: 3D Visualization
        viz_card = Card()
        viz_card.layout.setContentsMargins(0, 0, 0, 0)
        
        self.virtual_hand = VirtualHandWidget()
        viz_card.addWidget(self.virtual_hand)
        
        layout.addWidget(viz_card, stretch=70)
        
        # Right: Digital Twin Info
        info_card = Card()
        info_card.layout.addWidget(SectionHeader("DIGITAL TWIN"))
        
        desc = QLabel("Sensor-Derived Estimation\n\nNote: Represents estimated physical state. Physical servo feedback is not available on current hardware.")
        desc.setFont(Typography.body())
        desc.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        desc.setWordWrap(True)
        info_card.addWidget(desc)
        
        info_card.layout.addSpacing(24)
        
        self.finger_lbls = {}
        for f in FINGERS:
            row = QHBoxLayout()
            name_lbl = QLabel(f.capitalize())
            name_lbl.setFont(Typography.metadata())
            
            val_lbl = QLabel("0°")
            val_lbl.setFont(Typography.metadata())
            val_lbl.setStyleSheet(f"color: {Colors.ACCENT}; font-weight: bold;")
            val_lbl.setAlignment(Qt.AlignRight)
            
            row.addWidget(name_lbl)
            row.addWidget(val_lbl)
            info_card.addLayout(row)
            self.finger_lbls[f] = val_lbl
            
        info_card.layout.addStretch()
        layout.addWidget(info_card, stretch=30)

    def update_hand(self, filtered):
        self.virtual_hand.update_hand(filtered)
        
        for f in FINGERS:
            val = filtered.get(f, 0.0)
            angle = int((val / 100.0) * 180)
            self.finger_lbls[f].setText(f"{angle}°")
