<script lang="ts">
  import type { Snippet, Component } from 'svelte';
  import { saveLoaded } from '$stores/index';
  import EmptyState from '$components/ui/EmptyState.svelte';
  import { FileX } from '@lucide/svelte';

  let {
    icon = FileX as Component,
    children,
  }: { icon?: Component; children: Snippet } = $props();
</script>

{#if !$saveLoaded}
  <div class="p-6 max-w-4xl mx-auto animate-fade-in">
    <div class="card">
      <EmptyState {icon} title="No save loaded">
        <p>Load a <code class="text-accent-light">Level.sav</code> from the Overview page first.</p>
      </EmptyState>
    </div>
  </div>
{:else}
  {@render children()}
{/if}
