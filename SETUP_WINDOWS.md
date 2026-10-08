# Weather Data Analysis — Windows setup

This guide runs WeatherPulse directly on Windows. The dashboard uses Python to serve both the FastAPI API and the bundled Next.js interface. You do not need WSL, Docker, a virtual machine, Java, Node.js or Hadoop for normal dashboard use.

Use a Windows 10/11 **x64** computer and **Python 3.11, 3.12 or 3.13, 64-bit**. Python **3.12** is the recommended choice for this project; the scripts reject versions outside 3.11–3.13. This is the project's supported range, rather than a recommendation to install whichever Python version is newest. Native Windows setup is covered by the repository's CI workflow; consult its actual run results before treating Windows execution as verified on your machine.

## 1. Get the complete project

Choose either method. Git is optional.

### Download from GitHub without Git

1. Open [aryasentry/weatherpulse](https://github.com/aryasentry/weatherpulse).
2. Select **Code → Download ZIP**.
3. Right-click the downloaded ZIP in File Explorer and select **Extract All**. Wait for extraction to finish.
4. Open the extracted folder containing `Start-Windows.bat`, `Setup-Windows.bat`, `setup.py` and `run.py`. GitHub may name this folder `weatherpulse-main`; a release ZIP uses `Weather_Data_Analysis`.
5. Keep the entire folder together. Do not run files from the ZIP preview or copy only the batch files to your Desktop.

A short, writable local folder is convenient, for example `C:\Users\YourName\Projects\weatherpulse`. Folder names containing spaces work for the Python dashboard. Avoid `Program Files`, protected system folders and deeply nested paths. If you use OneDrive, ensure the entire extracted project is downloaded locally; a plain local folder avoids sync locks and online-only files.

### Clone with Git

If Git is already installed, open PowerShell and run:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\Projects" | Out-Null
Set-Location "$env:USERPROFILE\Projects"
git clone https://github.com/aryasentry/weatherpulse.git
Set-Location .\weatherpulse
```

The repository includes attributed source CSVs, processed data, saved run evidence and `frontend/out/`. Downloading/cloning requires internet, but no data download or UI build is needed to start the complete checkout.

## 2. Install a supported Python

Get Python from the [official Windows downloads page](https://www.python.org/downloads/windows/). Select a supported **64-bit Windows installer** with `pip` and the Python launcher. For a traditional installer, enable **Add Python to PATH** and the launcher option. Reopen PowerShell after installation so it sees the new commands. See [Python's Windows installation documentation](https://docs.python.org/3.12/using/windows.html) for installer options and command aliases.

Verify the interpreter before setup:

```powershell
py -3.12 --version
py -3.12 -c "import sys, struct; print(sys.executable); print('bits:', struct.calcsize('P') * 8)"
```

The first command should report `Python 3.12.x`; the second should report `bits: 64`. Substitute `3.11` or `3.13` in these commands if that is your installed supported version. A 32-bit interpreter is unsuitable for this dependency set.

If `py` is missing but `python` resolves to your installed interpreter, inspect it with `python --version` and the same `-c` command. Use that executable with `setup.py` only when it is a supported 64-bit interpreter. Installing Git, Java or Node.js does not install Python for this dashboard.

## 3. Simplest start: double-click the batch file

1. In the extracted project folder, double-click **Start-Windows.bat**.
2. On first start, it calls **Setup-Windows.bat** if `.venv\Scripts\python.exe` is missing. Setup creates a project-local `.venv` and installs the exact versions in `requirements.txt` from the official Python Package Index.
3. Wait for **Weather Data Analysis is ready** and the printed address. Your browser opens automatically after the API confirms that processed data is ready.
4. Leave the terminal window open while using the app. Closing the browser does not stop the server.

You can double-click **Setup-Windows.bat** separately before your first launch. It searches for Python **3.13 first, then 3.12, then 3.11**, and finally a supported `python` command. To deliberately select Python 3.12, use the manual method below instead. Once a `.venv` exists, setup reuses it; it does not automatically switch its Python version.

The default launcher picks the first free port between **8000 and 8010**. Open the address printed in your terminal, which may differ from [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Everything binds to your computer's loopback address; another computer cannot open this address to reach your app.

## 4. Manual PowerShell setup and launch

Open PowerShell from the project folder, or change into it first. Replace the example path with your actual extracted directory:

```powershell
Set-Location "C:\Users\YourName\Projects\weatherpulse"
Get-Item .\setup.py, .\run.py, .\requirements.txt
py -3.12 setup.py
```

After **Setup complete**, check and start:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe run.py --check
.\.venv\Scripts\python.exe run.py
```

Use `.\.venv\Scripts\python.exe` for subsequent project commands. There is no need to activate the environment, run `Activate.ps1`, use administrator PowerShell or change execution policy. Dependencies remain in this project's `.venv`, separate from other Python projects.

`--check` verifies the supported interpreter, imports, required files and a free port. It prints a prospective URL without starting a server. A later launch may select a different port if another program takes that port in between.

Other supported options:

```powershell
# Choose this exact free port instead of the automatic range.
.\.venv\Scripts\python.exe run.py --port 8011

# Start normally but open the printed address yourself.
.\.venv\Scripts\python.exe run.py --no-browser

# Allow more time on a slow computer.
.\.venv\Scripts\python.exe run.py --startup-timeout 120
```

These are alternative launch commands; run one server at a time. From PowerShell, `.\Start-Windows.bat --port 8011 --no-browser` also forwards those options to the launcher.

## 5. Verify the running app

In the browser, confirm that Overview loads, city/date filters apply, and CSV export downloads data. The archive is historical ERA5 reanalysis for ten Indian cities during 2021–2025; the original bundle contains **438,240 hourly records**. Model results are a saved chronological holdout evaluation, rather than a live weather forecast.

Keep the server window open and use a **second PowerShell window** for API checks. Set `$appUrl` to the actual printed address:

```powershell
$appUrl = "http://127.0.0.1:8000"
Invoke-RestMethod "$appUrl/api/health"
$result = Invoke-RestMethod "$appUrl/api/dashboard?city=Hyderabad&start=2025-01-01&end=2025-01-07"
$result.meta | Format-List
Invoke-RestMethod "$appUrl/api/pipeline"
Invoke-WebRequest "$appUrl/api/export?city=Hyderabad&start=2025-01-01&end=2025-01-02" -OutFile .\hyderabad-sample.csv
```

Health should report `status: ok` and `data_ready: True`; the sample dashboard should report a positive filtered record count. The export file is written into the second terminal's current directory. The API documentation is available at `/docs`, for example [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

For automated checks, from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

The smoke test starts a separate server on a free port, checks real analytics, CSV export, replay and Explorer routes, then checks shutdown. These commands do not require Java or Hadoop services. Saved Hadoop job evidence may appear verified while **live HDFS telemetry is offline**; that records a past computation, not a running Hadoop installation on your Windows computer.

## 6. Stop and restart

Click the terminal running the launcher and press **Ctrl+C**. Wait for the stopping/shutdown messages before closing it. The launcher shuts down its API child process. Your CSVs, processed data and environment remain intact.

To restart later, double-click **Start-Windows.bat** again, or rerun `.\.venv\Scripts\python.exe run.py`. Do not delete data or `.venv` just to stop the server.

## Internet and offline use

| Action | Internet needed? |
|---|---|
| Download/clone the project or install Python | Yes |
| First Python dependency setup | Yes, access to `pypi.org` and its package download hosts |
| Dashboard, filtering, exports and local processing after setup | No, with complete bundled data/UI and the installed environment |
| Download fresh weather observations | Yes, access to the Open-Meteo API |
| Install optional Node/Spark/Hadoop dependencies | Yes for initial downloads |

The project does not include `.venv`, `node_modules` or a downloaded Hadoop runtime. Copying the project to a new computer still requires its own dependency setup; a virtual environment copied from a Mac or another Windows installation is not a portable installer. Test your complete first installation while online before relying on it offline.

## Files to keep together

```text
weatherpulse/
  Start-Windows.bat       # Start the dashboard; set up if no venv exists
  Setup-Windows.bat       # Install requirements into the local venv
  setup.py, run.py        # Platform-aware setup and launcher
  requirements.txt       # Exact Python dependency pins
  backend/               # API, analytics and processing source
  frontend/
    out/                 # Prebuilt UI served by Python
    src/                 # Editable Next.js/TypeScript source
    package-lock.json    # Exact frontend dependency lock
  data/
    raw/                 # Ten city CSVs and request provenance
    processed/           # Parquet, manifest, model and saved engine evidence
  docs/, tests/, scripts/
  .venv/                 # Created locally by setup; not downloaded from GitHub
```

The launcher specifically requires `frontend/out/index.html`, `backend/main.py`, `requirements.txt`, `data/processed/weather.parquet` and `data/processed/manifest.json`.

## Optional: edit and rebuild the frontend

Normal dashboard use needs no Node.js. For UI development, install **Node.js 22 or newer** using the [official Node.js Windows download](https://nodejs.org/en/download), then reopen PowerShell. This project pins Next.js **16.4.0**, React **19.3.0**, Recharts **3.10.1** and TypeScript **7.0.2** in `frontend/package.json`; use the existing lock file:

```powershell
node --version
npm.cmd --version
Set-Location .\frontend
npm.cmd ci
npm.cmd run typecheck
npm.cmd run build
Set-Location ..
.\.venv\Scripts\python.exe run.py
```

`npm.cmd` avoids PowerShell trying to execute the `npm.ps1` shim. The build writes the static UI into `frontend/out/`. Restart the Python server and refresh the browser after rebuilding.

`npm.cmd run dev` is also available from `frontend/` for the Next.js development server. However, the current UI requests same-origin `/api/...`, and this repository has **no development API proxy configured**. Standalone `localhost:3000` will not supply the Python API; use the build-and-Python workflow above for the complete working app, or configure development forwarding deliberately. Do not interpret missing API errors on port 3000 as missing weather data.

## Optional: processing, Spark and Hadoop

Keep the delivered data for your first successful start. To rebuild processed artifacts from the saved raw CSVs, stop the dashboard, then run from the project folder:

```powershell
.\.venv\Scripts\python.exe -m backend.pipeline
.\.venv\Scripts\python.exe -m backend.forecast
.\.venv\Scripts\python.exe -m backend.mapreduce
.\.venv\Scripts\python.exe -m backend.streaming
```

Pipeline rebuilds replace processed data and invalidate prior prediction/demo/engine evidence. The following jobs recreate the model and Python demonstrations; they do **not** rerun Spark or Apache Hadoop. Restart the dashboard afterward. If raw files are absent, preferably re-extract the complete download. Intentional re-ingestion requires internet:

```powershell
.\.venv\Scripts\python.exe -m backend.ingest --start 2021-01-01 --end 2025-12-31
```

**Spark:** [docs/SPARK.md](docs/SPARK.md) describes the optional independent verification branch with **PySpark 4.0.1** and a native **JDK 17 or 21**. Successful macOS evidence does not prove Windows Spark execution. Check the actual job result on your computer before claiming success. The base dashboard remains usable if optional Spark fails.

**Hadoop:** [docs/HADOOP.md](docs/HADOOP.md) documents the tested native **macOS** Hadoop **3.5.0**, Java **17**, single DataNode, replication-one, HDFS + MapReduce LocalJobRunner setup. Native Hadoop runtime execution on Windows is **untested**. These instructions do not promise Windows HDFS/YARN support or require downloading `winutils.exe` from unofficial sources. You can inspect recorded Hadoop evidence and the Explorer's source-record trace on Windows without running Hadoop; live NameNode/DataNode details require the separately running services.

## Troubleshooting

| Symptom | What to do |
|---|---|
| `py` or `python` is not recognized | Install a supported Python with launcher/PATH options, reopen PowerShell, and verify the version. `Get-Command py, python -ErrorAction SilentlyContinue` shows resolved commands. |
| `python` opens the Microsoft Store | Prefer `py -3.12`. Inspect **Manage App Execution Aliases** if the Store shortcut masks your installed Python. See the official Python Windows documentation linked above. |
| Unsupported version / Python 3.14 selected | Use `py -3.12 setup.py` or another supported version explicitly. The batch file does not use 3.14. |
| Existing `.venv` has a wrong interpreter, missing packages, or was copied from another machine | Stop the app. In the project folder, rename only `.venv` to a currently unused backup name, such as `Rename-Item .\.venv .venv-old`, then run `py -3.12 setup.py`. Preserve `data/` and the project source. |
| Installation asks for compiler tools or reports no matching wheel | Confirm 64-bit Python 3.11–3.13, and that you used this project's requirements rather than a different environment. Keep the actual error; do not substitute arbitrary package versions. |
| Setup fails downloading dependencies | Check connectivity and corporate restrictions on `pypi.org`/package hosts. Setup invokes pip in isolated mode with the official index, so ordinary pip configuration/environment variables may not affect it. Do not disable certificate checks. Ask your network administrator about the approved proxy/CA, or install with explicit approved pip options using the project's Python. |
| Firewall/VPN/proxy interferes with localhost | Open the printed `127.0.0.1` URL and bypass the proxy for local addresses in your approved settings. The launcher readiness check already bypasses proxies. The dashboard needs no public inbound firewall rule. |
| Missing bundle files | Re-extract or clone the complete project. If only `frontend/out/` is absent, rebuild the UI with Node as above. If Parquet/manifest is absent but all raw CSVs are intact, run the processing steps above. |
| `data_ready: False` / startup timeout | Check the server error and processed files. A partial/corrupt manifest or Parquet pair fails readiness checks. Re-extract matching originals, or intentionally rebuild from raw files. Try `--startup-timeout 120` only when startup is simply slow. |
| Port 8000 is busy | Automatic launch tries ports through 8010. Use the printed address; do not assume 8000. If all are occupied, use `--port 8011` or another free port. |
| Explicit port is busy | The explicit `--port` must be free; it does not fall back. Select another port instead of killing unrelated programs. |
| Browser did not open / old page shown | Copy the printed URL into the browser. Confirm the correct port and server, then refresh. After a frontend rebuild, restart Python and hard-refresh if necessary. |
| Permission denied, very long path, OneDrive locks or online-only files | Extract into a short writable local folder outside sync-managed/protected directories. If moving an already set-up project causes problems, recreate its `.venv` at the new location. |
| PowerShell blocks `Activate.ps1` or `npm.ps1` | Use `.\.venv\Scripts\python.exe` directly and `npm.cmd`. Neither command requires relaxing execution policy. |
| Hadoop Explorer reports offline HDFS | Expected when native Hadoop services are not running. Refresh observes service state; it does not install/start Hadoop or rerun a job. |

For unresolved failures, retain the exact terminal error, interpreter path/version and the output of `.\.venv\Scripts\python.exe run.py --check`. Compare with [verification notes](docs/VERIFICATION.md), [the general README](README.md) and the repository's actual CI results.
