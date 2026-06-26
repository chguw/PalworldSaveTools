<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { saveLoaded } from '$stores/index';
  import type { PlayerSummary } from '$types/index';
  import SaveGate from '$components/ui/SaveGate.svelte';
  import Card from '$components/ui/Card.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import { Users } from '@lucide/svelte';

  let players = $state<PlayerSummary[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let query = $state('');

  async function load() {
    loading = true; error = null;
    try { players = (await api.players()).players; }
    catch (e) { error = e instanceof Error ? e.message : String(e); }
    finally { loading = false; }
  }
  onMount(() => { if ($saveLoaded) load(); });

  const filtered = $derived(
    players.filter((p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.uid.toLowerCase().includes(query.toLowerCase()) ||
      (p.guild_name ?? '').toLowerCase().includes(query.toLowerCase()),
    ),
  );
</script>

<SaveGate icon={Users}>
  <div class="p-6 max-w-5xl mx-auto space-y-4 animate-fade-in">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-ink-emphasis">Players</h1>
        <p class="text-xs text-ink-muted">{players.length} players across all guilds</p>
      </div>
      <input class="input max-w-xs" placeholder="Filter by name, UID, guild..." bind:value={query} />
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
                <th class="py-2 pr-4 font-medium">Name</th>
                <th class="py-2 pr-4 font-medium">Guild</th>
                <th class="py-2 pr-4 font-medium">Last seen</th>
                <th class="py-2 pr-4 font-medium font-mono">UID</th>
              </tr>
            </thead>
            <tbody>
              {#each filtered as p (p.uid)}
                <tr class="border-b border-line/20 hover:bg-bg-hover/50 transition-fast">
                  <td class="py-2.5 pr-4 text-ink-primary font-medium">{p.name}</td>
                  <td class="py-2.5 pr-4"><Badge tone="accent">{p.guild_name ?? '—'}</Badge></td>
                  <td class="py-2.5 pr-4 text-ink-secondary tabular-nums">{p.last_seen_text ?? 'Unknown'}</td>
                  <td class="py-2.5 pr-4 font-mono text-xs text-ink-muted">{p.uid}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </Card>
  </div>
</SaveGate>
