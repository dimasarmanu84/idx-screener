<script lang="ts">
	import { streamPortfolio } from '$lib/api';
	import PortfolioInput from '$lib/components/PortfolioInput.svelte';
	import PortfolioSummary from '$lib/components/PortfolioSummary.svelte';
	import PortfolioTable from '$lib/components/PortfolioTable.svelte';
	import ScanProgress from '$lib/components/ScanProgress.svelte';
	import { scanner, clearBadge, requestNotifPermission, toggleNotif, toggleTelegram } from '$lib/portfolioScanner.svelte';
	import { auth, syncToServer } from '$lib/auth.svelte';
	import type { PortfolioHolding, PortfolioResponse, PortfolioStockResult } from '$lib/types';
	import { onMount } from 'svelte';

	let notifSupported = $state(false);

	const STORAGE_KEY = 'screener_portfolio';

	let holdings = $state<PortfolioHolding[]>([]);
	let analyzing = $state(false);
	let progress = $state({ current: 0, total: 0, ticker: '' });
	let results = $state<PortfolioResponse | null>(null);
	let streamingHoldings = $state<PortfolioStockResult[]>([]);
	let error = $state('');
	let cleanup: (() => void) | null = $state(null);

	let displayHoldings = $derived(results ? results.holdings : streamingHoldings);

	onMount(() => {
		clearBadge();
		notifSupported = 'Notification' in window;
		const saved = localStorage.getItem(STORAGE_KEY);
		if (saved) {
			try {
				holdings = JSON.parse(saved);
			} catch {
				// ignore corrupted data
			}
		}

		// Listen for server sync events (from auth login/loadSession)
		const handleSync = (e: Event) => {
			const detail = (e as CustomEvent).detail;
			if (Array.isArray(detail)) {
				holdings = detail;
			}
		};
		window.addEventListener('portfolio-synced', handleSync);

		return () => {
			window.removeEventListener('portfolio-synced', handleSync);
		};
	});

	async function handleNotifToggle() {
		if (scanner.notifEnabled) {
			toggleNotif(false);
		} else {
			await requestNotifPermission();
		}
	}

	// Save to localStorage whenever holdings change, sync to server if logged in
	$effect(() => {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
		if (auth.isLoggedIn) {
			syncToServer(holdings);
		}
	});

	function startAnalysis() {
		if (holdings.length === 0) {
			error = 'Tambahkan saham terlebih dahulu';
			return;
		}

		analyzing = true;
		error = '';
		results = null;
		streamingHoldings = [];

		cleanup = streamPortfolio(
			holdings,
			(current, total, ticker) => {
				progress = { current, total, ticker };
			},
			(data) => {
				results = data;
				analyzing = false;
			},
			(err) => {
				error = err;
				analyzing = false;
			},
			(stock) => {
				streamingHoldings = [...streamingHoldings, stock];
			}
		);
	}

	function stopAnalysis() {
		cleanup?.();
		analyzing = false;
	}
</script>

<div class="py-3 md:py-8">
	<!-- Header -->
	<div class="mb-2 md:mb-6">
		<h1 class="text-lg font-extrabold tracking-tight text-gray-900 md:text-3xl dark:text-terminal-text">
			Portfolio Tracker
		</h1>
		<p class="hidden text-sm text-gray-500 md:mt-1 md:block dark:text-terminal-muted">
			Input portfolio saham kamu, dapatkan sinyal HOLD / JUAL / CUT LOSS berdasarkan analisis teknikal
		</p>
	</div>

	<!-- Sync indicator -->
	{#if auth.isLoggedIn}
		<div class="mb-1.5 flex items-center gap-1.5 text-[11px] text-gray-400 md:mb-2 md:text-xs dark:text-terminal-dim">
			<svg class="h-3 w-3 text-green-500" fill="currentColor" viewBox="0 0 24 24">
				<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
			</svg>
			Synced ke {auth.user?.email}
		</div>
	{/if}

	<!-- Portfolio Input -->
	<div class="mb-2 md:mb-6">
		<PortfolioInput bind:holdings disabled={analyzing} />
	</div>

	<!-- Action buttons -->
	<div class="mb-2 flex items-center gap-2 md:mb-6 md:gap-3">
		{#if analyzing}
			<button
				onclick={stopAnalysis}
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
				onclick={startAnalysis}
				disabled={holdings.length === 0}
				class="flex h-7 items-center gap-1 rounded-md bg-amber-600 px-2.5 text-[11px] font-semibold text-white shadow-sm shadow-amber-500/25 transition-all hover:bg-amber-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 md:h-10 md:gap-2 md:rounded-lg md:px-5 md:text-sm"
			>
				<svg class="h-3 w-3 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
				</svg>
				Analisis ({holdings.length} saham)
			</button>
		{/if}

		<!-- Notification toggle -->
		{#if notifSupported}
			<button
				onclick={handleNotifToggle}
				class="flex h-7 items-center gap-1 rounded-md px-2 text-[11px] font-semibold transition-all md:h-10 md:gap-1.5 md:rounded-lg md:px-3 md:text-xs
					{scanner.notifEnabled
						? 'bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400'
						: 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
				title={scanner.notifEnabled ? 'Notifikasi aktif' : 'Aktifkan notifikasi'}
			>
				{#if scanner.notifEnabled}
					<svg class="h-3.5 w-3.5 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
					</svg>
					<span class="hidden sm:inline">ON</span>
				{:else}
					<svg class="h-3.5 w-3.5 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
						<line x1="3" y1="3" x2="21" y2="21" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
					</svg>
					<span class="hidden sm:inline">Notif</span>
				{/if}
			</button>
		{/if}

		<!-- Telegram toggle -->
		<button
			onclick={() => toggleTelegram(!scanner.telegramEnabled)}
			disabled={!scanner.telegramConfigured}
			class="flex h-7 items-center gap-1 rounded-md px-2 text-[11px] font-semibold transition-all md:h-10 md:gap-1.5 md:rounded-lg md:px-3 md:text-xs
				{!scanner.telegramConfigured
					? 'cursor-not-allowed bg-gray-100 text-gray-300 dark:bg-terminal-surface dark:text-terminal-dim'
					: scanner.telegramEnabled
						? 'bg-sky-100 text-sky-700 dark:bg-sky-900/20 dark:text-sky-400'
						: 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
			title={!scanner.telegramConfigured ? 'Setup bot token di .env backend' : scanner.telegramEnabled ? 'Telegram aktif' : 'Aktifkan Telegram'}
		>
			<svg class="h-3.5 w-3.5 md:h-4 md:w-4" viewBox="0 0 24 24" fill="currentColor">
				<path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
			</svg>
			<span class="hidden sm:inline">{scanner.telegramEnabled ? 'TG ON' : 'TG'}</span>
		</button>
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
	{#if analyzing}
		<ScanProgress current={progress.current} total={progress.total} ticker={progress.ticker} />
	{/if}

	<!-- Results (show during analyzing + after complete) -->
	{#if results}
		<PortfolioSummary data={results} />
	{/if}
	{#if displayHoldings.length > 0}
		<PortfolioTable data={displayHoldings} />
	{/if}
</div>
