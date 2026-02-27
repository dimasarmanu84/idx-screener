<script lang="ts">
	import type { StockResult } from '$lib/types';
	import ScoreGauge from './ScoreGauge.svelte';
	import SLTightness from './SLTightness.svelte';

	let {
		data,
		mode,
		onselect
	}: {
		data: StockResult[];
		mode: string;
		onselect: (stock: StockResult) => void;
	} = $props();

	let sortField = $state('quality');
	let sortDir = $state<'asc' | 'desc'>('desc');
	let search = $state('');
	let labelFilter = $state('ALL');
	let fundFilter = $state('ALL');
	let selectedTicker = $state('');

	const fundFilterOptions = ['ALL', 'blue_chip', 'mid_cap', 'fundamental', 'spekulatif'] as const;
	const fundFilterLabels: Record<string, string> = {
		ALL: 'All',
		blue_chip: 'Blue Chip',
		mid_cap: 'Mid Cap',
		fundamental: 'Fundamental',
		spekulatif: 'Spekulatif',
	};
	const fundBadgeColors: Record<string, string> = {
		blue_chip: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400',
		mid_cap: 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400',
		fundamental: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400',
		spekulatif: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400',
		unknown: 'bg-gray-100 text-gray-500 dark:bg-gray-500/15 dark:text-gray-400',
	};

	function toggleSort(field: string) {
		if (sortField === field) {
			sortDir = sortDir === 'desc' ? 'asc' : 'desc';
		} else {
			sortField = field;
			sortDir = 'desc';
		}
	}

	let filtered = $derived(
		data.filter((s) => {
			if (search && !s.ticker.toLowerCase().includes(search.toLowerCase())) return false;
			if (labelFilter === 'LAYAK') {
				// Swing filter: only stocks passing all 5 anti-false-breakout checks
				if (!getSwingFilterChecks(s).layak) return false;
			} else if (labelFilter !== 'ALL' && s.q_label !== labelFilter) {
				return false;
			}
			if (fundFilter !== 'ALL' && s.fundamental?.fund_class !== fundFilter) return false;
			return true;
		})
	);

	let sorted = $derived(
		[...filtered].sort((a, b) => {
			const va = (a as any)[sortField] as number;
			const vb = (b as any)[sortField] as number;
			if (va == null && vb == null) return 0;
			if (va == null) return 1;
			if (vb == null) return -1;
			return sortDir === 'desc' ? vb - va : va - vb;
		})
	);

	function fmt(n: number | undefined | null): string {
		if (n == null) return '-';
		return n.toLocaleString('id-ID', { maximumFractionDigits: 0 });
	}

	function fmtPct(n: number | undefined | null): string {
		if (n == null) return '-';
		return (n >= 0 ? '+' : '') + n.toFixed(1) + '%';
	}

	const labelColors: Record<string, string> = {
		'STRONG BUY': 'bg-green-100 text-green-700 border border-green-200 dark:bg-green-500/15 dark:text-green-400 dark:border-green-500/30',
		BUY: 'bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-500/15 dark:text-blue-400 dark:border-blue-500/30',
		WATCH: 'bg-yellow-100 text-yellow-700 border border-yellow-200 dark:bg-yellow-500/15 dark:text-yellow-400 dark:border-yellow-500/30',
		SKIP: 'bg-gray-100 text-gray-600 border border-gray-200 dark:bg-gray-500/15 dark:text-gray-400 dark:border-gray-500/30'
	};

	const baseFilterLabels = ['ALL', 'STRONG BUY', 'BUY', 'WATCH', 'SKIP'];
	let filterLabels = $derived(mode === 'swing' ? [...baseFilterLabels, 'LAYAK'] : baseFilterLabels);

	// Swing anti-false-breakout filter checks
	function getSwingFilterChecks(stock: StockResult) {
		const e = stock.entry_data;
		const mcap = stock.mcap_t ?? 0;
		const avgVol = stock.volume_info?.avg_volume_20d ?? 0;
		const slPct = Math.abs(e?.sl_pct ?? 0);
		const stg = stock.stage ?? 0;
		const atrPct = stock.indicators?.atr_pct ?? 0;
		const checks = [
			{ key: 'MCap', pass: mcap >= 5, val: `${mcap.toFixed(0)}T` },
			{ key: 'Vol', pass: avgVol >= 5_000_000, val: `${(avgVol / 1e6).toFixed(1)}jt` },
			{ key: 'SL', pass: slPct <= 6, val: `${slPct.toFixed(1)}%` },
			{ key: 'Stage', pass: stg === 12 || stg === 2, val: stg === 12 ? 'BRK' : stg === 2 ? 'S2' : `S${stg}` },
			{ key: 'ATR%', pass: atrPct <= 4.5, val: `${atrPct.toFixed(1)}%` }
		];
		const passCount = checks.filter((c) => c.pass).length;
		return { checks, passCount, layak: passCount === 5 };
	}

	function handleSelect(stock: StockResult) {
		selectedTicker = stock.ticker;
		onselect(stock);
	}

	let copiedTicker = $state('');

	function copyRow(stock: StockResult, event: MouseEvent) {
		event.stopPropagation();
		const e = stock.entry_data;
		let text: string;
		if (stock.hard_reject) {
			text = `${stock.ticker} | REJECT — ${stock.hard_reject}`;
		} else if (e) {
			const entryMin = e.entry_area_min ?? e.entry_low;
			const entryMax = e.entry_area_max ?? e.entry_high;
			text = `${stock.ticker} | Entry: ${fmt(entryMin)}-${fmt(entryMax)} | SL: ${fmt(e.sl)} (${fmtPct(e.sl_pct)}) | TP1: ${fmt(e.tp1)} (${fmtPct(e.tp1_pct)}) | R:R 1:${e.rr1.toFixed(1)}`;
		} else {
			text = `${stock.ticker} | ${stock.q_label} | Harga: ${fmt(stock.close)} | CHG: ${fmtPct(stock.pct_change)}`;
		}
		navigator.clipboard.writeText(text);
		copiedTicker = stock.ticker;
		setTimeout(() => { if (copiedTicker === stock.ticker) copiedTicker = ''; }, 1500);
	}

	function exportCSV() {
		const headers = ['Ticker', 'Harga', 'Chg%', 'Score', 'Label', 'Rules', 'Entry', 'SL', '%SL', 'TP1', 'R:R', 'Reject'];
		const rows = sorted.map((s) => {
			const e = s.entry_data;
			return [
				s.ticker,
				s.close,
				s.pct_change?.toFixed(1),
				s.quality,
				s.hard_reject ? 'REJECT' : s.q_label,
				`${s.rule_score}/${s.max_rules}`,
				e ? `${e.entry_area_min ?? e.entry_low}-${e.entry_area_max ?? e.entry_high}` : '',
				e?.sl ?? '',
				e ? e.sl_pct?.toFixed(1) + '%' : '',
				e?.tp1 ?? '',
				e ? '1:' + e.rr1?.toFixed(1) : '',
				s.hard_reject || ''
			].join(',');
		});
		const csv = [headers.join(','), ...rows].join('\n');
		const blob = new Blob([csv], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `screener_${mode}_${new Date().toISOString().slice(0, 10)}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<!-- Toolbar: Search + Filter + Export -->
<div class="mb-3 flex flex-wrap items-center gap-2">
	<!-- Search -->
	<div class="relative">
		<svg class="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400 dark:text-terminal-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
		</svg>
		<input
			type="text"
			bind:value={search}
			placeholder="Cari ticker..."
			class="h-8 w-40 rounded-lg border border-gray-200 bg-white pl-8 pr-3 text-xs text-gray-700 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder-terminal-dim"
		/>
	</div>

	<!-- Label filter pills -->
	<div class="flex gap-1">
		{#each filterLabels as label}
			<button
				onclick={() => (labelFilter = label)}
				class="rounded-md px-2 py-1 text-[10px] font-semibold uppercase tracking-wider transition-all
					{labelFilter === label
						? label === 'LAYAK'
							? 'bg-green-600 text-white shadow-sm ring-1 ring-green-400'
							: 'bg-blue-600 text-white shadow-sm'
						: label === 'LAYAK'
							? 'text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20'
							: 'text-gray-500 hover:bg-gray-100 dark:text-terminal-dim dark:hover:bg-terminal-surface-hover'}"
			>
				{label === 'ALL' ? 'All' : label === 'STRONG BUY' ? 'S.Buy' : label}
			</button>
		{/each}
	</div>

	<!-- Fundamental filter pills -->
	<div class="flex items-center gap-1 border-l border-gray-200 pl-2 dark:border-terminal-border">
		<span class="text-[9px] font-medium uppercase tracking-wider text-gray-400 dark:text-terminal-dim mr-0.5">Fund:</span>
		{#each fundFilterOptions as f}
			<button
				onclick={() => (fundFilter = f)}
				class="rounded-md px-1.5 py-0.5 text-[9px] font-semibold transition-all
					{fundFilter === f
						? f === 'spekulatif'
							? 'bg-red-600 text-white shadow-sm'
							: 'bg-blue-600 text-white shadow-sm'
						: 'text-gray-500 hover:bg-gray-100 dark:text-terminal-dim dark:hover:bg-terminal-surface-hover'}"
			>
				{fundFilterLabels[f]}
			</button>
		{/each}
	</div>

	<div class="flex-1"></div>

	<!-- Count + Export -->
	<span class="font-mono text-xs text-gray-400 dark:text-terminal-dim">
		{sorted.length}/{data.length}
	</span>
	<button
		onclick={exportCSV}
		class="flex items-center gap-1 rounded-lg border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-50 dark:border-terminal-border dark:text-terminal-muted dark:hover:bg-terminal-surface-hover"
	>
		<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
		</svg>
		CSV
	</button>
</div>

<!-- Table -->
<div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-terminal-border">
	<table class="w-full text-left text-sm">
		<thead>
			<tr class="border-b border-gray-200 bg-gray-50 dark:border-terminal-border dark:bg-terminal-surface">
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">#</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('ticker')}>
					Ticker{#if sortField === 'ticker'}<span class="ml-1 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('close')}>
					Harga{#if sortField === 'close'}<span class="ml-1 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('pct_change')}>
					Chg%{#if sortField === 'pct_change'}<span class="ml-1 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('quality')}>
					Score{#if sortField === 'quality'}<span class="ml-1 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Label</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-center text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Rules</th>
				{#if mode === 'swing'}
					<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Stage</th>
					<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Filter</th>
				{/if}
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Entry</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">SL</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">%SL</th>
				{#if mode !== 'swing'}
					<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">SL/ATR</th>
				{/if}
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">TP1</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-3 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">R:R</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-3 text-center text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim w-8"></th>
			</tr>
		</thead>
		<tbody>
			{#each sorted as stock, i}
				{@const e = stock.entry_data}
				{@const isSelected = selectedTicker === stock.ticker}
				{@const isRejected = !!stock.hard_reject}
				{@const isActionable = stock.q_label === 'BUY' || stock.q_label === 'STRONG BUY'}
				{@const fc = mode === 'swing' ? getSwingFilterChecks(stock) : null}
				<tr
					class="cursor-pointer border-b border-gray-100 transition-colors
						{isRejected
							? 'bg-red-50/50 opacity-60 dark:bg-red-900/5'
							: isSelected
								? 'border-l-2 border-l-blue-500 bg-blue-50/80 dark:bg-blue-900/15'
								: i % 2 === 0
									? 'bg-white dark:bg-terminal-bg'
									: 'bg-gray-50/50 dark:bg-terminal-surface/30'}
						hover:bg-blue-50 dark:border-gray-800 dark:hover:bg-terminal-surface-hover"
					onclick={() => handleSelect(stock)}
				>
					<td class="px-3 py-2.5 font-mono text-xs text-gray-400 dark:text-terminal-dim">{i + 1}</td>
					<td class="px-3 py-2.5 font-semibold text-gray-900 dark:text-terminal-text">
						<span class="flex items-center gap-1">
							{stock.ticker}
							{#if stock.is_smallcap}
								<span class="cursor-help text-sm" title="Small Cap — High Risk, Max 2% modal">🔥</span>
							{/if}
							{#if stock.fundamental}
								<span
									class="rounded px-1 py-px text-[8px] font-bold uppercase leading-tight {fundBadgeColors[stock.fundamental.fund_class] || fundBadgeColors.unknown}"
									title={stock.fundamental.fund_desc}
								>
									{stock.fundamental.fund_class === 'blue_chip' ? 'BC'
										: stock.fundamental.fund_class === 'mid_cap' ? 'MC'
										: stock.fundamental.fund_class === 'fundamental' ? 'FD'
										: stock.fundamental.fund_class === 'spekulatif' ? 'SP'
										: '??'}
								</span>
							{/if}
						</span>
					</td>
					<td class="px-3 py-2.5 text-right font-mono text-xs text-gray-700 dark:text-terminal-text">{fmt(stock.close)}</td>
					<td
						class="px-3 py-2.5 text-right font-mono text-xs font-semibold
							{isRejected
								? 'text-red-600 font-bold dark:text-red-400'
								: stock.pct_change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}"
					>
						{fmtPct(stock.pct_change)}
					</td>
					<td class="px-3 py-2.5">
						<ScoreGauge score={stock.quality} />
					</td>
					<td class="px-3 py-2.5">
						{#if isRejected}
							<span class="inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide bg-red-100 text-red-700 border border-red-200 dark:bg-red-500/15 dark:text-red-400 dark:border-red-500/30">
								REJECT
							</span>
						{:else}
							<span
								class="inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide {labelColors[stock.q_label] || ''}"
							>
								{stock.q_label === 'STRONG BUY' ? 'S.BUY' : stock.q_label}
							</span>
						{/if}
					</td>
					<td class="px-3 py-2.5 text-center font-mono text-xs text-gray-500 dark:text-terminal-muted">
						{#if isRejected}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{:else}
							{stock.rule_score}/{stock.max_rules}
						{/if}
					</td>
					{#if mode === 'swing'}
						<td class="px-3 py-2.5 text-xs">
							{#if stock.stage_label}
								<span
									class="rounded-md px-1.5 py-0.5 text-[10px] font-bold
										{stock.is_breakout
											? 'bg-green-500/15 text-green-400 border border-green-500/30'
											: 'bg-gray-500/10 text-gray-400 dark:text-terminal-muted'}"
								>
									{stock.stage_label}
								</span>
							{/if}
						</td>
						<td class="px-2 py-2.5">
							{#if fc}
								<div class="flex flex-wrap gap-0.5">
									{#each fc.checks as c}
										<span
											class="rounded px-1 py-px text-[8px] font-bold
												{c.pass
													? 'bg-green-500/15 text-green-600 dark:text-green-400'
													: 'bg-red-500/15 text-red-500 dark:text-red-400'}"
											title="{c.key}: {c.val}"
										>
											{c.pass ? '✓' : '✗'}{c.key}
										</span>
									{/each}
									{#if fc.layak}
										<span class="rounded bg-green-600 px-1 py-px text-[8px] font-bold text-white">LAYAK</span>
									{/if}
								</div>
							{/if}
						</td>
					{/if}
					<td class="px-3 py-2.5 text-right font-mono text-xs text-gray-600 dark:text-terminal-muted">
						{#if isRejected}
							<span class="text-[10px] italic text-red-500 dark:text-red-400">{stock.hard_reject}</span>
						{:else if isActionable && e}
							{fmt(e.entry_area_min ?? e.entry_low)}-{fmt(e.entry_area_max ?? e.entry_high)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-3 py-2.5 text-right font-mono text-xs text-gray-600 dark:text-terminal-muted">
						{#if isActionable && e}
							{fmt(e.sl)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-3 py-2.5 text-right font-mono text-xs font-semibold text-red-500 dark:text-red-400">
						{#if isActionable && e}
							{fmtPct(e.sl_pct)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					{#if mode !== 'swing'}
						<td class="px-3 py-2.5">
							{#if isActionable && e?.sl_ketat && e?.sl_vs_atr != null}
								<SLTightness level={e.sl_ketat} ratio={e.sl_vs_atr} />
							{:else}
								<span class="text-gray-300 dark:text-terminal-dim">-</span>
							{/if}
						</td>
					{/if}
					<td class="px-3 py-2.5 text-right font-mono text-xs font-semibold text-green-600 dark:text-green-400">
						{#if isActionable && e}
							{fmt(e.tp1)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-3 py-2.5 text-right font-mono text-xs text-gray-600 dark:text-terminal-muted">
						{#if isActionable && e}
							1:{e.rr1.toFixed(1)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-1 py-2.5 text-center">
						{#if isActionable && e}
						<button
							onclick={(ev) => copyRow(stock, ev)}
							class="rounded p-1 text-gray-300 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:text-terminal-dim dark:hover:bg-terminal-surface-hover dark:hover:text-terminal-text"
							title="Copy to clipboard"
							aria-label="Copy {stock.ticker} data"
						>
							{#if copiedTicker === stock.ticker}
								<svg class="h-3.5 w-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
							{:else}
								<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
								</svg>
							{/if}
						</button>
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

{#if data.length === 0}
	<div class="py-12 text-center">
		<svg class="mx-auto mb-3 h-10 w-10 text-gray-300 dark:text-terminal-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
		</svg>
		<p class="text-sm text-gray-400 dark:text-terminal-dim">Belum ada hasil. Klik "Start Scan" untuk memulai.</p>
	</div>
{/if}
