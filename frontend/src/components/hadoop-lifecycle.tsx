import { ArrowRight, GitBranch, Layers } from 'lucide-react';
import { Panel } from './ui';
const tools=[
 ['Open-Meteo + requests','Historical ERA5 ingestion, source caching and provenance.'],
 ['pandas + PyArrow','Validation, aggregation and compressed Parquet storage.'],
 ['HDFS','Raw files and job outputs · single node · replication 1.'],
 ['Hadoop Streaming','Map / shuffle / reduce via LocalJobRunner.'],
 ['Spark SQL','Independent monthly aggregates and parity checks.'],
 ['scikit-learn','Temperature model with chronological holdout and baseline evaluation.'],
 ['FastAPI','Read-only analytics, export and HDFS inspection API.'],
 ['Next.js + Recharts','Interactive dashboard and charts.'],
] as const;
function Lineage({label,nodes,note}:{label:string;nodes:string[];note:string}) {return <div className="lineage-branch"><span>{label}</span><div>{nodes.map((node,i)=><span key={node}><strong>{node}</strong>{i<nodes.length-1&&<ArrowRight size={15}/>}</span>)}</div><p>{note}</p></div>}
export default function HadoopLifecycle(){return <>
 <Panel title="Data flow" subtitle="Archive processing and verification branches" icon={GitBranch}><div className="lineage-source"><span>Source</span><strong>Open-Meteo ERA5</strong><ArrowRight size={17}/><strong>Raw CSV</strong></div><div className="lineage-branches"><Lineage label="Dashboard" nodes={['Raw CSV','pandas','Parquet','FastAPI','Dashboard / CSV']} note="Clean hourly archive → analytics and exports."/><Lineage label="Predictions" nodes={['Parquet','scikit-learn','Prediction JSON','API / dashboard']} note="Historical holdout evaluation."/><Lineage label="Spark" nodes={['Raw CSV','Spark SQL','Monthly Parquet','Parity check']} note="Independent aggregate verification."/><Lineage label="Hadoop" nodes={['Raw CSV','HDFS input','MapReduce','HDFS output','Parity check']} note="LocalJobRunner · single node."/></div></Panel>
 <Panel title="Stack" icon={Layers}><div className="table-scroll lifecycle-table"><table><thead><tr><th>Tool</th><th>Role</th></tr></thead><tbody>{tools.map(([tool,role])=><tr key={tool}><td className="strong">{tool}</td><td>{role}</td></tr>)}</tbody></table></div></Panel>
 </>}
