"""
UI components for the reporting system.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from pathlib import Path
import webbrowser

import customtkinter as ctk
from tkcalendar import DateEntry
from utils import PROFILES_DIR
from .report_extractor import ReportCriteria, ReportExtractor, StudentReport
from .report_exporter import ReportExporter, OutputFormat

class ReportDialog(ctk.CTkToplevel):
    """Dialog for configuring and generating reports."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title("Generate Report")
        self.geometry("600x600")
        self.resizable(True, True)
        
        self.parent = parent
        self.report_extractor = ReportExtractor()
        self.report_exporter = ReportExporter()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        
        # Initialize UI
        self._setup_ui()
        
        # Center the dialog
        self.update_idletasks()
        self._center_window()
    
    def _center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="Generate Student Report",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Student selection
        student_frame = ctk.CTkFrame(content_frame)
        student_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        student_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(student_frame, text="Student:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.student_var = ctk.StringVar(value="All Students")
        self.student_dropdown = ctk.CTkOptionMenu(
            student_frame,
            variable=self.student_var,
            values=["All Students"] + self._get_student_list(),
            width=300
        )
        self.student_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Report type
        report_frame = ctk.CTkFrame(content_frame)
        report_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        report_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(report_frame, text="Report Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.report_type = ctk.StringVar(value="all")
        report_types = [
            ("All Reports", "all"),
            ("First Report in Period", "first"),
            ("Last Report in Period", "last"),
            ("Timeline (All Reports)", "timeline")
        ]
        
        for i, (text, value) in enumerate(report_types):
            rb = ctk.CTkRadioButton(
                report_frame,
                text=text,
                variable=self.report_type,
                value=value
            )
            rb.grid(row=i, column=1, padx=5, pady=2, sticky="w")
        
        # Date range
        date_frame = ctk.CTkFrame(content_frame)
        date_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(date_frame, text="Date Range:").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Month/Year selection
        current_month_name = datetime.now().strftime('%B')
        self.month_var = ctk.StringVar(value=current_month_name)
        self.year_var = ctk.StringVar(value=str(datetime.now().year))
        
        months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
        self._month_name_to_number = {name: num for num, name in months}
        years = list(range(2020, datetime.now().year + 2))
        
        ctk.CTkLabel(date_frame, text="Month:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        month_menu = ctk.CTkOptionMenu(
            date_frame,
            values=[name for _, name in months],
            variable=self.month_var,
            command=lambda _: self._update_date()
        )
        month_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(date_frame, text="Year:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        year_menu = ctk.CTkOptionMenu(
            date_frame,
            values=[str(y) for y in years],
            variable=self.year_var,
            command=lambda _: self._update_date()
        )
        year_menu.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Output format
        format_frame = ctk.CTkFrame(content_frame)
        format_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(format_frame, text="Output Format:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.format_var = ctk.StringVar(value="pdf")
        formats = ["PDF", "HTML"]
        
        for i, fmt in enumerate(formats):
            rb = ctk.CTkRadioButton(
                format_frame,
                text=fmt,
                variable=self.format_var,
                value=fmt.lower()
            )
            rb.grid(row=0, column=i+1, padx=10, pady=5, sticky="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, padx=20, pady=10, sticky="e")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="right", padx=5)
        
        generate_btn = ctk.CTkButton(
            button_frame,
            text="Generate Report",
            command=self._generate_report,
            width=150
        )
        generate_btn.pack(side="right", padx=5)

    def _get_student_list(self) -> List[str]:
        """Get list of all students with profiles."""
        profiles_dir = PROFILES_DIR
        students = set()
        
        for profile_file in profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    if 'student_name' in data:
                        students.add(data['student_name'])
            except (json.JSONDecodeError, OSError):
                continue
        
        return sorted(students)
    
    def _update_date(self):
        """Update date-related UI elements."""
        pass  # Can be used for dynamic updates if needed
    
    def _get_report_criteria(self) -> ReportCriteria:
        """Get report criteria from UI inputs."""
        student_name = None
        if self.student_var.get() != "All Students":
            student_name = self.student_var.get()
        
        report_type = self.report_type.get()
        
        # For timeline, we don't filter by month/year
        month = None
        year = None
        if report_type != 'timeline':
            month_name = self.month_var.get()
            month = self._month_name_to_number.get(month_name)
            year_str = self.year_var.get()
            try:
                year = int(year_str)
            except (TypeError, ValueError):
                year = None
        
        return ReportCriteria(
            student_name=student_name,
            month=month,
            year=year,
            mode=report_type if report_type != 'timeline' else 'all'
        )
    
    def _generate_report(self):
        """Generate the report based on current selections."""
        criteria = self._get_report_criteria()
        
        try:
            # Show loading indicator
            self.withdraw()
            
            # Generate report
            reports = self.report_extractor.get_reports(criteria)
            
            if not reports:
                tk.messagebox.showinfo("No Data", "No reports found matching the selected criteria.")
                self.deiconify()
                return
            
            # Export report
            output_format = self.format_var.get().lower()  # type: ignore
            output_path = self.report_exporter.export_report(
                reports=reports,
                output_format=output_format,  # type: ignore
                criteria=criteria,
                open_after=True
            )
            
            # Show success message
            tk.messagebox.showinfo(
                "Report Generated",
                f"Report successfully generated and saved to:\n{output_path}"
            )
            
            self.destroy()
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            self.deiconify()

def add_reporting_menu(parent: ctk.CTk) -> None:
    """Add reporting menu items to the main application.
    
    Args:
        parent: The main application window
    """
    if not hasattr(parent, 'menu'):
        # Create menu bar if it doesn't exist
        parent.menu = ctk.CTkMenu(parent)
        parent.config(menu=parent.menu)
    
    # Add Reports menu
    reports_menu = ctk.CTkMenu(parent.menu, tearoff=0)
    parent.menu.add_cascade(label="Reports", menu=reports_menu)
    
    # Add menu items
    reports_menu.add_command(
        label="Generate Report...",
        command=lambda: ReportDialog(parent)
    )
    
    reports_menu.add_separator()
    
    reports_menu.add_command(
        label="Open Reports Directory",
        command=lambda: webbrowser.open(f"file://{Path('reports').absolute()}")
    )
