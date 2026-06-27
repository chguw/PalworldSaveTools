/**
 * Map UI state store — visibility toggles, view transform, selected marker.
 */

import { writable, derived } from 'svelte/store';
import type { MapType } from '$lib/map/types';

// Layer visibility toggles (match the PySide6 overlay buttons)
export const showBases = writable(true);
export const showPlayers = writable(true);
export const showRings = writable(true);
export const showZones = writable(false);
export const mapType = writable<MapType>('world');

// Sidebar open/closed
export const sidebarOpen = writable(true);

// Current zoom level (1.0 = fit, up to 30.0)
export const zoom = writable(1.0);

// Cursor world coords (for the HUD display)
export const cursorWorld = writable<{ x: number; y: number } | null>(null);

// Selected marker ID + kind
export const selectedMarker = writable<{ kind: 'base' | 'player'; id: string } | null>(null);

// Zone drawing mode
export const zoneDrawingMode = writable(false);
export const zoneShapeType = writable<'rect' | 'polygon'>('rect');

// Search filter
export const mapSearch = writable('');

// Data loading state
export const mapLoading = writable(false);
export const mapError = writable<string | null>(null);
