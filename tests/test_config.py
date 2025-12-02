"""Unit tests for config module."""
import unittest
import tempfile
import shutil
import json
from pathlib import Path

# Import the module to test
import sys
from pathlib import Path as PathLib

# Add parent directory to path
sys.path.insert(0, str(PathLib(__file__).parent.parent))

from config import ConfigManager, DEFAULT_SETTINGS


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager singleton and methods."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset singleton instance
        ConfigManager._instance = None
        # Create temporary config directory
        self.temp_dir = Path(tempfile.mkdtemp())
        ConfigManager._config_path = self.temp_dir / "config"
        ConfigManager._settings_file = ConfigManager._config_path / "settings.json"
    
    def tearDown(self):
        """Clean up test environment."""
        # Reset singleton
        ConfigManager._instance = None
        # Clean up temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_singleton_pattern(self):
        """Test that ConfigManager is a singleton."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        self.assertIs(config1, config2, "ConfigManager should be a singleton")
    
    def test_default_settings(self):
        """Test that default settings are loaded."""
        config = ConfigManager()
        theme = config.get("theme")
        self.assertEqual(theme, DEFAULT_SETTINGS["theme"])
    
    def test_get_set_methods(self):
        """Test get and set methods."""
        config = ConfigManager()
        
        # Test setting a value
        config.set("test_key", "test_value")
        value = config.get("test_key")
        self.assertEqual(value, "test_value")
        
        # Test default value
        value = config.get("non_existent_key", "default")
        self.assertEqual(value, "default")
    
    def test_nested_keys(self):
        """Test getting and setting nested keys."""
        config = ConfigManager()
        
        # Set nested value
        config.set("teacher.name", "Test Teacher")
        name = config.get("teacher.name")
        self.assertEqual(name, "Test Teacher")
        
        # Get nested dict
        teacher_info = config.get("teacher")
        self.assertIsInstance(teacher_info, dict)
        self.assertEqual(teacher_info.get("name"), "Test Teacher")
    
    def test_teacher_info_methods(self):
        """Test teacher info getter and setter."""
        config = ConfigManager()
        
        # Set teacher info
        config.set_teacher_info(
            name="Test Teacher",
            email="teacher@example.com",
            phone="123-456-7890",
            institution="Test School",
            max_students=50
        )
        
        # Get teacher info
        info = config.get_teacher_info()
        self.assertEqual(info["name"], "Test Teacher")
        self.assertEqual(info["email"], "teacher@example.com")
        self.assertEqual(info["phone"], "123-456-7890")
        self.assertEqual(info["institution"], "Test School")
        self.assertEqual(info["max_students"], 50)
    
    def test_theme_methods(self):
        """Test theme getter and setter."""
        config = ConfigManager()
        
        # Set theme
        config.set_theme("dark")
        theme = config.get_theme()
        self.assertEqual(theme, "dark")
        
        # Get theme (should return default if not set)
        config.set_theme("light")
        theme = config.get_theme()
        self.assertEqual(theme, "light")
    
    def test_recent_files(self):
        """Test recent files management."""
        config = ConfigManager()
        
        # Add recent files
        config.add_recent_file("file1.json")
        config.add_recent_file("file2.json")
        config.add_recent_file("file3.json")
        
        # Get recent files
        recent = config.get_recent_files()
        self.assertIsInstance(recent, list)
        self.assertIn("file1.json", recent)
        self.assertIn("file2.json", recent)
        self.assertIn("file3.json", recent)
    
    def test_google_form_settings(self):
        """Test Google Form settings."""
        config = ConfigManager()
        
        # Set Google Form settings
        success = config.set_google_form_settings(
            form_url="https://forms.google.com/test",
            auto_submit=True,
            retries=5,
            retry_delay=10
        )
        self.assertTrue(success)
        
        # Get Google Form settings
        settings = config.get_google_form_settings()
        self.assertEqual(settings["form_url"], "https://forms.google.com/test")
        self.assertEqual(settings["auto_submit"], True)
        self.assertEqual(settings["retries"], 5)
        self.assertEqual(settings["retry_delay"], 10)


if __name__ == "__main__":
    unittest.main()

