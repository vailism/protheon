"""
Diagnostics Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton, SecondaryButton

class DiagnosticsPage(QWidget):
    def __init__(self, simulate=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        left_layout = QVBoxLayout()
        
        card = Card()
        card.layout.addWidget(SectionHeader("CONNECTION STATUS"))
        
        row = QHBoxLayout()
        self.combo_ports = QComboBox()
        self.btn_scan = SecondaryButton("SCAN")
        self.btn_connect = PrimaryButton("CONNECT")
        row.addWidget(self.combo_ports)
        row.addWidget(self.btn_scan)
        row.addWidget(self.btn_connect)
        card.addLayout(row)
        
        self.lbl_diag = QLabel("Waiting for data...")
        self.lbl_diag.setFont(Typography.metadata())
        card.addWidget(self.lbl_diag)
        left_layout.addWidget(card)
        
        if simulate:
            fault_card = Card()
            fault_card.layout.addWidget(SectionHeader("FAULT INJECTION (SIMULATOR)"))
            self.btn_noise = SecondaryButton("INJECT NOISE")
            self.btn_stuck = SecondaryButton("STUCK SENSOR")
            self.btn_drop = SecondaryButton("DROP PACKETS")
            self.btn_clear = PrimaryButton("CLEAR FAULTS")
            
            fault_card.addWidget(self.btn_noise)
            fault_card.addWidget(self.btn_stuck)
            fault_card.addWidget(self.btn_drop)
            fault_card.addWidget(self.btn_clear)
            left_layout.addWidget(fault_card)
            
        left_layout.addStretch()
        layout.addLayout(left_layout)
        layout.addStretch()
