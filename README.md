# Weather Data Analysis

A native Windows/macOS course project for **Big Data Analytics (22PC1CS401)**, VNRVJIET, B.Tech VII semester. WeatherPulse is the interface name; the project title is **Weather Data Analysis**.

Explore historical hourly weather for Indian cities, compare monthly trends, inspect correlations and educational extreme-event thresholds, export filtered CSV, and evaluate a temperature prediction model against a baseline. The bundled Next.js interface and FastAPI API run together on your computer using one Python server.

**Setup guides:** [Windows step by step](SETUP_WINDOWS.md) · [General setup, macOS and development](SETUP.md). The repository includes the built Nordic UI and attributed weather data, so ordinary setup does not require Node.js, Java, Spark or Hadoop.

## Start the delivered project

You need **Python 3.11, 3.12 or 3.13** and a browser. Get Python from [python.org](https://www.python.org/downloads/). On Windows, enable the Python launcher and PATH installation options. The first setup downloads project dependencies from the official Python Package Index; subsequent dashboard use requires no internet when the delivered data and interface are present. You do not need Node.js or Java to use the bundle.

1. Extract the complete ZIP into a writable folder. The Python dashboard supports paths containing spaces. If you plan to run optional native Hadoop, choose a full folder path with **no whitespace anywhere**, including parent folders. The new ZIP's top-level folder is `Weather_Data_Analysis`. Do not run inside the ZIP viewer.
2. On Windows, double-click **Start-Windows.bat**. On macOS, open **Start-Mac.command**. The start script runs setup automatically if the project's `.venv` is missing.
3. Wait for `Weather Data Analysis is ready`. Your browser opens the printed local address. The launcher selects the first free port from **8000 through 8010**, usually [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
4. Keep the terminal window open while using the dashboard. Press **Ctrl+C** in that window to stop the server.

If macOS does not open the `.command` file after extraction, open Terminal, change to the extracted directory, and run:

```bash
bash Setup-Mac.command
bash Start-Mac.command
```

Manual setup and launch from a terminal are also supported:

```powershell
# Windows: from the project directory
py -3.12 setup.py
.\.venv\Scripts\python.exe run.py
```

```bash
# macOS: from the project directory, using supported Python
python3.12 setup.py
.venv/bin/python run.py
```

Choose `3.11` or `3.13` instead of `3.12` if that is your installed version. Setup creates only this project's `.venv` and installs `requirements.txt` there. It never installs system runtimes or changes system settings. No Ubuntu, virtual machine, Docker, or WSL is required.

## A short classroom demonstration

1. Open the overview and identify the selected dates, number of records, data source and units.
2. Select Hyderabad and a year. Explain temperature trends and total rainfall for this city. Select all cities and explain that summed rainfall is the sum across selected city-hours, not rainfall at one place.
3. Compare cities and inspect the correlation matrix. Correlation describes association; it does not establish causation.
4. Show the prediction view, its chronological train/test split, model MAE and baseline MAE. A model result is useful only in relation to that baseline and held-out period.
5. Show pipeline/source evidence, historical stream replay and quality information. Export a CSV for the selected city and dates.

The tabs and visualizations use the actual bundled data. Missing data or failed requests are displayed as errors; the application does not silently replace data with random examples.

## Inspect Hadoop and the data lifecycle

Open **Hadoop Explorer** from the navigation:

- **Inside HDFS** explains the Client, NameNode and DataNode, separating metadata requests from file-byte transfers. Inspect the real input files, configured block size, block locations and replication. Refresh reads the local NameNode; it does not launch a Hadoop job.
- **Follow a record** walks through real example rows, mapper output, grouping and the completed month's result. Its play/step controls are a teaching replay, not live MapReduce progress. Sample rows are identified separately from the full-month aggregate.
- **Data flow** shows the processing branches and each tool's role. The operational assessment remains in the documentation. The main dashboard uses pandas/local Parquet; Spark and Hadoop are independent verification branches.

Live HDFS telemetry, saved verified execution evidence and instructional animations have different labels. If Hadoop is stopped or not installed, live details become unavailable while the saved evidence and source-based explanation remain usable. See [lifecycle and tool coverage](docs/LIFECYCLE.md) for the full assessment: the core batch path is implemented, while production orchestration, incremental ingestion, alerting, shared access and backup/restore remain incomplete.

## Design alternatives

Open `/ui-styles.html` on the running app, or open `frontend/public/ui-styles.html` directly. This standalone HTML contains ten distinct layouts with embedded 2025 weather data, full-size and phone previews, working city/metric controls, monthly CSV export and a saved shortlist. It has no external asset or package dependencies. Shortlisting does not apply a redesign to the app; choose a direction first.

The current app uses **05 — Nordic**: light top navigation, a pale blue workspace, vertical overview metrics and wide chart panels. Coursework branding, syllabus tables and lengthy scope/roadmap blocks have been removed. Source attribution, historical-data labels, saved-run timestamps and concise engine/status details remain visible. The previous interface is preserved in a local rollback snapshot, excluded from the public repository.

## Data and interpretation

Source: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), with provider and request provenance retained in `data/`. The delivered ERA5 dataset has **438,240 hourly rows**, **43,824 per city**, from **2021-01-01 through 2025-12-31** for ten Indian cities. **Use the dashboard and processed manifest for actual counts after any refresh.** This is historical **reanalysis**: model-based estimates informed by observations, rather than measurements from a sensor at each city coordinate. Attribution includes [Open-Meteo](https://open-meteo.com/) and Copernicus Climate Change Service / ECMWF, as recorded in the ingestion metadata. The data manifest records CC BY 4.0; retain attribution and check the provider's API terms for your use.

Times use Asia/Kolkata; temperature is °C, relative humidity %, precipitation mm, and wind speed km/h. Daily maximum temperature ≥40 °C and daily rainfall ≥50 mm define educational event categories, not official weather alerts. Replay presents saved historical rows, not a live weather feed. See [syllabus coverage and viva notes](docs/SYLLABUS.md) and [data ethics](docs/DATA_ETHICS.md).

## Troubleshooting

| Message or symptom | Action |
|---|---|
| Unsupported Python | Install/use Python 3.11–3.13. Python 3.14 is outside this bundle's supported range. |
| Missing dependencies | Rerun the setup script. The first setup needs internet access to `pypi.org`. |
| Existing `.venv` uses unsupported Python | Rename/remove only this project's `.venv`, then rerun setup with supported Python. |
| Missing frontend/data bundle files | Extract the complete delivered ZIP. A source-only checkout needs the development steps below. |
| A default port is occupied | The launcher automatically tries the next port through 8010. Use the printed browser address. |
| Explicit `--port` occupied / all default ports occupied | Choose another port, such as `python run.py --port 8011`. Explicit `--port` requires that exact port to be free. |
| Browser does not open | Manually open the printed `http://127.0.0.1:PORT/` address. |
| Server startup timeout | Read the server error in the terminal, check processed data, or try `python run.py --startup-timeout 120`. |
| Windows Python command opens the Store | Use `py -3.12`, or install Python and its launcher from python.org. |

Environment-only inspection: `python run.py --check` selects an available default port and prints the prospective URL without starting the server or opening a browser. `--check --port 8011` checks that exact port. To launch without opening a browser: `python run.py --no-browser`. Scripts work independently of the caller's working directory; Python commands shown above assume you are in the extracted project directory.

## Development and optional processing engines

The source and the prebuilt static UI are delivered together. To rebuild the UI, install **Node.js 22 or newer**, then use:

```bash
cd frontend
npm ci
npm run build
```

From the project directory, with the project environment activated (`.venv\Scripts\Activate.ps1` on Windows PowerShell or `source .venv/bin/activate` on macOS):

```bash
python -m backend.ingest --start 2021-01-01 --end 2025-12-31
python -m backend.pipeline
python -m backend.forecast
python -m backend.mapreduce
python -m backend.streaming
python -m pytest -q
```

Re-ingestion downloads source data and requires network access. Processing, local MapReduce, replay and dashboard use the saved data. The ingestion module supports `--help`; pipeline/forecast modules execute their jobs directly. Avoid overwriting source data immediately before a demonstration; keep its provenance with it.

**Spark is optional.** Spark 4.0.1 requires Java 17 or 21 and its Python package; install those only if you want to run the independent Spark computation. See [Spark setup](docs/SPARK.md). A real Spark run writes `data/processed/spark_evidence.json`, which the dashboard reads. A missing evidence file must not be presented as a verified Spark run. Spark local mode runs on one computer; it does not establish HDFS, Hadoop/YARN or a distributed cluster.

**Hadoop is an optional native macOS demonstration.** Separate setup scripts download checksum-verified Apache Hadoop 3.5.0 into this project's `.runtime/`, start a loopback HDFS NameNode and DataNode, and submit a Hadoop Streaming job using **LocalJobRunner**. Java **17** and a full project path **without whitespace** are required. It uses actual HDFS storage and the Hadoop MapReduce framework on one Mac; YARN and multiple worker machines are outside this setup. See [native Hadoop setup and evidence](docs/HADOOP.md). The base Windows/macOS dashboard still needs only Python and the delivered files, and Hadoop runtime execution on Windows is unverified.

Hive, Pig, Sqoop, HBase, ZooKeeper and Mahout remain **documented extensions**. [Reference exercises](docs/examples/README.md) explain their relationship to the weather data. `python -m backend.mapreduce` remains a separate local Python demonstration; the actual Hadoop job uses the Hadoop scripts and its own execution evidence.

## Validation and structure

`tests/` contains analytics and launcher checks. `.github/workflows/native.yml` defines future Windows/macOS CI with Python 3.11–3.13, including an actual startup smoke test. The presence of that workflow is not evidence that it has run. See [verification notes](docs/VERIFICATION.md) for the executed checks and known limits.

| Path | Purpose |
|---|---|
| `backend/` | Ingestion, cleaning, analytics, prediction, Python MapReduce/replay, API and optional Spark/Hadoop jobs |
| `frontend/` | Next.js/TypeScript source; `out/` is the bundled UI |
| `data/raw/` | Saved per-city source CSV and provenance |
| `data/processed/` | Clean Parquet, manifest, predictions and optional processing-engine evidence |
| `setup.py`, `run.py` | Project-local dependency setup and readiness-aware server launcher |
| `docs/` | Syllabus mapping, data ethics, Spark/Hadoop instructions and reference exercises |

To build the portable ZIP, run `python scripts/package_release.py`. It creates `dist/Weather_Data_Analysis_Windows_Mac_v3.zip`, with top-level folder `Weather_Data_Analysis`, source, data and the static UI, an internal file SHA256 manifest, and an external archive checksum. Downloaded `.runtime/`, virtual environments, build caches, dependencies and design assets are excluded. Existing archives are preserved; use a different `--output`, or `--overwrite` to keep a dated backup before rebuilding.
