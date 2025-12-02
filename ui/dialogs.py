"""Dialog classes for the UI module."""
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import customtkinter as ctk
from tkinter import messagebox

from utils import load_all_profiles, PROFILES_DIR
from automation import submit_profile_to_form
from config import config


class ProfileHistoryDialog(ctk.CTkToplevel):
    """Dialog for viewing profile history."""
    
    def __init__(self, master, profile_path: Path, entries: List[Dict[str, Any]]) -> None:
        super().__init__(master)
        self.master = master
        self.title(f"History - {profile_path.name}")
        self.geometry("1000x700")
        self.minsize(900, 600)
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
        self.tabview.set("Changes")

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
        """Populate the revisions list."""
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
        """Show details for a specific entry."""
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

    def __init__(self, master) -> None:
        super().__init__(master)
        self.master = master
        self.title("Batch Submit Profiles")
        self.geometry("600x500")
        self.resizable(True, True)

        # Make dialog behave like a proper top-level over the main UI
        self.transient(master)
        self.lift()
        self.focus_force()
        self.grab_set()

        self.profile_rows: List[Dict[str, Any]] = []

        # Top configuration frame
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Retries
        retries_label = ctk.CTkLabel(config_frame, text="Retries:")
        retries_label.grid(row=0, column=0, padx=(5, 2), pady=5, sticky="e")
        self.retries_entry = ctk.CTkEntry(config_frame, width=60)
        self.retries_entry.insert(0, self.master.retries_entry.get() or "3")
        self.retries_entry.grid(row=0, column=1, padx=(2, 10), pady=5, sticky="w")

        # Delay between retries (per profile)
        delay_label = ctk.CTkLabel(config_frame, text="Delay per attempt (s):")
        delay_label.grid(row=0, column=2, padx=(5, 2), pady=5, sticky="e")
        self.retry_delay_entry = ctk.CTkEntry(config_frame, width=60)
        self.retry_delay_entry.insert(0, self.master.retry_delay_entry.get() or "5")
        self.retry_delay_entry.grid(row=0, column=3, padx=(2, 10), pady=5, sticky="w")

        # Sleep between profiles
        between_label = ctk.CTkLabel(config_frame, text="Delay between profiles (s):")
        between_label.grid(row=1, column=0, padx=(5, 2), pady=5, sticky="e")
        self.between_profiles_entry = ctk.CTkEntry(config_frame, width=80)
        self.between_profiles_entry.insert(0, "3")
        self.between_profiles_entry.grid(row=1, column=1, padx=(2, 10), pady=5, sticky="w")

        # Switches copied from main app state
        self.send_copy_switch = ctk.CTkSwitch(
            config_frame,
            text="Send me a copy",
        )
        if bool(self.master.send_copy_switch.get()):
            self.send_copy_switch.select()
        self.send_copy_switch.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.show_browser_switch = ctk.CTkSwitch(
            config_frame,
            text="Show browser",
        )
        if bool(self.master.show_browser_switch.get()):
            self.show_browser_switch.select()
        self.show_browser_switch.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.use_extension_switch = ctk.CTkSwitch(
            config_frame,
            text="Use extension",
        )
        if bool(self.master.use_extension_switch.get()):
            self.use_extension_switch.select()
        self.use_extension_switch.grid(row=2, column=0, padx=5, pady=5, sticky="w", columnspan=2)

        # Scrollable list of profiles
        list_frame = ctk.CTkScrollableFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        profiles = load_all_profiles()

        # Order by date (most recent first) and group by date as categories
        def _date_key(profile: Dict[str, Any]) -> str:
            return str(profile.get("date", ""))

        ordered_profiles = sorted(profiles, key=_date_key, reverse=True)

        current_date = None
        for profile in ordered_profiles:
            file_path_str = profile.get("_file")
            if not file_path_str:
                continue

            path = Path(file_path_str)
            name = profile.get("student_name", "Unknown")
            teacher = profile.get("teacher_name", "")
            date = profile.get("date", "Unknown Date")

            # Date header row (category)
            if date != current_date:
                current_date = date
                date_label = ctk.CTkLabel(
                    list_frame,
                    text=str(current_date),
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w",
                )
                date_label.pack(fill="x", padx=5, pady=(6, 2))

            header_text = f"{name} | {teacher}" if teacher else name

            row_frame = ctk.CTkFrame(list_frame)
            row_frame.pack(fill="x", padx=5, pady=3)

            header = ctk.CTkFrame(row_frame)
            header.pack(fill="x")

            include_var = ctk.BooleanVar(value=False)
            include_cb = ctk.CTkCheckBox(header, text="", variable=include_var)
            include_cb.grid(row=0, column=0, padx=(5, 5))

            toggle_btn = ctk.CTkButton(
                header,
                text="\u25b6",
                width=24,
                command=lambda rf=row_frame: self._toggle_details(rf),
            )
            toggle_btn.grid(row=0, column=1, padx=(0, 5))

            label = ctk.CTkLabel(header, text=header_text, anchor="w")
            label.grid(row=0, column=2, sticky="ew", padx=(0, 5))
            header.grid_columnconfigure(2, weight=1)

            details = ctk.CTkFrame(row_frame)
            details.pack(fill="x", padx=5, pady=(3, 5))
            details.grid_columnconfigure(1, weight=1)

            def add_detail_row(r: int, title: str, value: str) -> None:
                t_label = ctk.CTkLabel(details, text=f"{title}:")
                t_label.grid(row=r, column=0, sticky="w", padx=(5, 5), pady=1)
                v_label = ctk.CTkLabel(details, text=value, anchor="w")
                v_label.grid(row=r, column=1, sticky="w", padx=(0, 5), pady=1)

            add_detail_row(0, "Quran Surah", profile.get("quran_surah", ""))
            add_detail_row(1, "Noor Page", profile.get("noor_page", ""))
            add_detail_row(2, "Tajweed", profile.get("tajweed_rules", ""))
            add_detail_row(3, "Topic", profile.get("topic", ""))

            # Start collapsed
            details.pack_forget()

            self.profile_rows.append(
                {
                    "path": path,
                    "include_var": include_var,
                    "details_frame": details,
                    "row_frame": row_frame,
                }
            )

        # Bottom controls
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(bottom_frame, text="Select profiles and click 'Send Selected'.")
        self.status_label.pack(side="left", padx=5)

        start_button = ctk.CTkButton(
            bottom_frame,
            text="Send Selected",
            command=self.start_batch_submission,
        )
        start_button.pack(side="right", padx=5)

    def _toggle_details(self, row_frame: ctk.CTkFrame) -> None:
        """Toggle visibility of profile details."""
        for row in self.profile_rows:
            if row["row_frame"] is row_frame:
                details = row["details_frame"]
                if details.winfo_manager():
                    details.pack_forget()
                else:
                    details.pack(fill="x", padx=5, pady=(3, 5))
                break

    def start_batch_submission(self) -> None:
        """Start batch submission of selected profiles."""
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
            form_url = config.get("form_url")
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

