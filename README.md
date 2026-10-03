# PROTHEON

**Intelligent Prosthetic Hand Control Platform**

![Protheon Software Status](https://img.shields.io/badge/Software-V2_Complete-4ECB71?style=for-the-badge)
![Protheon Hardware Status](https://img.shields.io/badge/Hardware-Pending_Validation-FFD93D?style=for-the-badge)

Protheon is an advanced, intelligent prosthetic and robotic hand control platform. It abstracts real-time sensor acquisition and safe hardware constraints onto an Arduino Uno R3, while delegating complex tasks—such as signal filtering, gesture recognition, Machine Learning, academic trial analysis, and 3D digital twin visualization—to a powerful, professional Python-based PySide6 desktop ecosystem.

## 🌟 Key Features

### 🖥️ Professional Engineering Interface
- **Modular Dashboard:** Real-time telemetry plotting and global safety state monitoring.
- **3D Digital Twin:** Sensor-derived real-time estimation of the prosthetic hand rendered in 3D using PyOpenGL.
- **Diagnostics & Safety:** Deep diagnostic fault injection (for simulation testing), real-time connection telemetry, and a mandatory global Emergency Stop.

### 🧠 Intelligence & Analytics
- **Deterministic & ML Hybrid Engine:** Core operations rely on deterministic, user-configurable gesture rules for absolute safety, while a k-NN Machine Learning model runs as an advisory overlay to learn and predict complex gestures.
- **Academic Experiment Mode:** Built-in trial runners for recording cognitive/physical reaction times to target gestures, generating automated exportable reports.
- **Engineering Analytics:** Analyzes session metrics, average telemetry frequency, and gesture distribution dynamically.

### 🔧 Core Infrastructure
- **Hardware Abstraction Layer (HAL):** Decoupled simulator and physical serial links allow full software development without attached hardware.
- **Session Replay Engine:** Safely re-injects past recorded database sessions into the application bus without activating physical servos.
- **SQLite Storage:** Every session, telemetry frame, and status code is serialized to disk automatically.

---

## 🏗️ Architecture

```text
┌─────────────────────┐       ┌──────────────────────┐
│  Glove / Sensors    │       │ Protheon Python Core │
└──────────┬──────────┘       │                      │
           ↓                  │ 1. Serializer/Link   │
┌─────────────────────┐       │ 2. Data Calibration  │
│    Arduino Uno R3   │ ────→ │ 3. EMA Filtering     │
│ Sensor + Servo Ctrl │ ←──── │ 4. Gesture Engine    │
└──────────┬──────────┘       │ 5. Session Storage   │
           │                  │ 6. Safety Enforcer   │
┌──────────┴──────────┐       └──────────┬───────────┘
│   Prosthetic Hand   │                  ↓
│    (5x Servos)      │       ┌──────────────────────┐
└─────────────────────┘       │ PySide6 UI Framework │
                              └──────────────────────┘
```

---

## 💻 Software Stack
* **Firmware:** Arduino C++
* **Backend Core:** Python 3.9+
* **UI/Graphics:** PySide6, PyQtGraph, PyOpenGL
* **Data & ML:** Pandas, NumPy, Scikit-Learn
* **Storage:** SQLite3

---

## 🚀 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/<your-username>/protheon.git
   cd protheon
   ```

2. **Setup the Python Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Running in Simulation Mode (No Hardware Required)**
   ```bash
   python3 backend/main_ui.py --simulate
   ```

4. **Running with Hardware**
   ```bash
   python3 backend/main_ui.py
   ```

---

## 🛠️ Hardware Integration

* **Microcontroller:** Arduino Uno R3 (Powered via USB)
* **Sensors:** 5x Flex Sensors (Voltage dividers connected to A0-A4)
* **Actuators:** 5x Servo Motors (PWM on pins 3, 5, 6, 9, 10)

### Firmware Upload
1. Open `firmware/PHIP_firmware/PHIP_firmware.ino` in the Arduino IDE.
2. Select **Arduino Uno**.
3. Upload.
4. **Close the Arduino IDE Serial Monitor before launching the Python UI.**

### ⚠️ Critical Safety Directives
* **Servo Power:** Servos **MUST** be powered by an external power supply. Do NOT power servos from the Arduino's 5V pin.
* **Common Ground:** The external supply and the Arduino MUST share a common ground.
* **Unloaded Verification:** Always verify unloaded servos before connecting them to the mechanical hand linkages.
* **E-Stop & Watchdog:** Arduino automatically stops all servos if the USB connection drops or stalls for >3 seconds.

---

## 🧪 Testing

The codebase includes comprehensive test coverage for data filtering, database handling, gesture states, hardware bridging, and diagnostics.

```bash
cd backend
pytest tests/
```

---

## 🗺️ Roadmap

### CURRENT
* ✅ Software V2 Engine Complete
* ✅ UI/UX Professional Redesign Complete
* ⏳ Physical Hardware Validation & Tuning

### PLANNED
* EMG (Electromyography) Integration
* IMU for spatial awareness
* Force sensing fingertip feedback
* ESP32 wireless connectivity migration
