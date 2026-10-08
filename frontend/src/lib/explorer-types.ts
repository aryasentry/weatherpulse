export interface HdfsFile {name:string;path:string;length_bytes:number|null;block_size_bytes:number|null;replication:number|null}
export interface HdfsBlock {offset:number;length:number;hosts:string[];names:string[];corrupt:boolean|null}
export interface WeatherAggregate {city:string;month:string;records:number;temperature:number|null;humidity:number|null;precipitation:number|null;wind_speed:number|null}
export interface ExplorerData {
 selection:{city:string;month:string;cities:string[];months:string[]};
 live:{available:boolean;observed_at:string;source:string;error:string|null;warnings:string[];namenode:{state:string|null;safe_mode:boolean|null;version:string|null;used_bytes:number|null;total_blocks:number|null;live_datanodes:number|null;dead_datanodes:number|null};datanodes:{name:string;hostname:string;used_bytes:number|null;capacity_bytes:number|null;remaining_bytes:number|null;last_contact_seconds:number|null}[];files:HdfsFile[];selected_file:(HdfsFile&{blocks:HdfsBlock[]})|null};
 job:{available:boolean;verified:boolean;source:string;error:string|null;id:string;generated_at:string;execution_mode:string;input_rows:number|null;clean_rows:number|null;monthly_groups:number|null;parity_passed:boolean;hdfs_input_path?:string|null;hdfs_output_path?:string|null;counters:Record<string,number|null>};
 trace:{available:boolean;mode:string;source:string;error:string|null;raw_records:{line:string;offset:number;city:string;time:string;temperature:number|null;humidity:number|null;precipitation:number|null;wind_speed:number|null}[];mapped:{key:string;value:{time:string;values:number[];source:string;offset:number};emitted_line:string}[];shuffle:{key:string;values:unknown[];sample_count:number};sample_aggregate:WeatherAggregate|null;full_month_aggregate:WeatherAggregate|null;full_month_verified?:boolean;note:string};
 definitions:{term:string;description:string;source_url:string}[];
}
export const bytes=(value:number|null|undefined)=>typeof value==='number'?value>=1048576?`${(value/1048576).toFixed(2)} MiB`:`${value.toLocaleString('en-IN')} bytes`:'—';
export const observed=(value:string|undefined)=>value&&!isNaN(new Date(value).getTime())?new Date(value).toLocaleString('en-IN'):'—';
