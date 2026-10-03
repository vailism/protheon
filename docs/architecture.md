# Protheon Architecture

## Overview
Protheon separates real-time embedded constraints from high-level intelligence.

## Arduino Layer
- **Target:** Arduino Uno R3.
- **Role:** Acquires sensor data and outputs servo PWM signals.
- **Design:** Zero dynamic memory (`malloc`/`String`). Uses fixed static arrays and non-blocking `millis()` timing to guarantee stability in the 2KB SRAM environment.

## Serial Layer
- **Format:** Pipe-delimited ASCII strings with an 8-bit XOR checksum.
- **Safety:** The Arduino employs a 3000ms watchdog timer. If the Python backend crashes or stalls, the Arduino halts all servos autonomously.
- **Throttling:** The Python UI runs internally at higher framerates but throttles servo command outputs to ~10Hz to prevent serial buffer overflows on the Uno.

## Python Backend
- **Calibration Engine:** Normalizes raw 10-bit ADC values (0-1023) into 0-100% ranges with per-finger bounds.
- **Filtering:** Employs an Exponential Moving Average (EMA) filter with deadzone thresholds to strip sensor noise without excessive latency.
- **Gestures:** A rule-based classification engine maps normalized bend percentages to discrete postures (e.g., OPEN_HAND, CLOSED_FIST, PINCH). Debouncing (hysteresis) prevents flickering on boundaries.

## UI
- **Framework:** PySide6 + pyqtgraph.
- **Threading:** Serial acquisition, parsing, and SQLite database commits run on separate background threads. Only safe signals are passed to the Qt UI thread.

## Storage
- **Engine:** SQLite.
- **Performance:** Inserts are batched in memory and committed sequentially every 2.0 seconds to prevent blocking.

## Simulation
- Synthetic data generation allows for complete testing of the pipeline (calibration → filtering → gestures → UI) without physical hardware attached.
