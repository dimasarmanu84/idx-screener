<script lang="ts">
	let { current, total, ticker }: { current: number; total: number; ticker: string } = $props();
	let pct = $derived(total > 0 ? (current / total) * 100 : 0);
</script>

<div class="mb-5 overflow-hidden rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-blue-50/50 p-4 dark:border-blue-500/20 dark:from-blue-900/10 dark:to-transparent">
	<div class="mb-2.5 flex items-center justify-between">
		<div class="flex items-center gap-2">
			<div class="h-2 w-2 animate-pulse rounded-full bg-blue-500"></div>
			<span class="text-sm text-gray-700 dark:text-terminal-text">
				Scanning <span class="font-mono font-bold">{ticker}</span>
			</span>
		</div>
		<span class="font-mono text-sm font-bold text-blue-600 dark:text-blue-400">{current}/{total}</span>
	</div>
	<div class="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-terminal-border">
		<div
			class="h-2 rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300"
			style="width: {pct}%"
		></div>
	</div>
	<div class="mt-1 text-right font-mono text-[10px] text-gray-400 dark:text-terminal-dim">
		{pct.toFixed(0)}%
	</div>
</div>
