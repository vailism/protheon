import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.app import ProtheonApp

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ProtheonApp(simulate=True)
    window.show()

    def grab():
        # Let the UI render and simulator run for a moment
        pixmap = window.grab()
        pixmap.save("/Users/goat/.gemini/antigravity-ide/brain/22179e54-d979-4865-81c1-42a8c9057ae3/scratch/protheon_ui_after.png")
        app.quit()

    QTimer.singleShot(2000, grab)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
