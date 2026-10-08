"""Read-only, bounded Hadoop telemetry plus source-faithful teaching traces.

Live JMX/WebHDFS responses, saved completed-job evidence, and a three-record
instructional sample have separate provenance. This module starts no daemon,
runs no job, sends no write request, and accepts no caller-supplied host/path.
"""
import csv
import json
import math
import re
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import PurePosixPath
from urllib.parse import quote
import requests
import pandas as pd
from urllib3.exceptions import HTTPError as TransportError
from backend.analytics import load_weather
from backend.config import RAW, PROCESSED, CITIES
from backend.hadoop_streaming.mapper import map_records
from backend.hadoop_streaming.reducer import reduce_records
BASE='http://127.0.0.1:19870'
MAX_RESPONSE=256*1024
MAX_LOCAL=2*1024*1024
WEB_DOC='https://hadoop.apache.org/docs/r3.5.0/hadoop-project-dist/hadoop-hdfs/WebHDFS.html'
METRICS_DOC='https://hadoop.apache.org/docs/r3.5.0/hadoop-project-dist/hadoop-common/Metrics.html'
STREAM_DOC='https://hadoop.apache.org/docs/r3.5.0/hadoop-streaming/HadoopStreaming.html'
BEANS={'NameNodeInfo','NameNodeStatus'}
COUNTERS={'map_input_records':'Map input records','map_output_records':'Map output records','reduce_input_groups':'Reduce input groups','reduce_output_records':'Reduce output records','shuffled_maps':'Shuffled Maps','reduce_input_records':'Reduce input records','map_output_bytes':'Map output bytes','reduce_shuffle_bytes':'Reduce shuffle bytes','hdfs_bytes_read':'HDFS: Number of bytes read','hdfs_bytes_written':'HDFS: Number of bytes written'}


def safe_path(path):
    return isinstance(path,str) and re.fullmatch(r'/weather-data-analysis/(?:raw|results)/[A-Za-z0-9_-]+(?:/[a-z]+\.csv)?',path) is not None


def fetch_json(resource, *, bean=None, path=None, op=None, length=None):
    """Fixed loopback, GET-only allowlist; redirects and environment proxies disabled."""
    if resource=='jmx' and bean in BEANS and path is None and op is None:
        url=BASE+'/jmx'; params={'qry':'Hadoop:service=NameNode,name='+bean}
    elif resource=='webhdfs' and safe_path(path) and op in {'LISTSTATUS','GETFILEBLOCKLOCATIONS'} and bean is None:
        url=BASE+'/webhdfs/v1'+quote(path,safe='/'); params={'op':op}
        if op=='GETFILEBLOCKLOCATIONS':
            if type(length) is not int or not 0<=length<=1024*1024*1024: raise ValueError('Invalid bounded block-location length')
            params.update({'offset':0,'length':length})
    else: raise ValueError('Only fixed localhost read-only Hadoop telemetry resources are allowed')
    with requests.Session() as session:
        session.trust_env=False
        with session.get(url,params=params,timeout=(.3,.3),allow_redirects=False,stream=True,headers={'Accept-Encoding':'identity'}) as response:
            if 300<=response.status_code<400: raise ValueError('Telemetry redirects are refused')
            response.raise_for_status()
            declared=response.headers.get('Content-Length')
            if declared and int(declared)>MAX_RESPONSE: raise ValueError('Telemetry response exceeds the size limit')
            chunks=[]; size=0; deadline=time.monotonic()+1
            while True:
                if time.monotonic()>deadline: raise ValueError('Telemetry response exceeded the time limit')
                try: chunk=response.raw.read1(8192)
                except TransportError as exc: raise requests.ConnectionError(str(exc)) from exc
                if not chunk: break
                size+=len(chunk)
                if size>MAX_RESPONSE: raise ValueError('Telemetry response exceeds the size limit')
                chunks.append(chunk)
            body=json.loads(b''.join(chunks))
            if not isinstance(body,dict): raise ValueError('Telemetry must be a JSON object')
            return body


def finite(value,nonnegative=True):
    if isinstance(value,bool): return None
    try:
        result=float(value)
        return result if math.isfinite(result) and (not nonnegative or result>=0) else None
    except (ValueError,TypeError): return None


def safe_json_file(name,default):
    path=PROCESSED/name
    try:
        if not path.is_file() or path.stat().st_size>MAX_LOCAL: return default
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError): return default


def parse_job_counters(log):
    # Select only the final job-wide section, never an individual task's counters.
    final=log.rsplit(' Counters:',1)[-1] if ' Counters:' in log else log
    result={}
    for key,label in COUNTERS.items():
        values=re.findall(re.escape(label)+r'\s*=\s*(\d+)',final)
        result[key]=int(values[-1]) if values else None
    return result


@lru_cache(maxsize=12)
def raw_samples(path,mtime,size):
    """Cache only the first three real rows per month, preserving CSV byte offsets."""
    samples={}; file_path=RAW/path
    if size>16*1024*1024: raise ValueError('City CSV exceeds the teaching-trace size limit')
    with file_path.open('rb') as stream:
        offset=0
        for raw in stream:
            position=offset; offset+=len(raw)
            if len(raw)>8192: continue
            line=raw.decode('utf-8').rstrip('\r\n')
            row=next(csv.reader([line]))
            if len(row)!=8 or row[0]=='city': continue
            try:
                timestamp=datetime.fromisoformat(row[1]); month=timestamp.strftime('%Y-%m')
                bucket=samples.setdefault(month,[])
                if len(bucket)<3 and list(map_records([f'{position}\t{line}\n'],source=path)):
                    bucket.append({'line':line,'offset':position,'city':row[0],'time':row[1],**dict(zip(['temperature','humidity','precipitation','wind_speed'],[float(x) for x in row[2:6]]))})
            except (ValueError,IndexError): continue
    return {key:rows for key,rows in samples.items() if rows}


def selection(city,month):
    if city not in [c['name'] for c in CITIES]: raise ValueError('Choose one of the ten available cities; all is not a city in this explorer.')
    if not isinstance(month,str) or not re.fullmatch(r'[0-9]{4}-(?:0[1-9]|1[0-2])',month): raise ValueError('Month must use YYYY-MM with a valid month number.')
    frame=load_weather()
    months=sorted(frame.loc[frame.city==city,'time'].dt.strftime('%Y-%m').unique().tolist())
    if month not in months: raise ValueError('Selected city/month is outside the available real cleaned data.')
    path=RAW/(city.lower()+'.csv'); rows=[]; error=None
    try:
        stat=path.stat(); samples=raw_samples(str(path),stat.st_mtime_ns,stat.st_size); rows=samples.get(month,[])
        if not rows: error='No usable raw CSV records are available for this month; teaching trace unavailable.'
    except (OSError,ValueError,csv.Error) as exc: error='Raw CSV teaching trace unavailable: '+str(exc)[:160]
    return {'city':city,'month':month,'cities':[c['name'] for c in CITIES if c['name'] in set(frame.city)],'months':months},rows,error


def bean_fields(body):
    beans=body.get('beans') if isinstance(body,dict) else None
    if not isinstance(beans,list): return {}
    result={}
    for bean in beans:
        if isinstance(bean,dict): result.update(bean)
    return result


def decode_nodes(value,field,warnings):
    try:
        nodes=json.loads(value) if isinstance(value,str) else value
        if not isinstance(nodes,dict): raise ValueError('not an object')
        return nodes
    except (TypeError,ValueError): warnings.append(f'{field} telemetry is missing or malformed; no node count was invented.'); return None


def live_status(evidence,city):
    result={'available':False,'observed_at':datetime.now(timezone.utc).isoformat(),'source':'Live fixed-localhost NameNode JMX + read-only WebHDFS','error':None,'warnings':[],'namenode':{key:None for key in ['state','safe_mode','version','used_bytes','total_blocks','live_datanodes','dead_datanodes']},'datanodes':[],'files':[],'selected_file':None}
    try:
        info=bean_fields(fetch_json('jmx',bean='NameNodeInfo'))
        if not info: raise ValueError('NameNode JMX contained no usable telemetry fields')
        result['available']=True
        try: status=bean_fields(fetch_json('jmx',bean='NameNodeStatus'))
        except (requests.RequestException,ValueError,OSError) as exc: status={}; result['warnings'].append('NameNode state unavailable: '+str(exc)[:160])
        live=decode_nodes(info.get('LiveNodes'),'LiveNodes',result['warnings']); dead=decode_nodes(info.get('DeadNodes'),'DeadNodes',result['warnings'])
        safe=info.get('Safemode')
        result['namenode']={'state':status.get('State') if isinstance(status.get('State'),str) else None,'safe_mode':bool(safe) if isinstance(safe,str) else None,'version':info.get('SoftwareVersion') if isinstance(info.get('SoftwareVersion'),str) else (info.get('Version') if isinstance(info.get('Version'),str) else None),'used_bytes':finite(info.get('Used')),'total_blocks':finite(info.get('TotalBlocks')),'live_datanodes':len(live) if live is not None else None,'dead_datanodes':len(dead) if dead is not None else None}
        if live is not None:
            for name,node in list(live.items())[:20]:
                if not isinstance(node,dict): result['warnings'].append('A DataNode telemetry entry was malformed.'); continue
                result['datanodes'].append({'name':name,'hostname':name.rsplit(':',1)[0],'used_bytes':finite(node.get('usedSpace',node.get('used'))),'capacity_bytes':finite(node.get('capacity')),'remaining_bytes':finite(node.get('remaining')),'last_contact_seconds':finite(node.get('lastContact'))})
        if evidence:
            input_path=evidence.get('hdfs',{}).get('input_path')
            if not safe_path(input_path): result['warnings'].append('Verified evidence has no allowed project HDFS input path.'); return result
            try:
                body=fetch_json('webhdfs',path=input_path,op='LISTSTATUS')
                entries=body.get('FileStatuses',{}).get('FileStatus')
                if not isinstance(entries,list): raise ValueError('WebHDFS file listing is missing')
                known={c['name'].lower()+'.csv' for c in CITIES}
                for item in entries[:30]:
                    if not isinstance(item,dict) or item.get('type')!='FILE' or item.get('pathSuffix') not in known: continue
                    result['files'].append({'name':item['pathSuffix'],'path':input_path+'/'+item['pathSuffix'],'length_bytes':finite(item.get('length')),'block_size_bytes':finite(item.get('blockSize')),'replication':finite(item.get('replication'))})
                selected=next((file for file in result['files'] if file['name']==city.lower()+'.csv'),None)
                if selected:
                    result['selected_file']={**selected,'blocks':[]}
                    try:
                        length=selected['length_bytes']
                        if length is None: raise ValueError('File length missing; block placement unavailable')
                        locations=fetch_json('webhdfs',path=selected['path'],op='GETFILEBLOCKLOCATIONS',length=int(length)).get('BlockLocations',{}).get('BlockLocation')
                        if not isinstance(locations,list): raise ValueError('WebHDFS block-location response is missing')
                        for block in locations[:100]:
                            if not isinstance(block,dict): continue
                            result['selected_file']['blocks'].append({'offset':finite(block.get('offset')),'length':finite(block.get('length')),'hosts':[x for x in block.get('hosts',[]) if isinstance(x,str)] if isinstance(block.get('hosts'),list) else [],'names':[x for x in block.get('names',[]) if isinstance(x,str)] if isinstance(block.get('names'),list) else [],'corrupt':block.get('corrupt') if isinstance(block.get('corrupt'),bool) else None})
                    except (requests.RequestException,ValueError,OSError) as exc: result['warnings'].append('Actual block placement unavailable: '+str(exc)[:160])
            except (requests.RequestException,ValueError,OSError,AttributeError) as exc: result['warnings'].append('Live HDFS file metadata unavailable: '+str(exc)[:160])
    except requests.RequestException:
        result['error']='The local Hadoop service could not be reached. Start the native HDFS runtime, then refresh this observation.'
    except (ValueError,OSError,AttributeError):
        result['error']='The local Hadoop service returned incomplete or unreadable telemetry. Check its status, then refresh this observation.'
    return result


def job_status(evidence,verified):
    saved=evidence or safe_json_file('hadoop_evidence.json',{})
    if not isinstance(saved,dict): saved={}
    counters={key:None for key in COUNTERS}; error=None
    if verified:
        try:
            path=PROCESSED/'hadoop-job.log'
            if path.stat().st_size>MAX_LOCAL: raise ValueError('Saved log exceeds the reading limit')
            counters=parse_job_counters(path.read_text())
        except (OSError,ValueError) as exc: error='Saved job counters unavailable: '+str(exc)
    elif saved: error='Saved evidence is not verified for the current dataset and raw-source checksums.'
    else: error='No saved Hadoop job evidence is available.'
    hdfs=saved.get('hdfs') if verified and isinstance(saved.get('hdfs'),dict) else {}
    return {'available':bool(saved),'verified':verified,'source':'Saved completed Hadoop job evidence; not a current job','error':error,'id':saved.get('job',{}).get('id') if isinstance(saved.get('job'),dict) else None,'generated_at':saved.get('generated_at'),'execution_mode':saved.get('execution_mode'),'input_rows':finite(saved.get('input_rows')) if verified else None,'clean_rows':finite(saved.get('clean_rows')) if verified else None,'monthly_groups':finite(saved.get('monthly_groups')) if verified else None,'parity_passed':bool(verified and saved.get('parity_passed') is True),'counters':counters,'hdfs_input_path':hdfs.get('input_path') if safe_path(hdfs.get('input_path')) else None,'hdfs_output_path':hdfs.get('output_path') if safe_path(hdfs.get('output_path')) else None}


def build_trace(city,month,rows,evidence,verified,raw_error=None):
    source=evidence.get('hdfs',{}).get('input_path')+'/'+city.lower()+'.csv' if evidence and safe_path(evidence.get('hdfs',{}).get('input_path')) else city.lower()+'.csv'
    lines=list(map_records([f"{row['offset']}\t{row['line']}\n" for row in rows],source=source))
    mapped=[{'key':line.split('\t',1)[0],'value':json.loads(line.split('\t',1)[1]),'emitted_line':line} for line in lines]
    reduced=list(reduce_records(sorted(lines)))
    full=None; error=raw_error
    if verified and raw_error is None:
        aggregates=safe_json_file('hadoop-monthly.json',[])
        if isinstance(aggregates,list):
            matches=[row for row in aggregates if isinstance(row,dict) and row.get('city')==city and row.get('month')==month]
            if len(matches)==1 and all(finite(matches[0].get(key),nonnegative=key!='temperature') is not None for key in ['records','temperature','humidity','precipitation','wind_speed']):
                first=pd.Timestamp(month+'-01'); last=first+pd.offsets.MonthBegin(1)
                frame=load_weather(); selected=frame[(frame.city==city)&(frame.time>=first)&(frame.time<last)]
                expected={'records':len(selected),'temperature':selected.temperature.mean(),'humidity':selected.humidity.mean(),'precipitation':selected.precipitation.sum(),'wind_speed':selected.wind_speed.mean()}
                if len(selected)>0 and all(abs(float(matches[0][key])-float(value))<=(0 if key=='records' else 1e-6) for key,value in expected.items()): full=matches[0]
                else: error='Saved full-month output differs from an independent recomputation of the current cleaned city/month; result hidden.'
            else: error='Saved full-month Hadoop output is missing, duplicated, or malformed.'
        else: error='Saved full-month Hadoop output is malformed.'
    return {'available':bool(mapped),'mode':'instructional sample','source':'Three real cached CSV records replayed through the production Hadoop Streaming mapper and reducer','error':error,'raw_records':rows,'mapped':mapped,'shuffle':{'key':city+'|'+month,'values':[item['value'] for item in mapped],'sample_count':len(mapped)},'sample_aggregate':reduced[0] if reduced else None,'full_month_aggregate':full,'full_month_verified':full is not None,'note':'This is a three-record instructional sample, not a running Hadoop job. The sample reducer total covers only these records. The separate full-month result comes from saved verified Hadoop output. NameNode metadata tells the client where blocks are; data bytes are transferred directly between client and DataNode. One replica on one DataNode demonstrates no failover redundancy.'}


def build_explorer(city,month,pipeline):
    selected,rows,raw_error=selection(city,month)
    verified=pipeline.get('hadoop_verified') is True and isinstance(pipeline.get('hadoop_evidence'),dict)
    evidence=pipeline.get('hadoop_evidence') if verified else None
    return {'selection':selected,'live':live_status(evidence,city),'job':job_status(evidence,verified),'trace':build_trace(city,month,rows,evidence,verified,raw_error),'definitions':[
        {'term':'Live telemetry','description':'Fetched now from NameNode JMX and GET-only WebHDFS. An unavailable server does not invalidate a previously completed job.','source_url':METRICS_DOC},
        {'term':'Configured block size versus actual length','description':'Configured block size is maximum target capacity. Actual block length is reported separately; these small CSV files each occupy one smaller block. NameNode total_blocks and used_bytes are cluster-wide, including prior job outputs, and are not the raw-file count or input-file byte sum. Hosts/names come from actual WebHDFS placement, never fabricated chunks.','source_url':WEB_DOC},
        {'term':'NameNode and DataNode','description':'NameNode manages namespace and block-location metadata. Clients transfer file bytes with DataNodes; this explorer reads metadata and does not download HDFS file bytes.','source_url':WEB_DOC},
        {'term':'Completed-job counters','description':'Map input includes 10 CSV headers (438250); map output excludes headers (438240). Counters cover the entire saved job, not the selected month or the three-record teaching sample. HDFS bytes-read counters can exceed raw CSV size because they account for task/job filesystem activity.','source_url':STREAM_DOC},
        {'term':'Teaching trace','description':'The production mapper emits city|month keys and four metrics with timestamp and source offset. Shuffle groups matching keys; reducer deduplicates timestamps, averages temperature/humidity/wind and sums precipitation. The visual replay is instructional and launches no job.','source_url':STREAM_DOC},
    ]}
