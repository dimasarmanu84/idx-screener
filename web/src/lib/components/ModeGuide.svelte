<script lang="ts">
	import type { ScreenerMode } from '$lib/types';

	let { mode = 'general' }: { mode: string } = $props();

	let open = $state(false);

	interface GuideSection {
		icon: string;
		title: string;
		items: string[];
	}

	interface ModeGuideData {
		title: string;
		subtitle: string;
		color: string;
		timing: string;
		sections: GuideSection[];
		tips: string[];
	}

	const guides: Record<string, ModeGuideData> = {
		bsjp: {
			title: 'BSJP — Beli Sore Jual Pagi',
			subtitle: 'Overnight trading: beli sore, jual besok pagi',
			color: 'blue',
			timing: 'Scan: 14:00-15:30 | Beli: 15:30-15:50 | Jual: 09:00-10:00',
			sections: [
				{
					icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Waktu Screening',
					items: [
						'Scan sore hari (14:00-15:30) saat data hampir final',
						'Beli di sesi akhir (15:30-15:50) jika sinyal BUY',
						'Jual besok pagi (09:00-10:00) saat opening gap'
					]
				},
				{
					icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Cara Baca Hasil',
					items: [
						'BUY = lolos semua filter teknikal, layak entry',
						'WATCH = hampir lolos, pantau besok',
						'Quality score = persentase rule yang terpenuhi',
						'R:R ratio > 1.5 = risk/reward bagus'
					]
				},
				{
					icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
					title: 'Risk Management',
					items: [
						'SL (Stop Loss) sudah otomatis dihitung',
						'SL ketat (< 1 ATR) = aman, SL longgar = hati-hati',
						'Max alokasi 5-10% per saham',
						'Jual pagi WAJIB, jangan hold > 1 hari'
					]
				}
			],
			tips: [
				'Gunakan grup LQ45 untuk pemula — paling likuid & aman',
				'Cek kolom SL/ATR — semakin rendah semakin ketat stop loss-nya',
				'Jangan entry jika market sedang crash (IHSG turun > 2%)'
			]
		},
		intraday: {
			title: 'Intraday — Beli Pagi Jual Sore',
			subtitle: 'Day trading: beli pagi, jual sore hari yang sama',
			color: 'green',
			timing: 'Scan: 09:15-09:30 | Beli: 09:15-10:00 | Jual: 14:30-15:50',
			sections: [
				{
					icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Waktu Screening',
					items: [
						'Scan pagi (09:15-09:30) setelah opening 15 menit',
						'Entry di momen momentum pagi (09:15-10:00)',
						'Exit di sesi sore (14:30-15:50) sebelum closing'
					]
				},
				{
					icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Cara Baca Hasil',
					items: [
						'Filter likuiditas lebih ketat dari BSJP',
						'SL maksimal 2% — cap risiko per trade',
						'R:R minimal 1:2 — target profit 2x risiko',
						'Volume harus di atas rata-rata 20 hari'
					]
				},
				{
					icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
					title: 'Risk Management',
					items: [
						'WAJIB jual di hari yang sama — jangan overnight',
						'Max 2% modal per posisi',
						'Jika hit SL, langsung cut — jangan average down',
						'Hindari saat market sideways / volatilitas rendah'
					]
				}
			],
			tips: [
				'Cocok untuk saham dengan momentum kuat dan volume tinggi',
				'Jangan trading intraday saat hari libur parsial (short session)',
				'Perhatikan spread bid-ask — spread > 1% kurang ideal'
			]
		},
		swing: {
			title: 'Swing Trading — Saham Syariah',
			subtitle: 'Hold beberapa hari hingga minggu, fokus breakout',
			color: 'purple',
			timing: 'Scan: kapan saja | Hold: 3 hari - 4 minggu | Saham: JII / JII70 / ISSI',
			sections: [
				{
					icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
					title: 'Stage Analysis (Weinstein)',
					items: [
						'Stage 1 (Basing) = akumulasi, belum breakout',
						'Stage 2 (Advancing) = uptrend, IDEAL untuk entry',
						'Stage 3 (Topping) = distribusi, hati-hati',
						'Stage 4 (Declining) = downtrend, JANGAN beli'
					]
				},
				{
					icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Cara Baca Hasil',
					items: [
						'Cari saham Stage 1 menuju 2 (breakout)',
						'Fibonacci level menunjukkan area support/resistance',
						'Chart pattern (Cup & Handle, dll) = konfirmasi breakout',
						'Volume breakout > rata-rata = sinyal kuat'
					]
				},
				{
					icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
					title: 'Risk Management',
					items: [
						'SL max 8% (metode Minervini)',
						'Entry bertahap — 50% awal, 50% saat konfirmasi',
						'Trailing stop saat sudah profit > 10%',
						'Saham syariah (JII/ISSI) — bebas riba'
					]
				}
			],
			tips: [
				'Paling cocok untuk trader yang tidak bisa pantau layar seharian',
				'Scan bisa dilakukan malam hari — tidak perlu real-time',
				'Fokus pada saham yang baru breakout dari Stage 1 ke Stage 2'
			]
		},
		'top-gainer': {
			title: 'Top Gainer — Saham Naik Tertinggi',
			subtitle: 'Scan MALAM H-1, eksekusi pagi. Bukan scan saat market buka!',
			color: 'red',
			timing: 'Scan: Malam 20:00-22:00 (H-1) | Entry: 09:00-09:30 | Hold: 1-2 hari max',
			sections: [
				{
					icon: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z',
					title: '1. Malam H-1 — Planning',
					items: [
						'Scan malam (20:00-22:00) pakai data closing — data paling bersih',
						'Filter: R:R >= 1.5, SL <= 8%, Jarak ARA >= 10%',
						'Pilih max 2 saham, catat Entry / SL / TP',
						'Screenshot trading plan — selesai, tidur'
					]
				},
				{
					icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
					title: '2. Pagi H — Checklist',
					items: [
						'08:50-09:00: Cek IHSG pre-open, merah >1%? Tunda 15 menit',
						'Cek harga pre-open watchlist',
						'Gap up >3% dari plan? SKIP, jangan kejar',
						'Harga sesuai plan? Siap eksekusi'
					]
				},
				{
					icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
					title: '3. Market Buka — Eksekusi',
					items: [
						'09:00-09:30: Harga <= entry level? BUY',
						'Langsung pasang SL setelah entry',
						'JANGAN buka screener lagi saat market jalan',
						'JANGAN cari saham baru — satu plan per hari'
					]
				},
				{
					icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
					title: '4. Sore — Evaluasi',
					items: [
						'14:00-15:00: Review posisi yang ada',
						'Scan screener untuk BESOK (bukan hari ini)',
						'Mulai planning cycle lagi untuk esok hari'
					]
				},
				{
					icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
					title: 'Kesalahan Umum',
					items: [
						'Scan saat market buka — data noise, harga belum settle',
						'Entry tanpa plan — kejar harga di atas max entry',
						'Buka screener siang — lihat saham lain naik, ganti plan',
						'FOMO — emosi tinggi, jangan trading tanpa plan'
					]
				},
				{
					icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Cara Baca Hasil',
					items: [
						'HOT = sangat dekat ARA, potensi tinggi tapi risiko besar',
						'WARM = momentum bagus, belum terlalu panas',
						'ENTRY = ada titik entry yang masuk akal',
						'Cek badge Fund (BC/MC/FD/SP) untuk keamanan'
					]
				}
			],
			tips: [
				'HIGH RISK — bisa langsung ARB besok (-25%). Max 1-2% modal',
				'Filter Fund: Blue Chip/Mid Cap untuk yang lebih aman',
				'Saham SP (Spekulatif) sangat berisiko — hindari jika pemula',
				'SL ketat wajib. Jika hit SL, cut — jangan average down'
			]
		},
		'night-scanner': {
			title: 'Night Scanner — Prediksi Top Gainer',
			subtitle: 'Scan malam hari, prediksi saham yang berpotensi naik besok',
			color: 'indigo',
			timing: 'Scan: 20:00-22:00 (malam) | Watchlist only | Konfirmasi: BSJP/Intraday pagi',
			sections: [
				{
					icon: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z',
					title: 'Konsep Night Scanner',
					items: [
						'Scan setelah market tutup — data end-of-day paling bersih',
						'Scoring 7 faktor: volume, breakout, momentum, price action, trend, MFI',
						'Hasil = WATCHLIST, bukan rekomendasi langsung beli',
						'Konfirmasi entry besok pagi pakai BSJP atau Intraday scanner'
					]
				},
				{
					icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Cara Baca Label',
					items: [
						'PRIME (>=70) = kandidat kuat, banyak faktor terpenuhi',
						'READY (50-69) = potensial, perlu konfirmasi besok',
						'WATCH (<50) = perlu perhatian lebih, belum cukup sinyal',
						'Catalyst = alasan utama kenapa saham masuk watchlist'
					]
				},
				{
					icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
					title: 'Faktor Scoring',
					items: [
						'Volume Accumulation — volume naik 3 hari berturut + stealth buying',
						'Near Breakout — harga dekat 20-day high + BB squeeze',
						'Momentum — MACD positif + RSI sweet spot (50-70)',
						'Trend Alignment — close > EMA20 > EMA50'
					]
				},
				{
					icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
					title: 'Cara Pakai',
					items: [
						'Scan malam setelah market tutup (20:00+)',
						'Catat 2-3 saham PRIME sebagai watchlist besok',
						'Pagi: konfirmasi pakai BSJP/Intraday scanner',
						'JANGAN langsung beli tanpa konfirmasi pagi'
					]
				}
			],
			tips: [
				'Night Scanner = watchlist builder, BUKAN signal langsung beli',
				'Kombinasi terbaik: Night Scanner malam + BSJP/Intraday pagi',
				'Saham PRIME belum tentu naik — selalu tunggu konfirmasi teknikal pagi',
				'Gunakan all_stocks untuk scan komprehensif, LQ45 untuk pemula'
			]
		},
		general: {
			title: 'Panduan IDXScreener',
			subtitle: 'Pilih mode screening yang sesuai gaya trading Anda',
			color: 'blue',
			timing: '',
			sections: [
				{
					icon: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z',
					title: 'Pilih Mode yang Tepat',
					items: [
						'BSJP — beli sore, jual pagi. Cocok untuk pekerja kantoran',
						'Intraday — beli pagi, jual sore. Butuh pantau layar',
						'Swing — hold hari-minggu. Saham syariah, paling santai',
						'Top Gainer — saham naik tertinggi. High risk high reward',
						'Night Scanner — prediksi top gainer malam hari (watchlist)'
					]
				},
				{
					icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
					title: 'Waktu Terbaik Screening',
					items: [
						'BSJP: scan sore (14:00-15:30), beli sore, jual pagi',
						'Intraday: scan pagi (09:15), beli pagi, jual sore',
						'Swing: scan kapan saja, hold beberapa hari-minggu',
						'Top Gainer: scan MALAM H-1 (20:00), eksekusi pagi',
						'Night Scanner: scan malam (20:00), watchlist besok'
					]
				},
				{
					icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
					title: 'Tips Umum',
					items: [
						'Mulai dari LQ45 — paling aman & likuid',
						'Selalu patuhi SL (Stop Loss) yang diberikan',
						'Max 5% modal per posisi untuk pemula',
						'Portfolio mode untuk monitor saham yang sudah dibeli'
					]
				}
			],
			tips: [
				'Data dari Yahoo Finance (delay 15 menit) — bukan real-time',
				'Ini alat bantu edukasi, bukan rekomendasi beli/jual',
				'DYOR — Do Your Own Research sebelum trading'
			]
		}
	};

	const colorMap: Record<string, { bg: string; border: string; text: string; badge: string; btnBg: string }> = {
		blue: {
			bg: 'bg-blue-50 dark:bg-blue-900/10',
			border: 'border-blue-200 dark:border-blue-500/30',
			text: 'text-blue-700 dark:text-blue-400',
			badge: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
			btnBg: 'bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400'
		},
		green: {
			bg: 'bg-green-50 dark:bg-green-900/10',
			border: 'border-green-200 dark:border-green-500/30',
			text: 'text-green-700 dark:text-green-400',
			badge: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
			btnBg: 'bg-green-500/10 hover:bg-green-500/20 text-green-600 dark:text-green-400'
		},
		purple: {
			bg: 'bg-purple-50 dark:bg-purple-900/10',
			border: 'border-purple-200 dark:border-purple-500/30',
			text: 'text-purple-700 dark:text-purple-400',
			badge: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400',
			btnBg: 'bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 dark:text-purple-400'
		},
		red: {
			bg: 'bg-red-50 dark:bg-red-900/10',
			border: 'border-red-200 dark:border-red-500/30',
			text: 'text-red-700 dark:text-red-400',
			badge: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400',
			btnBg: 'bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400'
		},
		indigo: {
			bg: 'bg-indigo-50 dark:bg-indigo-900/10',
			border: 'border-indigo-200 dark:border-indigo-500/30',
			text: 'text-indigo-700 dark:text-indigo-400',
			badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-400',
			btnBg: 'bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400'
		}
	};

	let guide = $derived(guides[mode] || guides.general);
	let c = $derived(colorMap[guide.color] || colorMap.blue);

	function handleClickOutside(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (!target.closest('.mode-guide-wrapper')) {
			open = false;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="mode-guide-wrapper relative inline-flex">
	<!-- Trigger button -->
	<button
		type="button"
		onclick={() => (open = !open)}
		class="flex h-7 w-7 items-center justify-center rounded-lg transition-colors md:h-8 md:w-8 {c.btnBg}"
		title="Panduan penggunaan"
	>
		<svg class="h-3.5 w-3.5 md:h-4 md:w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
		</svg>
	</button>

	<!-- Popover panel -->
	{#if open}
		<div class="absolute left-0 top-full z-50 mt-2 w-[340px] overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl md:w-[400px] dark:border-terminal-border dark:bg-terminal-bg">
			<!-- Header -->
			<div class="border-b px-4 py-3 {c.bg} {c.border}">
				<h3 class="text-sm font-bold {c.text}">{guide.title}</h3>
				<p class="mt-0.5 text-[11px] text-gray-500 dark:text-terminal-muted">{guide.subtitle}</p>
				{#if guide.timing}
					<div class="mt-2 rounded-md {c.badge} px-2 py-1 text-[10px] font-semibold">
						{guide.timing}
					</div>
				{/if}
			</div>

			<!-- Content -->
			<div class="max-h-[60vh] overflow-y-auto">
				<!-- Sections -->
				{#each guide.sections as section, si}
					<div class="border-b border-gray-100 px-4 py-3 dark:border-terminal-border {si === guide.sections.length - 1 ? 'border-b-0' : ''}">
						<div class="mb-1.5 flex items-center gap-2">
							<div class="flex h-5 w-5 items-center justify-center rounded-md {c.badge}">
								<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={section.icon} />
								</svg>
							</div>
							<span class="text-xs font-bold text-gray-800 dark:text-terminal-text">{section.title}</span>
						</div>
						<ul class="space-y-1 pl-7">
							{#each section.items as item}
								<li class="flex items-start gap-1.5 text-[11px] leading-snug text-gray-600 dark:text-terminal-muted">
									<span class="mt-1 h-1 w-1 shrink-0 rounded-full bg-gray-300 dark:bg-terminal-dim"></span>
									{item}
								</li>
							{/each}
						</ul>
					</div>
				{/each}

				<!-- Tips -->
				{#if guide.tips.length > 0}
					<div class="border-t border-gray-100 px-4 py-3 dark:border-terminal-border">
						<div class="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-terminal-dim">Pro Tips</div>
						<ul class="space-y-1">
							{#each guide.tips as tip}
								<li class="flex items-start gap-1.5 text-[11px] leading-snug text-gray-600 dark:text-terminal-muted">
									<span class="mt-0.5 shrink-0 text-[10px] {c.text}">*</span>
									{tip}
								</li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="border-t border-gray-100 px-4 py-2 dark:border-terminal-border">
				<button
					type="button"
					onclick={() => (open = false)}
					class="w-full rounded-lg bg-gray-100 py-1.5 text-[11px] font-semibold text-gray-600 transition-colors hover:bg-gray-200 dark:bg-terminal-surface dark:text-terminal-muted dark:hover:bg-terminal-surface-hover"
				>
					Tutup
				</button>
			</div>
		</div>
	{/if}
</div>
