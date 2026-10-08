import hashlib
import io
import tarfile
from pathlib import Path
import pytest
from scripts.setup_hadoop import verify_checksum, safe_extract
from scripts.hadoop_native import should_format, make_configuration, compare_monthly
from backend.hadoop_streaming.mapper import map_records
from backend.hadoop_streaming.reducer import reduce_records


def test_checksum_rejects_changed_bytes(tmp_path):
    path=tmp_path/'archive'; path.write_bytes(b'official release')
    digest=hashlib.sha512(path.read_bytes()).hexdigest()
    assert verify_checksum(path, f'SHA512 (hadoop.tar.gz) = {digest}')==digest
    path.write_bytes(b'changed')
    with pytest.raises(ValueError): verify_checksum(path,digest)


def test_extraction_rejects_path_escape(tmp_path):
    path=tmp_path/'bad.tar.gz'
    with tarfile.open(path,'w:gz') as archive:
        member=tarfile.TarInfo('../escape'); member.size=3
        archive.addfile(member,io.BytesIO(b'bad'))
    with pytest.raises(ValueError): safe_extract(path,tmp_path/'target')
    assert not (tmp_path/'escape').exists()


def test_never_formats_existing_namenode_state(tmp_path):
    state=tmp_path/'namenode'
    assert should_format(state)
    state.mkdir(); (state/'unrecognized-state').write_text('preserve')
    with pytest.raises(RuntimeError): should_format(state)
    (state/'current').mkdir(); (state/'current'/'VERSION').write_text('old state')
    assert not should_format(state)


def test_all_daemon_addresses_are_loopback_and_permissions_untouched(tmp_path):
    conf=make_configuration(tmp_path)
    text='\n'.join(path.read_text() for path in conf.glob('*-site.xml'))
    for port in ['19000','19870','19864','19866','19867']: assert f'127.0.0.1:{port}' in text
    assert '0.0.0.0' not in text
    assert 'dfs.permissions.enabled' not in text
    assert 'hadoop.security.authentication' not in text


def test_streaming_numerical_totals_invalid_and_duplicate_handling():
    lines=['city,time,temperature,humidity,precipitation,wind_speed,latitude,longitude\n',
           '0\tHyderabad,2025-01-01T00:00,20,50,2,4,17.3,78.4\n',
           '50\tHyderabad,2025-01-01T01:00,30,60,3,6,17.3,78.4\n',
           '80\tHyderabad,2025-01-01T01:00,30,60,3,6,17.3,78.4\n',
           '100\tHyderabad,2025-01-01T02:00,25,101,0,7,17.3,78.4\n']
    mapped=list(map_records(lines,source='city.csv'))
    result=list(reduce_records(sorted(mapped)))
    assert len(result)==1
    row=result[0]
    assert row['city']=='Hyderabad' and row['month']=='2025-01'
    assert row['records']==2 and row['temperature']==25
    assert row['precipitation']==5 and row['humidity']==55 and row['wind_speed']==5


def test_parity_detects_missing_groups_bad_counts_and_nan():
    row={'city':'Hyderabad','month':'2025-01','records':2,'temperature':25.,'humidity':55.,'precipitation':5.,'wind_speed':5.}
    assert compare_monthly([row],[row])['passed']
    for values in [[],[dict(row,records=1)],[dict(row,precipitation=6)],[dict(row,temperature=float('nan'))],[row,row]]:
        assert not compare_monthly(values,[row])['passed']


def test_job_counters_select_final_total_not_first_mapper():
    from scripts import hadoop_native
    log='InputRows=43824\nCleanRows=43824\nInputRows=438240\nCleanRows=438240\nInvalidRows=0\n'
    assert hadoop_native.parse_counters(log)=={'input_rows':438240,'clean_rows':438240,'invalid_rows':0}
    with pytest.raises(RuntimeError): hadoop_native.parse_counters('InputRows=43824')


def test_failed_run_invalidates_previous_verified_evidence(tmp_path,monkeypatch):
    import json
    from scripts import hadoop_native
    monkeypatch.setattr(hadoop_native,'ROOT',tmp_path)
    output=tmp_path/'data'/'processed'; output.mkdir(parents=True)
    (output/'hadoop_evidence.json').write_text(json.dumps({'status':'verified','parity_passed':True}))
    def failure(value=None): raise RuntimeError('job failure')
    monkeypatch.setattr(hadoop_native,'_run',failure,raising=False)
    with pytest.raises(RuntimeError): hadoop_native.run()
    evidence=json.loads((output/'hadoop_evidence.json').read_text())
    assert evidence['status']=='failed' and evidence['parity_passed'] is False
    assert 'job failure' in evidence['error']


def test_environment_avoids_whitespace_in_hadoop_shell_java_options(tmp_path,monkeypatch):
    from scripts import hadoop_native
    root=tmp_path/'Weather_Data_Analysis'; install=root/'.runtime'/'hadoop-3.5.0'
    (install/'bin').mkdir(parents=True); (install/'bin'/'hdfs').touch()
    monkeypatch.setattr(hadoop_native,'ROOT',root)
    monkeypatch.setattr(hadoop_native,'HADOOP',install)
    monkeypatch.setattr(hadoop_native,'STATE',root/'.runtime'/'hadoop-state')
    env=hadoop_native.environment()
    for key in ['HADOOP_HOME','HADOOP_CONF_DIR','HADOOP_LOG_DIR','HADOOP_PID_DIR']:
        assert ' ' not in env[key]
    assert '-Dweather.hadoop.project=' in env['HADOOP_OPTS']


def test_hadoop_rejects_whitespace_before_downloading_or_starting(tmp_path,monkeypatch):
    from scripts import setup_hadoop,hadoop_native
    root=tmp_path/'Weather Data Analysis'
    monkeypatch.setattr(setup_hadoop,'ROOT',root)
    with pytest.raises(RuntimeError,match='Weather_Data_Analysis'): setup_hadoop.setup()
    assert not root.exists()
    monkeypatch.setattr(hadoop_native,'ROOT',root)
    with pytest.raises(RuntimeError,match='Weather_Data_Analysis'): hadoop_native.start()


def test_verified_cached_installation_supports_offline_repeat(tmp_path,monkeypatch):
    import json
    from scripts import setup_hadoop
    monkeypatch.setattr(setup_hadoop,'ROOT',tmp_path)
    runtime=tmp_path/'.runtime'; monkeypatch.setattr(setup_hadoop,'RUNTIME',runtime)
    path=runtime/'downloads'/'hadoop-3.5.0.tar.gz'; path.parent.mkdir(parents=True); path.write_bytes(b'cached archive')
    installed=runtime/'hadoop-3.5.0'; (installed/'bin').mkdir(parents=True); (installed/'bin'/'hdfs').touch()
    receipt={'version':'3.5.0','sha512':hashlib.sha512(path.read_bytes()).hexdigest()}
    (runtime/'hadoop-download.json').write_text(json.dumps(receipt))
    def no_network(*args,**kwargs): raise RuntimeError('must work offline')
    monkeypatch.setattr(setup_hadoop.urllib.request,'urlopen',no_network)
    assert setup_hadoop.setup()==installed
    path.write_bytes(b'corrupted cache')
    with pytest.raises(ValueError,match='SHA512'): setup_hadoop.setup()
