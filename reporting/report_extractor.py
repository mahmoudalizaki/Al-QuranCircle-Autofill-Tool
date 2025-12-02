"""
Report extraction module for filtering and retrieving student reports based on various criteria.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Literal, TypedDict
import json
from dataclasses import dataclass

ReportMode = Literal['first', 'last', 'all']

@dataclass
class ReportCriteria:
    """Criteria for filtering reports."""
    student_name: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    mode: ReportMode = 'all'

class StudentReport(TypedDict):
    """Structure of a student report."""
    student_name: str
    date: str
    teacher_name: str
    quran_surah: str
    tafseer: str
    noor_page: str
    tajweed_rules: str
    topic: str
    homework: str
    parent_notes: str
    admin_notes: str
    _file: str
    _timestamp: str

class ReportExtractor:
    """Handles extraction of student reports based on various criteria."""
    
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.history_dir = Path("history")
        
    def _load_profile_history(self, profile_path: Path) -> List[StudentReport]:
        """Load history for a specific profile from the history directory."""
        # Look for history files that match the profile name pattern
        history_entries = []
        base_name = profile_path.stem.split(' - ')[0]  # Remove any " - Copy" suffixes
        
        for history_file in self.history_dir.glob(f"{base_name}*.jsonl"):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if 'snapshot' in entry:
                                # Convert the snapshot to a StudentReport
                                report = entry['snapshot']
                                report['_file'] = str(profile_path)
                                report['_timestamp'] = entry.get('timestamp', '')
                                history_entries.append(report)
                        except json.JSONDecodeError:
                            continue
            except (IOError, OSError):
                continue
                
        return history_entries
    
    def _get_all_profiles(self) -> List[Path]:
        """Get all profile JSON files."""
        return list(self.profiles_dir.glob("*.json"))
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in DD/MM/YYYY format, with fallback to YYYY-MM-DD."""
        try:
            # Try DD/MM/YYYY format first
            return datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            # Fall back to YYYY-MM-DD for backward compatibility
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid date format: {date_str}. Expected DD/MM/YYYY or YYYY-MM-DD") from e
    
    def _matches_date_criteria(self, report_date: str, criteria: ReportCriteria) -> bool:
        """Check if a report matches the date criteria."""
        if not (criteria.month or criteria.year):
            return True
            
        try:
            report_dt = self._parse_date(report_date)
            
            if criteria.year and report_dt.year != criteria.year:
                return False
            if criteria.month and report_dt.month != criteria.month:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    def get_reports(self, criteria: ReportCriteria) -> Dict[str, List[StudentReport]]:
        """
        Get reports based on the given criteria, including historical data.
        
        Args:
            criteria: ReportCriteria object with filtering options
            
        Returns:
            Dictionary mapping student names to their reports
        """
        all_reports: Dict[str, List[StudentReport]] = {}
        
        for profile_path in self._get_all_profiles():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
                    
                student_name = current_data.get('student_name', 'Unknown')
                
                # Skip if student name doesn't match filter
                if criteria.student_name and student_name != criteria.student_name:
                    continue
                    
                if student_name not in all_reports:
                    all_reports[student_name] = []
                
                # Add current version
                current_data['_file'] = str(profile_path)
                current_data['_timestamp'] = datetime.now().isoformat()
                
                # Add historical versions from history directory
                history_entries = self._load_profile_history(profile_path)
                
                # Combine current data and history, ensuring we don't have duplicates
                all_entries = [current_data] + history_entries
                seen = set()
                
                for entry in all_entries:
                    # Create a unique identifier for each entry based on its content
                    entry_id = (
                        entry.get('date', ''),
                        entry.get('quran_surah', ''),
                        entry.get('topic', '')
                    )
                    
                    if entry_id not in seen and self._matches_date_criteria(entry.get('date', ''), criteria):
                        seen.add(entry_id)
                        all_reports[student_name].append(entry)
                
                # Sort by date (newest first)
                all_reports[student_name].sort(
                    key=lambda x: datetime.strptime(x.get('date', '1970-01-01'), '%d/%m/%Y'),
                    reverse=True
                )
                
                # Apply report mode filter
                if criteria.mode == 'first' and all_reports[student_name]:
                    all_reports[student_name] = [all_reports[student_name][-1]]  # Oldest
                elif criteria.mode == 'last' and all_reports[student_name]:
                    all_reports[student_name] = [all_reports[student_name][0]]  # Newest
                
                # Add history
                history = self._load_profile_history(profile_path)
                for entry in history:
                    entry['_file'] = str(profile_path)
                    all_reports[student_name].append(entry)
                    
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error processing {profile_path}: {e}")
                continue
        
        # Apply filters and sorting
        filtered_reports: Dict[str, List[StudentReport]] = {}
        
        for student, reports in all_reports.items():
            # Filter by date criteria
            student_reports = [
                r for r in reports 
                if self._matches_date_criteria(r.get('date', ''), criteria)
            ]
            
            if not student_reports:
                continue
                
            # Sort by date
            student_reports.sort(key=lambda x: x.get('date', ''))
            
            # Apply mode filter
            if criteria.mode == 'first':
                filtered_reports[student] = [student_reports[0]]
            elif criteria.mode == 'last':
                filtered_reports[student] = [student_reports[-1]]
            else:  # 'all'
                filtered_reports[student] = student_reports
        
        return filtered_reports
