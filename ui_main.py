"""
Backward compatibility module for ui.py.

This module re-exports everything from the new ui package structure
to maintain backward compatibility with existing imports.
"""

# Import from the ui package (directory) not from this file
import sys
from pathlib import Path
import time

# Add the parent directory to path to import from ui package
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# Import from the ui package directory
# Skip this if we're being imported by ui/__init__.py to avoid circular import
try:
    # Check if we're being loaded by ui/__init__.py
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back and 'ui' in frame.f_back.f_globals:
        # We're being imported by ui package, skip the import
        raise ImportError("Circular import detected")
    from ui.ui import (
        PROJECT_TITLE,
        PROJECT_VERSION,
        PROJECT_DEVELOPER,
        PROJECT_DESCRIPTION,
        StudentManagerApp,
        ProfileHistoryDialog,
        BatchSubmitDialog,
        launch_app,
    )
except (ImportError, AttributeError):
    # Fallback: if ui package doesn't exist yet, import from local
    # This allows the file to work during the transition
    import logging
    logging.warning("ui package not found, using local definitions")
    
    # For now, keep the original implementation
    import customtkinter as ctk
    from typing import Dict, Any, List, Optional
    from pathlib import Path
    from datetime import datetime, date
    import threading
    from tkinter import messagebox, filedialog
    from tkcalendar import DateEntry
    
    from utils import (
        ensure_directories,
        setup_logging,
        load_all_profiles,
        save_profile,
        delete_profile,
        backup_profiles,
        search_profiles,
        sort_profiles,
        log_action,
        PROFILES_DIR,
        restore_profiles_from_backup,
        load_profile_history,
        append_profile_history,
    )
    from automation import submit_profile_to_form
    from config import config
    from settings_dialog import SettingsDialog
    
    PROJECT_TITLE = "Al-QuranCircle AutoFill Reports"
    PROJECT_VERSION = "v1.0.1 Beta"
    PROJECT_DEVELOPER = "Developed by Mahmoud Zaki"
    PROJECT_DESCRIPTION = "Automated reporting tool for Quran and Islamic studies teachers to manage student progress and generate reports.\n\nThis is a beta version of the application, please report any issues to the developer.\n\nDont't forget to make Du'aa for my parents."



DATE_FORMAT = "%d/%m/%Y"   # ← تنسيق التاريخ الجديد
class StudentManagerApp(ctk.CTk):
    """
    Main GUI application using CustomTkinter.
    """

    FIELD_KEYS = {
        "email": "Email",
        "date": "Date",
        "teacher_name": "Teacher Name",
        "student_name": "Student Name",
        "quran_surah": "Quran Surah",
        "tafseer": "Tafseer",
        "noor_page": "Noor Elbayan Page no.",
        "tajweed_rules": "Tajweed Rules",
        "topic": "Islamic Topic / AlQurancircle Duaa Book",
        "homework": "H.W",
        "parent_notes": "Additional Notes for Parent",
        "admin_notes": "Additional Notes for Admins",
    }

    def __init__(self):
        super().__init__()
        ensure_directories()
        setup_logging()

        # Apply theme and scaling from config
        theme = config.get("theme", "system")
        scaling = config.get("appearance.ui_scaling", 1.0)
        
        # Window configuration
        self.title(PROJECT_TITLE)
        
        # Set window size from config or use defaults
        window_width = config.get("window_size.width", 1180)
        window_height = config.get("window_size.height", 700)
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(960, 620)
        
        # Apply theme and scaling
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(scaling)
        ctk.set_window_scaling(scaling)
         
        # Check if window was maximized
        if config.get("window_size.maximized", False):
            self.state('zoomed')

        # State
        self.current_profile: Optional[Dict[str, Any]] = None
        self.current_profile_file: Optional[Path] = None
        self.profiles_cache: List[Dict[str, Any]] = []
        self.auto_save_on_close: bool = True
        self.field_widgets = {}
        self.student_buttons = []

        # Configure root window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Main content
        self.grid_columnconfigure(0, weight=0, minsize=280)  # Sidebar

        # Load UI settings before creating UI elements
        self._load_ui_settings()

        # Create UI components
        self._create_sidebar()
        self._create_main_panel()
        self._load_profiles_into_list()

        # Bind window resize event
        self.bind('<Configure>', self._on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def _on_window_resize(self, event=None):
        """Handle window resize events to ensure proper scaling."""
        # Update any dynamic elements here if needed
        pass

    # --- UI Creation Methods ---------------------------------------------

    def _create_sidebar(self) -> None:
        """Create the sidebar with consistent grid layout."""
        # Main sidebar container
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.sidebar.grid_propagate(False)
        
        # Configure grid weights
        self.sidebar.grid_rowconfigure(1, weight=1)  # For the scrollable area
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        # Top section (always visible)
        top_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        top_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 5))
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Students", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")
        
        # Settings buttons container with responsive layout
        settings_container = ctk.CTkFrame(top_frame, fg_color="transparent")
        settings_container.pack(fill="x")
        settings_container.grid_columnconfigure(0, weight=1)
        
        # Function to create responsive button grid
        def create_button(parent, text, command, width=80, **kwargs):
            btn = ctk.CTkButton(
                parent, 
                text=text, 
                command=command,
                width=width,
                **kwargs
            )
            return btn
        # --- Define theme-aware colors ---
        light_fg = "#FFFFFF"
        light_bg = "#0078D7"  # أزرق فاتح للأزرار في وضع النهار
        dark_fg = "#FFFFFF"
        dark_bg = "#1F6AA5"   # أزرق غامق للأزرار في وضع الليل
        hover_light = "#3399FF"
        hover_dark = "#3A8EDC"

        # Detect current theme (ctk supports light/dark automatically)
        if ctk.get_appearance_mode() == "Dark":
            btn_fg_color = dark_bg
            btn_hover_color = hover_dark
            btn_text_color = dark_fg
        else:
            btn_fg_color = light_bg
            btn_hover_color = hover_light
            btn_text_color = light_fg

        # --- Buttons container ---
        buttons_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 5))

        # Common button settings
        btn_width = 130
        btn_height = 40
        btn_padx = 5
        btn_pady = 5
        btn_corner = 8

        # --- First row ---
        row1 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, btn_pady))

        # Settings button
        settings_btn = ctk.CTkButton(
            row1, text="⚙️ Settings",
            width=btn_width, height=btn_height,
            fg_color=btn_fg_color, hover_color=btn_hover_color,
            text_color=btn_text_color,
            corner_radius=btn_corner,
            command=self.open_settings_dialog
        )
        settings_btn.pack(side="left", padx=btn_padx, expand=True, fill="x")

        # Report button
        report_btn = ctk.CTkButton(
            row1, text="📄 Report",
            width=btn_width, height=btn_height,
            fg_color=btn_fg_color, hover_color=btn_hover_color,
            text_color=btn_text_color,
            corner_radius=btn_corner,
            command=self.open_report_dialog
        )
        report_btn.pack(side="left", padx=btn_padx, expand=True, fill="x")


        # --- Second row ---
        row2 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row2.pack(fill="x")



        # Backup button
        backup_btn = ctk.CTkButton(
            row2, text="💾 Backup",
            width=btn_width, height=btn_height,
            fg_color=btn_fg_color, hover_color=btn_hover_color,
            text_color=btn_text_color,
            corner_radius=btn_corner,
            command=self.backup_profiles_action
        )
        backup_btn.pack(side="left", padx=btn_padx, expand=True, fill="x")


        # Restore button
        restore_btn = ctk.CTkButton(
            row2, text="♻️ Restore",
            width=btn_width, height=btn_height,
            fg_color=btn_fg_color, hover_color=btn_hover_color,
            text_color=btn_text_color,
            corner_radius=btn_corner,
            command=self.import_backup_action
        )
        restore_btn.pack(side="left", padx=btn_padx, expand=True, fill="x")

        # --- Store references ---
        self.settings_button = settings_btn
        self.backup_button = backup_btn
        self.import_backup_button = restore_btn
        self.report_button = report_btn

        
        # Search bar
        search_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(5, 0))
        
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search students...",
            height=32
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_students())
        
        # Sort options
        sort_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        sort_frame.pack(fill="x", pady=(5, 0))
        
        sort_label = ctk.CTkLabel(sort_frame, text="Sort by:")
        sort_label.pack(side="left", padx=(0, 5))
        
        self.sort_option = ctk.CTkComboBox(
            sort_frame,
            values=["", "Date", "Teacher Name", "Student Name"],
            state="readonly",
            width=120
        )
        self.sort_option.set("")
        self.sort_option.pack(side="left")
        self.sort_option.bind("<<ComboboxSelected>>", lambda e: self._load_profiles_into_list())
        
        # Student list in scrollable frame
        list_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        list_container.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame for student list
        self.student_listbox = ctk.CTkScrollableFrame(
            list_container,
            fg_color="transparent"
        )
        self.student_listbox.grid(row=0, column=0, sticky="nsew")
        self.student_buttons = []
        
        # Add Student button at the bottom
        add_btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        add_btn_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.add_button = ctk.CTkButton(
            add_btn_frame,
            text="➕ Add New Student",
            command=self.add_new_student,
            fg_color=("#3a7ebf", "#1f538d"),
            hover_color=("#325882", "#14375e"),
            height=36
        )
        self.add_button.pack(fill="x")
        
        # Set minimum width for the sidebar
        self.sidebar.update_idletasks()
        min_width = 280  # Minimum width to ensure all controls are visible
        self.sidebar.configure(width=max(self.sidebar.winfo_reqwidth(), min_width))


    def _create_main_panel(self) -> None:
        # Main panel container
        self.main_panel = ctk.CTkFrame(self)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.main_panel.grid_rowconfigure(0, weight=0)   # header
        self.main_panel.grid_rowconfigure(1, weight=1)   # scrollable form
        self.main_panel.grid_rowconfigure(2, weight=0)   # fixed bottom actions
        self.main_panel.grid_columnconfigure(0, weight=1)

        # =============================
        # HEADER AREA (Title + Buttons)
        # =============================
        header = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15), padx=10)
        header.grid_columnconfigure(0, weight=1)  # Title area expands
        header.grid_columnconfigure(1, weight=0)  # Top controls
        header.grid_columnconfigure(2, weight=0)  # Submit button

        # --- Left: Title, version, description ---
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        self.main_title = ctk.CTkLabel(
            title_box,
            text=PROJECT_TITLE,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.main_title.grid(row=0, column=0, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            title_box,
            text=f"{PROJECT_VERSION} • {PROJECT_DEVELOPER}",
            font=ctk.CTkFont(size=12),
            text_color="#A0A0A0"  # Subtle gray for secondary info
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.description_label = ctk.CTkLabel(
            title_box,
            text=PROJECT_DESCRIPTION,
            font=ctk.CTkFont(size=11),
            text_color="#C0C0C0"
        )
        self.description_label.grid(row=2, column=0, sticky="w", pady=(2, 0))

        # --- Right: Settings and Automation buttons ---
        top_controls = ctk.CTkFrame(header, fg_color="transparent")
        top_controls.grid(row=0, column=1, sticky="e", padx=8)
        top_controls.grid_columnconfigure(0, weight=1)

        button_width = 120
        button_height = 36
        button_padx = 4
        button_pady = 2
        corner_radius = 6

        # settings_btn = ctk.CTkButton(
        #     top_controls,
        #     text="⚙️ Settings",
        #     width=button_width,
        #     height=button_height,
        #     corner_radius=corner_radius,
        #     fg_color="#2D8CFF",
        #     hover_color="#1C6EDB",
        #     command=self.open_settings_dialog
        # )
        # settings_btn.grid(row=0, column=0, padx=button_padx, pady=button_pady, sticky="e")

        automation_btn = ctk.CTkButton(
            top_controls,
            text="🤖 Multiple Submissions",
            width=button_width,
            height=button_height,
            corner_radius=corner_radius,
            fg_color="red",
            hover_color="#DCE4EE",
            text_color="white",
            command=self.open_batch_submit_dialog
        )
        automation_btn.grid(row=0, column=2, padx=button_padx, pady=button_pady, sticky="e")

        # --- Submit button (top-right) ---
        self.submit_button = ctk.CTkButton(
            header,
            text="✅ Submit Current",
            width=150,
            height=button_height,
            corner_radius=corner_radius,
            fg_color="#28A745",
            hover_color="#1E7E34",
            command=self.submit_current_profile_to_form
        )
        self.submit_button.grid(row=0, column=2, padx=(12, 0), sticky="e")

        # =============================
        # SCROLLABLE FORM AREA
        # =============================
        form_scroll = ctk.CTkScrollableFrame(self.main_panel)
        form_scroll.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        form_scroll.grid_columnconfigure(1, weight=1)

        self.field_widgets = {}
        row_index = 0

        for key, text in self.FIELD_KEYS.items():
            lbl = ctk.CTkLabel(form_scroll, text=text + ":")
            lbl.grid(row=row_index, column=0, padx=10, pady=4, sticky="w")

            if key in {"parent_notes", "admin_notes"}:
                widget = ctk.CTkTextbox(form_scroll, height=60)

            elif key == "tafseer":
                widget = ctk.CTkComboBox(form_scroll, values=["Yes", "No"], state="readonly")
                widget.set("")

            elif key == "date":
                widget = ctk.CTkFrame(form_scroll)
                widget.grid_columnconfigure(0, weight=1)

                inner = ctk.CTkFrame(widget, fg_color="transparent")
                inner.grid(row=0, column=0, sticky="ew")

                date_entry = ctk.CTkEntry(inner)
                date_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

                cal_btn = ctk.CTkButton(
                    inner,
                    text="📅",
                    width=32,
                    command=lambda e=date_entry: self._show_calendar(e)
                )
                cal_btn.pack(side="right")

                widget._entry = date_entry

            else:
                widget = ctk.CTkEntry(form_scroll)

            widget.grid(row=row_index, column=1, padx=10, pady=4, sticky="ew")
            self.field_widgets[key] = widget
            row_index += 1

        # =============================
        # FIXED BOTTOM ACTION BAR
        # =============================
        actions = ctk.CTkFrame(self.main_panel)
        actions.grid(row=2, column=0, sticky="ew")
        actions.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

        # Row 0 buttons
        self.save_button = ctk.CTkButton(actions, text="Save Profile", command=self.save_profile_action)
        self.save_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.delete_button = ctk.CTkButton(actions, text="Delete Profile", command=self.delete_profile_action)
        self.delete_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.history_button = ctk.CTkButton(actions, text="History", command=self.open_history_dialog)
        self.history_button.grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        # Numeric inputs
        retries_label = ctk.CTkLabel(actions, text="Retries:")
        retries_label.grid(row=0, column=3, padx=(10, 2), sticky="e")
        self.retries_entry = ctk.CTkEntry(actions, width=60)
        self.retries_entry.insert(0, str(self._ui_settings.get("retries", 3)))
        self.retries_entry.grid(row=0, column=4, padx=2, sticky="w")

        delay_label = ctk.CTkLabel(actions, text="Delay (s):")
        delay_label.grid(row=0, column=5, padx=(10, 2), sticky="e")
        self.retry_delay_entry = ctk.CTkEntry(actions, width=60)
        self.retry_delay_entry.insert(0, str(self._ui_settings.get("retry_delay", 5)))
        self.retry_delay_entry.grid(row=0, column=6, padx=2, sticky="w")

        # Row 1 switches
        self.autosave_switch = ctk.CTkSwitch(actions, text="Autosave on close", command=self.toggle_autosave)
        if self._ui_settings.get("auto_save", True):
            self.autosave_switch.select()
        self.autosave_switch.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.send_copy_switch = ctk.CTkSwitch(actions, text="Send me a copy")
        if self._ui_settings.get("send_copy", False):
            self.send_copy_switch.select()
        self.send_copy_switch.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.show_browser_switch = ctk.CTkSwitch(actions, text="Show browser")
        if self._ui_settings.get("show_browser", False):
            self.show_browser_switch.select()
        self.show_browser_switch.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.use_extension_switch = ctk.CTkSwitch(actions, text="Use extension")
        if self._ui_settings.get("use_extension", False):
            self.use_extension_switch.select()
        self.use_extension_switch.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.auto_submit_switch = ctk.CTkSwitch(actions, text="Auto submit on save")
        if self._ui_settings.get("auto_submit", False):
            self.auto_submit_switch.select()
        self.auto_submit_switch.grid(row=1, column=4, padx=5, pady=5, sticky="w")


    # --- Helper methods --------------------------------------------------

    def _save_ui_settings(self) -> None:
        """Save all UI-related settings to config."""
        config.set("ui_settings.auto_save", bool(self.autosave_switch.get()))
        config.set("ui_settings.send_copy", bool(self.send_copy_switch.get()))
        config.set("ui_settings.show_browser", bool(self.show_browser_switch.get()))
        config.set("ui_settings.use_extension", bool(self.use_extension_switch.get()))
        config.set("ui_settings.auto_submit", bool(self.auto_submit_switch.get()))
        
        # Save retry settings
        try:
            retries = int(self.retries_entry.get())
            retry_delay = int(self.retry_delay_entry.get())
            config.set("ui_settings.retries", retries)
            config.set("ui_settings.retry_delay", retry_delay)
        except (ValueError, AttributeError):
            pass  # Keep existing values if conversion fails

    def _load_ui_settings(self) -> None:
        """Load UI settings from config and update UI elements."""
        # Load settings into instance variables first
        self.auto_save_on_close = config.get("ui_settings.auto_save", True)
        
        # Store settings in instance variables for later use
        self._ui_settings = {
            "auto_save": config.get("ui_settings.auto_save", True),
            "send_copy": config.get("ui_settings.send_copy", False),
            "show_browser": config.get("ui_settings.show_browser", False),
            "use_extension": config.get("ui_settings.use_extension", False),
            "auto_submit": config.get("ui_settings.auto_submit", False),
            "retries": config.get("ui_settings.retries", 3),
            "retry_delay": config.get("ui_settings.retry_delay", 5)
        }
        
        # Update UI elements if they exist
        if hasattr(self, 'autosave_switch'):
            if self._ui_settings["auto_save"]:
                self.autosave_switch.select()
            else:
                self.autosave_switch.deselect()
                
            if self._ui_settings["send_copy"]:
                self.send_copy_switch.select()
            else:
                self.send_copy_switch.deselect()
                
            if self._ui_settings["show_browser"]:
                self.show_browser_switch.select()
            else:
                self.show_browser_switch.deselect()
                
            if self._ui_settings["use_extension"]:
                self.use_extension_switch.select()
            else:
                self.use_extension_switch.deselect()
                
            if self._ui_settings["auto_submit"]:
                self.auto_submit_switch.select()
            else:
                self.auto_submit_switch.deselect()
                
            # Update retry settings
            if hasattr(self, 'retries_entry') and hasattr(self, 'retry_delay_entry'):
                self.retries_entry.delete(0, "end")
                self.retries_entry.insert(0, str(self._ui_settings["retries"]))
                self.retry_delay_entry.delete(0, "end")
                self.retry_delay_entry.insert(0, str(self._ui_settings["retry_delay"]))

    def _read_form_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, widget in self.field_widgets.items():
            if isinstance(widget, ctk.CTkTextbox):
                data[key] = widget.get("1.0", "end").strip()
            elif key == "date" and hasattr(widget, '_entry'):
                data[key] = widget._entry.get().strip()
            else:
                data[key] = widget.get().strip()
        return data

    def _write_form_data(self, data: Dict[str, Any]) -> None:
        for key, widget in self.field_widgets.items():
            value = data.get(key, "")
            if isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
                widget.insert("1.0", value)
            elif key == "date" and hasattr(widget, '_entry'):
                widget._entry.delete(0, "end")
                widget._entry.insert(0, value)
            elif isinstance(widget, ctk.CTkComboBox):
                widget.set(value)
            else:
                widget.delete(0, "end")
                widget.insert(0, value)

    def _clear_form(self) -> None:
        for key, widget in self.field_widgets.items():
            if isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
            elif key == "date" and hasattr(widget, '_entry'):
                widget._entry.delete(0, "end")
            elif isinstance(widget, ctk.CTkComboBox):
                widget.set("")
            elif isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")

    def open_report_dialog(self) -> None:
        """Open the report generation dialog."""
        try:
            from reporting.report_ui import ReportDialog
            ReportDialog(self)
        except ImportError as e:
            messagebox.showerror(
                "Error",
                f"Failed to load reporting module: {e}"
            )
            logging.exception("Error opening report dialog")

    def _show_calendar(self, entry_widget: ctk.CTkEntry) -> None:
        """Show a calendar popup for date selection."""
        def set_date():
            selected_date = cal.get_date()
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, selected_date.strftime('%d/%m/%Y'))
            top.destroy()

        top = ctk.CTkToplevel(self)
        top.title("Select Date")
        top.transient(self)
        top.grab_set()

        cal = DateEntry(top, width=12, background='darkblue',
                       foreground='white', borderwidth=2, date_pattern='dd/MM/yyyy')
        cal.pack(padx=10, pady=10)

        btn = ctk.CTkButton(top, text="OK", command=set_date)
        btn.pack(pady=5)
        
        # Center the window
        top.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (top.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (top.winfo_height() // 2)
        top.geometry(f"+{x}+{y}")
        top.focus_force()

    def open_settings_dialog(self) -> None:
        """Open the settings dialog."""
        def on_settings_saved():
            # Update theme if it was changed
            theme = config.get("theme", "system")
            ctk.set_appearance_mode(theme)
            
            # Update UI scaling
            scaling = config.get("appearance.ui_scaling", 1.0)
            ctk.set_widget_scaling(scaling)
            ctk.set_window_scaling(scaling)
            
            # Update font settings if needed
            font_family = config.get("appearance.font_family", "Arial")
            font_size = config.get("appearance.font_size", 12)
            
            # Update teacher info if it was changed
            teacher_info = config.get_teacher_info()
            
            # If we have a teacher name field, update it
            if hasattr(self, 'teacher_name_entry'):
                if teacher_info.get("name"):
                    self.teacher_name_entry.delete(0, "end")
                    self.teacher_name_entry.insert(0, teacher_info.get("name", ""))
                else:
                    self.teacher_name_entry.delete(0, "end")
            # Update email field if it exists in field_widgets
            if 'email' in self.field_widgets and teacher_info.get("email"):
                email_widget = self.field_widgets['email']
                if hasattr(email_widget, 'delete') and hasattr(email_widget, 'insert'):
                    email_widget.delete(0, 'end')
                    email_widget.insert(0, teacher_info.get("email", ""))
            
            # Update window title with teacher name if available
            if teacher_info.get("name"):
                self.title(f"{PROJECT_TITLE} - {teacher_info.get('name')}")
            else:
                self.title(PROJECT_TITLE)
            
            # Show a message that settings were saved
            messagebox.showinfo("Settings", "Settings have been saved successfully.")
        
        # Open the settings dialog
        settings_dialog = SettingsDialog(self, on_save=on_settings_saved)
        settings_dialog.wait_window()
    def _load_profiles_into_list(self) -> None:
        self.profiles_cache = load_all_profiles()

        # Map user-facing sort labels to actual profile dict keys
        sort_label = self.sort_option.get()
        sort_key_map = {
            "Date": "date",
            "Teacher Name": "teacher_name",
            "Student Name": "student_name",
        }
        sort_key = sort_key_map.get(sort_label, "")
        if sort_key:
            self.profiles_cache = sort_profiles(self.profiles_cache, sort_key)

        query = self.search_entry.get().strip()
        filtered = search_profiles(query, self.profiles_cache)

        # Clear sidebar list
        for child in self.student_listbox.winfo_children():
            child.destroy()
        self.student_buttons.clear()

        # Group profiles by date
        date_groups: Dict[str, List[Dict[str, Any]]] = {}
        for profile in filtered:
            date_str = profile.get("date", "Unknown Date")
            date_groups.setdefault(date_str, []).append(profile)

        # Convert string → date for proper sorting (latest → oldest)
        def get_date_key(d: str) -> date:
            try:
                if "/" in d:
                    return datetime.strptime(d, "%d/%m/%Y").date()
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return date.min

        # Sort by date (DESC)
        sorted_dates = sorted(date_groups.keys(), key=get_date_key, reverse=True)

        # Display groups with names sorted A→Z
        for date_str in sorted_dates:
            # Date header
            date_label = ctk.CTkLabel(
                self.student_listbox,
                text=str(date_str),
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            )
            date_label.pack(fill="x", padx=5, pady=(6, 2))

            # Sort students alphabetically
            students_sorted = sorted(
                date_groups[date_str],
                key=lambda p: p.get("student_name", "").strip().lower(),
            )

            # Add each student button
            for profile in students_sorted:
                name = profile.get("student_name", "Unknown")
                date_val = profile.get("date", "Unknown Date")
                display_text = f"{name} | {date_val}"

                button = ctk.CTkButton(
                    self.student_listbox,
                    text=display_text,
                    anchor="w",
                    command=lambda p=profile: self.load_profile_into_form(p),
                )
                button.pack(fill="x", padx=5, pady=2)
                self.student_buttons.append(button)


    def _filter_students(self) -> None:
        self._load_profiles_into_list()

    def _highlight_search(self) -> None:
        query = self.main_search_entry.get().strip()
        if not query:
            return
        logging.info("Main panel search: %s", query)

    def load_profile_into_form(self, profile: Dict[str, Any]) -> None:
        self.current_profile = profile
        file_path_str = profile.get("_file")
        self.current_profile_file = Path(file_path_str) if file_path_str else None
        self.main_title.configure(text=f"Student Profile: {profile.get('student_name', 'Unknown')}")
        self._write_form_data(profile)
        log_action(f"Loaded profile into form: {self.current_profile_file}")

    # --- Actions ---------------------------------------------------------

    def add_new_student(self) -> None:
        self.current_profile = None
        self.current_profile_file = None
        self._clear_form()
        
        # Auto-fill teacher information if available in config
        teacher_info = config.get_teacher_info()
        if teacher_info:
            # Auto-fill teacher name
            if 'teacher_name' in self.field_widgets:
                teacher_widget = self.field_widgets['teacher_name']
                if hasattr(teacher_widget, 'delete') and hasattr(teacher_widget, 'insert'):
                    teacher_widget.delete(0, 'end')
                    teacher_widget.insert(0, teacher_info.get('name', ''))
            
            # Auto-fill teacher email
            if 'email' in self.field_widgets and teacher_info.get('email'):
                email_widget = self.field_widgets['email']
                if hasattr(email_widget, 'delete') and hasattr(email_widget, 'insert'):
                    email_widget.delete(0, 'end')
                    email_widget.insert(0, teacher_info.get('email', ''))
        
        # Set current date in the date field
        if 'date' in self.field_widgets:
            date_widget = self.field_widgets['date']
            if hasattr(date_widget, '_entry'):
                date_widget._entry.delete(0, 'end')
                date_widget._entry.insert(0, datetime.now().strftime('%d/%m/%Y'))
            
        self.main_title.configure(text="New Student Profile")
        log_action("Started new student profile entry")

    def save_profile_action(self) -> None:
        data = self._read_form_data()

        if not data.get("student_name"):
            messagebox.showwarning("Missing Data", "Student Name is required.")
            return

        data["student_name"] = data.get("student_name", "").strip()
        data["teacher_name"] = data.get("teacher_name", "").strip()
        data["email"] = data.get("email", "").strip()

        filename = None
        old_data: Dict[str, Any] = {}
        if self.current_profile_file:
            filename = self.current_profile_file.name
            if self.current_profile:
                old_data = dict(self.current_profile)

        try:
            path = save_profile(data, filename=filename)

            if self.current_profile_file and old_data:
                append_profile_history(self.current_profile_file, old_data, data)

            self.current_profile_file = path
            self.current_profile = data
            self.main_title.configure(text=f"Student Profile: {data['student_name']}")
            self._load_profiles_into_list()
            messagebox.showinfo("Saved", "Profile saved successfully.")
            log_action(f"Profile saved: {self.current_profile_file}")

            if bool(self.auto_submit_switch.get()):
                self.submit_current_profile_to_form()
        except Exception as exc:
            logging.error("Error saving profile: %s", exc)
            messagebox.showerror("Error", f"Failed to save profile:\n{exc}")

    def open_history_dialog(self) -> None:
        if not self.current_profile_file:
            messagebox.showwarning(
                "No Profile Selected",
                "Load or save a profile before viewing history.",
            )
            return

        try:
            entries = load_profile_history(self.current_profile_file)
        except Exception as exc:  # noqa: BLE001
            logging.error("Error loading profile history: %s", exc)
            messagebox.showerror("Error", f"Failed to load history:\n{exc}")
            return

        if not entries:
            messagebox.showinfo(
                "No History",
                "No history is available for this profile yet.",
            )
            return

        ProfileHistoryDialog(self, self.current_profile_file, entries)

    def delete_profile_action(self) -> None:
        if not self.current_profile_file:
            messagebox.showwarning("No Profile Selected", "No profile is currently loaded.")
            return

        confirm = messagebox.askyesno(
            "Delete Profile",
            "Are you sure you want to delete this profile?",
        )
        if not confirm:
            return

        try:
            delete_profile(self.current_profile_file)
            self.add_new_student()
            self._load_profiles_into_list()
            messagebox.showinfo("Deleted", "Profile deleted successfully.")
        except Exception as exc:
            logging.error("Error deleting profile: %s", exc)
            messagebox.showerror("Error", f"Failed to delete profile:\n{exc}")

    def backup_profiles_action(self) -> None:
        try:
            backup_path = backup_profiles()
            messagebox.showinfo(
                "Backup Created",
                f"Backup created successfully:\n{backup_path.name}",
            )
        except Exception as exc:
            logging.error("Error creating backup: %s", exc)
            messagebox.showerror("Error", f"Failed to create backup:\n{exc}")

    def open_batch_submit_dialog(self) -> None:
        """Open a dialog to batch-submit multiple profiles in order."""
        try:
            BatchSubmitDialog(self)
        except Exception as exc:  # noqa: BLE001
            logging.error("Error opening BatchSubmitDialog: %s", exc)
            messagebox.showerror("Error", f"Failed to open batch submit dialog:\n{exc}")

    def submit_current_profile_to_form(self) -> None:
        if not self.current_profile_file:
            messagebox.showwarning(
                "No Profile Selected",
                "Load or save a profile before submitting the form.",
            )
            return

        form_settings = config.get_google_form_settings()
        form_url = (form_settings.get("form_url") or "").strip()
        if not form_url:
            messagebox.showerror(
                "Form URL Not Configured",
                "Please set up the Google Form URL in Settings > Reports tab."
            )
            return

        send_copy = bool(self.send_copy_switch.get())
        show_browser = bool(self.show_browser_switch.get())
        use_extension = bool(self.use_extension_switch.get())

        # Read retries and delay from UI with safe defaults
        try:
            max_retries = int(self.retries_entry.get().strip() or "3")
        except ValueError:
            max_retries = 3

        if max_retries < 1:
            max_retries = 1

        try:
            retry_delay = float(self.retry_delay_entry.get().strip() or "5")
        except ValueError:
            retry_delay = 5.0

        if retry_delay < 0:
            retry_delay = 0.0

        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Submitting...")
        progress_window.geometry("320x120")
        progress_window.resizable(False, False)

        label = ctk.CTkLabel(
            progress_window,
            text="Submitting form, please wait...",
        )
        label.pack(padx=15, pady=(15, 5))

        progress_bar = ctk.CTkProgressBar(progress_window, mode="indeterminate")
        progress_bar.pack(padx=15, pady=(5, 15), fill="x")
        progress_bar.start()

        progress_window.attributes("-topmost", True)

        def run_submission() -> None:
            try:
                success = submit_profile_to_form(
                    profile_path=str(self.current_profile_file),
                    form_url=form_url,
                    selectors_json_path=None,
                    max_retries=max_retries,
                    headless=not show_browser,
                    send_copy=send_copy,
                    use_extension=use_extension,
                    retry_delay_seconds=retry_delay,
                )

                def show_result() -> None:
                    if progress_window.winfo_exists():
                        progress_window.destroy()
                    if success:
                        messagebox.showinfo("Form Submission", "Form submitted successfully.")
                    else:
                        messagebox.showerror(
                            "Form Submission",
                            "Form submission failed after retries. See logs for details.",
                        )

                self.after(0, show_result)
            except FileNotFoundError as e:
                logging.error("Profile file not found during submission: %s", e)
                def show_error() -> None:
                    if progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showerror("File Not Found", f"Profile file not found:\n{str(e)}")
                self.after(0, show_error)
            except ValueError as e:
                logging.error("Validation error during submission: %s", e)
                def show_error() -> None:
                    if progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showerror("Validation Error", f"Invalid profile or form URL:\n{str(e)}")
                self.after(0, show_error)
            except RuntimeError as e:
                logging.error("Submission failed: %s", e)
                def show_error() -> None:
                    if progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showerror("Submission Failed", f"Form submission failed:\n{str(e)}")
                self.after(0, show_error)
            except Exception as exc:  # noqa: BLE001
                logging.error("Unexpected error during form submission: %s", exc, exc_info=True)
                def show_error() -> None:
                    if progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showerror("Error", f"An unexpected error occurred:\n{str(exc)}")
                self.after(0, show_error)

        threading.Thread(target=run_submission, daemon=True).start()

    def show_login_dialog(self) -> None:
        def on_success():
            messagebox.showinfo("Welcome", "Admin login successful.")

    def toggle_theme(self) -> None:
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        config.set("theme", new_mode.lower())  # Save the theme preference
        log_action(f"Theme switched to {new_mode}")

    def toggle_autosave(self) -> None:
        self.auto_save_on_close = bool(self.autosave_switch.get())
        log_action(f"Autosave on close set to {self.auto_save_on_close}")

    def on_close(self) -> None:
        """
        Handle window close event. Autosave current profile if enabled.
        """
        # Save UI settings and window state
        self._save_ui_settings()
        if self.state() == 'zoomed':
            config.set("window_size.maximized", True, save=False)
        else:
            config.set("window_size.maximized", False, save=False)
            config.set("window_size.width", self.winfo_width(), save=False)
            config.set("window_size.height", self.winfo_height(), save=False)
        config.save_settings()

        try:
            if self.auto_save_on_close:
                data = self._read_form_data()
                if any(value for value in data.values()):
                    filename = None
                    if self.current_profile_file:
                        filename = self.current_profile_file.name
                    save_profile(data, filename=filename)
                    log_action("Autosaved profile on close")
        except Exception as exc:  # noqa: BLE001
            logging.error("Error during autosave on close: %s", exc)
        finally:
            self.destroy()
    def import_backup_action(self) -> None:
        """Import profiles from a backup JSON file created by Backup Profiles."""
        file_path = filedialog.askopenfilename(
            title="Select backup JSON file",
            initialdir=str(PROFILES_DIR.parent / "backups"),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            restored_count = restore_profiles_from_backup(Path(file_path))
            self._load_profiles_into_list()
            messagebox.showinfo(
                "Import Complete",
                f"Restored {restored_count} profiles from backup:\n{Path(file_path).name}",
            )
        except Exception as exc:  # noqa: BLE001
            logging.error("Error importing backup %s: %s", file_path, exc)
            messagebox.showerror("Error", f"Failed to import backup:\n{exc}")

class ProfileHistoryDialog(ctk.CTkToplevel):
    def __init__(self, master: StudentManagerApp, profile_path: Path, entries: List[Dict[str, Any]]) -> None:
        super().__init__(master)
        self.master = master
        self.title(f"History - {profile_path.name}")
        self.geometry("1000x700")  # Increased window size
        self.minsize(900, 600)  # Set minimum size
        self.resizable(True, True)

        self.transient(master)
        self.lift()
        self.focus_force()
        self.grab_set()

        self.entries = entries
        self.current_entry = None

        # Configure grid weights for the main window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left panel - Revisions list
        left_frame = ctk.CTkFrame(main_frame, width=250)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # Right panel - Details with tabs
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Revisions header
        header_label = ctk.CTkLabel(
            left_frame,
            text="Revisions",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Revisions listbox with scroll
        self.listbox = ctk.CTkScrollableFrame(left_frame, corner_radius=0)
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 10))
        self.listbox.grid_columnconfigure(0, weight=1)

        # Create tabview for details
        self.tabview = ctk.CTkTabview(right_frame, corner_radius=0)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.tabview.add("Changes")
        self.tabview.add("Full Profile")
        self.tabview.set("Changes")  # Set default tab

        # Configure tab grid
        for tab in ["Changes", "Full Profile"]:
            self.tabview.tab(tab).grid_rowconfigure(0, weight=1)
            self.tabview.tab(tab).grid_columnconfigure(0, weight=1)

        # Changes tab
        self.changes_text = ctk.CTkTextbox(
            self.tabview.tab("Changes"),
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.changes_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Full Profile tab
        self.profile_text = ctk.CTkTextbox(
            self.tabview.tab("Full Profile"),
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.profile_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Bottom frame for buttons
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Close button
        close_button = ctk.CTkButton(
            bottom_frame,
            text="Close",
            command=self.destroy,
            width=100,
            height=32
        )
        close_button.pack(side="right", padx=5, pady=5)

        self._populate_entries()

    def _populate_entries(self) -> None:
        for child in self.listbox.winfo_children():
            child.destroy()

        for entry in self.entries:
            version = entry.get("version", "?")
            ts = entry.get("timestamp", "")
            # Format timestamp if it's in ISO format
            if "T" in ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    ts = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    pass
                    
            text = f"v{version} - {ts}"

            btn = ctk.CTkButton(
                self.listbox,
                text=text,
                anchor="w",
                command=lambda e=entry: self._show_entry_details(e),
                corner_radius=4,
                height=36,
                fg_color=("gray85", "gray16"),
                hover_color=("gray70", "gray30"),
                text_color=("gray10", "gray90")
            )
            btn.pack(fill="x", padx=4, pady=2)

        # Select the first entry by default if available
        if self.entries:
            self.after(100, lambda: self._show_entry_details(self.entries[0]))

    def _show_entry_details(self, entry: Dict[str, Any]) -> None:
        self.current_entry = entry
        
        # Update changes tab
        self.changes_text.configure(state="normal")
        self.changes_text.delete("1.0", "end")

        changes = entry.get("changes", {})
        if not changes:
            self.changes_text.insert("1.0", "No field changes recorded.")
        else:
            lines = []
            for field, diff in changes.items():
                old = diff.get("old", "[empty]")
                new = diff.get("new", "[empty]")
                lines.append(f"{field}:")
                lines.append(f"  Old: {old}")
                lines.append(f"  New: {new}")
                lines.append("-" * 50)
            self.changes_text.insert("1.0", "\n".join(lines))

        self.changes_text.configure(state="disabled")
        
        # Update full profile tab
        self._update_profile_preview(entry)
        
        # Highlight the selected entry
        for widget in self.listbox.winfo_children():
            if hasattr(widget, "configure"):
                if widget.cget("text").startswith(f"v{entry.get('version', '?')}"):
                    widget.configure(fg_color=("#3a7ebf", "#1f538d"))
                    widget.configure(text_color="white")
                else:
                    widget.configure(fg_color=("gray85", "gray16"))
                    widget.configure(text_color=("gray10", "gray90"))

    def _update_profile_preview(self, entry: Dict[str, Any]) -> None:
        """Update the full profile preview tab with formatted profile data."""
        self.profile_text.configure(state="normal")
        self.profile_text.delete("1.0", "end")
        
        # Get the full profile data (stored in the 'snapshot' key of the entry)
        profile_data = entry.get("snapshot", {})
        
        if not profile_data:
            self.profile_text.insert("end", "No profile data available.")
        else:
            # Format the profile data in a readable way
            for section, fields in profile_data.items():
                if not fields:
                    continue
                    
                # Skip internal fields starting with underscore
                if section.startswith('_'):
                    continue
                    
                # Add section header
                self.profile_text.insert("end", f"{section.upper()}\n")
                self.profile_text.insert("end", "=" * len(section) + "\n\n")
                
                # If fields is a dictionary, display key-value pairs
                if isinstance(fields, dict):
                    for field, value in fields.items():
                        # Skip internal fields
                        if field.startswith('_'):
                            continue
                        if value:  # Only show non-empty fields
                            self.profile_text.insert(
                                "end",
                                f"• {field}: {value}\n"
                            )
                # If fields is a string or other type, just display it
                elif fields:
                    self.profile_text.insert("end", f"• {fields}\n")
                
                self.profile_text.insert("end", "\n")
        
        self.profile_text.configure(state="disabled")


class BatchSubmitDialog(ctk.CTkToplevel):
    """Dialog for selecting and submitting multiple profiles in sequence."""

    def __init__(self, master: StudentManagerApp) -> None:
        super().__init__(master)
        self.master = master

        # ------------------ Window Config ------------------ #
        self.title("Batch Submit Profiles")
        self.geometry("650x520")
        self.resizable(True, True)

        self.transient(master)
        self.lift()
        self.focus_force()
        self.grab_set()

        self.profile_rows: List[Dict[str, Any]] = []

        # ====================================================
        #                   TOP CONFIG AREA
        # ====================================================
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Row 0
        ctk.CTkLabel(config_frame, text="Retries:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.retries_entry = ctk.CTkEntry(config_frame, width=70)
        self.retries_entry.insert(0, self.master.retries_entry.get() or "3")
        self.retries_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(config_frame, text="Delay per attempt (s):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.retry_delay_entry = ctk.CTkEntry(config_frame, width=70)
        self.retry_delay_entry.insert(0, self.master.retry_delay_entry.get() or "5")
        self.retry_delay_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Row 1
        ctk.CTkLabel(config_frame, text="Delay between profiles (s):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.between_profiles_entry = ctk.CTkEntry(config_frame, width=70)
        self.between_profiles_entry.insert(0, "3")
        self.between_profiles_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.send_copy_switch = ctk.CTkSwitch(config_frame, text="Send me a copy")
        if bool(self.master.send_copy_switch.get()): self.send_copy_switch.select()
        self.send_copy_switch.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.show_browser_switch = ctk.CTkSwitch(config_frame, text="Show browser")
        if bool(self.master.show_browser_switch.get()): self.show_browser_switch.select()
        self.show_browser_switch.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.use_extension_switch = ctk.CTkSwitch(config_frame, text="Use extension")
        if bool(self.master.use_extension_switch.get()): self.use_extension_switch.select()
        self.use_extension_switch.grid(row=2, column=0, padx=5, pady=5, sticky="w", columnspan=2)

        # ====================================================
        #           SCROLLABLE PROFILES LIST
        # ====================================================
        list_frame = ctk.CTkScrollableFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        from utils import load_all_profiles as _load_all_profiles
        profiles = _load_all_profiles()

        # --------- Parse date safely ---------
        def parse_date(date_str: str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return datetime.min

        # --------- Sort from newest to oldest ---------
        profiles_sorted = sorted(
            profiles,
            key=lambda p: parse_date(p.get("date", "")),
            reverse=True
        )

        # --------- Group profiles by date ---------
        from collections import defaultdict
        grouped_profiles: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for profile in profiles_sorted:
            raw_date = profile.get("date", "")
            try:
                date_str = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%d/%m/%Y")
            except:
                date_str = "Unknown Date"
            grouped_profiles[date_str].append(profile)

        # --------- Build UI grouped by date ---------
        for date_str in sorted(grouped_profiles.keys(), key=lambda d: parse_date(d), reverse=True):
            # Date header
            ctk.CTkLabel(
                list_frame,
                text=date_str,
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w"
            ).pack(fill="x", padx=5, pady=(10, 5))

            for profile in grouped_profiles[date_str]:
                file_path_str = profile.get("_file")
                if not file_path_str:
                    continue

                path = Path(file_path_str)
                name = profile.get("student_name", "Unknown")
                teacher = profile.get("teacher_name", "")
                title_text = f"{name} | {teacher}" if teacher else name

                # Row container
                row_frame = ctk.CTkFrame(list_frame)
                row_frame.pack(fill="x", padx=5, pady=3)

                # Header row
                header = ctk.CTkFrame(row_frame)
                header.pack(fill="x")

                include_var = ctk.BooleanVar(value=False)
                ctk.CTkCheckBox(header, text="", variable=include_var).grid(row=0, column=0, padx=5)

                toggle_btn = ctk.CTkButton(header, text="▶", width=28,
                                        command=lambda rf=row_frame: self._toggle_details(rf))
                toggle_btn.grid(row=0, column=1, padx=5)

                title = ctk.CTkLabel(header, text=title_text, anchor="w")
                title.grid(row=0, column=2, sticky="ew", padx=5)
                header.grid_columnconfigure(2, weight=1)

                # Details
                details = ctk.CTkFrame(row_frame)
                details.pack(fill="x", padx=5, pady=(5, 8))
                details.grid_columnconfigure(1, weight=1)

                def add(i, label, value):
                    ctk.CTkLabel(details, text=f"{label}:").grid(row=i, column=0, sticky="w", padx=5)
                    ctk.CTkLabel(details, text=value, anchor="w").grid(row=i, column=1, sticky="w")

                add(0, "Quran Surah", profile.get("quran_surah", ""))
                add(1, "Noor Page", profile.get("noor_page", ""))
                add(2, "Tajweed", profile.get("tajweed_rules", ""))
                add(3, "Topic", profile.get("topic", ""))

                details.pack_forget()  # default collapsed

                self.profile_rows.append(
                    {
                        "path": path,
                        "include_var": include_var,
                        "details_frame": details,
                        "row_frame": row_frame,
                    }
                )

        # ====================================================
        #                   BOTTOM BAR
        # ====================================================
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(bottom_frame, text="Select profiles and click 'Send Selected'.")
        self.status_label.pack(side="left", padx=5)

        ctk.CTkButton(
            bottom_frame,
            text="Send Selected",
            command=self.start_batch_submission
        ).pack(side="right", padx=5)



    def _toggle_details(self, row_frame: ctk.CTkFrame) -> None:
        for row in self.profile_rows:
            if row["row_frame"] is row_frame:
                details = row["details_frame"]
                if details.winfo_manager():
                    details.pack_forget()
                else:
                    details.pack(fill="x", padx=5, pady=(3, 5))
                break

    def start_batch_submission(self) -> None:
        # Read numeric options
        try:
            max_retries = int(self.retries_entry.get().strip() or "3")
        except ValueError:
            max_retries = 3
        if max_retries < 1:
            max_retries = 1

        try:
            retry_delay = float(self.retry_delay_entry.get().strip() or "5")
        except ValueError:
            retry_delay = 5.0
        if retry_delay < 0:
            retry_delay = 0.0

        try:
            between_delay = float(self.between_profiles_entry.get().strip() or "3")
        except ValueError:
            between_delay = 3.0
        if between_delay < 0:
            between_delay = 0.0

        send_copy = bool(self.send_copy_switch.get())
        show_browser = bool(self.show_browser_switch.get())
        use_extension = bool(self.use_extension_switch.get())

        selected = [row for row in self.profile_rows if row["include_var"].get()]
        if not selected:
            messagebox.showwarning("No Profiles Selected", "Please select at least one profile to submit.")
            return

        self.status_label.configure(text=f"Submitting {len(selected)} profiles...")

        def run_batch() -> None:
            success_count = 0
            total = len(selected)
            form_settings = config.get_google_form_settings()
            form_url = (form_settings.get("form_url") or "").strip()
            if not form_url:
                def show_error() -> None:
                    messagebox.showerror(
                        "Form URL Not Configured",
                        "Please set up the Google Form URL in Settings > Reports tab."
                    )
                self.after(0, show_error)
                return

            for idx, row in enumerate(selected, start=1):
                path = row["path"]
                try:
                    ok = submit_profile_to_form(
                        profile_path=str(path),
                        form_url=form_url,
                        selectors_json_path=None,
                        max_retries=max_retries,
                        headless=not show_browser,
                        send_copy=send_copy,
                        use_extension=use_extension,
                        retry_delay_seconds=retry_delay,
                    )
                    if ok:
                        success_count += 1
                        msg = f"[{idx}/{total}] OK: {path.name}"
                    else:
                        msg = f"[{idx}/{total}] FAILED: {path.name}"
                except Exception as exc:  # noqa: BLE001
                    logging.error("Batch submission error for %s: %s", path, exc)
                    msg = f"[{idx}/{total}] ERROR: {path.name}"

                def update_status(m: str = msg) -> None:
                    self.status_label.configure(text=m)

                self.after(0, update_status)

                if idx < total and between_delay > 0:
                    time.sleep(between_delay)

            def show_summary() -> None:
                messagebox.showinfo(
                    "Batch Submission Done",
                    f"Submitted {total} profiles. Successful: {success_count}, Failed: {total - success_count}.",
                )

            self.after(0, show_summary)

        threading.Thread(target=run_batch, daemon=True).start()


def launch_app() -> None:
    """
    Launcher function called from main.py.
    """
    app = StudentManagerApp()
    log_action(f"Application started. Profiles directory: {PROFILES_DIR}")
    app.mainloop()
    log_action("Application closed")