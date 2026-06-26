<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { saveLoaded } from '$stores/index';
  import type { GuildSummary } from '$types/index';
  import SaveGate from '$components/ui/SaveGate.svelte';
  import Card from '$components/ui/Card.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import { Building2, Users, MapPin, Crown } from '@lucide/svelte';

  let guilds = $state<GuildSummary[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  async function load() {
    loading = true; error = null;
    try { guilds = (await api.guilds()).guilds; }
    catch (e) { error = e instanceof Error ? e.message : String(e); }
    finally { loading = false; }
  }
  onMount(() => { if ($saveLoaded) load(); });
</script>

<SaveGate icon={Building2}>
  <div class="p-6 max-w-5xl mx-auto space-y-4 animate-fade-in">
    <div>
      <h1 class="text-xl font-bold text-ink-emphasis">Guilds</h1>
      <p class="text-xs text-ink-muted">{guilds.length} guilds</p>
    </div>

    {#if loading}
      <Card><div class="flex justify-center py-12"><Spinner size={24} /></div></Card>
    {:else if error}
      <Card><p class="text-sm text-status-error p-4">{error}</p></Card>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each guilds as g (g.id)}
          <Card hover>
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <Building2 size={18} class="text-accent" />
                <h3 class="text-base font-semibold text-ink-emphasis">{g.name}</h3>
              </div>
              <Badge tone="neutral">{g.player_count} players</Badge>
            </div>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div class="flex items-center gap-2 text-ink-secondary">
                <Users size={14} class="text-ink-muted" /> {g.player_count} members
              </div>
              <div class="flex items-center gap-2 text-ink-secondary">
                <MapPin size={14} class="text-ink-muted" /> {g.base_count} bases
              </div>
            </div>
            {#if g.leader_uid}
              <div class="mt-3 pt-3 border-t border-line/30 flex items-center gap-2 text-xs text-ink-muted">
                <Crown size={12} class="text-status-amber" />
                <span class="font-mono">{g.leader_uid}</span>
              </div>
            {/if}
          </Card>
        {/each}
      </div>
    {/if}
  </div>
</SaveGate>
