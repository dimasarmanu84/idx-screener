import type { ScreeningResponse, MarketStatus, PortfolioHolding, PortfolioResponse, PortfolioStockResult, StockResult } from './types';

const API_BASE = '/api';

export async function fetchMarketStatus(): Promise<MarketStatus> {
	const res = await fetch(`${API_BASE}/market-status`);
	return res.json();
}

export async function fetchStockLists(): Promise<Record<string, number>> {
	const res = await fetch(`${API_BASE}/stock-lists`);
	return res.json();
}

export async function runScreener(
	mode: string,
	stocks: string
): Promise<ScreeningResponse> {
	const res = await fetch(`${API_BASE}/screener/${mode}?stocks=${stocks}`);
	if (!res.ok) throw new Error(`Screening failed: ${res.statusText}`);
	return res.json();
}

export function streamScreener(
	mode: string,
	stocks: string,
	onProgress: (current: number, total: number, ticker: string) => void,
	onComplete: (data: ScreeningResponse) => void,
	onError: (error: string) => void,
	options?: { smallcap?: boolean },
	onResult?: (stock: StockResult) => void
): () => void {
	let url = `${API_BASE}/screener/${mode}/stream?stocks=${stocks}`;
	if (options?.smallcap) url += '&smallcap=true';
	const es = new EventSource(url);

	es.onmessage = (event) => {
		const msg = JSON.parse(event.data);
		if (msg.type === 'progress') {
			onProgress(msg.current, msg.total, msg.ticker);
		} else if (msg.type === 'result' && onResult) {
			onResult(msg.stock);
		} else if (msg.type === 'complete') {
			onComplete(msg.data);
			es.close();
		} else if (msg.type === 'error') {
			onError(msg.message);
			es.close();
		}
	};

	es.onerror = () => {
		onError('Koneksi terputus');
		es.close();
	};

	return () => es.close();
}

export function streamAraHunter(
	stocks: string,
	onProgress: (current: number, total: number, ticker: string) => void,
	onComplete: (data: ScreeningResponse) => void,
	onError: (error: string) => void
): () => void {
	const url = `${API_BASE}/ara-hunter/stream?stocks=${stocks}`;
	const es = new EventSource(url);

	es.onmessage = (event) => {
		const msg = JSON.parse(event.data);
		if (msg.type === 'progress') {
			onProgress(msg.current, msg.total, msg.ticker);
		} else if (msg.type === 'complete') {
			onComplete(msg.data);
			es.close();
		} else if (msg.type === 'error') {
			onError(msg.message);
			es.close();
		}
	};

	es.onerror = () => {
		onError('Koneksi terputus');
		es.close();
	};

	return () => es.close();
}

export function streamNightScanner(
	stocks: string,
	onProgress: (current: number, total: number, ticker: string) => void,
	onComplete: (data: ScreeningResponse) => void,
	onError: (error: string) => void,
	onResult?: (stock: StockResult) => void
): () => void {
	const url = `${API_BASE}/night-scanner/stream?stocks=${stocks}`;
	const es = new EventSource(url);

	es.onmessage = (event) => {
		const msg = JSON.parse(event.data);
		if (msg.type === 'progress') {
			onProgress(msg.current, msg.total, msg.ticker);
		} else if (msg.type === 'result' && onResult) {
			onResult(msg.stock);
		} else if (msg.type === 'complete') {
			onComplete(msg.data);
			es.close();
		} else if (msg.type === 'error') {
			onError(msg.message);
			es.close();
		}
	};

	es.onerror = () => {
		onError('Koneksi terputus');
		es.close();
	};

	return () => es.close();
}

export async function analyzePortfolio(
	holdings: PortfolioHolding[]
): Promise<PortfolioResponse> {
	const res = await fetch(`${API_BASE}/portfolio/analyze`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ holdings })
	});
	if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);
	return res.json();
}

export function streamPortfolio(
	holdings: PortfolioHolding[],
	onProgress: (current: number, total: number, ticker: string) => void,
	onComplete: (data: PortfolioResponse) => void,
	onError: (error: string) => void,
	onResult?: (stock: PortfolioStockResult) => void
): () => void {
	const controller = new AbortController();

	(async () => {
		try {
			const res = await fetch(`${API_BASE}/portfolio/analyze/stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ holdings }),
				signal: controller.signal
			});

			if (!res.ok) {
				onError(`Server error: ${res.status}`);
				return;
			}

			const reader = res.body!.getReader();
			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (!line.startsWith('data: ')) continue;
					try {
						const msg = JSON.parse(line.slice(6));
						if (msg.type === 'progress') {
							onProgress(msg.current, msg.total, msg.ticker);
						} else if (msg.type === 'result' && onResult) {
							onResult(msg.stock);
						} else if (msg.type === 'complete') {
							onComplete(msg.data);
						} else if (msg.type === 'error') {
							onError(msg.message);
						}
					} catch {
						// skip malformed lines
					}
				}
			}
		} catch (err: unknown) {
			if (err instanceof Error && err.name !== 'AbortError') {
				onError(err.message || 'Koneksi terputus');
			}
		}
	})();

	return () => controller.abort();
}

// ── Telegram ──

export async function checkTelegramStatus(): Promise<{ configured: boolean }> {
	try {
		const res = await fetch(`${API_BASE}/telegram/status`);
		return res.json();
	} catch {
		return { configured: false };
	}
}

export async function sendTelegramAlert(
	alerts: Array<{ ticker: string; signalCode: string; signalLabel: string; reason: string; pnlPct: number }>
): Promise<{ success: boolean; message: string }> {
	try {
		const res = await fetch(`${API_BASE}/telegram/send-alert`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ alerts })
		});
		return res.json();
	} catch {
		return { success: false, message: 'Network error' };
	}
}
