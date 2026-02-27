<script lang="ts">
	import type { StockResult } from '$lib/types';
	import SLTightness from './SLTightness.svelte';

	let {
		stock,
		mode,
		onclose
	}: {
		stock: StockResult;
		mode: string;
		onclose: () => void;
	} = $props();

	let e = $derived(stock.entry_data);
	let pp = $derived(stock.pivot_points);
	let sr = $derived(stock.sr);

	function fmt(n: number | undefined | null): string {
		if (n == null) return '-';
		return 'Rp ' + n.toLocaleString('id-ID', { maximumFractionDigits: 0 });
	}

	function fmtPct(n: number | undefined | null): string {
		if (n == null) return '-';
		return (n >= 0 ? '+' : '') + n.toFixed(1) + '%';
	}

	function copyEntry() {
		if (!e) return;
		const text = `${stock.ticker} | Entry: ${fmt(e.entry_area_min ?? e.entry_low)}-${fmt(e.entry_area_max ?? e.entry_high)} | SL: ${fmt(e.sl)} (${fmtPct(e.sl_pct)}) | TP1: ${fmt(e.tp1)} (${fmtPct(e.tp1_pct)}) | R:R 1:${e.rr1.toFixed(1)}`;
		navigator.clipboard.writeText(text);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	let copied = $state(false);

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') onclose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Slide-over panel -->
<div class="fixed inset-0 z-50 flex justify-end" role="dialog">
	<!-- Backdrop -->
	<button class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick={onclose} aria-label="Close detail panel"></button>

	<!-- Panel -->
	<div
		class="relative z-10 flex w-full max-w-lg flex-col overflow-y-auto bg-white shadow-2xl dark:bg-terminal-surface"
	>
		<!-- Header -->
		<div class="sticky top-0 z-10 border-b border-gray-200 bg-white/95 px-6 py-4 backdrop-blur-sm dark:border-terminal-border dark:bg-terminal-surface/95">
			<div class="flex items-start justify-between">
				<div>
					<div class="flex items-center gap-3">
						<h2 class="text-2xl font-extrabold text-gray-900 dark:text-terminal-text">{stock.ticker}</h2>
						<span
							class="rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide
								{stock.hard_reject
									? 'bg-red-500/20 text-red-600 dark:text-red-400 ring-1 ring-red-300 dark:ring-red-500/30'
									: stock.quality >= 60
										? 'bg-green-500/15 text-green-600 dark:text-green-400'
										: stock.quality >= 40
											? 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400'
											: 'bg-red-500/15 text-red-600 dark:text-red-400'}"
						>
							{stock.hard_reject ? 'REJECT' : stock.q_label}
						</span>
					</div>
					<div class="mt-1 flex items-baseline gap-2">
						<span class="font-mono text-lg font-bold text-gray-900 dark:text-terminal-text">
							{fmt(stock.close)}
						</span>
						<span class="font-mono text-sm font-semibold {stock.pct_change >= 0 ? 'text-green-500' : 'text-red-500'}">
							{fmtPct(stock.pct_change)}
						</span>
					</div>
				</div>
				<button
					onclick={onclose}
					class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-terminal-surface-hover dark:hover:text-terminal-text"
					aria-label="Close"
				>
					<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Score bar -->
			<div class="mt-3 flex items-center gap-3">
				<div class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-terminal-border">
					<div
						class="h-1.5 rounded-full transition-all duration-500
							{stock.quality >= 80 ? 'bg-green-500' : stock.quality >= 60 ? 'bg-blue-500' : stock.quality >= 40 ? 'bg-yellow-500' : 'bg-red-500'}"
						style="width: {stock.quality}%"
					></div>
				</div>
				<span class="font-mono text-xs font-bold text-gray-600 dark:text-terminal-muted">
					{stock.quality}/100
				</span>
				<span class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-500 dark:bg-terminal-bg dark:text-terminal-dim">
					{stock.rule_score}/{stock.max_rules} rules
				</span>
			</div>
		</div>

		<!-- Content -->
		<div class="flex-1 space-y-4 px-6 py-5">

			<!-- Hard Reject Warning -->
			{#if stock.hard_reject}
				<div class="rounded-xl border-2 border-red-300 bg-red-50 p-4 dark:border-red-500/30 dark:bg-red-900/15">
					<div class="flex items-start gap-2">
						<span class="text-lg leading-none">⛔</span>
						<div>
							<p class="text-sm font-bold text-red-700 dark:text-red-400">JANGAN BELI SAHAM INI</p>
							<p class="mt-1 text-xs text-red-600 dark:text-red-400/80">{stock.hard_reject}</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- Small Cap Warning -->
			{#if stock.is_smallcap}
				<div class="rounded-xl border border-orange-200 bg-orange-50 p-3 dark:border-orange-500/20 dark:bg-orange-900/10">
					<div class="flex items-start gap-2">
						<span class="text-base leading-none">🔥</span>
						<div>
							<p class="text-xs font-bold text-orange-700 dark:text-orange-400">SAHAM SMALL CAP — HIGH RISK</p>
							<p class="mt-0.5 text-[11px] text-orange-600 dark:text-orange-400/80">Max 2% modal. SL wajib ketat. Jangan average down.</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- Timeframe & Risk -->
			{#if stock.timeframe || stock.risk}
				<div class="flex flex-wrap gap-2">
					{#if stock.timeframe}
						{@const tfColors = {
							purple: { border: 'border-purple-200 bg-purple-50 dark:border-purple-500/20 dark:bg-purple-900/10', icon: 'text-purple-500', label: 'text-purple-600 dark:text-purple-400', hold: 'text-purple-500/70 dark:text-purple-400/70' },
							blue: { border: 'border-blue-200 bg-blue-50 dark:border-blue-500/20 dark:bg-blue-900/10', icon: 'text-blue-500', label: 'text-blue-600 dark:text-blue-400', hold: 'text-blue-500/70 dark:text-blue-400/70' },
							orange: { border: 'border-orange-200 bg-orange-50 dark:border-orange-500/20 dark:bg-orange-900/10', icon: 'text-orange-500', label: 'text-orange-600 dark:text-orange-400', hold: 'text-orange-500/70 dark:text-orange-400/70' },
							red: { border: 'border-red-200 bg-red-50 dark:border-red-500/20 dark:bg-red-900/10', icon: 'text-red-500', label: 'text-red-600 dark:text-red-400', hold: 'text-red-500/70 dark:text-red-400/70' },
							gray: { border: 'border-gray-200 bg-gray-50 dark:border-terminal-border dark:bg-terminal-surface', icon: 'text-gray-400', label: 'text-gray-600 dark:text-terminal-muted', hold: 'text-gray-500/70 dark:text-terminal-dim' },
						}[stock.timeframe.color] ?? { border: 'border-purple-200 bg-purple-50 dark:border-purple-500/20 dark:bg-purple-900/10', icon: 'text-purple-500', label: 'text-purple-600 dark:text-purple-400', hold: 'text-purple-500/70 dark:text-purple-400/70' }}
						<div class="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 {tfColors.border}">
							<svg class="h-3.5 w-3.5 {tfColors.icon}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<span class="text-[10px] font-bold {tfColors.label}">
								{stock.timeframe.label}
							</span>
							<span class="text-[10px] {tfColors.hold}">
								Hold: {stock.timeframe.hold}
							</span>
						</div>
					{/if}
					{#if stock.risk}
						{@const riskColor = stock.risk.risk_color === 'red'
							? 'border-red-200 bg-red-50 text-red-600 dark:border-red-500/20 dark:bg-red-900/10 dark:text-red-400'
							: stock.risk.risk_color === 'orange'
								? 'border-orange-200 bg-orange-50 text-orange-600 dark:border-orange-500/20 dark:bg-orange-900/10 dark:text-orange-400'
								: 'border-green-200 bg-green-50 text-green-600 dark:border-green-500/20 dark:bg-green-900/10 dark:text-green-400'}
						<div class="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 {riskColor}">
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
							</svg>
							<span class="text-[10px] font-bold">{stock.risk.risk_label}</span>
						</div>
						<div class="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 dark:border-terminal-border dark:bg-terminal-bg">
							<span class="text-[10px] text-gray-500 dark:text-terminal-dim">Max Alokasi:</span>
							<span class="text-[10px] font-bold text-gray-900 dark:text-terminal-text">{stock.risk.max_alloc}</span>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Entry / SL / TP — Only for actionable labels -->
			{#if e && (stock.q_label === 'BUY' || stock.q_label === 'STRONG BUY' || stock.q_label === 'HOT' || stock.q_label === 'WARM')}
				<div class="rounded-xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-blue-50/30 p-5 dark:border-blue-500/30 dark:from-blue-900/20 dark:to-transparent">
					<div class="mb-4 flex items-center justify-between">
						<h3 class="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-terminal-text">
							<svg class="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
							</svg>
							Entry / SL / TP
						</h3>
						<button
							onclick={copyEntry}
							class="flex items-center gap-1 rounded-lg border border-gray-200 px-2 py-1 text-[10px] font-medium text-gray-500 transition-colors hover:bg-white dark:border-terminal-border dark:text-terminal-muted dark:hover:bg-terminal-surface-hover"
						>
							{#if copied}
								<svg class="h-3 w-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
								Copied!
							{:else}
								<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
								</svg>
								Copy
							{/if}
						</button>
					</div>

					<div class="space-y-3">
						<!-- Entry -->
						<div class="flex items-center justify-between">
							<span class="flex items-center gap-1.5 text-sm text-gray-600 dark:text-terminal-muted">
								<span class="inline-block h-2 w-2 rounded-full bg-blue-500"></span>
								Entry
							</span>
							<span class="font-mono text-sm font-bold text-gray-900 dark:text-terminal-text">
								{fmt(e.entry_area_min ?? e.entry_low)} — {fmt(e.entry_area_max ?? e.entry_high)}
							</span>
						</div>
						{#if e.entry_basis}
							<div class="pl-3.5 text-[10px] text-gray-400 dark:text-terminal-dim">Basis: {e.entry_basis}</div>
						{/if}

						<div class="border-t border-blue-100 dark:border-blue-800/30"></div>

						<!-- SL -->
						<div class="flex items-center justify-between">
							<span class="flex items-center gap-1.5 text-sm text-red-500">
								<span class="inline-block h-2 w-2 rounded-full bg-red-500"></span>
								Stop Loss
							</span>
							<span class="font-mono text-sm font-bold text-red-500">
								{fmt(e.sl)} <span class="text-xs opacity-70">({fmtPct(e.sl_pct)})</span>
							</span>
						</div>
						<div class="pl-3.5 text-[10px] text-gray-400 dark:text-terminal-dim">Basis: {e.sl_basis}</div>

						{#if e.sl_ketat && e.sl_vs_atr != null && mode !== 'swing'}
							<div class="flex items-center gap-2 pl-3.5">
								<span class="text-[10px] text-gray-400">SL/ATR:</span>
								<SLTightness level={e.sl_ketat} ratio={e.sl_vs_atr} />
							</div>
							{#if e.sl_ketat === 'SANGAT KETAT' || e.sl_ketat === 'KETAT'}
								<div class="pl-3.5 text-[10px] text-orange-500">{e.sl_ketat_note}</div>
							{/if}
						{/if}

						<div class="border-t border-blue-100 dark:border-blue-800/30"></div>

						<!-- TP1 -->
						<div class="flex items-center justify-between">
							<span class="flex items-center gap-1.5 text-sm text-green-500">
								<span class="inline-block h-2 w-2 rounded-full bg-green-500"></span>
								TP1
							</span>
							<span class="font-mono text-sm font-bold text-green-500">
								{fmt(e.tp1)} <span class="text-xs opacity-70">({fmtPct(e.tp1_pct)})</span>
							</span>
						</div>
						<div class="pl-3.5 text-[10px] text-gray-400 dark:text-terminal-dim">Basis: {e.tp1_basis}</div>

						<!-- TP2 -->
						<div class="flex items-center justify-between">
							<span class="flex items-center gap-1.5 text-sm text-green-500">
								<span class="inline-block h-2 w-2 rounded-full bg-emerald-400"></span>
								TP2
							</span>
							<span class="font-mono text-sm font-bold text-green-500">
								{fmt(e.tp2)} <span class="text-xs opacity-70">({fmtPct(e.tp2_pct)})</span>
							</span>
						</div>
						<div class="pl-3.5 text-[10px] text-gray-400 dark:text-terminal-dim">Basis: {e.tp2_basis}</div>

						<div class="border-t border-blue-100 dark:border-blue-800/30"></div>

						<!-- R:R + Grade -->
						<div class="grid grid-cols-2 gap-3">
							<div class="rounded-lg bg-white/60 px-3 py-2 dark:bg-terminal-bg/60">
								<div class="text-[10px] text-gray-400">R:R (TP1)</div>
								<div class="font-mono text-sm font-bold text-gray-900 dark:text-terminal-text">1:{e.rr1.toFixed(1)}</div>
							</div>
							<div class="rounded-lg bg-white/60 px-3 py-2 dark:bg-terminal-bg/60">
								<div class="text-[10px] text-gray-400">R:R (TP2)</div>
								<div class="font-mono text-sm font-bold text-gray-900 dark:text-terminal-text">1:{e.rr2.toFixed(1)}</div>
							</div>
						</div>

						<!-- R:R Grade badge -->
						{#if stock.rr_grade}
							{@const gradeColor = stock.rr_grade === 'EXCELLENT'
								? 'bg-green-500/15 text-green-600 dark:text-green-400 border-green-200 dark:border-green-500/20'
								: stock.rr_grade === 'GOOD'
									? 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/20'
									: stock.rr_grade === 'CUKUP'
										? 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/20'
										: 'bg-red-500/15 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/20'}
							<div class="flex items-center justify-between rounded-lg border px-3 py-2 {gradeColor}">
								<span class="text-[10px] font-semibold">R:R Grade</span>
								<span class="text-xs font-bold">{stock.rr_grade}</span>
							</div>
						{/if}

						{#if e.expected_return != null}
							<div class="flex items-center justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-terminal-bg/60">
								<span class="text-[10px] text-gray-400">Expected Return</span>
								<span class="font-mono text-sm font-bold {e.expected_return >= 0 ? 'text-green-500' : 'text-red-500'}">
									{fmtPct(e.expected_return)}
								</span>
							</div>
						{/if}

						{#if e.real_gain_tp1 != null}
							<div class="rounded-lg bg-white/60 p-3 dark:bg-terminal-bg/60">
								<div class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Estimasi Realistis</div>
								<div class="grid grid-cols-3 gap-2 text-center">
									<div>
										<div class="font-mono text-xs font-bold text-green-500">+{e.real_gain_tp1?.toFixed(1)}%</div>
										<div class="text-[9px] text-gray-400">Kena TP1</div>
									</div>
									<div>
										<div class="font-mono text-xs font-bold text-green-500">+{e.real_gain_tp2?.toFixed(1)}%</div>
										<div class="text-[9px] text-gray-400">Kena TP2</div>
									</div>
									<div>
										<div class="font-mono text-xs font-bold text-red-500">{e.real_loss_sl?.toFixed(1)}%</div>
										<div class="text-[9px] text-gray-400">Kena SL</div>
									</div>
								</div>
							</div>
						{/if}
					</div>
				</div>
			{:else if !stock.hard_reject && e}
				<!-- WATCH / SKIP — Entry hidden -->
				<div class="rounded-xl border border-gray-200 bg-gray-50/50 p-4 dark:border-terminal-border dark:bg-terminal-bg/50">
					<div class="flex items-center gap-2 text-gray-400 dark:text-terminal-dim">
						<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
						</svg>
						<span class="text-xs font-semibold">Belum memenuhi kriteria BUY</span>
					</div>
					<p class="mt-1.5 text-[11px] text-gray-400 dark:text-terminal-dim">
						Entry/SL/TP hanya ditampilkan untuk saham dengan sinyal BUY atau STRONG BUY. Pantau terus perkembangannya.
					</p>
				</div>
			{/if}

			<!-- Stage (Swing only) -->
			{#if mode === 'swing' && stock.stage_label}
				<div class="rounded-xl border border-gray-200 p-4 dark:border-terminal-border {stock.is_breakout ? 'bg-green-500/5' : ''}">
					<h3 class="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Stage Analysis</h3>
					<div class="flex items-center gap-2">
						<span class="rounded-md bg-gray-100 px-2 py-1 font-mono text-sm font-bold text-gray-900 dark:bg-terminal-bg dark:text-terminal-text">
							{stock.stage_label}
						</span>
						{#if stock.is_breakout}
							<span class="rounded-md bg-green-500/15 px-2 py-0.5 text-[10px] font-bold text-green-500">BREAKOUT</span>
						{/if}
					</div>
					{#if stock.stage_desc}
						<p class="mt-1 text-xs text-gray-500 dark:text-terminal-muted">{stock.stage_desc}</p>
					{/if}
					{#if stock.chart_pattern}
						<div class="mt-2 flex items-center gap-1 text-xs text-blue-500">
							<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
							</svg>
							Pattern: {stock.chart_pattern}
						</div>
					{/if}
				</div>
			{/if}

			<!-- Screening Rules -->
			<div class="rounded-xl border border-gray-200 p-4 dark:border-terminal-border">
				<h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Screening Rules</h3>
				<div class="space-y-1.5">
					{#each stock.rules as rule}
						<div
							class="flex items-center justify-between rounded-lg px-3 py-1.5 text-xs transition-colors
								{rule.passed
									? 'bg-green-500/5 dark:bg-green-900/10'
									: 'bg-red-500/5 dark:bg-red-900/10'}"
						>
							<span class="flex items-center gap-2">
								<span class="flex h-4 w-4 items-center justify-center rounded-full text-[10px]
									{rule.passed
										? 'bg-green-500/20 text-green-600 dark:text-green-400'
										: 'bg-red-500/20 text-red-600 dark:text-red-400'}"
								>
									{rule.passed ? '✓' : '✗'}
								</span>
								<span class="text-gray-700 dark:text-terminal-text">{rule.rule}</span>
							</span>
							<span class="font-mono text-gray-400 dark:text-terminal-dim">{rule.value}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Pivot Points (BSJP/Intraday) -->
			{#if pp}
				<div class="rounded-xl border border-gray-200 p-4 dark:border-terminal-border">
					<h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Pivot Points</h3>
					<div class="grid grid-cols-5 gap-1.5 text-center">
						{#each [
							{ label: 'S2', val: pp.s2, color: 'text-red-500' },
							{ label: 'S1', val: pp.s1, color: 'text-red-400' },
							{ label: 'PP', val: pp.pp, color: 'text-yellow-500' },
							{ label: 'R1', val: pp.r1, color: 'text-green-400' },
							{ label: 'R2', val: pp.r2, color: 'text-green-500' }
						] as p}
							<div class="rounded-lg bg-gray-50 p-2.5 dark:bg-terminal-bg">
								<div class="text-[10px] font-bold {p.color}">{p.label}</div>
								<div class="mt-0.5 font-mono text-xs font-semibold text-gray-900 dark:text-terminal-text">
									{fmt(p.val)}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- S/R (Swing) -->
			{#if sr}
				<div class="rounded-xl border border-gray-200 p-4 dark:border-terminal-border">
					<h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Support / Resistance</h3>
					<div class="grid grid-cols-4 gap-1.5 text-center">
						{#each [
							{ label: 'S2', val: sr.s2, color: 'text-red-500' },
							{ label: 'S1', val: sr.s1, color: 'text-red-400' },
							{ label: 'R1', val: sr.r1, color: 'text-green-400' },
							{ label: 'R2', val: sr.r2, color: 'text-green-500' }
						] as p}
							<div class="rounded-lg bg-gray-50 p-2.5 dark:bg-terminal-bg">
								<div class="text-[10px] font-bold {p.color}">{p.label}</div>
								<div class="mt-0.5 font-mono text-xs font-semibold text-gray-900 dark:text-terminal-text">
									{fmt(p.val)}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Fibonacci (Swing) -->
			{#if stock.fib_levels}
				<div class="rounded-xl border border-gray-200 p-4 dark:border-terminal-border">
					<h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Fibonacci Retracement</h3>
					<div class="space-y-0.5">
						{#each ['0', '0.236', '0.382', '0.5', '0.618', '0.786', '1'] as level}
							{@const price = stock.fib_levels?.[level]}
							{@const isNear =
								price != null &&
								typeof price === 'number' &&
								Math.abs(stock.close - price) / stock.close < 0.02}
							{@const isGolden = level === '0.382' || level === '0.5' || level === '0.618'}
							<div
								class="flex items-center justify-between rounded-lg px-3 py-1.5 text-xs
									{isNear ? 'bg-blue-500/10 ring-1 ring-blue-500/30' : ''}
									{isGolden && !isNear ? 'bg-yellow-500/5' : ''}"
							>
								<span class="font-mono font-semibold text-gray-500 dark:text-terminal-muted">{level}</span>
								<span class="font-mono font-semibold text-gray-900 dark:text-terminal-text">
									{typeof price === 'number' ? fmt(price) : '-'}
								</span>
								<span class="text-[10px]">
									{#if isGolden}
										<span class="text-yellow-500">Golden</span>
									{/if}
									{#if isNear}
										<span class="font-bold text-blue-500">◄ HARGA</span>
									{/if}
								</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Indicators -->
			{#if stock.indicators}
				<div class="rounded-xl border border-gray-200 p-4 dark:border-terminal-border">
					<h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Indikator Teknikal</h3>
					<div class="grid grid-cols-2 gap-1.5">
						{#each Object.entries(stock.indicators) as [key, val]}
							{#if val != null}
								<div class="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-terminal-bg">
									<span class="text-[10px] text-gray-500 dark:text-terminal-dim">{key}</span>
									<span class="font-mono text-xs font-semibold text-gray-900 dark:text-terminal-text">
										{typeof val === 'number' ? val.toFixed(2) : val}
									</span>
								</div>
							{/if}
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
