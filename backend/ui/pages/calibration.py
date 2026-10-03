"""
Calibration Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']

class CalibrationPage(QWidget):
    def __init__(self, calib_profile, parent=None):
        super().__init__(parent)
        self.calib = calib_profile
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("CALIBRATION WORKFLOW"))
        
        self.status_lbl = QLabel("Loaded profile.")
        self.status_lbl.setFont(Typography.metadata())
        self.status_lbl.setStyleSheet(f"color: {Colors.ACCENT};")
        card.addWidget(self.status_lbl)
        
        card.layout.addSpacing(24)
        
        step1 = QLabel("STEP 1\nOpen your hand completely (straight fingers).")
        step1.setFont(Typography.body())
        card.addWidget(step1)
        
        self.btn_min = PrimaryButton("CAPTURE OPEN POSITION")
        card.addWidget(self.btn_min)
        
        card.layout.addSpacing(24)
        
        step2 = QLabel("STEP 2\nClose your hand completely (tight fist).")
        step2.setFont(Typography.body())
        card.addWidget(step2)
        
        self.btn_max = PrimaryButton("CAPTURE CLOSED POSITION")
        card.addWidget(self.btn_max)
        
        card.layout.addSpacing(24)
        
        self.calib_info = QLabel("")
        self.calib_info.setFont(Typography.metadata())
        card.addWidget(self.calib_info)
        
        layout.addWidget(card)
        layout.addStretch()

    def update_calib_display(self):
        txt = "Current Calibration:\n"
        for f in FINGERS:
            txt += f"{f.upper():8s} MIN: {self.calib.mins[f]:4d} | MAX: {self.calib.maxs[f]:4d}\n"
        self.calib_info.setText(txt)
