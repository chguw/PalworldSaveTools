<script lang="ts">
  import { toasts, dismissToast } from '$stores/toast';
  import { CircleCheck, TriangleAlert, Info, CircleX, X } from '@lucide/svelte';
  import type { Component } from 'svelte';
  import type { ToastKind } from '$stores/toast';

  const iconFor: Record<ToastKind, Component> = {
    success: CircleCheck,
    warning: TriangleAlert,
    error: CircleX,
    info: Info,
  };
  const toneFor: Record<ToastKind, string> = {
    success: 'border-status-success/50 text-status-success',
    warning: 'border-status-amber/50 text-status-amber',
    error: 'border-status-error/50 text-status-error',
    info: 'border-accent/50 text-accent-light',
  };
</script>

<div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-[90vw]">
  {#each $toasts as toast (toast.id)}
    {@const Icon = iconFor[toast.kind]}
    <div
      class="flex items-start gap-2.5 p-3 rounded-8 bg-bg-card/95 backdrop-blur
             border shadow-card-lg animate-slide-up {toneFor[toast.kind]}"
    >
      <Icon size={18} class="shrink-0 mt-0.5" />
      <p class="flex-1 text-sm text-ink-primary leading-snug">{toast.message}</p>
      <button class="text-ink-dim hover:text-ink-primary" onclick={() => dismissToast(toast.id)}>
        <X size={14} />
      </button>
    </div>
  {/each}
</div>
