<script lang="ts">
	import { page } from '$app/stores';
	import ThemeToggle from './ThemeToggle.svelte';
	import MarketStatus from './MarketStatus.svelte';
	import LoginButton from './LoginButton.svelte';
	import UserMenu from './UserMenu.svelte';
	import { scanner } from '$lib/portfolioScanner.svelte';
	import { auth } from '$lib/auth.svelte';

	const links = [
		{ href: '/', label: 'Home', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1' },
		{ href: '/bsjp', label: 'BSJP' },
		{ href: '/intraday', label: 'Intraday' },
		{ href: '/swing', label: 'Swing' },
		{ href: '/night-scanner', label: 'Night' },
		{ href: '/portfolio', label: 'Portfolio' }
	];

	let menuOpen = $state(false);
</script>

<nav class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
	<!-- Logo -->
	<a href="/" class="flex items-center gap-2">
		<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
			<svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
			</svg>
		</div>
		<span class="text-lg font-extrabold tracking-tight text-gray-900 dark:text-terminal-text">
			IDX<span class="text-blue-500">Screener</span>
		</span>
	</a>

	<!-- Desktop nav -->
	<div class="hidden items-center gap-1 md:flex">
		{#each links as link}
			{@const active = link.href === '/' ? $page.url.pathname === '/' : $page.url.pathname.startsWith(link.href)}
			<a
				href={link.href}
				class="relative rounded-lg px-3 py-1.5 text-sm font-semibold transition-all
					{active
						? 'text-blue-500 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-900 dark:text-terminal-muted dark:hover:text-terminal-text'}"
			>
				{link.label}
				{#if link.href === '/portfolio' && scanner.alertBadgeCount > 0}
					<span class="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
						{scanner.alertBadgeCount > 9 ? '9+' : scanner.alertBadgeCount}
					</span>
				{/if}
				{#if active}
					<span class="absolute -bottom-[11px] left-1/2 h-0.5 w-5 -translate-x-1/2 rounded-full bg-blue-500"></span>
				{/if}
			</a>
		{/each}
	</div>

	<!-- Right section -->
	<div class="flex items-center gap-3">
		<MarketStatus />
		<div class="hidden h-5 w-px bg-gray-200 dark:bg-terminal-border md:block"></div>

		<!-- Auth -->
		{#if !auth.isLoading}
			{#if auth.isLoggedIn}
				<UserMenu />
			{:else}
				<div class="hidden md:block">
					<LoginButton />
				</div>
			{/if}
		{/if}

		<div class="hidden h-5 w-px bg-gray-200 dark:bg-terminal-border md:block"></div>
		<ThemeToggle />

		<!-- Mobile menu button -->
		<button
			onclick={() => (menuOpen = !menuOpen)}
			class="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-terminal-surface-hover md:hidden"
			aria-label="Toggle menu"
		>
			<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				{#if menuOpen}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				{/if}
			</svg>
		</button>
	</div>
</nav>

<!-- Mobile menu -->
{#if menuOpen}
	<div class="border-t border-gray-200 px-4 py-2 dark:border-terminal-border md:hidden">
		{#each links as link}
			{@const active = link.href === '/' ? $page.url.pathname === '/' : $page.url.pathname.startsWith(link.href)}
			<a
				href={link.href}
				onclick={() => (menuOpen = false)}
				class="flex items-center rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors
					{active
						? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400'
						: 'text-gray-600 hover:bg-gray-50 dark:text-terminal-muted dark:hover:bg-terminal-surface-hover'}"
			>
				{link.label}
				{#if link.href === '/portfolio' && scanner.alertBadgeCount > 0}
					<span class="ml-auto flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
						{scanner.alertBadgeCount > 9 ? '9+' : scanner.alertBadgeCount}
					</span>
				{/if}
			</a>
		{/each}

		<!-- Mobile auth -->
		{#if !auth.isLoading}
			<div class="mt-2 border-t border-gray-200 pt-2 dark:border-terminal-border">
				{#if auth.isLoggedIn}
					<div class="flex items-center gap-2 px-3 py-2">
						{#if auth.user?.picture}
							<img src={auth.user.picture} alt="" class="h-6 w-6 rounded-full" referrerpolicy="no-referrer" />
						{/if}
						<span class="text-xs text-gray-600 dark:text-terminal-muted">{auth.user?.name}</span>
					</div>
				{:else}
					<div class="px-3 py-2">
						<LoginButton />
					</div>
				{/if}
			</div>
		{/if}
	</div>
{/if}
