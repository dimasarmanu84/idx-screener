<script lang="ts">
	import { auth, logout } from '$lib/auth.svelte';

	let menuOpen = $state(false);

	function handleLogout() {
		logout();
		menuOpen = false;
	}

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.user-menu-container')) {
			menuOpen = false;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="user-menu-container relative">
	<button
		onclick={() => (menuOpen = !menuOpen)}
		class="flex items-center gap-2 rounded-full p-0.5 transition-all hover:ring-2 hover:ring-blue-500/30"
		aria-label="User menu"
	>
		{#if auth.user?.picture}
			<img
				src={auth.user.picture}
				alt={auth.user.name}
				class="h-7 w-7 rounded-full"
				referrerpolicy="no-referrer"
			/>
		{:else}
			<div
				class="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white"
			>
				{auth.user?.name?.charAt(0) || '?'}
			</div>
		{/if}
	</button>

	{#if menuOpen}
		<div
			class="absolute right-0 top-full mt-2 w-56 rounded-xl border border-gray-200 bg-white p-2 shadow-lg dark:border-terminal-border dark:bg-terminal-surface"
		>
			<div class="border-b border-gray-100 px-3 py-2 dark:border-terminal-border">
				<p class="text-sm font-semibold text-gray-900 dark:text-terminal-text">
					{auth.user?.name}
				</p>
				<p class="text-xs text-gray-500 dark:text-terminal-muted">
					{auth.user?.email}
				</p>
			</div>
			<button
				onclick={handleLogout}
				class="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-600 transition-colors hover:bg-gray-100 dark:text-terminal-muted dark:hover:bg-terminal-surface-hover"
			>
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
					/>
				</svg>
				Logout
			</button>
		</div>
	{/if}
</div>
