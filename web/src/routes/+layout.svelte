<script lang="ts">
	import '../app.css';
	import Navbar from '$lib/components/Navbar.svelte';
	import ToastNotification from '$lib/components/ToastNotification.svelte';
	import { marketStatus } from '$lib/stores';
	import { startScanner, stopScanner } from '$lib/portfolioScanner.svelte';
	import { loadSession } from '$lib/auth.svelte';
	import { onMount, onDestroy } from 'svelte';

	let { children } = $props();

	onMount(() => {
		loadSession();
	});

	// Auto-scan portfolio when market is open
	$effect(() => {
		const status = $marketStatus;
		if (status) {
			startScanner(status.is_open);
		}
	});

	onDestroy(() => {
		stopScanner();
	});
</script>

<header
	class="fixed top-0 z-40 w-full border-b border-gray-200 bg-white/95 backdrop-blur-sm dark:border-terminal-border dark:bg-terminal-surface/95"
>
	<Navbar />
</header>

<main class="mx-auto min-h-screen max-w-7xl px-4 pb-8 pt-16 sm:px-6 lg:px-8">
	{@render children()}
</main>

<ToastNotification />
