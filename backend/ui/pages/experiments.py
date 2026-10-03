"""
Experiments Page
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, PrimaryButton

class ExperimentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        
        card = Card()
        card.layout.addWidget(SectionHeader("ACADEMIC TRIALS"))
        
        self.lbl_instruction = QLabel("Ready to start reaction time trial.")
        self.lbl_instruction.setFont(Typography.get_font(16, bold=True))
        self.lbl_instruction.setStyleSheet(f"color: {Colors.ACCENT};")
        card.addWidget(self.lbl_instruction)
        
        self.btn_start = PrimaryButton("START TRIAL")
        card.addWidget(self.btn_start)
        
        self.lbl_results = QLabel("Results will appear here.")
        self.lbl_results.setFont(Typography.metadata())
        card.addWidget(self.lbl_results)
        
        layout.addWidget(card)
        layout.addStretch()
