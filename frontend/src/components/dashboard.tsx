"use client";
import { useCallback, useEffect, useRef, useState } from 'react';
import { BarChart3, ChevronRight, CloudSun, Database, Download, Filter, Home, Menu, Network, RefreshCw, TrendingUp, X, CircleAlert, ArrowUpRight } from 'lucide-react';
import type { DashboardData, Filters } from '@/lib/types';
import { count, query } from '@/lib/types';
import { Analytics, Overview, PipelineView, Predictions } from './views';
import HadoopExplorer from './hadoop-explorer';
const views = [ {id:'overview',label:'Overview',icon:Home}, {id:'analytics',label:'Analytics',icon:BarChart3}, {id:'predictions',label:'Predictions',icon:TrendingUp}, {id:'pipeline',label:'Pipeline',icon:Database}, {id:'explorer',label:'Hadoop Explorer',icon:Network} ] as const;
type View = typeof views[number]['id'];
const initial:Filters={city:'all',start:'2021-01-01',end:'2025-12-31'};
export default function Dashboard() {
  const [view,setView]=useState<View>('overview'); const [mobileOpen,setMobileOpen]=useState(false);
  const [draft,setDraft]=useState<Filters>(initial); const [filters,setFilters]=useState<Filters>(initial);
  const [data,setData]=useState<DashboardData|null>(null); const [cities,setCities]=useState<string[]>([]);
  const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [empty,setEmpty]=useState(false);
  const [retry,setRetry]=useState(0); const [filterError,setFilterError]=useState('');
  const controller=useRef<AbortController|null>(null);
  const fetchData=useCallback(async()=>{controller.current?.abort();const abort=new AbortController();controller.current=abort;setLoading(true);setError('');setEmpty(false);
    try {const response=await fetch(`/api/dashboard?${query(filters)}`,{signal:abort.signal}); if(!response.ok) {let detail='The weather archive could not be loaded.';try {const body=await response.json();detail=typeof body.detail==='string'?body.detail:response.status===422?'Check the selected city and date range.':detail;}catch{}setEmpty(response.status===404);throw new Error(detail);} const result:DashboardData=await response.json();if(abort.signal.aborted)return;setData(result);setCities(result.meta.cities.map(c=>c.name));}
    catch(e) {if(abort.signal.aborted)return;setError(e instanceof Error?e.message:'Unable to connect to the weather API.');}
    finally {if(!abort.signal.aborted)setLoading(false);}
  },[filters]);
  useEffect(()=>{fetchData();return ()=>controller.current?.abort();},[fetchData,retry]);
  useEffect(()=>{if(window.location.hash==='#hadoop-explorer')setView('explorer');},[]);
  function apply(event:React.FormEvent){event.preventDefault();if(!draft.start||!draft.end){setFilterError('Choose both a start and end date.');return;}if(draft.start>draft.end){setFilterError('The start date must be on or before the end date.');return;}setFilterError('');setFilters({...draft});setRetry(x=>x+1);}
  const current=views.find(v=>v.id===view)!;
  return <div className="app-shell">
    {mobileOpen&&<button className="nav-scrim" aria-label="Close navigation" onClick={()=>setMobileOpen(false)}/>}
    <header className={`topbar ${mobileOpen?'open':''}`}><a className="brand" href="/" aria-label="WeatherPulse overview"><CloudSun size={35}/><span>WeatherPulse</span></a><button className="topbar-menu icon-button" onClick={()=>setMobileOpen(!mobileOpen)} aria-expanded={mobileOpen} aria-controls="main-navigation" aria-label={mobileOpen?'Close navigation':'Open navigation'}>{mobileOpen?<X/>:<Menu/>}</button><nav id="main-navigation" aria-label="Main navigation">{views.map(({id,label,icon:Icon})=><button key={id} onClick={()=>{setView(id);setMobileOpen(false);if(id==='explorer')window.history.replaceState(null,'','#hadoop-explorer');else if(window.location.hash==='#hadoop-explorer')window.history.replaceState(null,'',window.location.pathname+window.location.search);window.scrollTo(0,0);}} className={`nav-item ${view===id?'active':''}`} aria-current={view===id?'page':undefined}><Icon size={19}/><span>{label}</span></button>)}</nav><div className="topbar-meta"><span className="archive-dot"/>Historical weather<p>2021 – 2025</p></div></header>
    <main className="main"><header className="page-header"><div className="heading-with-menu"><div><h1>Weather Data Analysis</h1><p>Historical weather analytics.</p></div></div>{view!=='explorer'&&<a className={`button export-button ${!data||loading||error?'disabled':''}`} href={`/api/export?${query(filters)}`} aria-disabled={!data||loading||!!error} onClick={e=>{if(!data||loading||error)e.preventDefault();}} download><Download size={17}/>Export CSV</a>}</header>
    <div className="context-line"><div className="breadcrumbs"><Home size={15}/><span>{current.label}</span><ChevronRight size={14}/><span className="muted">Historical archive</span></div>{view!=='explorer'&&data&&!loading&&!error&&<span className="record-count">{count(data.meta.filtered_records)} hourly records</span>}</div>
    {view!=='explorer'&&<form className="filters" onSubmit={apply} aria-label="Weather filters"><label>City<select value={draft.city} onChange={e=>setDraft({...draft,city:e.target.value})}><option value="all">All cities</option>{cities.map(city=><option key={city} value={city}>{city}</option>)}</select></label><label>From<input type="date" value={draft.start} min="2021-01-01" max="2025-12-31" onChange={e=>setDraft({...draft,start:e.target.value})}/></label><label>To<input type="date" value={draft.end} min="2021-01-01" max="2025-12-31" onChange={e=>setDraft({...draft,end:e.target.value})}/></label><button className="button apply-button" type="submit" disabled={loading}><Filter size={16}/>{loading?'Loading…':'Apply filters'}</button>{filterError&&<p className="filter-error" role="alert">{filterError}</p>}</form>}
    <div className="content" aria-busy={view!=='explorer'&&loading}>
    {view==='explorer'?<HadoopExplorer/>:loading?<Loading/>:error?<div className="state-panel" role="alert"><div className="state-icon"><CircleAlert size={30}/></div><h2>{empty?'No data in this selection':'Unable to load weather data'}</h2><p>{error}</p><button className="button" onClick={()=>setRetry(x=>x+1)}><RefreshCw size={16}/>Retry</button><button className="text-button" onClick={()=>{setDraft(initial);setFilters(initial);setRetry(x=>x+1);}}>Reset filters</button></div>:data?<>{view==='overview'&&<Overview data={data} allCities={filters.city==='all'}/>} {view==='analytics'&&<Analytics data={data} allCities={filters.city==='all'}/>} {view==='predictions'&&<Predictions data={data}/>} {view==='pipeline'&&<PipelineView data={data}/>}</>:null}
    </div>
    <footer className="source-footer"><div><Database size={20}/><div><strong>{data?.meta.source||'Open-Meteo archive (reanalysis)'}</strong><p>Historical modelled weather · {data?.meta.timezone||'Asia/Kolkata'}<span className="footer-divider">·</span>{data?.meta.license||'Historical archive'}</p></div></div><a href={data?.meta.source_url||'https://open-meteo.com/en/docs/historical-weather-api'} target="_blank" rel="noreferrer">Data source<ArrowUpRight size={15}/></a></footer>
    </main>
  </div>
}
function Loading(){return <div className="loading-state" role="status" aria-label="Loading weather analysis"><div className="loading-line"><RefreshCw size={17} className="spin"/>Loading historical weather analysis…</div><div className="stats-grid">{Array.from({length:4},(_,i)=><div key={i} className="skeleton skeleton-stat"/>)}</div><div className="chart-grid">{Array.from({length:4},(_,i)=><div key={i} className="skeleton skeleton-chart"/>)}</div></div>}
