<script lang="ts">
	import type { StockGroup } from '$lib/types';

	let {
		value = $bindable('lq45'),
		groups
	}: { value: string; groups: StockGroup[] } = $props();

	let open = $state(false);
	let showInfo = $state(false);

	const labels: Record<string, string> = {
		lq45: 'LQ45 (46 saham)',
		idx80: 'LQ45 + IDX80 (70 saham)',
		all_idx: 'Semua IDX (86 saham)',
		all_stocks: 'Semua + Small Cap (130+)',
		all_bursa: 'Seluruh Bursa IDX (900+)',
		jii: 'JII (30 saham)',
		jii70: 'JII + JII70 (54 saham)',
		issi: 'Semua Syariah (73 saham)'
	};

	const shortLabels: Record<string, string> = {
		lq45: 'LQ45',
		idx80: 'IDX80',
		all_idx: 'Semua IDX',
		all_stocks: 'All + SmallCap',
		all_bursa: 'All Bursa',
		jii: 'JII',
		jii70: 'JII70',
		issi: 'Syariah'
	};

	// Category definitions with description
	interface CategoryDef {
		key: string;
		label: string;
		desc: string;
		icon: string;
		items: StockGroup[];
	}

	const allCategories: CategoryDef[] = [
		{
			key: 'populer',
			label: 'Populer & Likuid',
			desc: 'Saham blue chip dan mid cap dengan likuiditas tinggi, cocok untuk trader pemula hingga menengah.',
			icon: '~',
			items: ['lq45', 'idx80', 'all_idx']
		},
		{
			key: 'extended',
			label: 'Extended & Small Cap',
			desc: 'Termasuk saham small cap dan seluruh emiten. Lebih banyak peluang tapi risiko lebih tinggi.',
			icon: '+',
			items: ['all_stocks', 'all_bursa']
		},
		{
			key: 'syariah',
			label: 'Syariah',
			desc: 'Saham yang sesuai prinsip syariah Islam, disaring oleh OJK. Bebas riba dan sektor haram.',
			icon: '*',
			items: ['jii', 'jii70', 'issi']
		}
	];

	// Filter categories to only show groups that are passed in
	let categories = $derived(
		allCategories
			.map((cat) => ({
				...cat,
				items: cat.items.filter((item) => groups.includes(item))
			}))
			.filter((cat) => cat.items.length > 0)
	);

	function select(group: StockGroup) {
		value = group;
		open = false;
	}

	function handleClickOutside(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (!target.closest('.stock-selector-wrapper')) {
			open = false;
			showInfo = false;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="stock-selector-wrapper relative">
	<!-- Trigger Button -->
	<button
		type="button"
		onclick={() => (open = !open)}
		class="flex h-10 items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:hover:bg-terminal-surface-hover"
	>
		<span class="max-w-[180px] truncate">{labels[value] || value}</span>
		<svg
			class="h-4 w-4 shrink-0 text-gray-400 transition-transform {open ? 'rotate-180' : ''}"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	<!-- Dropdown Panel -->
	{#if open}
		<div
			class="absolute left-0 top-full z-50 mt-1 w-72 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg dark:border-terminal-border dark:bg-terminal-bg"
		>
			<!-- Info Toggle Header -->
			<div class="flex items-center justify-between border-b border-gray-100 px-3 py-2 dark:border-terminal-border">
				<span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Pilih Daftar Saham</span>
				<button
					type="button"
					onclick={(e) => { e.stopPropagation(); showInfo = !showInfo; }}
					class="flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium text-blue-500 transition-colors hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
				>
					<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					{showInfo ? 'Tutup' : 'Info'}
				</button>
			</div>

			<!-- Categories -->
			<div class="max-h-80 overflow-y-auto py-1">
				{#each categories as cat, ci}
					<!-- Category Header -->
					<div class="px-3 pt-2 {ci > 0 ? 'border-t border-gray-100 dark:border-terminal-border' : ''}">
						<div class="flex items-center gap-1.5">
							<span class="text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:text-terminal-muted">{cat.label}</span>
						</div>
						<!-- Info Popover per category -->
						{#if showInfo}
							<p class="mt-0.5 text-[10px] leading-snug text-gray-400 dark:text-terminal-dim">{cat.desc}</p>
						{/if}
					</div>

					<!-- Items -->
					{#each cat.items as group}
						<button
							type="button"
							onclick={() => select(group)}
							class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors
								{value === group
									? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
									: 'text-gray-700 hover:bg-gray-50 dark:text-terminal-text dark:hover:bg-terminal-surface-hover'}"
						>
							<!-- Check icon -->
							<span class="w-4 shrink-0 text-center text-xs {value === group ? 'text-blue-500' : 'text-transparent'}">
								{value === group ? '>' : ''}
							</span>

							<span class="flex-1">
								<span class="font-medium">{shortLabels[group] || group}</span>
								<span class="ml-1 text-xs text-gray-400 dark:text-terminal-dim">
									{labels[group]?.match(/\(.*\)/)?.[0] || ''}
								</span>
							</span>

							{#if value === group}
								<span class="rounded bg-blue-100 px-1.5 py-0.5 text-[9px] font-bold text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">AKTIF</span>
							{/if}
						</button>
					{/each}
				{/each}
			</div>
		</div>
	{/if}
</div>
