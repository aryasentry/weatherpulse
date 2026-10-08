# Weather Data Analysis — delivery verification

Verified on **8 October 2026**, on macOS with Python 3.13.13, Node 24.19.0 and Java 17.0.20.1. The required delivered runtime is Python 3.11–3.13; Node is only needed to rebuild the Next.js interface, and Java is needed to rerun optional Spark or Hadoop processing.

## Implemented and executed

| Check | Observed result |
|---|---|
| Real source ingestion | 438,240 hourly ERA5 reanalysis records, ten Indian cities, 2021–2025; all ten downloads succeeded, with request URLs, timestamps and raw-file checksums |
| Data processing | 438,240 clean rows; zero duplicate, invalid or missing metric cells in this source download |
| Native Apache Spark 4.0.1 | 438,240 rows processed in local[2]; all 600 city/month groups and five metrics per group matched independent pandas aggregates; 14.105 seconds for that run |
| Machine learning | Ten Random Forest evaluations; 1,454 training days per city through 2024-12-31, 365 held-out days in 2025; persistence baseline reported alongside model errors |
| Python MapReduce | Partition/map/shuffle/reduce demonstration completed over the whole archive; separate from the optional Apache Hadoop job |
| Native Apache Hadoop 3.5.0 HDFS | NameNode interface active, safe mode off, one live/zero dead DataNodes and approximately 24.13 MiB stored at the recorded check; all five configured listeners bound to loopback |
| Hadoop Streaming MapReduce | Actual LocalJobRunner job `job_local949140952_0001` read/wrote HDFS; final counters 438,240 input/clean rows, zero invalid; all 600 groups and five metrics matched pandas, max error 2.33 × 10⁻¹²; 55.57 seconds including HDFS restart |
| Stream concepts | Entire historical archive replayed with a 50-row reservoir; dashboard replay processed 10,000 Hyderabad records and retained 30 samples |
| Production frontend | Next.js static production export and TypeScript validation passed; generated interface served by FastAPI |
| Automated suite | 55 tests and 22 subtests passed on Python 3.13 after the Hadoop Explorer addition; one upstream Starlette/AnyIO deprecation warning |
| Dependency integrity | `python -m pip check` passed; Windows x64 CPython 3.11 wheel-only dependency resolution succeeded against official PyPI |
| Native launcher smoke | Ready health, bundled HTML, real analytics, CSV, pipeline, replay, invalid-city rejection, Ctrl+C shutdown and listener release passed from a different working directory containing spaces |
| Fresh installation | ZIP extracted into a new path containing spaces; setup created a new environment using only the base requirements; actual launch/API/shutdown smoke passed without Node, Java or Spark in that environment |
| Earlier Hadoop v2 release | Candidate ZIP contained 119 files plus an internal SHA256 manifest; every hash and ZIP integrity check passed. Extracted app launch/API/CSV/replay/shutdown passed using the existing validated Python dependencies, and the extracted code recognized current Hadoop and Spark proof. Runtime binaries and environments were excluded. |
| Hadoop Explorer v3 release | 127 files plus internal SHA256 manifest; all hashes matched the current source. Extracted launch, real-data analytics, CSV, pipeline, replay, Explorer trace/full-month proof, invalid-city handling and clean shutdown passed from a path with spaces, using the existing validated Python environment. No new dependency installation was claimed for this v3 check. |
| Independent review | Data provenance, checksums, forecast split/features, analytics semantics and native path handling reviewed; no material finding left open |

## Browser verification

The flow tested was: load the actual app, change city and dates, inspect analytics and predictions, open Spark evidence/SQL and verified Hadoop evidence, run a historical replay and download selected records.

- Page title and main problem-statement title are **Weather Data Analysis**. No framework error overlay or blank application was observed.
- Selecting Hyderabad changed the full-period result to 43,824 rows. Changing the date range to 2025 produced 8,760 rows and recomputed statistics.
- The original four navigation views rendered real API content; a fifth Hadoop Explorer view was added and checked separately. The overview shows all ten city labels; the analytical view shows sample statistics and Pearson correlations; the prediction view shows the fixed holdout scope and both model and baseline errors.
- The pipeline displayed real Spark engine/version, clean-row and group counts, parity evidence and the actual executed SQL. The replay control returned 10,000 processed records, a 30-record reservoir and actual sample rows.
- The Hadoop panel displayed the verified job ID, 438,240 rows, 600 groups, HDFS input/output paths and parity evidence. Independent API reads reported both Hadoop and Spark verified. The 490-pixel layout had no horizontal overflow, and no browser console errors were observed in the final Hadoop check.
- Clicking Export CSV downloaded a file independently checked to contain exactly 43,824 Hyderabad records from 2021-01-01 00:00 through 2025-12-31 23:00.
- The server was deliberately stopped. The already-loaded interface displayed its failure state; after restarting, **Retry** restored the real dashboard. The expected connection-refused message from this deliberate failure is not an unexplained application error.
- Desktop and narrow layouts were inspected. At the normal 490-pixel narrow viewport, document width equaled viewport width, controls remained readable, and mobile navigation worked. A full-page screenshot with a forced viewport was clipped by the in-app capture path; native viewport screenshots were used for visual verification instead.

## Hadoop Explorer verification

- The `#hadoop-explorer` direct link loads the fifth view with Inside HDFS, Follow a record and Lifecycle & tools tabs.
- Live reads reported Apache Hadoop 3.5.0, one live DataNode, safe mode off, ten raw CSV files, 13 namespace blocks and 25,583,616 HDFS bytes (24.40 MiB, including output files). The Delhi input is one real block with replication one; block size and actual length are presented separately.
- Selecting the DataNode changed its explanation. Selecting Delhi and January 2021 produced three actual CSV rows and mapper emissions; the sample mean temperature was 6.13 °C, while the independently rechecked full-month result had 744 rows, 13.31 °C mean temperature and 30.30 mm precipitation.
- All six teaching steps and Next/Previous/Reset/Play/Pause controls worked. Completed-job counters stayed separate from the sample. Playback launched no new Hadoop job.
- Stopping the owned Hadoop services produced unavailable live telemetry while saved job verification and the real-record trace remained available. Restart and refresh restored the live view with existing HDFS data preserved.
- The three Explorer tabs were inspected. Narrow and desktop layouts had no document-wide horizontal overflow (observed CSS widths 597 and 984 pixels). The desktop viewport override was reset. The final browser error log was empty.
- The actual lineage distinguishes the pandas/Parquet serving path from separate Hadoop and Spark verification branches. `LIFECYCLE.md` records implemented batch stages, partial operations and unimplemented retention/restore capabilities.

## Limits and syllabus fit

Actual Windows setup, startup, shutdown, Spark and Hadoop execution were **not run on a Windows host**. Binary dependency resolution, native scripts and the future CI matrix support base-dashboard portability but are not substituted for Windows runtime evidence. Python 3.11/3.12 runtime execution is likewise not claimed from the Python 3.13 run.

Optional native Hadoop requires the entire project path to contain no whitespace. Physical space-path Hadoop testing exposed upstream shell/JVM/DataNode path errors; the scripts therefore reject that configuration with rename/move instructions. The v3 ZIP's top-level folder is `Weather_Data_Analysis`, and its parent path must also avoid whitespace. This limitation is specific to optional Hadoop: the base Python dashboard remains tested in paths containing spaces.

The project preserves the provided title and maps to data management, statistics, stream sampling, processing and visualization topics. `SYLLABUS.md` identifies the exact boundaries. The optional native Mac Hadoop setup executed real HDFS and a verified Hadoop Streaming job with LocalJobRunner; its version/counters/HDFS paths/parity are retained in Hadoop evidence. YARN, multi-node Hadoop, Hive, Pig, Sqoop, HBase, ZooKeeper and Mahout remain extensions. This is a single-machine application with optional local processing engines; it makes no multi-machine or big-data speedup claim.

The Hyderabad model MAE was 0.588072 °C versus persistence MAE 0.570559 °C, so the simple baseline was better there. Reanalysis analysis and historical one-day evaluation are not a live weather forecasting or warning service.

## Start and maintain

Extract the delivered `Weather_Data_Analysis_Windows_Mac_v3.zip` (or the earlier base release), then run `Start-Windows.bat` or `Start-Mac.command`. The launcher automatically chooses a free local port from 8000 through 8010. The first run creates a local environment and downloads pinned packages. Later dashboard runs work with the bundled data without an internet connection. Keep the terminal open while using the app.

See `LIFECYCLE.md` for the full lifecycle assessment, `README.md` for setup and troubleshooting, `SYLLABUS.md` for the course mapping/viva, `SPARK.md` for optional Spark, and `HADOOP.md` for optional native Mac HDFS/MapReduce. Regenerating the data invalidates dependent model/demo/Spark/Hadoop evidence; rerun those jobs before showing new results. The downloaded Hadoop runtime is not inside the release ZIP; its setup downloads and verifies it separately.

## Product copy and design gallery update

Coursework branding, syllabus tables and lengthy scope/roadmap blocks were removed from the current app UI. The lifecycle audit remains in the documentation. The Hadoop tab is now called Data flow and retains concise lineage and tool roles. The live Pipeline page was browser-checked to contain no syllabus/CBP block.

`frontend/public/ui-styles.html` is a standalone ten-style design chooser with embedded real 2025 data. All ten desktop and 388-pixel phone previews rendered their plot without page overflow; city/metric changes, shortlist persistence and theme filtering passed. The downloaded CSV contained 12 months and matched the displayed mean city precipitation. The final browser error/warning log was empty. Next.js production export and TypeScript passed. This UI update is in the workspace; the earlier v3 ZIP remains the historical Explorer release until a new release is packaged after design selection.

## Nordic interface — 8 October 2026

The user's selected **05 — Nordic** design is applied to the running app and static export. It uses light top navigation, a vertical Overview metric rail, a wide temperature chart and a real city archive table. Analytics, Predictions, Pipeline and Hadoop Explorer use the same palette and typography. Small text was darkened from the gallery's original muted colour for legibility.

Production build and TypeScript passed. Browser checks covered all five views, Delhi filtering (43,824 rows and matching summary values), Hadoop HDFS/record/data-flow sections, and Next/Reset teaching controls. There was no document-wide overflow at 1280, 820 or 390 CSS pixels; the phone menu opened and closed through navigation. Browser error and warning logs were empty. Temporary viewport overrides were reset. The backend was unchanged, so the earlier backend test run was not repeated for this restyle.

The prior cleaned UI was archived before editing. Its ZIP extracted successfully and all 48 saved files matched the per-file SHA256 manifest. `UI-VERSIONS.md` records the local snapshot and rollback procedure. The older v3 release ZIP is preserved unchanged; Nordic is currently in the workspace and running app.
