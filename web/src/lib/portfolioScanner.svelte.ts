import { analyzePortfolio, checkTelegramStatus, sendTelegramAlert } from './api';
import type { PortfolioHolding, PortfolioAlert, ToastItem } from './types';

// ── Reactive state (single object — never reassigned, only properties mutated) ──
const BADGE_KEY = 'screener_portfolio_badge';

function loadBadgeCount(): number {
	try {
		return parseInt(localStorage.getItem(BADGE_KEY) || '0', 10) || 0;
	} catch {
		return 0;
	}
}

const NOTIF_PERM_KEY = 'screener_notif_enabled';
const TG_ENABLED_KEY = 'screener_telegram_enabled';

let scanner = $state({
	alertBadgeCount: loadBadgeCount(),
	toasts: [] as ToastItem[],
	isScanning: false,
	lastScanTime: null as number | null,
	notifEnabled: typeof window !== 'undefined' && localStorage.getItem(NOTIF_PERM_KEY) === '1',
	telegramConfigured: false,
	telegramEnabled: typeof window !== 'undefined' && localStorage.getItem(TG_ENABLED_KEY) === '1'
});

// ── Previous signals cache (localStorage) ──
const STORAGE_KEY = 'screener_portfolio';
const SIGNAL_CACHE_KEY = 'screener_portfolio_signals';

function loadPreviousSignals(): Record<string, string> {
	try {
		const raw = localStorage.getItem(SIGNAL_CACHE_KEY);
		return raw ? JSON.parse(raw) : {};
	} catch {
		return {};
	}
}

function savePreviousSignals(signals: Record<string, string>) {
	localStorage.setItem(SIGNAL_CACHE_KEY, JSON.stringify(signals));
}

// ── Browser notification ──
async function requestNotifPermission(): Promise<boolean> {
	if (!('Notification' in window)) return false;
	if (Notification.permission === 'granted') {
		scanner.notifEnabled = true;
		localStorage.setItem(NOTIF_PERM_KEY, '1');
		return true;
	}
	if (Notification.permission === 'denied') return false;
	const result = await Notification.requestPermission();
	const granted = result === 'granted';
	scanner.notifEnabled = granted;
	localStorage.setItem(NOTIF_PERM_KEY, granted ? '1' : '0');
	return granted;
}

function toggleNotif(enabled: boolean) {
	scanner.notifEnabled = enabled;
	localStorage.setItem(NOTIF_PERM_KEY, enabled ? '1' : '0');
}

function sendBrowserNotification(alerts: PortfolioAlert[]) {
	if (!scanner.notifEnabled || Notification.permission !== 'granted') return;

	const top = alerts[0];
	const tickers = alerts.map((a) => a.ticker).join(', ');
	const title = alerts.length === 1
		? `${top.ticker} — ${top.signalLabel}`
		: `${alerts.length} Sinyal Jual`;
	const body = alerts.length === 1
		? `${top.reason} (${top.pnlPct >= 0 ? '+' : ''}${top.pnlPct.toFixed(1)}%)`
		: `${tickers}`;

	const notif = new Notification(title, {
		body,
		icon: '/icons/icon-192.png',
		tag: 'portfolio-alert'
	});

	notif.onclick = () => {
		window.focus();
		window.location.href = '/portfolio';
		notif.close();
	};
}

// ── Signal change detection ──
const SELL_SIGNALS = new Set([
	'CUT_LOSS',
	'JUAL_SEMUA',
	'JUAL_SEBAGIAN',
	'JUAL_KURANGI',
	'SIAP_JUAL',
	'PERTIMBANGKAN_JUAL'
]);

function detectChanges(
	holdings: Array<{
		ticker: string;
		signal: { code: string; label: string; severity: number; reason: string };
		pnl_pct: number;
	}>,
	previousSignals: Record<string, string>
): PortfolioAlert[] {
	const alerts: PortfolioAlert[] = [];

	for (const h of holdings) {
		const code = h.signal.code;
		if (!SELL_SIGNALS.has(code)) continue;

		const prev = previousSignals[h.ticker] ?? null;

		// Only alert if signal is new or changed
		if (prev !== code) {
			alerts.push({
				ticker: h.ticker,
				signalCode: code,
				signalLabel: h.signal.label,
				severity: h.signal.severity,
				reason: h.signal.reason,
				pnlPct: h.pnl_pct,
				previousSignalCode: prev
			});
		}
	}

	alerts.sort((a, b) => a.severity - b.severity);
	return alerts;
}

// ── Core scan function ──
async function runBackgroundScan(): Promise<void> {
	if (scanner.isScanning) return;

	const raw = localStorage.getItem(STORAGE_KEY);
	if (!raw) return;

	let holdings: PortfolioHolding[];
	try {
		holdings = JSON.parse(raw);
	} catch {
		return;
	}
	if (!holdings.length) return;

	scanner.isScanning = true;

	try {
		const result = await analyzePortfolio(holdings);
		const previousSignals = loadPreviousSignals();
		const alerts = detectChanges(result.holdings, previousSignals);

		// Update cache for next comparison
		const newSignals: Record<string, string> = {};
		for (const h of result.holdings) {
			newSignals[h.ticker] = h.signal.code;
		}
		savePreviousSignals(newSignals);

		// Show toast + badge + browser notification if new/changed sell alerts
		if (alerts.length > 0) {
			const toast: ToastItem = {
				id: crypto.randomUUID(),
				alerts,
				timestamp: Date.now()
			};
			scanner.toasts = [...scanner.toasts, toast];
			scanner.alertBadgeCount = alerts.length;
			localStorage.setItem(BADGE_KEY, String(alerts.length));
			sendBrowserNotification(alerts);

			// Telegram notification
			if (scanner.telegramEnabled && scanner.telegramConfigured) {
				sendTelegramAlert(
					alerts.map((a) => ({
						ticker: a.ticker,
						signalCode: a.signalCode,
						signalLabel: a.signalLabel,
						reason: a.reason,
						pnlPct: a.pnlPct
					}))
				);
			}
		}

		scanner.lastScanTime = Date.now();
	} catch {
		// Silent fail for background scan
	} finally {
		scanner.isScanning = false;
	}
}

// ── Toast management ──
function dismissToast(id: string) {
	scanner.toasts = scanner.toasts.filter((t) => t.id !== id);
}

function clearBadge() {
	scanner.alertBadgeCount = 0;
	localStorage.removeItem(BADGE_KEY);
}

// ── Telegram toggle ──
function toggleTelegram(enabled: boolean) {
	scanner.telegramEnabled = enabled;
	localStorage.setItem(TG_ENABLED_KEY, enabled ? '1' : '0');
}

async function initTelegram() {
	try {
		const { configured } = await checkTelegramStatus();
		scanner.telegramConfigured = configured;
	} catch {
		scanner.telegramConfigured = false;
	}
}

// ── Interval management ──
let intervalId: ReturnType<typeof setInterval> | null = null;
const SCAN_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

function startScanner(isMarketOpen: boolean) {
	stopScanner();

	// Check Telegram config
	initTelegram();

	// Always run once on start (check signals even after market close)
	runBackgroundScan();

	// Only set up periodic scanning when market is open
	if (isMarketOpen) {
		intervalId = setInterval(() => {
			runBackgroundScan();
		}, SCAN_INTERVAL_MS);
	}
}

function stopScanner() {
	if (intervalId) {
		clearInterval(intervalId);
		intervalId = null;
	}
}

// ── Public exports ──
export {
	scanner,
	dismissToast,
	clearBadge,
	startScanner,
	stopScanner,
	requestNotifPermission,
	toggleNotif,
	toggleTelegram
};
