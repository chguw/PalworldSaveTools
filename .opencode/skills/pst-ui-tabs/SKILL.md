---
name: pst-ui-tabs
description: Every UI tab, dialog, and reusable widget in palworld_aio/ui/ and widgets/, plus the map rendering pipeline (MapGraphicsView/markers/items/effects). Load when editing UI, tabs, dialogs, the map, or Qt styling.
---

# PST UI Tabs, Dialogs, Widgets

"wsd" = `constants.loaded_level_json['properties']['worldSaveData']['value']`. Shared by all tabs.

## The 9 tabs (QStackedWidget pages, MainWindow index order)

### 0. Tools — `ui/tools_tab.py:244` (ToolsTab)
Landing/dashboard. Save-load card (button+drag-drop) + 4 StatIconBtn counters (navigate on click) + tool grids (Converting: json↔sav, game_pass_save_fix, convertids, restore_map; Management: slot_injector, modify_save, character_transfer, fix_host_save). `_update_stats:362` reads wsd. `_run_*_tool:434/459` import+call palworld_toolsets via `_import_and_call:420`. ConversionOptionsDialog(66).

### 1. Base Inventory — `ui/base_inventory_tab.py:1661` (BaseInventoryTab)
Edit guild/base shared storage + view base-worker pals. Holds `self.manager = BaseInventoryManager()`. guild_button→base_button→content_stack[Inventory page (ContainerListWidget:717 + ContainerInfoWidget:939 + InventoryGridWidget) | BasePalsContentWidget:1261]. Auto-save 2s debounce (`_trigger_auto_save:2452`→`_auto_save_changes:2455`). Dialogs: GuildItemPickerDialog(51), GuildStructurePickerDialog(346), EconomyStatsDialog(604), ContainerSlotModificationDialog(648). 2606 lines — heaviest tab.

### 2. Player Inventory — `ui/inventory_tab.py:789` (PlayerInventoryTab)
Full per-player inventory/equipment/stats editor. `self.inventory = get_player_inventory(uid)`. inv_tabs QTabWidget = main_grid + key_grid + stats(StatsPanelWidget). Right equip_wrapper: EquipmentSlotWidget(105) grids (weapon×6, accessory×4, food×5, head/body/shield/glider/sphere_mod). Writes wsd ItemContainerSaveData via _update_raw_save_data(1715); stats via CharacterSaveParameterMap. `_save_changes:1912` (memory only). Dialogs: ItemPickerDialog(628), InventoryLoadoutDialog(2068), QuantityDialog(1961). Emits `saved`, `unlock_all_map_requested`. 2203 lines.

### 3. Pal Editor — `ui/pal_editor_tab.py:8` (PalEditorTab)
Thin host for `edit_pals.PalEditorWidget`. `_show_editor:109` → PalEditorWidget.set_player(uid,name). Delegates everything. See pst-pal-editor skill for the editor engine.

### 4. Players — inline MainWindow (`_setup_players_tab:315`)
SearchPanel(search_players, 8 cols) + bulk-action toolbar (Bulk Item/Pal/Technology → dialogs). Right-click → `_show_player_context_menu:1045` (ScrollableContextMenu: delete/rename/exclude/unlock cage/reset timestamp/container IDs/tech/level/guild ops). `_refresh_players:709` → save_manager.get_players(), `[L]` leader prefix, pal counts, guild info.

### 5. Guilds — inline (`_setup_guilds_tab:345`)
QSplitter(Vertical) = guilds SearchPanel(3 cols) + members SearchPanel(5 cols). `_on_guild_selected:1016` fills members via get_guild_members. Right-click → `_show_guild_context_menu:1070` / `_show_guild_member_context_menu:1086`.

### 6. Bases — inline (`_setup_bases_tab:360`)
Single bases SearchPanel(4 cols). `_refresh_bases:725` → get_bases(). Right-click → `_show_base_context_menu:1105` (delete/export/import/clone/adjust radius/rename guild/set level).

### 7. Map — `ui/map_tab.py:23` (MapTab)
Interactive world/tree map. QHBoxLayout = _map_widget (MapGraphicsView + overlay buttons) stretch3 + _sidebar_widget (search + QStackedWidget[base_tree|player_tree] + info_label) stretch2. `refresh:796` → _get_guild_bases:809 (GroupSaveDataMap + BaseCampSaveData via palworld_coord.sav_to_map) + _get_players:876 (reads Players/*.sav LastTransform). _to_image_coordinates:920 maps world[-1000,1000]²→pixels. Toggles: bases/players/rings/zones/map-type/calibrate. Zone drawing (rect+polygon) via `_set_zone_drawing_mode:1776`. 1916 lines. See map rendering pipeline below.

### 8. Exclusions — inline (`_setup_exclusions_tab:390`)
3 SearchPanels (players/guilds/bases exclusions). `_refresh_exclusions:734` reads constants.exclusions. Mutations _add_exclusion:1555/_remove_exclusion:1561, persisted via _save_exclusions:1491.

## Map rendering pipeline (map_view/markers/items/effects)

**MapGraphicsView** (`ui/map_view.py:8`, QGraphicsView): QGraphicsScene holds single QGraphicsPixmapItem map image (z=-1, _load_map loads T_WorldMap.webp/T_TreeMap.webp) + marker/zone/ring/effect items. Coord transform (mouseMoveEvent:208): `x_world = img_x/width*2000-1000`, `y_world = 1000 - img_y/height*2000`, then palworld_coord.map_to_sav/sav_to_map. Zoom (wheelEvent:100, factor 1.15, clamp 1.0-30.0), smooth zoom-to via animate_to_marker:268. Signals: marker_clicked/double_clicked/right_clicked, empty_space_right_clicked, zone_*, zoom_changed, calibration_clicked.

**Markers** (`ui/map_markers.py`): BaseMarker:5 / PlayerMarker:122 (QGraphicsPixmapItem, ItemIgnoresTransformations). scale_to_zoom(zoom) dynamic sizing. Custom paint: animated "shine" sweep + QRadialGradient glow when selected/hovered. update_glow() pulse driven by MapTab._update_animations.

**Map items** (`ui/map_items.py`): BaseRadiusRing:4 (QGraphicsEllipseItem, save radius → scene pixels). ExclusionZoneItem:43 / PolygonExclusionZoneItem:125 (world↔scene via zone_manager.world_to_scene, red translucent). ZonePreviewItem:96 / PolygonPreviewItem:181 (live drag previews).

**Effects** (`ui/map_effects.py`): EffectItem:6 (QGraphicsObject, animated progress). DeleteEffect:23, ImportEffect:39, ExportEffect:88, CalibrationEffect:59. Played by MapTab._play_effect:1091 (QPropertyAnimation 0→1).

## Header / Sidebar / Results

**HeaderWidget** (`ui/header_widget.py:15`): custom title bar. logo, menu_chip_btn (opens MenuPopup), version chip (pulses on update), game-version chip, info/warn/toolbox buttons, discord/min/max/close. Signals: minimize/maximize/close/about/toolbox_clicked.

**SidebarWidget** (`ui/sidebar_widget.py:133`, fixed 48px): 9 NavItem:47 buttons (NerdFont glyphs) → nav_changed(str). Bottom: console_toggled, right_panel_toggled. set_active() toggles indicator pill.

**ResultsWidget** (`ui/results_widget.py:7`, fixed 350px): right dashboard. "Selection & Stats" cards (set_player/guild/base) + StatsPanel (before/after/result counts). refresh_stats_before/after:123/128 from save_manager.get_current_stats().

## Dialogs

| Dialog | file:line | Purpose |
|---|---|---|
| PlayerItemActionDialog | player_item_dialog.py:37 | Bulk add/remove item across players; find-players-with-item. Signals: item_action_selected, add_all_key_items_requested, add_all_effigies_requested, unlock_all_map_requested. |
| PlayerPalActionDialog | player_pal_dialog.py:21 | Delete pal species everywhere; remove skills from all pals. pal_action_selected. |
| PlayerTechnologyActionDialog | player_technology_dialog.py:14 | Add/remove tech per players. Edits Players/*.sav UnlockedRecipeTechnologyNames. |
| ContainerSelectorDialog | container_selector_dialog.py:17 | Reassign container IDs (fix broken inventories). get_selected_container_ids():666. |
| SkillPicker | skill_picker.py:120 | Searchable active/passive skill chooser. pick(). _PassiveSkillDelegate:13 animates rank≥4/5. |
| TabGuideDialog | tab_guide_dialog.py:67 | In-app help from tab_guide/<lang>/*.html (10 sections). |
| ConversionOptionsDialog | tools_tab.py:66 | json↔sav direction picker. |
| ItemPickerDialog | inventory_tab.py:628 | Icon-grid item selector + qty. |
| ContainerSlotModificationDialog | base_inventory_tab.py:648 | Resize container slot count. |
| GuildItemPickerDialog/StructurePicker | base_inventory_tab.py:51/346 | Pick item/structure for bulk guild ops. |
| InventoryLoadoutDialog | inventory_tab.py:2068 | Save/load inventory presets. |

## Reusable widgets (widgets/)

| Widget | file:line | Purpose |
|---|---|---|
| SearchPanel | search_panel.py:6 | title + search QLineEdit + sortable QTreeWidget. item_selected, add_item, get_selected_data, refresh_labels. Used by players/guilds/bases/exclusions. |
| StatsPanel | stats_panel.py:8 | before/after/result count grid + copy button. update_stats, refresh_stats_before/after. |
| MenuPopup | menu_popup.py:111 | main app menu (File/Functions/Maps/Exclusions/Updates/Languages). cursor-tracking submenu. ScrollableMenu:8. |
| ScrollableContextMenu | scrollable_context_menu.py:6 | scrollable context menu (long action lists). add_action, exec. |
| BaseHoverOverlay/PlayerHoverOverlay | base_hover_overlay.py:6 / player_hover_overlay.py:6 | map marker tooltips. show_for_base/player. |
| CollapsibleSplitter | collapsible_splitter.py:41 | splitter with toggle handle. collapsed_changed, collapse/expand. |
| LoadingPopup | loading_popup.py:3 | fade-in/out loading overlay. show_with_fade/hide_with_fade. |
| SortableTreeWidget | tree_widgets.py:5 | sortable tree + context_menu_requested signal. |

## Styling
`ui/styles.py`: ThemeManager(:4, apply_global/apply_to_widget) + CSS constants (DIALOG_STYLE, MENU_STYLE, STATS_PANEL_STYLE, SLOT_*_STYLE) + helpers (slot_full, slot_rarity, wrap_tooltip_text).
`ui/styled_combo.py:4` (StyledCombo): custom QComboBox replacement.
`ui/menus.py`: MenuFactory, ContextMenuBuilder, create_*_context_menu fns (MainWindow builds menus inline; these are alternatives).
`resources/ui/themes/darkmode.qss`: Qt dark theme stylesheet.

## Cross-cutting
- **i18n**: every label uses `t('key', default=...)`; all tabs/dialogs implement refresh_labels() called from MainWindow._change_language:1494.
- **Game data**: ItemData (items db), characters.json (pals icons/desc/passives), world.json technology, pal_exp_table.json. Icons under resources/game_data/icons/, map images T_WorldMap.webp/T_TreeMap.webp, game icons baseicon.webp/playericon.webp.
- **Persistence**: edits mutate in-memory + player .sav; disk flush via File→Save Changes → save_manager.save_changes(). Base-inventory auto-saves containers every 2s.