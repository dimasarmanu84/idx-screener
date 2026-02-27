<script lang="ts">
	import ModeGuide from '$lib/components/ModeGuide.svelte';

	const modes = [
		{
			id: 'bsjp',
			title: 'BSJP',
			subtitle: 'Beli Sore Jual Pagi',
			desc: 'Screening overnight: beli sore 14:00-15:50, jual besok pagi 09:00-10:00',
			features: ['ATR + Pivot Points', 'RSI + MACD + ADX', 'Volume + Bollinger', 'SL/ATR Tightness'],
			icon: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z',
			color: 'blue',
			href: '/bsjp'
		},
		{
			id: 'intraday',
			title: 'Intraday',
			subtitle: 'Beli Pagi Jual Sore',
			desc: 'Day trading: beli pagi 09:15-10:00, jual sore 15:00-15:50',
			features: ['Filter likuiditas ketat', 'Momentum kuat', 'Cap SL 2%', 'R:R min 1:2'],
			icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z',
			color: 'green',
			href: '/intraday'
		},
		{
			id: 'swing',
			title: 'Swing Trading',
			subtitle: 'Saham Syariah',
			desc: 'Swing trading: hold beberapa hari-minggu, fokus breakout Stage 1 -> 2',
			features: ['Stage Analysis (Weinstein)', 'Fibonacci Retracement', 'Chart Patterns', 'Minervini SL (max 8%)'],
			icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
			color: 'purple',
			href: '/swing'
		},
		{
			id: 'night-scanner',
			title: 'Night Scanner',
			subtitle: 'Prediksi Top Gainer',
			desc: 'Prediksi saham yang berpotensi naik besok — analisis volume, breakout, dan momentum malam hari',
			features: ['Volume Accumulation', 'Near Breakout Detection', 'Momentum + MFI Score', 'Watchlist only — konfirmasi pagi'],
			icon: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z',
			color: 'indigo',
			href: '/night-scanner'
		},
		{
			id: 'portfolio',
			title: 'Portfolio',
			subtitle: 'Hold / Jual Signal',
			desc: 'Input portfolio, dapatkan sinyal HOLD/JUAL/CUT LOSS berdasarkan analisis teknikal',
			features: ['Input manual/paste/CSV', 'Sinyal Teknikal', 'Stage + MA50 Analysis', 'SL/TP monitoring'],
			icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
			color: 'amber',
			href: '/portfolio'
		}
	];

	const colorMap: Record<string, { border: string; icon: string; btn: string; glow: string }> = {
		blue: {
			border: 'border-gray-200 hover:border-blue-400 dark:border-terminal-border dark:hover:border-blue-500/50',
			icon: 'bg-blue-500/10 text-blue-500',
			btn: 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/25',
			glow: 'dark:hover:shadow-blue-500/5'
		},
		green: {
			border: 'border-gray-200 hover:border-green-400 dark:border-terminal-border dark:hover:border-green-500/50',
			icon: 'bg-green-500/10 text-green-500',
			btn: 'bg-green-600 hover:bg-green-700 text-white shadow-green-500/25',
			glow: 'dark:hover:shadow-green-500/5'
		},
		purple: {
			border: 'border-gray-200 hover:border-purple-400 dark:border-terminal-border dark:hover:border-purple-500/50',
			icon: 'bg-purple-500/10 text-purple-500',
			btn: 'bg-purple-600 hover:bg-purple-700 text-white shadow-purple-500/25',
			glow: 'dark:hover:shadow-purple-500/5'
		},
		red: {
			border: 'border-gray-200 hover:border-red-400 dark:border-terminal-border dark:hover:border-red-500/50',
			icon: 'bg-red-500/10 text-red-500',
			btn: 'bg-red-600 hover:bg-red-700 text-white shadow-red-500/25',
			glow: 'dark:hover:shadow-red-500/5'
		},
		indigo: {
			border: 'border-gray-200 hover:border-indigo-400 dark:border-terminal-border dark:hover:border-indigo-500/50',
			icon: 'bg-indigo-500/10 text-indigo-500',
			btn: 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-500/25',
			glow: 'dark:hover:shadow-indigo-500/5'
		},
		amber: {
			border: 'border-gray-200 hover:border-amber-400 dark:border-terminal-border dark:hover:border-amber-500/50',
			icon: 'bg-amber-500/10 text-amber-500',
			btn: 'bg-amber-600 hover:bg-amber-700 text-white shadow-amber-500/25',
			glow: 'dark:hover:shadow-amber-500/5'
		}
	};
</script>

<div class="py-4 md:py-10">
	<!-- Header -->
	<div class="mb-4 text-center md:mb-10">
		<div class="mb-2 inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-600 md:mb-4 md:gap-2 md:px-3 md:py-1 md:text-xs dark:border-blue-500/20 dark:bg-blue-900/10 dark:text-blue-400">
			<span class="h-1 w-1 rounded-full bg-blue-500 md:h-1.5 md:w-1.5"></span>
			Auto-screening saham Indonesia
		</div>
		<div class="flex items-center justify-center gap-2">
			<h1 class="text-2xl font-extrabold tracking-tight text-gray-900 md:text-4xl dark:text-terminal-text sm:md:text-5xl">
				IDX<span class="text-blue-500">Screener</span>
			</h1>
			<ModeGuide mode="general" />
		</div>
		<p class="mx-auto mt-1 hidden max-w-md text-sm text-gray-500 md:mt-3 md:block dark:text-terminal-muted">
			Formula teknikal canggih untuk BSJP, Intraday, dan Swing Trading saham Indonesia
		</p>
	</div>

	<!-- Mode cards -->
	<div class="grid gap-2.5 md:grid-cols-2 md:gap-5 lg:grid-cols-4">
		{#each modes as mode}
			{@const c = colorMap[mode.color]}
			<div
				class="group rounded-xl border bg-white p-3 transition-all duration-200 hover:shadow-lg md:rounded-2xl md:p-6 {c.border} {c.glow} dark:bg-terminal-surface"
			>
				<!-- Icon + Title -->
				<div class="mb-2 flex items-center gap-2.5 md:mb-4 md:gap-3">
					<div class="flex h-8 w-8 items-center justify-center rounded-lg md:h-10 md:w-10 md:rounded-xl {c.icon}">
						<svg class="h-4 w-4 md:h-5 md:w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d={mode.icon} />
						</svg>
					</div>
					<div>
						<h2 class="text-sm font-bold text-gray-900 md:text-lg dark:text-terminal-text">{mode.title}</h2>
						<p class="text-[10px] text-gray-400 md:text-xs dark:text-terminal-dim">{mode.subtitle}</p>
					</div>
				</div>

				<p class="mb-2 text-[11px] leading-relaxed text-gray-600 md:mb-4 md:text-sm dark:text-terminal-muted">{mode.desc}</p>

				<ul class="mb-3 space-y-1 md:mb-5 md:space-y-2">
					{#each mode.features as feature}
						<li class="flex items-center gap-1.5 text-[10px] text-gray-500 md:gap-2 md:text-xs dark:text-terminal-muted">
							<svg class="h-3 w-3 shrink-0 text-green-500 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
							</svg>
							{feature}
						</li>
					{/each}
				</ul>

				<a
					href={mode.href}
					class="flex items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-semibold shadow-sm transition-all active:scale-[0.98] md:gap-2 md:rounded-xl md:px-4 md:py-2.5 md:text-sm {c.btn}"
				>
					{mode.id === 'portfolio' ? 'Buka Portfolio' : mode.id === 'night-scanner' ? 'Mulai Scan Malam' : 'Mulai Screening'}
					<svg class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
				</a>
			</div>
		{/each}
	</div>

	<!-- Timing Guidance -->
	<div class="mt-4 md:mt-10">
		<div class="mb-2 flex items-center gap-2 md:mb-4">
			<svg class="h-4 w-4 text-gray-500 md:h-5 md:w-5 dark:text-terminal-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<h2 class="text-sm font-bold text-gray-900 md:text-lg dark:text-terminal-text">Kapan Harus Screening?</h2>
		</div>

		<div class="grid gap-2 md:grid-cols-2 md:gap-3 lg:grid-cols-3">
			<!-- BSJP -->
			<div class="rounded-lg border border-gray-200 bg-white p-2.5 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="mb-1.5 flex items-center gap-2 md:mb-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-md bg-blue-500/10 text-blue-500 md:h-7 md:w-7 md:rounded-lg">
						<svg class="h-3 w-3 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
						</svg>
					</span>
					<span class="text-xs font-bold text-gray-900 md:text-sm dark:text-terminal-text">BSJP</span>
				</div>
				<div class="space-y-1 text-[10px] md:text-xs">
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">14:00 - 15:30</span> — Waktu terbaik scan & entry</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-yellow-600 dark:text-yellow-400">13:00 - 14:00</span> — Bisa scan awal, data belum final</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-red-500">Pagi / Malam</span> — Jangan scan, data belum update</span>
					</div>
				</div>
			</div>

			<!-- Intraday -->
			<div class="rounded-lg border border-gray-200 bg-white p-2.5 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="mb-1.5 flex items-center gap-2 md:mb-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-md bg-green-500/10 text-green-500 md:h-7 md:w-7 md:rounded-lg">
						<svg class="h-3 w-3 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
						</svg>
					</span>
					<span class="text-xs font-bold text-gray-900 md:text-sm dark:text-terminal-text">Intraday</span>
				</div>
				<div class="space-y-1 text-[10px] md:text-xs">
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">09:15 - 10:00</span> — Waktu terbaik scan & entry</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-yellow-600 dark:text-yellow-400">10:00 - 13:00</span> — Masih bisa, tapi momentum berkurang</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-red-500">Sore / Malam</span> — Jangan scan, market sudah tutup</span>
					</div>
				</div>
			</div>

			<!-- Swing -->
			<div class="rounded-lg border border-gray-200 bg-white p-2.5 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="mb-1.5 flex items-center gap-2 md:mb-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-md bg-purple-500/10 text-purple-500 md:h-7 md:w-7 md:rounded-lg">
						<svg class="h-3 w-3 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
						</svg>
					</span>
					<span class="text-xs font-bold text-gray-900 md:text-sm dark:text-terminal-text">Swing Trading</span>
				</div>
				<div class="space-y-1 text-[10px] md:text-xs">
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">Setelah 16:00</span> — Terbaik, data EOD sudah lengkap</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-yellow-600 dark:text-yellow-400">Jam market</span> — Bisa scan, tapi candle belum final</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">Weekend</span> — Bisa scan, data Jumat masih valid</span>
					</div>
				</div>
			</div>

			<!-- Night Scanner -->
			<div class="rounded-lg border border-gray-200 bg-white p-2.5 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="mb-1.5 flex items-center gap-2 md:mb-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-500/10 text-indigo-500 md:h-7 md:w-7 md:rounded-lg">
						<svg class="h-3 w-3 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
						</svg>
					</span>
					<span class="text-xs font-bold text-gray-900 md:text-sm dark:text-terminal-text">Night Scanner</span>
				</div>
				<div class="space-y-1 text-[10px] md:text-xs">
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">19:00 - 23:00</span> — Waktu terbaik, data EOD lengkap</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-yellow-600 dark:text-yellow-400">16:00 - 19:00</span> — Bisa, tapi data mungkin delay</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-red-500">Jam market</span> — Jangan scan, ini untuk prediksi besok</span>
					</div>
				</div>
			</div>

			<!-- Portfolio -->
			<div class="rounded-lg border border-gray-200 bg-white p-2.5 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-surface">
				<div class="mb-1.5 flex items-center gap-2 md:mb-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-md bg-amber-500/10 text-amber-500 md:h-7 md:w-7 md:rounded-lg">
						<svg class="h-3 w-3 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
						</svg>
					</span>
					<span class="text-xs font-bold text-gray-900 md:text-sm dark:text-terminal-text">Portfolio</span>
				</div>
				<div class="space-y-1 text-[10px] md:text-xs">
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">Kapan saja</span> — Bisa cek kapanpun</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-green-600 dark:text-green-400">Setelah 16:00</span> — Terbaik untuk keputusan hold/jual</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-500"></span>
						<span class="text-gray-600 dark:text-terminal-muted"><span class="font-semibold text-yellow-600 dark:text-yellow-400">Jam market</span> — Data realtime tapi belum final</span>
					</div>
				</div>
			</div>

			<!-- Tips -->
			<div class="rounded-lg border border-dashed border-gray-300 bg-gray-50/50 p-2.5 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-bg">
				<div class="mb-1.5 flex items-center gap-2 md:mb-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-md bg-gray-500/10 text-gray-500 md:h-7 md:w-7 md:rounded-lg dark:text-terminal-muted">
						<svg class="h-3 w-3 md:h-3.5 md:w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					</span>
					<span class="text-xs font-bold text-gray-900 md:text-sm dark:text-terminal-text">Tips</span>
				</div>
				<div class="space-y-1 text-[10px] md:text-xs">
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-400"></span>
						<span class="text-gray-600 dark:text-terminal-muted">Night Scanner = watchlist saja, konfirmasi pakai BSJP/Intraday pagi</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-400"></span>
						<span class="text-gray-600 dark:text-terminal-muted">Weekend & libur: hanya Swing & Portfolio yang relevan</span>
					</div>
					<div class="flex items-start gap-1.5">
						<span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-400"></span>
						<span class="text-gray-600 dark:text-terminal-muted">Data Yahoo Finance delay ~15 menit saat market buka</span>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- UP Days Legend (Night Scanner) -->
	<div class="mt-4 rounded-lg border border-indigo-200 bg-indigo-50/50 p-2.5 md:mt-6 md:rounded-xl md:p-4 dark:border-indigo-500/20 dark:bg-indigo-900/10">
		<div class="mb-1.5 flex items-center gap-2 md:mb-3">
			<svg class="h-4 w-4 text-indigo-500 md:h-5 md:w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
			</svg>
			<h2 class="text-sm font-bold text-gray-900 md:text-lg dark:text-terminal-text">Kolom UP — Night Scanner</h2>
			<span class="rounded bg-indigo-100 px-1.5 py-0.5 text-[8px] font-bold text-indigo-600 md:text-[10px] dark:bg-indigo-500/20 dark:text-indigo-400">Consecutive Up Days</span>
		</div>
		<div class="grid grid-cols-2 gap-x-4 gap-y-1.5 md:grid-cols-4 md:gap-x-6 md:gap-y-2">
			<div class="flex items-center gap-2">
				<span class="w-8 shrink-0 text-right font-mono text-[11px] font-bold text-green-600 md:text-xs dark:text-green-400">1d</span>
				<div>
					<span class="text-[10px] font-bold text-green-600 md:text-xs dark:text-green-400">IDEAL</span>
					<p class="text-[9px] text-gray-500 md:text-[10px] dark:text-terminal-dim">Baru mulai naik — timing entry bagus</p>
				</div>
			</div>
			<div class="flex items-center gap-2">
				<span class="w-8 shrink-0 text-right font-mono text-[11px] font-bold text-yellow-600 md:text-xs dark:text-yellow-400">2-4d</span>
				<div>
					<span class="text-[10px] font-bold text-yellow-600 md:text-xs dark:text-yellow-400">OK</span>
					<p class="text-[9px] text-gray-500 md:text-[10px] dark:text-terminal-dim">Momentum jalan — masih oke</p>
				</div>
			</div>
			<div class="flex items-center gap-2">
				<span class="w-8 shrink-0 text-right font-mono text-[11px] font-bold text-orange-500 md:text-xs dark:text-orange-400">5-10d</span>
				<div>
					<span class="text-[10px] font-bold text-orange-500 md:text-xs dark:text-orange-400">RISKY</span>
					<p class="text-[9px] text-gray-500 md:text-[10px] dark:text-terminal-dim">Hati-hati profit taking</p>
				</div>
			</div>
			<div class="flex items-center gap-2">
				<span class="w-8 shrink-0 text-right font-mono text-[11px] font-bold text-red-500 md:text-xs">11d+</span>
				<div>
					<span class="text-[10px] font-bold text-red-500 md:text-xs">TELAT</span>
					<p class="text-[9px] text-gray-500 md:text-[10px] dark:text-terminal-dim">Kemungkinan besar koreksi</p>
				</div>
			</div>
		</div>
	</div>

	<!-- Disclaimer -->
	<div class="mt-4 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 md:mt-6 md:rounded-xl md:p-4 dark:border-terminal-border dark:bg-terminal-surface">
		<p class="text-[10px] text-gray-500 md:text-xs dark:text-terminal-muted">
			<span class="font-semibold text-gray-700 dark:text-terminal-text">Disclaimer:</span>
			Untuk edukasi. Bukan ajakan beli/jual. DYOR.
		</p>
		<p class="mt-0.5 text-[10px] text-gray-400 md:mt-1 md:text-xs dark:text-terminal-dim">
			Data: Yahoo Finance (delay 15 menit).
		</p>
	</div>
</div>
