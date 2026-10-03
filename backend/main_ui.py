"""
Protheon Desktop Application — Main Entry Point

Launches the PySide6 dashboard with:
  - Dashboard (live graph + gesture + emergency stop)
  - Calibration tab
  - Diagnostics tab
  - Connection state indicator
  - Simulation mode (no Arduino required)

Usage:
    python main_ui.py              # Connect to real Arduino
    python main_ui.py --simulate   # Use simulated data
"""

import sys
import os
import argparse
import logging

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QProgressBar, QCheckBox,
    QStatusBar, QGroupBox, QGridLayout, QSlider, QComboBox,
    QMessageBox,
)
from PySide6.QtCore import Signal, QObject, Slot, Qt
from PySide6.QtGui import QFont, QColor
import pyqtgraph as pg

from phip.serial_link import SerialLink
from phip.simulator import SimulatedArduino
from phip.calibration import CalibrationProfile
from phip.filtering import EMAFilter
from phip.gestures import GestureRecognizer
from phip.storage import DataLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("phip.ui")

FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']
FINGER_COLORS = {
    'thumb': '#FF6B6B', 'index': '#4ECB71', 'middle': '#4DA6FF',
    'ring': '#FFD93D', 'pinky': '#C77DFF',
}


class BackendBridge(QObject):
    """Thread-safe bridge: serial thread → Qt UI thread via signal."""
    telemetry_signal = Signal(dict)
    state_signal = Signal(str)


class PHIPMainWindow(QMainWindow):
    def __init__(self, simulate=False):
        super().__init__()
        self.setWindowTitle("Protheon — Intelligent Prosthetic Hand Control Platform")
        self.resize(1100, 750)
        self.simulate = simulate

        # ---- Core Modules ----
        self.calib = CalibrationProfile("profiles/default.json")
        self.ema = EMAFilter(alpha=0.3, deadzone=2.0)
        self.recognizer = GestureRecognizer()
        self.db = DataLogger()

        # ---- Hardware Link ----
        if simulate:
            self.link = SimulatedArduino()
        else:
            self.link = SerialLink()

        # ---- Safety State ----
        self.hardware_armed = False
        self.estop_active = False
        self.last_raw = {}
        self.last_filtered = {f: 0.0 for f in FINGERS}

        # ---- Rate Limiting for Servo Commands ----
        # Only send commands every N telemetry frames to avoid flooding
        self._servo_send_counter = 0
        self._servo_send_interval = 5  # Send every 5th frame (~10Hz at 50Hz telemetry)

        # ---- Thread Bridge ----
        self.bridge = BackendBridge()
        self.bridge.telemetry_signal.connect(self._on_telemetry)
        self.bridge.state_signal.connect(self._on_state_change)
        self.link.add_callback(self.bridge.telemetry_signal.emit)
        self.link.add_state_callback(self.bridge.state_signal.emit)

        # ---- Graph History ----
        self.history_len = 200
        self.data_history = {f: [0.0] * self.history_len for f in FINGERS}

        self._build_ui()
        self._apply_stylesheet()

        # Auto-connect
        if not self.link.connect():
            if not simulate:
                self.status_bar.showMessage("⚠️  No Arduino detected. Use --simulate for testing.", 5000)

    # ==============================================================
    # UI CONSTRUCTION
    # ==============================================================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # ---- Top Bar: Connection + E-Stop ----
        top_bar = QHBoxLayout()

        self.conn_label = QLabel("🔴 DISCONNECTED")
        self.conn_label.setFont(QFont("monospace", 12, QFont.Bold))
        top_bar.addWidget(self.conn_label)

        self.mode_label = QLabel("MODE: SIMULATION" if self.simulate else "MODE: HARDWARE")
        self.mode_label.setFont(QFont("monospace", 10))
        self.mode_label.setStyleSheet("color: #888;")
        top_bar.addWidget(self.mode_label)

        top_bar.addStretch()

        self.estop_btn = QPushButton("🛑  EMERGENCY STOP")
        self.estop_btn.setFixedHeight(45)
        self.estop_btn.setMinimumWidth(200)
        self.estop_btn.setStyleSheet(
            "QPushButton { background-color: #D32F2F; color: white; font-size: 16px; "
            "font-weight: bold; border: 2px solid #B71C1C; border-radius: 6px; }"
            "QPushButton:hover { background-color: #B71C1C; }"
            "QPushButton:pressed { background-color: #7f0000; }"
        )
        self.estop_btn.clicked.connect(self._emergency_stop)
        top_bar.addWidget(self.estop_btn)

        main_layout.addLayout(top_bar)

        # ---- Tabs ----
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_dashboard_tab()
        self._build_calibration_tab()
        self._build_control_tab()
        self._build_diagnostics_tab()

        # ---- Status Bar ----
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")

    def _build_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Gesture Label
        self.gesture_lbl = QLabel("GESTURE: —")
        self.gesture_lbl.setFont(QFont("monospace", 28, QFont.Bold))
        self.gesture_lbl.setAlignment(Qt.AlignCenter)
        self.gesture_lbl.setStyleSheet("color: #4ECB71; padding: 10px;")
        layout.addWidget(self.gesture_lbl)

        # Live Graph
        self.plot_widget = pg.PlotWidget(title="Live Finger Bend (%)")
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.addLegend()
        self.plot_widget.setBackground('#1E1E2E')
        layout.addWidget(self.plot_widget)

        self.curves = {}
        for f in FINGERS:
            pen = pg.mkPen(FINGER_COLORS[f], width=2)
            self.curves[f] = self.plot_widget.plot(pen=pen, name=f.capitalize())

        # Per-Finger Gauges
        gauge_group = QGroupBox("Finger Bend Gauges")
        gauge_layout = QGridLayout()
        self.bars = {}
        self.val_labels = {}
        for i, f in enumerate(FINGERS):
            lbl = QLabel(f.upper())
            lbl.setFont(QFont("monospace", 10, QFont.Bold))
            lbl.setMinimumWidth(60)
            gauge_layout.addWidget(lbl, i, 0)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(True)
            bar.setFormat("%v%")
            gauge_layout.addWidget(bar, i, 1)
            self.bars[f] = bar

            val = QLabel("ADC: — | Servo: —°")
            val.setFont(QFont("monospace", 9))
            val.setStyleSheet("color: #888;")
            gauge_layout.addWidget(val, i, 2)
            self.val_labels[f] = val

        gauge_group.setLayout(gauge_layout)
        layout.addWidget(gauge_group)

        self.tabs.addTab(tab, "📊 Dashboard")

    def _build_calibration_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<h2>Calibration Engine</h2>"))

        # Calibration status
        self.calib_status = QLabel("⚠️  Not calibrated — using defaults.")
        self.calib_status.setStyleSheet("color: #FFD93D; font-size: 13px;")
        layout.addWidget(self.calib_status)
        if self.calib.is_calibrated:
            self.calib_status.setText("✅ Calibration loaded from profile.")
            self.calib_status.setStyleSheet("color: #4ECB71; font-size: 13px;")

        layout.addWidget(QLabel(
            "<b>Step 1:</b> Open your hand fully (straight fingers), then click:"))
        btn_min = QPushButton("📖  Set OPEN Position (Min)")
        btn_min.setFixedHeight(40)
        btn_min.clicked.connect(self._set_calib_min)
        layout.addWidget(btn_min)

        layout.addWidget(QLabel(
            "<b>Step 2:</b> Close your hand into a tight fist, then click:"))
        btn_max = QPushButton("✊  Set CLOSED Position (Max)")
        btn_max.setFixedHeight(40)
        btn_max.clicked.connect(self._set_calib_max)
        layout.addWidget(btn_max)

        # Validation warnings
        self.calib_warnings = QLabel("")
        self.calib_warnings.setStyleSheet("color: #FF6B6B;")
        layout.addWidget(self.calib_warnings)

        # Per-finger calibration values
        self.calib_info = QLabel("")
        self.calib_info.setFont(QFont("monospace", 10))
        layout.addWidget(self.calib_info)
        self._update_calib_display()

        layout.addStretch()
        self.tabs.addTab(tab, "🎯 Calibration")

    def _build_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<h2>Manual Servo Control</h2>"))

        # Hardware arm checkbox with warning
        arm_layout = QHBoxLayout()
        self.chk_arm = QCheckBox("🔓 ARM Hardware Servo Output")
        self.chk_arm.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.chk_arm.stateChanged.connect(self._toggle_hardware)
        arm_layout.addWidget(self.chk_arm)

        self.arm_status = QLabel("DISARMED — servos will not move")
        self.arm_status.setStyleSheet("color: #4ECB71;")
        arm_layout.addWidget(self.arm_status)
        layout.addLayout(arm_layout)

        # Manual sliders
        slider_group = QGroupBox("Individual Finger Control (requires ARM)")
        slider_layout = QGridLayout()
        self.sliders = {}
        self.slider_labels = {}
        for i, f in enumerate(FINGERS):
            lbl = QLabel(f.upper())
            lbl.setFont(QFont("monospace", 10, QFont.Bold))
            slider_layout.addWidget(lbl, i, 0)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 180)
            slider.setValue(0)
            slider.setEnabled(False)
            slider.valueChanged.connect(lambda val, idx=i: self._manual_servo(idx, val))
            slider_layout.addWidget(slider, i, 1)
            self.sliders[f] = slider

            val_lbl = QLabel("0°")
            slider_layout.addWidget(val_lbl, i, 2)
            self.slider_labels[f] = val_lbl

        slider_group.setLayout(slider_layout)
        layout.addWidget(slider_group)

        layout.addStretch()
        self.tabs.addTab(tab, "🎮 Control")

    def _build_diagnostics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("<h2>Diagnostics</h2>"))

        self.diag_text = QLabel("Waiting for data...")
        self.diag_text.setFont(QFont("monospace", 11))
        self.diag_text.setWordWrap(True)
        layout.addWidget(self.diag_text)

        # Port scan
        scan_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        scan_layout.addWidget(self.port_combo)

        btn_scan = QPushButton("🔍 Scan Ports")
        btn_scan.clicked.connect(self._scan_ports)
        scan_layout.addWidget(btn_scan)

        btn_connect = QPushButton("🔌 Connect")
        btn_connect.clicked.connect(self._manual_connect)
        scan_layout.addWidget(btn_connect)

        layout.addLayout(scan_layout)

        layout.addStretch()
        self.tabs.addTab(tab, "🔧 Diagnostics")

    # ==============================================================
    # TELEMETRY HANDLER (runs on Qt UI thread via signal)
    # ==============================================================
    @Slot(dict)
    def _on_telemetry(self, data):
        raw = data['sensors']
        self.last_raw = raw

        # Pipeline: raw → calibrate → filter → gesture → log
        pct = self.calib.get_percentage(raw)
        filtered = self.ema.process(pct)
        self.last_filtered = filtered
        gesture = self.recognizer.recognize(filtered)

        # Update gesture label
        self.gesture_lbl.setText(f"GESTURE: {gesture}")

        # Update gauges
        for f in FINGERS:
            self.bars[f].setValue(int(filtered[f]))
            self.val_labels[f].setText(
                f"ADC: {raw[f]:4d} | Servo: {data['servos'][f]}°")

        # Update graph
        for f in FINGERS:
            self.data_history[f].pop(0)
            self.data_history[f].append(filtered[f])
            self.curves[f].setData(self.data_history[f])

        # Log to database
        self.db.log_telemetry(
            data['timestamp'], raw, filtered, gesture, data['status'])

        # Send servo commands (rate-limited to avoid serial flooding)
        if self.hardware_armed and not self.estop_active:
            self._servo_send_counter += 1
            if self._servo_send_counter >= self._servo_send_interval:
                self._servo_send_counter = 0
                for idx, f in enumerate(FINGERS):
                    angle = int((filtered[f] / 100.0) * 180)
                    self.link.send_command("SET", idx, angle)

        # Update diagnostics
        stats = self.link.get_stats()
        status_flags = data.get('status', 0)
        faults = data.get('sensor_faults', 0)
        fault_str = ""
        for i, f in enumerate(FINGERS):
            if faults & (1 << i):
                fault_str += f"  ⚠️ {f.upper()} SENSOR FAULT\n"

        self.diag_text.setText(
            f"Port: {stats['port']}\n"
            f"State: {stats['state']}\n"
            f"Packets received: {stats['received']}\n"
            f"Packets dropped: {stats['dropped']}\n"
            f"Arduino status: {status_flags}\n"
            f"E-Stop active: {data.get('estop', False)}\n"
            f"{fault_str}"
        )

    @Slot(str)
    def _on_state_change(self, state):
        if state == "CONNECTED":
            self.conn_label.setText("🟢 CONNECTED")
            self.conn_label.setStyleSheet("color: #4ECB71;")
        elif state == "ERROR":
            self.conn_label.setText("🔴 ERROR")
            self.conn_label.setStyleSheet("color: #FF6B6B;")
        else:
            self.conn_label.setText("🔴 DISCONNECTED")
            self.conn_label.setStyleSheet("color: #FF6B6B;")

    # ==============================================================
    # ACTIONS
    # ==============================================================
    def _emergency_stop(self):
        """Immediately stop all servos and disarm."""
        self.estop_active = True
        self.hardware_armed = False
        self.chk_arm.setChecked(False)
        self.link.send_stop()
        self.arm_status.setText("🛑 E-STOP ACTIVE — servos stopped")
        self.arm_status.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        self.status_bar.showMessage("🛑 EMERGENCY STOP activated.", 10000)
        logger.warning("EMERGENCY STOP activated by user.")

    def _toggle_hardware(self, state):
        if state == Qt.Checked.value:
            if self.estop_active:
                # Must clear e-stop first
                reply = QMessageBox.question(
                    self, "Clear E-Stop?",
                    "Emergency stop is active. Clear it and arm servos?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    self.chk_arm.setChecked(False)
                    return
                self.estop_active = False
                self.link.send_ping()  # Clear Arduino e-stop state

            if not self.calib.is_calibrated:
                QMessageBox.warning(
                    self, "Calibration Required",
                    "Please calibrate the sensors before arming hardware.\n"
                    "Go to the Calibration tab.",
                )
                self.chk_arm.setChecked(False)
                return

            self.hardware_armed = True
            self.arm_status.setText("⚠️ ARMED — servos WILL move with your glove")
            self.arm_status.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            for s in self.sliders.values():
                s.setEnabled(True)
        else:
            self.hardware_armed = False
            self.link.send_stop()
            self.arm_status.setText("DISARMED — servos will not move")
            self.arm_status.setStyleSheet("color: #4ECB71;")
            for s in self.sliders.values():
                s.setEnabled(False)

    def _manual_servo(self, finger_idx, angle):
        """Manual slider control for individual fingers."""
        if self.hardware_armed and not self.estop_active:
            self.link.send_command("SET", finger_idx, angle)
            f = FINGERS[finger_idx]
            self.slider_labels[f].setText(f"{angle}°")

    def _set_calib_min(self):
        if not self.last_raw:
            self.status_bar.showMessage("No sensor data yet — is Arduino connected?", 3000)
            return
        self.calib.update_min(self.last_raw)
        self.calib.save()
        self._update_calib_display()
        self.status_bar.showMessage("✅ OPEN position calibrated.", 3000)

    def _set_calib_max(self):
        if not self.last_raw:
            self.status_bar.showMessage("No sensor data yet — is Arduino connected?", 3000)
            return
        self.calib.update_max(self.last_raw)
        self.calib.save()
        self.ema.reset()  # Reset filter after recalibration
        self._update_calib_display()
        self.calib_status.setText("✅ Calibration complete.")
        self.calib_status.setStyleSheet("color: #4ECB71; font-size: 13px;")
        self.status_bar.showMessage("✅ CLOSED position calibrated. Calibration saved.", 3000)

    def _update_calib_display(self):
        lines = []
        for f in FINGERS:
            lo = self.calib.min_vals[f]
            hi = self.calib.max_vals[f]
            span = abs(hi - lo)
            lines.append(f"{f.upper():8s}  min={lo:4d}  max={hi:4d}  range={span:3d}")
        self.calib_info.setText("\n".join(lines))

        warnings = self.calib.validate()
        if warnings:
            self.calib_warnings.setText("⚠️ " + "\n⚠️ ".join(warnings))
        else:
            self.calib_warnings.setText("")

    def _scan_ports(self):
        self.port_combo.clear()
        ports = SerialLink.list_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("(no ports found)")

    def _manual_connect(self):
        port = self.port_combo.currentText()
        if port and port != "(no ports found)":
            self.link.disconnect()
            if not self.simulate:
                self.link = SerialLink()
                self.link.add_callback(self.bridge.telemetry_signal.emit)
                self.link.add_state_callback(self.bridge.state_signal.emit)
            self.link.connect(port)

    # ==============================================================
    # STYLING
    # ==============================================================
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E2E; color: #CDD6F4; }
            QTabWidget::pane { border: 1px solid #45475A; background: #1E1E2E; }
            QTabBar::tab { background: #313244; color: #CDD6F4; padding: 8px 16px;
                           border: 1px solid #45475A; }
            QTabBar::tab:selected { background: #45475A; }
            QGroupBox { border: 1px solid #45475A; border-radius: 4px;
                        margin-top: 8px; padding-top: 16px; color: #CDD6F4; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QProgressBar { border: 1px solid #45475A; border-radius: 3px;
                           background: #313244; text-align: center; color: #CDD6F4; }
            QProgressBar::chunk { background-color: #4ECB71; }
            QPushButton { background: #313244; color: #CDD6F4; border: 1px solid #45475A;
                          border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background: #45475A; }
            QLabel { color: #CDD6F4; }
            QSlider::groove:horizontal { border: 1px solid #45475A; height: 6px;
                                         background: #313244; border-radius: 3px; }
            QSlider::handle:horizontal { background: #4DA6FF; width: 14px;
                                         margin: -4px 0; border-radius: 7px; }
            QCheckBox { color: #CDD6F4; }
            QComboBox { background: #313244; color: #CDD6F4; border: 1px solid #45475A;
                        padding: 4px; }
            QStatusBar { background: #181825; color: #888; }
        """)

    # ==============================================================
    # CLEANUP
    # ==============================================================
    def closeEvent(self, event):
        self.link.send_stop()
        self.link.disconnect()
        self.db.close()
        event.accept()


def main():
    parser = argparse.ArgumentParser(description="Protheon Desktop Application")
    parser.add_argument("--simulate", action="store_true",
                        help="Run with simulated Arduino data (no hardware needed)")
    parser.add_argument("--port", type=str, default=None,
                        help="Serial port to connect to (e.g., /dev/tty.usbmodem14101)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Protheon")
    window = PHIPMainWindow(simulate=args.simulate)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
