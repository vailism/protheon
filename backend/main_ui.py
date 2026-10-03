"""
Protheon Desktop Application — Main Entry Point
"""
import sys
import argparse
import logging
from PySide6.QtWidgets import QApplication
from ui.app import ProtheonApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

def main():
    parser = argparse.ArgumentParser(description="Protheon Desktop UI")
    parser.add_argument("--simulate", action="store_true", help="Run with simulated Arduino data.")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ProtheonApp(simulate=args.simulate)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
