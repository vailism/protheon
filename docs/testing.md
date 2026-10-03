# Testing Guide

Protheon relies on a comprehensive suite of unit tests, plus a robust simulation engine.

## Unit Tests
Tests are located in `tests/test_core.py`.
Run them using:
```bash
pytest tests/
```

Coverage includes:
* **Calibration:** Division-by-zero, out-of-bounds clamping, inverted polarity.
* **Filtering:** First-sample initialization, EMA smoothing, deadzone suppression.
* **Gestures:** Deterministic rule validation, hold-time hysteresis.
* **Protocol:** 8-bit XOR checksum consistency.
* **Safety:** Servo angle boundary clamping.

## Simulator
To test the pipeline without an Arduino, run:
```bash
python backend/main_ui.py --simulate
```
The simulator generates synthetic ADC values that smoothly cycle through known gestures, allowing UI and database logic testing.

## Hardware Test Procedure
1. Upload firmware.
2. Confirm serial output using a generic Serial Monitor (115200 baud).
3. Connect flex sensors and use the UI to verify real-time graphs.
4. Calibrate.
5. Connect unloaded servos one by one.
6. Verify safety E-STOP functionality.
