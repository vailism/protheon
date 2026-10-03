"""
Protheon CLI — Serial Telemetry Monitor

Usage:
    python main.py              # Connect to real Arduino
    python main.py --simulate   # Use simulated data
    python main.py --port /dev/tty.usbmodem14101   # Specify port
"""

import argparse
import time
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

from phip.calibration import CalibrationProfile
from phip.filtering import EMAFilter
from phip.gestures import GestureRecognizer


def on_telemetry(data, cal, filt, gest):
    raw = data['sensors']
    pct = cal.get_percentage(raw)
    filtered = filt.process(pct)
    gesture = gest.recognize(filtered)

    s = data['sensors']
    line = (
        f"\r[T:{data['timestamp']:8d}ms] "
        f"TH:{s['thumb']:4d} IX:{s['index']:4d} MD:{s['middle']:4d} "
        f"RG:{s['ring']:4d} PK:{s['pinky']:4d} | "
        f"{gesture:20s}"
    )
    sys.stdout.write(line)
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Protheon CLI Telemetry Monitor")
    parser.add_argument("--simulate", action="store_true", help="Use simulated Arduino")
    parser.add_argument("--port", type=str, default=None, help="Serial port")
    args = parser.parse_args()

    print("=" * 60)
    print("  Protheon — Intelligent Prosthetic Hand Control Platform (CLI)")
    print("=" * 60)

    cal = CalibrationProfile("profiles/default.json")
    filt = EMAFilter(alpha=0.3, deadzone=2.0)
    gest = GestureRecognizer()

    if args.simulate:
        from phip.simulator import SimulatedArduino
        link = SimulatedArduino()
    else:
        from phip.serial_link import SerialLink
        link = SerialLink(port=args.port)

    link.add_callback(lambda d: on_telemetry(d, cal, filt, gest))

    if link.connect():
        try:
            print("Listening... Press Ctrl+C to stop.\n")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            link.disconnect()
    else:
        print("Could not connect. Use --simulate to test without hardware.")


if __name__ == "__main__":
    main()
