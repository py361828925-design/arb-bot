export interface Thresholds {
  aa: number;
  bb: number;
  cc: number;
  dd: number;
  ee: number;
  ff: number;
  gg: number;
  hh: number;
}

export interface RiskLimits {
  group_max: number;
  duplicate_max: number;
  leverage_max: number;
  margin_per_leg: number;
  taker_fee: number;
  maker_fee: number;
  trade_fee: number;
}

export interface ConfigResponse {
  version: number;
  thresholds: Thresholds;
  risk_limits: RiskLimits;
  global_enable: boolean;
  created_by: string;
  created_at: string;
  scan_interval_seconds?: number;
  close_interval_seconds?: number;
  open_interval_seconds?: number;
}

export type ConfigUpdatePayload = {
  global_enable?: boolean;
  thresholds?: Partial<Thresholds>;
  risk_limits?: Partial<RiskLimits>;
  scan_interval_seconds?: number;
  close_interval_seconds?: number;
  open_interval_seconds?: number;
} & Record<string, unknown>;

export interface ConfigFormValues extends ConfigUpdatePayload {
  global_enable: boolean;
  thresholds: Thresholds;
  risk_limits: RiskLimits;
  scan_interval_seconds: number;
  close_interval_seconds: number;
  open_interval_seconds: number;
}
