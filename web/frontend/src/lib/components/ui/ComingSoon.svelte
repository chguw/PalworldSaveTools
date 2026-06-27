<script lang="ts">
  import type { Component } from 'svelte';
  import Card from '$components/ui/Card.svelte';
  import { Construction } from '@lucide/svelte';

  let {
    icon: Icon = Construction,
    title,
    description = '',
    phase = 'Phase 2',
  }: { icon?: Component; title: string; description?: string; phase?: string } = $props();
</script>

<div class="p-6 max-w-3xl mx-auto animate-fade-in">
  <Card>
    <div class="flex flex-col items-center text-center py-10 px-4">
      <div class="w-14 h-14 rounded-12 bg-accent/10 border border-accent/30 flex items-center justify-center mb-4">
        <Icon size={26} class="text-accent" />
      </div>
      <span class="badge bg-status-amber/15 border-status-amber/40 text-status-amber mb-3">{phase}</span>
      <h1 class="text-xl font-bold text-ink-emphasis">{title}</h1>
      {#if description}
        <p class="mt-2 text-sm text-ink-muted max-w-md">{description}</p>
      {/if}
    </div>
  </Card>
</div>
