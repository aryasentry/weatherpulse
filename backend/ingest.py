"""Fetch actual Open-Meteo ERA5 hourly reanalysis; no synthetic fallback."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
from backend.config import CITIES, RAW, SOURCE_URL


def fetch_city(city, start, end, force=False):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / (city["name"].lower()+".csv")
    metadata_path=path.with_suffix(".provenance.json")
    if path.is_file() and metadata_path.is_file() and not force:
        meta=json.loads(metadata_path.read_text())
        if meta.get("start")==start and meta.get("end")==end and meta.get("sha256")==hashlib.sha256(path.read_bytes()).hexdigest():
            return {"city":city["name"],"rows":meta["rows"],"cached":True}
    params={"latitude":city["latitude"],"longitude":city["longitude"],"start_date":start,"end_date":end,"hourly":"temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m","timezone":"Asia/Kolkata","models":"era5","temperature_unit":"celsius","wind_speed_unit":"kmh","precipitation_unit":"mm"}
    for attempt in range(4):
        try:
            response=requests.get("https://archive-api.open-meteo.com/v1/archive",params=params,timeout=180)
            response.raise_for_status()
            body=response.json()
            hourly=body["hourly"]
            frame=pd.DataFrame({"city":city["name"],"time":hourly["time"],"temperature":hourly["temperature_2m"],"humidity":hourly["relative_humidity_2m"],"precipitation":hourly["precipitation"],"wind_speed":hourly["wind_speed_10m"],"latitude":city["latitude"],"longitude":city["longitude"]})
            if frame.empty:
                raise ValueError("Archive response contained no hourly records")
            tmp=path.with_suffix(".csv.tmp")
            frame.to_csv(tmp,index=False)
            tmp.replace(path)
            meta={"city":city, "start":start,"end":end,"rows":len(frame),"retrieved_at":datetime.now(timezone.utc).isoformat(),"request_url":response.url,"source_url":SOURCE_URL,"license":"CC BY 4.0","attribution":"Weather data by Open-Meteo; ERA5 reanalysis by Copernicus Climate Change Service (C3S) / ECMWF","model":"era5","timezone":"Asia/Kolkata","hourly_units":body.get("hourly_units"),"grid_latitude":body.get("latitude"),"grid_longitude":body.get("longitude"),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
            metadata_path.write_text(json.dumps(meta,indent=2),encoding="utf-8")
            return {"city":city["name"],"rows":len(frame),"cached":False}
        except (requests.RequestException,KeyError,ValueError) as exc:
            if attempt==3: raise RuntimeError(f"{city['name']}: archive ingestion failed: {exc}") from exc
            time.sleep(2**attempt)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start",default="2021-01-01")
    parser.add_argument("--end",default="2025-12-31")
    parser.add_argument("--force",action="store_true")
    args=parser.parse_args()
    failures=[]; successes=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(fetch_city,c,args.start,args.end,args.force):c for c in CITIES}
        for future in as_completed(futures):
            try:
                result=future.result(); successes.append(result); print(json.dumps(result),flush=True)
            except Exception as exc:
                failures.append(str(exc)); print(str(exc),flush=True)
    report={"start":args.start,"end":args.end,"target_rows":len(pd.date_range(args.start,args.end,freq="D"))*24*len(CITIES),"actual_rows":sum(x["rows"] for x in successes),"cities":successes,"failures":failures}
    (RAW/"ingestion_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report),flush=True)
    if failures: raise SystemExit(1)

if __name__=="__main__": main()
