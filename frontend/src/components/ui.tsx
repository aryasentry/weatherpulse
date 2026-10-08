import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { ArrowUpRight } from 'lucide-react';
export function Panel({title,subtitle,icon:Icon,children,className='',action}:{title:string;subtitle?:string;icon?:LucideIcon;children:ReactNode;className?:string;action?:ReactNode}) {return <section className={`panel ${className}`}><div className="panel-heading"><div className="panel-title">{Icon && <Icon size={19}/>}<div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div></div>{action}</div>{children}</section>}
export function Stat({label,value,unit,detail,icon:Icon}:{label:string;value:string;unit:string;detail?:string;icon:LucideIcon}) {return <article className="stat"><div className="stat-top"><span>{label}</span><Icon size={20}/></div><div className="stat-value">{value}<span>{unit}</span></div>{detail && <p>{detail}</p>}</article>}
export function SourceLink({href,children}:{href:string;children:ReactNode}) {return <a className="source-link" href={href} target="_blank" rel="noreferrer">{children}<ArrowUpRight size={14}/></a>}
