# Bundled weather data

The project includes historical hourly **ERA5 reanalysis** retrieved through the [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). Data attribution is **Open-Meteo / ERA5 (Copernicus Climate Change Service)**, with the delivered source metadata recording **CC BY 4.0**. These are model-based historical estimates, not a live sensor stream or operational weather forecast.

The delivered archive covers ten Indian cities from 2021-01-01 to 2025-12-31 in Asia/Kolkata: 438,240 hourly rows, 43,824 per city. Each city has a CSV and a provenance JSON recording request parameters, source URL, retrieval time and SHA256. `processed/manifest.json` identifies the exact raw files and cleaned Parquet checksum.

Preserve this attribution, the provenance files and the recorded license when redistributing the data. The application reports rainfall summed over selected city-hours; that sum is not rainfall at one geographic point.

`processed/spark_evidence.json` and `processed/hadoop_evidence.json` describe actual saved single-machine runs. They do not imply the engines are installed or running on a fresh checkout. Their verification is bound to the bundled source and processed-data checksums.

For public distribution, local project paths and the operating-system username in the Hadoop job log/evidence were replaced with placeholders. Execution timestamps, job IDs, counters, HDFS dataset paths, raw/Parquet hashes and aggregate results are unchanged. `${PROJECT_ROOT}` marks a redacted local path, not an environment variable required for setup. New local runs may generate machine-specific paths again; review generated evidence before publishing it.
