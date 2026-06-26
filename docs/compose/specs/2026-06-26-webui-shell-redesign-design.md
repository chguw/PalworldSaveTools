# WebUI Shell + Theme Redesign — Design Spec

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/webui-shell-redesign.md)

**Date:** 2026-06-26
**Status:** Approved (Approach A)
**Scope:** Visual/structural redesign of the SvelteKit frontend shell to high-fidelity match the scraped Reflex reference (`web/.web_ref`, sourced from `reflex_branch/`). Backend logic untouched.

## [S1] Problem

The existing `web/frontend/` SvelteKit app is functional but its shell does not faithfully match the reference visual design. Concrete gaps discovered during exploration:

- **Orphaned `DetailPanel.svelte`** — built but never mounted in `+layout.svelte`; the 3-pane design intent is unrealized.
- **Magic-number heights** — `+layout.svelte` uses `h-[calc(100vh-56px)]`; route pages use fragile inline `calc(100vh - 56px - 64px - 28px - 32px)` sums.
- **Unimported font** — `app.css` references `'Inter'` with no `@font-face`/Google link → silent fallback.
- **Dead Header cascade** — a large multi-level "Functions" menu with action stubs that only handle `redirect`.
- **`@theme` tokens already match the reference** — the color system is correct; the execution fidelity is what's broken.

## [S2] Solution overview

Ground-up rewrite of the **three structural pillars** (Header, Sidebar, main Content canvas) + the theme layer, matching the reference's exact dimensions, colors, gradients, and motion. Keep the existing Tailwind v4 `@theme` tokens (they already mirror `reflex_branch/styles/colors.py`). Reuse the existing `shell.ts` store fields. Drop the right `DetailPanel` (the three pillars are Header + Sidebar + Content).

**Approach:** In-place rewrite of 4 files (`+layout.svelte`, `Sidebar.svelte`, `Header.svelte`, `app.css`) + `app.html` font preload. Delete `DetailPanel.svelte`. Copy 2 assets into `static/`. No new abstraction layer.

## [S3] Resolved decisions

| Decision | Choice |
|---|---|
| Pane layout | **2-pane**: Header + Sidebar + Content. No right DetailPanel. |
| Header content | **Clean top bar** — logo + version/game pills + quick-action icons + Discord. Drop the cascade menu. |
| Typography | **system-ui** body + **Hack Nerd Font** mono (import ttf from `reflex_branch/assets/fonts/`). |
| Execution style | In-place rewrite; nav items inline in `Sidebar` (matches reference `NAV_GROUPS`). |
| Responsive | Desktop-locked app shell (`overflow: hidden`, fixed-height) — matches reference. No mobile. |

## [S4] Layout shell (`+layout.svelte`)

Replaces the magic `calc()` with proper flexbox + `min-h-0`:

```svelte
<div class="h-screen w-screen overflow-hidden flex flex-col bg-bg-base text-text-primary">
  <Header />                              <!-- h-14, flex-shrink-0 -->
  <div class="flex flex-1 min-h-0">       <!-- min-h-0 fixes the overflow chain -->
    <Sidebar />                           <!-- flex-shrink-0 -->
    <main class="flex-1 min-w-0 overflow-y-auto bg-gradient-content">
      <div class="mx-auto w-full max-w-[1280px] px-8 py-8 flex flex-col gap-4 min-h-full">
        {@render children()}
      </div>
    </main>
  </div>
</div>
```

Matches reference: content `padding: 32px`, inner `max-width: 1280px`, `gap: 16px`, `overflow-y: auto`, bg `gradient.content_bg`. Imports: drop `DetailPanel`; keep `Header`, `Sidebar`, `app.css`.

## [S5] Sidebar (`Sidebar.svelte`)

**Container** — width toggled via inline `style` (240px ↔ 64px), `transition-[width] duration-250 ease-[cubic-bezier(0.4,0,0.2,1)]`, classes `bg-gradient-nav border-r border-border-default shadow-[4px_0_20px_rgba(0,0,0,0.3)]`, inner `p-3`, `flex flex-col`. Collapse state read from `leftNavCollapsed`, toggled via `toggleLeftNav()` (both from `$lib/stores/shell`).

**Navigation** — 3 groups / 12 routes, lucide-svelte icons, exact match to reference `NAV_GROUPS`:
- **Tools**: All Tools `wrench` `/` · Players `users` `/players` · Guilds `building-2` `/guilds` · Bases `map-pin` `/bases` · Map `map` `/map`
- **Editors**: Player Inventory `package` `/inventory` · Base Inventory `warehouse` `/base-inventory` · Pal Editor `pencil` `/pal-editor`
- **Utilities**: Exclusions `shield-off` `/exclusions` · Containers `box` `/containers` · Backups `archive` `/backups` · Settings `settings` `/settings`

**Group label** — `px-2 pt-3 pb-1 text-[11px] font-bold uppercase tracking-[0.1em] text-text-muted`; wrapped in `{#if !collapsed}` with `svelte/transition` `fade` so labels hide when collapsed.

**Nav item** — `relative flex items-center gap-3 min-h-[44px] px-2 rounded-[10px] text-sm transition-all duration-250 ease-[cubic-bezier(0.4,0,0.2,1)]`, icon `size-5` (20px).
- Inactive: `text-text-secondary hover:bg-alpha-primary-10`
- Active (`$page.url.pathname === item.route`): `text-text-primary font-semibold bg-alpha-primary-15` + glowing indicator dot `absolute right-3 size-1.5 rounded-full bg-accent-primary shadow-[0_0_8px_rgba(59,142,208,0.99)]`
- Label wrapped in `{#if !collapsed}` with `svelte/transition` `fade`.

**Collapse button** — pinned at bottom: `chevrons-left` (expanded) / `chevrons-right` (collapsed), size 18px, calls `toggleLeftNav()`.

## [S6] Header (`Header.svelte`)

**Container** — `<header class="h-14 flex-shrink-0 flex items-center justify-between px-2.5 bg-gradient-header border-b border-border-default shadow-[0_2px_8px_rgba(0,0,0,0.2)] z-[1000]">`.

**Left** — logo `<img src="/images/PalworldSaveTools.png" alt="PST" class="h-11" />` (44px) + app title (`text-text-primary font-semibold`).

**Right** —
- Version pill: `bg-alpha-sky-08 border border-alpha-primary-20 text-header-sky rounded-full px-2 py-0.5 text-xs` reading `$appVersion`.
- Game-version pill: green variant (`text-header-green`) reading `$gameVersion`.
- Quick-action icon buttons: About, Warnings — `text-text-muted hover:text-text-primary hover:bg-white/5 rounded-lg p-2 transition-colors`.
- Discord link: `text-header-discord hover:bg-header-discord-hover rounded-lg p-2`.

**Removed:** the entire multi-level cascade menu (`menuOpen`/`activeSubmenu` state, 6-category dropdown, backdrop). All values read from `shell.ts` (`appVersion`, `gameVersion`).

## [S7] Theme (`app.css`)

- **`@theme` tokens:** keep the existing block — it already mirrors `reflex_branch/styles/colors.py` exactly (bg/accent/status/text/border/header-* scales).
- **Fonts:** add to `@theme`:
  - `--font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`
  - `--font-mono: 'Hack Nerd Font', ui-monospace, Consolas, 'Liberation Mono', Menlo, monospace;`
  - `@font-face { font-family: 'Hack Nerd Font'; src: url('/fonts/HackNerdFont-Regular.ttf') format('truetype'); font-display: swap; }`
  - Change `html, body` `font-family` from `'Inter', system-ui, ...` to `var(--font-sans)`.
- **Gradients / alpha utilities / keyframes:** keep existing (they're correct); no functional change.

## [S8] Assets

Copy into `web/frontend/static/`:
- `reflex_branch/assets/images/PalworldSaveTools.png` → `static/images/PalworldSaveTools.png`
- `reflex_branch/assets/fonts/HackNerdFont-Regular.ttf` → `static/fonts/HackNerdFont-Regular.ttf`

## [S9] Files touched

| Action | Path |
|---|---|
| Rewrite | `web/frontend/src/routes/+layout.svelte` |
| Rewrite | `web/frontend/src/lib/components/shell/Sidebar.svelte` |
| Rewrite | `web/frontend/src/lib/components/shell/Header.svelte` |
| Edit | `web/frontend/src/app.css` (fonts) |
| Edit | `web/frontend/src/app.html` (font preload, optional) |
| Add | `web/frontend/static/images/PalworldSaveTools.png` |
| Add | `web/frontend/static/fonts/HackNerdFont-Regular.ttf` |
| Delete | `web/frontend/src/lib/components/shell/DetailPanel.svelte` |

## [S10] Out of scope

- Backend (`web/backend/`) — no changes.
- `lib/api/` + `lib/stores/` — reused as-is (read-only consumers of `shell.ts`).
- Route page internals (`+page.svelte`) — including their inline `calc()` heights (a follow-up cleanup; the new flex shell makes those resolvable later).
- Responsive/mobile design.
- Wiring the now-removed Header menu actions (the cascade is dropped, not migrated).

## [S11] Verification

- `npm run build` (or `npm run check`) in `web/frontend/` compiles clean — no references to deleted `DetailPanel`, no orphan imports.
- `npm run test` (vitest) — existing store tests still pass (no store logic touched).
- Visual: load the app, confirm Sidebar collapses 240↔64px smoothly, active nav shows glowing dot on each of the 12 routes, Header shows logo + version/game pills, content canvas is 1280px centered with 32px padding, Hack Nerd Font renders on mono text.
