# Reference commands for an existing Hadoop environment

**Status: these specific commands are educational references, rather than execution evidence.** The production native Mac HDFS/Streaming setup is documented in [HADOOP.md](../HADOOP.md). Adapt the examples below to an existing course environment, including paths, versions, privileges and SQL connections. They are not required for Windows/macOS dashboard startup. Hive/Pig/Sqoop commands remain unexecuted extensions.

## HDFS and Hadoop Streaming

```text
hdfs dfs -mkdir -p /course/weather/raw
hdfs dfs -put data/raw/*.csv /course/weather/raw/
hdfs dfs -ls /course/weather/raw
hdfs dfs -du -h /course/weather/raw
hdfs dfs -cat /course/weather/raw/hyderabad.csv
```

HDFS splits files into replicated blocks; a NameNode maintains filesystem metadata and DataNodes store blocks. MapReduce reads input splits, maps observations, shuffles by city/date, and reduces sums/counts. Multiple files should retain the header-skip behavior in the mapper.

```text
hadoop jar <HADOOP_STREAMING_JAR> -files docs/examples/hadoop_mapper.py,docs/examples/hadoop_reducer.py -mapper "python3 hadoop_mapper.py" -reducer "python3 hadoop_reducer.py" -input /course/weather/raw -output /course/weather/daily-output
hdfs dfs -cat /course/weather/daily-output/part-*
```

Python must be available on every worker. The output directory must not already exist. This reducer is not a valid combiner. Modern Hadoop versions, security policies and CSV input splitting may need additional configuration. For full CSV quoting/multiline support, use a dedicated CSV input format; the project's raw hourly files have simple one-line rows.

## HiveQL

An external table describes the same raw CSV without claiming that Hive performed the local app's cleaning. `OpenCSVSerde` stores fields as text, so cast numeric values during aggregation. Header skipping should be configured/verified for the target Hive version and input files.

```sql
CREATE EXTERNAL TABLE weather_raw (
  city STRING, time_text STRING, temperature_text STRING,
  humidity_text STRING, precipitation_text STRING, wind_speed_text STRING,
  latitude_text STRING, longitude_text STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/course/weather/raw'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT city, COUNT(*) AS observations,
       MIN(CAST(temperature_text AS DOUBLE)) AS min_temperature,
       MAX(CAST(temperature_text AS DOUBLE)) AS max_temperature
FROM weather_raw GROUP BY city;

SELECT COUNT(DISTINCT city) AS unique_cities FROM weather_raw;

SELECT city, SUBSTR(time_text, 1, 10) AS day,
       SUM(CAST(precipitation_text AS DOUBLE)) AS rainfall_mm
FROM weather_raw GROUP BY city, SUBSTR(time_text, 1, 10);
```

Weather-city counts adapt the grouping concept from the syllabus's property/state examples; they do not constitute results for that original dataset. Reject invalid values and compare counts with the local processed manifest before asserting parity.

## Pig daily aggregation

```pig
raw = LOAD '/course/weather/raw' USING PigStorage(',') AS
  (city:chararray, stamp:chararray, temperature:chararray,
   humidity:chararray, rain:chararray, wind:chararray,
   latitude:chararray, longitude:chararray);
rows = FILTER raw BY city != 'city' AND rain IS NOT NULL;
daily = FOREACH rows GENERATE city, SUBSTRING(stamp,0,10) AS day,
  (double)rain AS rainfall;
groups = GROUP daily BY (city,day);
totals = FOREACH groups GENERATE FLATTEN(group), SUM(daily.rainfall);
DUMP totals;
```

PigStorage is sufficient for this simple CSV layout; general CSV quoting needs a dedicated loader. This adapts hourly/day log aggregation to weather data. Check timestamp parsing, numeric casts and invalid rows in the target Pig version.

## Sqoop relational staging

Create a relational staging table in a separately managed SQL database and load attributed, cleaned data there before transferring it. Do not place passwords directly in commands; use the environment's approved credential mechanism.

```sql
CREATE TABLE weather_hourly (
  id BIGINT PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  observation_time TIMESTAMP NOT NULL,
  temperature DOUBLE PRECISION,
  humidity DOUBLE PRECISION,
  precipitation DOUBLE PRECISION,
  wind_speed DOUBLE PRECISION
);
```

```text
sqoop import --connect <JDBC_URL> --username <USER> -P --table weather_hourly --split-by id --target-dir /course/weather/sql-import
sqoop import --connect <JDBC_URL> --username <USER> -P --table weather_hourly --split-by id --hive-import --hive-table course_weather
sqoop export --connect <JDBC_URL> --username <USER> -P --table weather_hourly_export --export-dir /course/weather/compatible-export --input-fields-terminated-by ','
```

Prepare the export target table and a compatible CSV schema separately; daily Streaming output has a different schema and must not be exported directly into the hourly table. Sqoop requires a compatible JDBC driver and independently configured Hadoop/Hive services.

## Other ecosystem extensions

HBase could store city/time records with a designed row key; ZooKeeper would coordinate services; Mahout could support a separate clustering exercise. None is executed here. The project ML uses scikit-learn, and its optional distributed-computation evidence uses Spark local mode.

Primary references: [Hadoop filesystem shell](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/FileSystemShell.html), [Hadoop Streaming](https://hadoop.apache.org/docs/stable/hadoop-streaming/HadoopStreaming.html), [Hive language manual](https://cwiki.apache.org/confluence/display/Hive/LanguageManual), [Pig documentation](https://pig.apache.org/docs/latest/), and [Sqoop user guide](https://sqoop.apache.org/docs/1.4.7/SqoopUserGuide.html). Consult the specific versions installed in the course environment.
