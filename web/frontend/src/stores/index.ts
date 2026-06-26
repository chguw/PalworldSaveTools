import { writable, derived, get } from 'svelte/store';
import type {
  HealthResponse, LanguagesResponse, SaveStateResponse, WorldCounts,
} from '$types/index';

// ---- system ----
export const health = writable<HealthResponse | null>(null);
export const isHealthy = derived(health, ($h) => $h?.status === 'ok');
export const wsConnected = writable(false);
export const languages = writable<LanguagesResponse | null>(null);
export const currentLang = writable('en_US');
export const i18n = writable<Record<string, string>>({});

// ---- save lifecycle ----
export const saveState = writable<SaveStateResponse | null>(null);
export const saveLoaded = derived(saveState, ($s) => !!$s?.loaded);
export const saveSummary = derived(saveState, ($s) => $s?.summary ?? null);
export const saveCounts = derived(saveState, ($s) => $s?.counts ?? null);
export const loadingSave = writable(false);
export const loadError = writable<string | null>(null);

// ---- i18n helper ----
export const t = derived(
  [i18n, currentLang],
  ([$i18n, $lang]) =>
    (key: string, fallback?: string): string =>
      $i18n[key] ?? fallback ?? key,
);

export function resetSaveData(): void {
  saveState.set(null);
  loadError.set(null);
  loadingSave.set(false);
}

// convenience: read current loaded flag without subscribing
export function isSaveLoaded(): boolean {
  return get(saveLoaded);
}
