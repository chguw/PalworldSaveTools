<script lang="ts">
  import type { Snippet } from 'svelte';
  import clsx from 'clsx';

  let {
    title = '',
    class: klass = '',
    hover = false,
    children,
  }: { title?: string; class?: string; hover?: boolean; children: Snippet } = $props();
</script>

<section class={clsx('card', hover && 'card-hover', klass)}>
  {#if title}
    <h3 class="card-header">{title}</h3>
  {/if}
  {@render children()}
</section>
