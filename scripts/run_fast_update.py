#!/usr/bin/env python3
"""Run pal + item data update with optimized icon file handling."""
import os, sys, shutil, json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / 'scripts'))
sys.path.insert(0, str(BASE_DIR))

# Build a quick lookup of available icon files in exports
print("Building icon name lookup...")
EXPORT_TEXTURES_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Pal' / 'Texture'
OTHER_ICON_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Others'

icon_name_to_path = {}  # lowercase stem -> full path
for search_dir in [str(EXPORT_TEXTURES_DIR), str(OTHER_ICON_DIR)]:
    if os.path.exists(search_dir):
        for root, dirs, files in os.walk(search_dir):
            for f in files:
                stem = os.path.splitext(f)[0].lower()
                icon_name_to_path[stem] = os.path.join(root, f)
print(f"  Found {len(icon_name_to_path)} icon files")

from update_game_data import (
    update_pal_data, update_item_data, update_npc_data,
    ensure_dir, RESOURCES_DIR, ICONS_DIR,
)

# Monkey-patch find_and_copy_icon with a cached version
import update_game_data as ugd

def fast_find_and_copy(search_name, target_subdir, export_subdirs):
    if not search_name:
        return None
    name_lower = search_name.lower()
    target_dir = ICONS_DIR / target_subdir
    ensure_dir(target_dir)
    
    import re as _re
    
    # Build list of search terms to try (cache keys are stems WITHOUT extension)
    search_terms = [name_lower]
    
    # Also try without leading zeros in numbers (e.g. _05 -> _5)
    no_zero = _re.sub(r'_0+(\d)', r'_\1', name_lower)
    if no_zero != name_lower:
        search_terms.append(no_zero)
    
    # Deduplicate
    seen = set()
    unique_terms = []
    for t in search_terms:
        if t not in seen:
            seen.add(t)
            unique_terms.append(t)
    
    # Step 1: Exact match in cache (cache stores stems WITHOUT extension)
    for term in unique_terms:
        full_path = icon_name_to_path.get(term)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    
    # Step 2: Exact match with T_itemicon_ prefix
    for term in unique_terms:
        with_ti = f't_itemicon_{term}'
        full_path = icon_name_to_path.get(with_ti)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    
    # Step 3: Exact match with T_ prefix
    for term in unique_terms:
        with_t = f't_{term}'
        full_path = icon_name_to_path.get(with_t)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    
    # Step 4: Try stripping trailing _{digit} tier suffix, then try exact match
    # (only try this if the original didn't have _T_itemicon_ prefix already)
    if not name_lower.startswith('t_itemicon_'):
        tier_stripped = _re.sub(r'_\d+$', '', name_lower)
        if tier_stripped != name_lower:
            # Try original and T_itemicon_ prefixed versions of stripped name
            for try_term in [tier_stripped, f't_itemicon_{tier_stripped}', f't_{tier_stripped}']:
                full_path = icon_name_to_path.get(try_term)
                if full_path:
                    target_file = target_dir / os.path.basename(full_path)
                    if not target_file.exists():
                        shutil.copy2(full_path, str(target_file))
                    return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    
    # Step 5: Partial match - prefer longest (most specific) match
    best_match = None
    best_match_len = 0
    for term in unique_terms:
        for cache_key, full_path in icon_name_to_path.items():
            if term in cache_key and len(cache_key) > best_match_len:
                best_match = full_path
                best_match_len = len(cache_key)
    if best_match:
        target_file = target_dir / os.path.basename(best_match)
        if not target_file.exists():
            shutil.copy2(best_match, str(target_file))
        return f'/icons/{target_subdir}/{os.path.basename(best_match)}'
    
    return None

ugd.find_and_copy_icon = fast_find_and_copy

# Ensure output dirs
ensure_dir(RESOURCES_DIR)
for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements']:
    ensure_dir(ICONS_DIR / subdir)

print("\n=== Updating Pal Data ===")
update_pal_data()

print("\n=== Updating Item Data ===")
update_item_data()

print("\n=== Updating NPC Data ===")
update_npc_data()

print("\n=== Done ===")
