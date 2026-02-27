<script lang="ts">
	import { streamNightScanner } from '$lib/api';
	import NightScannerTable from '$lib/components/NightScannerTable.svelte';
	import StockDetail from '$lib/components/StockDetail.svelte';
	import StockSelector from '$lib/components/StockSelector.svelte';
	import ScanProgress from '$lib/components/ScanProgress.svelte';
	import ModeGuide from '$lib/components/ModeGuide.svelte';
	import type { ScreeningResponse, StockResult, StockGroup } from '$lib/types';

	let stockGroup = $state<string>('all_stocks');
	let scanning = $state(false);
	let progress = $state({ current: 0, total: 0, ticker: '' });
	let results = $state<ScreeningResponse | null>(null);
	let streamingResults = $state<StockResult[]>([]);
	let selectedStock = $state<StockResult | null>(null);
	let error = $state('');
	let cleanup = $state<(() => void) | null>(null);

	let manualMode = $state(false);
	let manualInput = $state('');

	const groups: StockGroup[] = ['lq45', 'idx80', 'all_idx', 'all_stocks', 'all_bursa'];

	// Use streaming results during scan, final results after complete
	let displayResults = $derived(results ? results.results : streamingResults);
	let primeCount = $derived(displayResults.filter(s => s.night_label === 'PRIME').length);
	let readyCount = $derived(displayResults.filter(s => s.night_label === 'READY').length);

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
			error = 'Masukkan kode saham (contoh: BBCA, TLKM, BMRI)';
			return;
		}

		scanning = true;
		error = '';
		results = null;
		streamingResults = [];
		selectedStock = null;

		cleanup = streamNightScanner(
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
			(stock) => {
				streamingResults = [...streamingResults, stock].sort(
					(a, b) => (b.night_score ?? 0) - (a.night_score ?? 0)
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
	<!-- Header + Controls inline -->
	<div class="mb-2 flex flex-wrap items-center gap-2 md:mb-4 md:flex-col md:items-start md:gap-0">
		<div class="flex items-center gap-2">
			<h1 class="text-lg font-extrabold tracking-tight text-gray-900 md:text-3xl dark:text-terminal-text">
				Night Scanner
			</h1>
			<ModeGuide mode="night-scanner" />
		</div>
		<p class="hidden text-sm text-gray-500 md:mt-1 md:block dark:text-terminal-muted">
			Prediksi saham potensial naik besok — scan setelah market tutup
		</p>
	</div>

	<!-- Warning -->
	<div class="mb-2 flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-2.5 py-1.5 md:mb-4 md:rounded-xl md:border-2 md:p-4 dark:border-indigo-500/20 dark:bg-indigo-900/10">
		<svg class="h-3.5 w-3.5 shrink-0 text-indigo-500 md:h-5 md:w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
		</svg>
		<span class="text-[10px] font-semibold text-indigo-700 md:text-sm dark:text-indigo-400">WATCHLIST ONLY</span>
		<span class="hidden text-xs text-indigo-600 md:inline dark:text-indigo-400/80">— Konfirmasi entry besok pagi. Bukan sinyal beli langsung!</span>
	</div>

	<!-- Mode toggle -->
	<div class="mb-2 flex items-center gap-1 md:mb-3">
		<button
			onclick={() => (manualMode = false)}
			class="rounded-md px-2 py-1 text-[11px] font-semibold transition-all md:rounded-lg md:px-3 md:py-1.5 md:text-xs
				{!manualMode
					? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/25'
					: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
		>
			Grup
		</button>
		<button
			onclick={() => (manualMode = true)}
			class="rounded-md px-2 py-1 text-[11px] font-semibold transition-all md:rounded-lg md:px-3 md:py-1.5 md:text-xs
				{manualMode
					? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/25'
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
					placeholder="BBCA, TLKM, BMRI ..."
					class="h-7 w-full rounded-md border border-gray-300 bg-white px-2 font-mono text-[11px] uppercase placeholder:normal-case placeholder:font-sans placeholder:text-gray-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 md:h-10 md:rounded-lg md:px-3 md:text-sm dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim sm:w-72"
				/>
			</div>
		{:else}
			<StockSelector bind:value={stockGroup} groups={groups} />
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
				class="flex h-7 items-center gap-1 rounded-md bg-indigo-600 px-2.5 text-[11px] font-semibold text-white shadow-sm shadow-indigo-500/25 transition-all hover:bg-indigo-700 active:scale-[0.98] md:h-10 md:gap-2 md:rounded-lg md:px-5 md:text-sm"
			>
				<svg class="h-3 w-3 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
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
			<div class="rounded-md border border-indigo-200 bg-indigo-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-indigo-500/20 dark:bg-indigo-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-indigo-600 md:text-[10px] dark:text-indigo-400">Found</div>
				<div class="font-mono text-base font-bold text-indigo-700 md:mt-1 md:text-2xl dark:text-indigo-400">{displayResults.length}{#if results}<span class="text-[9px] font-normal text-indigo-500 md:text-xs">/{results.total_passed}</span>{/if}</div>
			</div>
			<div class="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-emerald-500/20 dark:bg-emerald-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-emerald-600 md:text-[10px] dark:text-emerald-400">Prime</div>
				<div class="font-mono text-base font-bold text-emerald-700 md:mt-1 md:text-2xl dark:text-emerald-400">{primeCount}</div>
			</div>
			<div class="rounded-md border border-blue-200 bg-blue-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-blue-500/20 dark:bg-blue-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-blue-600 md:text-[10px] dark:text-blue-400">Ready</div>
				<div class="font-mono text-base font-bold text-blue-700 md:mt-1 md:text-2xl dark:text-blue-400">{readyCount}</div>
			</div>
		</div>

		<NightScannerTable
			data={displayResults}
			onselect={(stock) => (selectedStock = stock)}
		/>
	{/if}

	<!-- Detail panel -->
	{#if selectedStock}
		<StockDetail stock={selectedStock} mode="intraday" onclose={() => (selectedStock = null)} />
	{/if}
</div>
