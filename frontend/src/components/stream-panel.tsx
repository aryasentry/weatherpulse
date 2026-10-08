"use client";
import { useState } from 'react';
import { Activity, Play, RefreshCw } from 'lucide-react';
import { Panel } from './ui';
import { count, number } from '@/lib/types';
interface Replay {mode:string;algorithm:string;available_records:number;processed_records:number;capacity:number;start:string;end:string;note:string;sample:{city:string;time:string;temperature:number|null;humidity:number|null;precipitation:number|null;wind_speed:number|null}[]}
export default function StreamPanel() {
 const [result,setResult]=useState<Replay|null>(null);const [loading,setLoading]=useState(false);const [error,setError]=useState('');
 async function run(){setLoading(true);setError('');try{const response=await fetch('/api/stream?city=Hyderabad');if(!response.ok){const body=await response.json();throw new Error(typeof body.detail==='string'?body.detail:'Historical replay could not be processed.');}setResult(await response.json());}catch(e){setError(e instanceof Error?e.message:'Unable to load historical replay.');}finally{setLoading(false);}}
 return <Panel title="Historical replay" subtitle="Hyderabad · Reservoir sampling" icon={Activity} action={<button className="button" onClick={run} disabled={loading}>{loading?<RefreshCw size={14} className="spin"/>:<Play size={14}/>} {loading?'Processing…':result?'Run again':'Run replay'}</button>}>
 {!result&&!error&&<p className="panel-note">Sample up to 10,000 archived records.</p>}
 {error&&<p className="filter-error" role="alert">{error}</p>}
 {result&&<><div className="replay-summary"><div><span>Processed records</span><strong>{count(result.processed_records)}</strong></div><div><span>Reservoir capacity</span><strong>{count(result.capacity)}</strong></div><div><span>Available city records</span><strong>{count(result.available_records)}</strong></div><div><span>Replay mode</span><strong>{result.mode}</strong></div></div><p className="panel-note">Previewing {Math.min(5,result.sample.length)} of {count(result.sample.length)} retained records.</p><div className="table-scroll"><table><thead><tr><th>City</th><th>Historical timestamp</th><th>Temperature °C</th><th>Humidity %</th><th>Precipitation mm</th><th>Wind km/h</th></tr></thead><tbody>{result.sample.slice(0,5).map((row,i)=><tr key={i}><td className="strong">{row.city}</td><td>{row.time.replace('T',' ')}</td><td>{number(row.temperature)}</td><td>{number(row.humidity)}</td><td>{number(row.precipitation)}</td><td>{number(row.wind_speed)}</td></tr>)}</tbody></table></div></>}
 </Panel>
}
