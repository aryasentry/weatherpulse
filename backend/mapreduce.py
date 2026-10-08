"""Educational local map/shuffle/reduce; no Hadoop runtime is claimed."""
import json
from collections import defaultdict
import numpy as np
from backend.analytics import load_weather, number
from backend.config import METRICS, PROCESSED


def map_reduce(frame, partitions=4):
    if partitions<1: raise ValueError("Partitions must be positive")
    mapped=[]
    for part in np.array_split(np.arange(len(frame)),partitions):
        partition=frame.iloc[part]
        for city,group in partition.groupby("city"):
            mapped.append((city,len(group),*[float(group[col].sum()) for col in METRICS]))
    shuffled=defaultdict(list)
    for item in mapped: shuffled[item[0]].append(item[1:])
    reduced=[]
    for city,items in sorted(shuffled.items()):
        sums=np.asarray(items).sum(axis=0); count=int(sums[0])
        reduced.append({"city":city,"records":count,"temperature":number(sums[1]/count),"humidity":number(sums[2]/count),"precipitation":number(sums[3]),"wind_speed":number(sums[4]/count)})
    return {"engine":"Python local map/shuffle/reduce demonstration","partitions":partitions,"mapped_pairs":len(mapped),"shuffle_keys":len(shuffled),"rows":len(frame),"cities":reduced,"note":"Runs on one computer; demonstrates partitioned associative aggregation. It is not Hadoop MapReduce or a distributed cluster."}


def main():
    result=map_reduce(load_weather()); (PROCESSED/"mapreduce.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result))

if __name__=="__main__": main()
