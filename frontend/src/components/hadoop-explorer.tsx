"use client";
import { useEffect, useRef, useState } from 'react';
import { CircleAlert, HardDrive, RefreshCw, ShieldCheck } from 'lucide-react';
import type { ExplorerData } from '@/lib/explorer-types';
import { observed } from '@/lib/explorer-types';
import InsideHdfs from './hdfs-inside';
import HadoopTrace from './hadoop-trace';
import HadoopLifecycle from './hadoop-lifecycle';
import { Panel } from './ui';
const sections=[{id:'hdfs',label:'Inside HDFS'},{id:'trace',label:'Follow a record'},{id:'lifecycle',label:'Data flow'}] as const;
type Section=typeof sections[number]['id'];
export default function HadoopExplorer(){
 const [section,setSection]=useState<Section>('hdfs');const [city,setCity]=useState('Hyderabad');const [month,setMonth]=useState('2025-01');const [data,setData]=useState<ExplorerData|null>(null);const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [cached,setCached]=useState(false);const [refresh,setRefresh]=useState(0);const controller=useRef<AbortController|null>(null);
 useEffect(()=>{const abort=new AbortController();controller.current?.abort();controller.current=abort;const params=new URLSearchParams({city,month});const cacheKey=`weather-hadoop-explorer:${params}`;setLoading(true);setError('');setData(previous=>previous?.selection.city===city&&previous.selection.month===month?previous:null);
  async function request(){try{const response=await fetch(`/api/hadoop/explorer?${params}`,{signal:abort.signal});if(!response.ok){let detail='The Hadoop explorer could not be loaded.';try{const body=await response.json();if(typeof body.detail==='string')detail=body.detail;}catch{}throw new Error(detail);}const result:ExplorerData=await response.json();if(!result.selection||!result.live||!result.trace||!result.job)throw new Error('The explorer response is incomplete.');if(abort.signal.aborted)return;setData(result);setCached(false);try{sessionStorage.setItem(cacheKey,JSON.stringify(result));}catch{}}
   catch(e){if(abort.signal.aborted)return;setError(e instanceof Error?e.message:'Unable to connect to the explorer API.');setCached(true);try{const saved=sessionStorage.getItem(cacheKey);if(saved){const snapshot:ExplorerData=JSON.parse(saved);if(snapshot.selection&&snapshot.live&&snapshot.trace&&snapshot.job)setData(snapshot);}}catch{}}
   finally{if(!abort.signal.aborted)setLoading(false);}}
  request();return()=>abort.abort();
 },[city,month,refresh]);
 const available=data?.live.available&&!cached;const cities=data?.selection.cities||[];const months=data?.selection.months||[];
 return <div className="hadoop-explorer"><div className="section-intro explorer-intro"><div><h2>Hadoop Explorer</h2><p>Storage, recorded runs and data flow.</p></div><HardDrive size={29}/></div>
 <div className="explorer-toolbar"><div className="explorer-selector"><label>City<select value={city} onChange={event=>setCity(event.target.value)} aria-label="Explorer city">{!cities.length&&<option value={city}>{city}</option>}{cities.map(name=><option key={name}>{name}</option>)}</select></label><label>Month<select value={month} onChange={event=>setMonth(event.target.value)} aria-label="Explorer month">{!months.length&&<option value={month}>{month}</option>}{months.map(value=><option key={value}>{value}</option>)}</select></label></div><button className="button" disabled={loading} onClick={()=>setRefresh(x=>x+1)}><RefreshCw size={15} className={loading?'spin':''}/>{loading?'Refreshing…':'Refresh'}</button></div>
 <div className={`explorer-status ${available?'online':'offline'}`} role="status"><span className="observation-dot"/><div><strong>{loading?'Loading observation…':available?'HDFS online':cached?'Offline · saved snapshot':'HDFS offline'}</strong><p>{data?`${cached?'Saved snapshot observed':'Last observation'}: ${observed(data.live.observed_at)} · ${data.selection.city} / ${data.selection.month}`:'No HDFS observation has been loaded.'}</p></div><span>{data?.job.verified?<><ShieldCheck size={14}/>{cached?'Verified at capture':'Saved run verified'}</>:<>Execution proof unverified</>}</span></div>
 {error&&<div className="explorer-warning" role="alert"><CircleAlert size={17}/><p>{error} {data?`Saved snapshot: ${data.selection.city} / ${data.selection.month}.`:'Refresh to retry.'}</p></div>}
 {data&&!available&&!loading&&<div className="explorer-warning"><CircleAlert size={17}/><p>{data.live.error||'HDFS services are offline or their live endpoints are unavailable.'} {data.job.verified?'Saved run available.':'Start HDFS and refresh.'}</p></div>}
 <div className="explorer-tabs" role="tablist" aria-label="Hadoop explorer sections">{sections.map(item=><button key={item.id} id={`explorer-tab-${item.id}`} role="tab" aria-selected={section===item.id} aria-controls={`explorer-section-${item.id}`} onClick={()=>setSection(item.id)}>{item.label}</button>)}</div>
 <div role="tabpanel" id={`explorer-section-${section}`} aria-labelledby={`explorer-tab-${section}`}>
 {section==='lifecycle'?<HadoopLifecycle/>:!data?<Panel title={loading?'Loading the explorer':'Explorer unavailable'} icon={HardDrive}><p className="empty-copy">{loading?'Loading HDFS metadata and saved runs…':'No saved snapshot for this selection. Refresh to retry.'}</p></Panel>:section==='hdfs'?<InsideHdfs data={cached?{...data,live:{...data.live,available:false}}:data} onCity={setCity}/>:<HadoopTrace key={`${data.selection.city}-${data.selection.month}`} data={data}/>}
 </div>
 {data?.live.warnings?.length ? <details className="explorer-definitions"><summary>Observation notes ({data.live.warnings.length})</summary>{data.live.warnings.map((warning,i)=><p key={i}>{warning}</p>)}</details>:null}

 </div>
}
