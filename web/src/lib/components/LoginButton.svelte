<script lang="ts">
	import { PUBLIC_GOOGLE_CLIENT_ID } from '$env/static/public';
	import { login } from '$lib/auth.svelte';
	import { onMount } from 'svelte';

	let buttonDiv: HTMLDivElement;

	onMount(() => {
		const initGsi = () => {
			if (!window.google?.accounts?.id) {
				setTimeout(initGsi, 100);
				return;
			}

			window.google.accounts.id.initialize({
				client_id: PUBLIC_GOOGLE_CLIENT_ID,
				callback: handleCredentialResponse,
				auto_select: false,
				itp_support: true
			});

			window.google.accounts.id.renderButton(buttonDiv, {
				theme: 'outline',
				size: 'medium',
				type: 'standard',
				shape: 'pill',
				text: 'signin_with',
				width: 200
			});
		};

		initGsi();
	});

	function handleCredentialResponse(response: { credential: string }) {
		login(response.credential);
	}
</script>

<div bind:this={buttonDiv} class="flex items-center"></div>
