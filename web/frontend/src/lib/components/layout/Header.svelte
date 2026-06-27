<script lang="ts">
  import { health, saveLoaded, isHealthy } from '$stores/index';
  import Icon from '@iconify/svelte';
  import AboutModal from './AboutModal.svelte';
  import WarningModal from './WarningModal.svelte';

  let aboutOpen = $state(false);
  let warnOpen = $state(false);

  const h = $derived($health);
</script>

<header class="flex items-center gap-3 h-14 px-4 border-b border-line/50 bg-header-gradient shrink-0">
  <div class="flex items-center gap-2 min-w-0">
    <a href="https://github.com/deafdudecomputers/PalworldSaveTools" target="_blank" rel="noreferrer"
       class="version-chip version-sky" title="App version">
      <Icon icon="simple-icons:github" width={15} />
      <span>v{h?.app_version ?? '?'}</span>
    </a>
    <span class="version-chip version-green" title="Palworld version">
      <Icon icon="lucide:save" width={15} />
      <span>{h?.game_version ?? '?'}</span>
    </span>
  </div>

  <div class="flex items-center gap-1">
    <button class="hdr-btn hdr-info" title="About PST" onclick={() => (aboutOpen = true)}>
      <Icon icon="lucide:info" width={16} />
    </button>
    <button class="hdr-btn hdr-warn" title="Warnings" onclick={() => (warnOpen = true)}>
      <Icon icon="lucide:triangle-alert" width={16} />
    </button>
    <button class="hdr-btn hdr-toolbox" title="Tab Usage Guide — Click to view detailed usage instructions for every tab">
      <Icon icon="lucide:book-open" width={16} />
    </button>
  </div>

  <div class="flex items-center gap-3 min-w-0">
    {#if $saveLoaded}
      <span class="badge bg-status-success/15 border-status-success/40 text-status-success">
        <span class="w-1.5 h-1.5 rounded-full bg-status-success shadow-glow"></span>
        Save loaded
      </span>
    {:else}
      <span class="badge bg-bg-elevated border-line text-ink-muted">No save loaded</span>
    {/if}

  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-2">
    <a href="https://discord.gg/sYcZwcT4cT" target="_blank" rel="noreferrer"
       class="discord-link" title="Join Discord">
      <Icon icon="simple-icons:discord" width={16} />
    </a>
    <div class="flex items-center gap-1.5 text-xs">
      <span
        class="w-2.5 h-2.5 rounded-full {$isHealthy ? 'bg-status-success' : 'bg-status-error'}"
        class:animate-pulse-dot={$isHealthy}
      ></span>
      <span class="{$isHealthy ? 'text-status-success' : 'status-error'}">
        {$isHealthy ? 'Online' : 'Offline'}
      </span>
    </div>
  </div>
</header>

<AboutModal bind:open={aboutOpen} />
<WarningModal bind:open={warnOpen} />

<style>
  .version-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
    cursor: default;
    border-width: 2px;
  }
  .version-sky {
    background: linear-gradient(135deg, rgba(59, 142, 208, 0.12), rgba(0, 188, 212, 0.08));
    border-color: rgba(59, 142, 208, 0.5);
    color: #7DD3FC;
    cursor: pointer;
  }
  .version-sky:hover {
    background: linear-gradient(135deg, rgba(59, 142, 208, 0.2), rgba(0, 188, 212, 0.15));
    border-color: rgba(59, 142, 208, 0.7);
    box-shadow: 0 0 16px rgba(59, 142, 208, 0.2);
  }
  .version-green {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.12), rgba(0, 200, 83, 0.08));
    border-color: rgba(76, 175, 80, 0.5);
    color: #81C784;
  }
  .version-green:hover {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(0, 200, 83, 0.15));
    border-color: rgba(76, 175, 80, 0.7);
    box-shadow: 0 0 16px rgba(76, 175, 80, 0.2);
  }

  .hdr-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 33px;
    height: 33px;
    box-sizing: border-box;
    border-radius: 4px;
    border: 2px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .hdr-info {
    color: #7DD3FC;
    border-color: rgba(59, 142, 208, 0.35);
  }
  .hdr-info:hover {
    background: rgba(59, 142, 208, 0.15);
    border-color: rgba(59, 142, 208, 0.6);
    box-shadow: 0 0 12px rgba(59, 142, 208, 0.2);
    color: #B3E5FC;
  }
  .hdr-warn {
    color: #FFCC80;
    border-color: rgba(255, 183, 77, 0.35);
  }
  .hdr-warn:hover {
    background: rgba(255, 183, 77, 0.15);
    border-color: rgba(255, 183, 77, 0.6);
    box-shadow: 0 0 12px rgba(255, 183, 77, 0.2);
    color: #FFE0B2;
  }
  .hdr-toolbox {
    color: #81C784;
    border-color: rgba(76, 175, 80, 0.35);
  }
  .hdr-toolbox:hover {
    background: rgba(76, 175, 80, 0.15);
    border-color: rgba(76, 175, 80, 0.6);
    box-shadow: 0 0 12px rgba(76, 175, 80, 0.2);
    color: #A5D6A7;
  }

  .discord-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 33px;
    height: 33px;
    box-sizing: border-box;
    border-radius: 4px;
    border: 2px solid rgba(88, 101, 242, 0.4);
    color: #8B9CF7;
    text-decoration: none;
    transition: all 0.2s ease;
  }
  .discord-link:hover {
    background: rgba(88, 101, 242, 0.15);
    border-color: rgba(88, 101, 242, 0.7);
    color: #A5B4FC;
    box-shadow: 0 0 14px rgba(88, 101, 242, 0.25);
  }
</style>
