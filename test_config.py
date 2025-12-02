"""Test script to verify config loading and saving."""
import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import config
sys.path.append(str(Path(__file__).parent))

from config import config, DEFAULT_SETTINGS

def test_config():
    print("=== Testing ConfigManager ===")
    print(f"Working directory: {os.getcwd()}")
    
    # Test getting a value
    theme = config.get("theme")
    print(f"Current theme: {theme}")
    
    # Set a test value
    test_key = "test_value"
    test_value = "test123"
    print(f"Setting {test_key} = {test_value}")
    config.set(test_key, test_value)
    
    # Read it back
    read_value = config.get(test_key)
    print(f"Read back {test_key} = {read_value}")
    
    # Verify
    if read_value == test_value:
        print("✅ Config test passed!")
    else:
        print(f"❌ Config test failed: expected {test_value}, got {read_value}")
    
    # Print the full config
    print("\nCurrent config:")
    print(config._config)

if __name__ == "__main__":
    test_config()
