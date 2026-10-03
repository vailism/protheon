"""
Dashboard Page
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PySide6.QtCore import Qt
import pyqtgraph as pg
from ui.theme import Colors, Typography
from ui.components import Card, SectionHeader, StatusBadge

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']
FINGER_COLORS = {
    'thumb': Colors.RED, 'index': Colors.GREEN, 'middle': Colors.ACCENT,
    'ring': Colors.AMBER, 'pinky': '#C77DFF',
}

class SensorPanel(QWidget):
    def __init__(self, finger, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        
        lbl = QLabel(finger.upper())
        lbl.setFont(Typography.metadata())
        lbl.setFixedWidth(60)
        
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BORDER};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {FINGER_COLORS[finger]};
                border-radius: 4px;
            }}
        """)
        
        self.val_lbl = QLabel("0%")
        self.val_lbl.setFont(Typography.metadata())
        self.val_lbl.setFixedWidth(40)
        self.val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(lbl)
        layout.addWidget(self.bar)
        layout.addWidget(self.val_lbl)

    def update_val(self, pct):
        val = int(pct)
        self.bar.setValue(val)
        self.val_lbl.setText(f"{val}%")

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # Top Row
        top_layout = QHBoxLayout()
        top_layout.setSpacing(24)
        
        # Left: Sensors
        left_card = Card()
        left_card.layout.addWidget(SectionHeader("LIVE SENSOR TELEMETRY"))
        
        self.sensors = {}
        for f in FINGERS:
            sp = SensorPanel(f)
            self.sensors[f] = sp
            left_card.addWidget(sp)
            
        top_layout.addWidget(left_card, stretch=65)
        
        # Right: System State
        right_card = Card()
        right_card.layout.addWidget(SectionHeader("SYSTEM STATE"))
        
        self.gesture_lbl = QLabel("UNKNOWN")
        self.gesture_lbl.setFont(Typography.get_font(28, bold=True, mono=True))
        self.gesture_lbl.setStyleSheet(f"color: {Colors.GREEN};")
        self.gesture_lbl.setAlignment(Qt.AlignCenter)
        right_card.addWidget(self.gesture_lbl)
        
        state_layout = QVBoxLayout()
        self.safety_badge = StatusBadge("DISARMED", color=Colors.GREEN)
        state_layout.addWidget(self.safety_badge, alignment=Qt.AlignCenter)
        right_card.addLayout(state_layout)
        
        top_layout.addWidget(right_card, stretch=35)
        layout.addLayout(top_layout)
        
        # Bottom: Graph
        graph_card = Card()
        graph_card.layout.addWidget(SectionHeader("TELEMETRY HISTORY"))
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground(Colors.BG_PANEL)
        self.plot.setYRange(0, 100)
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        
        self.curves = {}
        for f in FINGERS:
            pen = pg.mkPen(FINGER_COLORS[f], width=2)
            self.curves[f] = self.plot.plot(pen=pen, name=f.capitalize())
            
        graph_card.addWidget(self.plot)
        layout.addWidget(graph_card, stretch=1)
        
        self.history_len = 200
        self.data_history = {f: [0.0] * self.history_len for f in FINGERS}

    def update_telemetry(self, filtered, gesture):
        self.gesture_lbl.setText(gesture)
        
        for f in FINGERS:
            val = filtered.get(f, 0.0)
            self.sensors[f].update_val(val)
            
            self.data_history[f].pop(0)
            self.data_history[f].append(val)
            self.curves[f].setData(self.data_history[f])

    def update_safety(self, armed, estop):
        if estop:
            self.safety_badge.setText("EMERGENCY STOP")
            self.safety_badge.set_color(Colors.RED)
        elif armed:
            self.safety_badge.setText("ARMED")
            self.safety_badge.set_color(Colors.AMBER)
        else:
            self.safety_badge.setText("DISARMED")
            self.safety_badge.set_color(Colors.GREEN)
