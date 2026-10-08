# WeatherPulse — project setup

This guide covers running the downloaded project, macOS setup, development, data regeneration and optional processing engines. For a screen-by-screen Windows workflow and PowerShell troubleshooting, use [SETUP_WINDOWS.md](SETUP_WINDOWS.md).

## 1. Choose what you want to run

| Goal | Required software | What you get |
| --- | --- | --- |
| Use the complete dashboard | Python 3.11, 3.12 or 3.13; a modern browser | Overview, Analytics, Predictions, Pipeline, Hadoop Explorer and CSV export |
| Edit/rebuild the frontend | Above, plus Node.js and npm; Node 24 was used for the delivered build | Next.js/TypeScript source and a new static export |
| Recompute the Spark comparison | Base setup, Java 17 or 21, `requirements-spark.txt` | Actual single-machine Spark aggregation and parity evidence |
| Run native Hadoop on macOS | Base setup, Java 17, Apache Hadoop downloaded by this project's installer | Local HDFS and Hadoop Streaming with LocalJobRunner |

The base app does not require a database server, API key, cloud account, Docker, Ubuntu, WSL, a VM, Java or Node.js. It binds to `127.0.0.1` and is intended for local use. Public GitHub source does not publish a running web service.

The repository includes:

- A prebuilt Nordic interface under `frontend/out/`.
- 438,240 hourly ERA5 observations for ten Indian cities, covering 2021–2025.
- Clean Parquet, source provenance, model evaluation and recorded Spark/Hadoop results.

Dependencies, `.venv/`, `node_modules/`, Hadoop binaries/HDFS state and local UI backups are not included. Internet is needed for the first dependency installation. Once installed, the bundled dashboard and data work offline. Refreshing weather data or installing an optional engine requires internet again.

## 2. Download the project

### Without Git

1. Open [aryasentry/weatherpulse](https://github.com/aryasentry/weatherpulse).
2. Choose **Code → Download ZIP**.
3. Extract the entire archive before launching anything.
4. Open the extracted folder containing `README.md`, `setup.py`, `run.py`, `backend/`, `frontend/` and `data/`.

A GitHub download may be named `weatherpulse-main`. Renaming that folder to `weatherpulse` is fine. Do not run scripts from an archive preview or copy only the frontend folder.

### With Git

```bash
git clone https://github.com/aryasentry/weatherpulse.git
cd weatherpulse
```

Use a writable local folder. The base dashboard supports paths with spaces. Optional native Hadoop requires the **entire absolute path** to have no whitespace; `/Users/yourname/Projects/weatherpulse` is suitable, while a parent called `Course Projects` is not.

## 3. macOS: install and launch

Install a supported Python from [python.org](https://www.python.org/downloads/macos/) if needed. A Python 3.14+ interpreter is not accepted by this project's setup; select 3.11–3.13 explicitly. Python 3.13 was used for the local verification.

### Finder workflow

1. Open the project folder.
2. Open **Start-Mac.command**. It invokes setup if `.venv` is missing.
3. Wait for dependency installation to finish and for `Weather Data Analysis is ready`.
4. Use the browser window opened by the launcher. Keep its Terminal window open.
5. Press **Ctrl+C** in that Terminal to stop the application.

If Finder does not open the script, use Terminal. No executable-bit change is needed when invoking it with `bash`:

```bash
cd /path/to/weatherpulse
bash Setup-Mac.command
bash Start-Mac.command
```

### Explicit interpreter workflow

For a Python 3.12 installation:

```bash
cd /path/to/weatherpulse
python3.12 --version
python3.12 setup.py
.venv/bin/python run.py --check
.venv/bin/python run.py
```

Replace `python3.12` with `python3.13` or `python3.11` if that is your installed supported version. After setup, use `.venv/bin/python` for project commands; activating the virtual environment is optional.

`setup.py` creates only the project's `.venv` and installs the pinned `requirements.txt` from PyPI. It does not install Python, Java or operating-system packages. Rerunning it repairs missing Python dependencies. An environment copied from another computer or OS should be replaced with a new project-local environment.

## 4. Windows: quick path

The detailed guide is [SETUP_WINDOWS.md](SETUP_WINDOWS.md). Install 64-bit Python 3.11–3.13, including its launcher, extract the project, and double-click **Start-Windows.bat**.

For an explicit Python 3.12 setup in PowerShell:

```powershell
Set-Location C:\Projects\weatherpulse
py -3.12 --version
py -3.12 setup.py
.\.venv\Scripts\python.exe run.py --check
.\.venv\Scripts\python.exe run.py
```

Use the full virtual-environment executable as shown. No PowerShell execution-policy change is required.

## 5. Verify the running application

The launcher prints its actual address and selects the first free port from **8000–8010**. Do not assume it is 8000 when another application is already using that port.

At the printed address:

1. Open `/` and check the Overview, charts and city archive table.
2. Select Delhi and apply the full 2021–2025 range. The bundled archive gives **43,824 records**, mean temperature approximately **25.1 °C**, and precipitation approximately **4,108 mm**.
3. Open Analytics, Predictions and Pipeline.
4. Download **Export CSV** and confirm it reflects the selected filters.
5. Open `/api/health`; expect `status: "ok"` and `data_ready: true`.
6. Open `/docs` for the generated API documentation.
7. Open Hadoop Explorer. Without local HDFS it should report HDFS offline, while the saved run and real-record trace can still be inspected. This is expected on a fresh dashboard-only installation.

To choose a port or avoid browser auto-opening:

```bash
# macOS
.venv/bin/python run.py --port 8011 --no-browser
```

```powershell
# Windows
.\.venv\Scripts\python.exe run.py --port 8011 --no-browser
```

An explicitly requested occupied port causes an error; it does not silently move to another port. Close only your own conflicting server or choose a free port. To allow more startup time, add `--startup-timeout 120`.

Closing the browser does not stop the server. Press **Ctrl+C** in the launching terminal and wait for shutdown. Optional HDFS daemons are separate and must be stopped with their Hadoop stop command.

## 6. Verify setup with automated checks

Run from the project root after setup:

```bash
# macOS
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python scripts/smoke_test.py
```

```powershell
# Windows
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/smoke_test.py
```

The smoke test starts the real bundled app on a temporary free port, checks health, HTML, analytics, CSV export, Pipeline, replay and Hadoop Explorer, then verifies shutdown and port release. It does not need live HDFS. The unit tests use isolated fixtures for optional-engine failure cases; passing them is not proof that Hadoop or Spark ran on that computer.

GitHub Actions defines Windows and macOS checks for Python 3.11–3.13 in [native.yml](.github/workflows/native.yml). Use the repository's **Actions** tab to inspect the outcome for the exact commit you downloaded. Historical local results and scope limits are in [docs/VERIFICATION.md](docs/VERIFICATION.md).

## 7. Edit and build the frontend

You can run the delivered app without this section. Install a supported Node.js release from [nodejs.org](https://nodejs.org/); the delivered build was made with Node 24. Check `node --version` and `npm --version`, then:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
cd ..
```

`npm ci` uses the committed lockfile. `npm run build` writes the static site into `frontend/out/`, which FastAPI serves. Start or keep running the ordinary Python launcher and refresh the browser to view the new build. Check all five screens and mobile navigation after layout changes.

The supplied `npm run dev` starts Next.js separately, but this repository does **not** configure an API proxy for that server. Analytics requests use relative `/api/...` paths. For a complete working preview, use the static build plus the Python server above; a standalone Next.js development page is not the full application without additional API routing configuration.

If distributing a change, include the rebuilt `frontend/out/` along with `frontend/src/`. Do not commit `node_modules/`, `.next/` or `*.tsbuildinfo`. The ten-style design gallery remains available at `/ui-styles.html`; choosing a shortlist there does not change the app's current Nordic design.

## 8. Regenerate data and derived results

The bundled data is ready to use. Skip regeneration for a normal installation. Before deliberately refreshing it, stop the dashboard and preserve a copy of `data/` if you need to keep the recorded results.

Run these commands from the project root, replacing `PYTHON` with `.venv/bin/python` on macOS or `.\.venv\Scripts\python.exe` on Windows:

```text
PYTHON -m backend.ingest --help
PYTHON -m backend.ingest
PYTHON -m backend.pipeline
PYTHON -m backend.forecast
PYTHON -m backend.mapreduce
PYTHON -m backend.streaming
```

`PYTHON` above is a placeholder, not a command to type literally. For example, Windows uses `.\.venv\Scripts\python.exe -m backend.pipeline`.

- Ingestion downloads ERA5 data and reuses matching validated cached city files. `--force` requests a fresh download. Retain the `.provenance.json` files with the CSVs.
- Pipeline validates/deduplicates the CSVs and writes compressed `weather.parquet` and `manifest.json`.
- Pipeline deliberately invalidates dependent predictions, replay/MapReduce artifacts and Spark/Hadoop execution evidence. Recreate them before presenting new results as verified.
- Forecast trains the temperature model and records chronological holdout and persistence-baseline metrics. It is historical evaluation, not a live forecast service.
- `backend.mapreduce` is a Python-only map/shuffle/reduce demonstration. It does not invoke Apache Hadoop.
- `backend.streaming` creates a historical replay sample. It is not a live sensor feed.

Restart the dashboard after changing data so its cached dataset reloads. The delivered UI/date bounds and examples target 2021–2025; extending the project's date range requires updating those bounds as well as ingestion. Rerun tests and independently check counts after any refresh.

## 9. Optional Spark and Hadoop

### Spark

Follow [docs/SPARK.md](docs/SPARK.md). Install Java 17 or 21, then install `requirements-spark.txt` into this project's environment and run `PYTHON -m backend.spark_job`. The job reads raw CSVs and checks monthly aggregates against the prepared dataset. It runs in local mode on one computer.

### Hadoop on macOS

Follow [docs/HADOOP.md](docs/HADOOP.md) for the complete instructions and path restriction. With a native Java 17 installation and no whitespace in the full project path:

```bash
.venv/bin/python scripts/setup_hadoop.py
.venv/bin/python scripts/hadoop_native.py start
.venv/bin/python scripts/hadoop_native.py run
.venv/bin/python scripts/hadoop_native.py status
# When finished:
.venv/bin/python scripts/hadoop_native.py stop
```

The installer downloads Hadoop from Apache and verifies its SHA512. It stores everything under `.runtime/`. Start-Hadoop-Mac.command combines setup, service start and the weather job. Stop-Hadoop-Mac.command stops the owned services while preserving HDFS data.

The NameNode UI is `http://127.0.0.1:19870/` while the service is running. This setup is one NameNode, one DataNode, replication one and MapReduce LocalJobRunner. It does not start YARN or install Hive, Pig, Sqoop, HBase, ZooKeeper or Mahout.

Native Hadoop execution on Windows has not been validated. The Windows dashboard does not need Hadoop installed; it can show the included saved execution proof and sample trace. A saved verified run is distinct from a live HDFS service on the current machine.

## 10. Folder guide

| Path | Contents |
| --- | --- |
| `backend/` | FastAPI routes, analytics, data jobs and Hadoop mapper/reducer |
| `frontend/src/` | Editable Next.js/React UI |
| `frontend/out/` | Prebuilt static UI served by Python |
| `frontend/public/ui-styles.html` | Standalone design gallery |
| `data/raw/` | City CSVs, request provenance and ingestion report |
| `data/processed/` | Parquet, model outputs and saved processing evidence |
| `tests/` | Automated analytics, launcher and optional-engine tests |
| `scripts/` | Smoke test, Hadoop setup/control and release packaging |
| `docs/` | Architecture, lifecycle, syllabus, attribution and verification |
| `.venv/` | Local Python packages; generated and excluded from Git |
| `.runtime/` | Optional downloaded Hadoop/runtime state; excluded from Git |

The data attribution and publication notes are in [data/README.md](data/README.md). `.gitattributes` preserves CSV bytes across platforms so the source checksums remain valid.

## 11. Troubleshooting

| Symptom | Action |
| --- | --- |
| Python unsupported or command missing | Install/select Python 3.11–3.13 explicitly; check the version before setup. |
| Dependency import fails | Rerun setup with the supported interpreter, then run the virtual environment's `python -m pip check`. |
| `.venv` was copied from another machine | Rename that environment folder and rerun setup locally; do not reuse its executables. |
| Package download fails | Check the network, proxy/certificate configuration and the displayed error; retry setup. Do not disable TLS verification. |
| Missing bundled UI or data | Re-extract the full repository ZIP; developers can rebuild the UI and regenerate data using the sections above. |
| App opens on 8001 instead of 8000 | Expected when 8000 is occupied; use the printed address. |
| Browser shows old styling | Refresh the page after the static build; confirm you are viewing the port printed by this project's launcher. |
| Hadoop Explorer says offline | Expected if HDFS is not running locally. Start the optional Mac services or inspect the saved run. |
| Saved engine proof becomes unverified | Data/evidence changed or is missing. Rerun the applicable computation; do not edit verification flags manually. |
| Hadoop reports whitespace in path | Move to a path with no spaces in any parent directory. This restriction does not apply to the base dashboard. |

For a portable distribution, run `python scripts/package_release.py --output dist/WeatherPulse.zip` after building and checking the UI. The archive excludes installed dependencies and optional runtime downloads and includes a SHA256 manifest. Keep the folder structure intact when sharing it.
