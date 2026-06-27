<script lang="ts">
  import { api } from '$lib/api/client';
  import { saveState, loadingSave, loadError } from '$stores/index';
  import { toast } from '$stores/toast';
  import Button from '$components/ui/Button.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import { X, FolderOpen } from '@lucide/svelte';

  let { open = $bindable(false) }: { open: boolean } = $props();

  let path = $state('');
  let busy = $state(false);

  function close() {
    if (!busy) open = false;
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && open) close();
  }

  async function doLoad() {
    const p = path.trim();
    if (!p) return;
    busy = true;
    loadingSave.set(true);
    loadError.set(null);
    try {
      const res = await api.loadFromPath(p);
      saveState.set({ loaded: true, summary: res.summary, counts: res.counts });
      toast.success(`Loaded ${res.summary.filename} (${res.counts.guilds} guilds, ${res.counts.players} players)`);
      open = false;
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      loadError.set(msg);
      toast.error(`Load failed: ${msg}`);
    } finally {
      busy = false;
      loadingSave.set(false);
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if open}
  <div class="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in" role="presentation">
    <div class="w-full max-w-lg card shadow-card-lg" role="dialog" aria-modal="true" aria-label="Load save">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-semibold text-ink-emphasis flex items-center gap-2">
          <FolderOpen size={18} class="text-accent" /> Load Save
        </h2>
        <button class="text-ink-dim hover:text-ink-primary" onclick={close} disabled={busy} aria-label="Close">
          <X size={18} />
        </button>
      </div>

      <label for="save-path" class="block text-xs font-medium text-ink-secondary mb-1.5">
        Path to Level.sav
      </label>
      <input
        id="save-path"
        class="input font-mono text-xs"
        placeholder="/path/to/Saved/0/Level.sav"
        bind:value={path}
        onkeydown={(e) => e.key === 'Enter' && doLoad()}
      />
      <p class="mt-2 text-xs text-ink-muted">
        Must be inside a save folder that contains a <code class="text-ink-secondary">Players/</code> sibling directory.
      </p>

      {#if $loadError}
        <p class="mt-3 text-xs text-status-error bg-status-error/10 border border-status-error/30 rounded-6 p-2">
          {$loadError}
        </p>
      {/if}

      <div class="flex justify-end gap-2 mt-5">
        <Button variant="ghost" onclick={close} disabled={busy}>Cancel</Button>
        <Button variant="primary" onclick={doLoad} disabled={busy || !path.trim()}>
          {#if busy}<Spinner size={14} />{/if}
          Load
        </Button>
      </div>
    </div>
  </div>
{/if}
