#!/usr/bin/env python3
"""Launch the real bundled app, exercise public routes, then verify cleanup."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    with socket.socket() as available:
        available.bind(("127.0.0.1", 0))
        port = available.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def fetch(path):
        with opener.open(url + path, timeout=20) as response:
            return response.read(), response.headers
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with tempfile.TemporaryDirectory(prefix="weather unrelated cwd with spaces ") as other_cwd:
        process = subprocess.Popen([sys.executable, str(ROOT / "run.py"), "--no-browser", "--port", str(port)], cwd=other_cwd, **options)
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Launcher exited before ready: {process.returncode}")
                try:
                    health = json.loads(fetch("/api/health")[0])
                    if health.get("status") == "ok" and health.get("data_ready") is True:
                        break
                except (OSError, ValueError):
                    pass
                time.sleep(0.2)
            else:
                raise RuntimeError("App did not become ready in 90 seconds")
            page, headers = fetch("/")
            if b"<html" not in page.lower() or "text/html" not in headers.get("Content-Type", ""):
                raise RuntimeError("Bundled UI did not return HTML")
            dashboard = json.loads(fetch("/api/dashboard?city=Hyderabad&start=2025-01-01&end=2025-01-07")[0])
            if dashboard["meta"]["filtered_records"] <= 0 or not dashboard["trends"]:
                raise RuntimeError("Real-data dashboard has no results")
            csv_data, csv_headers = fetch("/api/export?city=Hyderabad&start=2025-01-01&end=2025-01-02")
            if b"temperature" not in csv_data.splitlines()[0] or "attachment" not in csv_headers.get("Content-Disposition", ""):
                raise RuntimeError("Filtered export was not a downloadable CSV")
            fetch("/api/pipeline")
            fetch("/api/stream?city=Hyderabad")
            explorer = json.loads(fetch("/api/hadoop/explorer?city=Delhi&month=2021-01")[0])
            if explorer["selection"]["city"] != "Delhi" or len(explorer["trace"]["raw_records"]) != 3:
                raise RuntimeError("Explorer did not return the selected real-record trace")
            if explorer["job"]["verified"] and (not explorer["trace"]["full_month_verified"] or explorer["trace"]["full_month_aggregate"]["records"] != 744):
                raise RuntimeError("Explorer did not independently verify the saved full-month output")
            try:
                fetch("/api/dashboard?city=Atlantis")
            except urllib.error.HTTPError as exc:
                if exc.code != 422:
                    raise RuntimeError(f"Invalid-city validation returned {exc.code}") from exc
            else:
                raise RuntimeError("Invalid city was accepted")
            print("PASS: ready health, bundled HTML, actual analytics, filtered CSV, pipeline, replay, Hadoop Explorer and invalid-city validation.", flush=True)
        finally:
            if process.poll() is None:
                process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise RuntimeError("Launcher did not shut down after interrupt")
    with socket.socket() as released:
        released.settimeout(2)
        if released.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError("Server still accepts connections after shutdown")
    print("PASS: interrupt released the server port; launcher ran from an unrelated cwd with spaces.", flush=True)


if __name__ == "__main__":
    main()
