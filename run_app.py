"""This script is the official and ONLY entry point for launching the GUI application."""

import sys
import os

# Robustly add the project root directory to the Python path.
# This allows for consistent imports, e.g., `from app.modes import ...`
# Assumes the script is in a directory like 'project\run_app.py' and the
# root to be added is 'project'.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.modes import gui_mode


def main() -> int:
    """Initializes the application and starts the main event loop."""
    return gui_mode.main()


if __name__ == "__main__":
    sys.exit(main())