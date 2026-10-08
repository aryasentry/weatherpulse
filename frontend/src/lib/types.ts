export type MaybeNumber = number | null;
export interface HadoopEvidence { status:string;engine:string;version:string;execution_mode:string;generated_at:string;input_rows:number;clean_rows:number;monthly_groups:number;parity_passed:boolean;comparison:{passed:boolean;compared_groups:number;tolerance:number;max_abs_error:number};hdfs:{uri:string;input_path:string;output_path:string;namenode_url?:string};job?:{id:string;log_path:string};artifact?:string; }
export interface Pipeline { engine: string; generated_at: string; duration_seconds: number; steps: {name: string;status: string;detail: string}[]; artifacts: {name: string;description: string}[]; spark_verified: boolean; hadoop_verified?:boolean; hadoop_evidence?:HadoopEvidence; spark_evidence?: { engine:string; master:string; input_rows:number; clean_rows:number; city_count:number; monthly_groups:number; query:string; duration_seconds:number; note:string; comparison:{passed:boolean;groups_compared:number;metrics_per_group:number} }; }
export interface DashboardData {
  meta: { title: string; source: string; source_url: string; license: string; data_kind: string; timezone: string; start: string; end: string; total_records: number; filtered_records: number; city_count: number; generated_at: string; engine: string; cities: {name:string;latitude:number;longitude:number}[]; years: number[] };
  summary: { avg_temperature: MaybeNumber; total_precipitation: MaybeNumber; avg_humidity: MaybeNumber; avg_wind_speed: MaybeNumber; max_temperature: MaybeNumber; min_temperature: MaybeNumber; extreme_count: number; temperature_std: MaybeNumber; temperature_variance: MaybeNumber; temperature_median: MaybeNumber };
  trends: {date:string;temperature:MaybeNumber;precipitation:MaybeNumber;humidity:MaybeNumber;wind_speed:MaybeNumber}[];
  comparison: {city:string;temperature:MaybeNumber;precipitation:MaybeNumber;humidity:MaybeNumber;wind_speed:MaybeNumber;records:number}[];
  correlation: {labels:string[];matrix:MaybeNumber[][]};
  extremes: {city:string;date:string;type:string;value:number;threshold:number;unit:string}[];
  quality: {input_rows:number;clean_rows:number;duplicates_removed:number;invalid_rows:number;missing_values:number | Record<string,number>};
  insights: string[]; pipeline: Pipeline;
  prediction: {available:boolean;city:string;model:string;mae:MaybeNumber;baseline_mae:MaybeNumber;rmse:MaybeNumber;train_end:string;test_start:string;test_end:string;train_samples:number;test_samples:number;points:{date:string;actual:MaybeNumber;predicted:MaybeNumber;baseline:MaybeNumber}[];note:string};
}
export interface Filters {city:string;start:string;end:string}
export const number = (value: MaybeNumber | undefined, digits=1) => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('en-IN', {maximumFractionDigits:digits, minimumFractionDigits:digits}) : '—';
export const count = (value: number | undefined) => number(value, 0);
export const month = (value: string) => { const d = new Date(value + (value.length === 7 ? '-01' : '') + 'T00:00:00'); return isNaN(d.getTime()) ? value : d.toLocaleDateString('en-IN', {month:'short',year:'2-digit'}); };
export const query = (filters: Filters) => new URLSearchParams(filters as unknown as Record<string,string>).toString();
