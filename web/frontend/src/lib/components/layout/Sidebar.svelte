<script lang="ts">
  import { page } from '$app/stores';
  import { saveLoaded } from '$stores/index';
  import {
    Wrench, Users, Building2, MapPin, Map as MapIcon, Package,
    Warehouse, Pencil, ShieldOff, Box, Archive, Settings,
  } from '@lucide/svelte';
  import type { Component } from 'svelte';

  interface NavItem { href: string; label: string; icon: Component; needsSave?: boolean; }
  interface NavGroup { label: string; items: NavItem[]; }

  // Mirrors web/.web_ref/pstmain/core/constants.py NAV_GROUPS (layout only).
  const groups: NavGroup[] = [
    {
      label: 'Tools',
      items: [
        { href: '/', label: 'Overview', icon: Wrench },
        { href: '/tools', label: 'All Tools', icon: Wrench },
        { href: '/players', label: 'Players', icon: Users, needsSave: true },
        { href: '/guilds', label: 'Guilds', icon: Building2, needsSave: true },
        { href: '/bases', label: 'Bases', icon: MapPin, needsSave: true },
        { href: '/map', label: 'Map', icon: MapIcon, needsSave: true },
      ],
    },
    {
      label: 'Editors',
      items: [
        { href: '/inventory', label: 'Player Inventory', icon: Package, needsSave: true },
        { href: '/base-inventory', label: 'Base Inventory', icon: Warehouse, needsSave: true },
        { href: '/pal-editor', label: 'Pal Editor', icon: Pencil, needsSave: true },
      ],
    },
    {
      label: 'Utilities',
      items: [
        { href: '/containers', label: 'Containers', icon: Box, needsSave: true },
        { href: '/exclusions', label: 'Exclusions', icon: ShieldOff, needsSave: true },
        { href: '/backups', label: 'Backups', icon: Archive },
        { href: '/settings', label: 'Settings', icon: Settings },
      ],
    },
  ];

  function isActive(href: string): boolean {
    if (href === '/') return $page.url.pathname === '/';
    return $page.url.pathname.startsWith(href);
  }
</script>

<aside class="relative h-full w-56 shrink-0 flex flex-col bg-nav-gradient border-r border-line/50">
  <div class="flex items-center gap-2.5 px-4 h-14 border-b border-line/40 shrink-0">
    <div class="w-6 h-6 rounded-4 bg-accent-gradient shrink-0 shadow-glow"></div>
    <span class="font-semibold text-ink-emphasis text-sm tracking-wide">PalworldSaveTools</span>
  </div>

  <nav class="flex-1 overflow-y-auto py-3 px-2 space-y-4">
    {#each groups as group}
      <div>
        <p class="px-3 mb-1 text-[10px] font-semibold uppercase tracking-widest text-ink-dim">
          {group.label}
        </p>
        <div class="space-y-0.5">
          {#each group.items as item}
            <a
              href={item.href}
              class="nav-link {isActive(item.href) ? 'nav-link-active' : 'nav-link-inactive'}"
              class:opacity-40={item.needsSave && !$saveLoaded}
              title={item.needsSave && !$saveLoaded ? 'Load a save to enable' : item.label}
            >
              <item.icon size={16} class="shrink-0" />
              <span class="truncate">{item.label}</span>
            </a>
          {/each}
        </div>
      </div>
    {/each}
  </nav>

  <div class="px-3 py-3 border-t border-line/40 text-[10px] text-ink-dim">
    Read-only viewers · Editing in phase 2
  </div>
</aside>
