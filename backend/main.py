"""Read-only API and static UI served by a single native Python process."""
import hashlib
import io
import json
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from backend.analytics import load_weather, filter_weather, summarize, monthly_trends, city_comparison, daily_extremes, number
from backend.config import ROOT, RAW, PROCESSED, CITIES, METRICS, SOURCE_URL
from backend.streaming import replay

app=FastAPI(title="Weather Data Analysis",version="1.0.0",description="Local read-only analysis of attributed Open-Meteo ERA5 reanalysis.")


def read_json(name, default=None):
    path=PROCESSED/name
    if not path.is_file(): return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def selected(city,start,end):
    try:
        frame=load_weather()
    except (FileNotFoundError,ValueError,OSError) as exc: raise HTTPException(503,str(exc)) from exc
    try:
        subset=filter_weather(frame,city,start,end)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    if subset.empty: raise HTTPException(404,"No hourly records match the selected city and date range. Choose dates within the cached dataset.")
    return frame,subset


@lru_cache(maxsize=4)
def dataset_hash(path,mtime,size):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pipeline_status():
    manifest=read_json("manifest.json")
    result={key:manifest.get(key) for key in ["engine","generated_at","duration_seconds","steps","artifacts"]}
    result["engine"]=result["engine"] or "pandas + Apache Parquet (PyArrow)"
    result["steps"]=list(result["steps"] or [])
    result["artifacts"]=list(result["artifacts"] or [])
    spark=read_json("spark_evidence.json"); path=PROCESSED/"weather.parquet"
    current_hash=dataset_hash(str(path),path.stat().st_mtime_ns,path.stat().st_size) if path.exists() else None
    verified=bool(spark.get("status")=="verified" and spark.get("parity_passed") is True and spark.get("dataset_sha256")==current_hash and current_hash)
    result["spark_verified"]=verified
    result["steps"].append({"name":"Spark SQL","status":"verified" if verified else "optional","detail":f"{spark.get('engine')}; independent monthly aggregate parity passed." if verified else "Optional local Spark execution; no current verified dataset evidence."})
    for filename,name,description in [("predictions.json","Random Forest","Chronological next-day holdout with persistence baseline"),("mapreduce.json","Local MapReduce","Python partition/map/shuffle/reduce demonstration"),("streaming.json","Historical replay","Algorithm R reservoir sampling on cached records")]:
        ready=(PROCESSED/filename).is_file()
        result["steps"].append({"name":name,"status":"complete" if ready else "pending","detail":description})
        if ready: result["artifacts"].append({"name":filename,"description":description})
    if verified: result["spark_evidence"]=spark
    # Hadoop proof must match both the cleaned dataset and every current raw CSV.
    # A failed, truncated, missing or stale artifact can never advertise execution.
    hadoop={}; hadoop_verified=False
    try:
        evidence=read_json("hadoop_evidence.json")
        comparison=evidence.get("comparison") if isinstance(evidence,dict) else None
        hdfs=evidence.get("hdfs") if isinstance(evidence,dict) else None
        details_valid=(
            isinstance(comparison,dict) and comparison.get("passed") is True
            and isinstance(hdfs,dict)
            and all(isinstance(hdfs.get(key),str) and hdfs[key].startswith("/") and len(hdfs[key])>1 for key in ["input_path","output_path"])
            and all(type(evidence.get(key)) is int and evidence[key]>0 for key in ["clean_rows","monthly_groups"])
        )
        if details_valid and evidence.get("status")=="verified" and evidence.get("parity_passed") is True and current_hash and evidence.get("dataset_sha256")==current_hash:
            checks=evidence.get("raw_checksums")
            if isinstance(checks,list) and checks and all(isinstance(item,dict) and isinstance(item.get("name"),str) and isinstance(item.get("sha256"),str) for item in checks):
                recorded={item["name"]:item["sha256"] for item in checks}
                current={file.name:hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(RAW.glob("*.csv"))}
                hadoop_verified=bool(current and len(recorded)==len(checks) and recorded==current)
                if hadoop_verified: hadoop=evidence
    except (OSError,ValueError,TypeError):
        hadoop_verified=False
    result["hadoop_verified"]=hadoop_verified
    result["steps"].extend([
        {"name":"HDFS","status":"verified" if hadoop_verified else "optional","detail":"Native NameNode/DataNode execution recorded in current Hadoop evidence." if hadoop_verified else "Optional native HDFS; no current verified dataset and raw-source evidence."},
        {"name":"Hadoop MapReduce","status":"verified" if hadoop_verified else "optional","detail":f"{hadoop.get('engine')}; {hadoop.get('execution_mode')}; independent aggregate parity passed." if hadoop_verified else "Optional Hadoop Streaming with LocalJobRunner; no verified execution. A distributed YARN cluster is not claimed."}
    ])
    if hadoop_verified:
        result["hadoop_evidence"]=hadoop
        result["artifacts"].append({"name":"hadoop_evidence.json","description":"Native HDFS and Hadoop Streaming execution, raw checksums and independent aggregate parity"})
    return result


def prediction_for(city,start,end):
    chosen="Hyderabad" if city=="all" else city
    result=dict(read_json("predictions.json").get(chosen,{"available":False,"city":chosen,"points":[],"note":"Model evaluation has not been generated for this city."}))
    if result.get("available"):
        matching=[p for p in result["points"] if start<=p["date"]<=end]
        # Chart is bounded; metrics always describe the full fixed chronological holdout.
        result["points"]=matching[-60:]
        result["note"]+=" Metrics describe the complete fixed holdout; chart displays up to 60 matching test days."
        if city=="all": result["note"]+=" All-city dashboard displays Hyderabad's model; select a city for its evaluation."
        if not matching: result["note"]+=" No holdout days fall within the selected dates."
    return result


@app.get("/api/health")
def health():
    ready=False
    try:
        frame=load_weather()
        manifest=read_json("manifest.json")
        path=PROCESSED/"weather.parquet"; stat=path.stat()
        ready=bool(len(frame)>0 and manifest.get("total_records")==len(frame) and manifest.get("city_count")==frame.city.nunique() and manifest.get("quality",{}).get("clean_rows")==len(frame) and manifest.get("dataset_sha256")==dataset_hash(str(path),stat.st_mtime_ns,stat.st_size))
    except (OSError,ValueError,KeyError,TypeError):
        ready=False
    return {"status":"ok","data_ready":ready}


@app.get("/api/dashboard")
def dashboard(city:str="all", start:str="2021-01-01", end:str="2025-12-31"):
    frame,subset=selected(city,start,end)
    events=daily_extremes(subset); summary=summarize(subset); summary["extreme_count"]=len(events)
    correlations=subset[METRICS].corr()
    manifest=read_json("manifest.json")
    rain_note="Rainfall is summed across selected city-hours; the all-city sum is not rainfall at a single location." if city=="all" else f"Rainfall is the sum of hourly precipitation for {city} in the selected period."
    insights=[rain_note,"Heat means a city-day maximum ≥40 °C; heavy rain means city-day precipitation ≥50 mm. These educational thresholds are not official warnings.",f"{len(subset):,} hourly reanalysis records across {subset.city.nunique()} cities; values represent modeled historical weather.","Daily extremes use the selected hours only; missing hourly records can affect daily completeness."]
    return {"meta":{"title":"Weather Data Analysis","source":"Open-Meteo ERA5 hourly reanalysis","source_url":SOURCE_URL,"license":"CC BY 4.0","data_kind":"reanalysis","timezone":"Asia/Kolkata","start":start,"end":end,"total_records":len(frame),"filtered_records":len(subset),"city_count":int(subset.city.nunique()),"generated_at":manifest.get("generated_at",datetime.now(timezone.utc).isoformat()),"engine":"pandas + Apache Parquet (PyArrow)","cities":[c for c in CITIES if c["name"] in set(frame.city)],"years":sorted(int(y) for y in frame.time.dt.year.unique())},"summary":summary,"trends":monthly_trends(subset),"comparison":city_comparison(subset),"correlation":{"labels":["Temperature","Humidity","Precipitation","Wind"],"matrix":[[number(v) for v in row] for row in correlations.to_numpy()]},"extremes":events[:100],"quality":manifest.get("quality",{"input_rows":len(frame),"clean_rows":len(frame),"duplicates_removed":0,"invalid_rows":0,"missing_values":0}),"insights":insights,"pipeline":pipeline_status(),"prediction":prediction_for(city,start,end)}


@app.get("/api/export")
def export(city:str="all",start:str="2021-01-01",end:str="2025-12-31"):
    _,subset=selected(city,start,end)
    content=subset.to_csv(index=False)
    filename=f"weather-{city.lower()}-{start}-to-{end}.csv"
    return Response(content,media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="{filename}"'})


@app.get("/api/pipeline")
def pipeline():
    result=pipeline_status()
    hadoop_scope="Verified native macOS HDFS NameNode/DataNode and Hadoop Streaming MapReduce LocalJobRunner; single machine, no YARN distributed execution" if result["hadoop_verified"] else "Optional native HDFS and Hadoop Streaming; no current verified execution evidence"
    result["syllabus_mapping"]=[{"topic":"Data ingestion, cleaning and aggregation","implementation":"Open-Meteo CSV cache → pandas → Parquet"},{"topic":"HDFS and Hadoop MapReduce","implementation":hadoop_scope},{"topic":"MapReduce concepts","implementation":"Additional local Python map/shuffle/reduce demonstration"},{"topic":"Spark and Spark SQL","implementation":"Optional actual Apache Spark local job; verify execution evidence"},{"topic":"Stream processing","implementation":"Historical hourly replay and bounded Algorithm R reservoir"},{"topic":"Machine learning","implementation":"scikit-learn Random Forest chronological holdout and persistence baseline"},{"topic":"Hive, Pig, Sqoop, HBase, ZooKeeper, Mahout","implementation":"Documented conceptual mappings/extensions; not installed or executed"}]
    return result


@app.get("/api/stream")
def stream(city:str="Hyderabad"):
    frame,subset=selected(city,"2021-01-01","2025-12-31")
    return replay(subset,limit=10000,size=30)

@app.get("/api/hadoop/explorer")
def hadoop_explorer(city:str="Hyderabad", month:str="2025-01"):
    from backend.hadoop_explorer import build_explorer
    try:
        return build_explorer(city,month,pipeline_status())
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except OSError as exc:
        raise HTTPException(503,"Cached Hadoop explorer source unavailable: "+str(exc)) from exc

# Mount last: /api and /docs remain API routes. Relative paths are repository-rooted.
if (ROOT/"frontend"/"out"/"index.html").is_file():
    app.mount("/",StaticFiles(directory=ROOT/"frontend"/"out",html=True),name="frontend")
