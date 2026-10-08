"""Shuffle groups city/month; dedup timestamps and reduce sums/counts."""
import itertools
import json
import sys


def reduce_records(lines):
    pairs=(line.rstrip('\n').split('\t',1) for line in lines)
    for key,group in itertools.groupby(pairs,key=lambda pair:pair[0]):
        timestamps={}
        for _,value in group:
            row=json.loads(value); previous=timestamps.get(row['time'])
            if previous is None or (row['source'],row['offset'])<(previous['source'],previous['offset']): timestamps[row['time']]=row
        sums=[0.,0.,0.,0.]; count=len(timestamps)
        for row in timestamps.values():
            for index,value in enumerate(row['values']): sums[index]+=value
        city,month=key.split('|',1)
        yield {'city':city,'month':month,'records':count,'temperature':sums[0]/count,'humidity':sums[1]/count,'precipitation':sums[2],'wind_speed':sums[3]/count}


def main():
    clean_rows=0
    for row in reduce_records(sys.stdin):
        print(f"{row['city']}|{row['month']}\t"+json.dumps(row,separators=(',',':'))); clean_rows+=row['records']
    print(f'reporter:counter:Weather,CleanRows,{clean_rows}',file=sys.stderr)

if __name__=='__main__': main()
