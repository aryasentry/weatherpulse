# Hadoop ecosystem reference exercises

These reference files extend Weather Data Analysis for course discussion. The base dashboard uses local files, while [the optional native macOS Hadoop path](../HADOOP.md) adds real HDFS and a Hadoop Streaming job using the production modules under `backend/hadoop_streaming/`. `python -m backend.mapreduce` remains the separate Python-only map/shuffle/reduce demonstration. The examples in this directory are teaching references, rather than the production Hadoop job.

- `hadoop_mapper.py` / `hadoop_reducer.py`: Hadoop Streaming-compatible city/day temperature and precipitation aggregation. They also accept ordinary stdin/stdout for local inspection. They have not been executed on Hadoop here.
- `hadoop-reference.md`: HDFS dataflow, Streaming, HiveQL, Pig and Sqoop reference commands. Paths/connection settings are placeholders for the independent environment.

The examples use the raw weather CSV schema, assume one hourly observation per city/time and skip invalid/missing numeric records. They do not duplicate the app's full cleaning/provenance pipeline. For rigorous parity, use the app's cleaned data and independently verify row counts first. Reducer input must be sorted by its composite city/date key. Do not use this reducer as a combiner: its final output schema differs from the mapper values.
