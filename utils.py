import json
import logging
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"
HISTORY_DIR = BASE_DIR / "history"
LOG_FILE = LOGS_DIR / "submissions.log"
CONFIG_DIR = BASE_DIR / "config"
REPORTS_DIR = BASE_DIR / "reports"
IMAGES_DIR = BASE_DIR / "images"
PNG_REPORTS_DIR = BASE_DIR / "images" / "reports"

# ============================================================================
# Input Validation and Sanitization Functions
# ============================================================================

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    if not filename or not isinstance(filename, str):
        return "unnamed"
    
    # Remove path components to prevent directory traversal
    filename = Path(filename).name
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces (Windows issue)
    filename = filename.strip('. ')
    
    # Limit length to prevent filesystem issues
    if len(filename) > 255:
        filename = filename[:255]
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def validate_profile_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate profile data before saving.
    
    Args:
        data: Profile data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
        If valid, returns (True, None)
        If invalid, returns (False, error_message)
    """
    if not isinstance(data, dict):
        return False, "Profile data must be a dictionary"
    
    # Validate required field: student_name
    student_name = data.get("student_name", "").strip()
    if not student_name:
        return False, "Student name is required"
    
    # Validate student name length
    if len(student_name) > 200:
        return False, "Student name is too long (maximum 200 characters)"
    
    # Validate email if provided
    email = data.get("email", "").strip()
    if email and not validate_email(email):
        return False, "Invalid email format"
    
    # Validate date format if provided
    date_str = data.get("date", "").strip()
    if date_str:
        try:
            # Try common date formats
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
                try:
                    datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return False, "Invalid date format. Use DD/MM/YYYY or YYYY-MM-DD"
        except (ValueError, TypeError):
            return False, "Invalid date format. Use DD/MM/YYYY or YYYY-MM-DD"
    
    # Validate field lengths
    max_lengths = {
        "teacher_name": 200,
        "quran_surah": 200,
        "noor_page": 500,
        "tajweed_rules": 500,
        "topic": 500,
        "homework": 2000,
        "parent_notes": 2000,
        "admin_notes": 2000,
    }
    
    for field, max_len in max_lengths.items():
        value = data.get(field, "")
        if value and isinstance(value, str) and len(value) > max_len:
            return False, f"{field.replace('_', ' ').title()} is too long (maximum {max_len} characters)"
    
    return True, None


def validate_path(path: Path, must_exist: bool = False, must_be_file: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate file path to prevent path traversal attacks.
    
    Args:
        path: Path to validate
        must_exist: If True, path must exist
        must_be_file: If True, path must be a file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Resolve to absolute path
        resolved = path.resolve()
        
        # Check if path is within allowed directories
        base_dir = BASE_DIR.resolve()
        try:
            resolved.relative_to(base_dir)
        except ValueError:
            return False, "Path is outside application directory"
        
        if must_exist and not resolved.exists():
            return False, "Path does not exist"
        
        if must_be_file and not resolved.is_file():
            return False, "Path is not a file"
        
        return True, None
    except (OSError, ValueError) as e:
        return False, f"Invalid path: {str(e)}"


def sanitize_string(value: Any, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: Value to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if value is None:
        return ""
    
    # Convert to string
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes and control characters (except newlines and tabs)
    value = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', value)
    
    # Limit length if specified
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


# ============================================================================
# Directory and File Management
# ============================================================================

def ensure_directories() -> None:
    """
    Ensure that all required directories exist.
    """
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """
    Configure the logging system to log into submissions.log.
    """
    ensure_directories()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("Al-QuranCircle AutoFill Reports started. Profiles directory: %s", PROFILES_DIR)


def log_action(message: str) -> None:
    """
    Log a single application action.
    """
    logging.info(message)


def list_profile_files() -> List[Path]:
    """
    List all student profile JSON files.
    """
    ensure_directories()
    return sorted(PROFILES_DIR.glob("*.json"))


def load_profile(profile_path: Path) -> Dict[str, Any]:
    """
    Load a single student profile from JSON file.
    
    Args:
        profile_path: Path to profile JSON file
        
    Returns:
        Profile data dictionary
        
    Raises:
        FileNotFoundError: If profile file doesn't exist
        json.JSONDecodeError: If profile file contains invalid JSON
        OSError: If file cannot be read
    """
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    
    if not profile_path.is_file():
        raise ValueError(f"Profile path is not a file: {profile_path}")
    
    try:
        with profile_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in profile file {profile_path}: {e.msg}",
            e.doc,
            e.pos
        ) from e
    except OSError as e:
        raise OSError(f"Failed to read profile file {profile_path}: {e}") from e


def save_profile(profile_data: Dict[str, Any], filename: Optional[str] = None) -> Path:
    """
    Save a profile to the profiles directory.
    If filename is not provided, generate one from student name and timestamp.
    
    Args:
        profile_data: Profile data dictionary (will be validated)
        filename: Optional filename (will be sanitized)
        
    Returns:
        Path to saved profile file
        
    Raises:
        ValueError: If profile data is invalid
    """
    # Validate profile data
    is_valid, error_msg = validate_profile_data(profile_data)
    if not is_valid:
        raise ValueError(error_msg or "Invalid profile data")
    
    ensure_directories()
    student_name = profile_data.get("student_name", "student").strip() or "student"
    safe_name = "_".join(student_name.split())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if filename is None:
        filename = f"{safe_name}_{timestamp}.json"
    else:
        # Sanitize provided filename
        filename = sanitize_filename(filename)
        if not filename.endswith('.json'):
            filename += '.json'

    profile_path = PROFILES_DIR / filename
    
    # Validate path is safe
    is_valid_path, path_error = validate_path(profile_path, must_exist=False)
    if not is_valid_path:
        raise ValueError(path_error or "Invalid file path")
    
    with profile_path.open("w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)
    log_action(f"Saved profile: {profile_path.name}")
    return profile_path


def delete_profile(profile_path: Path) -> None:
    """
    Delete a student profile JSON file.
    """
    try:
        profile_path.unlink(missing_ok=True)
        log_action(f"Deleted profile: {profile_path.name}")
    except OSError as exc:
        logging.error("Error deleting profile %s: %s", profile_path, exc)


def load_all_profiles() -> List[Dict[str, Any]]:
    """
    Load all student profiles into a list of dicts.
    """
    profiles = []
    for path in list_profile_files():
        try:
            data = load_profile(path)
            data["_file"] = str(path)  # store the file path for reference
            profiles.append(data)
        except json.JSONDecodeError as exc:
            logging.error("Failed to decode profile %s: %s", path, exc)
    return profiles


def backup_profiles() -> Path:
    """
    Create a single JSON backup of all profiles with a timestamped filename.
    The backup file will contain a list of profile dicts.
    """
    ensure_directories()
    profiles = load_all_profiles()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"profiles_backup_{timestamp}.json"
    backup_path = BACKUPS_DIR / backup_filename

    with backup_path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    log_action(f"Created backup: {backup_path.name}")
    return backup_path


def _history_file_for_profile(profile_path: Path) -> Path:
    ensure_directories()
    return HISTORY_DIR / f"{profile_path.stem}.jsonl"


def load_profile_history(profile_path: Path) -> List[Dict[str, Any]]:
    history_file = _history_file_for_profile(profile_path)
    if not history_file.is_file():
        return []

    entries: List[Dict[str, Any]] = []
    with history_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    entries.append(entry)
            except json.JSONDecodeError:
                logging.error("Invalid history line in %s", history_file)
    return entries


def _compute_profile_diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    changes: Dict[str, Dict[str, Any]] = {}
    keys = set(old.keys()) | set(new.keys())
    for key in keys:
        old_value = old.get(key)
        new_value = new.get(key)
        if old_value != new_value:
            changes[key] = {"old": old_value, "new": new_value}
    return changes


def append_profile_history(profile_path: Path, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
    history_file = _history_file_for_profile(profile_path)
    existing = load_profile_history(profile_path)
    last_version = existing[-1].get("version", 0) if existing else 0
    version = last_version + 1

    changes = _compute_profile_diff(old_data, new_data)
    if not changes:
        return

    snapshot = dict(new_data)
    snapshot.setdefault("_file", str(profile_path))

    entry = {
        "version": version,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "profile_file": profile_path.name,
        "changes": changes,
        "snapshot": snapshot,
    }

    with history_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def backup_profiles_as_folder() -> Path:
    """
    OPTIONAL helper: copy entire profiles directory to a timestamped folder.
    Kept in case directory-level backup is preferred.
    """
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = BACKUPS_DIR / f"profiles_backup_{timestamp}"
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(PROFILES_DIR, dest_dir)
    log_action(f"Created folder backup: {dest_dir.name}")
    return dest_dir


def restore_profiles_from_backup(backup_path: Path) -> int:
    """Restore profiles from a JSON backup created by backup_profiles.

    Args:
        backup_path: Path to backup file (will be validated)
        
    Returns:
        Number of profiles restored
        
    Raises:
        FileNotFoundError: If backup file doesn't exist
        ValueError: If backup file is invalid or path is unsafe
    """
    ensure_directories()
    
    # Validate backup path
    is_valid_path, path_error = validate_path(backup_path, must_exist=True, must_be_file=True)
    if not is_valid_path:
        raise ValueError(path_error or "Invalid backup file path")
    
    if not backup_path.is_file():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    try:
        with backup_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Backup file is corrupted (invalid JSON): {e}")

    if not isinstance(data, list):
        raise ValueError("Backup file format is invalid; expected a list of profiles.")

    restored = 0
    errors = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {idx} is not a dictionary, skipping")
            continue
        
        # Validate profile data before restoring
        is_valid, error_msg = validate_profile_data(item)
        if not is_valid:
            errors.append(f"Item {idx} validation failed: {error_msg}, skipping")
            continue
        
        # Prefer original filename from _file if present, otherwise let save_profile generate one
        original_path = item.get("_file")
        filename = None
        if original_path:
            try:
                filename = sanitize_filename(Path(original_path).name)
            except Exception:  # noqa: BLE001
                filename = None

        try:
            save_profile(item, filename=filename)
            restored += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"Failed to restore item {idx}: {e}")
            logging.error(f"Failed to restore profile {idx}: {e}")

    if errors:
        logging.warning(f"Some profiles failed to restore: {len(errors)} errors")
        for error in errors[:10]:  # Log first 10 errors
            logging.warning(error)

    log_action(f"Restored {restored} profiles from backup: {backup_path.name}")
    return restored


def search_profiles(
    query: str,
    profiles: List[Dict[str, Any]],
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search profiles by query across given fields.
    """
    if not query:
        return profiles

    query_lower = query.lower()
    if fields is None:
        fields = ["student_name", "teacher_name", "email", "date"]

    def matches(profile: Dict[str, Any]) -> bool:
        for field in fields:
            value = str(profile.get(field, "")).lower()
            if query_lower in value:
                return True
        return False

    return [p for p in profiles if matches(p)]


def sort_profiles(
    profiles: List[Dict[str, Any]],
    sort_key: str,
) -> List[Dict[str, Any]]:
    """
    Sort profile list by a given key (e.g., date, teacher_name, student_name).
    """
    if not sort_key:
        return profiles

    def sort_value(profile: Dict[str, Any]):
        return str(profile.get(sort_key, "")).lower()

    return sorted(profiles, key=sort_value)

    