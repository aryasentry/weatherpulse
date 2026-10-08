@echo off
setlocal
cd /d "%~dp0"
py -3.13 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    py -3.13 "%~dp0setup.py"
    goto result
)
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    py -3.12 "%~dp0setup.py"
    goto result
)
py -3.11 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    py -3.11 "%~dp0setup.py"
    goto result
)
python -c "import sys; raise SystemExit(0 if sys.version_info[0] == 3 and 11 <= sys.version_info[1] <= 13 else 1)" >nul 2>&1
if not errorlevel 1 (
    python "%~dp0setup.py"
    goto result
)
echo Python 3.11, 3.12 or 3.13 was not found.
echo Install from https://www.python.org/downloads/windows/ with the launcher and PATH options enabled.
pause
exit /b 1
:result
if errorlevel 1 (
    echo Setup failed. Read the error above, then retry.
    pause
    exit /b 1
)
endlocal
