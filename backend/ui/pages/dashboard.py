"""
Dashboard Page (Astra-style).
"""
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QSplitter
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF
from ui.theme import Colors, Typography

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']
# Astra colors: green, blue, purple, orange, pink
F_COLORS = [
    QColor("#4dd0b2"), QColor("#62a6ff"), QColor("#c783ff"), QColor("#f6a55d"), QColor("#f588a4")
]

class GloveVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setStyleSheet(f"background-color: {Colors.BG_PANEL};")
        self.pcts = [0, 0, 0, 0, 0]

    def update_flex(self, pcts):
        self.pcts = pcts
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw palm
        palm_w, palm_h = 200, 50
        cx, cy = self.width() / 2, self.height() - 80
        palm_rect = QRectF(cx - palm_w/2, cy, palm_w, palm_h)
        painter.setBrush(QBrush(QColor("#2a3b4c")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(palm_rect, 10, 10)
        
        # Draw fingers
        spacing = 35
        start_x = cx - (2 * spacing)
        
        for i, (f, c) in enumerate(zip(FINGERS, F_COLORS)):
            painter.setPen(QPen(c, 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            fx = start_x + (i * spacing)
            
            if i == 0: # Thumb angles out
                fx -= 15
            
            # length based on flex (0 = fully extended, 100 = curled)
            # if 100% flexed, it's very short. 0% flexed = tall
            flex_pct = self.pcts[i] / 100.0
            base_length = 150
            if i == 0: base_length = 100
            if i == 2: base_length = 170 # middle longest
            if i == 4: base_length = 110 # pinky shortest
            
            length = base_length * (1.0 - (flex_pct * 0.7)) # don't completely disappear
            
            if i == 0:
                painter.drawLine(int(fx), int(cy), int(fx - 40), int(cy - length))
            else:
                painter.drawLine(int(fx), int(cy), int(fx), int(cy - length))
                
            # Draw dot at tip
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#ffffff")))
            if i == 0:
                painter.drawEllipse(QRectF(fx - 40 - 3, cy - length - 3, 6, 6))
            else:
                painter.drawEllipse(QRectF(fx - 3, cy - length - 3, 6, 6))

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # --- Header ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("System overview")
        title.setFont(Typography.get_font(20, bold=True))
        title.setStyleSheet(f"color: {Colors.TEXT_MAIN};")
        desc = QLabel("USB first. All readings keep their source and availability.")
        desc.setFont(Typography.body())
        desc.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        
        self.status_lbl = QLabel("CONNECTED · OPEN_HAND · Host: DISARMED / Firmware: DISARMED · LOCKED")
        self.status_lbl.setFont(Typography.get_font(13, bold=True))
        self.status_lbl.setStyleSheet(f"color: {Colors.TEXT_MAIN}; padding-top: 8px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(desc)
        header_layout.addWidget(self.status_lbl)
        layout.addLayout(header_layout)
        
        # --- Middle Splitter ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {Colors.BORDER}; width: 2px; }}")
        
        # Left Panel (Glove)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        glove_lbl = QLabel("ILLUSTRATIVE GLOVE ARTICULATION")
        glove_lbl.setFont(Typography.metadata())
        glove_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background-color: {Colors.BG_PANEL}; padding: 12px;")
        self.glove = GloveVisualizer()
        
        act_lbl = QLabel("Actual robotic finger / servo position: UNAVAILABLE")
        act_lbl.setFont(Typography.metadata())
        act_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background-color: {Colors.BG_PANEL}; padding: 12px;")
        
        left_layout.addWidget(glove_lbl)
        left_layout.addWidget(self.glove, stretch=1)
        left_layout.addWidget(act_lbl)
        
        # Right Panel (Table)
        self.table = QTableWidget(5, 6)
        self.table.setHorizontalHeaderLabels(["Finger", "Raw ADC", "Flex %", "Bend estimate", "Last command", "Actual"])
        self.table.verticalHeader().setVisible(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_PANEL};
                color: {Colors.TEXT_MAIN};
                gridline-color: {Colors.BORDER};
                border: none;
            }}
            QHeaderView::section {{
                background-color: #1c2732;
                color: {Colors.TEXT_MAIN};
                border: none;
                border-right: 1px solid {Colors.BORDER};
                border-bottom: 1px solid {Colors.BORDER};
                padding: 4px;
            }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i, f in enumerate(FINGERS):
            self.table.setItem(i, 0, QTableWidgetItem(f.capitalize()))
            for col in range(1, 6):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, col, item)
                
        splitter.addWidget(left_panel)
        splitter.addWidget(self.table)
        splitter.setSizes([400, 600])
        layout.addWidget(splitter, stretch=5)
        
        # --- Bottom Graph ---
        self.plot = pg.PlotWidget()
        self.plot.setBackground(Colors.BG_PANEL)
        self.plot.setYRange(0, 1023)
        self.plot.showGrid(x=False, y=True, alpha=0.1)
        self.plot.getAxis('left').setPen(pg.mkPen(Colors.TEXT_MUTED))
        self.plot.getAxis('bottom').setPen(pg.mkPen(Colors.TEXT_MUTED))
        
        self.curves = {}
        for i, f in enumerate(FINGERS):
            pen = pg.mkPen(F_COLORS[i], width=1.5)
            self.curves[f] = self.plot.plot(pen=pen, name=f.capitalize())
            
        layout.addWidget(self.plot, stretch=3)
        
        # History
        self.history_len = 200
        self.data_history = {f: [0.0] * self.history_len for f in FINGERS}
        
        # --- Bottom Bar ---
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(36)
        bottom_bar.setStyleSheet(f"background-color: {Colors.BG_PANEL}; border: 1px solid {Colors.BORDER}; border-radius: 4px;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0,0,0,0)
        self.btn_run_demo = QPushButton("Run confirmed demonstration")
        self.btn_run_demo.setStyleSheet(f"color: {Colors.TEXT_MAIN}; background: transparent; border: none;")
        bottom_layout.addWidget(self.btn_run_demo)
        layout.addWidget(bottom_bar)

    def update_telemetry(self, raw, filtered, gesture):
        # raw has raw ADC, filtered has %
        for i, f in enumerate(FINGERS):
            r_val = raw.get(f, 0) if raw else 0
            f_val = filtered.get(f, 0.0) if filtered else 0.0
            
            self.table.item(i, 1).setText(str(r_val))
            self.table.item(i, 2).setText(f"{int(f_val)}%")
            self.table.item(i, 3).setText(f"{int(f_val * 1.8)}° illustrative")
            self.table.item(i, 4).setText("---")
            self.table.item(i, 5).setText("UNAVAILABLE")
            
            self.data_history[f].pop(0)
            self.data_history[f].append(r_val) # Graph shows raw ADC according to Y axis 1023
            self.curves[f].setData(self.data_history[f])
            
        if filtered:
            self.glove.update_flex([filtered.get(f, 0) for f in FINGERS])
            
    def update_safety(self, armed, estop):
        pass # Status is updated via app.py
