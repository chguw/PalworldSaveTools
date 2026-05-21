#!/usr/bin/env python3
"""Run only the item data update from update_game_data.py."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from update_game_data import update_item_data, ensure_dir, RESOURCES_DIR, ICONS_DIR

ensure_dir(RESOURCES_DIR)
for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements']:
    ensure_dir(ICONS_DIR / subdir)

update_item_data()
print("Item data update complete.")
