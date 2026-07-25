export interface Metrics {
  avg_daily_range_pct: number;
  avg_volume: number;
  spread_pct: number;
  momentum_today_pct: number;
}

export interface TechnicalPick {
  ticker: string;
  rank: number;
  score: number;
  metrics: Metrics;
}

export interface CompanyNews {
  ticker: string;
  summary: string | null;
  has_catalyst: boolean;
}

export interface NewsData {
  market_risk_score: number;
  macro_summary: string;
  market_summary: string;
  international_summary: string;
  companies: CompanyNews[];
}

export interface AggregatePick {
  ticker: string;
  final_rank: number;
  avg_rank: number;
  times_first: number;
  why: string | null;
}

export interface RunPick {
  ticker: string;
  rank: number;
  reason: string | null;
}

export interface LlmRun {
  run_index: number;
  model: string;
  picks: RunPick[];
}

export interface DecisionData {
  num_runs: number;
  aggregate: AggregatePick[];
  runs: LlmRun[];
}

export interface Research {
  date: string;
  has_data: boolean;
  technical?: { run_datetime: string; picks: TechnicalPick[] };
  news?: NewsData | null;
  decision?: DecisionData | null;
}

export interface RunStatus {
  running: boolean;
  error: string | null;
  finished_at: string | null;
}

export async function fetchResearch(date: string): Promise<Research> {
  const r = await fetch(`/api/research?date=${date}`);
  if (!r.ok) throw new Error(`research ${r.status}`);
  return r.json();
}

export async function triggerRun(): Promise<{ started: boolean }> {
  const r = await fetch(`/api/research/run`, { method: "POST" });
  return r.json();
}

export async function fetchStatus(): Promise<RunStatus> {
  const r = await fetch(`/api/research/status`);
  return r.json();
}
