import json
from pathlib import Path
import pytest
import requests
from fastapi.testclient import TestClient
from backend import hadoop_explorer as explorer
from backend import main


def fixture_files(tmp_path,monkeypatch):
    raw=tmp_path/'raw'; processed=tmp_path/'processed'; raw.mkdir(); processed.mkdir()
    monkeypatch.setattr(explorer,'RAW',raw); monkeypatch.setattr(explorer,'PROCESSED',processed)
    (raw/'hyderabad.csv').write_text('city,time,temperature,humidity,precipitation,wind_speed,latitude,longitude\nHyderabad,2025-01-01T00:00,20,50,2,4,17.3,78.4\nHyderabad,2025-01-01T01:00,30,60,3,6,17.3,78.4\nHyderabad,2025-01-01T02:00,25,55,4,5,17.3,78.4\nHyderabad,2025-01-01T03:00,40,80,5,7,17.3,78.4\n')
    (processed/'hadoop-monthly.json').write_text(json.dumps([{'city':'Hyderabad','month':'2025-01','records':4,'temperature':28.75,'humidity':61.25,'precipitation':14.,'wind_speed':5.5}]))
    (processed/'hadoop-job.log').write_text('Map input records=4\nMap input records=438250\nMap output records=438240\nReduce input groups=600\nReduce output records=600\nReduce input records=438240\nShuffled Maps =10\n')
    import pandas as pd
    frame=pd.read_csv(raw/'hyderabad.csv',parse_dates=['time'])
    monkeypatch.setattr(explorer,'load_weather',lambda:frame,raising=False)
    evidence={'status':'verified','job':{'id':'job_local_test'},'generated_at':'2026-10-08T00:00:00Z','execution_mode':'LocalJobRunner','input_rows':438240,'clean_rows':438240,'monthly_groups':600,'parity_passed':True,'hdfs':{'input_path':'/weather-data-analysis/raw/abc','output_path':'/weather-data-analysis/results/run'}}
    (processed/'hadoop_evidence.json').write_text(json.dumps(evidence))
    return {'hadoop_verified':True,'hadoop_evidence':evidence}


def offline(*args,**kwargs): raise requests.ConnectionError('offline')


def test_offline_still_returns_real_teaching_sample_and_saved_full_result(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch); monkeypatch.setattr(explorer,'fetch_json',offline)
    result=explorer.build_explorer('Hyderabad','2025-01',proof)
    assert not result['live']['available'] and result['live']['error']
    assert result['job']['verified']
    trace=result['trace']; assert trace['mode']=='instructional sample'
    assert len(trace['raw_records'])==3 and len(trace['mapped'])==3
    assert all(item['key']=='Hyderabad|2025-01' for item in trace['mapped'])
    assert trace['sample_aggregate']['records']==3 and trace['sample_aggregate']['precipitation']==9
    assert trace['full_month_aggregate']['records']==4 and trace['full_month_aggregate']['precipitation']==14
    assert 'not a running Hadoop job' in trace['note']
    assert result['job']['counters']['map_input_records']==438250
    assert result['job']['counters']['shuffled_maps']==10


def test_stale_proof_hides_full_hadoop_result_and_never_queries_old_hdfs_paths(tmp_path,monkeypatch):
    fixture_files(tmp_path,monkeypatch); queries=[]
    def fetch(resource,**kwargs): queries.append((resource,kwargs)); return {'beans':[]}
    monkeypatch.setattr(explorer,'fetch_json',fetch)
    result=explorer.build_explorer('Hyderabad','2025-01',{'hadoop_verified':False})
    assert not result['job']['verified']
    assert result['trace']['full_month_aggregate'] is None
    assert all(resource=='jmx' for resource,_ in queries)


def test_invalid_city_or_month_rejected_before_network(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch)
    monkeypatch.setattr(explorer,'fetch_json',lambda *a,**k:pytest.fail('network should not be called'))
    for city,month in [('Unknown','2025-01'),('Hyderabad','2025-13'),('Hyderabad','202501'),('Hyderabad','2024-01'),('Hyderabad','../../etc/passwd')]:
        with pytest.raises(ValueError): explorer.build_explorer(city,month,proof)


def test_partial_corrupt_jmx_fields_do_not_invent_zero_values(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch)
    def fetch(resource,**kwargs):
        if resource=='jmx': return {'beans':[{'State':'active','SoftwareVersion':'3.5.0','LiveNodes':'not JSON','Used':'NaN','TotalBlocks':13}]}
        return {}
    monkeypatch.setattr(explorer,'fetch_json',fetch)
    result=explorer.build_explorer('Hyderabad','2025-01',proof)
    assert result['live']['available']
    assert result['live']['namenode']['used_bytes'] is None
    assert result['live']['namenode']['live_datanodes'] is None
    assert result['live']['warnings']


def test_files_and_actual_locations_use_reported_lengths_not_configured_capacity(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch)
    def fetch(resource,**kwargs):
        if resource=='jmx': return {'beans':[{'State':'active','SoftwareVersion':'3.5.0','LiveNodes':'{}','DeadNodes':'{}','Safemode':''}]}
        if kwargs['op']=='LISTSTATUS': return {'FileStatuses':{'FileStatus':[{'type':'FILE','pathSuffix':'hyderabad.csv','length':2562050,'blockSize':134217728,'replication':1}]}}
        return {'BlockLocations':{'BlockLocation':[{'offset':0,'length':2562050,'hosts':['127.0.0.1'],'names':['127.0.0.1:19866'],'corrupt':False}]}}
    monkeypatch.setattr(explorer,'fetch_json',fetch)
    result=explorer.build_explorer('Hyderabad','2025-01',proof)
    file=result['live']['selected_file']; assert file['block_size_bytes']==134217728
    assert file['blocks'][0]['length']==2562050 and file['replication']==1
    assert file['blocks'][0]['names']==['127.0.0.1:19866']


def test_read_only_allowlist_rejects_external_urls_paths_and_write_operations():
    for resource,kwargs in [('http://example.com',{}),('webhdfs',{'path':'/etc/passwd','op':'LISTSTATUS'}),('webhdfs',{'path':'/weather-data-analysis/raw/../etc','op':'LISTSTATUS'}),('webhdfs',{'path':'/weather-data-analysis/raw/abc','op':'DELETE'}),('jmx',{'bean':'AnyBean'})]:
        with pytest.raises(ValueError): explorer.fetch_json(resource,**kwargs)


def test_endpoint_validates_inputs_and_offline_contract(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch)
    monkeypatch.setattr(main,'pipeline_status',lambda:proof); monkeypatch.setattr(explorer,'fetch_json',offline)
    client=TestClient(main.app)
    assert client.get('/api/hadoop/explorer?city=Unknown').status_code==422
    result=client.get('/api/hadoop/explorer?city=Hyderabad&month=2025-01')
    assert result.status_code==200 and result.json()['live']['available'] is False


def test_tampered_missing_or_corrupt_monthly_artifact_hides_full_result(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch); monkeypatch.setattr(explorer,'fetch_json',offline)
    file=explorer.PROCESSED/'hadoop-monthly.json'
    data=json.loads(file.read_text()); data[0]['precipitation']=999.; file.write_text(json.dumps(data))
    result=explorer.build_explorer('Hyderabad','2025-01',proof)
    assert result['trace']['full_month_aggregate'] is None
    assert result['trace']['error']
    for replacement in ['{broken JSON','[]']:
        file.write_text(replacement)
        assert explorer.build_explorer('Hyderabad','2025-01',proof)['trace']['full_month_aggregate'] is None


def test_malformed_raw_csv_returns_trace_error_without_losing_saved_job(tmp_path,monkeypatch):
    proof=fixture_files(tmp_path,monkeypatch); monkeypatch.setattr(explorer,'fetch_json',offline)
    (explorer.RAW/'hyderabad.csv').write_bytes(b'city,time\n\xffinvalid UTF8\n')
    result=explorer.build_explorer('Hyderabad','2025-01',proof)
    assert result['job']['verified']
    assert result['trace']['available'] is False and result['trace']['error']
    assert result['trace']['full_month_aggregate'] is None


def test_transport_errors_redirects_and_oversize_responses_are_bounded(monkeypatch):
    from urllib3.exceptions import ReadTimeoutError
    class Body:
        def read1(self,size): raise ReadTimeoutError(None,'fixed localhost','closed body')
    class Response:
        status_code=200; headers={}; raw=Body()
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def raise_for_status(self): pass
    response=Response(); calls=[]
    class Session:
        trust_env=True
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def get(self,url,**kwargs):
            calls.append((url,kwargs,self.trust_env)); return response
    monkeypatch.setattr(explorer.requests,'Session',Session)
    with pytest.raises(requests.RequestException): explorer.fetch_json('jmx',bean='NameNodeInfo')
    response.status_code=302
    with pytest.raises(ValueError,match='redirect'): explorer.fetch_json('jmx',bean='NameNodeInfo')
    response.status_code=200; response.headers={'Content-Length':str(explorer.MAX_RESPONSE+1)}
    with pytest.raises(ValueError,match='size'): explorer.fetch_json('jmx',bean='NameNodeInfo')
    assert all(url.startswith('http://127.0.0.1:19870/') and args['allow_redirects'] is False and trust is False for url,args,trust in calls)
    assert all(args['timeout']==(.3,.3) for _,args,_ in calls)
