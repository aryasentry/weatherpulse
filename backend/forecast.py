"""Chronological, one-day-ahead temperature evaluation against persistence."""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from backend.analytics import load_weather, number
from backend.config import PROCESSED
FEATURES=["lag_1","lag_2","lag_7","rolling_7","season_sin","season_cos"]


def make_features(daily):
    daily=daily.sort_values("date").set_index("date").asfreq("D").reset_index()
    for lag in [1,2,7]: daily[f"lag_{lag}"]=daily.temperature.shift(lag)
    daily["rolling_7"]=daily.temperature.shift(1).rolling(7).mean()
    radians=2*np.pi*daily.date.dt.dayofyear/365.25
    daily["season_sin"],daily["season_cos"]=np.sin(radians),np.cos(radians)
    return daily.dropna(subset=["temperature"]+FEATURES).reset_index(drop=True)


def chronological_split(features):
    cutoff=pd.Timestamp("2025-01-01")
    train=features[features.date < cutoff]; test=features[features.date >= cutoff]
    if train.empty or test.empty:
        split=int(len(features)*0.8)
        train,test=features.iloc[:split],features.iloc[split:]
    return train,test


def evaluate_city(frame, city):
    hourly=frame[frame.city==city]
    daily=hourly.groupby(hourly.time.dt.normalize()).agg(temperature=("temperature","mean"),hours=("temperature","count")).reset_index().rename(columns={"time":"date"})
    # An incomplete day never supplies a target or lag. Reindex in make_features preserves gaps.
    daily.loc[daily.hours!=24,"temperature"]=np.nan
    features=make_features(daily)
    train,test=chronological_split(features)
    if len(train)<30 or len(test)<2:
        return {"available":False,"city":city,"note":"Insufficient complete daily records for a chronological evaluation.","points":[]}
    model=RandomForestRegressor(n_estimators=100,max_depth=12,min_samples_leaf=3,random_state=42,n_jobs=2)
    model.fit(train[FEATURES],train.temperature)
    predicted=model.predict(test[FEATURES]); actual=test.temperature.to_numpy(); baseline=test.lag_1.to_numpy()
    return {"available":True,"city":city,"model":"Random Forest · next-day daily mean temperature","mae":number(mean_absolute_error(actual,predicted)),"baseline_mae":number(mean_absolute_error(actual,baseline)),"rmse":number(np.sqrt(mean_squared_error(actual,predicted))),"train_end":train.date.max().strftime("%Y-%m-%d"),"test_start":test.date.min().strftime("%Y-%m-%d"),"test_end":test.date.max().strftime("%Y-%m-%d"),"train_samples":len(train),"test_samples":len(test),"features":FEATURES,"points":[{"date":day.strftime("%Y-%m-%d"),"actual":number(a),"predicted":number(p),"baseline":number(b)} for day,a,p,b in zip(test.date,actual,predicted,baseline)],"note":"Chronological holdout; model fits once before the test period. One-day-ahead evaluation uses observed previous-day temperatures, including prior test days. Persistence predicts yesterday's mean. Reanalysis demonstration, not a live forecast or a multi-day recursive forecast."}


def main():
    frame=load_weather(); results={}
    for city in sorted(frame.city.unique()):
        results[city]=evaluate_city(frame,city)
        print(json.dumps({k:v for k,v in results[city].items() if k not in ["points","features"]}),flush=True)
    PROCESSED.mkdir(exist_ok=True,parents=True)
    (PROCESSED/"predictions.json").write_text(json.dumps(results,indent=2,allow_nan=False),encoding="utf-8")

if __name__=="__main__": main()
