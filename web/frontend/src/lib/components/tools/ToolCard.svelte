<script lang="ts">
  import type { ToolInfo } from '$types/index';
  import {
    FileSymlink, Hash, PackagePlus, Map, Wrench,
    Gamepad2, FileArchive, ArrowRightFromLine, UserRoundPlus,
    Users, HardDrive,
  } from '@lucide/svelte';
  let { tool, onSelect }: {
    tool: ToolInfo;
    onSelect: (id: string) => void;
  } = $props();

  const iconMap: Record<string, typeof FileSymlink> = {
    FileSymlink, Hash, PackagePlus, Map, Wrench,
    Gamepad2, FileArchive, ArrowRightFromLine, UserRoundPlus,
    Users, HardDrive,
  };

  const iconColors: Record<string, string> = {
    converting: 'text-sky-400',
    management: 'text-amber-400',
    utility: 'text-emerald-400',
  };

  const iconBgs: Record<string, string> = {
    converting: 'bg-sky-500/10',
    management: 'bg-amber-500/10',
    utility: 'bg-emerald-500/10',
  };

  let Icon = $derived(iconMap[tool.icon] ?? Wrench);
</script>

<button
  class="card card-hover group cursor-pointer text-left w-full"
  class:opacity-50={tool.windows_only}
  onclick={() => onSelect(tool.id)}
>
  <div class="flex items-start gap-3 px-4 py-3">
    <div class="w-9 h-9 rounded-lg {iconBgs[tool.category] ?? 'bg-surface-hover'} flex items-center justify-center shrink-0 mt-0.5">
      <Icon class="w-4 h-4 {iconColors[tool.category] ?? 'text-ink-muted'}" />
    </div>
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <span class="font-semibold text-sm text-ink-emphasis group-hover:text-accent transition-colors truncate">
          {tool.name}
        </span>
        <div class="flex items-center gap-1.5 shrink-0">
          {#if tool.category === 'converting'}
            <span class="chip chip-blue text-[10px]">Converting</span>
          {:else if tool.category === 'management'}
            <span class="chip chip-amber text-[10px]">Management</span>
          {:else}
            <span class="chip chip-green text-[10px]">Utility</span>
          {/if}
          {#if tool.windows_only}
            <span class="chip text-[10px] bg-purple-500/10 text-purple-400">Windows</span>
          {/if}
        </div>
      </div>
      <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">
        {tool.description}
      </p>
    </div>
  </div>
</button>
