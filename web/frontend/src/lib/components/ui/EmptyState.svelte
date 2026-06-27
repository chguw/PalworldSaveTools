<script lang="ts">
  import type { Component, Snippet } from 'svelte';
  import { Inbox } from '@lucide/svelte';

  let {
    icon: Icon = Inbox,
    title = 'Nothing here yet',
    class: klass = '',
    children,
  }: {
    icon?: Component;
    title?: string;
    class?: string;
    children?: Snippet;
  } = $props();
</script>

<div class={klass}>
  <div class="flex flex-col items-center justify-center text-center py-12 px-4">
    <Icon size={32} class="text-ink-dim mb-3" />
    <p class="text-ink-secondary font-medium">{title}</p>
    {#if children}
      <div class="mt-2 text-sm text-ink-muted">{@render children()}</div>
    {/if}
  </div>
</div>
