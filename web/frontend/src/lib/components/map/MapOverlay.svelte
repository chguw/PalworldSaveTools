<script lang="ts">
  /**
   * MapOverlay — top-right floating control bar + bottom HUD.
   * Mirrors the PySide6 overlay: Bases/Players/Rings/Zones/MapType toggles,
   * plus zoom controls and cursor/zoom readouts.
   */

  import Icon from '@iconify/svelte';
  import {
    showBases, showPlayers, showRings, showZones, mapType, zoom,
  } from '$stores/mapStore';

  interface Props {
    cursorWorld?: { x: number; y: number } | null;
    onZoomIn?: () => void;
    onZoomOut?: () => void;
    onResetView?: () => void;
  }

  let {
    cursorWorld = null,
    onZoomIn,
    onZoomOut,
    onResetView,
  }: Props = $props();

  const btnClass =
    'flex items-center justify-center w-9 h-9 rounded-4 border transition-all duration-150 ' +
    'border-line/30 bg-bg-elevated/80 backdrop-blur text-ink-secondary hover:text-ink-primary ' +
    'hover:border-accent-cyan/50 hover:bg-bg-elevated';

  const btnActiveClass =
    'flex items-center justify-center w-9 h-9 rounded-4 border transition-all duration-150 ' +
    'border-accent-cyan bg-accent-cyan/20 text-accent-cyan shadow-glow';

  const hudClass =
    'px-2 py-1 rounded-4 bg-bg-deep/90 backdrop-blur border border-line/30 ' +
    'text-[10px] font-mono text-ink-muted pointer-events-none';

  function toggleMapType() {
    mapType.update((t) => (t === 'world' ? 'tree' : 'world'));
  }
</script>

<!-- Top-left toggle bar -->
<div class="absolute top-3 left-3 z-20 flex items-center gap-1.5">
  <button
    class={btnClass}
    title="Zoom In"
    onclick={() => onZoomIn?.()}
  >
    <Icon icon="lucide:zoom-in" width="18" />
  </button>
  <button
    class={btnClass}
    title="Zoom Out"
    onclick={() => onZoomOut?.()}
  >
    <Icon icon="lucide:zoom-out" width="18" />
  </button>
  <button
    class={btnClass}
    title="Reset View"
    onclick={() => onResetView?.()}
  >
    <Icon icon="lucide:maximize" width="18" />
  </button>

  <div class="w-px h-7 bg-line/30 mx-0.5"></div>

  <button
    class={$showBases ? btnActiveClass : btnClass}
    title="Toggle Bases"
    onclick={() => showBases.update((v) => !v)}
  >
    <Icon icon="lucide:home" width="18" />
  </button>
  <button
    class={$showPlayers ? btnActiveClass : btnClass}
    title="Toggle Players"
    onclick={() => showPlayers.update((v) => !v)}
  >
    <Icon icon="lucide:user" width="18" />
  </button>
  <button
    class={$showRings ? btnActiveClass : btnClass}
    title="Toggle Base Radius Rings"
    onclick={() => showRings.update((v) => !v)}
  >
    <Icon icon="lucide:circle-dashed" width="18" />
  </button>
  <button
    class={$showZones ? btnActiveClass : btnClass}
    title="Toggle Exclusion Zones"
    onclick={() => showZones.update((v) => !v)}
  >
    <Icon icon="lucide:hexagon" width="18" />
  </button>

  <div class="w-px h-7 bg-line/30 mx-0.5"></div>

  <button
    class={$mapType === 'tree' ? btnActiveClass : btnClass}
    title={$mapType === 'world' ? 'Switch to Tree Map' : 'Switch to World Map'}
    onclick={toggleMapType}
  >
    <Icon icon={$mapType === 'world' ? 'lucide:trees' : 'lucide:globe'} width="18" />
  </button>
</div>

<!-- Bottom-left cursor coords -->
<div class="absolute bottom-3 left-3 z-20 {hudClass}">
  {#if cursorWorld}
    Cursor: {cursorWorld.x},{cursorWorld.y}
  {:else}
    Cursor: 0,0
  {/if}
</div>

<!-- Bottom-right zoom % -->
<div class="absolute bottom-3 right-3 z-20 {hudClass}">
  Zoom: {Math.round($zoom * 100)}%
</div>
