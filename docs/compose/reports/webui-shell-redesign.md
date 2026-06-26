---
feature: webui-shell-redesign
status: delivered
specs:
  - docs/compose/specs/2026-06-26-webui-shell-redesign-design.md
plans:
  - docs/compose/plans/2026-06-26-webui-shell-redesign.md
branch: Testing
commits: uncommitted (deferred to user request per repo git-safety)
---

# WebUI Shell + Theme Redesign — Final Report

## What Was Built

The PST WebUI frontend shell (SvelteKit 2 / Svelte 5 / Tailwind v4) was redesigned to high-fidelity match the scraped Reflex reference (`web/.web_ref`, sourced from `reflex_branch/`). The shell is a desktop-locked **two-pane** layout: a 56px **Header** on top, a collapsible **Sidebar** (240px ↔ 64px) on the left, and a centered **main Content canvas** (`max-w-1280px`, `32px` padding) that scrolls independently.

The redesign fixes the four concrete fidelity breaks that made the prior shell "miss the mark": the body font (`'Inter'`) was referenced but never imported (silent fallback), the Header carried a 110-line dead cascade menu with no logo, the layout used fragile `h-[calc(100vh-56px)]` pixel math, and a `DetailPanel` component was built but never mounted. Backend logic, stores, API clients, and route pages are untouched — only the presentation shell and theme fonts changed.

## Architecture

```
+layout.svelte            h-screen flex-col shell (Header over flex-1 row)
├── Header.svelte         h-14 top bar: logo + title + version/game pills + actions + Discord
├── Sidebar.svelte        240/64px nav: 3 groups / 12 routes, glowing active dot, fade transitions
└── <main>                flex-1 overflow-y-auto, inner max-w-1280px px-8 py-8 canvas → children
```

- **`src/routes/+layout.svelte`** — root `h-screen w-screen overflow-hidden flex flex-col`; the row below the header is `flex flex-1 min-h-0`. The `min-h-0` is the key fix — it lets `<main>`'s `overflow-y-auto` work without any pixel `calc()`.
- **`src/lib/components/shell/Header.svelte`** — clean top bar reading `$displayVersion` / `$gameVersion` from `$lib/stores/shell`. Logo served from `/images/PalworldSaveTools.png` (44px). The entire cascade (`menuOpen`/`activeSubmenu`/`menuCategories`/`handleMenuAction`) was removed.
- **`src/lib/components/shell/Sidebar.svelte`** — nav data inline (matches reference `NAV_GROUPS`): Tools (All Tools/Players/Guilds/Bases/Map), Editors (Player Inventory/Base Inventory/Pal Editor), Utilities (Exclusions/Containers/Backups/Settings). Icons referenced directly (no `iconMap` indirection). Collapse via `leftNavCollapsed` / `toggleLeftNav`; labels use `svelte/transition` `fade`; active item gets `font-semibold` + a `bg-accent-primary` glowing dot.
- **`src/app.css`** — Tailwind v4 `@theme` color tokens were already correct (they mirror `reflex_branch/styles/colors.py`); only fonts changed: added `--font-sans` (system-ui stack) and `--font-mono` (Hack Nerd Font), an `@font-face` loading `/fonts/HackNerdFont-Regular.ttf`, and switched `html, body` from `'Inter'` to `var(--font-sans)`.
- **`src/lib/components/shell/DetailPanel.svelte`** — **deleted** (orphaned; never imported anywhere).

### Design Decisions

- **Two-pane over the reference's three-pane.** The reference has a right DetailPanel (380/72px); the user scoped the redesign to three pillars — Header + Sidebar + Content — so the DetailPanel was dropped rather than wired in. The three-pane design remains recoverable (the reference specs are preserved).
- **Flex `min-h-0` over magic `calc()`.** Replacing `h-[calc(100vh-56px)]` (and route pages' `calc(100vh - 56px - 64px - 28px - 32px)`) with a flexbox + `min-h-0` chain makes the shell resilient to header/padding changes. Route pages still carry their old inline `calc()` heights (out of scope) but now sit inside a correct flex container.
- **`displayVersion` for the header pill.** The store exposes `appVersion`, `displayVersion`, and `gameVersion`; the pill uses `displayVersion` to preserve the prior wiring rather than introduce a second version surface.
- **Kept codebase conventions.** Sidebar link colors stay in a scoped `<style>` and self-closing `<div/>` syntax is retained — both match the existing component library, so the new shell doesn't introduce a divergent style.
- **Language picker dropped with the cascade.** It lived inside the removed menu; `currentLanguage` / `availableLanguages` store fields remain intact for a future standalone control.

## Usage

Run the frontend (the Python backend in `web/backend/` is unchanged):

```bash
cd web/frontend
npm run dev      # dev server
npm run build    # production build → build/
npm run check    # svelte-check (types + a11y)
npm run test     # vitest store tests
```

The shell consumes only these `shell.ts` exports: `leftNavCollapsed`, `toggleLeftNav`, `displayVersion`, `gameVersion`. Route pages render unchanged inside the new `<main>` canvas.

## Verification

- **`npm run check`** — 0 errors in the changed files (`+layout`, `Header`, `Sidebar`, `app.css`). svelte-check reports 4 errors / 43 warnings total, all **pre-existing** in untouched files: `StatsEditor.svelte` (`$inventoryStore` binding) and `MapView.svelte` (leaflet `onMount` type + missing `@types/leaflet`); the warnings are the codebase-wide self-closing-`<div/>` / a11y style. None were introduced by this change.
- **`npm run build`** — `✓ built in 3.44s`, site written to `build/` (succeeds; the pre-existing svelte-check errors do not block `vite build`).
- **`npm run test`** — 28/28 passed (save: 8, containers: 8, **shell: 12** — confirms store consumption is intact).
- **Manual visual** — *pending user run*: `npm run dev` and confirm sidebar collapse + fade, glowing active dot on each of the 12 routes, header logo + pills (no cascade), 1280px-centered canvas, and Hack Nerd Font rendering on monospace text (e.g. pal IDs / coordinates on the Pal Editor page).

## Journey Log

> Brief notes on what informed the final design. Not required reading.

- [pivot] Exploration revealed the existing `Sidebar.svelte` already implemented ~90% of the reference (correct groups/routes/collapse/active dot) — shifted from a dogmatic "ground-up rewrite" to targeted fidelity fixes and avoided churning working code.
- [lesson] The `@theme` color tokens already mirrored the reference's `colors.py` exactly; the real visual breaks were the unimported `Inter` font, the dead Header cascade with no logo, magic `calc()` heights, and an orphaned DetailPanel that was never mounted.
- [decision] Dropped the in-menu Language picker together with the cascade (it lived inside it); store fields retained for a future standalone control.
- [lesson] svelte-check's 4 errors all pre-existed in untouched files and do not block `vite build` — always confirm build/test output rather than halting on a noisy type-check.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/specs/2026-06-26-webui-shell-redesign-design.md` | Design spec | Approved Approach A; sections S1–S11 |
| `docs/compose/plans/2026-06-26-webui-shell-redesign.md` | Implementation plan | 7 tasks, all complete |
