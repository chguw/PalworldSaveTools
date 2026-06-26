# WebUI Shell + Theme Redesign — Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/webui-shell-redesign.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the PST WebUI frontend shell (Header + Sidebar + main Content) to high-fidelity match the scraped Reflex reference, fixing the unimported font, dropping the cluttered Header cascade, replacing magic `calc()` heights with flexbox, and removing the orphaned DetailPanel.

**Architecture:** In-place rewrite of 4 frontend files (`+layout.svelte`, `Sidebar.svelte`, `Header.svelte`, `app.css`) + 2 asset copies + 1 deletion. SvelteKit 2 / Svelte 5 runes / Tailwind v4 CSS-first. The existing `@theme` color tokens already match the reference exactly, so theme work is fonts only. Backend, stores, and route pages are untouched.

**Tech Stack:** SvelteKit ^2.20, Svelte ^5.25 (runes), Tailwind v4 (`@tailwindcss/vite`), lucide-svelte ^1.0.1, vitest ^4.1.

**Spec:** `docs/compose/specs/2026-06-26-webui-shell-redesign-design.md`

**Honest note on the current code:** Exploration found the `Sidebar.svelte` already implements ~90% of the reference (correct 3 groups / 12 routes, collapse, glowing active dot, gradient bg). The biggest fidelity breaks are elsewhere: the `'Inter'` font is referenced but never imported (silent fallback), the Header carries a 110-line dead cascade menu with no logo, the layout uses fragile `h-[calc(100vh-56px)]`, and `DetailPanel.svelte` is built but never mounted. This plan targets those real breaks rather than churning what already matches.

**Verification strategy (TDD adaptation):** These are layout/CSS/markup changes — unit-testing "does this `<div>` have class `p-8`" is bad test design. Verification is: `npm run check` (svelte-check: types + unused-import detection, catches dropped imports / dangling refs), `npm run build` (full compile), `npm run test` (existing vitest store tests must stay green), and a manual `npm run dev` visual check. No new unit tests are added.

**Git:** Per repo git-safety (AGENTS.md), commits are deferred — stage files per task but only commit when the user explicitly asks. The commit steps below are the intended messages when approved.

**Working directory for all commands:** `web/frontend/`

---

### Task 1: Copy reference assets into `static/`

**Covers:** [S8]

**Files:**
- Add: `web/frontend/static/images/PalworldSaveTools.png`
- Add: `web/frontend/static/fonts/HackNerdFont-Regular.ttf`

- [ ] **Step 1: Copy the logo**

```bash
cp /mnt/dev/Dev/Coding_Projects/PalworldSaveTools/reflex_branch/assets/images/PalworldSaveTools.png \
   /mnt/dev/Dev/Coding_Projects/PalworldSaveTools/pst_dev/web/frontend/static/images/PalworldSaveTools.png
```

- [ ] **Step 2: Copy the mono font**

```bash
mkdir -p /mnt/dev/Dev/Coding_Projects/PalworldSaveTools/pst_dev/web/frontend/static/fonts
cp /mnt/dev/Dev/Coding_Projects/PalworldSaveTools/reflex_branch/assets/fonts/HackNerdFont-Regular.ttf \
   /mnt/dev/Dev/Coding_Projects/PalworldSaveTools/pst_dev/web/frontend/static/fonts/HackNerdFont-Regular.ttf
```

- [ ] **Step 3: Verify both landed**

Run: `ls -l web/frontend/static/images/PalworldSaveTools.png web/frontend/static/fonts/HackNerdFont-Regular.ttf`
Expected: both files present; logo ~94 KB, font ~2.6 MB.

---

### Task 2: Fix fonts in `app.css`

**Covers:** [S7]

**Files:**
- Modify: `web/frontend/src/app.css`

- [ ] **Step 1: Add font tokens to the `@theme` block**

In `web/frontend/src/app.css`, inside the `@theme { ... }` block, immediately before its closing `}` (currently line 37), add:

```css
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Hack Nerd Font', ui-monospace, Consolas, 'Liberation Mono', Menlo, monospace;
```

- [ ] **Step 2: Add the `@font-face` for Hack Nerd Font**

Immediately after the `@theme { ... }` block closes and before `html, body {`, add:

```css
@font-face {
  font-family: 'Hack Nerd Font';
  src: url('/fonts/HackNerdFont-Regular.ttf') format('truetype');
  font-display: swap;
}
```

- [ ] **Step 3: Switch the body font from the unimported `'Inter'` to the token**

In the `html, body { ... }` rule, change the `font-family` declaration from:

```css
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

to:

```css
  font-family: var(--font-sans);
```

- [ ] **Step 4: Verify the build picks up the CSS**

Run: `npm run build` (in `web/frontend/`)
Expected: builds successfully, no CSS/postcss errors.

---

### Task 3: Rewrite `Header.svelte` — clean top bar, drop the cascade, add logo

**Covers:** [S6]

**Files:**
- Rewrite: `web/frontend/src/lib/components/shell/Header.svelte`

**Consequence to flag:** dropping the cascade also removes the in-menu Language picker (it lived inside the cascade). The `currentLanguage` / `availableLanguages` store fields remain intact for a future standalone language control. Backend/store logic is untouched.

- [ ] **Step 1: Replace the entire file with the clean top bar**

Overwrite `web/frontend/src/lib/components/shell/Header.svelte` with:

```svelte
<script lang="ts">
  import { displayVersion, gameVersion } from '$lib/stores/shell';
  import ExternalLink from 'lucide-svelte/icons/external-link';
  import Save from 'lucide-svelte/icons/save';
  import Info from 'lucide-svelte/icons/info';
  import TriangleAlert from 'lucide-svelte/icons/triangle-alert';
  import MessageCircle from 'lucide-svelte/icons/message-circle';
</script>

<header class="h-14 shrink-0 flex items-center gap-2 px-2.5 bg-gradient-header border-b border-border-default shadow-[0_2px_8px_rgba(0,0,0,0.2)] z-[1000]">
  <img src="/images/PalworldSaveTools.png" alt="Palworld Save Tools" class="h-11 shrink-0" />
  <span class="text-text-primary font-semibold text-sm select-none mr-1">Palworld Save Tools</span>

  <button
    onclick={() => window.open('https://github.com/deadafdudecomputers/PalworldSaveTools/releases/latest', '_blank')}
    class="flex items-center gap-1.5 px-3 py-1.5 rounded-[10px] bg-alpha-sky-08 border border-alpha-sky-12 text-header-sky text-[13px] font-medium cursor-pointer transition-all duration-150 hover:bg-alpha-sky-12 whitespace-nowrap"
    title="Latest release"
  >
    <ExternalLink size={14} />
    <span>v{$displayVersion}</span>
  </button>

  <span class="flex items-center gap-1.5 px-3 py-1.5 rounded-[10px] bg-alpha-green-08 border border-alpha-green-12 text-header-green text-[13px] font-medium select-none whitespace-nowrap">
    <Save size={14} />
    <span>{$gameVersion}</span>
  </span>

  <button class="flex items-center justify-center size-8 rounded-md text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all duration-150 cursor-pointer" title="About PST">
    <Info size={18} />
  </button>

  <button class="flex items-center justify-center size-8 rounded-md text-status-warning hover:bg-white/5 transition-all duration-150 cursor-pointer" title="Warnings">
    <TriangleAlert size={18} />
  </button>

  <div class="flex-1" />

  <button
    onclick={() => window.open('https://discord.gg/sYcZwcT4cT', '_blank')}
    class="flex items-center gap-1.5 px-3 py-2 rounded-md text-header-discord hover:bg-[rgba(88,101,242,0.1)] transition-all duration-150 cursor-pointer"
    title="Join Discord"
  >
    <MessageCircle size={20} />
  </button>
</header>
```

- [ ] **Step 2: Verify type-check passes (catches dropped imports)**

Run: `npm run check` (in `web/frontend/`)
Expected: PASS, 0 errors, 0 warnings. If it reports unused imports or missing refs, the file wasn't fully replaced — re-apply Step 1.

---

### Task 4: Polish `Sidebar.svelte` — Svelte transitions + active weight

**Covers:** [S5]

**Files:**
- Rewrite: `web/frontend/src/lib/components/shell/Sidebar.svelte`

**Why a rewrite not a patch:** the current file already matches the reference closely; the rewrite collapses the `iconMap` indirection (icons referenced directly), adds `svelte/transition` `fade` on collapsing labels/group-labels, and bumps the active item to `font-semibold`. Net effect is a cleaner, slightly smaller file.

- [ ] **Step 1: Replace the entire file**

Overwrite `web/frontend/src/lib/components/shell/Sidebar.svelte` with:

```svelte
<script lang="ts">
  import { fade } from 'svelte/transition';
  import { leftNavCollapsed, toggleLeftNav } from '$lib/stores/shell';
  import { page } from '$app/stores';
  import Wrench from 'lucide-svelte/icons/wrench';
  import Users from 'lucide-svelte/icons/users';
  import Building2 from 'lucide-svelte/icons/building-2';
  import MapPin from 'lucide-svelte/icons/map-pin';
  import MapIcon from 'lucide-svelte/icons/map';
  import Package from 'lucide-svelte/icons/package';
  import Warehouse from 'lucide-svelte/icons/warehouse';
  import Pencil from 'lucide-svelte/icons/pencil';
  import ShieldOff from 'lucide-svelte/icons/shield-off';
  import Box from 'lucide-svelte/icons/box';
  import Archive from 'lucide-svelte/icons/archive';
  import Settings from 'lucide-svelte/icons/settings';
  import ChevronsLeft from 'lucide-svelte/icons/chevrons-left';
  import ChevronsRight from 'lucide-svelte/icons/chevrons-right';

  type Icon = typeof Wrench;
  interface NavItem { label: string; route: string; icon: Icon }
  interface NavGroup { label: string; items: NavItem[] }

  const navGroups: NavGroup[] = [
    { label: 'Tools', items: [
      { label: 'All Tools', route: '/', icon: Wrench },
      { label: 'Players', route: '/players', icon: Users },
      { label: 'Guilds', route: '/guilds', icon: Building2 },
      { label: 'Bases', route: '/bases', icon: MapPin },
      { label: 'Map', route: '/map', icon: MapIcon },
    ]},
    { label: 'Editors', items: [
      { label: 'Player Inventory', route: '/inventory', icon: Package },
      { label: 'Base Inventory', route: '/base-inventory', icon: Warehouse },
      { label: 'Pal Editor', route: '/pal-editor', icon: Pencil },
    ]},
    { label: 'Utilities', items: [
      { label: 'Exclusions', route: '/exclusions', icon: ShieldOff },
      { label: 'Containers', route: '/containers', icon: Box },
      { label: 'Backups', route: '/backups', icon: Archive },
      { label: 'Settings', route: '/settings', icon: Settings },
    ]},
  ];
</script>

<nav
  class="shrink-0 border-r border-border-default bg-gradient-nav flex flex-col overflow-hidden relative shadow-[4px_0_20px_rgba(0,0,0,0.3)] transition-[width,min-width] duration-[250ms] ease-[cubic-bezier(0.4,0,0.2,1)]"
  style="width: {$leftNavCollapsed ? '64px' : '240px'}; min-width: {$leftNavCollapsed ? '64px' : '240px'}"
>
  <div class="flex-1 overflow-y-auto overflow-x-hidden px-3 py-4">
    <div class="flex flex-col gap-1 w-full">
      {#each navGroups as group, i}
        <div class="w-full">
          {#if i > 0}
            <div class="h-px bg-border-default opacity-40 {$leftNavCollapsed ? 'mx-4 my-2' : 'mt-3'}" />
          {/if}
          {#if !$leftNavCollapsed}
            <span transition:fade={{ duration: 150 }} class="block px-2 text-[11px] font-bold uppercase tracking-[0.1em] text-text-muted">{group.label}</span>
          {/if}
          <div class="flex flex-col gap-0.5 w-full mt-2">
            {#each group.items as item}
              {@const isActive = $page.url.pathname === item.route}
              <a
                href={item.route}
                class="flex items-center min-h-11 rounded-[10px] transition-all duration-[250ms] ease-[cubic-bezier(0.4,0,0.2,1)] relative no-underline {$leftNavCollapsed ? 'justify-center px-0' : 'px-2'} py-2.5 gap-3 sidebar-nav-link"
                class:sidebar-nav-active={isActive}
              >
                {#if isActive}
                  <div class="absolute right-3 top-1/2 -translate-y-1/2 size-1.5 rounded-full bg-accent-primary shadow-[0_0_8px_#3B8ED099]" />
                {/if}
                <item.icon size={20} class="shrink-0" />
                {#if !$leftNavCollapsed}
                  <span transition:fade={{ duration: 150 }} class="text-sm truncate {isActive ? 'font-semibold' : 'font-medium'}">{item.label}</span>
                {/if}
              </a>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </div>

  <button
    onclick={toggleLeftNav}
    class="flex items-center justify-center gap-2 h-9 rounded-md text-text-secondary hover:text-text-primary hover:bg-alpha-primary-10 transition-colors w-full shrink-0 border-t border-border-default pt-3 cursor-pointer"
  >
    {#if $leftNavCollapsed}
      <ChevronsRight size={18} />
    {:else}
      <ChevronsLeft size={18} />
    {/if}
    {#if !$leftNavCollapsed}
      <span class="text-[13px]">Collapse</span>
    {/if}
  </button>
</nav>

<style>
  .sidebar-nav-link { color: var(--color-text-secondary); }
  .sidebar-nav-link:hover { background-color: rgba(59, 142, 208, 0.10); color: var(--color-text-primary); }
  .sidebar-nav-active { background-color: rgba(59, 142, 208, 0.15); color: var(--color-text-primary); }
  .sidebar-nav-active:hover { background-color: rgba(59, 142, 208, 0.25); }
</style>
```

- [ ] **Step 2: Verify type-check passes**

Run: `npm run check` (in `web/frontend/`)
Expected: PASS, 0 errors, 0 warnings. The `Icon = typeof Wrench` type and `<item.icon .../>` usage must type-check cleanly.

---

### Task 5: Restructure `+layout.svelte` — flex shell, drop magic `calc()`

**Covers:** [S4]

**Files:**
- Rewrite: `web/frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Replace the entire file**

Overwrite `web/frontend/src/routes/+layout.svelte` with:

```svelte
<script lang="ts">
  import '../app.css';
  import Header from '$lib/components/shell/Header.svelte';
  import Sidebar from '$lib/components/shell/Sidebar.svelte';

  let { children } = $props();
</script>

<div class="h-screen w-screen overflow-hidden flex flex-col bg-bg-base text-text-primary">
  <Header />
  <div class="flex flex-1 min-h-0">
    <Sidebar />
    <main class="flex-1 min-w-0 overflow-y-auto bg-gradient-content">
      <div class="mx-auto w-full max-w-[1280px] px-8 py-8 flex flex-col gap-4 min-h-full">
        {@render children()}
      </div>
    </main>
  </div>
</div>
```

Key changes vs. current: `h-screen w-screen` + `text-text-primary` on root; `flex flex-1 min-h-0` replaces `h-[calc(100vh-56px)]` (the `min-h-0` is what makes the inner `overflow-y-auto` work without pixel math); content padding `px-8 py-8` moves to the inner wrapper; `DetailPanel` was never imported here, so nothing to remove.

- [ ] **Step 2: Verify type-check passes**

Run: `npm run check` (in `web/frontend/`)
Expected: PASS, 0 errors, 0 warnings.

---

### Task 6: Delete the orphaned `DetailPanel.svelte`

**Covers:** [S9], [S10]

**Files:**
- Delete: `web/frontend/src/lib/components/shell/DetailPanel.svelte`

- [ ] **Step 1: Confirm nothing references DetailPanel**

Run: `grep -rn "DetailPanel" web/frontend/src` (or ripgrep `rg -n "DetailPanel" web/frontend/src`)
Expected: matches ONLY inside `DetailPanel.svelte` itself (its own `<script>`/class names). If any OTHER file imports it, stop and remove that import first.

- [ ] **Step 2: Delete the file**

```bash
rm web/frontend/src/lib/components/shell/DetailPanel.svelte
```

- [ ] **Step 3: Verify the build still compiles without it**

Run: `npm run build` (in `web/frontend/`)
Expected: builds successfully (confirms no dangling import).

---

### Task 7: Full verification

**Covers:** [S11]

- [ ] **Step 1: Type-check the whole frontend**

Run: `npm run check` (in `web/frontend/`)
Expected: PASS, 0 errors, 0 warnings.

- [ ] **Step 2: Full production build**

Run: `npm run build` (in `web/frontend/`)
Expected: builds successfully into `build/`.

- [ ] **Step 3: Existing tests stay green**

Run: `npm run test` (in `web/frontend/`)
Expected: all existing vitest store tests pass (no store logic was touched).

- [ ] **Step 4: Manual visual check**

Run: `npm run dev` (in `web/frontend/`), open the local URL, and confirm:
- Sidebar collapses 240px ↔ 64px smoothly; labels fade (Svelte transition).
- Active nav shows the glowing dot + `font-semibold` label on each of the 12 routes.
- Header shows the logo (44px) + "Palworld Save Tools" title + version pill (sky) + game-version pill (green) + About/Warnings + Discord; NO cascade menu.
- Main content canvas is 1280px-centered with 32px padding; pages scroll within `<main>`.
- Hack Nerd Font renders on any monospace text (e.g. pal IDs / coordinates on the Pal Editor page).

- [ ] **Step 5: Stage all changes (commit deferred to user request)**

```bash
git add web/frontend/static/images/PalworldSaveTools.png \
        web/frontend/static/fonts/HackNerdFont-Regular.ttf \
        web/frontend/src/app.css \
        web/frontend/src/app.html \
        web/frontend/src/routes/+layout.svelte \
        web/frontend/src/lib/components/shell/Header.svelte \
        web/frontend/src/lib/components/shell/Sidebar.svelte
git rm web/frontend/src/lib/components/shell/DetailPanel.svelte
git status
```

Intended commit message (run only when the user asks to commit):
`feat(web): redesign shell (Header/Sidebar/layout) + system-ui/Hack Nerd Font theme; drop Header cascade and orphaned DetailPanel`

---

## Self-Review (ran after writing)

- **Spec coverage:** [S1] problem (context only, no task needed) ✓; [S2]/[S3] decisions (context) ✓; [S4] layout → Task 5 ✓; [S5] sidebar → Task 4 ✓; [S6] header → Task 3 ✓; [S7] theme → Task 2 ✓; [S8] assets → Task 1 ✓; [S9]/[S10] files/out-of-scope (delete DetailPanel) → Task 6 ✓; [S11] verification → Task 7 ✓. All sections covered.
- **Placeholder scan:** none — every code step contains the full target file content.
- **Type consistency:** Header reads `displayVersion`/`gameVersion` (matches the existing store exports in `shell.ts`); Sidebar imports `leftNavCollapsed`/`toggleLeftNav` (existing exports); `Icon = typeof Wrench` is consistent across the `navGroups` literal and the `<item.icon />` render. Note: spec [S6] mentioned `appVersion`; the implementation uses `displayVersion` (the field the current code already wired for the displayed version) — same default value, avoids introducing a second version field.
- **app.html:** spec [S9] listed an optional font preload; with `@font-face` + `font-display: swap` a preload is unnecessary, so it is intentionally not modified (YAGNI). The `git add app.html` line in Task 7 Step 5 is a no-op if unchanged.
