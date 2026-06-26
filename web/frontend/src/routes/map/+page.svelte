<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { saveLoaded } from '$stores/index';
  import type { BaseSummary } from '$types/index';
  import SaveGate from '$components/ui/SaveGate.svelte';
  import Card from '$components/ui/Card.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import { Map as MapIcon } from '@lucide/svelte';

  let bases = $state<BaseSummary[]>([]);
  let loading = $state(true);

  // Normalise game coords (≈ -440k..440k) into a 0..100% plot box.
  const SCALE = 450000;
  function pct(v: number): number {
    return 50 + (Math.max(-SCALE, Math.min(SCALE, v)) / SCALE) * 50;
  }
  async function load() {
    loading = true;
    try { bases = (await api.bases()).bases.filter((b) => b.location); }
    catch { /* ignore */ }
    finally { loading = false; }
  }
  onMount(() => { if ($saveLoaded) load(); });
</script>

<SaveGate icon={MapIcon}>
  <div class="p-6 max-w-5xl mx-auto space-y-4 animate-fade-in">
    <div>
      <h1 class="text-xl font-bold text-ink-emphasis">Map</h1>
      <p class="text-xs text-ink-muted">Approximate base positions from save coordinates (read-only)</p>
    </div>

    <Card>
      {#if loading}
        <div class="flex justify-center py-12"><Spinner size={24} /></div>
      {:else}
        <div class="relative w-full aspect-square max-w-2xl mx-auto bg-bg-deep border border-line/40 rounded-8 overflow-hidden">
          <div class="absolute inset-0 opacity-30"
               style="background-image: linear-gradient(rgba(59,142,208,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(59,142,208,0.15) 1px, transparent 1px); background-size: 10% 10%;"></div>
          {#each bases as b (b.id)}
            {@const loc = b.location as [number, number, number]}
            <div class="absolute -translate-x-1/2 -translate-y-1/2 group" style="left:{pct(loc[0])}%;top:{pct(loc[1])}%;">
              <div class="w-3 h-3 rounded-full bg-accent-cyan shadow-glow border-2 border-accent-light"></div>
              <div class="absolute left-4 top-1/2 -translate-y-1/2 hidden group-hover:block whitespace-nowrap text-[10px] bg-bg-elevated border border-line rounded-4 px-1.5 py-0.5 text-ink-secondary">
                {b.guild_name ?? 'Base'}
              </div>
            </div>
          {/each}
          <div class="absolute bottom-2 left-2 text-[10px] text-ink-dim font-mono">{bases.length} bases plotted</div>
        </div>
      {/if}
    </Card>
  </div>
</SaveGate>
