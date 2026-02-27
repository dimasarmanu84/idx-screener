<script lang="ts">
	import { streamScreener } from '$lib/api';
	import StockTable from '$lib/components/StockTable.svelte';
	import StockDetail from '$lib/components/StockDetail.svelte';
	import StockSelector from '$lib/components/StockSelector.svelte';
	import ScanProgress from '$lib/components/ScanProgress.svelte';
	import ModeGuide from '$lib/components/ModeGuide.svelte';
	import type { ScreeningResponse, StockResult, StockGroup } from '$lib/types';

	let stockGroup = $state<string>('jii');
	let scanning = $state(false);
	let progress = $state({ current: 0, total: 0, ticker: '' });
	let results = $state<ScreeningResponse | null>(null);
	let streamingResults = $state<StockResult[]>([]);
	let selectedStock = $state<StockResult | null>(null);
	let error = $state('');
	let cleanup = $state<(() => void) | null>(null);

	// Manual check
	let manualMode = $state(false);
	let manualInput = $state('');

	const groups: StockGroup[] = ['jii', 'jii70', 'issi'];

	let displayResults = $derived(results ? results.results : streamingResults);
	let buyCount = $derived(displayResults.filter((s) => s.q_label === 'STRONG BUY' || s.q_label === 'BUY').length);
	let watchCount = $derived(displayResults.filter((s) => s.q_label === 'WATCH').length);
	let skipCount = $derived(displayResults.filter((s) => s.q_label === 'SKIP').length);

	let stageStats = $derived.by(() => {
		if (displayResults.length === 0) return null;
		const stages: Record<string, number> = {};
		for (const s of displayResults) {
			const label = s.stage_label || 'Unknown';
			stages[label] = (stages[label] || 0) + 1;
		}
		return stages;
	});

	function startScan() {
		const tickers = manualMode
			? manualInput
					.toUpperCase()
					.split(/[,\s]+/)
					.map((t) => t.trim())
					.filter(Boolean)
					.join(',')
			: stockGroup;

		if (manualMode && !tickers) {
			error = 'Masukkan kode saham (contoh: BBCA, TLKM, ANTM)';
			return;
		}

		scanning = true;
		error = '';
		results = null;
		streamingResults = [];
		selectedStock = null;

		cleanup = streamScreener(
			'swing',
			tickers,
			(current, total, ticker) => {
				progress = { current, total, ticker };
			},
			(data) => {
				results = data;
				scanning = false;
			},
			(err) => {
				error = err;
				scanning = false;
			},
			undefined,
			(stock) => {
				streamingResults = [...streamingResults, stock].sort(
					(a, b) => b.quality - a.quality
				);
			}
		);
	}

	function stopScan() {
		cleanup?.();
		scanning = false;
	}

	function handleManualKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !scanning) startScan();
	}
</script>

<div class="py-3 md:py-8">
	<!-- Header -->
	<div class="mb-2 md:mb-4">
		<div class="flex items-center gap-2">
			<h1 class="text-lg font-extrabold tracking-tight text-gray-900 md:text-3xl dark:text-terminal-text">
				Swing Screener
			</h1>
			<ModeGuide mode="swing" />
		</div>
		<p class="hidden text-sm text-gray-500 md:mt-1 md:block dark:text-terminal-muted">
			Stage Analysis + Fibonacci + Chart Pattern — Saham Syariah (JII/JII70/ISSI)
		</p>
	</div>

	<!-- Mode toggle: Group / Manual -->
	<div class="mb-2 flex items-center gap-1 md:mb-4 md:gap-2">
		<button
			onclick={() => (manualMode = false)}
			class="rounded-md px-2 py-1 text-[11px] font-semibold transition-all md:rounded-lg md:px-3 md:py-1.5 md:text-xs
				{!manualMode
					? 'bg-purple-600 text-white shadow-sm shadow-purple-500/25'
					: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
		>
			Grup
		</button>
		<button
			onclick={() => (manualMode = true)}
			class="rounded-md px-2 py-1 text-[11px] font-semibold transition-all md:rounded-lg md:px-3 md:py-1.5 md:text-xs
				{manualMode
					? 'bg-purple-600 text-white shadow-sm shadow-purple-500/25'
					: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
		>
			Manual
		</button>
	</div>

	<!-- Controls -->
	<div class="mb-2 flex flex-wrap items-center gap-2 md:mb-5 md:gap-3">
		{#if manualMode}
			<div class="flex flex-1 items-center gap-2 sm:flex-none">
				<input
					type="text"
					bind:value={manualInput}
					onkeydown={handleManualKeydown}
					placeholder="BBCA, TLKM, ANTM ..."
					class="h-7 w-full rounded-md border border-gray-300 bg-white px-2 font-mono text-[11px] uppercase placeholder:normal-case placeholder:font-sans placeholder:text-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 md:h-10 md:rounded-lg md:px-3 md:text-sm dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim sm:w-72"
				/>
			</div>
		{:else}
			<StockSelector bind:value={stockGroup} {groups} />
		{/if}

		{#if scanning}
			<button
				onclick={stopScan}
				class="flex h-7 items-center gap-1 rounded-md bg-red-600 px-2.5 text-[11px] font-semibold text-white shadow-sm transition-all hover:bg-red-700 active:scale-[0.98] md:h-10 md:gap-2 md:rounded-lg md:px-5 md:text-sm"
			>
				<svg class="h-3 w-3 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
				</svg>
				Stop
			</button>
		{:else}
			<button
				onclick={startScan}
				class="flex h-7 items-center gap-1 rounded-md bg-purple-600 px-2.5 text-[11px] font-semibold text-white shadow-sm shadow-purple-500/25 transition-all hover:bg-purple-700 active:scale-[0.98] md:h-10 md:gap-2 md:rounded-lg md:px-5 md:text-sm"
			>
				<svg class="h-3 w-3 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				{manualMode ? 'Check' : 'Scan'}
			</button>
		{/if}
	</div>

	<!-- Error -->
	{#if error}
		<div class="mb-2 flex items-center gap-1.5 rounded-md border border-red-200 bg-red-50 px-2.5 py-1.5 text-[11px] text-red-700 md:mb-5 md:rounded-xl md:p-4 md:text-sm dark:border-red-500/20 dark:bg-red-900/10 dark:text-red-400">
			<svg class="h-3 w-3 shrink-0 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			{error}
		</div>
	{/if}

	<!-- Progress -->
	{#if scanning}
		<ScanProgress current={progress.current} total={progress.total} ticker={progress.ticker} />
	{/if}

	<!-- Results (show during scanning + after complete) -->
	{#if displayResults.length > 0 || results}
		<!-- Stats cards -->
		<div class="mb-2 grid grid-cols-4 gap-1.5 md:mb-5 md:gap-3">
			<div class="rounded-md border border-gray-200 bg-white px-2 py-1.5 md:rounded-xl md:p-3 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-gray-400 md:text-[10px] dark:text-terminal-dim">Scan</div>
				<div class="font-mono text-base font-bold text-gray-900 md:mt-1 md:text-2xl dark:text-terminal-text">{results ? results.total_scanned : progress.current}<span class="text-[9px] font-normal text-gray-400 md:text-xs">{scanning ? `/${progress.total}` : ''}</span></div>
			</div>
			<div class="rounded-md border border-green-200 bg-green-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-green-500/20 dark:bg-green-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-green-600 md:text-[10px] dark:text-green-400">BUY</div>
				<div class="font-mono text-base font-bold text-green-700 md:mt-1 md:text-2xl dark:text-green-400">{results ? results.strong.length : buyCount}</div>
			</div>
			<div class="rounded-md border border-yellow-200 bg-yellow-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-yellow-500/20 dark:bg-yellow-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-yellow-600 md:text-[10px] dark:text-yellow-400">Watch</div>
				<div class="font-mono text-base font-bold text-yellow-700 md:mt-1 md:text-2xl dark:text-yellow-400">{results ? results.watch.length : watchCount}</div>
			</div>
			<div class="rounded-md border border-gray-200 bg-white px-2 py-1.5 md:rounded-xl md:p-3 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-gray-400 md:text-[10px] dark:text-terminal-dim">Skip</div>
				<div class="font-mono text-base font-bold text-gray-400 md:mt-1 md:text-2xl dark:text-terminal-dim">{skipCount}</div>
				{#if results && results.total_errors > 0}
					<div class="text-[9px] text-red-500">{results.total_errors} err</div>
				{/if}
			</div>
		</div>

		<!-- Stage breakdown -->
		{#if stageStats}
			<div class="mb-2 flex flex-wrap gap-1 md:mb-4 md:gap-1.5">
				{#each Object.entries(stageStats) as [stage, count]}
					<span class="rounded-md bg-gray-100 px-1.5 py-0.5 font-mono text-[9px] font-semibold text-gray-600 md:rounded-lg md:px-2.5 md:py-1 md:text-[10px] dark:bg-terminal-surface dark:text-terminal-muted">
						{stage}: <span class="text-gray-900 dark:text-terminal-text">{count}</span>
					</span>
				{/each}
			</div>
		{/if}

		<StockTable
			data={displayResults}
			mode="swing"
			onselect={(stock) => (selectedStock = stock)}
		/>
	{/if}

	<!-- Detail panel -->
	{#if selectedStock}
		<StockDetail stock={selectedStock} mode="swing" onclose={() => (selectedStock = null)} />
	{/if}
</div>
