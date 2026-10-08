"""Bounded-memory reservoir sampling of chronological historical replay."""
import json
import random
from backend.analytics import load_weather, number
from backend.config import PROCESSED


def reservoir_sample(iterable, size=30, seed=42):
    if size<1: raise ValueError("Reservoir size must be positive")
    rng=random.Random(seed); sample=[]; seen=0
    for seen,item in enumerate(iterable,1):
        if seen<=size: sample.append(item)
        else:
            index=rng.randrange(seen)
            if index<size: sample[index]=item
    return {"seen":seen,"sample":sample,"capacity":size,"seed":seed}


def replay(frame, limit=10000, size=30):
    ordered=frame.sort_values(["time","city"]).iloc[:limit] if limit else frame.sort_values(["time","city"])
    records=({"city":r.city,"time":r.time.isoformat(),"temperature":number(r.temperature),"humidity":number(r.humidity),"precipitation":number(r.precipitation),"wind_speed":number(r.wind_speed)} for r in ordered.itertuples(index=False))
    result=reservoir_sample(records,size=size)
    result.update({"mode":"historical replay","algorithm":"Algorithm R reservoir sampling","available_records":len(frame),"processed_records":result["seen"],"bounded":bool(limit),"limit":limit,"start":ordered.time.min().isoformat() if not ordered.empty else None,"end":ordered.time.max().isoformat() if not ordered.empty else None,"note":"Replays cached historical hourly records in time order; not a live sensor feed. Reservoir retains at most the stated capacity and every processed record has equal inclusion probability."})
    return result


def main():
    result=replay(load_weather(),limit=0,size=50); (PROCESSED/"streaming.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps({k:v for k,v in result.items() if k!="sample"}))

if __name__=="__main__": main()
