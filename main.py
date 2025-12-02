import sys
import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional
import os

from utils import ensure_directories, setup_logging
from ui import launch_app

class Application:
    def __init__(self):
        self.root = None

    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """Show a message box with the specified level."""
        if not self.root:
            self.root = tk.Tk()
            self.root.withdraw()
        
        try:
            if level.lower() == "error":
                messagebox.showerror(title, message)
            elif level.lower() == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        except Exception as e:
            logging.error(f"Failed to show message: {e}")

    def run(self) -> None:
        """Main application entry point."""
        try:
            ensure_directories()
            setup_logging()
            logging.info("Starting Al-QuranCircle AutoFill Reports application")

            # Remote control mechanism removed for security
            # If needed in the future, implement with proper authentication
            # and signature verification (see remote_control.py for secure example)

            # Launch main application
            launch_app()

        except Exception as e:
            logging.exception("Fatal error in application")
            self.show_message(
                "Fatal Error",
                "A critical error occurred. Please check the logs for details.",
                "error"
            )
        finally:
            if self.root:
                try:
                    self.root.destroy()
                except:
                    pass

def main() -> None:
    app = Application()
    app.run()

if __name__ == "__main__":
    main()