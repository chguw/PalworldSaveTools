<script lang="ts">
  import { saveLoaded, saveSummary, saveCounts, loadingSave } from '$stores/index';
  import { api } from '$lib/api/client';
  import { toast } from '$stores/toast';
  import { saveState } from '$stores/index';
  import Card from '$components/ui/Card.svelte';
  import Button from '$components/ui/Button.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import EmptyState from '$components/ui/EmptyState.svelte';
  import LoadSaveModal from '$components/layout/LoadSaveModal.svelte';
  import {
    FolderOpen, Download, LogOut, Users, Building2, MapPin, Box, Sparkles,
    ArrowRight, FileX,
  } from '@lucide/svelte';
  import type { Component } from 'svelte';

  let loadOpen = $state(false);
  let exporting = $state(false);

  async function doExport() {
    exporting = true;
    try {
      const { blob, filename, size } = await api.exportSave();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported ${filename} (${(size / 1024 / 1024).toFixed(1)} MB)`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Export failed');
    } finally {
      exporting = false;
    }
  }

  async function doUnload() {
    try {
      const res = await api.unload();
      saveState.set(res);
      toast.info('Save unloaded');
    } catch (e) {
      toast.error('Unload failed');
    }
  }

  function fmtBytes(n: number): string {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(n) / Math.log(1024));
    return `${(n / Math.pow(1024, i)).toFixed(i ? 1 : 0)} ${u[i]}`;
  }

  const stats = $derived([
    { label: 'Guilds', value: $saveCounts?.guilds ?? 0, icon: Building2 as Component, href: '/guilds' },
    { label: 'Players', value: $saveCounts?.players ?? 0, icon: Users as Component, href: '/players' },
    { label: 'Bases', value: $saveCounts?.bases ?? 0, icon: MapPin as Component, href: '/bases' },
    { label: 'Containers', value: $saveCounts?.containers ?? 0, icon: Box as Component, href: '/containers' },
    { label: 'Characters', value: $saveCounts?.characters ?? 0, icon: Sparkles as Component, href: '/pal-editor' },
  ]);
</script>

<div class="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
  <div>
    <h1 class="text-2xl font-bold text-ink-emphasis">Overview</h1>
    <p class="text-sm text-ink-muted mt-1">
      Load a Palworld save to inspect its contents. Viewers are read-only in this phase.
    </p>
  </div>

  <Card>
    <div class="flex flex-wrap items-center gap-3">
      {#if !$saveLoaded}
        <Button variant="primary" onclick={() => (loadOpen = true)}>
          <FolderOpen size={16} /> Load Save
        </Button>
      {:else}
        <Button variant="primary" onclick={() => (loadOpen = true)} disabled={$loadingSave}>
          <FolderOpen size={16} /> Load Another
        </Button>
        <Button variant="secondary" onclick={doExport} disabled={exporting}>
          <Download size={16} /> Export .sav
        </Button>
        <Button variant="ghost" onclick={doUnload}>
          <LogOut size={16} /> Unload
        </Button>
      {/if}
      <div class="flex-1"></div>
      {#if $saveSummary}
        <Badge tone="accent">type {$saveSummary.save_type}</Badge>
        <Badge tone="neutral">{$saveSummary.class_name}</Badge>
      {/if}
    </div>
  </Card>

  {#if $saveLoaded}
    <div>
      <h2 class="text-sm font-semibold text-ink-secondary uppercase tracking-wider mb-3">World Summary</h2>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {#each stats as s}
          <a href={s.href} class="card card-hover flex flex-col gap-2 group">
            <div class="flex items-center justify-between">
              <s.icon size={18} class="text-accent" />
              <ArrowRight size={14} class="text-ink-dim group-hover:text-accent transition-fast" />
            </div>
            <div>
              <p class="text-2xl font-bold text-ink-emphasis tabular-nums">{s.value}</p>
              <p class="text-xs text-ink-muted uppercase tracking-wide">{s.label}</p>
            </div>
          </a>
        {/each}
      </div>
    </div>

    <Card title="Loaded File">
      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 text-sm">
        <div class="flex justify-between py-1.5 border-b border-line/30">
          <dt class="text-ink-muted">Filename</dt>
          <dd class="text-ink-primary font-mono text-xs">{$saveSummary?.filename}</dd>
        </div>
        <div class="flex justify-between py-1.5 border-b border-line/30">
          <dt class="text-ink-muted">File size</dt>
          <dd class="text-ink-primary tabular-nums">{fmtBytes($saveSummary?.file_size ?? 0)}</dd>
        </div>
        <div class="flex justify-between py-1.5 border-b border-line/30">
          <dt class="text-ink-muted">Save directory</dt>
          <dd class="text-ink-secondary font-mono text-xs truncate max-w-[260px]">{$saveSummary?.save_dir}</dd>
        </div>
        <div class="flex justify-between py-1.5 border-b border-line/30">
          <dt class="text-ink-muted">Compression</dt>
          <dd class="text-ink-primary">
            {$saveSummary?.save_type === 50 ? 'PLZ (double-zlib)' : 'PLM (Oodle)'}
          </dd>
        </div>
      </dl>
    </Card>
  {:else}
    <Card>
      <EmptyState icon={FileX} title="No save loaded">
        <p>Click <strong class="text-ink-secondary">Load Save</strong> and point to your
        <code class="text-accent-light">Level.sav</code> to begin.</p>
      </EmptyState>
    </Card>
  {/if}
</div>

<LoadSaveModal bind:open={loadOpen} />
