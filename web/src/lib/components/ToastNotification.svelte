<script lang="ts">
	import { scanner, dismissToast } from '$lib/portfolioScanner.svelte';
	import { onDestroy } from 'svelte';

	const severityBorder: Record<string, string> = {
		CUT_LOSS: 'border-l-red-500',
		JUAL_SEMUA: 'border-l-orange-500',
		JUAL_SEBAGIAN: 'border-l-amber-500',
		JUAL_KURANGI: 'border-l-yellow-500',
		SIAP_JUAL: 'border-l-yellow-500',
		PERTIMBANGKAN_JUAL: 'border-l-blue-500'
	};

	const signalBadge: Record<string, string> = {
		CUT_LOSS: 'bg-red-500/15 text-red-600 dark:text-red-400',
		JUAL_SEMUA: 'bg-orange-500/15 text-orange-600 dark:text-orange-400',
		JUAL_SEBAGIAN: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
		JUAL_KURANGI: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400',
		SIAP_JUAL: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400',
		PERTIMBANGKAN_JUAL: 'bg-blue-500/15 text-blue-600 dark:text-blue-400'
	};

	// Auto-dismiss timers
	let timers = new Map<string, ReturnType<typeof setTimeout>>();

	$effect(() => {
		for (const toast of scanner.toasts) {
			if (!timers.has(toast.id)) {
				const timer = setTimeout(() => {
					dismissToast(toast.id);
					timers.delete(toast.id);
				}, 8000);
				timers.set(toast.id, timer);
			}
		}

		// Cleanup removed toasts
		for (const [id, timer] of timers) {
			if (!scanner.toasts.find((t) => t.id === id)) {
				clearTimeout(timer);
				timers.delete(id);
			}
		}
	});

	onDestroy(() => {
		for (const timer of timers.values()) clearTimeout(timer);
		timers.clear();
	});
</script>

{#if scanner.toasts.length > 0}
	<div class="fixed bottom-4 right-4 z-50 flex max-w-sm flex-col gap-2">
		{#each scanner.toasts as toast (toast.id)}
			{@const topAlert = toast.alerts[0]}
			<div
				class="animate-slide-in overflow-hidden rounded-xl border-l-4 bg-white shadow-lg dark:bg-terminal-surface {severityBorder[topAlert.signalCode] || 'border-l-gray-500'}"
				role="alert"
			>
				<div class="p-3">
					<!-- Header -->
					<div class="mb-2 flex items-center justify-between">
						<div class="flex items-center gap-1.5">
							<svg
								class="h-4 w-4 text-red-500"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
								/>
							</svg>
							<span class="text-xs font-bold text-gray-900 dark:text-terminal-text">
								Portfolio Alert
							</span>
						</div>
						<button
							onclick={() => dismissToast(toast.id)}
							class="rounded p-0.5 text-gray-400 hover:text-gray-700 dark:hover:text-terminal-text"
							aria-label="Dismiss"
						>
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					</div>

					<!-- Alert items (max 3) -->
					<div class="space-y-1">
						{#each toast.alerts.slice(0, 3) as alert}
							<div class="flex items-center justify-between">
								<span
									class="font-mono text-[11px] font-bold text-gray-900 dark:text-terminal-text"
									>{alert.ticker}</span
								>
								<span
									class="rounded px-1.5 py-0.5 text-[9px] font-bold {signalBadge[alert.signalCode] || ''}"
								>
									{alert.signalLabel}
								</span>
							</div>
						{/each}
						{#if toast.alerts.length > 3}
							<p class="text-[10px] text-gray-500 dark:text-terminal-muted">
								+{toast.alerts.length - 3} saham lainnya
							</p>
						{/if}
					</div>

					<!-- Link -->
					<a
						href="/portfolio"
						onclick={() => dismissToast(toast.id)}
						class="mt-2 flex items-center gap-1 text-[11px] font-semibold text-amber-600 hover:text-amber-700 dark:text-amber-400"
					>
						Buka Portfolio
						<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M13 7l5 5m0 0l-5 5m5-5H6"
							/>
						</svg>
					</a>
				</div>
			</div>
		{/each}
	</div>
{/if}
