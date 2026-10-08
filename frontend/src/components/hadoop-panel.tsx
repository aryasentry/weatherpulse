import { CircleAlert, ExternalLink, HardDrive, ShieldCheck } from 'lucide-react';
import type { Pipeline } from '@/lib/types';
import { count, number } from '@/lib/types';
import { Panel } from './ui';
function localNameNode(value?:string) {if(!value)return null;try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)&&['127.0.0.1','localhost','[::1]'].includes(url.hostname)?url.href:null;}catch{return null;}}
export default function HadoopPanel({pipeline}:{pipeline:Pipeline}) {
 const evidence=pipeline.hadoop_evidence;
 if(!pipeline.hadoop_verified||!evidence)return <Panel title="Hadoop" subtitle="HDFS + MapReduce" icon={HardDrive}><div className="threshold-note"><CircleAlert size={17}/><p>No verified Hadoop run is available.</p></div></Panel>;
 const url=localNameNode(evidence.hdfs?.namenode_url);
 return <Panel title="Hadoop run" subtitle={evidence.engine} icon={HardDrive} action={<span className="evidence-snapshot"><ShieldCheck size={14}/>Verified record</span>}>
 <div className="replay-summary"><div><span>Processed input rows</span><strong>{count(evidence.input_rows)}</strong></div><div><span>Clean rows</span><strong>{count(evidence.clean_rows)}</strong></div><div><span>Monthly city groups</span><strong>{count(evidence.monthly_groups)}</strong></div><div><span>Hadoop version</span><strong>{evidence.version}</strong></div></div>
 <dl className="hadoop-facts"><div><dt>Execution mode</dt><dd>{evidence.execution_mode.includes('LocalJobRunner')?'LocalJobRunner · single node':evidence.execution_mode}</dd></div><div><dt>Run timestamp</dt><dd>{evidence.generated_at?new Date(evidence.generated_at).toLocaleString('en-IN'):'—'}</dd></div><div><dt>Independent aggregate parity</dt><dd>{evidence.parity_passed?'Passed':'Not passed'} · {count(evidence.comparison?.compared_groups)} groups compared{typeof evidence.comparison?.max_abs_error==='number'?` · maximum error ${number(evidence.comparison.max_abs_error,8)}`:''}</dd></div><div><dt>HDFS URI</dt><dd className="evidence-path">{evidence.hdfs?.uri}</dd></div><div><dt>HDFS input path</dt><dd className="evidence-path">{evidence.hdfs?.input_path}</dd></div><div><dt>HDFS output path</dt><dd className="evidence-path">{evidence.hdfs?.output_path}</dd></div>{evidence.job?.id&&<div><dt>Recorded job</dt><dd className="evidence-path">{evidence.job.id}</dd></div>}</dl>

 {url&&<a className="source-link namenode-link" href={url} target="_blank" rel="noreferrer">NameNode console<ExternalLink size={14}/></a>}
 <p className="panel-note">Saved run · NameNode console requires HDFS to be online.</p>
 </Panel>
}
