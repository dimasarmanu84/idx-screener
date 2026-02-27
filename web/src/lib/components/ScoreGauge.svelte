<script lang="ts">
	let { score }: { score: number } = $props();

	let color = $derived(
		score >= 80
			? 'bg-green-500'
			: score >= 60
				? 'bg-blue-500'
				: score >= 40
					? 'bg-yellow-500'
					: 'bg-red-500'
	);

	let textColor = $derived(
		score >= 80
			? 'text-green-600 dark:text-green-400'
			: score >= 60
				? 'text-blue-600 dark:text-blue-400'
				: score >= 40
					? 'text-yellow-600 dark:text-yellow-400'
					: 'text-red-600 dark:text-red-400'
	);
</script>

<div class="flex items-center gap-2">
	<div class="h-1.5 w-12 overflow-hidden rounded-full bg-gray-200 dark:bg-terminal-border">
		<div class="{color} h-1.5 rounded-full transition-all duration-300" style="width: {score}%"></div>
	</div>
	<span class="font-mono text-xs font-bold {textColor}">{score}</span>
</div>
