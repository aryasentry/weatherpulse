"""Pure numerical functions shared by the pipeline and read-only API."""
from functools import lru_cache
from datetime import date
import math
import re
import pandas as pd
import numpy as np
from backend.config import CITIES, METRICS, PROCESSED


def number(value):
    return round(float(value), 6) if pd.notna(value) and math.isfinite(float(value)) else None


def clean_data(raw):
    frame = raw.copy()
    frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
    for col in METRICS + ["latitude", "longitude"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    missing_values = int(frame[METRICS].isna().sum().sum())
    valid = frame["city"].isin([c["name"] for c in CITIES]) & frame["time"].notna()
    bounds = {"temperature": (-90, 60), "humidity": (0, 100), "precipitation": (0, 500), "wind_speed": (0, 400), "latitude": (-90,90), "longitude": (-180,180)}
    for col, (low, high) in bounds.items():
        valid &= frame[col].between(low, high)
    invalid_rows = int((~valid).sum())
    frame = frame.loc[valid].copy()
    before_dedup = len(frame)
    frame = frame.drop_duplicates(["city", "time"], keep="first").sort_values(["city", "time"]).reset_index(drop=True)
    return frame, {"input_rows": len(raw), "clean_rows": len(frame), "duplicates_removed": before_dedup-len(frame), "invalid_rows": invalid_rows, "missing_values": missing_values}


@lru_cache(maxsize=2)
def _read_weather(path, mtime, size):
    frame = pd.read_parquet(path)
    expected = {"city", "time", "latitude", "longitude", *METRICS}
    if not expected.issubset(frame.columns) or frame.empty:
        raise ValueError("Cached Parquet is empty or lacks the weather schema. Rebuild the pipeline.")
    if not pd.api.types.is_datetime64_any_dtype(frame.time):
        raise ValueError("Cached Parquet time column must contain datetime values.")
    return frame


def load_weather():
    path = PROCESSED / "weather.parquet"
    if not path.is_file():
        raise FileNotFoundError("Cleaned data missing. Run python -m backend.ingest then python -m backend.pipeline.")
    stat = path.stat()
    return _read_weather(str(path), stat.st_mtime_ns, stat.st_size)


load_weather.cache_clear = _read_weather.cache_clear


def filter_weather(frame, city="all", start="2021-01-01", end="2025-12-31"):
    if city != "all" and city not in [c["name"] for c in CITIES]:
        raise ValueError("Unknown city. Choose all or a listed city.")
    try:
        if not all(isinstance(value,str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}",value) for value in [start,end]):
            raise ValueError("Invalid date format")
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (ValueError, TypeError):
        raise ValueError("Dates must be valid YYYY-MM-DD calendar dates.") from None
    if first > last:
        raise ValueError("Start date must be on or before end date.")
    # Compare calendar dates: end is inclusive, even on the last hour.
    dates = frame.time.dt.date
    selected = frame[(dates >= first) & (dates <= last)]
    if city != "all":
        selected = selected[selected.city == city]
    return selected


def summarize(frame):
    return {"avg_temperature": number(frame.temperature.mean()), "total_precipitation": number(frame.precipitation.sum(min_count=1)), "avg_humidity": number(frame.humidity.mean()), "avg_wind_speed": number(frame.wind_speed.mean()), "max_temperature": number(frame.temperature.max()), "min_temperature": number(frame.temperature.min()), "temperature_std": number(frame.temperature.std(ddof=1)), "temperature_variance": number(frame.temperature.var(ddof=1)), "temperature_median": number(frame.temperature.median())}


def monthly_trends(frame):
    grouped = frame.assign(date=frame.time.dt.strftime("%Y-%m")).groupby("date", sort=True).agg(temperature=("temperature","mean"), precipitation=("precipitation","sum"), humidity=("humidity","mean"), wind_speed=("wind_speed","mean"))
    return [{"date": key, **{c:number(row[c]) for c in METRICS}} for key,row in grouped.iterrows()]


def city_comparison(frame):
    grouped = frame.groupby("city").agg(temperature=("temperature","mean"),precipitation=("precipitation","sum"),humidity=("humidity","mean"),wind_speed=("wind_speed","mean"),records=("city","size"))
    return [{"city":key, **{c:number(row[c]) for c in METRICS},"records":int(row.records)} for key,row in grouped.iterrows()]


def daily_extremes(frame):
    daily = frame.assign(date=frame.time.dt.strftime("%Y-%m-%d")).groupby(["city","date"]).agg(temperature=("temperature","max"),precipitation=("precipitation","sum"))
    events=[]
    for (city, day), row in daily.iterrows():
        for metric,kind,threshold,unit in [("temperature","Heat",40,"°C"),("precipitation","Heavy rain",50,"mm")]:
            if row[metric] >= threshold:
                events.append({"city":city,"date":day,"type":kind,"value":number(row[metric]),"threshold":threshold,"unit":unit})
    return sorted(events,key=lambda x:(-x["value"]/x["threshold"],x["city"],x["date"]))
