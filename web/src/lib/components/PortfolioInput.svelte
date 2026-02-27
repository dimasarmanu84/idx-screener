<script lang="ts">
	import type { PortfolioHolding } from '$lib/types';

	let {
		holdings = $bindable(),
		disabled = false
	}: {
		holdings: PortfolioHolding[];
		disabled?: boolean;
	} = $props();

	let activeTab = $state<'manual' | 'paste' | 'csv'>('manual');

	// Manual form
	let newTicker = $state('');
	let newLot = $state('');
	let newAvgPrice = $state('');

	// Paste
	let pasteText = $state('');
	let parseMessage = $state('');

	function addManual() {
		const ticker = newTicker.trim().toUpperCase();
		const lot = parseInt(newLot);
		const avg_price = parseFloat(newAvgPrice);

		if (!ticker || ticker.length < 3 || ticker.length > 5) return;
		if (isNaN(lot) || lot <= 0) return;
		if (isNaN(avg_price) || avg_price <= 0) return;

		holdings = [...holdings, { ticker, lot, avg_price }];
		newTicker = '';
		newLot = '';
		newAvgPrice = '';
	}

	function handleManualKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') addManual();
	}

	function parsePasteText() {
		if (!pasteText.trim()) return;
		const lines = pasteText.trim().split('\n');
		const parsed: PortfolioHolding[] = [];
		const errors: string[] = [];

		for (let i = 0; i < lines.length; i++) {
			const parts = lines[i].trim().split(/[\s,;]+/);
			if (parts.length < 3) {
				errors.push(`Baris ${i + 1}: format tidak valid`);
				continue;
			}
			const ticker = parts[0].replace(/[^A-Za-z]/g, '').toUpperCase();
			const numbers = parts
				.slice(1)
				.map((p) => parseFloat(p.replace(/,/g, '')))
				.filter((n) => !isNaN(n));
			if (ticker && ticker.length >= 3 && ticker.length <= 5 && numbers.length >= 2) {
				parsed.push({ ticker, lot: Math.round(numbers[0]), avg_price: numbers[1] });
			} else {
				errors.push(`Baris ${i + 1}: tidak bisa di-parse`);
			}
		}

		if (parsed.length > 0) {
			holdings = [...holdings, ...parsed];
			pasteText = '';
			parseMessage = `${parsed.length} saham ditambahkan`;
			if (errors.length > 0) parseMessage += ` (${errors.length} baris gagal)`;
		} else {
			parseMessage = errors.length > 0 ? errors[0] : 'Tidak ada data valid';
		}
		setTimeout(() => (parseMessage = ''), 4000);
	}

	function handleFileUpload(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onload = (ev) => {
			pasteText = (ev.target?.result as string) || '';
			activeTab = 'paste';
			parsePasteText();
		};
		reader.readAsText(file);
		input.value = '';
	}

	function removeHolding(index: number) {
		holdings = holdings.filter((_, i) => i !== index);
	}

	function clearAll() {
		holdings = [];
	}

	function fmt(n: number): string {
		return n.toLocaleString('id-ID', { maximumFractionDigits: 0 });
	}
</script>

<div class="space-y-4">
	<!-- Tab buttons -->
	<div class="flex items-center gap-2">
		{#each [
			{ id: 'manual', label: 'Manual' },
			{ id: 'paste', label: 'Paste Teks' },
			{ id: 'csv', label: 'Upload CSV' }
		] as tab}
			<button
				onclick={() => (activeTab = tab.id as 'manual' | 'paste' | 'csv')}
				class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-all
					{activeTab === tab.id
						? 'bg-amber-600 text-white shadow-sm shadow-amber-500/25'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
				{disabled}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- Manual form -->
	{#if activeTab === 'manual'}
		<div class="flex flex-wrap items-end gap-2">
			<div class="flex-1 min-w-[100px]">
				<label for="pf-ticker" class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Ticker</label>
				<input
					id="pf-ticker"
					type="text"
					bind:value={newTicker}
					onkeydown={handleManualKeydown}
					placeholder="BBCA"
					maxlength="5"
					class="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 font-mono text-sm uppercase placeholder:normal-case placeholder:text-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim dark:focus:border-amber-500"
					{disabled}
				/>
			</div>
			<div class="w-20">
				<label for="pf-lot" class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Lot</label>
				<input
					id="pf-lot"
					type="number"
					bind:value={newLot}
					onkeydown={handleManualKeydown}
					placeholder="10"
					min="1"
					class="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 font-mono text-sm placeholder:text-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim dark:focus:border-amber-500"
					{disabled}
				/>
			</div>
			<div class="w-28">
				<label for="pf-price" class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Harga Beli</label>
				<input
					id="pf-price"
					type="number"
					bind:value={newAvgPrice}
					onkeydown={handleManualKeydown}
					placeholder="9500"
					min="1"
					class="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 font-mono text-sm placeholder:text-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim dark:focus:border-amber-500"
					{disabled}
				/>
			</div>
			<button
				onclick={addManual}
				class="flex h-10 items-center gap-1.5 rounded-lg bg-amber-600 px-4 text-sm font-semibold text-white shadow-sm shadow-amber-500/25 transition-all hover:bg-amber-700 active:scale-[0.98]"
				{disabled}
			>
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
				</svg>
				Tambah
			</button>
		</div>
	{/if}

	<!-- Paste text -->
	{#if activeTab === 'paste'}
		<div class="space-y-2">
			<textarea
				bind:value={pasteText}
				placeholder={"Paste portfolio di sini. Format per baris:\nBBCA 10 9500\nTLKM 5 3200\nANTM 20 1500"}
				rows="4"
				class="w-full rounded-lg border border-gray-300 bg-white p-3 font-mono text-sm placeholder:font-sans placeholder:text-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-terminal-border dark:bg-terminal-bg dark:text-terminal-text dark:placeholder:text-terminal-dim dark:focus:border-amber-500"
				{disabled}
			></textarea>
			<div class="flex items-center gap-3">
				<button
					onclick={parsePasteText}
					class="flex items-center gap-1.5 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-amber-500/25 transition-all hover:bg-amber-700 active:scale-[0.98]"
					{disabled}
				>
					Parse Portfolio
				</button>
				<p class="text-xs text-gray-400 dark:text-terminal-dim">
					Format: TICKER LOT HARGA_BELI (spasi/tab/koma)
				</p>
				{#if parseMessage}
					<span class="text-xs font-semibold text-amber-600 dark:text-amber-400">{parseMessage}</span>
				{/if}
			</div>
		</div>
	{/if}

	<!-- CSV upload -->
	{#if activeTab === 'csv'}
		<div
			class="rounded-xl border-2 border-dashed border-gray-300 bg-white p-6 text-center transition-all hover:border-amber-400 hover:bg-amber-50/50 dark:border-terminal-border dark:bg-terminal-surface dark:hover:border-amber-500/50 dark:hover:bg-amber-900/5"
		>
			<svg class="mx-auto mb-2 h-8 w-8 text-amber-500/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
			</svg>
			<p class="mb-2 text-sm text-gray-600 dark:text-terminal-muted">Upload file CSV atau TXT</p>
			<label
				class="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-amber-500/25 transition-all hover:bg-amber-700 active:scale-[0.98]"
			>
				Pilih File
				<input type="file" accept=".csv,.txt" class="hidden" onchange={handleFileUpload} {disabled} />
			</label>
			<p class="mt-2 text-[10px] text-gray-400 dark:text-terminal-dim">Format: TICKER,LOT,HARGA_BELI per baris</p>
		</div>
	{/if}

	<!-- Holdings table -->
	{#if holdings.length > 0}
		<div class="rounded-xl border border-gray-200 dark:border-terminal-border">
			<div class="flex items-center justify-between border-b border-gray-200 px-4 py-2 dark:border-terminal-border">
				<span class="text-xs font-semibold text-gray-500 dark:text-terminal-muted">
					{holdings.length} saham dalam portfolio
				</span>
				<button
					onclick={clearAll}
					class="text-[10px] font-semibold text-red-500 hover:text-red-700 dark:hover:text-red-400"
					{disabled}
				>
					Hapus Semua
				</button>
			</div>
			<div class="max-h-48 overflow-y-auto">
				<table class="w-full text-xs">
					<thead>
						<tr class="border-b border-gray-100 text-left dark:border-terminal-border">
							<th class="px-4 py-2 font-semibold text-gray-400 dark:text-terminal-dim">Ticker</th>
							<th class="px-4 py-2 text-right font-semibold text-gray-400 dark:text-terminal-dim">Lot</th>
							<th class="px-4 py-2 text-right font-semibold text-gray-400 dark:text-terminal-dim">Avg Beli</th>
							<th class="px-4 py-2 text-right font-semibold text-gray-400 dark:text-terminal-dim">Invested</th>
							<th class="w-8"></th>
						</tr>
					</thead>
					<tbody>
						{#each holdings as h, i}
							<tr class="border-b border-gray-50 dark:border-terminal-border/50">
								<td class="px-4 py-1.5 font-mono font-bold text-gray-900 dark:text-terminal-text">{h.ticker}</td>
								<td class="px-4 py-1.5 text-right font-mono text-gray-600 dark:text-terminal-muted">{h.lot}</td>
								<td class="px-4 py-1.5 text-right font-mono text-gray-600 dark:text-terminal-muted">{fmt(h.avg_price)}</td>
								<td class="px-4 py-1.5 text-right font-mono text-gray-600 dark:text-terminal-muted">
									Rp {fmt(h.avg_price * h.lot * 100)}
								</td>
								<td class="px-2 py-1.5">
									<button
										onclick={() => removeHolding(i)}
										class="rounded p-0.5 text-gray-300 transition-colors hover:text-red-500 dark:text-terminal-dim dark:hover:text-red-400"
										aria-label="Hapus {h.ticker}"
										{disabled}
									>
										<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
										</svg>
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
