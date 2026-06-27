<script lang="ts">
  import { health, saveLoaded, saveSummary, saveCounts, isHealthy } from '$stores/index';
  import { Save, ExternalLink } from '@lucide/svelte';

  function fmtBytes(n: number): string {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(n) / Math.log(1024));
    return `${(n / Math.pow(1024, i)).toFixed(i ? 1 : 0)} ${u[i]}`;
  }

  const counts = $derived($saveCounts);
  const h = $derived($health);
</script>

<header class="flex items-center gap-4 h-14 px-5 border-b border-line/50 bg-header-gradient shrink-0">
  <div class="flex items-center gap-3 min-w-0">
    {#if $saveLoaded}
      <span class="badge bg-status-success/15 border-status-success/40 text-status-success">
        <span class="w-1.5 h-1.5 rounded-full bg-status-success shadow-glow"></span>
        Save loaded
      </span>
    {:else}
      <span class="badge bg-bg-elevated border-line text-ink-muted">No save loaded</span>
    {/if}
    <div class="hidden md:flex items-center gap-3 text-xs text-ink-muted min-w-0">
      {#if $saveLoaded}
        <span class="truncate max-w-[220px] text-ink-secondary font-medium">
          {$saveSummary?.filename}
        </span>
        <span>·</span>
        <span>{fmtBytes($saveSummary?.file_size ?? 0)}</span>
      {/if}
      {#if counts}
        <span>·</span>
        <span>{counts.guilds} guilds</span>
        <span>·</span>
        <span>{counts.players} players</span>
        <span>·</span>
        <span>{counts.bases} bases</span>
      {/if}
    </div>
  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-2">
    <!-- App version chip -->
    <a href="https://github.com/deafdudecomputers/PalworldSaveTools" target="_blank" rel="noreferrer"
       class="chip chip-sky" title="App version">
      <ExternalLink size={14} />
      <span>v{h?.app_version ?? '?'}</span>
    </a>

    <!-- Game version chip -->
    <span class="chip chip-green" title="Palworld version">
      <Save size={14} />
      <span>{h?.game_version ?? '?'}</span>
    </span>

    <!-- Backend status -->
    <div class="flex items-center gap-1.5 text-xs ml-1">
      <span
        class="w-2 h-2 rounded-full {$isHealthy ? 'bg-status-success shadow-glow' : 'bg-status-error'}"
      ></span>
      <span class="{$isHealthy ? 'text-status-success' : 'text-status-error'}">
        {$isHealthy ? 'Online' : 'Offline'}
      </span>
    </div>
  </div>
</header>

<style>
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.15s ease;
    cursor: default;
  }
  .chip-sky {
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.12);
    color: #7dd3fc;
    cursor: pointer;
  }
  .chip-sky:hover {
    background: rgba(56, 189, 248, 0.12);
  }
  .chip-green {
    background: rgba(74, 222, 128, 0.08);
    border: 1px solid rgba(74, 222, 128, 0.12);
    color: #86efac;
  }
</style>
