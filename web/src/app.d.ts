// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	// Google Identity Services
	interface Window {
		google?: {
			accounts: {
				id: {
					initialize: (config: {
						client_id: string;
						callback: (response: { credential: string; select_by: string }) => void;
						auto_select?: boolean;
						itp_support?: boolean;
					}) => void;
					renderButton: (
						parent: HTMLElement,
						options: {
							theme?: string;
							size?: string;
							type?: string;
							shape?: string;
							text?: string;
							width?: number;
						}
					) => void;
					prompt: () => void;
					disableAutoSelect: () => void;
				};
			};
		};
	}
}

export {};
