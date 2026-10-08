# Weather Data Analysis — syllabus and viva notes

Course: **22PC1CS401 Big Data Analytics**, VNRVJIET, B.Tech VII semester. This mapping follows the course topics supplied in the project brief. It explains project evidence and extensions; it does not claim that one application completes every course/laboratory exercise.

## Problem statement

Historical weather records are difficult to compare across cities and dates without consistent units, cleaning and aggregation. Build a reproducible pipeline that collects attributed hourly reanalysis, validates and stores it, summarizes city/month patterns, identifies educational event categories, evaluates a temperature prediction model against a baseline, and makes results inspectable in a native browser dashboard.

The workload illustrates big-data preparation and processing concepts. A five-year sample across ten cities is manageable on one modern computer; its size alone does not establish a production-scale distributed system. Scaling to many locations, decades or additional source models would motivate partitioned storage and distributed processing.

## Theory units I–V

| Unit and supplied syllabus topics | Executable project evidence | Limits / further work |
|---|---|---|
| **I: Data Management.** Sources/types, preprocessing, collection APIs, storage, multiple sources; big-data platforms, challenges, scalability, analysis vs reporting and tools. | Historical API ingestion, per-city source files, provenance, duplicate/invalid/missing-value handling, Parquet storage, interactive date/city analysis and CSV reporting; optional HDFS storage. | One provider/API is implemented. Multiple cities are not multiple independent providers. Multi-provider harmonization, ingestion scheduling and multi-machine capacity are extensions. |
| **II: Statistics.** Central tendencies, distributions, variance, CLT, sampling/resampling, inference/prediction error, regression and multivariate analysis. | Mean/median, sampled standard deviation and variance (`ddof=1`), precipitation totals, correlations; chronological temperature prediction evaluation with MAE/RMSE and an explicit baseline. | CLT, confidence intervals, bootstrapping and causal inference are explanation/extension topics unless separately executed. Weather observations are temporally dependent, so IID assumptions need justification. Model quality is determined by held-out error, not by having an ML tab. |
| **III: Mining Data Streams.** Stream models, architecture, computing, sampling/filtering; Hadoop comparison/ecosystem and analyzing data. | Bounded historical row replay with online summary/reservoir sampling and filters; Python analytics; optional Spark and Hadoop computations with separate execution evidence. | Replay is historical simulation. It is not a live sensor ingestion system, message broker or production stream cluster. Spark computation and Hadoop services have separate runtime/evidence paths. |
| **IV: Hadoop tools.** HDFS concepts/design/dataflow; developing MapReduce; Pig operators, Hive/HiveQL, HBase, ZooKeeper and Sqoop. | Python map/group/reduce demonstration; optional real HDFS NameNode/DataNode and Hadoop Streaming job through LocalJobRunner; reference Hive/Pig/Sqoop exercises. | Native Hadoop is a single-Mac demonstration, without YARN scheduling or multiple worker machines. Hive, Pig, HBase, ZooKeeper and Sqoop remain extensions. Inspect actual Hadoop evidence before claiming execution. |
| **V: Visualization and ethics.** Tableau/Qlik/D3, privacy and industry cases. | Browser charts, correlations, city comparisons, filtered reporting and visible attribution/units/uncertainty. | The project uses its frontend chart implementation; do not call it Tableau, Qlik or D3 unless those tools are actually used. Tableau/Qlik imports can use exported CSV. Privacy, source rights and limitations are discussed in DATA_ETHICS.md. |

## Laboratory mapping

| Laboratory topic | Project relationship and status |
|---|---|
| **I: HDFS commands** | Optional native Mac setup provides a real NameNode/DataNode and uploads/results in HDFS; inspect its executed commands and listing evidence. Generic shell exercises remain in `examples/hadoop-reference.md`. |
| **II: Word count/frequent words/K-means with MapReduce** | Weather aggregation has a Python-only demonstration and a separate Hadoop Streaming job over HDFS using LocalJobRunner. Word count, frequent words and distributed K-means are distinct exercises and are not claimed as implemented. |
| **III: Hive property min/max/unique/state counts; Pig hourly/day log aggregates** | Weather-specific city counts/min/max and daily rainfall reference queries adapt these aggregation concepts. They are examples for a separate Hadoop environment, not evidence of executing the original property/log datasets. |
| **IV: Sqoop SQL/Hive import/export** | Reference SQL schema and Sqoop import commands show relational-to-Hadoop transfer. No SQL server or Sqoop import/export is run by this bundle. |
| **V: Python/R visualization and Mahout** | Python provides analytics; a browser provides presentation. R and Mahout are not installed or executed. Scikit-learn temperature prediction is not a Mahout job. |

## Architecture and distinctions

```text
Open-Meteo historical API -> attributed per-city CSV
                                |
                      validation and deduplication
                                |
                     pandas -> clean Parquet + manifest
                                |              |
                    statistics + ML      optional Spark SQL
                                |              |
                        FastAPI API <--- execution evidence
                                |
                       bundled Next.js browser UI

Optional separate Mac Hadoop path:
raw city CSV -> real HDFS -> Hadoop Streaming / LocalJobRunner
                              -> HDFS city/month output -> parity evidence
```

**Hadoop** is an ecosystem: HDFS storage, MapReduce batch computation and commonly YARN resource management. The optional native Mac setup runs real HDFS with one NameNode/one DataNode; LocalJobRunner executes an actual Hadoop MapReduce job on the same machine. It does not demonstrate a YARN cluster, multi-node replication or high availability. **Spark** is a computation engine that can use local files or external storage, including HDFS if available. Its separate `local[*]` run here does not prove a Hadoop cluster. **Parquet** is a columnar file format, not a distributed filesystem. **Python MapReduce** demonstrates the dataflow locally and must not be confused with the optional Apache Hadoop job.

## Questions you should be ready to answer

- **What is one observation?** One city and hourly timestamp with weather values and coordinates. Daily/monthly tables are derived aggregates.
- **Why retain raw and processed files?** Raw data plus request provenance support reproducibility; processed files support efficient repeated analysis and explicit quality reporting.
- **What happens to duplicate or invalid records?** Point to the actual quality counts and cleaning code; do not invent dropped-row counts. Explain how missing values are represented and excluded from each statistic.
- **Why use chronological evaluation?** Training on later records and testing earlier records would leak future information. Features must use only information available before the predicted day.
- **Does the model outperform its baseline?** Read the current MAE values. A higher model MAE means it did worse on that hold-out; report that result honestly.
- **Are extreme events official alerts?** No. The thresholds are educational definitions applied to historical reanalysis, not a warning service.
- **Is the stream live?** No. It is a bounded replay used to illustrate incremental summaries and sampling.
- **Is the data distributed?** The base dashboard reads local CSV/Parquet. The optional Hadoop path stores input/output in real HDFS, with one DataNode on one Mac. It is not a multi-machine deployment. Hive/Pig/Sqoop remain extensions.
- **Why is LocalJobRunner still Hadoop MapReduce?** Apache Hadoop submits and runs the Streaming map/reduce tasks and uses HDFS input/output. LocalJobRunner schedules them on this Mac; it does not provide YARN resource scheduling or distributed workers.
- **What would scaling change?** Partition by city/year, enforce schema/provenance, add incremental ingestion and monitoring, compare independent distributed aggregates, then assess storage, scheduling and fault tolerance.

For final demonstration evidence, use the actual dashboard metadata, manifest, predictions and optional Spark/Hadoop evidence rather than hard-coded slide numbers.
