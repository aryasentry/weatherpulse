"""Run native project-local HDFS and real Hadoop Streaming on macOS.

python scripts/setup_hadoop.py                    # verified official download
python scripts/hadoop_native.py start             # NameNode + DataNode, no SSH
python scripts/hadoop_native.py run               # HDFS upload, MapReduce, parity
python scripts/hadoop_native.py status            # owned PIDs / localhost ports
python scripts/hadoop_native.py stop              # bounded shutdown, retains HDFS

Requires JDK 17. --java-home selects an existing JDK; no global installation.
Only a NEW, EMPTY project NameNode directory is formatted. Existing state is
never reformatted. Permissions/authentication defaults are left unchanged.
MapReduce runs via LocalJobRunner; it reads/writes real HDFS, without YARN.
Optional Hadoop requires a whitespace-free full project path, e.g.
~/Projects/Weather_Data_Analysis; the normal dashboard supports spaces.
"""
import argparse
import hashlib
import json
import math
import os
import re
import signal
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path
from xml.etree.ElementTree import Element,SubElement,tostring
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
RUNTIME=ROOT/'.runtime'
HADOOP=RUNTIME/'hadoop-3.5.0'
STATE=RUNTIME/'hadoop-state'
URI='hdfs://127.0.0.1:19000'
NAMENODE_URL='http://127.0.0.1:19870'
PORTS=[19000,19870,19864,19866,19867]


def should_format(directory):
    directory=Path(directory)
    if (directory/'current'/'VERSION').is_file(): return False
    if directory.exists() and any(directory.iterdir()): raise RuntimeError('Unrecognized existing NameNode state: preserving it; refusing to format')
    return True


def make_configuration(state):
    state=Path(state).resolve(); conf=state/'conf'; conf.mkdir(parents=True,exist_ok=True)
    properties={
        'core-site.xml':{'fs.defaultFS':URI,'hadoop.tmp.dir':str(state/'tmp')},
        'hdfs-site.xml':{'dfs.replication':'1','dfs.namenode.name.dir':str(state/'namenode'),'dfs.datanode.data.dir':str(state/'datanode'),'dfs.namenode.rpc-address':'127.0.0.1:19000','dfs.namenode.rpc-bind-host':'127.0.0.1','dfs.namenode.http-address':'127.0.0.1:19870','dfs.namenode.http-bind-host':'127.0.0.1','dfs.datanode.address':'127.0.0.1:19866','dfs.datanode.http.address':'127.0.0.1:19864','dfs.datanode.ipc.address':'127.0.0.1:19867','dfs.datanode.hostname':'127.0.0.1','dfs.client.use.datanode.hostname':'true','dfs.datanode.use.datanode.hostname':'true'},
        'mapred-site.xml':{'mapreduce.framework.name':'local','mapreduce.cluster.local.dir':str(state/'mapred-local'),'mapreduce.jobtracker.staging.root.dir':str(state/'staging'),'mapreduce.job.reduces':'1'},
    }
    for filename,values in properties.items():
        xml=Element('configuration')
        for name,value in values.items():
            prop=SubElement(xml,'property'); SubElement(prop,'name').text=name; SubElement(prop,'value').text=value
        (conf/filename).write_bytes(tostring(xml,encoding='utf-8',xml_declaration=True))
    (conf/'hadoop-env.sh').write_text('# Environment is passed only to this project subprocess.\n')
    logging=HADOOP/'etc'/'hadoop'/'log4j.properties'
    if logging.is_file(): (conf/'log4j.properties').write_text(logging.read_text())
    return conf


def java_home(value=None):
    candidates=[value,os.environ.get('JAVA_HOME'),'/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home']
    if sys.platform=='darwin':
        result=subprocess.run(['/usr/libexec/java_home','-v','17'],capture_output=True,text=True)
        if result.returncode==0: candidates.append(result.stdout.strip())
    for candidate in candidates:
        if not candidate: continue
        executable=Path(candidate)/'bin'/'java'
        if not executable.is_file(): continue
        output=subprocess.run([str(executable),'-version'],capture_output=True,text=True)
        if re.search(r'version "17\.',output.stderr+output.stdout): return str(Path(candidate).resolve())
    raise RuntimeError('JDK17 required. Install an appropriate Temurin17 JDK, or pass --java-home /path/to/jdk17. Hadoop setup does not change global Java.')


def project_marker(): return '-Dweather.hadoop.project='+hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]


def environment(value=None):
    if not (HADOOP/'bin'/'hdfs').is_file(): raise RuntimeError('Hadoop is not installed in .runtime. Run python scripts/setup_hadoop.py first.')
    env=os.environ.copy(); env.update({'JAVA_HOME':java_home(value),'HADOOP_HOME':os.path.relpath(HADOOP,ROOT),'HADOOP_CONF_DIR':os.path.relpath(make_configuration(STATE),ROOT),'HADOOP_LOG_DIR':os.path.relpath(STATE/'logs',ROOT),'HADOOP_PID_DIR':os.path.relpath(STATE/'pids',ROOT),'HADOOP_OPTS':'-Djava.net.preferIPv4Stack=true '+project_marker(),'HADOOP_HEAPSIZE_MAX':'512','PATH':str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')})
    (STATE/'logs').mkdir(parents=True,exist_ok=True)
    return env


def hdfs(args,env,timeout=120):
    result=subprocess.run([str(HADOOP/'bin'/'hdfs'),*args],env=env,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    if result.returncode: raise RuntimeError(f'HDFS command failed ({args[0]}): {result.stderr[-3000:]}')
    return result.stdout


def pid_file(role): return STATE/f'{role}.json'


def owned_process(role):
    path=pid_file(role)
    if not path.exists(): return None
    try:
        pid=int(json.loads(path.read_text())['pid'])
        result=subprocess.run(['ps','-p',str(pid),'-o','args='],capture_output=True,text=True,timeout=5)
        classname='org.apache.hadoop.hdfs.server.'+('namenode.NameNode' if role=='namenode' else 'datanode.DataNode')
        if result.returncode==0 and project_marker() in result.stdout and classname in result.stdout: return pid
    except (ValueError,KeyError,OSError,subprocess.TimeoutExpired): pass
    return None


def listening(port):
    with socket.socket() as sock:
        sock.settimeout(.3)
        return sock.connect_ex(('127.0.0.1',port))==0


def status():
    result={'namenode_pid':owned_process('namenode'),'datanode_pid':owned_process('datanode'),'ports':{str(port):listening(port) for port in PORTS},'namenode_url':NAMENODE_URL,'hdfs_uri':URI,'state':str(STATE)}
    result['running']=bool(result['namenode_pid'] and result['datanode_pid'] and all(result['ports'].values()))
    return result


def start(value=None):
    from scripts.setup_hadoop import check_project_path
    check_project_path(ROOT)
    current=status()
    if current['running']: print(json.dumps(current),flush=True); return current
    if current['namenode_pid'] or current['datanode_pid']: raise RuntimeError('Partial project HDFS state: run stop then start; preserving existing storage.')
    occupied=[port for port in PORTS if listening(port)]
    if occupied: raise RuntimeError(f'Project HDFS ports already in use: {occupied}; no unrelated process will be stopped.')
    env=environment(value); directory=STATE/'namenode'
    if should_format(directory):
        directory.mkdir(parents=True,exist_ok=True)
        print('Formatting NEW empty project-local NameNode storage (no force).',flush=True)
        output=hdfs(['namenode','-format','-nonInteractive'],env)
        (STATE/'logs'/'format.log').write_text(output)
    for role in ['namenode','datanode']:
        with (STATE/'logs'/f'{role}.log').open('ab') as log:
            process=subprocess.Popen([str(HADOOP/'bin'/'hdfs'),role],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        pid_file(role).write_text(json.dumps({'pid':process.pid,'created_at':datetime.now(timezone.utc).isoformat(),'runtime':str(HADOOP)}))
        print(f'Started {role} PID {process.pid}',flush=True)
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        current=status()
        if current['running']:
            try:
                report=hdfs(['dfsadmin','-report'],env,timeout=10)
                safe=hdfs(['dfsadmin','-safemode','get'],env,timeout=10)
                if 'Live datanodes (1)' in report and 'Safe mode is OFF' in safe:
                    print(json.dumps(current),flush=True); return current
            except RuntimeError: pass
        time.sleep(1)
    raise RuntimeError('HDFS did not become ready within60s. Inspect .runtime/hadoop-state/logs/*.log; run stop to clean owned processes.')


def stop():
    for role in ['datanode','namenode']:
        pid=owned_process(role)
        if pid: os.kill(pid,signal.SIGTERM)
    deadline=time.monotonic()+15
    while time.monotonic()<deadline and any(owned_process(role) for role in ['datanode','namenode']): time.sleep(.3)
    for role in ['datanode','namenode']:
        pid=owned_process(role)
        if pid: os.kill(pid,signal.SIGKILL)
        pid_file(role).unlink(missing_ok=True)
    result=status(); print(json.dumps(result),flush=True)
    return result


def compare_monthly(actual,expected,tolerance=1e-6):
    keys=lambda row:(row['city'],row['month'])
    observed={keys(row):row for row in actual}; reference={keys(row):row for row in expected}
    passed=len(observed)==len(actual) and len(reference)==len(expected) and set(observed)==set(reference)
    max_error=0.; failures=[]
    for key in set(observed)&set(reference):
        for metric in ['records','temperature','humidity','precipitation','wind_speed']:
            a,b=float(observed[key][metric]),float(reference[key][metric]); error=abs(a-b)
            if math.isfinite(error): max_error=max(max_error,error)
            if not math.isfinite(a) or not math.isfinite(b) or (error!=0 if metric=='records' else error>tolerance): passed=False; failures.append({'city':key[0],'month':key[1],'metric':metric})
    return {'passed':passed,'compared_groups':len(set(observed)&set(reference)),'expected_groups':len(reference),'actual_groups':len(observed),'tolerance':tolerance,'max_abs_error':max_error,'failures':failures[:10]}


def parse_counters(log):
    result={}
    for source,key in [('InputRows','input_rows'),('CleanRows','clean_rows'),('InvalidRows','invalid_rows')]:
        matches=re.findall(r'\b'+source+r'=(\d+)',log)
        if not matches: raise RuntimeError(f'Missing final Hadoop counter {source}; cannot verify execution')
        result[key]=int(matches[-1])
    return result


def run(value=None):
    path=ROOT/'data'/'processed'/'hadoop_evidence.json'; path.parent.mkdir(parents=True,exist_ok=True)
    initial={'status':'running','parity_passed':False,'generated_at':datetime.now(timezone.utc).isoformat(),'engine':'Apache Hadoop 3.5.0 HDFS + Hadoop Streaming'}
    path.write_text(json.dumps(initial,indent=2))
    try:
        return _run(value)
    except (Exception,KeyboardInterrupt) as exc:
        initial.update({'status':'failed','error':str(exc),'generated_at':datetime.now(timezone.utc).isoformat()})
        path.write_text(json.dumps(initial,indent=2)); raise


def _run(value=None):
    import pandas as pd
    from backend.analytics import load_weather
    started=time.perf_counter(); start(value); env=environment(value)
    raw_files=sorted((ROOT/'data'/'raw').glob('*.csv'))
    checksums=[{'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in raw_files]
    cache_id=hashlib.sha256(json.dumps(checksums,sort_keys=True).encode()).hexdigest()[:16]
    input_path=f'/weather-data-analysis/raw/{cache_id}'
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
    output_path=f'/weather-data-analysis/results/{run_id}'
    hdfs(['dfs','-mkdir','-p',input_path,'/weather-data-analysis/results'],env)
    # -put actually copies all ten city CSVs into HDFS; overwrite only this content-addressed project cache.
    hdfs(['dfs','-put','-f',*[str(path) for path in raw_files],input_path],env)
    listing=hdfs(['dfs','-ls',input_path],env)
    print(f'Uploaded {len(raw_files)} actual city CSVs into {URI}{input_path}',flush=True)
    jars=list((HADOOP/'share'/'hadoop'/'tools'/'lib').glob('hadoop-streaming-*.jar'))
    if len(jars)!=1: raise RuntimeError('Expected exactly one Hadoop Streaming release JAR')
    mapper=ROOT/'backend'/'hadoop_streaming'/'mapper.py'; reducer=ROOT/'backend'/'hadoop_streaming'/'reducer.py'
    command=[str(HADOOP/'bin'/'hadoop'),'jar',str(jars[0]),'-D','mapreduce.framework.name=local','-D','mapreduce.job.reduces=1','-D','stream.map.input.ignoreKey=false','-files',mapper.as_uri()+','+reducer.as_uri(),'-input',URI+input_path+'/*.csv','-output',URI+output_path,'-mapper','python3 mapper.py','-reducer','python3 reducer.py']
    log_path=STATE/'logs'/f'mapreduce-{run_id}.log'
    print('Executing actual Hadoop Streaming MapReduce with HDFS input/output...',flush=True)
    with log_path.open('w') as log:
        completed=subprocess.run(command,env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    if completed.returncode: raise RuntimeError(f'Hadoop Streaming failed. Inspect {log_path}: '+log_path.read_text()[-5000:])
    text=hdfs(['dfs','-cat',output_path+'/part-*'],env)
    actual=[json.loads(line.split('\t',1)[1]) for line in text.splitlines() if line]
    frame=load_weather()
    grouped=frame.assign(month=frame.time.dt.strftime('%Y-%m')).groupby(['city','month']).agg(records=('city','size'),temperature=('temperature','mean'),humidity=('humidity','mean'),precipitation=('precipitation','sum'),wind_speed=('wind_speed','mean')).reset_index()
    expected=grouped.to_dict(orient='records'); comparison=compare_monthly(actual,expected)
    if not comparison['passed']: raise RuntimeError('Hadoop versus pandas parity failed: '+json.dumps(comparison))
    log_text=log_path.read_text(); jobs=re.findall(r'job_local\w+',log_text)
    counters=parse_counters(log_text)
    input_rows=counters['input_rows']; raw_rows=sum(len(pd.read_csv(path)) for path in raw_files)
    if input_rows!=raw_rows or counters['clean_rows']!=sum(row['records'] for row in actual): raise RuntimeError('Hadoop final counters disagree with raw CSV / reduced row totals')
    artifact=ROOT/'data'/'processed'/'hadoop-monthly.json'; artifact.write_text(json.dumps(actual,indent=2,allow_nan=False))
    # Keep bounded job evidence in the delivery; bulky runtime/download stays excluded.
    deliver_log=ROOT/'data'/'processed'/'hadoop-job.log'; deliver_log.write_text(log_text)
    receipt=json.loads((RUNTIME/'hadoop-download.json').read_text())
    evidence={'status':'verified','engine':'Apache Hadoop 3.5.0 HDFS + Hadoop Streaming','version':'3.5.0','execution_mode':'HDFS NameNode/DataNode + MapReduce LocalJobRunner (no YARN)','dataset_sha256':hashlib.sha256((ROOT/'data'/'processed'/'weather.parquet').read_bytes()).hexdigest(),'raw_checksums':checksums,'generated_at':datetime.now(timezone.utc).isoformat(),'duration_seconds':round(time.perf_counter()-started,3),'input_rows':input_rows,'counters':counters,'clean_rows':sum(row['records'] for row in actual),'city_count':int(frame.city.nunique()),'monthly_groups':len(actual),'parity_passed':comparison['passed'],'comparison':comparison,'hdfs':{'uri':URI,'input_path':input_path,'output_path':output_path,'namenode_url':NAMENODE_URL,'replication':1,'csv_files':len(raw_files),'listing':listing},'job':{'id':jobs[-1] if jobs else None,'log_path':'data/processed/hadoop-job.log','runtime_log_path':str(log_path),'mapper':'backend/hadoop_streaming/mapper.py','reducer':'backend/hadoop_streaming/reducer.py'},'artifact':'data/processed/hadoop-monthly.json','download':receipt,'java_home':env['JAVA_HOME'],'note':'Actual HDFS daemons and actual Hadoop Streaming map/shuffle/reduce executed on native macOS. LocalJobRunner computes on one machine; no YARN cluster or distributed speedup is claimed. Ports bind loopback; no SSH configuration or global package changes.'}
    path=ROOT/'data'/'processed'/'hadoop_evidence.json'; path.write_text(json.dumps(evidence,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in evidence.items() if k not in ['raw_checksums','hdfs','download']}),flush=True)
    return evidence


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command',choices=['start','run','status','stop']); parser.add_argument('--java-home')
    args=parser.parse_args()
    if args.command=='status': print(json.dumps(status(),indent=2))
    elif args.command=='stop': stop()
    elif args.command=='start': start(args.java_home)
    else: run(args.java_home)

if __name__=='__main__':
    try: main()
    except (RuntimeError,OSError,subprocess.TimeoutExpired) as exc: print(f'ERROR: {exc}',file=sys.stderr); raise SystemExit(1)
