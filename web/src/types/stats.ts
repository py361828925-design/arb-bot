export interface PositionLeg {
  exchange?: string;
  return?: number;
}

export interface OpenPosition {
  group_id: string;
  symbol: string;
  long?: PositionLeg | null;
  short?: PositionLeg | null;
  current_funding_diff?: number | null;
  current_countdown_secs?: number | null;
  duration_seconds?: number | null;
  notional_per_leg?: number | null;
}

export interface DynamicStats {
  active_notional: number;
  active_group_count: number;
  total_open: number;
  total_open_count: number;
  total_close: number;
  total_close_count: number;
  net_profit: number;
  logic1_amount: number;
  logic1_count: number;
  logic2_amount: number;
  logic2_count: number;
  logic3_amount: number;
  logic3_count: number;
  logic4_amount: number;
  logic4_count: number;
  logic5_amount: number;
  logic5_count: number;
  updated_at?: string;
}

export interface SnapshotSummary {
  snapshot_date: string;
  total_open: number;
  total_close: number;
  net_profit: number;
  logic1_amount: number;
  logic2_amount: number;
  logic3_amount: number;
  logic4_amount: number;
  logic5_amount: number;
}

export interface PositionEventPayload {
  notional_per_leg?: number | null;
  [key: string]: unknown;
}

export interface PositionEventItem {
  id: string;
  created_at: string;
  event_type: string;
  symbol: string;
  logic_reason: string | null;
  realized_pnl: number | null;
  data?: PositionEventPayload | null;
}
