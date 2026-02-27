<script lang="ts">
	import type { PortfolioResponse } from '$lib/types';

	let { data }: { data: PortfolioResponse } = $props();

	let s = $derived(data.summary);

	function fmtRp(n: number): string {
		if (Math.abs(n) >= 1e9) return 'Rp ' + (n / 1e9).toFixed(1) + 'B';
		if (Math.abs(n) >= 1e6) return 'Rp ' + (n / 1e6).toFixed(1) + 'M';
		return 'Rp ' + n.toLocaleString('id-ID');
	}

	let jualCount = $derived(
		(s.signal_counts['JUAL_SEMUA'] || 0) +
		(s.signal_counts['JUAL_SEBAGIAN'] || 0) +
		(s.signal_counts['JUAL_KURANGI'] || 0) +
		(s.signal_counts['SIAP_JUAL'] || 0) +
		(s.signal_counts['PERTIMBANGKAN_JUAL'] || 0)
	);
</script>

<!-- Urgent alert banner -->
{#if s.cut_loss_tickers.length > 0}
	<div class="mb-4 flex items-center gap-3 rounded-xl border-2 border-red-300 bg-red-50 p-4 dark:border-red-500/40 dark:bg-red-900/20">
		<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-500/20">
			<svg class="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
			</svg>
		</div>
		<div>
			<p class="text-sm font-bold text-red-700 dark:text-red-400">
				CUT LOSS SEGERA: {s.cut_loss_tickers.join(', ')}
			</p>
			<p class="text-xs text-red-600 dark:text-red-400/80">
				{s.cut_loss_tickers.length} saham perlu segera dijual!
			</p>
		</div>
	</div>
{/if}

<!-- Summary cards -->
<div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
	<div class="rounded-xl border border-gray-200 bg-white p-3 dark:border-terminal-border dark:bg-terminal-surface">
		<div class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Invested</div>
		<div class="mt-1 font-mono text-lg font-bold text-gray-900 dark:text-terminal-text">{fmtRp(s.total_invested)}</div>
	</div>
	<div class="rounded-xl border border-gray-200 bg-white p-3 dark:border-terminal-border dark:bg-terminal-surface">
		<div class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Market Value</div>
		<div class="mt-1 font-mono text-lg font-bold text-gray-900 dark:text-terminal-text">{fmtRp(s.total_market_value)}</div>
	</div>
	<div class="rounded-xl border p-3 {s.total_pnl_rp >= 0
		? 'border-green-200 bg-green-50 dark:border-green-500/20 dark:bg-green-900/10'
		: 'border-red-200 bg-red-50 dark:border-red-500/20 dark:bg-red-900/10'}">
		<div class="text-[10px] font-semibold uppercase tracking-wider {s.total_pnl_rp >= 0
			? 'text-green-600 dark:text-green-400'
			: 'text-red-600 dark:text-red-400'}">P&L</div>
		<div class="mt-1 font-mono text-lg font-bold {s.total_pnl_rp >= 0
			? 'text-green-700 dark:text-green-400'
			: 'text-red-600 dark:text-red-400'}">
			{s.total_pnl_pct >= 0 ? '+' : ''}{s.total_pnl_pct.toFixed(1)}%
		</div>
		<div class="mt-0.5 font-mono text-[10px] {s.total_pnl_rp >= 0
			? 'text-green-600/70 dark:text-green-400/70'
			: 'text-red-500/70 dark:text-red-400/70'}">
			{s.total_pnl_rp >= 0 ? '+' : ''}{fmtRp(s.total_pnl_rp)}
		</div>
	</div>
	<div class="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-500/20 dark:bg-amber-900/10">
		<div class="text-[10px] font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">Signals</div>
		<div class="mt-1 flex flex-wrap gap-1">
			{#if s.signal_counts['CUT_LOSS']}
				<span class="rounded bg-red-500/15 px-1.5 py-0.5 font-mono text-[10px] font-bold text-red-500">
					{s.signal_counts['CUT_LOSS']} CL
				</span>
			{/if}
			{#if jualCount > 0}
				<span class="rounded bg-orange-500/15 px-1.5 py-0.5 font-mono text-[10px] font-bold text-orange-500">
					{jualCount} Jual
				</span>
			{/if}
			{#if s.signal_counts['HOLD']}
				<span class="rounded bg-green-500/15 px-1.5 py-0.5 font-mono text-[10px] font-bold text-green-500">
					{s.signal_counts['HOLD']} Hold
				</span>
			{/if}
		</div>
		{#if data.total_errors > 0}
			<div class="mt-1 text-[10px] text-red-500">{data.total_errors} errors</div>
		{/if}
	</div>
</div>
