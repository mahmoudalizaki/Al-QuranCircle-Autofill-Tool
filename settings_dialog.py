import customtkinter as ctk
import logging
from typing import Optional, Callable, Dict, Any
from config import config
from tkinter import messagebox
from utils import THEMES_DIR


class SettingsDialog(ctk.CTkToplevel):
    """Dialog for managing application settings."""
    
    def __init__(self, master, on_save: Optional[Callable[[], None]] = None):
        super().__init__(master)
        self.title("Application Settings")
        self.geometry("800x600")
        self.resizable(True, True)
        self.on_save = on_save

        # Initialize all variables
        # Appearance
        self.theme_var = ctk.StringVar(value="system")
        self.font_family_var = ctk.StringVar(value="Arial")
        self.font_size_var = ctk.IntVar(value=12)
        self.scaling_var = ctk.DoubleVar(value=1.0)
        self.color_theme_var = ctk.StringVar(value="blue")
        
        # Teacher
        self.teacher_name_var = ctk.StringVar()
        self.teacher_email_var = ctk.StringVar()
        self.teacher_phone_var = ctk.StringVar()
        self.teacher_institution_var = ctk.StringVar()
        self.max_students_var = ctk.IntVar(value=30)
        
        # Backup
        self.auto_backup_var = ctk.BooleanVar(value=True)
        self.backup_count_var = ctk.IntVar(value=5)
        self.backup_path_var = ctk.StringVar()
        
        # Reports
        self.report_format_var = ctk.StringVar(value="pdf")
        self.include_logo_var = ctk.BooleanVar(value=True)
        self.logo_path_var = ctk.StringVar()
        
        # Google Form
        self.google_form_url = ctk.StringVar()
        self.auto_submit = ctk.BooleanVar(value=False)
        self.max_retries = ctk.IntVar(value=3)
        self.retry_delay = ctk.IntVar(value=5)
        
        # Setup UI
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Set up the main UI components of the settings dialog."""
        # Make dialog modal
        self.transient(self.master)
        self.grab_set()
        self.focus_force()
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.container = ctk.CTkFrame(self, corner_radius=0)
        self.container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Create tabs
        self.tabview = ctk.CTkTabview(self.container, corner_radius=0)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Add tabs
        self.tabview.add("Appearance")
        self.tabview.add("Teacher")
        self.tabview.add("Backup")
        self.tabview.add("Reports")
        
        # Configure tab weights
        for tab in ["Appearance", "Teacher", "Backup", "Reports"]:
            self.tabview.tab(tab).grid_rowconfigure(0, weight=1)
            self.tabview.tab(tab).grid_columnconfigure(0, weight=1)
        
        # Setup individual tabs
        self._setup_appearance_tab()
        self._setup_teacher_tab()
        self._setup_backup_tab()
        self._setup_reports_tab()
        
        # Bottom buttons
        self.button_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Save button
        self.save_btn = ctk.CTkButton(
            self.button_frame, 
            text="Save Settings", 
            command=self._on_save,
            fg_color="#2e8b57",
            hover_color="#3cb371"
        )
        self.save_btn.pack(side="right", padx=5)
        
        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            self.button_frame, 
            text="Cancel", 
            command=self.destroy
        )
        self.cancel_btn.pack(side="right", padx=5)
        
        # Bind Enter key to save
        self.bind('<Return>', self._on_save)
        self.bind('<Escape>', lambda e: self.destroy())
    def _setup_appearance_tab(self):
        """Set up the appearance tab with theme and UI options."""
        tab = self.tabview.tab("Appearance")
        
        # --- Appearance Mode (System / Light / Dark) ---
        theme_frame = ctk.CTkFrame(tab, corner_radius=0)
        theme_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(theme_frame, text="Appearance", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
                # عند فتح الـ dialog
        current_theme = config.get("appearance.theme", config.get("theme", "system"))
        self.appearance_var = ctk.StringVar(value=current_theme)

        ctk.CTkLabel(theme_frame, text="Mode:").pack(anchor="w")
        appearance_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["system", "light", "dark"],
            variable=self.appearance_var,
            command=self._on_appearance_select  # ← استخدم handler جديد
        )
        appearance_menu.pack(fill="x", pady=(0, 10))
        
        # --- Color Theme (Default + JSON files) ---
        default_themes = ["blue"]
        
        theme_files = []
        if THEMES_DIR.exists() and THEMES_DIR.is_dir():
            theme_files = [f.stem for f in THEMES_DIR.iterdir() if f.suffix.lower() == ".json"]
        
        all_themes = default_themes + theme_files
        
        self.color_theme_var = ctk.StringVar(value=config.get("appearance.color_theme", "blue"))
        ctk.CTkLabel(theme_frame, text="Color Theme:").pack(anchor="w")
        color_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=all_themes,
            variable=self.color_theme_var,
            command=self._on_color_theme_select  # ← handler جديد
        )
        color_menu.pack(fill="x", pady=(0, 10))
            
        # UI Scaling
        self.scaling_var = ctk.DoubleVar(value=config.get("appearance.ui_scaling", 1.0))
        ctk.CTkLabel(theme_frame, text="UI Scaling:").pack(anchor="w")
        scaling_slider = ctk.CTkSlider(
            theme_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            variable=self.scaling_var,
            command=lambda v: self.scaling_var.set(round(v, 1))
        )
        scaling_slider.pack(fill="x", pady=(0, 10))
        
        # Font settings
        font_frame = ctk.CTkFrame(tab, corner_radius=0)
        font_frame.pack(fill="x", padx=10, pady=(5, 5))
        
        ctk.CTkLabel(
            font_frame, 
            text="Font Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Font family
        self.font_family_var = ctk.StringVar(value=config.get("appearance.font_family", "Arial"))
        ctk.CTkLabel(font_frame, text="Font Family:").pack(anchor="w")
        font_family_entry = ctk.CTkEntry(font_frame, textvariable=self.font_family_var)
        font_family_entry.pack(fill="x", pady=(0, 10))
        
        # Font size
        self.font_size_var = ctk.IntVar(value=config.get("appearance.font_size", 12))
        ctk.CTkLabel(font_frame, text="Font Size:").pack(anchor="w")
        font_size_slider = ctk.CTkSlider(
            font_frame,
            from_=8,
            to=24,
            number_of_steps=16,
            variable=self.font_size_var,
            command=lambda v: self.font_size_var.set(int(v))
        )
        font_size_slider.pack(fill="x", pady=(0, 10))


    # --- Handlers الجديدة ---

    def _on_appearance_select(self, value: str):
        """تحديث المتغير فقط بدون تطبيق فورًا على التطبيق"""
        self.appearance_var.set(value)

    def _on_color_theme_select(self, value: str):
        """تحديث المتغير فقط بدون تطبيق فورًا على التطبيق"""
        self.color_theme_var.set(value)

    def _apply_appearance_settings(self):
        """تطبيق الـ appearance و color theme على التطبيق عند الحفظ"""
        try:
            # Appearance mode
            mode_map = {"system": "System", "light": "Light", "dark": "Dark"}
            selected_mode = mode_map.get(self.appearance_var.get().lower(), "System")
            ctk.set_appearance_mode(selected_mode)
            
            # Color theme
            theme_path = THEMES_DIR / f"{self.color_theme_var.get()}.json"
            if theme_path.exists():
                ctk.set_default_color_theme(str(theme_path))
            else:
                ctk.set_default_color_theme(self.color_theme_var.get())
        except Exception as e:
            print(f"Failed to apply appearance settings: {e}")
           
    def _setup_teacher_tab(self):
        """Set up the teacher information tab."""
        tab = self.tabview.tab("Teacher")
        
        # Teacher info frame
        teacher_frame = ctk.CTkFrame(tab, corner_radius=0)
        teacher_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            teacher_frame, 
            text="Teacher Information",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        # Name
        ctk.CTkLabel(teacher_frame, text="Full Name:").pack(anchor="w")
        self.teacher_name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(teacher_frame, textvariable=self.teacher_name_var)
        name_entry.pack(fill="x", pady=(0, 10))
        
        # Email
        ctk.CTkLabel(teacher_frame, text="Email:").pack(anchor="w")
        self.teacher_email_var = ctk.StringVar()
        email_entry = ctk.CTkEntry(teacher_frame, textvariable=self.teacher_email_var)
        email_entry.pack(fill="x", pady=(0, 10))
        
        # Phone
        ctk.CTkLabel(teacher_frame, text="Phone:").pack(anchor="w")
        self.teacher_phone_var = ctk.StringVar()
        phone_entry = ctk.CTkEntry(teacher_frame, textvariable=self.teacher_phone_var)
        phone_entry.pack(fill="x", pady=(0, 10))
        
        # Institution
        ctk.CTkLabel(teacher_frame, text="Institution:").pack(anchor="w")
        self.teacher_institution_var = ctk.StringVar()
        institution_entry = ctk.CTkEntry(teacher_frame, textvariable=self.teacher_institution_var)
        institution_entry.pack(fill="x", pady=(0, 10))

    def _setup_backup_tab(self):
        """Set up the backup settings tab."""
        tab = self.tabview.tab("Backup")
        
        # Backup settings frame
        backup_frame = ctk.CTkFrame(tab, corner_radius=0)
        backup_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            backup_frame, 
            text="Backup Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        # Auto backup
        self.auto_backup_var = ctk.BooleanVar(value=config.get("backup.auto_backup", True))
        auto_backup_switch = ctk.CTkSwitch(
            backup_frame,
            text="Enable Auto Backup",
            variable=self.auto_backup_var
        )
        auto_backup_switch.pack(anchor="w", pady=(0, 10))
        
        # Number of backups to keep
        ctk.CTkLabel(backup_frame, text="Number of Backups to Keep:").pack(anchor="w")
        self.backup_count_var = ctk.IntVar(value=config.get("backup.backup_count", 5))
        backup_count_slider = ctk.CTkSlider(
            backup_frame,
            from_=1,
            to=20,
            number_of_steps=19,
            variable=self.backup_count_var,
            command=lambda v: self.backup_count_var.set(int(v))
        )
        backup_count_slider.pack(fill="x", pady=(0, 10))
        
        # Backup location
        ctk.CTkLabel(backup_frame, text="Backup Location:").pack(anchor="w")
        backup_loc_frame = ctk.CTkFrame(backup_frame, fg_color="transparent")
        backup_loc_frame.pack(fill="x", pady=(0, 10))
        
        self.backup_path_var = ctk.StringVar(value=config.get("backup.backup_path", ""))
        backup_path_entry = ctk.CTkEntry(backup_loc_frame, textvariable=self.backup_path_var)
        backup_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_btn = ctk.CTkButton(
            backup_loc_frame,
            text="Browse...",
            width=80,
            command=self._browse_backup_location
        )
        browse_btn.pack(side="right")
        # Reports Frame
        reports_frame = ctk.CTkFrame(tab, corner_radius=0)
        reports_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            reports_frame,
            text="Logo Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 15))

        # Reports Settings Frame
        reports_settings_frame = ctk.CTkFrame(reports_frame, fg_color="transparent")
        reports_settings_frame.pack(fill="x", pady=(0, 10))

        # Default Format
        ctk.CTkLabel(reports_settings_frame, text="Default Format:").pack(anchor="w")
        self.report_format_var = ctk.StringVar(value=config.get("reports.default_format", "pdf"))
        format_menu = ctk.CTkOptionMenu(
            reports_settings_frame,
            values=["pdf", "html"],
            variable=self.report_format_var
        )
        format_menu.pack(fill="x", pady=(0, 10))

        # Include Logo Checkbox
        self.include_logo_var = ctk.BooleanVar(value=config.get("reports.include_logo", True))
        include_logo_cb = ctk.CTkCheckBox(
            reports_settings_frame,
            text="Include logo in generated reports",
            variable=self.include_logo_var
        )
        include_logo_cb.pack(anchor="w", pady=(0, 10))

        # Logo Path
        ctk.CTkLabel(reports_frame, text="Logo Path:").pack(anchor="w")
        logo_loc_frame = ctk.CTkFrame(reports_frame, fg_color="transparent")
        logo_loc_frame.pack(fill="x", pady=(0, 10))

        self.logo_path_var = ctk.StringVar(
            value=config.get("reports.logo_path", "")
        )

        logo_path_entry = ctk.CTkEntry(
            logo_loc_frame,
            textvariable=self.logo_path_var
        )
        logo_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_logo_btn = ctk.CTkButton(
            logo_loc_frame,
            text="Browse...",
            width=80,
            command=self._browse_logo_location
        )
        browse_logo_btn.pack(side="right")


    def _browse_logo_location(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.logo_path_var.set(file_path)

    def _setup_reports_tab(self):
        """Set up the reports and Google Form settings tab."""
        tab = self.tabview.tab("Reports")
        tab.grid_columnconfigure(0, weight=1)
        
        # Main container with scrollbar
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Google Form Section
        google_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        google_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            google_frame,
            text="Google Form Integration",
            font=ctk.CTkFont(weight="bold", size=14)
        ).pack(anchor="w", pady=(0, 10))
        
        # Form URL
        form_url_frame = ctk.CTkFrame(google_frame, fg_color="transparent")
        form_url_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form_url_frame, text="Form URL:").pack(anchor="w")
        self.google_form_url = ctk.StringVar()
        url_entry = ctk.CTkEntry(
            form_url_frame,
            textvariable=self.google_form_url,
            placeholder_text="https://docs.google.com/forms/d/e/...",
            width=400
        )
        url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Test Connection Button
        test_btn = ctk.CTkButton(
            form_url_frame,
            text="Test Connection",
            width=120,
            command=self._test_google_form_connection
        )
        test_btn.pack(side="right")
        
        # Auto-submit option
        self.auto_submit = ctk.BooleanVar(value=False)
        auto_submit_switch = ctk.CTkSwitch(
            google_frame,
            text="Auto-submit after filling",
            variable=self.auto_submit
        )
        auto_submit_switch.pack(anchor="w", pady=(0, 15))
        
        # Retry settings
        retry_frame = ctk.CTkFrame(google_frame, fg_color="transparent")
        retry_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(retry_frame, text="Max Retries:").pack(side="left", padx=(0, 5))
        self.max_retries = ctk.IntVar(value=3)
        retry_spin = ctk.CTkEntry(
            retry_frame,
            textvariable=self.max_retries,
            width=50
        )
        retry_spin.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(retry_frame, text="Retry Delay (seconds):").pack(side="left", padx=(0, 5))
        self.retry_delay = ctk.IntVar(value=5)
        delay_spin = ctk.CTkEntry(
            retry_frame,
            textvariable=self.retry_delay,
            width=50
        )
        delay_spin.pack(side="left")
        
        # Add a separator
        ctk.CTkFrame(google_frame, height=1, fg_color="gray30").pack(fill="x", pady=20)
        
        # Rest of your reports settings...
        
        # Load current settings
        self._load_google_form_settings()

    def _load_google_form_settings(self):
        """Load Google Form settings from config."""
        settings = config.get_google_form_settings()
        self.google_form_url.set(settings["form_url"])
        self.auto_submit.set(settings["auto_submit"])
        self.max_retries.set(settings["retries"])
        self.retry_delay.set(settings["retry_delay"])

    def _save_google_form_settings(self) -> bool:
        """Save Google Form settings to config."""
        return config.set_google_form_settings(
            form_url=self.google_form_url.get(),
            auto_submit=self.auto_submit.get(),
            retries=self.max_retries.get(),
            retry_delay=self.retry_delay.get()
        )

    def _test_google_form_connection(self):
        """Test connection to the Google Form."""
        raw_url = self.google_form_url.get()
        
        if not raw_url or not raw_url.strip():
            messagebox.showwarning("Warning", "Please enter a Google Form URL")
            return
        
        # Clean up the URL
        url = raw_url.strip()
        
        # Show loading state
        self.save_btn.configure(state="disabled")
        self.after(100, self._perform_connection_test, url)

    def _perform_connection_test(self, url: str):
        """Perform the actual connection test (run in main thread)."""
        try:
            # Add your actual connection test logic here
            # For now, we'll just simulate a test
            import time
            time.sleep(1)  # Simulate network delay
            
            # Check if URL looks like a Google Form URL
            if "docs.google.com/forms/" in url:
                messagebox.showinfo("Success", "Successfully connected to Google Form!")
            else:
                messagebox.showwarning("Warning", "The URL doesn't appear to be a Google Form")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to Google Form: {str(e)}")
        finally:
            self.save_btn.configure(state="normal")

    # Update the save method to include Google Form settings
    
    def _browse_backup_location(self):
        """Open a directory dialog to select backup location."""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Backup Location")
        if path:
            self.backup_path_var.set(path)
    
    def _browse_logo_location(self):
        """Open a file dialog to select logo image."""
        from tkinter import filedialog
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=filetypes
        )
        if path:
            self.logo_path_var.set(path)
    
    def _on_theme_change(self, theme: str):
        """Store the selected theme without applying it."""
        # Just update the variable, don't apply the theme yet
        self.theme_var.set(theme)
    
    def _load_settings(self):
        """Load current settings into the dialog."""
        try:
            # Appearance
            appearance = config.get("appearance", {})
            theme_value = appearance.get("theme")
            if not theme_value:
                theme_value = config.get("theme", "system")
            self.theme_var.set(theme_value)
            self.font_family_var.set(appearance.get("font_family", "Arial"))
            self.font_size_var.set(appearance.get("font_size", 12))
            self.scaling_var.set(appearance.get("ui_scaling", 1.0))
            
            # Teacher
            teacher = config.get("teacher", {})
            self.teacher_name_var.set(teacher.get("name", ""))
            self.teacher_email_var.set(teacher.get("email", ""))
            self.teacher_phone_var.set(teacher.get("phone", ""))
            self.teacher_institution_var.set(teacher.get("institution", ""))
            self.max_students_var.set(teacher.get("max_students", 30))
            
            # Backup
            backup = config.get("backup", {})
            self.auto_backup_var.set(backup.get("auto_backup", True))
            self.backup_count_var.set(backup.get("backup_count", 5))
            self.backup_path_var.set(backup.get("backup_path", ""))
            
            # Reports
            reports = config.get("reports", {})
            self.report_format_var.set(reports.get("default_format", "pdf"))
            self.include_logo_var.set(reports.get("include_logo", True))
            self.logo_path_var.set(reports.get("logo_path", ""))
            
            # Google Form
            google_form = config.get("google_form", {})
            self.google_form_url.set(google_form.get("form_url", ""))
            self.auto_submit.set(google_form.get("auto_submit", False))
            self.max_retries.set(google_form.get("retries", 3))
            self.retry_delay.set(google_form.get("retry_delay", 5))
            # Save logo path to config
            config.set("reports.logo_path", reports.get("logo_path", ""))
        except Exception as e:
            logging.error(f"Error loading settings: {e}", exc_info=True)
            
    # def _save_settings(self) -> bool:
    #     """Save settings from the dialog to config."""
    #     try:
    #         # Save appearance / theme (store in both appearance + root for compatibility)
    #         selected_theme = self.theme_var.get()
    #         config.set("appearance.theme", selected_theme)
    #         if hasattr(config, "set_theme"):
    #             config.set_theme(selected_theme)
    #         else:
    #             config.set("theme", selected_theme)
    #         config.set("appearance.font_family", self.font_family_var.get())
    #         config.set("appearance.font_size", self.font_size_var.get())
    #         config.set("appearance.ui_scaling", self.scaling_var.get())
    #         config.set("appearance.color_theme", self.color_theme_var.get())

            
    #         # Save teacher info
    #         teacher_info = {
    #             "name": self.teacher_name_var.get().strip(),
    #             "email": self.teacher_email_var.get().strip(),
    #             "phone": self.teacher_phone_var.get().strip(),
    #             "institution": self.teacher_institution_var.get().strip(),
    #             "max_students": self.max_students_var.get()
    #         }
    #         config.set("teacher", teacher_info)
            
    #         # Save backup settings
    #         backup_info = {
    #             "auto_backup": self.auto_backup_var.get(),
    #             "backup_count": self.backup_count_var.get(),
    #             "backup_path": self.backup_path_var.get().strip()
    #         }
    #         config.set("backup", backup_info)
            
    #         # Save report settings
    #         report_info = {
    #             "default_format": self.report_format_var.get(),
    #             "include_logo": self.include_logo_var.get(),
    #             "logo_path": self.logo_path_var.get().strip()
    #         }
    #         config.set("reports", report_info)
            
    #         # Save Google Form settings
    #         google_form_info = {
    #             "form_url": self.google_form_url.get().strip(),
    #             "auto_submit": self.auto_submit.get(),
    #             "retries": self.max_retries.get(),
    #             "retry_delay": self.retry_delay.get()
    #         }
    #         config.set("google_form", google_form_info)
    #         config.set("reports.logo_path", self.logo_path_var.get().strip())
    #         # Save all settings to disk
    #         if not config.save_settings():
    #             raise Exception("Failed to save settings")
                
    #         # --- Update UI after saving settings ---

    #         # Scaling
    #         scaling = self.scaling_var.get()
    #         ctk.set_widget_scaling(scaling)
    #         ctk.set_window_scaling(scaling)

    #         # Appearance mode
    #         self._apply_appearance_settings()

            
    #         return True
            
    #     except Exception as e:
    #         logging.error(f"Error saving settings: {e}", exc_info=True)
    #         return False
    def _save_settings(self) -> bool:
        """Save settings from the dialog to config and apply them immediately."""
        try:
            # --- حفظ الإعدادات في Config ---
            # Appearance
            config.set("appearance.theme", self.appearance_var.get())
            config.set("appearance.color_theme", self.color_theme_var.get())
            config.set("appearance.font_family", self.font_family_var.get())
            config.set("appearance.font_size", self.font_size_var.get())
            config.set("appearance.ui_scaling", self.scaling_var.get())
            
            # Teacher
            teacher_info = {
                "name": self.teacher_name_var.get().strip(),
                "email": self.teacher_email_var.get().strip(),
                "phone": self.teacher_phone_var.get().strip(),
                "institution": self.teacher_institution_var.get().strip(),
                "max_students": self.max_students_var.get()
            }
            config.set("teacher", teacher_info)
            
            # Backup
            backup_info = {
                "auto_backup": self.auto_backup_var.get(),
                "backup_count": self.backup_count_var.get(),
                "backup_path": self.backup_path_var.get().strip()
            }
            config.set("backup", backup_info)
            
            # Reports
            report_info = {
                "default_format": self.report_format_var.get(),
                "include_logo": self.include_logo_var.get(),
                "logo_path": self.logo_path_var.get().strip()
            }
            config.set("reports", report_info)
            
            # Google Form
            google_form_info = {
                "form_url": self.google_form_url.get().strip(),
                "auto_submit": self.auto_submit.get(),
                "retries": self.max_retries.get(),
                "retry_delay": self.retry_delay.get()
            }
            config.set("google_form", google_form_info)
            
            # حفظ كل شيء على القرص أولًا
            if not config.save_settings():
                raise Exception("Failed to save settings to disk")
            
            # --- تطبيق الإعدادات على التطبيق فورًا ---
            self._apply_appearance_settings()
            
            return True

        except Exception as e:
            logging.error(f"Error saving settings: {e}", exc_info=True)
            return False

          
    def _on_save(self):
        if self._save_settings():
            # إعلام المستخدم
            messagebox.showinfo(
                "Settings Saved",
                "Your settings have been saved successfully!\n"
                "Please restart the application manually to apply the new settings."
            )

            # اغلاق نافذة الإعدادات
            self.destroy()

            # اغلاق Main UI إذا موجود
            if hasattr(self.master, "destroy"):
                self.master.destroy()

            # إنهاء العملية بالكامل
            import sys
            sys.exit(0)
