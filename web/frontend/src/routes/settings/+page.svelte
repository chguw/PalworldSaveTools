<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { health, languages, currentLang, i18n, isHealthy } from '$stores/index';
  import { toast } from '$stores/toast';
  import Card from '$components/ui/Card.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Button from '$components/ui/Button.svelte';
  import { Globe, Cpu, Check } from '@lucide/svelte';

  let switching = $state(false);
  let savedPath = $state('');

  async function switchLang(code: string) {
    if (code === $currentLang) return;
    switching = true;
    try {
      const res = await api.i18n(code);
      i18n.set(res.keys);
      currentLang.set(code);
      toast.success(`Language set to ${code}`);
    } catch (e) {
      toast.error('Failed to load language');
    } finally {
      switching = false;
    }
  }

  onMount(async () => {
    if (!$languages) {
      try { languages.set(await api.languages()); } catch { /* ignore */ }
    }
    if (!$health) {
      try { health.set(await api.health()); } catch { /* ignore */ }
    }
  });

  function fmtTime(ts: number): string {
    return new Date(ts * 1000).toLocaleString();
  }
</script>

<div class="p-6 max-w-3xl mx-auto space-y-6 animate-fade-in">
  <div>
    <h1 class="text-xl font-bold text-ink-emphasis">Settings</h1>
    <p class="text-xs text-ink-muted">Interface language and backend information</p>
  </div>

  <Card title="Language">
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {#each $languages?.available ?? [] as lang}
        <button
          class="relative p-3 rounded-6 border text-left transition-fast disabled:opacity-50
                 {lang.code === $currentLang
                   ? 'border-accent bg-accent/10 text-ink-primary shadow-glow'
                   : 'border-line bg-bg-deep text-ink-secondary hover:border-accent/40 hover:bg-bg-hover'}"
          onclick={() => switchLang(lang.code)}
          disabled={switching}
        >
          {#if lang.code === $currentLang}
            <Check size={14} class="absolute top-2 right-2 text-accent" />
          {/if}
          <p class="text-sm font-medium">{lang.label}</p>
          <p class="text-[10px] font-mono text-ink-muted mt-0.5">{lang.code}</p>
        </button>
      {/each}
    </div>
    <p class="mt-3 text-xs text-ink-muted flex items-center gap-1.5">
      <Globe size={12} /> Active: <span class="text-ink-secondary font-mono">{$currentLang}</span>
    </p>
  </Card>

  <Card title="Backend">
    <dl class="space-y-2 text-sm">
      <div class="flex justify-between py-1.5 border-b border-line/30">
        <dt class="text-ink-muted flex items-center gap-1.5"><Cpu size={13} /> Status</dt>
        <dd>
          {#if $isHealthy}
            <Badge tone="success">online</Badge>
          {:else}
            <Badge tone="error">offline</Badge>
          {/if}
        </dd>
      </div>
      <div class="flex justify-between py-1.5 border-b border-line/30">
        <dt class="text-ink-muted">WebUI version</dt>
        <dd class="text-ink-primary font-mono text-xs">{$health?.version ?? '—'}</dd>
      </div>
      <div class="flex justify-between py-1.5 border-b border-line/30">
        <dt class="text-ink-muted">Save loaded</dt>
        <dd class="text-ink-secondary">{$health?.save_loaded ? 'yes' : 'no'}</dd>
      </div>
      <div class="flex justify-between py-1.5 border-b border-line/30">
        <dt class="text-ink-muted">Backend</dt>
        <dd class="text-ink-secondary text-xs">FastAPI + palsav (headless, no Qt)</dd>
      </div>
    </dl>
  </Card>

  <Card title="About">
    <p class="text-sm text-ink-secondary leading-relaxed">
      This WebUI is a Svelte + Tailwind frontend with a lightweight FastAPI backend that wraps the
      project's <code class="text-accent-light">palsav</code> serialization engine. It uses the full
      CLI-grade custom-properties table for byte-faithful SAV round-trips. The Qt desktop app remains
      the canonical editor; this interface provides read-only inspection now and editing in phase 2.
    </p>
  </Card>
</div>
