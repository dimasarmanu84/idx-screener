<script lang="ts">
	import { onMount } from 'svelte';
	import { marketStatus } from '$lib/stores';
	import { fetchMarketStatus } from '$lib/api';

	onMount(() => {
		fetchMarketStatus().then((s) => marketStatus.set(s)).catch(() => {});
		const interval = setInterval(async () => {
			try {
				const s = await fetchMarketStatus();
				marketStatus.set(s);
			} catch {}
		}, 60000);
		return () => clearInterval(interval);
	});
</script>

{#if $marketStatus}
	<div class="flex items-center gap-2 rounded-lg bg-gray-50 px-2.5 py-1.5 dark:bg-terminal-bg">
		<span class="relative flex h-2 w-2">
			{#if $marketStatus.is_open}
				<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
			{/if}
			<span
				class="relative inline-flex h-2 w-2 rounded-full {$marketStatus.is_open
					? 'bg-green-500'
					: 'bg-red-500'}"
			></span>
		</span>
		<span class="font-mono text-xs font-semibold {$marketStatus.is_open ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}">
			{$marketStatus.is_open ? 'LIVE' : 'CLOSED'}
		</span>
		{#if $marketStatus.is_open}
			<div class="h-1 w-10 overflow-hidden rounded-full bg-gray-200 dark:bg-terminal-border">
				<div
					class="h-1 rounded-full bg-green-500 transition-all duration-500"
					style="width: {$marketStatus.progress_pct}%"
				></div>
			</div>
			<span class="font-mono text-[10px] text-gray-500 dark:text-terminal-dim">{$marketStatus.progress_pct.toFixed(0)}%</span>
		{/if}
	</div>
{/if}
