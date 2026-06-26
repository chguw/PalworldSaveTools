<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { saveLoaded } from '$stores/index';
  import type { ContainerSummary } from '$types/index';
  import SaveGate from '$components/ui/SaveGate.svelte';
  import Card from '$components/ui/Card.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import { Box } from '@lucide/svelte';

  let containers = $state<ContainerSummary[]>([]);
  let total = $state(0);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let query = $state('');

  const LIMIT = 500;
  async function load() {
    loading = true; error = null;
    try { const r = await api.containers(LIMIT); containers = r.containers; total = r.total; }
    catch (e) { error = e instanceof Error ? e.message : String(e); }
    finally { loading = false; }
  }
  onMount(() => { if ($saveLoaded) load(); });

  const filtered = $derived(
    containers.filter((c) =>
      c.id.toLowerCase().includes(query.toLowerCase()) ||
      (c.owner_player_uid ?? '').toLowerCase().includes(query.toLowerCase()) ||
      (c.guild_id ?? '').toLowerCase().includes(query.toLowerCase()),
    ),
  );
</script>

<SaveGate icon={Box}>
  <div class="p-6 max-w-5xl mx-auto space-y-4 animate-fade-in">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-ink-emphasis">Containers</h1>
        <p class="text-xs text-ink-muted">
          Showing first {containers.length} of {total} item containers
        </p>
      </div>
      <input class="input max-w-xs" placeholder="Filter by ID, owner, guild..." bind:value={query} />
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
                <th class="py-2 pr-4 font-medium">Slots</th>
                <th class="py-2 pr-4 font-medium">Owner</th>
                <th class="py-2 pr-4 font-medium font-mono">Container ID</th>
              </tr>
            </thead>
            <tbody>
              {#each filtered as c (c.id)}
                <tr class="border-b border-line/20 hover:bg-bg-hover/50 transition-fast">
                  <td class="py-2.5 pr-4"><Badge tone={c.slot_count ? 'accent' : 'neutral'}>{c.slot_count}</Badge></td>
                  <td class="py-2.5 pr-4 font-mono text-xs text-ink-muted">
                    {c.owner_player_uid ? c.owner_player_uid.slice(0, 13) + '…' : '—'}
                  </td>
                  <td class="py-2.5 pr-4 font-mono text-xs text-ink-secondary">{c.id.slice(0, 18)}…</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        {#if total > LIMIT}
          <p class="mt-3 text-xs text-ink-dim text-center">
            Refine the filter or increase the backend limit to see beyond the first {LIMIT}.
          </p>
        {/if}
      {/if}
    </Card>
  </div>
</SaveGate>
