"""Entry point for launching the application in GUI mode."""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

# Attempt to import main application window and its dependencies.
# This helps catch missing libraries early.
try:
    from app.GUI.main_window import MainWindow
    BACKEND_LOADED = True
except ImportError as e:
    print(f"A required library is missing: {e}")
    BACKEND_LOADED = False


def main() -> int:
    """Initializes the GUI application and starts the main event loop."""
    app = QApplication(sys.argv)
    if not BACKEND_LOADED:
        QMessageBox.critical(None, "Fatal Error",
                             "Could not find a required backend package or one of its dependencies (e.g., PyQt5, vtk). Please check the console and your installation.")
        return 1

    window = MainWindow()
    window.show()
    return app.exec_()