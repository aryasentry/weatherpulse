#!/usr/bin/env python3
"""Create a project-local environment; never install or modify system runtimes."""
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def main():
    if sys.version_info[0] != 3 or not 11 <= sys.version_info[1] <= 13:
        print("Setup needs Python 3.11, 3.12 or 3.13. Install a supported version from https://www.python.org/downloads/ and rerun this script.", file=sys.stderr)
        return 1
    requirements = ROOT / "requirements.txt"
    if not requirements.is_file():
        print("requirements.txt is missing. Extract the complete project ZIP and retry.", file=sys.stderr)
        return 1
    target = ROOT / ".venv"
    python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    try:
        if not python.is_file():
            print(f"Creating a local Python environment in {target}", flush=True)
            venv.EnvBuilder(with_pip=True).create(target)
        version = subprocess.run([str(python), "-c", "import sys; raise SystemExit(0 if sys.version_info[0] == 3 and 11 <= sys.version_info[1] <= 13 else 1)"], cwd=ROOT)
        if version.returncode:
            print("Existing .venv uses unsupported Python. Rename or remove only this project's .venv folder, then rerun setup with Python 3.11–3.13.", file=sys.stderr)
            return 1
        print("Installing project dependencies from the official Python Package Index…", flush=True)
        subprocess.run([str(python), "-m", "pip", "--isolated", "--disable-pip-version-check", "install", "--index-url", "https://pypi.org/simple", "-r", str(requirements)], cwd=ROOT, check=True)
        print("\nSetup complete. Use Start-Windows.bat or Start-Mac.command.\nYou can also run: python run.py", flush=True)
        return 0
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Setup failed: {exc}. Check your internet connection and Python installation, then retry. Nothing was installed system-wide.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
