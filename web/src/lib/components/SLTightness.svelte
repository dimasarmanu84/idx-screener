<script lang="ts">
	let { level, ratio }: { level: string; ratio: number } = $props();

	const colorMap: Record<string, string> = {
		AMAN: 'bg-green-500/15 text-green-600 dark:text-green-400',
		CUKUP: 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400',
		KETAT: 'bg-orange-500/15 text-orange-600 dark:text-orange-400',
		'SANGAT KETAT': 'bg-red-500/15 text-red-600 dark:text-red-400'
	};

	let classes = $derived(colorMap[level] || 'bg-gray-500/15 text-gray-600');
</script>

<span class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-bold {classes}">
	{level === 'SANGAT KETAT' ? 'S.KETAT' : level}
	<span class="ml-1 font-mono opacity-60">({ratio.toFixed(2)})</span>
</span>
