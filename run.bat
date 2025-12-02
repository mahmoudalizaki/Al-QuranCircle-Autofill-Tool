@echo off
echo Using virtual environment...

:: Activate the virtual environment
call .\venv\Scripts\activate.bat

echo Running the app...
python .\main.py

:: Pause to keep the window open if run manually
pause
