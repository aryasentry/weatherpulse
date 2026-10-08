# Verification evidence

This file separates locally executed checks, completed hosted CI and unverified optional-engine/platform cases.

## Completed native GitHub Actions matrix

On **8 October 2026**, [run 37815484065](https://github.com/aryasentry/weatherpulse/actions/runs/37815484065) completed successfully for application commit **6563fa2**. All six jobs passed: Windows and macOS, each with Python **3.11, 3.12 and 3.13**. Subsequent documentation-only updates record this run without changing the tested application code.

Each job checked out into a path containing spaces, created a fresh project environment through `setup.py`, ran the automated suite and executed `scripts/smoke_test.py` against the real bundled application. The smoke test verified ready health, HTML, analytics, filtered CSV, pipeline/replay, Hadoop Explorer, invalid-city rejection, interrupt shutdown and release of the listening port.

The inspected Windows 3.12 log reported **54 passed, 1 skipped and 22 subtests passed**; the skipped check is explicitly POSIX-only TCP restart behavior. The inspected macOS 3.13 log reported **55 passed and 22 subtests passed**. Both reported the same upstream Starlette/AnyIO deprecation warning. All other matrix jobs also completed successfully.

The Windows shutdown check initially exposed an unbounded process wait that delayed Python signal handling. The launcher now uses bounded waits; the same native Windows smoke test passed after the fix. The Hadoop environment-configuration unit test isolates Java discovery so the base suite needs no optional JDK.

Hosted CI verifies the Python setup/launcher path on its runner operating systems. It does not verify a particular user's desktop, batch-file double-click interaction, browser rendering on Windows, or native Windows Spark/Hadoop execution. UI browser checks and real optional-engine runs were performed separately on the development Mac.

## Native launcher checks

- Standard-library launcher unit tests were executed on the development macOS host. They cover Python 3.11–3.13 acceptance, rejection of unsupported versions, required bundle files, paths containing spaces, a genuinely occupied local TCP port, and restart after recently closed TCP connections.
- Shell syntax for the macOS start/setup wrappers is checked with `bash -n`.
- Official PyPI binary dependency resolution succeeded for Windows x64 / CPython 3.11 using pip's dry-run cross-platform resolver. This checks available compatible wheels, not native Windows execution.
- `scripts/smoke_test.py` was executed successfully on macOS using the actual bundle and an unrelated working directory containing spaces. It read ready health, served bundled HTML, read real-data analytics, checked filtered CSV/pipeline/replay/invalid-city endpoints, interrupted the launcher, and verified the server no longer accepted connections.
- The complete `python -m pytest -q` suite passed **55 tests and 22 subtests** on the development Python 3.13 environment after the Hadoop Explorer addition and again after the Windows shutdown fix. One upstream Starlette/AnyIO deprecation warning was reported. Python 3.11/3.12 runtime execution is now covered by the completed matrix above.

The parent integration process records the final dataset, browser, extracted-bundle and full-suite results in its delivery report. Do not infer that those checks have passed from the presence of this document or smoke script.

## Spark evidence recorded on macOS

The integration process executed Spark 4.0.1 in native local mode on macOS. It independently cleaned **438,240 hourly rows** and compared **600 city/month groups**, **five metrics per group**, against pandas, with parity passing. The recorded execution took **14.105 seconds**; timing is specific to that run. Inspect `data/processed/spark_evidence.json` for the execution metadata and dataset hash. This establishes real local Spark computation; it does not establish HDFS or a distributed Hadoop cluster.

## Analytical evidence

The manifest records 438,240 input/cleaned rows, ten cities, and zero invalid, duplicate or missing metric cells for this download. The model uses 1,454 training days per city through 2024-12-31 and 365 held-out days in 2025. Its one-day-ahead evaluation uses observed lag values; it does not constitute an operational forecast. Hyderabad model MAE was 0.588072 °C versus persistence MAE 0.570559 °C, so persistence was better there. The model beat persistence only for Bengaluru and Kolkata in this run. Inspect the prediction artifact after rebuilding rather than assuming those results persist.

The reference Streaming mapper/reducer was checked locally with a small explicit stdin/stdout example, including invalid-value handling and hand-checked temperature/rainfall totals. This is not Hadoop execution.

## Native Hadoop storage evidence on macOS

The optional Apache Hadoop 3.5.0 path started actual NameNode/DataNode processes. The NameNode interface reported safe mode off, one live/zero dead DataNodes and approximately 24.13 MiB of weather files stored in HDFS (25,302,546 bytes at the recorded check). All five service listeners were checked on loopback.

Final Hadoop Streaming job `job_local949140952_0001` completed using HDFS input/output and LocalJobRunner after existing HDFS was stopped and restarted without reformatting its data. The final counters recorded 438,240 input rows, 438,240 clean rows and zero invalid rows. All 600 city/month groups and five metrics matched independently prepared pandas aggregates, maximum absolute error 2.33 × 10⁻¹² with tolerance 10⁻⁶. Recorded duration was 55.57 seconds including HDFS restart. The API independently reported `hadoop_verified=true` alongside verified Spark evidence. Evidence, monthly output and bounded job log are retained under `data/processed/`. This is native one-machine Hadoop execution, without YARN or multiple workers.

The final browser check displayed the real Hadoop engine/job ID, counts, HDFS paths and parity result. At a 490-pixel viewport, document width equaled viewport width; no console errors were observed. HDFS service processes remained live after that check; saved execution proof and live service status are distinct.

## Platform limitations

The development environment is macOS; the completed hosted Windows/macOS matrix is recorded above. Optional Spark and native Mac Hadoop have separate prerequisites and execution evidence; base-dashboard launch requires neither engine. Native Windows Spark/Hadoop runtime execution remains unverified. Hadoop's LocalJobRunner executes on one Mac and does not establish YARN or a multi-machine deployment.

Physical space-path testing of optional Hadoop failed with Apache shell/JVM/DataNode path handling errors. Hadoop is supported only when the whole project path has no whitespace; the scripts enforce that restriction. The release folder is named `Weather_Data_Analysis`. The base dashboard's successful space-path checks remain valid.

## Hadoop Explorer

The read-only Explorer route was verified with live NameNode JMX/WebHDFS and with the owned HDFS services stopped. Offline telemetry was unavailable while current saved job evidence remained verified. Restart restored the original namespace and live observations. Three real source records pass through the production mapper/reducer for the teaching trace, separately from a full-month result rechecked against current Parquet. Tests cover offline transport, bounded requests, allowlisted paths, malformed sources and stale/tampered evidence. The three browser tabs, city/month selection, six steps and playback controls passed; narrow/desktop layouts had no page-width overflow. See `DELIVERY.md` for exact observations and `LIFECYCLE.md` for the scope audit.
