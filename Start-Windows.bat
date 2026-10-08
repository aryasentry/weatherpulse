@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    call "%~dp0Setup-Windows.bat"
    if errorlevel 1 exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0run.py" %*
if errorlevel 1 (
    echo.
    echo Launch failed. Read the message above and see README.md.
    pause
    exit /b 1
)
endlocal
