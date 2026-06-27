<script lang="ts">
  import type { Snippet } from 'svelte';
  import clsx from 'clsx';

  type Tone = 'neutral' | 'accent' | 'success' | 'warning' | 'error' | 'amber';

  let {
    tone = 'neutral' as Tone,
    class: klass = '',
    children,
  }: { tone?: Tone; class?: string; children: Snippet } = $props();

  const tones: Record<Tone, string> = {
    neutral: 'bg-bg-elevated border-line text-ink-secondary',
    accent: 'bg-accent/15 border-accent/40 text-accent-light',
    success: 'bg-status-success/15 border-status-success/40 text-status-success',
    warning: 'bg-status-warning/15 border-status-warning/40 text-status-warning',
    error: 'bg-status-error/15 border-status-error/40 text-status-error',
    amber: 'bg-status-amber/15 border-status-amber/40 text-status-amber',
  };
</script>

<span class={clsx('badge', tones[tone], klass)}>
  {@render children()}
</span>
