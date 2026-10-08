#!/usr/bin/env python3
"""Native, standard-library launcher for the bundled Weather Data Analysis app."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
REQUIRED_FILES = (
    "frontend/out/index.html", "backend/main.py", "requirements.txt",
    "data/processed/weather.parquet", "data/processed/manifest.json",
)


class LaunchError(RuntimeError):
    """An error the user can act on without reading a Python traceback."""


def check_python(version=None):
    version = sys.version_info[:2] if version is None else version
    if version[0] != 3 or not 11 <= version[1] <= 13:
        raise LaunchError("Python 3.11, 3.12 or 3.13 is required. Install a supported version from https://www.python.org/downloads/ and rerun setup.py.")


def venv_python(root=ROOT, windows=None):
    windows = os.name == "nt" if windows is None else windows
    return root / ".venv" / ("Scripts/python.exe" if windows else "bin/python")


def check_bundle(root=ROOT):
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    if missing:
        raise LaunchError("Missing bundle files: " + ", ".join(missing) + ". Extract the complete delivered ZIP. Developers: see README.md for UI build and data processing commands.")


def check_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            # Match asyncio's POSIX listener restart behavior. Windows reuse
            # can permit competing listeners, so keep its exclusive bind probe.
            if os.name != "nt":
                candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            candidate.bind(("127.0.0.1", port))
    except OSError as exc:
        raise LaunchError(f"Cannot use local port {port}: {exc}. Stop the other application or run: python run.py --port 8001") from exc


def pick_free_port(candidates=range(8000, 8011)):
    for port in candidates:
        try:
            check_port(port)
        except LaunchError:
            continue
        return port
    raise LaunchError("No free local port was found in the default range 8000–8010. Choose another port with: python run.py --port 8011")


def check_environment(python):
    if not python.is_file():
        raise LaunchError("The local .venv is missing. Run Setup-Windows.bat, Setup-Mac.command, or a supported Python with setup.py first.")
    # Run the probe in the same interpreter and cwd used by the actual server.
    probe = subprocess.run(
        [str(python), "-c", "import sys; assert sys.version_info[0] == 3 and 11 <= sys.version_info[1] <= 13, 'Use Python 3.11–3.13'; import fastapi, uvicorn, pandas, numpy, pyarrow, sklearn"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if probe.returncode:
        detail = (probe.stderr or probe.stdout).strip().splitlines()
        raise LaunchError("The .venv has unsupported Python or missing dependencies. Rerun setup.py using Python 3.11–3.13. " + (detail[-1] if detail else "Dependency probe failed."))


def stop_server(process):
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(process.pid, signal.SIGINT)
        process.wait(timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def wait_until_ready(process, url, timeout):
    deadline = time.monotonic() + timeout
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise LaunchError(f"The server exited with code {process.returncode}. Read its error above; check bundle data and rerun setup.py if dependencies are missing.")
        try:
            with opener.open(url + "api/health", timeout=1) as response:
                health = json.load(response)
            if health.get("status") == "ok" and health.get("data_ready") is True:
                return
        except (OSError, urllib.error.URLError, ValueError):
            pass
        time.sleep(0.2)
    raise LaunchError(f"The server did not report ready data within {timeout:g} seconds. Check data/processed/weather.parquet and manifest.json, or retry with --startup-timeout 120. Read server output above.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Start Weather Data Analysis on this computer.")
    parser.add_argument("--port", type=int, help="Require this local TCP port; default selects the first free port from 8000–8010")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    parser.add_argument("--check", action="store_true", help="Check the environment and bundle without starting")
    parser.add_argument("--startup-timeout", type=float, default=60, help="Seconds to wait for ready data")
    args = parser.parse_args(argv)
    process = None
    def interrupt_handler(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupt_handler)
    if os.name == "nt":
        signal.signal(signal.SIGBREAK, interrupt_handler)
    try:
        check_python()
        if args.port is not None and not 1 <= args.port <= 65535:
            raise LaunchError("--port must be between 1 and 65535.")
        if args.startup_timeout <= 0:
            raise LaunchError("--startup-timeout must be positive.")
        check_bundle()
        python = venv_python()
        check_environment(python)
        if args.port is None:
            port = pick_free_port()
        else:
            check_port(args.port)
            port = args.port
        url = f"http://127.0.0.1:{port}/"
        if args.check:
            print(f"Ready: supported Python, dependencies, bundled UI, processed data and free port {port}.\nLaunch URL: {url}")
            return 0
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen(
            [str(python), "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, **options,
        )
        wait_until_ready(process, url, args.startup_timeout)
        print(f"\nWeather Data Analysis is ready: {url}\nKeep this window open. Press Ctrl+C to stop.\n", flush=True)
        if not args.no_browser:
            try:
                if not webbrowser.open(url):
                    print("Open the address above in your browser.", flush=True)
            except webbrowser.Error:
                print("Open the address above in your browser.", flush=True)
        return process.wait()
    except KeyboardInterrupt:
        print("\nStopping Weather Data Analysis…", flush=True)
        return 0
    except (LaunchError, OSError) as exc:
        print(f"\nCannot start Weather Data Analysis: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        if process is not None:
            stop_server(process)


if __name__ == "__main__":
    raise SystemExit(main())
