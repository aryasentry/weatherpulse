"""Execute real local Spark SQL and verify its output against pandas.

No Hadoop services or downloaded winutils binaries are used. Only small,
aggregated results are collected; PyArrow serializes those results to a local
Parquet file so Hadoop's native Windows file-output helpers are unnecessary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("records", "temperature", "precipitation", "humidity", "wind_speed")
QUERY = """SELECT city, date_format(time, 'yyyy-MM') AS month,
       COUNT(*) AS records, AVG(temperature) AS temperature,
       SUM(precipitation) AS precipitation, AVG(humidity) AS humidity,
       AVG(wind_speed) AS wind_speed
FROM weather
GROUP BY city, date_format(time, 'yyyy-MM')
ORDER BY city, month"""


def compare_aggregates(actual: list[dict], expected: list[dict]) -> dict:
    """Compare keyed groups and all metrics, rejecting duplicate/NaN results."""
    key = lambda row: (row["city"], row["month"])
    left, right = {key(r): r for r in actual}, {key(r): r for r in expected}
    errors = []
    if len(left) != len(actual) or len(right) != len(expected):
        errors.append("Duplicate city-month groups")
    if left.keys() != right.keys():
        errors.append("City-month groups differ")
    for group in left.keys() & right.keys():
        for metric in METRICS:
            a, b = float(left[group][metric]), float(right[group][metric])
            if not (math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-6)):
                errors.append(f"{group[0]} {group[1]} {metric}: Spark={a}, pandas={b}")
    return {"passed": not errors, "groups_compared": len(left.keys() & right.keys()),
            "metrics_per_group": len(METRICS), "errors": errors[:20]}


def run(data_dir: Path, master: str = "local[2]") -> dict:
    import pandas as pd
    from backend.config import CITIES
    try:
        import pyspark
        from pyspark.sql import SparkSession, functions as F
    except ImportError as exc:
        raise RuntimeError("Install the optional engine: python -m pip install -r requirements-spark.txt") from exc
    if shutil.which("java") is None and not os.environ.get("JAVA_HOME"):
        raise RuntimeError("Spark requires Java 17 or 21. Set JAVA_HOME or put java on PATH.")
    parquet = data_dir / "processed" / "weather.parquet"
    raw_files = sorted((data_dir / "raw").glob("*.csv"))
    if not parquet.exists() or not raw_files:
        raise RuntimeError("Run backend.ingest and backend.pipeline before the Spark verification job.")
    evidence_path = data_dir / "processed" / "spark_evidence.json"
    # A failed attempt must not leave an earlier result displayed as this run.
    started = time.perf_counter()
    dataset_hash = hashlib.sha256(parquet.read_bytes()).hexdigest()
    evidence = {"status": "running", "parity_passed": False, "dataset_sha256": dataset_hash,
                "generated_at": datetime.now(timezone.utc).isoformat(), "master": master}
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    spark = None
    try:
        spark = (SparkSession.builder.appName("Weather Data Analysis")
                 .master(master).config("spark.ui.enabled", "false")
                 .config("spark.driver.bindAddress", "127.0.0.1")
                 .config("spark.sql.session.timeZone", "Asia/Kolkata")
                 .config("spark.sql.shuffle.partitions", "4")
                 .config("spark.sql.ansi.enabled", "false").getOrCreate())
        spark.sparkContext.setLogLevel("ERROR")
        # All fields begin as strings so corrupt numeric cells can be rejected.
        columns = ["city", "time", "temperature", "humidity", "precipitation", "wind_speed", "latitude", "longitude"]
        frame = spark.read.option("header", True).option("inferSchema", False).csv([str(p) for p in raw_files])
        input_rows = frame.count()
        frame = frame.withColumn("time", F.to_timestamp("time"))
        for column in columns[2:]:
            frame = frame.withColumn(column, F.col(column).cast("double"))
        frame = frame.dropna(subset=columns)
        frame = frame.filter(
            F.col("city").isin([city["name"] for city in CITIES])
            & F.col("temperature").between(-90, 60)
            & F.col("humidity").between(0, 100)
            & F.col("precipitation").between(0, 500)
            & F.col("wind_speed").between(0, 400)
            & F.col("latitude").between(-90, 90)
            & F.col("longitude").between(-180, 180)
        ).dropDuplicates(["city", "time"]).cache()
        clean_rows = frame.count()
        frame.createOrReplaceTempView("weather")
        results = [row.asDict() for row in spark.sql(QUERY).collect()]
        # Independent, already-cleaned pandas dataset is the reference.
        reference = pd.read_parquet(parquet)
        reference["month"] = pd.to_datetime(reference["time"]).dt.strftime("%Y-%m")
        reference_rows = (reference.groupby(["city", "month"], as_index=False).agg(
            records=("temperature", "size"), temperature=("temperature", "mean"),
            precipitation=("precipitation", "sum"), humidity=("humidity", "mean"),
            wind_speed=("wind_speed", "mean")).to_dict(orient="records"))
        comparison = compare_aggregates(results, reference_rows)
        if clean_rows != len(reference):
            comparison["passed"] = False
            comparison["errors"].append(f"Clean row mismatch: {clean_rows} versus {len(reference)}")
        output = data_dir / "processed" / "spark_monthly.parquet"
        pd.DataFrame(results).to_parquet(output, index=False)
        evidence.update({"status": "verified" if comparison["passed"] else "failed",
                         "parity_passed": comparison["passed"], "engine": f"Apache Spark {pyspark.__version__} ({master})",
                         "input_rows": input_rows, "clean_rows": clean_rows,
                         "city_count": len({row["city"] for row in results}), "monthly_groups": len(results),
                         "query": QUERY, "comparison": comparison, "artifacts": [output.name],
                         "note": "Real local Spark SQL computation; aggregate results serialized with PyArrow. Single-machine execution, no HDFS or distributed cluster.",
                         "duration_seconds": round(time.perf_counter() - started, 3)})
        if not comparison["passed"]:
            raise RuntimeError("Spark/pandas parity failed: " + "; ".join(comparison["errors"]))
        return evidence
    except Exception as exc:
        evidence.update(status="failed", parity_passed=False, error=str(exc),
                        duration_seconds=round(time.perf_counter() - started, 3))
        raise
    finally:
        evidence_path.write_text(json.dumps(evidence, indent=2, allow_nan=False), encoding="utf-8")
        if spark is not None:
            spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        result = run(args.data_dir.resolve())
    except Exception as exc:
        print(f"Spark verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
