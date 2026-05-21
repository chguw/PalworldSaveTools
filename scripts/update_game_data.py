#!/usr/bin/env python3
"""
Game Data Resource Updater for Palworld Save Tools (PST)

This script reads the latest exported game data tables from Exports/Pal/Content/Pal/DataTable/
and generates/updates the curated JSON files in resources/game_data/ that the PST application
uses at runtime.

Usage:
    python scripts/update_game_data.py

This will update all resource files based on the latest exports from the Palworld game files.
It handles:
  - pals (paldata.json + icons)
  - items (itemdata.json + icons)
  - structures (structuredata.json + icons)
  - passive skills (passivedata.json + icons)
  - technologies (technologydata.json + icons)
  - NPCs (npcdata.json + icons)
  - skills (skilldata.json)
  - pal_exp_table.json
  - Pal passive data
"""

import os
import sys
import json
import re
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / 'resources' / 'game_data'
ICONS_DIR = RESOURCES_DIR / 'icons'
EXPORTS_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Pal' / 'DataTable'
EXPORT_TEXTURES_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Pal' / 'Texture'
EXPORT_L10N_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'L10N' / 'en' / 'Pal' / 'DataTable' / 'Text'


def ensure_dir(directory: Path):
    """Create directory if it doesn't exist."""
    directory.mkdir(parents=True, exist_ok=True)


def load_export_json(rel_path: str) -> dict | list | None:
    """
    Load an exported JSON file from the Exports directory.
    Uses a relative path like 'Character/DT_PalCharacterIconDataTable.json'
    """
    path = EXPORTS_DIR / rel_path
    if not path.exists():
        print(f"  WARNING: Export file not found: {rel_path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ERROR loading {rel_path}: {e}")
        return None


def load_l10n_table(filename: str) -> dict[str, str]:
    """
    Load a localization table from the English L10N directory and return
    a dict mapping keys to their localized SourceString.
    
    e.g. load_l10n_table('DT_PalNameText_Common.json')
    -> {'PAL_NAME_Anubis': 'Anubis', 'PAL_NAME_DomeArmorDragon': 'Aegidron', ...}
    """
    path = EXPORT_L10N_DIR / filename
    if not path.exists():
        print(f"  WARNING: L10N file not found: {filename}")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR loading L10N {filename}: {e}")
        return {}
    
    result = {}
    all_rows = {}
    if isinstance(data, list):
        for table in data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(data, dict):
        rows = data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    
    for key, row in all_rows.items():
        if isinstance(row, dict):
            text_data = row.get('TextData', row)
            source = text_data.get('SourceString', '')
            if source:
                result[key] = source
    return result


def load_resource_json(filename: str) -> dict:
    """Load an existing resource JSON file, returning {} if not found."""
    path = RESOURCES_DIR / filename
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_resource_json(filename: str, data: dict | list):
    """Save data to a resource JSON file with pretty formatting."""
    path = RESOURCES_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"  Saved: {filename} ({len(data.get(list(data.keys())[0]) if isinstance(data, dict) and data else data) if isinstance(data, list) else len(data)} entries)")


def get_rows(data: list | dict) -> dict:
    """
    Extract the 'Rows' dictionary from an exported data table JSON.
    Export files are lists of table objects, each with a 'Rows' key.
    Some tables have rows directly on the first element, others use composite tables
    where we need to check the parent and common tables.
    """
    if isinstance(data, dict):
        return data.get('Rows', {})
    
    # It's a list - find the table that has Rows
    rows = {}
    for table in data:
        if isinstance(table, dict):
            r = table.get('Rows', {})
            if r:
                rows.update(r)
            # Handle composite tables with parent tables
            props = table.get('Properties', {})
            parent_tables = props.get('ParentTables', [])
            for parent in parent_tables:
                if isinstance(parent, dict):
                    obj_name = parent.get('ObjectName', '')
                    obj_path = parent.get('ObjectPath', '')
                    # Try to load parent table
                    if obj_name:
                        # Extract filename from ObjectName e.g. "DataTable'DT_PalCharacterIconDataTable_Common'"
                        m = re.search(r"'([^']+)'", obj_name)
                        if m:
                            parent_name = m.group(1)
                            # Look for the parent table in the same directory
                            # We'll handle this by reading the _Common files explicitly
                            pass
    return rows


def extract_icon_path(asset_path: str) -> str:
    """
    Extract a usable icon path from the UE asset path.
    
    e.g. '/Game/Pal/Texture/PalIcon/Normal/T_Anubis_icon_normal.T_Anubis_icon_normal'
    -> 'pals/T_Anubis_icon_normal.webp'
    
    e.g. '/Game/Pal/Texture/UI/Item/T_itemicon_PalSphere.T_itemicon_PalSphere'
    -> 'items/T_itemicon_PalSphere.webp'
    """
    if not asset_path:
        return None
    
    # Remove the sub-path (everything after the last '.')
    if '.' in asset_path:
        asset_path = asset_path[:asset_path.rindex('.')]
    
    # Extract filename
    filename = os.path.basename(asset_path)
    
    return filename


def find_icon_file(export_texture_path: str, icon_subdir: str) -> str | None:
    """
    Look for an icon in the exported textures and return the relative resource path.
    
    Tries multiple extensions (webp, png) and naming conventions.
    """
    if not export_texture_path:
        return None
    
    # Remove the sub-path from the asset path
    clean_path = export_texture_path
    if '.' in clean_path:
        clean_path = clean_path[:clean_path.rindex('.')]
    
    # Get the filename without extension
    filename = os.path.basename(clean_path)
    
    # Search for the file in the exported textures
    extensions_to_try = ['.webp', '.png', '.PNG', '.jpg', '.tga']
    search_patterns = [
        filename,
        filename.replace('_icon_normal', '_icon'),
        filename.replace('_icon_normal', ''),
    ]
    
    # Search recursively in the texture dir
    for ext in extensions_to_try:
        for pattern in search_patterns:
            # Search in appropriate subdirs
            search_dirs = []
            if icon_subdir == 'pals':
                search_dirs = [EXPORT_TEXTURES_DIR / 'PalIcon' / 'Normal',
                               EXPORT_TEXTURES_DIR / 'PalIcon' / 'NPC']
            elif icon_subdir == 'items':
                search_dirs = [EXPORT_TEXTURES_DIR / 'Item',
                               EXPORT_TEXTURES_DIR / 'UI' / 'InGame',
                               EXPORT_TEXTURES_DIR / 'UI' / 'Common']
            elif icon_subdir == 'structures':
                search_dirs = [EXPORT_TEXTURES_DIR / 'BuildObject' / 'Icon',
                               EXPORT_TEXTURES_DIR / 'BuildObject' / 'PNG']
            elif icon_subdir == 'technologies':
                search_dirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common']
            elif icon_subdir == 'passives':
                search_dirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common',
                               EXPORT_TEXTURES_DIR / 'StatusParameterIcon']
            elif icon_subdir == 'elements':
                search_dirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common',
                               EXPORT_TEXTURES_DIR / 'UI' / 'InGame']
            
            for search_dir in search_dirs:
                if search_dir.exists():
                    for found_file in search_dir.rglob(f'{pattern}{ext}'):
                        # Found it, return relative resource path
                        return f'/icons/{icon_subdir}/{found_file.name}'
    
    return None


def copy_icon_to_resources(export_path: Path, target_subdir: str) -> str | None:
    """
    Copy an icon from the exports to the resources/game_data/icons/ directory.
    Returns the relative path for the JSON data.
    """
    if not export_path.exists():
        return None
    
    target_dir = ICONS_DIR / target_subdir
    ensure_dir(target_dir)
    
    target_file = target_dir / export_path.name
    
    # Only copy if source is newer
    if not target_file.exists() or export_path.stat().st_mtime > target_file.stat().st_mtime:
        try:
            shutil.copy2(str(export_path), str(target_file))
        except Exception as e:
            print(f"    ERROR copying {export_path.name}: {e}")
            return None
    
    return f'/icons/{target_subdir}/{export_path.name}'


def find_and_copy_icon(search_name: str, target_subdir: str, export_subdirs: list[Path]) -> str | None:
    """
    Find an icon file in export texture subdirectories and copy it to resources.
    
    Args:
        search_name: The filename to search for (without extension)
        target_subdir: The target subdirectory under icons/ (e.g. 'pals', 'items')
        export_subdirs: List of Path objects to search in
        
    Returns:
        The relative path string (e.g. '/icons/pals/T_Anubis_icon_normal.webp') or None
    """
    extensions = ['.webp', '.png', '.PNG', '.jpg', '.tga']
    
    for export_dir in export_subdirs:
        if not export_dir.exists():
            continue
        
        for ext in extensions:
            for file_path in export_dir.rglob(f'{search_name}{ext}'):
                return copy_icon_to_resources(file_path, target_subdir)
    
    return None


# ============================================================================
# PAL DATA UPDATE
# ============================================================================

def update_pal_data():
    """Update paldata.json based on exported data tables.
    
    Primary source: DT_PalCharacterIconDataTable (has icon info)
    Secondary source: DT_PalMonsterParameter (has all variants including BOSS_/POLICE_)
    
    In-game names are resolved from English localization data (DT_PalNameText_Common.json)
    using the OverrideNameTextID field from MonsterParameter rows.
    """
    print("\n=== Updating Pal Data ===")
    
    export_data = load_export_json('Character/DT_PalCharacterIconDataTable.json')
    export_data_common = load_export_json('Character/DT_PalCharacterIconDataTable_Common.json')
    monster_param = load_export_json('Character/DT_PalMonsterParameter.json')
    monster_param_common = load_export_json('Character/DT_PalMonsterParameter_Common.json')
    
    existing = load_resource_json('paldata.json')
    existing_pals = {p.get('asset', '').lower(): p for p in existing.get('pals', [])}
    
    # Load localization data for pal names
    # This maps: PAL_NAME_Anubis -> "Anubis", PAL_NAME_DomeArmorDragon -> "Aegidron", etc.
    pal_name_l10n = load_l10n_table('DT_PalNameText_Common.json')
    
    # Also load name prefix localization (for BOSS/ALPHA prefixes)
    name_prefix_l10n = load_l10n_table('DT_NamePrefixText_Common.json')
    
    # Collect all rows from icon tables
    icon_rows = {}
    for data in [export_data, export_data_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            icon_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    icon_rows.update(rows)
    
    # Collect all rows from monster parameter (catches BOSS_/POLICE_ variants)
    monster_rows = {}
    for data in [monster_param, monster_param_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            monster_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    monster_rows.update(rows)
    
    if not icon_rows and not monster_rows:
        print("  No pal rows found in exports. Skipping.")
        return
    
    # Build case-insensitive L10N lookup: lowercase key -> value
    # This handles mismatches like PAL_NAME_Kirin_ice vs PAL_NAME_Kirin_Ice
    _pal_name_l10n_lower = {}
    for k, v in pal_name_l10n.items():
        _pal_name_l10n_lower[k.lower()] = v

    def _lookup_l10n(key: str) -> str | None:
        """Case-insensitive L10N lookup."""
        val = pal_name_l10n.get(key)
        if val:
            return val
        val = _pal_name_l10n_lower.get(key.lower())
        return val

    def _is_valid_name(name: str) -> bool:
        if not name:
            return False
        return name.lower() not in ('en_text', 'none', 'unidentified pal')

    def _get_pal_name(name_key: str) -> str | None:
        n = _lookup_l10n(name_key)
        return n if n and _is_valid_name(n) else None

    PREFIX_MAP = {'BOSS_': 'Boss', 'POLICE_': 'Police', 'PREDATOR_': 'Predator',
                   'GYM_': 'Gym', 'RAID_': 'Raid', 'SUMMON_': 'Summon'}

    def _get_base_l10n_name(raw_id: str) -> str | None:
        """Get the L10N name for a pal ID, trying direct and stripped variants."""
        # Direct lookup
        direct = _get_pal_name(f"PAL_NAME_{raw_id}")
        if direct:
            return direct
        # Strip known prefixes and try
        for prefix_str in PREFIX_MAP:
            if raw_id.startswith(prefix_str):
                inner = raw_id[len(prefix_str):]
                inner_name = _get_pal_name(f"PAL_NAME_{inner}")
                if inner_name:
                    return inner_name
        return None

    def _append_prefix_label(base: str, pal_id: str) -> str:
        """Append a generic prefix label like '(Boss)' to a base name."""
        for pfx_key, pfx_label in PREFIX_MAP.items():
            if pal_id.startswith(pfx_key) and pfx_label not in base:
                return f"{base} ({pfx_label})"
        return base

    def _clean_pal_id(raw: str) -> str:
        """Convert an internal pal ID into a readable fallback name."""
        name = raw
        for pfx in PREFIX_MAP:
            if name.startswith(pfx):
                name = name[len(pfx):]
                break
        name = name.replace('_', ' ').strip()
        import re
        name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
        return name if name else raw

    def resolve_pal_name(pal_id: str, monster_row: dict = None) -> str:
        """
        Resolve the in-game name for a pal using localization data.
        
        Priority:
        1. MonsterParameter OverrideNameTextID -> L10N table lookup, then append (Boss) etc.
        2. Direct PAL_NAME_{asset} lookup (case-insensitive), append prefix label
        3. Stripped prefix + base name, append prefix label
        4. Cleaned-up internal name as fallback
        """
        
        # 1. Try MonsterParameter OverrideNameTextID
        if monster_row and isinstance(monster_row, dict):
            name_text_id = monster_row.get('OverrideNameTextID', '')
            base_name = _get_pal_name(name_text_id) if name_text_id else None
            if base_name:
                return _append_prefix_label(base_name, pal_id)
        
        # 2 & 3. Try PAL_NAME_{asset} lookup (case-insensitive)
        base_name = _get_base_l10n_name(pal_id)
        if base_name:
            return _append_prefix_label(base_name, pal_id)
        
        # 4. Fallback: clean up the internal ID
        fallback = _clean_pal_id(pal_id)
        return _append_prefix_label(fallback, pal_id)
    
    updated_pals = []
    pal_icon_subdirs = [
        EXPORT_TEXTURES_DIR / 'PalIcon' / 'Normal',
        EXPORT_TEXTURES_DIR / 'PalIcon' / 'NPC',
        EXPORT_TEXTURES_DIR / 'PalIcon' / 'SKin',
    ]
    
    # Phase 1: process all pal IDs from icon tables (has actual icon data)
    processed_ids = set()
    for pal_id, row_data in sorted(icon_rows.items()):
        pal_id_lower = pal_id.lower()
        processed_ids.add(pal_id_lower)
        
        # Get existing entry if any
        existing_entry = existing_pals.get(pal_id_lower, {})
        
        # Extract icon path from export data
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        
        # Try to find and copy the icon
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'pals', pal_icon_subdirs)
        else:
            copied_icon = None
        
        # Resolve in-game name using L10N
        monster_row = monster_rows.get(pal_id, None)
        display_name = resolve_pal_name(pal_id, monster_row)
        
        # Determine icon
        existing_icon = existing_entry.get('icon', '')
        if existing_icon and not existing_icon.startswith('/icons/'):
            existing_icon = None
        final_icon = copied_icon or existing_icon or f'/icons/pals/{pal_id}_icon_normal.webp'
        if final_icon == f'/icons/pals/{pal_id}_icon_normal.webp' and not existing_icon:
            t_prefixed = f'/icons/pals/T_{pal_id}_icon_normal.webp'
            t_file = RESOURCES_DIR / t_prefixed.lstrip('/')
            if t_file.exists():
                final_icon = t_prefixed
            else:
                # Also try .png if .webp doesn't exist
                t_png = f'/icons/pals/T_{pal_id}_icon_normal.png'
                if (RESOURCES_DIR / t_png.lstrip('/')).exists():
                    final_icon = t_png
        
        # Build the pal entry
        pal_entry = {
            'name': display_name,
            'asset': pal_id,
            'icon': final_icon,
            'elements': existing_entry.get('elements', {})
        }
        
        updated_pals.append(pal_entry)
    
    # Phase 2: process pal IDs from monster parameter that aren't in icon tables
    # These are BOSS_/POLICE_ variants. Use the base pal icon as fallback.
    for pal_id in sorted(monster_rows.keys()):
        pal_id_lower = pal_id.lower()
        if pal_id_lower in processed_ids:
            continue  # Already added from icon table
        processed_ids.add(pal_id_lower)
        
        monster_row = monster_rows[pal_id_lower] if pal_id_lower in monster_rows else monster_rows.get(pal_id, {})
        existing_entry = existing_pals.get(pal_id_lower, {})
        
        # Try to derive base pal ID (strip BOSS_ prefix)
        base_pal_id = pal_id
        if pal_id.startswith('BOSS_'):
            base_pal_id = pal_id[5:]  # Remove 'BOSS_' prefix
        elif pal_id.startswith('POLICE_'):
            base_pal_id = pal_id[7:]  # Remove 'POLICE_' prefix
        
        # Look for icon of base pal
        base_icon = None
        if base_pal_id != pal_id:
            # Check if base pal exists in existing data
            base_lower = base_pal_id.lower()
            if base_lower in existing_pals:
                base_icon = existing_pals[base_lower].get('icon', None)
            # Or check icon table rows
            elif base_pal_id in icon_rows:
                base_icon_data = icon_rows[base_pal_id].get('Icon', {})
                if isinstance(base_icon_data, dict):
                    base_icon_path = base_icon_data.get('AssetPathName', '')
                    if base_icon_path:
                        fn = base_icon_path.split('/')[-1].split('.')[0] if '.' in base_icon_path else base_icon_path.split('/')[-1]
                        base_icon = find_and_copy_icon(fn, 'pals', pal_icon_subdirs)
        
        # Or check if there's a matching icon file
        icon_path = None
        if not base_icon:
            for fname in (f'T_{pal_id}_icon_normal', f'T_{pal_id}_icon', f'T_{pal_id}',
                         f'T_{base_pal_id}_icon_normal', f'T_{base_pal_id}'):
                for ext in ['.webp', '.png', '.PNG']:
                    for subdir in pal_icon_subdirs:
                        if subdir.exists():
                            matches = list(subdir.rglob(f'{fname}{ext}'))
                            if matches:
                                copied = copy_icon_to_resources(matches[0], 'pals')
                                if copied:
                                    icon_path = copied
                                    break
                    if icon_path:
                        break
        
        # Resolve in-game name using L10N
        # For variants from monster parameter, always resolve via L10N
        # to override old "en_text" or fallback names from previous runs
        display_name = resolve_pal_name(pal_id, monster_row)
        
        # Determine icon: prefer newly found icons, then base pal icon,
        # then existing entry (only if path looks valid), then generated fallback
        existing_icon = existing_entry.get('icon', '')
        if existing_icon and not existing_icon.startswith('/icons/'):
            existing_icon = None  # Skip corrupted paths like "/pals/T_icon_unknown.png"
        final_icon = icon_path or base_icon or existing_icon or f'/icons/pals/{pal_id}_icon_normal.webp'
        
        # Also try with T_ prefix for fallback paths
        if final_icon == f'/icons/pals/{pal_id}_icon_normal.webp' and not existing_icon:
            t_prefixed = f'/icons/pals/T_{pal_id}_icon_normal.webp'
            t_file = RESOURCES_DIR / t_prefixed.lstrip('/')
            if t_file.exists():
                final_icon = t_prefixed
        
        pal_entry = {
            'name': display_name,
            'asset': pal_id,
            'icon': final_icon,
            'elements': existing_entry.get('elements', {})
        }
        
        if not pal_entry['elements']:
            pal_entry['elements'] = {}
        
        updated_pals.append(pal_entry)
        if display_name != pal_id:
            print(f"  Added new variant from MonsterParameter: {pal_id} -> '{display_name}'")
        else:
            print(f"  Added new variant from MonsterParameter: {pal_id}")
    
    # Phase 3: Add any existing pals that might not be in the new export but we want to keep
    existing_assets = {p['asset'].lower() for p in updated_pals}
    for pal_id, entry in existing_pals.items():
        if pal_id not in existing_assets:
            print(f"  Keeping existing pal not in new exports: {entry.get('name', pal_id)}")
            updated_pals.append(entry)
    
    result = {'pals': updated_pals}
    save_resource_json('paldata.json', result)
    print(f"  Total pals: {len(updated_pals)}")


# ============================================================================
# NPC DATA UPDATE
# ============================================================================

def update_npc_data():
    """Update npcdata.json based on exported data tables."""
    print("\n=== Updating NPC Data ===")
    
    # NPC icon data
    npc_icon_data = load_export_json('Character/DT_PalBossNPCIcon.json')
    
    existing = load_resource_json('npcdata.json')
    existing_npcs = {n.get('asset', '').lower(): n for n in existing.get('npcs', [])}
    
    # Load NPC name localization
    # Maps: NAME_Male_Trader01 -> "Villager", NAME_DarkTrader -> "Black Marketeer", etc.
    npc_name_l10n = load_l10n_table('DT_HumanNameText_Common.json')
    # Build case-insensitive lookup
    _npc_l10n_lower = {k.lower(): v for k, v in npc_name_l10n.items()}
    
    def _resolve_npc_name(npc_id: str) -> str:
        """Resolve NPC display name from L10N (case-insensitive)."""
        # NAME_{asset} pattern
        key = f'NAME_{npc_id}'
        val = npc_name_l10n.get(key)
        if val and val.lower() not in ('en_text', 'none', ''):
            return val
        val = _npc_l10n_lower.get(key.lower())
        if val and val.lower() not in ('en_text', 'none', ''):
            return val
        return None
    
    all_rows = {}
    for data in [npc_icon_data]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    
    if not all_rows:
        print("  No NPC rows found. Skipping.")
        return
    
    npc_icon_subdirs = [
        EXPORT_TEXTURES_DIR / 'PalIcon' / 'NPC',
        EXPORT_TEXTURES_DIR / 'PalIcon' / 'Normal',
    ]
    
    updated_npcs = []
    for npc_id, row_data in sorted(all_rows.items()):
        npc_id_lower = npc_id.lower()
        existing_entry = existing_npcs.get(npc_id_lower, {})
        
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'npcs', npc_icon_subdirs)
        
        # Resolve name from L10N first, fall back to existing
        l10n_name = _resolve_npc_name(npc_id)
        npc_entry = {
            'name': l10n_name or existing_entry.get('name', npc_id),
            'asset': npc_id,
            'icon': copied_icon or existing_entry.get('icon', f'/icons/npcs/{npc_id}_icon_normal.webp')
        }
        updated_npcs.append(npc_entry)
    
    existing_assets = {n['asset'].lower() for n in updated_npcs}
    for npc_id, entry in existing_npcs.items():
        if npc_id not in existing_assets:
            print(f"  Keeping existing NPC not in new exports: {entry.get('name', npc_id)}")
            updated_npcs.append(entry)
    
    result = {'npcs': updated_npcs}
    save_resource_json('npcdata.json', result)


# ============================================================================
# ITEM DATA UPDATE
# ============================================================================

def update_item_data():
    """Update itemdata.json based on exported data tables."""
    print("\n=== Updating Item Data ===")
    
    item_table = load_export_json('Item/DT_ItemDataTable.json')
    item_table_common = load_export_json('Item/DT_ItemDataTable_Common.json')
    icon_table = load_export_json('Item/DT_ItemIconDataTable.json')
    icon_table_common = load_export_json('Item/DT_ItemIconDataTable_Common.json')
    
    existing = load_resource_json('itemdata.json')
    existing_items = {i.get('asset', '').lower(): i for i in existing.get('items', [])}
    
    # Load item name localization
    # Maps: ITEM_NAME_PalSphere -> "Pal Sphere", etc.
    item_name_l10n = load_l10n_table('DT_ItemNameText_Common.json')
    
    # Collect all item data rows
    all_item_rows = {}
    for data in [item_table, item_table_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_item_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_item_rows.update(rows)
    
    # Collect all icon rows
    all_icon_rows = {}
    for data in [icon_table, icon_table_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_icon_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_icon_rows.update(rows)
    
    if not all_item_rows and not all_icon_rows:
        print("  No item rows found. Skipping.")
        return
    
    # Merge data: use item rows as the primary source, enhance with icon rows
    all_item_ids = set(all_item_rows.keys()) | set(all_icon_rows.keys())
    
    item_icon_subdirs = [
        EXPORT_TEXTURES_DIR / 'Item',
        EXPORT_TEXTURES_DIR / 'Item' / 'Weapon',
        EXPORT_TEXTURES_DIR / 'UI' / 'InGame',
        EXPORT_TEXTURES_DIR / 'UI' / 'Main_Menu',
        EXPORT_TEXTURES_DIR / 'UI' / 'Common',
        EXPORT_TEXTURES_DIR.parent.parent / 'Others' / 'InventoryItemIcon' / 'Texture',
    ]
    
    def resolve_item_name(item_id: str, item_row: dict) -> str:
        """Resolve item display name from localization data.
        
        Item names come from DT_ItemNameText_Common.json where the key
        pattern is ITEM_NAME_{item_id} (e.g. ITEM_NAME_AIcore -> 'AI Core').
        Some items have an OverrideName field with a different key.
        """
        # Try OverrideName first (some items have custom name keys)
        override = ''
        if isinstance(item_row, dict):
            override = item_row.get('OverrideName', '')
        if override and override != 'None' and override in item_name_l10n:
            return item_name_l10n[override]
        
        # Standard lookup: ITEM_NAME_{item_id}
        standard_key = f'ITEM_NAME_{item_id}'
        if standard_key in item_name_l10n:
            return item_name_l10n[standard_key]
        
        # Also try item_id directly as a key
        if item_id in item_name_l10n:
            return item_name_l10n[item_id]
        
        return item_id
    
    updated_items = []
    for item_id in sorted(all_item_ids):
        item_id_lower = item_id.lower()
        existing_entry = existing_items.get(item_id_lower, {})
        
        # Get name from L10N if available
        item_row = all_item_rows.get(item_id, {})
        item_name = resolve_item_name(item_id, item_row)
        
        # Get icon from icon table
        icon_row = all_icon_rows.get(item_id, {})
        icon_path = ''
        if isinstance(icon_row, dict):
            icon_data = icon_row.get('Icon', {})
            if isinstance(icon_data, dict):
                icon_path = icon_data.get('AssetPathName', '')
        
        # Try to find and copy the icon
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'items', item_icon_subdirs)
        
        # Also try to find icon by L10N name or alternative patterns
        if not copied_icon:
            for try_name in [item_id, item_name.replace(' ', '')]:
                for alt_fn in [f'T_itemicon_{try_name}', f'T_{try_name}', try_name]:
                    for ext in ['.webp', '.png']:
                        found = find_and_copy_icon(alt_fn, 'items', item_icon_subdirs)
                        if found:
                            copied_icon = found
                            break
                    if copied_icon:
                        break
            if copied_icon:
                print(f"    Found icon for {item_id} via alt search: {copied_icon}")
        
        item_entry = {
            'name': existing_entry.get('name', item_name),
            'asset': item_id,
            'icon': copied_icon or existing_entry.get('icon', f'/icons/items/{item_id}.webp')
        }
        updated_items.append(item_entry)
    
    existing_assets = {i['asset'].lower() for i in updated_items}
    for item_id, entry in existing_items.items():
        if item_id not in existing_assets:
            print(f"  Keeping existing item not in new exports: {entry.get('name', item_id)}")
            updated_items.append(entry)
    
    result = {'items': updated_items}
    save_resource_json('itemdata.json', result)
    print(f"  Total items: {len(updated_items)}")


# ============================================================================
# STRUCTURE DATA UPDATE
# ============================================================================

def update_structure_data():
    """Update structuredata.json based on exported data tables."""
    print("\n=== Updating Structure Data ===")
    
    # Structures are found in MapObject and BaseCamp data tables
    mapobj_data = load_export_json('MapObject/DT_MapObjectDataTable.json')
    basecamp_data = load_export_json('BaseCamp/DT_BaseCampMapObjectDataTable.json')
    
    existing = load_resource_json('structuredata.json')
    existing_structures = {s.get('asset', '').lower(): s for s in existing.get('structures', [])}
    
    all_rows = {}
    for data in [mapobj_data, basecamp_data]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    
    if not all_rows:
        print("  No structure rows found. Skipping.")
        return
    
    structure_icon_subdirs = [
        EXPORT_TEXTURES_DIR / 'BuildObject' / 'Icon',
        EXPORT_TEXTURES_DIR / 'BuildObject' / 'PNG',
        EXPORT_TEXTURES_DIR / 'MapObject',
    ]
    
    updated_structures = []
    for struct_id, row_data in sorted(all_rows.items()):
        struct_id_lower = struct_id.lower()
        existing_entry = existing_structures.get(struct_id_lower, {})
        
        # Extract icon info
        icon_data = row_data.get('Icon', row_data.get('MapObjectIcon', {}))
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'structures', structure_icon_subdirs)
        
        struct_entry = {
            'name': existing_entry.get('name', struct_id),
            'asset': struct_id,
            'icon': copied_icon or existing_entry.get('icon', f'/icons/structures/{struct_id}.webp')
        }
        updated_structures.append(struct_entry)
    
    existing_assets = {s['asset'].lower() for s in updated_structures}
    for struct_id, entry in existing_structures.items():
        if struct_id not in existing_assets:
            print(f"  Keeping existing structure not in new exports: {entry.get('name', struct_id)}")
            updated_structures.append(entry)
    
    result = {'structures': updated_structures}
    save_resource_json('structuredata.json', result)
    print(f"  Total structures: {len(updated_structures)}")


# ============================================================================
# PASSIVE SKILL DATA UPDATE
# ============================================================================

def update_passive_data():
    """Update passivedata.json based on exported data tables."""
    print("\n=== Updating Passive Data ===")
    
    passive_main = load_export_json('PassiveSkill/DT_PassiveSkill_Main.json')
    passive_main_common = load_export_json('PassiveSkill/DT_PassiveSkill_Main_Common.json')
    
    existing = load_resource_json('passivedata.json')
    existing_passives = {p.get('asset', '').lower(): p for p in existing.get('passives', [])}
    
    all_rows = {}
    for data in [passive_main, passive_main_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    
    if not all_rows:
        print("  No passive rows found. Skipping.")
        return
    
    passive_icon_subdirs = [
        EXPORT_TEXTURES_DIR / 'UI' / 'Common',
        EXPORT_TEXTURES_DIR / 'StatusParameterIcon',
    ]
    
    updated_passives = []
    for passive_id, row_data in sorted(all_rows.items()):
        passive_id_lower = passive_id.lower()
        existing_entry = existing_passives.get(passive_id_lower, {})
        
        # Determine rank
        rank = existing_entry.get('rank', 1)
        if isinstance(row_data, dict):
            rank_data = row_data.get('Rank', row_data.get('PassiveRank', {}))
            if isinstance(rank_data, dict):
                rank = rank_data.get('value', rank)
            else:
                rank = rank_data or rank
        
        # Extract icon
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'passives', passive_icon_subdirs)
        
        passive_entry = {
            'name': existing_entry.get('name', passive_id),
            'asset': passive_id,
            'rank': rank,
            'icon': copied_icon or existing_entry.get('icon', '/icons/passives/T_icon_skillstatus_rank_arrow_04.png')
        }
        updated_passives.append(passive_entry)
    
    existing_assets = {p['asset'].lower() for p in updated_passives}
    for passive_id, entry in existing_passives.items():
        if passive_id not in existing_assets:
            print(f"  Keeping existing passive not in new exports: {entry.get('name', passive_id)}")
            updated_passives.append(entry)
    
    result = {'passives': updated_passives}
    save_resource_json('passivedata.json', result)
    print(f"  Total passives: {len(updated_passives)}")


# ============================================================================
# TECHNOLOGY DATA UPDATE
# ============================================================================

def update_technology_data():
    """Update technologydata.json based on exported data tables."""
    print("\n=== Updating Technology Data ===")
    
    tech_data = load_export_json('Technology/DT_PalTechnologyDataTable.json')
    
    existing = load_resource_json('technologydata.json')
    existing_techs = {t.get('asset', '').lower(): t for t in existing.get('technologies', [])}
    
    all_rows = {}
    if tech_data:
        if isinstance(tech_data, list):
            for table in tech_data:
                if isinstance(table, dict):
                    rows = table.get('Rows', {})
                    if rows:
                        all_rows.update(rows)
        elif isinstance(tech_data, dict):
            rows = tech_data.get('Rows', {})
            if rows:
                all_rows.update(rows)
    
    if not all_rows:
        print("  No technology rows found. Skipping.")
        return
    
    tech_icon_subdirs = [
        EXPORT_TEXTURES_DIR / 'UI' / 'Common',
        EXPORT_TEXTURES_DIR / 'UI' / 'InGame',
    ]
    
    updated_techs = []
    for tech_id, row_data in sorted(all_rows.items()):
        tech_id_lower = tech_id.lower()
        existing_entry = existing_techs.get(tech_id_lower, {})
        
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'technologies', tech_icon_subdirs)
        
        tech_entry = {
            'name': existing_entry.get('name', tech_id),
            'asset': tech_id,
            'icon': copied_icon or existing_entry.get('icon', f'/icons/technologies/{tech_id}.webp'),
            'type': existing_entry.get('type', '')
        }
        updated_techs.append(tech_entry)
    
    existing_assets = {t['asset'].lower() for t in updated_techs}
    for tech_id, entry in existing_techs.items():
        if tech_id not in existing_assets:
            print(f"  Keeping existing technology not in new exports: {entry.get('name', tech_id)}")
            updated_techs.append(entry)
    
    result = {'technologies': updated_techs}
    save_resource_json('technologydata.json', result)


# ============================================================================
# SKILL DATA UPDATE
# ============================================================================

def get_all_rows_for_tables(table_names: list[str]) -> dict:
    """
    Load multiple export tables and merge their Rows.
    Tables can be in the main file or _Common variant.
    """
    all_rows = {}
    for table_name in table_names:
        # Try main table
        data = load_export_json(table_name)
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
        
        # Try _Common variant
        base, ext = table_name.rsplit('.', 1) if '.' in table_name else (table_name, 'json')
        common_name = f"{base}_Common.{ext}"
        data_common = load_export_json(common_name)
        if data_common:
            if isinstance(data_common, list):
                for table in data_common:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data_common, dict):
                rows = data_common.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    return all_rows


def update_skill_data():
    """Update skilldata.json based on exported Waza data tables.
    
    NOTE: WazaDataTable uses numeric row keys (NewRow_1, etc.) with the actual
    skill ID stored in the 'WazaType' field (e.g. 'EPalWazaID::Unique_...').
    We extract the WazaType value and strip the 'EPalWazaID::' prefix.
    
    Skill display names are resolved from DT_SkillNameText_Common.json L10N data.
    The L10N key pattern is: ACTION_SKILL_{asset_name}
    e.g. 'ACTION_SKILL_CreepingBubble' -> 'Bubble March'
    """
    print("\n=== Updating Skill Data ===")
    
    all_rows = get_all_rows_for_tables(['Waza/DT_WazaDataTable.json'])
    
    existing = load_resource_json('skilldata.json')
    existing_skills = {s.get('asset', '').lower(): s for s in existing.get('skills', [])}
    
    # Load skill name localization
    # Maps: ACTION_SKILL_CreepingBubble -> 'Bubble March', etc.
    raw_skill_l10n = load_l10n_table('DT_SkillNameText_Common.json')
    # Build lookup by stripping ACTION_SKILL_ prefix
    skill_name_l10n = {}
    for uid_key, display_name in raw_skill_l10n.items():
        if uid_key.startswith('ACTION_SKILL_'):
            skill_asset = uid_key[len('ACTION_SKILL_'):]
            skill_name_l10n[skill_asset] = display_name
    
    if not all_rows:
        print("  No skill rows found. Skipping.")
        return
    
    # Collect unique skills by WazaType (stripping EPalWazaID:: prefix)
    skill_map = {}  # asset_lower -> {name, asset, element, power, cooldown}
    for row_key, row_data in all_rows.items():
        waza_type = ''
        element = ''
        power = 0
        cooldown = 0
        
        if isinstance(row_data, dict):
            waza_type = row_data.get('WazaType', '')
            element_raw = row_data.get('Element', '')
            power = row_data.get('Power', 0) or row_data.get('DisplayPower', 0) or 0
            cooldown = row_data.get('CoolTime', 0) or 0
            
            # Parse element
            if isinstance(element_raw, str) and element_raw.startswith('EPalElementType::'):
                element = element_raw.replace('EPalElementType::', '')
            
            # Parse element from embedded dict
            if isinstance(element_raw, dict):
                element = element_raw.get('value', '')
        
        # Skip disabled rows
        if isinstance(row_data, dict) and row_data.get('DisabledData', False):
            continue
            
        # Extract skill asset name from WazaType
        if isinstance(waza_type, str) and waza_type.startswith('EPalWazaID::'):
            skill_asset = waza_type.replace('EPalWazaID::', '')
        elif isinstance(waza_type, str):
            skill_asset = waza_type
        else:
            skill_asset = row_key
        
        skill_lower = skill_asset.lower()
        
        # Don't overwrite if already seen (prefer non-empty data)
        if skill_lower in skill_map:
            continue
        
        skill_map[skill_lower] = {
            'name': skill_asset,
            'asset': skill_asset,
            'element': element,
            'power': power if isinstance(power, (int, float)) else 0,
            'cooldown': cooldown if isinstance(cooldown, (int, float)) else 0
        }
    
    # Sort and build final list
    updated_skills = []
    for skill_asset in sorted(skill_map.keys()):
        entry = skill_map[skill_asset]
        skill_lower = entry['asset'].lower()
        existing_entry = existing_skills.get(skill_lower, {})
        
        # Resolve display name using L10N (ACTION_SKILL_{asset})
        l10n_name = skill_name_l10n.get(entry['asset'], None)
        
        skill_entry = {
            'name': existing_entry.get('name', l10n_name or entry['name']),
            'asset': entry['asset'],
            'element': existing_entry.get('element', entry['element']),
            'power': existing_entry.get('power', entry['power']),
            'cooldown': existing_entry.get('cooldown', entry['cooldown'])
        }
        updated_skills.append(skill_entry)
    
    # Add any existing skills not in new exports
    existing_assets = {s['asset'].lower() for s in updated_skills}
    for skill_id, entry in existing_skills.items():
        if skill_id not in existing_assets:
            print(f"  Keeping existing skill not in new exports: {entry.get('name', skill_id)}")
            updated_skills.append(entry)
    
    result = {'skills': updated_skills}
    save_resource_json('skilldata.json', result)
    print(f"  Total skills: {len(updated_skills)}")


# ============================================================================
# PAL EXP TABLE UPDATE
# ============================================================================

def update_pal_exp_table():
    """Update pal_exp_table.json based on exported Exp data tables."""
    print("\n=== Updating Pal EXP Table ===")
    
    exp_data = load_export_json('Exp/DT_Pal_EXP_DataTable.json')
    
    if not exp_data:
        print("  No EXP table found. Skipping.")
        return
    
    all_rows = {}
    if isinstance(exp_data, list):
        for table in exp_data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(exp_data, dict):
        rows = exp_data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    
    if not all_rows:
        print("  No EXP rows found. Skipping.")
        return
    
    save_resource_json('pal_exp_table.json', all_rows)
    print(f"  Total EXP entries: {len(all_rows)}")


# ============================================================================
# FRIENDSHIP DATA UPDATE
# ============================================================================

def update_friendship_data():
    """Update friendship.json based on exported Friendship data tables."""
    print("\n=== Updating Friendship Data ===")
    
    friend_data = load_export_json('Friendship/DT_PalFriendshipDataTable.json')
    
    if not friend_data:
        print("  No friendship data found. Skipping.")
        return
    
    all_rows = {}
    if isinstance(friend_data, list):
        for table in friend_data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(friend_data, dict):
        rows = friend_data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    
    if not all_rows:
        print("  No friendship rows found. Skipping.")
        return
    
    save_resource_json('friendship.json', all_rows)


# ============================================================================
# ITEMS PSP UPDATE
# ============================================================================

def update_items_psp():
    """Update items_psp.json (persistent storage pal items) based on exports."""
    print("\n=== Updating Items PSP ===")
    
    # This data comes from Item data tables
    item_table = load_export_json('Item/DT_ItemDataTable.json')
    
    if not item_table:
        print("  No item data found. Skipping.")
        return
    
    all_rows = {}
    if isinstance(item_table, list):
        for table in item_table:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(item_table, dict):
        rows = item_table.get('Rows', {})
        if rows:
            all_rows.update(rows)
    
    if not all_rows:
        print("  No item rows for PSP. Skipping.")
        return
    
    # Keep the structure similar to what the app expects
    existing = load_resource_json('items_psp.json')
    existing_items = existing.get('items', [])
    
    # This is typically the same as itemdata but fewer entries
    # We'll keep the existing list and merge with new items
    updated = {'items': existing_items}
    
    existing_assets = {i.get('asset', '').lower() for i in existing_items}
    for item_id in all_rows:
        if item_id.lower() not in existing_assets:
            updated['items'].append({
                'name': item_id,
                'asset': item_id,
                'icon': f'/icons/items/{item_id}.webp'
            })
    
    save_resource_json('items_psp.json', updated)


# ============================================================================
# PAL PASSIVE DATA UPDATE
# ============================================================================

def update_pal_passive_data():
    """Update palpassivedata.json based on exported data."""
    print("\n=== Updating Pal Passive Data ===")
    
    # Partner skill data often contains pal-specific passives
    partner_data = load_export_json('PartnerSkill/DT_PartnerSkillParameter.json')
    
    existing = load_resource_json('palpassivedata.json')
    existing_passives = {p.get('asset', '').lower(): p for p in existing.get('passives', [])}
    
    all_rows = {}
    if partner_data:
        if isinstance(partner_data, list):
            for table in partner_data:
                if isinstance(table, dict):
                    rows = table.get('Rows', {})
                    if rows:
                        all_rows.update(rows)
        elif isinstance(partner_data, dict):
            rows = partner_data.get('Rows', {})
            if rows:
                all_rows.update(rows)
    
    if not all_rows:
        print("  No partner skill rows found. Skipping.")
        return
    
    updated_passives = []
    for skill_id, row_data in sorted(all_rows.items()):
        skill_id_lower = skill_id.lower()
        existing_entry = existing_passives.get(skill_id_lower, {})
        
        passive_entry = {
            'name': existing_entry.get('name', skill_id),
            'asset': skill_id,
            'icon': existing_entry.get('icon', '/icons/passives/T_icon_skillstatus_rank_arrow_04.png')
        }
        updated_passives.append(passive_entry)
    
    existing_assets = {p['asset'].lower() for p in updated_passives}
    for passive_id, entry in existing_passives.items():
        if passive_id not in existing_assets:
            print(f"  Keeping existing pal passive not in new exports: {entry.get('name', passive_id)}")
            updated_passives.append(entry)
    
    result = {'passives': updated_passives}
    save_resource_json('palpassivedata.json', result)


# ============================================================================
# LAB RESEARCH DATA UPDATE
# ============================================================================

def update_lab_research_data():
    """Update labresearchdata.json based on exported Lab data tables."""
    print("\n=== Updating Lab Research Data ===")
    
    lab_data = load_export_json('Lab/DT_LaboratoryDataTable.json')
    
    if not lab_data:
        print("  No lab data found. Skipping.")
        return
    
    all_rows = {}
    if isinstance(lab_data, list):
        for table in lab_data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(lab_data, dict):
        rows = lab_data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    
    if not all_rows:
        print("  No lab research rows found. Skipping.")
        return
    
    save_resource_json('labresearchdata.json', all_rows)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 60)
    print("  Palworld Save Tools - Game Data Resource Updater")
    print("=" * 60)
    print(f"  Base directory: {BASE_DIR}")
    print(f"  Resources directory: {RESOURCES_DIR}")
    print(f"  Exports directory: {EXPORTS_DIR}")
    print("=" * 60)
    
    # Ensure output directories exist
    ensure_dir(RESOURCES_DIR)
    for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements']:
        ensure_dir(ICONS_DIR / subdir)
    
    # Check that export directories exist
    if not EXPORTS_DIR.exists():
        print(f"\nWARNING: Exports directory not found at {EXPORTS_DIR}")
        print("Please run the Palworld exporter first to generate the required export files.")
        print("The script will attempt to use existing resources as-is and only update ")
        print("what's available from exports.\n")
    
    # Run all updaters
    update_pal_data()
    update_npc_data()
    update_item_data()
    update_structure_data()
    update_passive_data()
    update_technology_data()
    update_skill_data()
    update_pal_exp_table()
    update_friendship_data()
    update_items_psp()
    update_pal_passive_data()
    update_lab_research_data()
    
    print("\n" + "=" * 60)
    print("  Update complete!")
    print("=" * 60)
    print("\nNote: Existing entries that are not found in new exports are preserved.")
    print("Icon files from exports are copied to resources/game_data/icons/")
    print("Run this script every time you get updated Palworld exports.")


if __name__ == '__main__':
    main()