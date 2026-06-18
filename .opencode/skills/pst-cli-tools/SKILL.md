---
name: pst-cli-tools
description: The CLI toolsets (palworld_toolsets - character_transfer, fix_host_save, slot_injector, game_pass_save_fix, modify_save, restore_map, convert_generic, convertids, xgp_save_extract), the GamePass import pipeline (palworld_xgp_import), and coordinate transforms (palworld_coord). Load when working on any CLI tool, XGP saves, or coordinate math.
---

# PST CLI Tools, GamePass, Coordinates

## palworld_coord/ — coordinate transforms (single file __init__.py, 72 lines)
Pure-math, no deps. Point = namedtuple(x,y).

**Constants:**
- OLD map: transl_x=123888, transl_y=158000, scale=459 (cm/map-unit)
- NEW map (post-Sakurajima): transl_x=375247, transl_y=-18, scale=725
- TREEMAP: transl 358540/-382365, scale 724, pixel_offset 1760/2571, cursor_offset -1075/1568, coord_range 2500
- MAP_Z_THRESHOLD=5000

**Functions:**
- `sav_to_map(x,y,new=False)` (18): save(cm float) to world(int). Swaps axes: out.x=(y-transl_y)/scale, out.y=(x+transl_x)/scale. new=True uses Sakurajima params.
- `map_to_sav(x,y,new=False)` (62): inverse.
- `sav_to_treemap(x,y)` (30) / `treemap_to_sav(x,y)` (41): treemap variants.
- `sav_to_map_by_z(x,y,z=0)` (34): auto-select — tries new-map (+/-1000 threshold), then treemap (+/-2500), else fallback. z is a no-op param.
- `treemap_to_pixel(x_world,y_world,w,h)` (45): world to image pixels. range +/-2500, Y flipped.
- `treemap_pixel_to_cursor(img_x,img_y,w,h)` (53): pixel to world for cursor. Uses cursor offsets NOT pixel offsets (not strict inverse).

**Coordinate system:** save=UE world-space cm floats (hundreds of thousands); world=integer grid units. Axes swap (out.x from input Y). MAP_Z_THRESHOLD exported but unused internally.

## palworld_xgp_import/ — Xbox GamePass save pipeline
Steam saves: flat folder with Level.sav/LevelMeta.sav/Players/. XGP saves: UWP sandboxed container store (wgs/<USERID_HEX>_<TITLEID_HEX>/), each blob in GUID dir + container.<n> manifest, indexed by containers.index (version 14). .sav byte content identical — only wrapper differs.

**container_types.py (162):** binary codec. Container(46), ContainerIndex(85, version must be 14), ContainerFileList(127, version must be 4). UTF-16LE, length-prefixed strings, FILETIME(33). Naming: "<saveid>-Level"/"-LevelMeta"/"-Players-<uid>".
**gamepass_manager.py (322):** library API used by GUI. find_container_paths(17), extract_save_to_temp(123 — reconstructs Steam layout), convert_to_steam(221), save_to_container(171 — Steam to XGP), convert_to_gamepass_from_steam(246). _try_read_world_name(48) decompresses LevelMeta to read WorldName.
**main.py (46):** standalone CLI Steam to XGP. Removes EggTest* ghost containers.
**utils.py (27):** DUPLICATE of container_types helpers, UNUSED — cruft.

## palworld_toolsets/ — 9 CLI tools (all GUI-launched via tools_tab._import_and_call)
All use `from import_libs import *` (shared bootstrap injecting globals). Save type heuristic: 50 if 'Pal.PalworldSaveGame' OR 'Pal.PalLocalWorldSaveGame' in class name, else 49.

### character_transfer.py (1284) — cross-save player migration
Transfer player (character, tech, inventory, pals, guild, timestamps) source to target Level.sav. Handles pre/post-v1 (Sakurajima) format normalization (_normalize_save_parameter 137: adds ExpTableMigrationVersion/bApplyShieldDamage pre to post, SanityValue post to pre). migrate_pal_via_api(519) bumps InstanceId via hex-translate. GUI: CharacterTransferWindow. Entry: character_transfer()(1279).

### fix_host_save.py (628) — GUID swap / host fix
Swap two players' GUIDs across Level + both player files. Both must be level>=2. deep_swap(185) recursively swaps OwnerPlayerUId/owner_player_uid/build_player_uid/private_lock_player_uid. copy_dps_file(219) rewrites SlotId.ContainerId in copied dps pals. Entry: fix_host_save()(604). Core: fix_save(129).

### slot_injector.py (709) — palbox/party slot capacity editor
Edit CharacterContainerSaveData SlotNum. Identifies injected containers by SlotNum>=960. _cleanup_excess_slots(543): comprehensive orphan cleanup (excess slots, dangling pals, stale guild handles). Entry: slot_injector()(704).

### game_pass_save_fix.py (577) — XGP/Steam converter GUI
Windows-only. XGP to Steam: extract, sav, json, sav, move. Steam to XGP: stop GamingServices, xgp_import.main, restart. convert_sav_JSON(309)/convert_JSON_sav(334) drive palsav convert via sys.argv rewrite. Entry: game_pass_save_fix()(560).

### modify_save.py (559) — external editor launcher
Downloads/runs Palworld Save Pal + Palworld Pal Editor from GitHub. No save manipulation. SSL fallback chain: bundled, user, downloaded, unverified. Entry: modify_save()(549).

### restore_map.py (164) — map fog clearer
Zero WorldMapUISaveDataMap MaskTextureData + set Local_HiddenLocationFlagMap=False in all LocalData.sav under SaveGames. Entry: restore_map()(74).

### convert_generic.py (60) — SAV/JSON single file
Delegates to palsav.commands.convert. Entry: convert_generic(ext)(32).

### convertids.py (112) — SteamID to Palworld UID
steamIdToPlayerUid + PlayerUid2NoSteam. Auto-detects local SaveGames Steam ID. No save IO. Entry: convert_steam_id()(12).

### xgp_save_extract.py (276) — raw XGP container extractor to zip
Parses containers.index, maps containers to arcnames (name.replace('-','/')+'.sav'), outputs zip. No decompression. Entry: main(wgs_path)(183).

## Cross-cutting
- GUI wiring (tools_tab.py:443): CONVERTING group (convert, gamepass, steamid, restore_map) + MANAGEMENT group (slot_injector, modify_save, character_transfer, fix_host_save).
- Backups via backup_whole_directory(path, sublabel).
- Ownership: ContainerOwnership.build for pal-to-player resolution.
- UUID normalization: str(uid).lower().replace('-','').