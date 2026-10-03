# Protheon

**Intelligent Prosthetic Hand Control Platform**

## Overview
Protheon is an intelligent prosthetic/robotic hand control platform built around an Arduino Uno R3, five flex sensors, and a Python-based processing engine. It abstracts the real-time sensor acquisition and safe hardware constraints onto the microcontroller, while delegating complex tasks—such as signal filtering, gesture recognition, and UI visualization—to a powerful desktop backend.

## Features
* Arduino Uno integration
* Five-channel flex sensor acquisition
* Real-time monitoring
* Sensor calibration
* EMA filtering
* Deadzone handling
* Gesture recognition
* Servo control
* Hardware safety limits
* Communication watchdog
* Emergency stop
* SQLite telemetry
* Simulation mode
* Automated tests

## Architecture

```text
┌─────────────────────┐
│    Flex Sensors     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│    Arduino Uno R3   │
│ Sensor + Servo Ctrl │
└──────────┬──────────┘
           │ USB Serial
           ↓
┌─────────────────────┐
│ Python Backend      │
│                     │
│ Calibration         │
│ Filtering           │
│ Gestures            │
│ Safety              │
│ Storage             │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Protheon Dashboard  │
└─────────────────────┘
```

## Hardware
* **Microcontroller:** Arduino Uno R3 (Powered via USB)
* **Sensors:** 5x Flex Sensors (Voltage dividers connected to A0-A4)
* **Actuators:** 5x Servo Motors (PWM on pins 3, 5, 6, 9, 10)

## Software Stack
* **Firmware:** Arduino C++
* **Backend:** Python 3.9+
* **Dependencies:** `pyserial`, `PySide6`, `pyqtgraph`, `numpy`, `pytest`

## Installation
```bash
git clone <repository>
cd protheon
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## Running Simulation
```bash
python backend/main_ui.py --simulate
```

## Running Hardware
```bash
python backend/main_ui.py
```

## Arduino Firmware
1. Open `firmware/PHIP_firmware/PHIP_firmware.ino` in the Arduino IDE.
2. Select **Arduino Uno**.
3. Upload.
4. **Close the Arduino IDE Serial Monitor before running the Python UI.**

## Calibration
1. Launch the Protheon UI.
2. Navigate to the **Calibration** tab.
3. Fully extend all fingers (open hand) and click **Set OPEN Position (Min)**.
4. Close your hand into a tight fist and click **Set CLOSED Position (Max)**.
5. The profile is saved automatically to `profiles/default.json`.

## Safety
* **Servo Limits:** Firmware restricts angles to safe physical bounds.
* **Emergency Stop:** Prominent UI button stops all servos and blocks new commands.
* **Communication Watchdog:** Arduino automatically stops all servos if the USB connection drops or stalls for 3 seconds.
* **External Servo Power:** Servos **MUST** be powered by an external power supply. Do NOT power servos from the Arduino's 5V pin.
* **Common Ground:** The external supply and the Arduino MUST share a common ground.
* **Conservative Initial Testing:** Always verify unloaded servos before connecting them to the mechanical hand linkages.

## Testing
```bash
pytest tests/
```

## Project Status
* **Software:** functional / tested
* **Simulation:** tested
* **Firmware:** compiled
* **Physical hardware:** pending validation

## Roadmap

### CURRENT
* Hardware validation
* Physical integration testing

### PLANNED
* ML gesture recognition
* 3D digital twin
* EMG
* IMU
* Force sensing
* ESP32 wireless connectivity
