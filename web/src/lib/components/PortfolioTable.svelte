<script lang="ts">
	import type { PortfolioStockResult } from '$lib/types';

	let { data }: { data: PortfolioStockResult[] } = $props();

	let signalFilter = $state('ALL');
	let sortField = $state<'severity' | 'pnl_pct' | 'pnl_rp' | 'ticker'>('severity');
	let sortDir = $state<'asc' | 'desc'>('asc');
	let expandedTicker = $state('');

	const signalColorMap: Record<string, string> = {
		CUT_LOSS: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-500/15 dark:text-red-400 dark:border-red-500/30',
		JUAL_SEMUA: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-500/15 dark:text-orange-400 dark:border-orange-500/30',
		JUAL_SEBAGIAN: 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30',
		JUAL_KURANGI: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-500/15 dark:text-yellow-400 dark:border-yellow-500/30',
		SIAP_JUAL: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-500/15 dark:text-yellow-400 dark:border-yellow-500/30',
		PERTIMBANGKAN_JUAL: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/15 dark:text-blue-400 dark:border-blue-500/30',
		HOLD: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-500/15 dark:text-green-400 dark:border-green-500/30',
	};

	let cutLossCount = $derived(data.filter((h) => h.signal.code === 'CUT_LOSS').length);
	let jualCount = $derived(data.filter((h) => h.signal.code.includes('JUAL')).length);
	let holdCount = $derived(data.filter((h) => h.signal.code === 'HOLD').length);

	let filtered = $derived.by(() => {
		let items = data;
		if (signalFilter === 'CUT_LOSS') items = items.filter((h) => h.signal.code === 'CUT_LOSS');
		else if (signalFilter === 'JUAL') items = items.filter((h) => h.signal.code.includes('JUAL'));
		else if (signalFilter === 'HOLD') items = items.filter((h) => h.signal.code === 'HOLD');
		return items;
	});

	let sorted = $derived.by(() => {
		const items = [...filtered];
		items.sort((a, b) => {
			let va: number, vb: number;
			switch (sortField) {
				case 'severity':
					va = a.signal.severity;
					vb = b.signal.severity;
					break;
				case 'pnl_pct':
					va = a.pnl_pct;
					vb = b.pnl_pct;
					break;
				case 'pnl_rp':
					va = a.pnl_rp;
					vb = b.pnl_rp;
					break;
				case 'ticker':
					return sortDir === 'asc' ? a.ticker.localeCompare(b.ticker) : b.ticker.localeCompare(a.ticker);
				default:
					return 0;
			}
			return sortDir === 'asc' ? va - vb : vb - va;
		});
		return items;
	});

	function toggleSort(field: typeof sortField) {
		if (sortField === field) {
			sortDir = sortDir === 'asc' ? 'desc' : 'asc';
		} else {
			sortField = field;
			sortDir = field === 'severity' ? 'asc' : 'desc';
		}
	}

	function fmt(n: number): string {
		return n.toLocaleString('id-ID', { maximumFractionDigits: 0 });
	}

	function fmtPct(n: number): string {
		return (n >= 0 ? '+' : '') + n.toFixed(1) + '%';
	}

	function fmtRp(n: number): string {
		const prefix = n >= 0 ? '+' : '';
		if (Math.abs(n) >= 1e6) return prefix + (n / 1e6).toFixed(1) + 'M';
		return prefix + fmt(n);
	}
</script>

<!-- Filter pills -->
<div class="mb-3 flex flex-wrap gap-1.5">
	{#each [
		{ id: 'ALL', label: `Semua (${data.length})` },
		{ id: 'CUT_LOSS', label: `Cut Loss (${cutLossCount})`, color: 'text-red-500' },
		{ id: 'JUAL', label: `Jual (${jualCount})`, color: 'text-orange-500' },
		{ id: 'HOLD', label: `Hold (${holdCount})`, color: 'text-green-500' }
	] as pill}
		<button
			onclick={() => (signalFilter = pill.id)}
			class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-all
				{signalFilter === pill.id
					? 'bg-amber-600 text-white shadow-sm shadow-amber-500/25'
					: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
		>
			{pill.label}
		</button>
	{/each}
</div>

<!-- Table -->
<div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-terminal-border">
	<table class="w-full text-xs">
		<thead>
			<tr class="border-b border-gray-200 bg-gray-50 dark:border-terminal-border dark:bg-terminal-bg">
				<th class="w-8 px-3 py-2.5 text-left font-semibold text-gray-400 dark:text-terminal-dim">#</th>
				<th class="cursor-pointer px-3 py-2.5 text-left font-semibold text-gray-400 dark:text-terminal-dim" onclick={() => toggleSort('ticker')}>
					Saham {sortField === 'ticker' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
				</th>
				<th class="px-3 py-2.5 text-right font-semibold text-gray-400 dark:text-terminal-dim">Lot</th>
				<th class="px-3 py-2.5 text-right font-semibold text-gray-400 dark:text-terminal-dim">Avg Beli</th>
				<th class="px-3 py-2.5 text-right font-semibold text-gray-400 dark:text-terminal-dim">Harga Now</th>
				<th class="cursor-pointer px-3 py-2.5 text-right font-semibold text-gray-400 dark:text-terminal-dim" onclick={() => toggleSort('pnl_pct')}>
					P&L % {sortField === 'pnl_pct' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
				</th>
				<th class="cursor-pointer px-3 py-2.5 text-right font-semibold text-gray-400 dark:text-terminal-dim" onclick={() => toggleSort('pnl_rp')}>
					P&L Rp {sortField === 'pnl_rp' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
				</th>
				<th class="cursor-pointer px-3 py-2.5 text-center font-semibold text-gray-400 dark:text-terminal-dim" onclick={() => toggleSort('severity')}>
					Sinyal {sortField === 'severity' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
				</th>
			</tr>
		</thead>
		<tbody>
			{#each sorted as h, i}
				{@const isUrgent = h.signal.severity <= 2}
				{@const isExpanded = expandedTicker === h.ticker}
				<tr
					class="cursor-pointer border-b transition-colors
						{isUrgent ? 'border-l-[3px] border-l-red-500 bg-red-50/50 dark:bg-red-900/5' : 'border-l-[3px] border-l-transparent'}
						{isExpanded ? 'bg-amber-50/50 dark:bg-amber-900/5' : ''}
						border-b-gray-100 hover:bg-gray-50 dark:border-b-terminal-border/50 dark:hover:bg-terminal-surface-hover"
					onclick={() => (expandedTicker = isExpanded ? '' : h.ticker)}
				>
					<td class="px-3 py-2 text-gray-400 dark:text-terminal-dim">{i + 1}</td>
					<td class="px-3 py-2 font-mono font-bold text-gray-900 dark:text-terminal-text">{h.ticker}</td>
					<td class="px-3 py-2 text-right font-mono text-gray-600 dark:text-terminal-muted">{h.lot}</td>
					<td class="px-3 py-2 text-right font-mono text-gray-600 dark:text-terminal-muted">{fmt(h.avg_price)}</td>
					<td class="px-3 py-2 text-right font-mono font-semibold text-gray-900 dark:text-terminal-text">{fmt(h.current_price)}</td>
					<td class="px-3 py-2 text-right font-mono font-semibold {h.pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}">
						{fmtPct(h.pnl_pct)}
					</td>
					<td class="px-3 py-2 text-right font-mono {h.pnl_rp >= 0 ? 'text-green-500' : 'text-red-500'}">
						{fmtRp(h.pnl_rp)}
					</td>
					<td class="px-3 py-2 text-center">
						<span class="inline-block rounded-md border px-2 py-0.5 text-[10px] font-bold {signalColorMap[h.signal.code] || ''}">
							{h.signal.label}
						</span>
					</td>
				</tr>

				<!-- Expanded detail row -->
				{#if isExpanded}
					<tr class="border-b border-gray-100 dark:border-terminal-border/50">
						<td colspan="8" class="px-4 py-4">
							<div class="space-y-3">
								<!-- Signal reason -->
								<div class="flex items-start gap-3 rounded-lg border px-4 py-3 {signalColorMap[h.signal.code] || ''}">
									<div>
										<p class="text-sm font-bold">{h.signal.label}</p>
										<p class="mt-0.5 text-xs">{h.signal.reason}</p>
									</div>
								</div>

								<!-- Action items -->
								<div class="rounded-lg bg-gray-50 p-3 dark:bg-terminal-bg">
									<p class="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Aksi</p>
									<ul class="space-y-1">
										{#each h.signal.action_items as item}
											<li class="flex items-start gap-2 text-xs text-gray-700 dark:text-terminal-text">
												<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-400 dark:bg-terminal-dim"></span>
												{item}
											</li>
										{/each}
									</ul>
								</div>

								<!-- Technical data -->
								<div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
									{#if h.stage_label}
										<div class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-terminal-bg">
											<div class="text-[10px] text-gray-400 dark:text-terminal-dim">Stage</div>
											<div class="font-mono text-xs font-semibold text-gray-900 dark:text-terminal-text">{h.stage_label}</div>
										</div>
									{/if}
									{#if h.ma50 != null}
										<div class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-terminal-bg">
											<div class="text-[10px] text-gray-400 dark:text-terminal-dim">MA50</div>
											<div class="font-mono text-xs font-semibold {h.current_price > h.ma50 ? 'text-green-500' : 'text-red-500'}">
												{fmt(h.ma50)}
												<span class="text-[9px]">({h.current_price > h.ma50 ? 'di atas' : 'di bawah'})</span>
											</div>
										</div>
									{/if}
									{#if h.sl != null}
										<div class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-terminal-bg">
											<div class="text-[10px] text-gray-400 dark:text-terminal-dim">Stop Loss</div>
											<div class="font-mono text-xs font-semibold text-red-500">{fmt(h.sl)}</div>
										</div>
									{/if}
									{#if h.rsi != null}
										<div class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-terminal-bg">
											<div class="text-[10px] text-gray-400 dark:text-terminal-dim">RSI</div>
											<div class="font-mono text-xs font-semibold text-gray-900 dark:text-terminal-text">
												{h.rsi.toFixed(0)}
												{#if h.rsi > 70}<span class="text-[9px] text-red-500">(OB)</span>{/if}
												{#if h.rsi < 30}<span class="text-[9px] text-green-500">(OS)</span>{/if}
											</div>
										</div>
									{/if}
								</div>

								<!-- TP levels -->
								{#if h.tp1 != null || h.tp2 != null}
									<div class="flex flex-wrap gap-2">
										{#if h.tp1 != null}
											<div class="rounded-lg bg-green-50 px-3 py-1.5 dark:bg-green-900/10">
												<span class="text-[10px] text-green-600 dark:text-green-400">TP1:</span>
												<span class="font-mono text-xs font-bold text-green-600 dark:text-green-400">{fmt(h.tp1)}</span>
												{#if h.current_price >= h.tp1}
													<span class="ml-1 text-[9px] font-bold text-green-500">TERCAPAI</span>
												{/if}
											</div>
										{/if}
										{#if h.tp2 != null}
											<div class="rounded-lg bg-green-50 px-3 py-1.5 dark:bg-green-900/10">
												<span class="text-[10px] text-green-600 dark:text-green-400">TP2:</span>
												<span class="font-mono text-xs font-bold text-green-600 dark:text-green-400">{fmt(h.tp2)}</span>
												{#if h.current_price >= h.tp2}
													<span class="ml-1 text-[9px] font-bold text-green-500">TERCAPAI</span>
												{/if}
											</div>
										{/if}
									</div>
								{/if}
							</div>
						</td>
					</tr>
				{/if}
			{/each}
		</tbody>
	</table>
</div>
