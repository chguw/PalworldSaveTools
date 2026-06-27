<script lang="ts">
  import type { ToolInfo } from '$types/index';
  import ToolCard from './ToolCard.svelte';

  let { tools, onSelectTool }: {
    tools: ToolInfo[];
    onSelectTool: (id: string) => void;
  } = $props();

  let categories = $derived<{ label: string; key: string; tools: ToolInfo[] }[]>([
    {
      label: 'Converting',
      key: 'converting',
      tools: tools.filter((t) => t.category === 'converting'),
    },
    {
      label: 'Management',
      key: 'management',
      tools: tools.filter((t) => t.category === 'management'),
    },
    {
      label: 'Utility',
      key: 'utility',
      tools: tools.filter((t) => t.category === 'utility'),
    },
  ]);
</script>

<div class="space-y-6">
  {#each categories as cat (cat.key)}
    {#if cat.tools.length > 0}
      <section>
        <h2 class="text-sm font-semibold text-ink-emphasis mb-2 flex items-center gap-2">
          {cat.label}
          <span class="text-xs text-ink-dim font-normal">({cat.tools.length})</span>
        </h2>
        <div class="flex flex-col gap-1">
          {#each cat.tools as tool (tool.id)}
            <ToolCard {tool} onSelect={onSelectTool} />
          {/each}
        </div>
      </section>
    {/if}
  {/each}
</div>
