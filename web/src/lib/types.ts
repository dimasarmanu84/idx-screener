export interface RuleResult {
	rule: string;
	passed: boolean;
	value: string;
}

export interface EntryData {
	entry: number;
	entry_area_min: number;
	entry_area_max: number;
	avg_entry?: number;
	sl: number;
	sl_basis: string;
	sl_pct: number;
	sl_vs_atr?: number;
	sl_ketat?: string;
	sl_ketat_icon?: string;
	sl_ketat_note?: string;
	tp1: number;
	tp1_basis: string;
	tp1_pct: number;
	tp2: number;
	tp2_basis: string;
	tp2_pct: number;
	rr1: number;
	rr2: number;
	expected_return?: number;
	real_gain_tp1?: number;
	real_gain_tp2?: number;
	real_loss_sl?: number;
	// Swing-specific
	entry_low?: number;
	entry_high?: number;
	entry_mid?: number;
	entry_basis?: string;
	max_alloc?: string;
	hold_short?: string;
	hold_medium?: string;
}

export interface TimeframeInfo {
	label: string;
	hold: string;
	color: string;
}

export interface RiskInfo {
	risk_label: string;
	risk_color: string;
	risk_score: number;
	max_alloc: string;
}

export interface FundamentalInfo {
	fund_class: 'blue_chip' | 'mid_cap' | 'fundamental' | 'spekulatif' | 'unknown';
	fund_label: string;
	fund_color: string;
	fund_desc: string;
}

export interface StockResult {
	ticker: string;
	close: number;
	pct_change: number;
	rule_score: number;
	max_rules: number;
	quality: number;
	status: string;
	q_label: string;
	rr_grade?: string;
	timeframe?: TimeframeInfo;
	risk?: RiskInfo;
	rules: RuleResult[];
	entry_data: EntryData | null;
	indicators?: Record<string, number | null>;
	pivot_points?: Record<string, number>;
	volume_info?: {
		volume: number;
		avg_volume_20d: number;
		volume_ratio: number;
		vol_normalized: boolean;
		value_b: number;
	};
	// Fundamental classification
	fundamental?: FundamentalInfo;
	// Small cap flag
	is_smallcap?: boolean;
	// Hard reject reason (ARA/ARB/extreme CHG%)
	hard_reject?: string | null;
	// Top Gainer fields
	ara_score?: number;
	ara_label?: string;
	ara_rekom?: string;
	ara_pct?: number;
	dist_to_ara_pct?: number;
	ara_limit?: number;
	prev_close?: number;
	consecutive_up_days?: number;
	price_vs_high_pct?: number;
	// Night Scanner fields
	night_score?: number;
	night_label?: string;
	night_catalyst?: string;
	dist_to_high_20d_pct?: number;
	vol_trend_3d?: boolean;
	// Swing-specific
	stage?: number;
	stage_label?: string;
	stage_desc?: string;
	is_breakout?: boolean;
	chart_pattern?: string;
	has_pattern?: boolean;
	vol_label?: string;
	hist_vol_20d?: number;
	mcap_t?: number;
	fib_levels?: Record<string, number | string | null>;
	sr?: { s1: number; s2: number; r1: number; r2: number };
	ma50_slope?: number;
	dist_ma50_pct?: number;
}

export interface MarketStatus {
	is_open: boolean;
	progress: number;
	progress_pct: number;
	session: string;
	timestamp: string;
}

export interface ScreeningResponse {
	mode: string;
	timestamp: string;
	market_status: MarketStatus;
	total_scanned: number;
	total_passed?: number;
	total_errors: number;
	errors: string[];
	results: StockResult[];
	strong: StockResult[];
	watch: StockResult[];
}

export type ScreenerMode = 'bsjp' | 'intraday' | 'swing' | 'top-gainer' | 'night-scanner';
export type StockGroup = 'lq45' | 'idx80' | 'all_idx' | 'all_stocks' | 'all_bursa' | 'jii' | 'jii70' | 'issi';

// === PORTFOLIO TYPES ===

export interface PortfolioHolding {
	ticker: string;
	lot: number;
	avg_price: number;
}

export interface PortfolioSignal {
	code: string;
	label: string;
	reason: string;
	severity: number;
	action_items: string[];
	color: string;
}

export interface PortfolioStockResult {
	ticker: string;
	lot: number;
	shares: number;
	avg_price: number;
	current_price: number;
	pct_change_today: number;
	invested: number;
	market_value: number;
	pnl_rp: number;
	pnl_pct: number;
	signal: PortfolioSignal;
	fundamental?: FundamentalInfo;
	stage?: number;
	stage_label?: string;
	ma50?: number;
	dist_ma50_pct?: number;
	rsi?: number;
	sl?: number;
	tp1?: number;
	tp2?: number;
	entry_data?: EntryData | null;
	indicators?: Record<string, number | null>;
}

export interface PortfolioSummary {
	total_invested: number;
	total_market_value: number;
	total_pnl_rp: number;
	total_pnl_pct: number;
	signal_counts: Record<string, number>;
	cut_loss_tickers: string[];
}

export interface PortfolioResponse {
	timestamp: string;
	total_analyzed: number;
	total_errors: number;
	errors: string[];
	holdings: PortfolioStockResult[];
	summary: PortfolioSummary;
}

// === NOTIFICATION TYPES ===

export interface PortfolioAlert {
	ticker: string;
	signalCode: string;
	signalLabel: string;
	severity: number;
	reason: string;
	pnlPct: number;
	previousSignalCode: string | null;
}

export interface ToastItem {
	id: string;
	alerts: PortfolioAlert[];
	timestamp: number;
}
