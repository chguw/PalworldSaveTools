---
name: pst-opencode-config
description: OpenCode configuration knowledge for this repo — skills setup, plugin wiring, JSONC config format, snapshot system behavior (doesn't track .opencode/), and the diff-logger plugin pattern. Load when editing .opencode/ config, plugins, or troubleshooting opencode behavior.
---

# PST OpenCode Config Knowledge

## Config file
- Format: `.opencode/opencode.jsonc` — JSONC (JSON with Comments) is supported natively.
- Configs merge across locations: remote → global → custom → project → `.opencode/` dirs.
- The `"lsp": true` enables auto-diagnostics for agent code.
- The `"instructions"` array loads files into every session context.

## Skills (pst-*)
Skills live in `.opencode/skills/<name>/SKILL.md`. Each must have YAML frontmatter with:
- `name` (required) — lowercase alphanumeric with single hyphens, matches regex `^[a-z0-9]+(-[a-z0-9]+)*$`, must match the directory name.
- `description` (required) — 1-1024 chars, specific enough for agent to choose correctly.
- Optional: `license`, `compatibility`, `metadata`.

Permission to load without asking is set via `"permission": { "skill": { "pst-*": "allow" } }` in `opencode.jsonc`. Wildcard patterns supported.

## Plugins
- **Local plugins** in `.opencode/plugins/*.ts` are auto-discovered at startup — no config entry needed.
- The `"plugin"` config key is for **npm packages only** (e.g., `"opencode-helicone-session"`).
- Local plugins with npm deps: add a `package.json` in `.opencode/` with the dependencies; `bun install` runs at startup.
- Plugin modules export a `Plugin` function (named `export const MyPlugin: Plugin = ...` or `export default`).

### diff-logger plugin pattern
The `diff-logger.ts` plugin writes `.opencode/changes.md` with rolling session entries. Key design:
- **Primary trigger:** `tool.execute.after` hook for `write`/`edit` tools — fires after every file-modifying tool call. Runs `git diff --stat HEAD` + `git ls-files --others` to capture ALL changes (tracked + untracked).
- **Secondary trigger:** `event` hook for `session.diff` events — uses opencode's built-in snapshot diff data (but only fires for tracked files outside `.opencode/`).
- Session dedup via HTML comment markers: `<!-- ${sessionID} -->`.
- Handles new files via `git ls-files --others --exclude-standard` + `wc -l`.

## Snapshot system behavior
- OpenCode's internal snapshot system (`~/.local/share/opencode/snapshot/{project-id}/`) tracks changes between step boundaries.
- **It intentionally excludes `.opencode/`** from tracking to prevent infinite recursion (editing config → snapshot → diff event → state change → snapshot → ...).
- The "Modified Files" TUI panel does NOT show changes to `.opencode/` files.
- `session.diff` events only fire for changes outside `.opencode/`.
- Known issues: #11856 (session.diff not clearing after git commit), #14013 (non-clickable modified files list).

## Plugin event system
Two ways to hook into events:
1. **Direct hooks** (on the Hooks object): `"tool.execute.after"`, `"tool.execute.before"`, `"shell.env"`, `"chat.params"`, etc. — these are callback properties on the Hooks object.
2. **Bus events** (via `event` hook): `session.diff`, `file.edited`, `session.created`, `permission.asked`, `todo.updated`, `command.executed`, etc. — received via `event: async ({ event }) => { ... }`.

## Known limitations
- `file.edited` events only carry the file path, not diff stats — you need `git diff` to compute +/- counts.
- `client.session.get()` API expects `{ path: { sessionID } }`, not `{ sessionID }`.
- The `event` hook receives ALL opencode bus events — filter by `event.type`.
- Bun APIs (`Bun.file`, `Bun.write`, `Bun.spawnSync`) are available in plugins since opencode runs on Bun.
