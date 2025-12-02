# Al-QuranCircle AutoFill Reports

## Overview
Al-QuranCircle AutoFill Reports is a professional desktop application designed to manage and automate the submission of student progress reports for Quran and Islamic studies. This tool helps teachers and educational administrators efficiently handle student data, track progress, and submit forms with ease.

## Features

- **Student Profile Management**
  - Create, edit, and delete student profiles
  - Store comprehensive student information including personal details and academic progress
  - Track revision history for each student's profile

- **Form Automation**
  - Automated form submission to streamline administrative tasks
  - Batch processing for submitting multiple student reports at once
  - Configurable retry mechanism for failed submissions

- **Data Management**
  - Secure backup and restore functionality
  - Search and filter capabilities for quick access to student records
  - History tracking for all profile changes

- **User Interface**
  - Modern, intuitive interface built with CustomTkinter
  - Dark/Light theme support
  - Responsive design that adapts to different screen sizes

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd ResetIT
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Main Interface:
   - Left sidebar: Browse and search student profiles
   - Main panel: View and edit student details
   - Toolbar: Access additional features like backup and batch processing

3. Creating a New Profile:
   - Click "New Student" button
   - Fill in the required fields
   - Click "Save" to store the profile

4. Submitting Forms:
   - Select a student profile
   - Click "Submit to Form" to automatically fill and submit the online form
   - Use "Batch Submit" to process multiple students at once

## Configuration

The application automatically creates the following directory structure:
- `profiles/`: Stores student profile data
- `backups/`: Automatic and manual profile backups
- `logs/`: Application logs for troubleshooting
- `history/`: Detailed change history for each profile

## Dependencies

- `customtkinter`: Modern UI components
- `playwright`: Browser automation
- `python-dotenv`: Environment variable management
- `loguru`: Advanced logging

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support or feature requests, please open an issue on the GitHub repository.

---

*ResetIT v1.0.0 - Developed by Mahmoud Zaki*
