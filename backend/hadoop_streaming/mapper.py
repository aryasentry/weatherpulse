"""Input: TextInputFormat offset + raw CSV; output: city/month + validated row."""
import csv
import json
import math
import os
import sys
from datetime import datetime
CITIES={'Hyderabad','Delhi','Mumbai','Bengaluru','Chennai','Kolkata','Pune','Ahmedabad','Jaipur','Lucknow'}
BOUNDS=[(-90,60),(0,100),(0,500),(0,400),(-90,90),(-180,180)]


def map_records(lines,source=''):
    for index,line in enumerate(lines):
        offset,indexed_line=(line.split('\t',1) if '\t' in line else (str(index),line))
        row=next(csv.reader([indexed_line]))
        if not row or row[0]=='city': continue
        try:
            if len(row)!=8 or row[0] not in CITIES: continue
            timestamp=datetime.fromisoformat(row[1])
            if timestamp.tzinfo is not None: continue
            values=[float(x) for x in row[2:]]
            if not all(math.isfinite(value) and low<=value<=high for value,(low,high) in zip(values,BOUNDS)): continue
            key=f'{row[0]}|{timestamp:%Y-%m}'
            yield key+'\t'+json.dumps({'time':timestamp.isoformat(),'values':values[:4],'source':source,'offset':int(offset)},separators=(',',':'))
        except (ValueError,IndexError): continue


def main():
    source=os.environ.get('mapreduce_map_input_file',os.environ.get('map_input_file',''))
    input_rows=0
    def rows():
        nonlocal input_rows
        for line in sys.stdin:
            raw=line.split('\t',1)[-1]
            if raw.startswith('city,'): continue
            input_rows+=1
            yield line
    valid=0
    for line in map_records(rows(),source): print(line); valid+=1
    print(f'reporter:counter:Weather,InputRows,{input_rows}',file=sys.stderr)
    print(f'reporter:counter:Weather,InvalidRows,{input_rows-valid}',file=sys.stderr)

if __name__=='__main__': main()
