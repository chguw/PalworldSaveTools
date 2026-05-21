#!/usr/bin/env python3
"""Run only pal + item data update with optimized icon searching."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_game_data import (
    update_pal_data, update_item_data, update_skill_data,
    update_passive_data, update_technology_data,
    update_npc_data, update_pal_exp_table,
    update_friendship_data, update_items_psp,
    update_pal_passive_data, update_lab_research_data,
    ensure_dir, RESOURCES_DIR, ICONS_DIR,
    EXPORT_TEXTURES_DIR
)

# Build icon cache once to speed up icon lookups
print("Building icon file cache for faster lookups...")
icon_cache = {}  # lowercase filename -> full path
for root, dirs, files in os.walk(str(EXPORT_TEXTURES_DIR)):
    for f in files:
        key = os.path.splitext(f)[0].lower()
        icon_cache[key] = os.path.join(root, f)
print(f"  Cached {len(icon_cache)} icon files")

# Monkey-patch find_and_copy_icon to use the cache
import update_game_data as ugd
original_find = ugd.find_and_copy_icon

def cached_find_and_copy_icon(search_name, target_subdir, export_subdirs):
    """Fast icon lookup using pre-built cache."""
    from pathlib import Path
    extensions = ['.webp', '.png', '.PNG', '.jpg', '.tga']
    search_lower = search_name.lower()
    
    for ext in extensions:
        cached_path = icon_cache.get(search_lower + ext.lower())
        if cached_path:
            target_dir = ugd.ICONS_DIR / target_subdir
            ensure_dir(target_dir)
            target_file = target_dir / os.path.basename(cached_path)
            if not target_file.exists():
                import shutil
                shutil.copy2(cached_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(cached_path)}'
    return None

ugd.find_and_copy_icon = cached_find_and_copy_icon

ensure_dir(RESOURCES_DIR)
for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements']:
    ensure_dir(ICONS_DIR / subdir)

update_pal_data()
update_item_data()

print("\n=== Update complete! ===")
