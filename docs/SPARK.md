# Optional native Spark computation

The dashboard needs only Python 3.11–3.13 and the bundled UI/data. Run Spark only to produce additional computation evidence. Use **Java 17 or 21** and **PySpark 4.0.1**, in the same project environment. [Spark's installation documentation](https://spark.apache.org/docs/4.0.1/api/python/getting_started/install.html) describes its supported prerequisites.

Install a JDK using its normal native Windows/macOS installer, then verify `java -version`. If required, set `JAVA_HOME` to that installed JDK for your terminal session and include its `bin` on PATH. This project's setup does not install Java or modify your system environment.

```powershell
# Windows PowerShell, in the project folder
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple pyspark==4.0.1
.\.venv\Scripts\python.exe -m backend.spark_job
```

```bash
# macOS, in the project folder
.venv/bin/python -m pip install --index-url https://pypi.org/simple pyspark==4.0.1
.venv/bin/python -m backend.spark_job
```

See `python -m backend.spark_job --help` for job options. The job reads saved weather files, performs real local Spark aggregation, writes result Parquet and `data/processed/spark_evidence.json`, and compares independent totals with the processed data. Inspect its exit status and evidence before claiming success. The dashboard should reflect the evidence file after it is created.

Spark local mode is a one-machine computation. These Spark steps do not start HDFS; the separate [native macOS Hadoop path](HADOOP.md) supplies HDFS and a Hadoop Streaming job. If your native Windows Spark build reports Hadoop native-library or filesystem permission errors, keep using the validated Python dashboard and record Spark as unverified on that machine; do not download unidentified `winutils.exe` binaries or silently switch to a VM. A successful macOS Spark run does not prove Windows Spark execution.
