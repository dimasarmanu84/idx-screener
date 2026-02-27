/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

declare const self: ServiceWorkerGlobalScope;

import { build, files, version } from '$service-worker';

const CACHE = `cache-${version}`;

// Static assets to cache (JS, CSS, images, etc.)
const ASSETS = [...build, ...files];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE)
			.then((cache) => cache.addAll(ASSETS))
			.then(() => self.skipWaiting())
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);

	// Skip non-GET requests
	if (event.request.method !== 'GET') return;

	// Skip API calls — always go to network (real-time stock data)
	if (url.pathname.startsWith('/api')) return;

	// Skip EventSource/SSE streams
	if (event.request.headers.get('accept')?.includes('text/event-stream')) return;

	// Skip cross-origin requests (fonts, etc.)
	if (url.origin !== self.location.origin) return;

	event.respondWith(
		caches.match(event.request).then((cached) => {
			if (cached) return cached;

			return fetch(event.request)
				.then((response) => {
					// Cache successful responses for static assets
					if (response.ok && response.status === 200) {
						const clone = response.clone();
						caches.open(CACHE).then((cache) => cache.put(event.request, clone));
					}
					return response;
				})
				.catch(() => {
					// Offline fallback for navigation requests
					if (event.request.mode === 'navigate') {
						return caches.match('/index.html') as Promise<Response>;
					}
					return new Response('Offline', { status: 503, statusText: 'Offline' });
				});
		})
	);
});
