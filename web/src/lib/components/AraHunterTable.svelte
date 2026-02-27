<script lang="ts">
	import type { StockResult } from '$lib/types';

	let {
		data,
		onselect
	}: {
		data: StockResult[];
		onselect: (stock: StockResult) => void;
	} = $props();

	let sortField = $state('ara_score');
	let sortDir = $state<'asc' | 'desc'>('desc');
	let search = $state('');
	let labelFilter = $state('ALL');
	let selectedTicker = $state('');

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
			if (labelFilter === 'TOP 2') {
				// Step 1-2: HOT/WARM + semua filter criteria pass
				if (s.ara_label !== 'HOT' && s.ara_label !== 'WARM') return false;
				return getFilterChecks(s).layak;
			}
			if (labelFilter !== 'ALL' && s.ara_label !== labelFilter) return false;
			return true;
		})
	);

	let sorted = $derived.by(() => {
		if (labelFilter === 'TOP 2') {
			// Step 3: Sort by R:R tertinggi → ambil top 2
			return [...filtered]
				.sort((a, b) => (b.entry_data?.rr1 ?? 0) - (a.entry_data?.rr1 ?? 0))
				.slice(0, 2);
		}
		return [...filtered].sort((a, b) => {
			const va = (a as any)[sortField] as number;
			const vb = (b as any)[sortField] as number;
			if (va == null && vb == null) return 0;
			if (va == null) return 1;
			if (vb == null) return -1;
			return sortDir === 'desc' ? vb - va : va - vb;
		});
	});

	function fmt(n: number | undefined | null): string {
		if (n == null) return '-';
		return n.toLocaleString('id-ID', { maximumFractionDigits: 0 });
	}

	function fmtPct(n: number | undefined | null): string {
		if (n == null) return '-';
		return (n >= 0 ? '+' : '') + n.toFixed(1) + '%';
	}

	const labelColors: Record<string, string> = {
		HOT: 'bg-red-100 text-red-700 border border-red-200 dark:bg-red-500/15 dark:text-red-400 dark:border-red-500/30',
		WARM: 'bg-orange-100 text-orange-700 border border-orange-200 dark:bg-orange-500/15 dark:text-orange-400 dark:border-orange-500/30',
		WATCH: 'bg-yellow-100 text-yellow-700 border border-yellow-200 dark:bg-yellow-500/15 dark:text-yellow-400 dark:border-yellow-500/30'
	};

	const rekomColors: Record<string, string> = {
		ENTRY: 'bg-green-600 text-white dark:bg-green-500',
		WAIT: 'bg-yellow-500 text-white dark:bg-yellow-500',
		SKIP: 'bg-gray-300 text-gray-600 dark:bg-gray-600 dark:text-gray-300'
	};

	const filterLabels = ['ALL', 'TOP 2', 'HOT', 'WARM', 'WATCH'];

	// Step 2 filter checks — visual labels per stock
	function getFilterChecks(stock: StockResult) {
		const e = stock.entry_data;
		const rr = e?.rr1 ?? 0;
		const slPct = Math.abs(e?.sl_pct ?? 0);
		const dist = stock.dist_to_ara_pct ?? 0;
		const chg = stock.pct_change ?? 0;

		const checks = [
			{ key: 'R:R', pass: rr >= 1.5, val: `1:${rr.toFixed(1)}` },
			{ key: 'SL', pass: slPct <= 8, val: `${slPct.toFixed(0)}%` },
			{ key: 'Jarak', pass: dist >= 10, val: `${dist.toFixed(0)}%` },
			{ key: 'CHG', pass: chg <= 15, val: `${chg.toFixed(0)}%` }
		];
		const passCount = checks.filter((c) => c.pass).length;
		return { checks, passCount, layak: passCount === 4 };
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
		if (e) {
			const entryMin = e.entry_area_min ?? e.entry_low;
			const entryMax = e.entry_area_max ?? e.entry_high;
			text = `${stock.ticker} | ARA Score: ${stock.ara_score} | CHG: ${fmtPct(stock.pct_change)} | Vol: ${(stock.volume_info?.volume_ratio ?? 0).toFixed(1)}x | Jarak ARA: ${fmtPct(stock.dist_to_ara_pct)} | Entry: ${fmt(entryMin)}-${fmt(entryMax)} | SL: ${fmt(e.sl)} (${fmtPct(e.sl_pct)}) | R:R 1:${e.rr1.toFixed(1)}`;
		} else {
			text = `${stock.ticker} | ARA Score: ${stock.ara_score} | CHG: ${fmtPct(stock.pct_change)} | Jarak ARA: ${fmtPct(stock.dist_to_ara_pct)}`;
		}
		navigator.clipboard.writeText(text);
		copiedTicker = stock.ticker;
		setTimeout(() => { if (copiedTicker === stock.ticker) copiedTicker = ''; }, 1500);
	}

	function exportCSV() {
		const headers = ['Ticker', 'Harga', 'Chg%', 'Vol Ratio', 'ARA Score', 'Label', 'Jarak ARA%', 'Batas ARA', 'Entry', 'SL', '%SL', 'TP1', 'R:R'];
		const rows = sorted.map((s) => {
			const e = s.entry_data;
			return [
				s.ticker,
				s.close,
				s.pct_change?.toFixed(1),
				(s.volume_info?.volume_ratio ?? 0).toFixed(1),
				s.ara_score ?? 0,
				s.ara_label ?? '',
				s.dist_to_ara_pct?.toFixed(1) ?? '',
				s.ara_limit ?? '',
				e ? `${e.entry_area_min ?? e.entry_low}-${e.entry_area_max ?? e.entry_high}` : '',
				e?.sl ?? '',
				e ? e.sl_pct?.toFixed(1) + '%' : '',
				e?.tp1 ?? '',
				e ? '1:' + e.rr1?.toFixed(1) : ''
			].join(',');
		});
		const csv = [headers.join(','), ...rows].join('\n');
		const blob = new Blob([csv], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `ara_hunter_${new Date().toISOString().slice(0, 10)}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<!-- Toolbar -->
<div class="mb-2 flex items-center gap-1.5 md:mb-3 md:gap-2">
	<div class="relative">
		<svg class="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-gray-400 dark:text-terminal-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
		</svg>
		<input
			type="text"
			bind:value={search}
			placeholder="Cari..."
			class="h-7 w-24 rounded-md border border-gray-200 bg-white pl-7 pr-2 text-[11px] text-gray-700 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:w-36 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder-terminal-dim"
		/>
	</div>

	<div class="flex gap-0.5">
		{#each filterLabels as label}
			<button
				onclick={() => (labelFilter = label)}
				class="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider transition-all md:px-2 md:py-1 md:text-[10px]
					{labelFilter === label
						? label === 'TOP 2'
							? 'bg-green-600 text-white shadow-sm'
							: 'bg-blue-600 text-white shadow-sm'
						: label === 'TOP 2'
							? 'text-green-600 ring-1 ring-green-300 hover:bg-green-50 dark:text-green-400 dark:ring-green-500/30 dark:hover:bg-green-900/20'
							: 'text-gray-500 hover:bg-gray-100 dark:text-terminal-dim dark:hover:bg-terminal-surface-hover'}"
			>
				{label === 'ALL' ? 'All' : label}
			</button>
		{/each}
	</div>

	<div class="flex-1"></div>

	<span class="font-mono text-[10px] text-gray-400 dark:text-terminal-dim">
		{sorted.length}/{data.length}
	</span>
	<button
		onclick={exportCSV}
		class="flex items-center gap-0.5 rounded-md border border-gray-200 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 transition-colors hover:bg-gray-50 dark:border-terminal-border dark:text-terminal-muted dark:hover:bg-terminal-surface-hover"
		title="Export CSV"
	>
		<svg class="h-2.5 w-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
		</svg>
		CSV
	</button>
</div>

<!-- ========== MOBILE: Card Layout ========== -->
<div class="flex flex-col gap-1.5 md:hidden">
	{#each sorted as stock, i}
		{@const e = stock.entry_data}
		{@const isSelected = selectedTicker === stock.ticker}
		{@const volRatio = stock.volume_info?.volume_ratio ?? 0}
		{@const araScore = stock.ara_score ?? 0}
		{@const fc = getFilterChecks(stock)}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="w-full cursor-pointer rounded-lg border px-2.5 py-2 text-left transition-all active:scale-[0.99]
				{isSelected
					? 'border-blue-400 bg-blue-50/80 dark:border-blue-500/40 dark:bg-blue-900/15'
					: 'border-gray-200 bg-white dark:border-terminal-border dark:bg-terminal-surface'}"
			onclick={() => handleSelect(stock)}
			role="button"
			tabindex="0"
			onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleSelect(stock); }}
		>
			<!-- Row 1: Ticker + Label + Rekom + Score + Copy -->
			<div class="flex items-center gap-1.5">
				<span class="font-mono text-[9px] text-gray-400 dark:text-terminal-dim">{i + 1}</span>
				<span class="text-xs font-bold text-gray-900 dark:text-terminal-text">{stock.ticker}</span>
				{#if stock.is_smallcap}<span class="text-[10px]" title="Small Cap">🔥</span>{/if}
				{#if stock.fundamental}
					{@const fc = stock.fundamental.fund_class}
					<span
						class="rounded px-1 py-px text-[7px] font-bold uppercase leading-tight
							{fc === 'blue_chip' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400'
							: fc === 'mid_cap' ? 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400'
							: fc === 'fundamental' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400'
							: fc === 'spekulatif' ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400'
							: 'bg-gray-100 text-gray-500 dark:bg-gray-500/15 dark:text-gray-400'}"
						title={stock.fundamental.fund_desc}
					>
						{fc === 'blue_chip' ? 'BC' : fc === 'mid_cap' ? 'MC' : fc === 'fundamental' ? 'FD' : fc === 'spekulatif' ? 'SP' : '??'}
					</span>
				{/if}
				<span class="rounded px-1 py-px text-[8px] font-bold uppercase leading-tight {labelColors[stock.ara_label ?? 'WATCH'] || ''}">
					{stock.ara_label ?? '-'}
				</span>
				<span class="rounded px-1 py-px text-[7px] font-bold uppercase leading-tight {rekomColors[stock.ara_rekom ?? 'SKIP'] || rekomColors['SKIP']}">
					{stock.ara_rekom ?? 'SKIP'}
				</span>
				<div class="flex-1"></div>
				<div class="flex items-center gap-0.5">
					<div class="h-1 w-6 overflow-hidden rounded-full bg-gray-200 dark:bg-terminal-border">
						<div
							class="h-1 rounded-full {araScore >= 70 ? 'bg-red-500' : araScore >= 40 ? 'bg-orange-500' : 'bg-yellow-500'}"
							style="width: {araScore}%"
						></div>
					</div>
					<span class="font-mono text-[10px] font-bold {araScore >= 70 ? 'text-red-500' : araScore >= 40 ? 'text-orange-500 dark:text-orange-400' : 'text-yellow-600 dark:text-yellow-400'}">
						{araScore}
					</span>
				</div>
				<button
					onclick={(ev) => copyRow(stock, ev)}
					class="-mr-1 rounded p-0.5 text-gray-300 transition-colors hover:text-gray-600 dark:text-terminal-dim dark:hover:text-terminal-text"
					title="Copy"
				>
					{#if copiedTicker === stock.ticker}
						<svg class="h-3 w-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					{:else}
						<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
						</svg>
					{/if}
				</button>
			</div>

			<!-- Row 2: Metrics inline -->
			<div class="mt-1 flex items-baseline gap-3 text-[10px]">
				<span class="font-mono font-medium text-gray-700 dark:text-terminal-text">{fmt(stock.close)}</span>
				<span class="font-mono font-bold text-green-600 dark:text-green-400">{fmtPct(stock.pct_change)}</span>
				<span class="font-mono font-bold {volRatio >= 3 ? 'text-red-500' : volRatio >= 2 ? 'text-orange-500 dark:text-orange-400' : 'text-yellow-600 dark:text-yellow-400'}">{volRatio.toFixed(1)}x</span>
				<span class="font-mono font-semibold {(stock.dist_to_ara_pct ?? 0) <= 5 ? 'text-red-500' : (stock.dist_to_ara_pct ?? 0) <= 10 ? 'text-orange-500 dark:text-orange-400' : 'text-green-600 dark:text-green-400'}">ARA {fmtPct(stock.dist_to_ara_pct)}</span>
			</div>

			<!-- Row 2.5: Filter checks -->
			<div class="mt-1 flex items-center gap-1">
				{#if fc.layak}
					<span class="rounded bg-green-600 px-1 py-px text-[7px] font-bold text-white">LAYAK</span>
				{/if}
				{#each fc.checks as c}
					<span class="rounded px-1 py-px text-[7px] font-semibold {c.pass ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-500 dark:bg-red-900/30 dark:text-red-400'}">
						{c.pass ? '✓' : '✗'}{c.key}
					</span>
				{/each}
			</div>

			<!-- Row 3: Entry / SL / R:R -->
			{#if e}
				<div class="mt-1 flex items-baseline gap-2 text-[10px]">
					<span class="text-gray-400 dark:text-terminal-dim">E</span>
					<span class="font-mono text-gray-600 dark:text-terminal-muted">{fmt(e.entry_area_min ?? e.entry_low)}-{fmt(e.entry_area_max ?? e.entry_high)}</span>
					<span class="text-red-400">SL</span>
					<span class="font-mono text-red-500">{fmt(e.sl)} <span class="opacity-60">({fmtPct(e.sl_pct)})</span></span>
					<span class="font-mono font-semibold text-gray-500 dark:text-terminal-muted">1:{e.rr1.toFixed(1)}</span>
				</div>
			{/if}
		</div>
	{/each}
</div>

<!-- ========== DESKTOP: Table Layout ========== -->
<div class="hidden overflow-x-auto rounded-lg border border-gray-200 md:block dark:border-terminal-border">
	<table class="w-full text-left text-xs">
		<thead>
			<tr class="border-b border-gray-200 bg-gray-50 dark:border-terminal-border dark:bg-terminal-surface">
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">#</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-2 py-2 text-[9px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('ticker')}>
					Ticker{#if sortField === 'ticker'}<span class="ml-0.5 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('close')}>
					Harga{#if sortField === 'close'}<span class="ml-0.5 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('pct_change')}>
					CHG%{#if sortField === 'pct_change'}<span class="ml-0.5 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('volume_ratio')}>
					Vol{#if sortField === 'volume_ratio'}<span class="ml-0.5 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-2 py-2 text-[9px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('ara_score')}>
					Score{#if sortField === 'ara_score'}<span class="ml-0.5 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Label</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Rekom</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Filter</th>
				<th class="sticky top-0 z-10 cursor-pointer bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:text-gray-900 dark:bg-terminal-surface dark:text-terminal-dim dark:hover:text-terminal-text" onclick={() => toggleSort('dist_to_ara_pct')}>
					Jarak{#if sortField === 'dist_to_ara_pct'}<span class="ml-0.5 text-blue-500">{sortDir === 'desc' ? '▼' : '▲'}</span>{/if}
				</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">Entry</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">SL</th>
				<th class="sticky top-0 z-10 bg-gray-50 px-2 py-2 text-right text-[9px] font-semibold uppercase tracking-wider text-gray-500 dark:bg-terminal-surface dark:text-terminal-dim">R:R</th>
				<th class="sticky top-0 z-10 w-6 bg-gray-50 px-1 py-2 dark:bg-terminal-surface"></th>
			</tr>
		</thead>
		<tbody>
			{#each sorted as stock, i}
				{@const e = stock.entry_data}
				{@const isSelected = selectedTicker === stock.ticker}
				{@const volRatio = stock.volume_info?.volume_ratio ?? 0}
				{@const araScore = stock.ara_score ?? 0}
				{@const fc = getFilterChecks(stock)}
				<tr
					class="cursor-pointer border-b border-gray-100 transition-colors
						{isSelected
							? 'border-l-2 border-l-blue-500 bg-blue-50/80 dark:bg-blue-900/15'
							: i % 2 === 0
								? 'bg-white dark:bg-terminal-bg'
								: 'bg-gray-50/50 dark:bg-terminal-surface/30'}
						hover:bg-blue-50 dark:border-gray-800 dark:hover:bg-terminal-surface-hover"
					onclick={() => handleSelect(stock)}
				>
					<td class="px-2 py-1.5 font-mono text-[10px] text-gray-400 dark:text-terminal-dim">{i + 1}</td>
					<td class="px-2 py-1.5 text-xs font-semibold text-gray-900 dark:text-terminal-text">
						<span class="flex items-center gap-0.5">
							{stock.ticker}
							{#if stock.is_smallcap}<span class="cursor-help text-[10px]" title="Small Cap">🔥</span>{/if}
							{#if stock.fundamental}
								{@const fclass = stock.fundamental.fund_class}
								<span
									class="rounded px-0.5 py-px text-[7px] font-bold uppercase leading-tight
										{fclass === 'blue_chip' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400'
										: fclass === 'mid_cap' ? 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400'
										: fclass === 'fundamental' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400'
										: fclass === 'spekulatif' ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400'
										: 'bg-gray-100 text-gray-500 dark:bg-gray-500/15 dark:text-gray-400'}"
									title={stock.fundamental.fund_desc}
								>
									{fclass === 'blue_chip' ? 'BC' : fclass === 'mid_cap' ? 'MC' : fclass === 'fundamental' ? 'FD' : fclass === 'spekulatif' ? 'SP' : '??'}
								</span>
							{/if}
						</span>
					</td>
					<td class="px-2 py-1.5 text-right font-mono text-[11px] text-gray-700 dark:text-terminal-text">{fmt(stock.close)}</td>
					<td class="px-2 py-1.5 text-right font-mono text-[11px] font-bold text-green-600 dark:text-green-400">
						{fmtPct(stock.pct_change)}
					</td>
					<td class="px-2 py-1.5 text-right">
						<div class="flex items-center justify-end gap-1">
							<div class="h-1 w-8 overflow-hidden rounded-full bg-gray-200 dark:bg-terminal-border">
								<div
									class="h-1 rounded-full {volRatio >= 3 ? 'bg-red-500' : volRatio >= 2 ? 'bg-orange-500' : 'bg-yellow-500'}"
									style="width: {Math.min(volRatio / 5 * 100, 100)}%"
								></div>
							</div>
							<span class="font-mono text-[11px] font-bold {volRatio >= 3 ? 'text-red-500' : volRatio >= 2 ? 'text-orange-500 dark:text-orange-400' : 'text-yellow-600 dark:text-yellow-400'}">
								{volRatio.toFixed(1)}x
							</span>
						</div>
					</td>
					<td class="px-2 py-1.5">
						<div class="flex items-center gap-1.5">
							<div class="h-1 w-10 overflow-hidden rounded-full bg-gray-200 dark:bg-terminal-border">
								<div
									class="h-1 rounded-full {araScore >= 70 ? 'bg-red-500' : araScore >= 40 ? 'bg-orange-500' : 'bg-yellow-500'}"
									style="width: {araScore}%"
								></div>
							</div>
							<span class="font-mono text-[11px] font-bold {araScore >= 70 ? 'text-red-500' : araScore >= 40 ? 'text-orange-500 dark:text-orange-400' : 'text-yellow-600 dark:text-yellow-400'}">
								{araScore}
							</span>
						</div>
					</td>
					<td class="px-2 py-1.5">
						<span class="inline-block rounded px-1.5 py-px text-[9px] font-bold uppercase {labelColors[stock.ara_label ?? 'WATCH'] || ''}">
							{stock.ara_label ?? '-'}
						</span>
					</td>
					<td class="px-2 py-1.5">
						<span class="inline-block rounded px-1.5 py-px text-[9px] font-bold uppercase {rekomColors[stock.ara_rekom ?? 'SKIP'] || rekomColors['SKIP']}">
							{stock.ara_rekom ?? 'SKIP'}
						</span>
					</td>
					<td class="px-2 py-1.5">
						<div class="flex items-center gap-0.5">
							{#if fc.layak}
								<span class="rounded bg-green-600 px-1 py-px text-[8px] font-bold text-white">LAYAK</span>
							{:else}
								{#each fc.checks as c}
									{#if !c.pass}
										<span class="rounded bg-red-100 px-1 py-px text-[8px] font-semibold text-red-500 dark:bg-red-900/30 dark:text-red-400" title="{c.key}: {c.val}">
											✗{c.key}
										</span>
									{/if}
								{/each}
							{/if}
						</div>
					</td>
					<td class="px-2 py-1.5 text-right font-mono text-[11px] font-semibold {(stock.dist_to_ara_pct ?? 0) <= 5 ? 'text-red-500' : (stock.dist_to_ara_pct ?? 0) <= 10 ? 'text-orange-500 dark:text-orange-400' : 'text-green-600 dark:text-green-400'}">
						{fmtPct(stock.dist_to_ara_pct)}
					</td>
					<td class="px-2 py-1.5 text-right font-mono text-[11px] text-gray-600 dark:text-terminal-muted">
						{#if e}
							{fmt(e.entry_area_min ?? e.entry_low)}-{fmt(e.entry_area_max ?? e.entry_high)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-2 py-1.5 text-right font-mono text-[11px] text-red-500">
						{#if e}
							{fmt(e.sl)} <span class="text-[9px] opacity-70">({fmtPct(e.sl_pct)})</span>
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-2 py-1.5 text-right font-mono text-[11px] text-gray-600 dark:text-terminal-muted">
						{#if e}
							1:{e.rr1.toFixed(1)}
						{:else}
							<span class="text-gray-300 dark:text-terminal-dim">-</span>
						{/if}
					</td>
					<td class="px-0.5 py-1.5 text-center">
						<button
							onclick={(ev) => copyRow(stock, ev)}
							class="rounded p-0.5 text-gray-300 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:text-terminal-dim dark:hover:bg-terminal-surface-hover dark:hover:text-terminal-text"
							title="Copy"
							aria-label="Copy {stock.ticker} data"
						>
							{#if copiedTicker === stock.ticker}
								<svg class="h-3 w-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
							{:else}
								<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
								</svg>
							{/if}
						</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

{#if data.length === 0}
	<div class="py-8 text-center">
		<svg class="mx-auto mb-2 h-8 w-8 text-gray-300 dark:text-terminal-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
		</svg>
		<p class="text-xs text-gray-400 dark:text-terminal-dim">Tidak ada saham yang memenuhi kriteria ARA potential.</p>
	</div>
{/if}
