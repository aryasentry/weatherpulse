"""CSV ingestion -> validation -> deduplication -> compressed Parquet."""
import hashlib
import json
import time
from datetime import datetime, timezone
import pandas as pd
from backend.analytics import clean_data, load_weather
from backend.config import RAW, PROCESSED, SOURCE_URL


def run_pipeline():
    started=time.perf_counter(); files=sorted(RAW.glob("*.csv"))
    if not files: raise FileNotFoundError("No raw city CSVs. Run python -m backend.ingest first.")
    raw=pd.concat([pd.read_csv(path) for path in files],ignore_index=True)
    clean,quality=clean_data(raw)
    if clean.empty: raise ValueError("No valid records remain after cleaning; dataset was not replaced.")
    PROCESSED.mkdir(parents=True,exist_ok=True)
    output=PROCESSED/"weather.parquet"; tmp=PROCESSED/"weather.parquet.tmp"
    clean.to_parquet(tmp,index=False,compression="zstd"); tmp.replace(output)
    # Model, demos and execution proofs refer to this exact dataset; stale results are removed.
    for name in ["spark_evidence.json","hadoop_evidence.json","predictions.json","mapreduce.json","streaming.json"]:
        (PROCESSED/name).unlink(missing_ok=True)
    load_weather.cache_clear()
    manifest={"title":"Weather Data Analysis","source":"Open-Meteo ERA5 hourly reanalysis","source_url":SOURCE_URL,"license":"CC BY 4.0","data_kind":"reanalysis","timezone":"Asia/Kolkata","generated_at":datetime.now(timezone.utc).isoformat(),"engine":"pandas + Apache Parquet (PyArrow)","duration_seconds":round(time.perf_counter()-started,3),"start":clean.time.min().strftime("%Y-%m-%d"),"end":clean.time.max().strftime("%Y-%m-%d"),"total_records":len(clean),"city_count":int(clean.city.nunique()),"target_records":438240,"quality":quality,"dataset_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"raw_files":[{"name":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],"steps":[{"name":"Ingest","status":"complete","detail":f"{len(files)} cached real Open-Meteo city CSVs; per-city request provenance retained."},{"name":"Validate","status":"complete","detail":f"{quality['invalid_rows']} invalid rows rejected; {quality['missing_values']} missing metric cells counted."},{"name":"Deduplicate","status":"complete","detail":f"{quality['duplicates_removed']} city/time duplicates removed."},{"name":"Store","status":"complete","detail":f"{len(clean):,} cleaned hourly rows written to compressed Parquet."}],"artifacts":[{"name":"weather.parquet","description":"Validated hourly reanalysis data, compressed with Zstandard"},{"name":"manifest.json","description":"Counts, quality checks, source attribution and dataset checksums"}]}
    (PROCESSED/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest),flush=True)
    return manifest

if __name__=="__main__": run_pipeline()
