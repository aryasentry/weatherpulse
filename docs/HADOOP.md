# Weather Data Analysis — optional native Hadoop on macOS

The base Windows/macOS dashboard requires Python 3.11–3.13, the bundled UI/data and a browser. This separate path adds **Apache Hadoop 3.5.0** on macOS with **Java 17**: real HDFS storage, a NameNode, one DataNode, and a Hadoop Streaming MapReduce job using LocalJobRunner. See [Apache Hadoop 3.5.0 documentation](https://hadoop.apache.org/docs/r3.5.0/), which requires Java 17 for its server components.

The Hadoop runtime is downloaded from Apache and verified using its published SHA512 checksum. Downloads, configuration, HDFS storage and logs stay under this project's `.runtime/`. That large runtime directory is excluded from source control and the release ZIP; first-time Hadoop setup requires network access and additional disk space. Subsequent Hadoop starts can use the previously verified local download/receipt without internet access. The saved execution evidence and results can be included in the small dashboard bundle.

## Start, run and stop

**Use a full project path without whitespace, including all parent directories.** The release extracts into `Weather_Data_Analysis`; a location such as `/Users/yourname/Documents/Weather_Data_Analysis` is appropriate. A parent folder named `Course Projects` would still make the full path unsupported for this Hadoop runtime. Move or rename the extracted folder/parent path before optional Hadoop setup. The scripts refuse whitespace paths with an actionable message.

Actual macOS testing exposed Apache Hadoop shell/JVM failures when the physical project path contained spaces, including a DataNode formatting exception with `%20` in the path. That Hadoop configuration is not supported by this release. **The base Python dashboard still supports paths containing spaces** and passed its extracted-bundle checks independently.

From the project folder, after the regular Python setup, verify `java -version` reports Java 17. A native Temurin JDK 17 is used in the development environment. The scripts discover the installed JDK, or accept `--java-home` for a specific installation; they do not install Java or alter your system environment.

```bash
.venv/bin/python scripts/setup_hadoop.py
.venv/bin/python scripts/hadoop_native.py start
.venv/bin/python scripts/hadoop_native.py run
.venv/bin/python scripts/hadoop_native.py status
```

Alternatively, use **Start-Hadoop-Mac.command** to perform Hadoop setup, start HDFS and run the weather job. The ordinary **Start-Mac.command** starts only the dashboard. Hadoop services are separate processes; stop them explicitly when finished:

```bash
.venv/bin/python scripts/hadoop_native.py stop
```

**Stop-Hadoop-Mac.command** performs the same bounded service shutdown. Stopping Hadoop preserves project-local HDFS files for later runs. Do not delete or reformat the HDFS storage just to stop it.

The HDFS endpoint is `hdfs://127.0.0.1:19000`. When running, open the [NameNode interface](http://127.0.0.1:19870/) to inspect its filesystem and DataNode state. Configuration is in `.runtime/hadoop-state/conf/`; HDFS metadata/data is in its `namenode/` and `datanode/` directories, with service logs under `logs/`. These services bind to loopback for a one-user classroom demonstration. No SSH daemon, virtual machine, container, WSL, YARN ResourceManager or NodeManager is required.

During the native macOS integration run, the NameNode 3.5.0 interface showed safe mode off, **one live DataNode**, zero dead DataNodes and approximately **24.13 MiB of weather data in HDFS** (25,302,546 bytes at the recorded check). All five configured RPC/HTTP/data listeners were checked on loopback. This establishes actual HDFS execution; MapReduce aggregate verification is recorded separately in the job evidence.

## Dataflow and evidence

The final native macOS run completed Hadoop job **`job_local949140952_0001`** in **55.57 seconds including HDFS restart**. Its final counters recorded **438,240 input rows**, **438,240 cleaned rows** and **zero invalid rows**. The resulting **600 city/month groups** matched the independent pandas result across all **five metrics**, with maximum absolute error **2.33 × 10⁻¹²** against tolerance **10⁻⁶**. This is actual Hadoop Streaming execution with HDFS input/output and LocalJobRunner, rather than the Python-only demonstration. Counts/timing describe this recorded run; consult regenerated evidence after subsequent runs.

The job uploads the ten attributed raw city CSVs into a content-addressed `/weather-data-analysis/raw/<source-hash>` directory in HDFS. Hadoop Streaming reads them, invokes the production Python mapper/reducer under `backend/hadoop_streaming/`, and writes city/month results to a unique `/weather-data-analysis/results/<run-id>` directory in HDFS. The complete archive has 438,240 observations and 600 city/month groups; inspect observed counters and parity evidence after a refresh.

The run compares Hadoop output with independently prepared pandas aggregates. A successful result must show matching groups, row counts and metrics, and evidence associated with the current dataset checksum. Inspect these durable artifacts:

- `data/processed/hadoop_evidence.json`: execution mode/version, job ID, input/output HDFS paths, source/dataset checksums, observed counts, timing and comparison results.
- `data/processed/hadoop-monthly.json`: actual Hadoop city/month results with counts, mean temperature/humidity/wind and total precipitation.
- `data/processed/hadoop-job.log`: bounded job log containing MapReduce completion and counters. This one deliberate proof log is retained in the release; service/runtime logs are excluded.

A source-data refresh requires rebuilding processing/model/Spark/Hadoop evidence. Saved success evidence is historical proof of that computation; it does not mean HDFS services are currently running. Use `status` to inspect live service state.

`backend.mapreduce` is the original Python-only map/shuffle/reduce demonstration. The optional Hadoop run is different: Apache Hadoop launches the Streaming job and reads/writes real HDFS paths. LocalJobRunner executes MapReduce tasks on this Mac rather than distributing them through YARN. A single DataNode and replication factor one do not demonstrate multi-node replication, high availability or failure tolerance.

The teaching examples under `docs/examples/` remain separate reference exercises. Hive, Pig, Sqoop, HBase, ZooKeeper and Mahout are not installed or executed by this Hadoop path. Word count, frequent-word mining and distributed K-means are also distinct syllabus exercises rather than weather aggregation results.

## Troubleshooting and portability

- Missing Java or wrong Java version: provide a native JDK 17 installation, then retry with the script's `--java-home` option if necessary.
- Whitespace in project path: move/rename the folder or its parent directories so the entire path has no whitespace, then rerun. Changing only the last folder name is insufficient when a parent still contains spaces.
- Download/checksum failure: retry the official setup; preserve the verification failure rather than extracting an unchecked archive.
- HDFS port occupied: read the reported conflict and close only a service you own. Avoid changing or killing unrelated applications.
- MapReduce failure: inspect the reported Hadoop logs/evidence; do not relabel an incomplete run as verified.
- Dashboard-only use: stop Hadoop and keep using the delivered local Parquet/UI files.

Native Hadoop runtime execution on Windows is **unverified**. The tested base dashboard setup remains independent of Hadoop. This Mac demonstration does not make a claim about Windows Hadoop helper binaries or a distributed deployment.
