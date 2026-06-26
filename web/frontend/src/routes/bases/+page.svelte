<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { saveLoaded } from '$stores/index';
  import type { BaseSummary } from '$types/index';
  import SaveGate from '$components/ui/SaveGate.svelte';
  import Card from '$components/ui/Card.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import { MapPin, Building2 } from '@lucide/svelte';

  let bases = $state<BaseSummary[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  async function load() {
    loading = true; error = null;
    try { bases = (await api.bases()).bases; }
    catch (e) { error = e instanceof Error ? e.message : String(e); }
    finally { loading = false; }
  }
  onMount(() => { if ($saveLoaded) load(); });

  function fmtCoord(loc: [number, number, number] | null): string {
    if (!loc) return '—';
    return `${loc[0].toFixed(0)}, ${loc[1].toFixed(0)}, ${loc[2].toFixed(0)}`;
  }
</script>

<SaveGate icon={MapPin}>
  <div class="p-6 max-w-5xl mx-auto space-y-4 animate-fade-in">
    <div>
      <h1 class="text-xl font-bold text-ink-emphasis">Bases</h1>
      <p class="text-xs text-ink-muted">{bases.length} base camps</p>
    </div>

    <Card>
      {#if loading}
        <div class="flex justify-center py-12"><Spinner size={24} /></div>
      {:else if error}
        <p class="text-sm text-status-error p-4">{error}</p>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs uppercase tracking-wider text-ink-muted border-b border-line/40">
                <th class="py-2 pr-4 font-medium">#</th>
                <th class="py-2 pr-4 font-medium">Guild</th>
                <th class="py-2 pr-4 font-medium">Location (x, y, z)</th>
                <th class="py-2 pr-4 font-medium font-mono">Base ID</th>
              </tr>
            </thead>
            <tbody>
              {#each bases as b, i (b.id)}
                <tr class="border-b border-line/20 hover:bg-bg-hover/50 transition-fast">
                  <td class="py-2.5 pr-4 text-ink-muted tabular-nums">{i + 1}</td>
                  <td class="py-2.5 pr-4">
                    {#if b.guild_name}
                      <Badge tone="accent"><Building2 size={11} />{b.guild_name}</Badge>
                    {:else}
                      <span class="text-ink-dim">—</span>
                    {/if}
                  </td>
                  <td class="py-2.5 pr-4 font-mono text-xs text-ink-secondary tabular-nums">{fmtCoord(b.location)}</td>
                  <td class="py-2.5 pr-4 font-mono text-xs text-ink-muted">{b.id.slice(0, 13)}…</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </Card>
  </div>
</SaveGate>
