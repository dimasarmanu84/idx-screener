<script lang="ts">
	import { streamAraHunter } from '$lib/api';
	import AraHunterTable from '$lib/components/AraHunterTable.svelte';
	import StockDetail from '$lib/components/StockDetail.svelte';
	import StockSelector from '$lib/components/StockSelector.svelte';
	import ScanProgress from '$lib/components/ScanProgress.svelte';
	import ModeGuide from '$lib/components/ModeGuide.svelte';
	import type { ScreeningResponse, StockResult, StockGroup } from '$lib/types';

	let stockGroup = $state<string>('all_bursa');
	let scanning = $state(false);
	let progress = $state({ current: 0, total: 0, ticker: '' });
	let results = $state<ScreeningResponse | null>(null);
	let selectedStock = $state<StockResult | null>(null);
	let error = $state('');
	let cleanup = $state<(() => void) | null>(null);

	let manualMode = $state(false);
	let manualInput = $state('');

	const groups: StockGroup[] = ['lq45', 'idx80', 'all_idx', 'all_stocks', 'all_bursa', 'jii', 'jii70', 'issi'];

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
			error = 'Masukkan kode saham (contoh: TOSK, YELO, IKAN)';
			return;
		}

		scanning = true;
		error = '';
		results = null;
		selectedStock = null;

		cleanup = streamAraHunter(
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

	let hotCount = $derived(results ? results.results.filter(s => s.ara_label === 'HOT').length : 0);
	let warmCount = $derived(results ? results.results.filter(s => s.ara_label === 'WARM').length : 0);
	let entryCount = $derived(results ? results.results.filter(s => s.ara_rekom === 'ENTRY').length : 0);
</script>

<div class="py-3 md:py-8">
	<!-- Header + Controls inline -->
	<div class="mb-2 flex flex-wrap items-center gap-2 md:mb-4 md:flex-col md:items-start md:gap-0">
		<div class="flex items-center gap-2">
			<h1 class="text-lg font-extrabold tracking-tight text-gray-900 md:text-3xl dark:text-terminal-text">
				Top Gainer
			</h1>
			<ModeGuide mode="top-gainer" />
		</div>
		<p class="hidden text-sm text-gray-500 md:mt-1 md:block dark:text-terminal-muted">
			Cari saham naik tertinggi hari ini — tangkap momentum sebelum terlambat
		</p>
	</div>

	<!-- Warning + Controls row -->
	<div class="mb-2 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 md:mb-4 md:rounded-xl md:border-2 md:p-4 dark:border-red-500/20 dark:bg-red-900/10">
		<svg class="h-3.5 w-3.5 shrink-0 text-red-500 md:h-5 md:w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
		</svg>
		<span class="text-[10px] font-semibold text-red-700 md:text-sm dark:text-red-400">HIGH RISK</span>
		<span class="hidden text-xs text-red-600 md:inline dark:text-red-400/80">— Bisa langsung ARB besok. SL ketat, max 2% modal. Jangan FOMO!</span>
	</div>

	<!-- Mode toggle -->
	<div class="mb-2 flex items-center gap-1 md:mb-3">
		<button
			onclick={() => (manualMode = false)}
			class="rounded-md px-2 py-1 text-[11px] font-semibold transition-all md:rounded-lg md:px-3 md:py-1.5 md:text-xs
				{!manualMode
					? 'bg-red-600 text-white shadow-sm shadow-red-500/25'
					: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
		>
			Grup
		</button>
		<button
			onclick={() => (manualMode = true)}
			class="rounded-md px-2 py-1 text-[11px] font-semibold transition-all md:rounded-lg md:px-3 md:py-1.5 md:text-xs
				{manualMode
					? 'bg-red-600 text-white shadow-sm shadow-red-500/25'
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
					placeholder="TOSK, YELO, IKAN ..."
					class="h-7 w-full rounded-md border border-gray-300 bg-white px-2 font-mono text-[11px] uppercase placeholder:normal-case placeholder:font-sans placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500 md:h-10 md:rounded-lg md:px-3 md:text-sm dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim sm:w-72"
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
				class="flex h-7 items-center gap-1 rounded-md bg-red-600 px-2.5 text-[11px] font-semibold text-white shadow-sm shadow-red-500/25 transition-all hover:bg-red-700 active:scale-[0.98] md:h-10 md:gap-2 md:rounded-lg md:px-5 md:text-sm"
			>
				<svg class="h-3 w-3 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					{#if manualMode}
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					{:else}
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
					{/if}
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

	<!-- Results -->
	{#if results}
		<!-- Stats cards — single row, ultra compact on mobile -->
		<div class="mb-2 grid grid-cols-4 gap-1.5 md:mb-5 md:gap-3">
			<div class="rounded-md border border-gray-200 bg-white px-2 py-1.5 md:rounded-xl md:p-3 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-gray-400 md:text-[10px] dark:text-terminal-dim">Scan</div>
				<div class="font-mono text-base font-bold text-gray-900 md:mt-1 md:text-2xl dark:text-terminal-text">{results.total_scanned}</div>
			</div>
			<div class="rounded-md border border-green-200 bg-green-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-green-500/20 dark:bg-green-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-green-600 md:text-[10px] dark:text-green-400">Top</div>
				<div class="font-mono text-base font-bold text-green-700 md:mt-1 md:text-2xl dark:text-green-400">{results.results.length}<span class="text-[9px] font-normal text-green-500 md:text-xs">/{results.total_passed}</span></div>
			</div>
			<div class="rounded-md border border-green-300 bg-green-100 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-green-500/30 dark:bg-green-900/20">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-green-700 md:text-[10px] dark:text-green-400">Entry</div>
				<div class="font-mono text-base font-bold text-green-800 md:mt-1 md:text-2xl dark:text-green-300">{entryCount}</div>
			</div>
			<div class="rounded-md border border-red-200 bg-red-50 px-2 py-1.5 md:rounded-xl md:p-3 dark:border-red-500/20 dark:bg-red-900/10">
				<div class="text-[7px] font-semibold uppercase tracking-wider text-red-600 md:text-[10px] dark:text-red-400">HOT</div>
				<div class="font-mono text-base font-bold text-red-700 md:mt-1 md:text-2xl dark:text-red-400">{hotCount}</div>
			</div>
		</div>

		<AraHunterTable
			data={results.results}
			onselect={(stock) => (selectedStock = stock)}
		/>
	{/if}

	<!-- Detail panel -->
	{#if selectedStock}
		<StockDetail stock={selectedStock} mode="intraday" onclose={() => (selectedStock = null)} />
	{/if}
</div>
