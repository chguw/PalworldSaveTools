<script lang="ts">
  import type { Snippet } from 'svelte';
  import clsx from 'clsx';

  type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

  let {
    variant = 'secondary' as Variant,
    disabled = false,
    loading = false,
    onclick,
    class: klass = '',
    type = 'button',
    children,
  }: {
    variant?: Variant;
    disabled?: boolean;
    loading?: boolean;
    onclick?: (e: MouseEvent) => void;
    class?: string;
    type?: 'button' | 'submit';
    children: Snippet;
  } = $props();

  const variantClass: Record<Variant, string> = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    ghost: 'btn-ghost',
    danger: 'btn-danger',
  };
</script>

<button
  {type}
  class={clsx(variantClass[variant], klass)}
  disabled={disabled || loading}
  {onclick}
>
  {#if loading}
    <span class="inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
  {/if}
  {@render children()}
</button>
