"""
UI module for Al-QuranCircle AutoFill Reports.

This module provides the main GUI application and dialogs.
"""

from .constants import (
    PROJECT_TITLE,
    PROJECT_VERSION,
    PROJECT_DEVELOPER,
    PROJECT_DESCRIPTION,
)
from .dialogs import ProfileHistoryDialog, BatchSubmitDialog

# Import StudentManagerApp from parent ui.py file
# Since main_window.py doesn't exist yet, we import directly from ui.py
# We need to do this carefully to avoid circular imports
import sys
import importlib.util
from pathlib import Path

# Get the parent ui.py file
parent_dir = Path(__file__).parent.parent
ui_py_path = parent_dir / "ui.py"

if ui_py_path.exists():
    # Load ui.py as a separate module to avoid circular imports
    # Use a unique module name to prevent conflicts
    module_name = "_ui_legacy_module"
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, ui_py_path)
        ui_legacy = importlib.util.module_from_spec(spec)
        # Execute the module - it will fall back to defining classes locally
        # since importing from ui.ui will fail (which is what we want)
        spec.loader.exec_module(ui_legacy)
        StudentManagerApp = ui_legacy.StudentManagerApp
        sys.modules[module_name] = ui_legacy
    else:
        # Module already loaded, get StudentManagerApp from it
        ui_legacy = sys.modules[module_name]
        StudentManagerApp = ui_legacy.StudentManagerApp
else:
    raise ImportError("Could not find ui.py file")

__all__ = [
    "PROJECT_TITLE",
    "PROJECT_VERSION",
    "PROJECT_DEVELOPER",
    "PROJECT_DESCRIPTION",
    "StudentManagerApp",
    "ProfileHistoryDialog",
    "BatchSubmitDialog",
    "launch_app",
]


def launch_app() -> None:
    """
    Launcher function called from main.py.
    """
    from utils import log_action, PROFILES_DIR
    
    app = StudentManagerApp()
    log_action(f"Application started. Profiles directory: {PROFILES_DIR}")
    app.mainloop()
    log_action("Application closed")

