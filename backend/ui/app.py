"""
Protheon UI Main Application Shell.
"""
import sys
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Slot, Qt

from ui.theme import GLOBAL_STYLESHEET
from ui.sidebar import Sidebar
from ui.topbar import Topbar

# Pages
from ui.pages.dashboard import DashboardPage
from ui.pages.virtual_hand import VirtualHandPage
from ui.pages.calibration import CalibrationPage
from ui.pages.control import ControlPage
from ui.pages.sessions import SessionsPage
from ui.pages.gestures import GesturesPage
from ui.pages.experiments import ExperimentsPage
from ui.pages.analytics import AnalyticsPage
from ui.pages.ml_lab import MLLabPage
from ui.pages.replay import ReplayPage
from ui.pages.diagnostics import DiagnosticsPage

# Backend Modules
from phip.serial_link import SerialLink
from phip.simulator import SimulatedArduino
from phip.calibration import CalibrationProfile
from phip.filtering import EMAFilter
from phip.gestures import GestureRecognizer
from phip.storage import SessionManager
from phip.analytics import AnalyticsEngine
from phip.export import DataExporter
from phip.replay import ReplayHardware
from phip.diagnostics import HealthMonitor
from phip.ml import MLAgent
from phip.experiment import ExperimentRunner
from PySide6.QtCore import Signal, QObject

logger = logging.getLogger("phip.ui")
FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky']

class BackendBridge(QObject):
    telemetry_signal = Signal(dict)
    state_signal = Signal(str)

class ProtheonApp(QMainWindow):
    def __init__(self, simulate=False):
        super().__init__()
        self.setWindowTitle("Protheon — Intelligent Prosthetic Hand Control Platform")
        self.resize(1280, 720)
        self.simulate = simulate
        self.setStyleSheet(GLOBAL_STYLESHEET)
        
        self._init_backend()
        self._build_ui()
        self._connect_signals()
        
        # Connect to Hardware
        if not self.link.connect():
            if not simulate:
                logger.warning("No Arduino detected. Use --simulate for testing.")

    def _init_backend(self):
        self.calib = CalibrationProfile("profiles/default.json")
        self.ema = EMAFilter(alpha=0.3, deadzone=2.0)
        self.recognizer = GestureRecognizer()
        self.db = SessionManager()
        self.analytics = AnalyticsEngine()
        self.exporter = DataExporter()
        self.health = HealthMonitor()
        self.ml = MLAgent()
        self.experiment = ExperimentRunner()
        
        self.db.start_session(name="Default UI Session", mode="SIMULATION" if self.simulate else "HARDWARE")
        
        if self.simulate:
            self.link = SimulatedArduino()
        else:
            self.link = SerialLink()
            
        self.replay_link = ReplayHardware(session_id=None)
        
        self.hardware_armed = False
        self.estop_active = False
        self._servo_send_counter = 0
        self._servo_send_interval = 5
        
        self.bridge = BackendBridge()
        self.bridge.telemetry_signal.connect(self._on_telemetry)
        self.bridge.state_signal.connect(self._on_state_change)
        self.link.add_callback(self.bridge.telemetry_signal.emit)
        self.link.add_state_callback(self.bridge.state_signal.emit)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Right Content Area
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.topbar = Topbar()
        right_layout.addWidget(self.topbar)
        
        # Stacked Pages
        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)
        
        # Initialize Pages
        self.pages = {}
        self.pages['dashboard'] = DashboardPage()
        self.pages['virtual_hand'] = VirtualHandPage()
        self.pages['calibration'] = CalibrationPage(self.calib)
        self.pages['control'] = ControlPage()
        self.pages['sessions'] = SessionsPage()
        self.pages['gestures'] = GesturesPage()
        self.pages['experiments'] = ExperimentsPage()
        self.pages['analytics'] = AnalyticsPage()
        self.pages['ml_lab'] = MLLabPage()
        self.pages['replay'] = ReplayPage()
        self.pages['diagnostics'] = DiagnosticsPage(self.simulate)
        
        for nav_id, widget in self.pages.items():
            self.stack.addWidget(widget)
            
        main_layout.addWidget(right_widget)
        
        self.sidebar.update_mode("SIMULATION" if self.simulate else "HARDWARE")
        self.topbar.update_session(self.db.current_session_id)

    def _connect_signals(self):
        self.sidebar.nav_requested.connect(self._switch_page)
        self.topbar.estop_requested.connect(self._emergency_stop)
        
        # Connect Actions
        self.pages['diagnostics'].btn_scan.clicked.connect(self._scan_ports)
        self.pages['diagnostics'].btn_connect.clicked.connect(self._manual_connect)
        if self.simulate:
            self.pages['diagnostics'].btn_noise.clicked.connect(lambda: self.link.inject_fault("NOISE", "thumb"))
            self.pages['diagnostics'].btn_stuck.clicked.connect(lambda: self.link.inject_fault("STUCK", "index"))
            self.pages['diagnostics'].btn_drop.clicked.connect(lambda: self.link.inject_fault("DROP"))
            self.pages['diagnostics'].btn_clear.clicked.connect(lambda: self.link.inject_fault("CLEAR"))
            
        # Calibration
        self.pages['calibration'].btn_min.clicked.connect(self._set_calib_min)
        self.pages['calibration'].btn_max.clicked.connect(self._set_calib_max)
        
        # Sessions
        self.pages['sessions'].btn_start.clicked.connect(self._start_new_session)
        self.pages['sessions'].btn_stop.clicked.connect(self._stop_current_session)
        self.pages['sessions'].btn_export.clicked.connect(self._export_session)
        
        # Control
        self.pages['control'].btn_arm.clicked.connect(self._toggle_hardware)
        for i, f in enumerate(FINGERS):
            self.pages['control'].sliders[f].valueChanged.connect(lambda val, idx=i: self._manual_servo(idx, val))
            
        # ML
        self.pages['ml_lab'].btn_train.clicked.connect(self._train_ml)
        
        # Gestures
        self.pages['gestures'].btn_save.clicked.connect(self._save_custom_gesture)
        
        # Replay
        self.pages['replay'].btn_start.clicked.connect(self._start_replay)
        self.pages['replay'].btn_stop.clicked.connect(self._stop_replay)
        
        # Analytics
        self.pages['analytics'].btn_analyze.clicked.connect(self._run_analytics)
        
        # Experiments
        self.pages['experiments'].btn_start.clicked.connect(self._start_experiment)

    @Slot(str)
    def _switch_page(self, nav_id):
        if nav_id in self.pages:
            self.stack.setCurrentWidget(self.pages[nav_id])
            
        titles = {
            'dashboard': ("Dashboard", "Live sensor telemetry and prosthetic state"),
            'virtual_hand': ("Virtual Hand", "3D digital twin sensor-derived estimation"),
            'calibration': ("Calibration", "Sensor range normalization"),
            'control': ("Control", "Manual servo command interface"),
            'sessions': ("Sessions", "Recording and exporting data"),
            'gestures': ("Gestures", "Custom deterministic gesture rules"),
            'experiments': ("Experiments", "Academic trials and response analysis"),
            'analytics': ("Analytics", "Post-session metrics and statistics"),
            'ml_lab': ("ML Lab", "Advisory k-NN modeling"),
            'replay': ("Replay", "Historical session playback"),
            'diagnostics': ("Diagnostics", "Hardware status and fault injection")
        }
        t, d = titles.get(nav_id, ("Protheon", ""))
        self.topbar.update_page_info(t, d)

    @Slot(dict)
    def _on_telemetry(self, data):
        raw = data['sensors']
        pct = self.calib.get_percentage(raw)
        filtered = self.ema.process(pct)
        gesture = self.recognizer.recognize(filtered)
        
        # Update Dashboard
        self.pages['dashboard'].update_telemetry(filtered, gesture)
        self.pages['dashboard'].update_safety(self.hardware_armed, self.estop_active)
        
        # Update Virtual Hand
        self.pages['virtual_hand'].update_hand(filtered)
        
        # Advisory ML Overlay
        if self.ml.is_trained:
            ml_pred, ml_conf = self.ml.predict(filtered)
            self.pages['ml_lab'].lbl_pred.setText(f"PREDICTION: {ml_pred} ({ml_conf*100:.0f}%)")
            if ml_conf > 0.6 and ml_pred != gesture and ml_pred != "UNKNOWN" and gesture != "UNKNOWN":
                self.pages['ml_lab'].lbl_pred.setStyleSheet("color: #FF4C4C;")
            else:
                self.pages['ml_lab'].lbl_pred.setStyleSheet("color: #4DA6FF;")

        # Experiments
        if self.experiment.is_running:
            self.experiment.process_telemetry(gesture)
            
        # Log to DB
        self.db.log_telemetry(data['timestamp'], raw, filtered, gesture, data['status'])
        
        # Hardware Servo Send
        if self.hardware_armed and not self.estop_active:
            self._servo_send_counter += 1
            if self._servo_send_counter >= self._servo_send_interval:
                self._servo_send_counter = 0
                for idx, f in enumerate(FINGERS):
                    angle = int((filtered[f] / 100.0) * 180)
                    self.link.send_command("SET", idx, angle)
                    
        # Diagnostics
        health_status = self.health.analyze(raw, data['timestamp'])
        stats = self.link.get_stats()
        faults = data.get('sensor_faults', 0)
        diag = f"=== CONNECTION ===\\nPort: {stats['port']}\\nState: {stats['state']}\\nRX/Drops: {stats['received']} / {stats['dropped']}\\n\\n"
        diag += f"=== SAFETY ===\\nE-Stop: {data.get('estop', False)}\\nArmed: {self.hardware_armed}\\n\\n"
        diag += f"=== HEALTH ===\\n"
        for i, f in enumerate(FINGERS):
            h_stat = health_status[f]
            indicator = "✅" if h_stat == "OK" else "⚠️"
            diag += f"[{f.upper():6s}] {indicator} {h_stat:15s}\\n"
        self.pages['diagnostics'].lbl_diag.setText(diag)

    @Slot(str)
    def _on_state_change(self, state):
        self.sidebar.update_connection(state)

    def _emergency_stop(self):
        self.estop_active = True
        self.hardware_armed = False
        self.link.send_stop()
        self.pages['control'].lbl_status.setText("E-STOP ACTIVE")
        self.pages['control'].lbl_status.setStyleSheet("color: #FF4C4C;")
        self.pages['dashboard'].update_safety(self.hardware_armed, self.estop_active)
        logger.warning("EMERGENCY STOP activated by user.")

    # Calibration Wrappers
    def _set_calib_min(self):
        self.calib.calibrate_min(self.link.last_data)
        self.pages['calibration'].update_calib_display()
    def _set_calib_max(self):
        self.calib.calibrate_max(self.link.last_data)
        self.pages['calibration'].update_calib_display()
        
    # Control Wrappers
    def _toggle_hardware(self):
        if self.estop_active:
            return # Can't arm in estop
        self.hardware_armed = not self.hardware_armed
        self.pages['control'].lbl_status.setText("ARMED" if self.hardware_armed else "DISARMED")
        self.pages['control'].lbl_status.setStyleSheet("color: #FFD93D;" if self.hardware_armed else "color: #4ECB71;")
        for f in FINGERS:
            self.pages['control'].sliders[f].setEnabled(self.hardware_armed)
        
    def _manual_servo(self, idx, val):
        if self.hardware_armed and not self.estop_active:
            self.link.send_command("SET", idx, val)
            
    # Session Wrappers
    def _start_new_session(self):
        mode = "SIMULATION" if self.simulate else "HARDWARE"
        sid = self.db.start_session(name="Manual Session", mode=mode)
        self.topbar.update_session(sid)
        self.pages['sessions'].lbl_current.setText(f"Session: {sid}")
        
    def _stop_current_session(self):
        self.db.stop_session()
        self.topbar.update_session(None)
        self.pages['sessions'].lbl_current.setText("NO SESSION")
        
    def _export_session(self):
        if self.db.current_session_id:
            self.exporter.export_session_csv(self.db.current_session_id)
            
    # Analytics Wrapper
    def _run_analytics(self):
        if not self.db.current_session_id: return
        self.db.flush()
        res = self.analytics.analyze_session(self.db.current_session_id)
        if "error" in res: return
        sys_m = res["system_metrics"]
        g_m = res["gesture_metrics"]
        txt = f"Runtime: {sys_m['runtime_sec']:.2f}s | Samples: {sys_m['total_samples']}\\nAvg Rate: {sys_m['avg_sample_rate_hz']:.1f} Hz\\nGestures:\\n"
        for g, c in g_m['distribution'].items(): txt += f" - {g}: {c}\\n"
        self.pages['analytics'].lbl_results.setText(txt)
        
    # ML Wrapper
    def _train_ml(self):
        if not self.db.current_session_id: return
        self.db.flush()
        success, msg = self.ml.train_on_session(self.db.current_session_id)
        self.pages['ml_lab'].lbl_status.setText(msg)
        
    # Gestures Wrapper
    def _save_custom_gesture(self):
        name = self.pages['gestures'].txt_name.text().strip().upper().replace(' ', '_')
        if not name: return
        rule = {}
        for f, combo in self.pages['gestures'].combos.items():
            val = combo.currentText()
            if val != "IGNORE": rule[f] = val
        self.recognizer.add_rule(name, rule)
        self.pages['gestures'].lbl_status.setText(f"Saved: {name}")
        self.pages['gestures'].txt_name.clear()
        
    # Replay
    def _start_replay(self):
        if not self.db.current_session_id: return
        self.link.disconnect()
        self.replay_link.set_session(self.db.current_session_id)
        self.replay_link.add_callback(self.bridge.telemetry_signal.emit)
        self.replay_link.add_state_callback(self.bridge.state_signal.emit)
        self.replay_link.connect()
        self.sidebar.update_mode("REPLAY")
        
    def _stop_replay(self):
        self.replay_link.disconnect()
        self._manual_connect()
        self.sidebar.update_mode("SIMULATION" if self.simulate else "HARDWARE")
        
    # Diagnostics
    def _scan_ports(self):
        self.pages['diagnostics'].combo_ports.clear()
        self.pages['diagnostics'].combo_ports.addItems(self.link.list_ports())
        
    def _manual_connect(self):
        self.link.disconnect()
        port = self.pages['diagnostics'].combo_ports.currentText()
        if port:
            self.link.connect(port)

    # Experiments
    def _start_experiment(self):
        trials = [
            {"gesture": "CLOSED_FIST", "hold_time": 1.0},
            {"gesture": "OPEN_HAND", "hold_time": 1.0},
        ]
        self.experiment.load_experiment(trials)
        self.experiment.start(self._on_experiment_update)
        self.pages['experiments'].lbl_results.setText("Running...")

    def _on_experiment_update(self, state):
        p = self.pages['experiments']
        if state["status"] == "WAITING":
            p.lbl_instruction.setText(f"[{state['trial_idx']}/{state['total_trials']}] {state['instruction']}")
        elif state["status"] == "SUCCESS":
            p.lbl_results.setText(f"Target '{state['target']}' hit in {state['reaction_time']:.3f}s\\n" + p.lbl_results.text())
        elif state["status"] == "COMPLETE":
            p.lbl_instruction.setText("Experiment Complete.")
