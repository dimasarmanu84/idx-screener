import { writable } from 'svelte/store';
import type { MarketStatus } from './types';

export const marketStatus = writable<MarketStatus | null>(null);
