"""Unit tests for utils module."""
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import the module to test
import sys
from pathlib import Path as PathLib

# Add parent directory to path
sys.path.insert(0, str(PathLib(__file__).parent.parent))

from utils import (
    validate_email,
    sanitize_filename,
    validate_profile_data,
    sanitize_string,
    save_profile,
    load_profile,
    delete_profile,
    PROFILES_DIR,
)


class TestValidationFunctions(unittest.TestCase):
    """Test input validation functions."""
    
    def test_validate_email_valid(self):
        """Test valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.com",
            "user_123@test-domain.com",
        ]
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(validate_email(email), f"{email} should be valid")
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user@domain",
            "user space@example.com",
            "",
            None,
        ]
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(validate_email(email), f"{email} should be invalid")
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        test_cases = [
            ("normal_file.json", "normal_file.json"),
            ("../../etc/passwd", "passwd"),
            # Note: Path().name treats both / and \ as path separators,
            # so 'file<>:"/\\|?*.json' becomes just the part after the last separator
            ("file<>:\"/\\|?*.json", "___.json"),  # Both / and \ are separators
            ("file<>:\"/|?*.json", "___.json"),  # / is a separator, extracts '|?*.json'
            ("file<>:|?*.json", "file______.json"),  # No separators, all dangerous chars replaced
            ("file with spaces.json", "file with spaces.json"),
            ("", "unnamed"),
            (None, "unnamed"),
            ("a" * 300, "a" * 255),  # Test length limit
        ]
        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = sanitize_filename(input_name)
                self.assertEqual(result, expected)
    
    def test_validate_profile_data_valid(self):
        """Test valid profile data."""
        valid_data = {
            "student_name": "John Doe",
            "email": "john@example.com",
            "date": "01/12/2024",
            "teacher_name": "Teacher Name",
        }
        is_valid, error = validate_profile_data(valid_data)
        self.assertTrue(is_valid, f"Should be valid: {error}")
        self.assertIsNone(error)
    
    def test_validate_profile_data_missing_student_name(self):
        """Test profile data without student name."""
        invalid_data = {
            "email": "john@example.com",
        }
        is_valid, error = validate_profile_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("Student name is required", error)
    
    def test_validate_profile_data_invalid_email(self):
        """Test profile data with invalid email."""
        invalid_data = {
            "student_name": "John Doe",
            "email": "invalid-email",
        }
        is_valid, error = validate_profile_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("Invalid email format", error)
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        test_cases = [
            ("normal string", "normal string"),
            ("string with\0null\1bytes", "string withnullbytes"),
            ("  trimmed  ", "trimmed"),
            (None, ""),
            (123, "123"),
        ]
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = sanitize_string(input_val)
                self.assertEqual(result, expected)


class TestProfileManagement(unittest.TestCase):
    """Test profile management functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for profiles
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_profiles_dir = PROFILES_DIR
        # Note: We can't easily mock PROFILES_DIR without refactoring,
        # so these tests will use the actual directory
        # In a production test suite, you'd use dependency injection or mocking
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary directory if created
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_profile(self):
        """Test saving and loading a profile."""
        profile_data = {
            "student_name": "Test Student",
            "email": "test@example.com",
            "date": "01/12/2024",
            "teacher_name": "Test Teacher",
        }
        
        # Validate first
        is_valid, error = validate_profile_data(profile_data)
        self.assertTrue(is_valid, f"Profile should be valid: {error}")
        
        # Save profile
        profile_path = save_profile(profile_data)
        self.assertTrue(profile_path.exists(), "Profile file should be created")
        
        # Load profile
        loaded_data = load_profile(profile_path)
        self.assertEqual(loaded_data["student_name"], "Test Student")
        self.assertEqual(loaded_data["email"], "test@example.com")
    
    def test_delete_profile(self):
        """Test deleting a profile."""
        profile_data = {
            "student_name": "Delete Test",
            "date": "01/12/2024",
        }
        
        # Save profile
        profile_path = save_profile(profile_data)
        self.assertTrue(profile_path.exists())
        
        # Delete profile
        delete_profile(profile_path)
        self.assertFalse(profile_path.exists(), "Profile file should be deleted")


if __name__ == "__main__":
    unittest.main()

