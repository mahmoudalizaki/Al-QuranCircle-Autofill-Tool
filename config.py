import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
from utils import CONFIG_DIR 
# -------------------
# Default settings
# -------------------
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "system",
    "teacher": {
        "name": "",
        "email": "",
        "max_students": 40,
        "phone": "",
        "institution": ""
    },
    "appearance": {
        "font_family": "Arial",
        "font_size": 12,
        "ui_scaling": 1.0
    },
    "backup": {
        "auto_backup": True,
        "backup_count": 5,
        "backup_path": ""
    },
    "reports": {
        "default_format": "pdf",
        "include_logo": True,
        "logo_path": ""
    },
    "google_form": {
        "form_url": "",
        "auto_submit": False,
        "retries": 3,
        "retry_delay": 5
    },
    "recent_files": [],
    "window_size": {
        "width": 1200,
        "height": 800,
        "maximized": False
    }
}
# -------------------
# Config Manager
# -------------------

class ConfigManager:
    _instance = None
    _config_path = CONFIG_DIR
    _settings_file = _config_path / "settings.json"
    
    def __init__(self):
        # This is just for initialization, the actual instance is managed by __new__
        pass

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._load_settings()
        return cls._instance

    @staticmethod
    def _deep_merge(default: dict, override: dict) -> dict:
        """Recursively merge override dict into default dict."""
        result = default.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = ConfigManager._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self._config_path.mkdir(parents=True, exist_ok=True)

    def _load_settings(self) -> None:
        self._ensure_config_dir()
        logging.debug(f"Loading settings from: {self._settings_file.absolute()}")
        
        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                logging.debug(f"Loaded settings from file")
                self._config = self._deep_merge(DEFAULT_SETTINGS.copy(), loaded)
            except Exception as e:
                logging.error(f"Error loading settings, using defaults: {e}")
                self._config = DEFAULT_SETTINGS.copy()
        else:
            logging.info("Settings file not found, creating with defaults")
            self._config = DEFAULT_SETTINGS.copy()
            self.save_settings()

    def save_settings(self):
        """Save settings to the settings file with error handling and verification."""
        try:
            self._ensure_config_dir()
            temp_file = self._settings_file.with_suffix('.tmp')
            
            # Write to a temporary file first
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            
            # Verify the file was written correctly
            if not temp_file.exists() or temp_file.stat().st_size == 0:
                raise IOError("Failed to write settings: file is empty or not created")
                
            # Replace the original file
            if self._settings_file.exists():
                self._settings_file.unlink()
            temp_file.rename(self._settings_file)
            
            # Verify the final file
            if not self._settings_file.exists():
                raise IOError("Failed to create settings file")
                
            logging.debug(f"Settings successfully saved to: {self._settings_file.absolute()}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            raise

    # --- Generic get/set ---
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, save: bool = True):
        try:
            keys = key.split(".")
            cfg = self._config
            for k in keys[:-1]:
                if k not in cfg or not isinstance(cfg[k], dict):
                    cfg[k] = {}
                cfg = cfg[k]
            
            # Only update and save if the value has changed
            if keys[-1] not in cfg or cfg[keys[-1]] != value:
                cfg[keys[-1]] = value
                if save:
                    return self.save_settings()
            return True
        except Exception as e:
            logging.error(f"Error setting config key '{key}': {e}")
            return False

    # --- Teacher helpers ---
    def get_teacher_info(self) -> Dict[str, Any]:
        return self.get("teacher", DEFAULT_SETTINGS["teacher"].copy())

    def set_teacher_info(
        self, 
        name: str = "", 
        email: str = "", 
        phone: str = "", 
        institution: str = "", 
        max_students: int = 30
    ) -> None:
        teacher = self.get_teacher_info()
        teacher.update({
            "name": name,
            "email": email,
            "phone": phone,
            "institution": institution,
            "max_students": max_students
        })
        self.set("teacher", teacher)
    # -------------------
    # Theme
    # -------------------
    def get_theme(self) -> str:
        return self.get("theme", DEFAULT_SETTINGS["theme"])

    def set_theme(self, theme: str) -> None:
        if theme in ["light", "dark", "system"]:
            self.set("theme", theme)

    # -------------------
    # Recent files
    # -------------------
    def add_recent_file(self, file_path: str) -> None:
        recent = self.get("recent_files", [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.set("recent_files", recent[:10])

    def get_recent_files(self) -> List[str]:
        return self.get("recent_files", [])

    def get_google_form_settings(self) -> Dict[str, Any]:
        """Safely get Google Form settings with defaults."""
        # First try to get from google_form.form_url, if empty try the top-level google_form_url
        form_url = self.get("google_form.form_url", "")
        if not form_url.strip():
            form_url = self.get("google_form_url", "")
            
        return {
            "form_url": form_url,
            "auto_submit": self.get("google_form.auto_submit", False),
            "retries": self.get("google_form.retries", 3),
            "retry_delay": self.get("google_form.retry_delay", 5)
        }

    def set_google_form_settings(self, form_url: str, auto_submit: bool, retries: int, retry_delay: int) -> bool:
        """Safely set Google Form settings."""
        try:
            settings = {
                "form_url": form_url.strip(),
                "auto_submit": bool(auto_submit),
                "retries": max(0, int(retries)),
                "retry_delay": max(1, int(retry_delay))
            }
            # Save to both locations for backward compatibility
            self.set("google_form_url", form_url.strip(), save=False)
            return self.set("google_form", settings, save=True)
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid Google Form settings: {e}")
            return False

# -------------------
# Global config instance
# -------------------
config = ConfigManager()
