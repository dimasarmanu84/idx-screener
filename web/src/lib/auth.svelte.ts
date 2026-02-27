/**
 * Auth state management — Google Sign-In + server portfolio sync.
 * Pattern mirrors portfolioScanner.svelte.ts (Svelte 5 runes).
 */

const API_BASE = '/api';
const TOKEN_KEY = 'screener_auth_token';
const STORAGE_KEY = 'screener_portfolio';

export interface User {
	id: number;
	email: string;
	name: string;
	picture: string;
}

// ── Reactive state ──
let auth = $state({
	user: null as User | null,
	token: '',
	isLoggedIn: false,
	isLoading: true
});

// ── Token persistence ──
function saveToken(token: string) {
	auth.token = token;
	localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
	auth.token = '';
	localStorage.removeItem(TOKEN_KEY);
}

// ── Auth headers helper ──
function getAuthHeaders(): Record<string, string> {
	if (!auth.token) return {};
	return { Authorization: `Bearer ${auth.token}` };
}

// ── Server sync ──
let syncTimer: ReturnType<typeof setTimeout> | null = null;

async function syncFromServer(): Promise<void> {
	if (!auth.token) return;

	try {
		const res = await fetch(`${API_BASE}/user/portfolio`, {
			headers: { Authorization: `Bearer ${auth.token}` }
		});

		if (res.ok) {
			const data = await res.json();
			const serverHoldings = data.holdings as Array<{
				ticker: string;
				lot: number;
				avg_price: number;
			}>;

			if (serverHoldings.length === 0) {
				// Server empty — push local data (first-time migration)
				const local = localStorage.getItem(STORAGE_KEY);
				if (local) {
					try {
						const localHoldings = JSON.parse(local);
						if (Array.isArray(localHoldings) && localHoldings.length > 0) {
							await syncToServer(localHoldings);
							window.dispatchEvent(
								new CustomEvent('portfolio-synced', { detail: localHoldings })
							);
							return;
						}
					} catch {
						/* ignore */
					}
				}
			}

			// Server has data — it wins
			localStorage.setItem(STORAGE_KEY, JSON.stringify(serverHoldings));
			window.dispatchEvent(new CustomEvent('portfolio-synced', { detail: serverHoldings }));
		}
	} catch {
		// Silent fail — user can still use localStorage data
	}
}

async function syncToServer(
	holdings: Array<{ ticker: string; lot: number; avg_price: number }>
): Promise<void> {
	if (!auth.token) return;

	// Debounce 500ms to avoid rapid-fire PUTs
	if (syncTimer) clearTimeout(syncTimer);
	syncTimer = setTimeout(async () => {
		try {
			await fetch(`${API_BASE}/user/portfolio`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${auth.token}`
				},
				body: JSON.stringify({ holdings })
			});
		} catch {
			// Silent fail — data is still in localStorage
		}
	}, 500);
}

// ── Login with Google credential ──
async function login(credential: string): Promise<boolean> {
	try {
		const res = await fetch(`${API_BASE}/auth/google`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ credential })
		});

		if (!res.ok) return false;

		const data = await res.json();
		auth.user = data.user;
		auth.isLoggedIn = true;
		saveToken(data.token);

		await syncFromServer();
		return true;
	} catch {
		return false;
	}
}

// ── Validate stored token on app load ──
async function loadSession(): Promise<void> {
	const stored = localStorage.getItem(TOKEN_KEY);
	if (!stored) {
		auth.isLoading = false;
		return;
	}

	auth.token = stored;

	try {
		const res = await fetch(`${API_BASE}/auth/me`, {
			headers: { Authorization: `Bearer ${stored}` }
		});

		if (res.ok) {
			const user = await res.json();
			auth.user = user;
			auth.isLoggedIn = true;
			await syncFromServer();
		} else {
			clearToken();
		}
	} catch {
		// Network error — keep token, try later
	} finally {
		auth.isLoading = false;
	}
}

// ── Logout ──
function logout() {
	auth.user = null;
	auth.isLoggedIn = false;
	clearToken();
	// Keep localStorage portfolio data intact (guest mode resumes)
}

// ── Public exports ──
export { auth, login, logout, loadSession, getAuthHeaders, syncToServer, syncFromServer };
