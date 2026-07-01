import json
import os
import sys
import concurrent.futures
from pathlib import Path
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print('Installing deep-translator...')
    import subprocess
    subprocess.check_call(['uv', 'pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}}
NEW_TRANSLATIONS = {
    'json_editor.tab': 'JSON Editor',
    'json_editor.refresh': 'Refresh from Save',
    'json_editor.export': 'Export JSON',
    'json_editor.import': 'Import JSON',
    'json_editor.no_save': 'No save loaded',
    'json_editor.loaded': 'JSON loaded from save',
    'json_editor.export_save': 'Export JSON',
    'json_editor.import_save': 'Import JSON',
    'json_editor.exported': 'Exported to {path}',
    'json_editor.imported': 'Imported {path}',
    'json_editor.col_key': 'Key',
    'json_editor.col_value': 'Value',
    'json_editor.col_type': 'Type',
    'json_editor.search_placeholder': 'Search...',
    'json_editor.search_prev': 'Previous match',
    'json_editor.search_next': 'Next match',
    'json_editor.search_count': '{count} matches',
    'json_editor.search_no_matches': 'No matches',
    'base_inventory.booth_item_title': 'Booth Items: {count}',
    'base_inventory.booth_item_no_data': 'Booth: No container data',
    'base_inventory.booth_pal_title': 'Booth Pals: {count}',
    'base_inventory.booth_pal_no_data': 'Booth: No pals listed',
    'edit_pals.ctx.bulk_heal': 'Bulk Restore',
    'edit_pals.bulk_heal_title': 'Bulk Restore - {name}',
    'edit_pals.bulk_heal_desc': 'Restores HP to max, cures sickness, resets physical health.',
    'edit_pals.restore_all': 'Restore All',
    'edit_pals.restore_all_confirm': 'Restore HP, SAN, and hunger for all pals in party & all palbox pages? Sickness will also be cured.',
    'edit_pals.restore_all_success': 'Restored {count} pals.',
    'edit_pals.max_all': 'Max All',
    'edit_pals.max_all_confirm': 'Max all stats (talents, ranks, friendship, awakening, level 80, work suitabilities) for all pals in party & all palbox pages?',
    'edit_pals.max_all_success': 'Maxed {count} pals.',
    'base_inventory.restore_all': 'Restore All',
    'base_inventory.restore_all_confirm': 'Restore HP, SAN, and hunger for all working pals in this base? Sickness will also be cured.',
    'base_inventory.restore_all_success': 'Restored {count} pals.',
    'base_inventory.max_all': 'Max All',
    'base_inventory.max_all_confirm': 'Max all stats (talents, ranks, friendship, awakening, level 80, work suitabilities) for all working pals in this base?',
    'base_inventory.max_all_success': 'Maxed {count} pals.',
    'inventory.max_all_abilities': 'Max All Abilities',
    'inventory.max_all_abilities_confirm.title': 'Max All Abilities',
    'inventory.max_all_abilities_confirm.msg': 'Max all relic abilities for this player?',
    'inventory.max_all_abilities_done': 'Abilities maxed to maximum rank.',
    'inventory.add_all_key_items_confirm.title': 'Add All Key Items',
    'inventory.add_all_key_items_confirm.msg': 'Add all missing key items? ({count} items)',
    'inventory.add_all_key_items_success.title': 'Add All Key Items',
    'inventory.add_all_key_items_success.msg': 'Added {count} missing key items.',
    'base_inventory.replace_structures': 'Replace Structures',
    'base_inventory.replace_dialog_title': 'Replace Structures - {base}',
    'base_inventory.replace_from_list': 'Structures in Base',
    'base_inventory.replace_to_list': 'Replace With',
    'base_inventory.replace_select_prompt': 'Select a structure on the left...',
    'base_inventory.replace_no_building_parts': 'No building parts found in this base.',
    'base_inventory.replace_source_label': 'Replace:',
    'base_inventory.replace_target_label': 'With:',
    'base_inventory.replace_confirm': 'Replace {count} {old_name} with {new_name}?',
    'base_inventory.replace_success': 'Replaced {count} structures.',
    'base_inventory.replace_skip_current': 'Same element',
    'stat_tooltip.hp': 'HP',
    'stat_tooltip.hp_desc': "Pal's HP.\nSurvives longer as\nHP increases.",
    'stat_tooltip.atk': 'Attack',
    'stat_tooltip.atk_desc': "Pal's Attack.\nDamage dealt increases as\nAttack increases.",
    'stat_tooltip.def': 'Defense',
    'stat_tooltip.def_desc': "Pal's Defense.\nDamage taken decreases as\nDefense increases.",
    'stat_tooltip.ws': 'Work Speed',
    'stat_tooltip.ws_desc': "Pal's Work Speed.\nAffects the efficiency of\nworking on various tasks\nat base.",
    'stat_tooltip.bonus_trust': 'Bonus from Trust +{value}',
    'stat_tooltip.bonus_awakening': 'Bonus from Awakening +{value}',
    'stat_tooltip.enhance_souls': 'Enhance Souls +{percent}%',
    'docs.tab': 'Docs',
    'docs.wiki': 'Wiki',
    'docs.guides': 'Guides',
    'docs.tours': 'Tours',
    'docs.wiki.pals': 'Pals',
    'docs.wiki.items': 'Items',
    'docs.wiki.buildings': 'Buildings',
    'docs.wiki.active_skills': 'Active Skills',
    'docs.wiki.passive_skills': 'Passive Skills',
    'docs.wiki.technologies': 'Technologies',
    'docs.wiki.elements': 'Elements',
    'docs.wiki.work_suitability': 'Work Suitability',
    'docs.wiki.search': 'Search...',
    'docs.wiki.select_hint': 'Select an item to view details',
    'docs.wiki.no_results': 'No results found',
    'docs.wiki.category': 'Category',
    'docs.guides.toc_title': 'Table of Contents',
    'docs.tours.start': 'Start Tour',
    'docs.tours.description': 'Interactive guide through the {tab_name} tab',
    'docs.tours.title': 'Tours',
    'map.info.base_pals': 'Base Pals:',
    'docs.wiki.filter.rank': 'Rank',
    'docs.wiki.filter.value.boss': 'Ancient',
    'docs.wiki.filter.value.standard': 'Standard',
    'docs.wiki.sort.work_level': 'Level',
    'edit_pals.learnt_skills_search': 'Search skills...',
    'edit_pals.learnt_skills_learn_all': 'Learn All',
}
OLD_KEYS = [
    'json_editor.apply', 'json_editor.validate', 'json_editor.applied',
    'json_editor.apply_error', 'json_editor.apply_error_detail',
    'json_editor.empty', 'json_editor.valid', 'json_editor.modified', 'json_editor.unchanged',
    'inventory.add_all_effigies',
    'inventory.add_all_effigies_confirm.title',
    'inventory.add_all_effigies_confirm.msg',
    'inventory.add_all_effigies_done',
    'inventory.add_all_effigies_qty.title',
    'inventory.add_all_effigies_qty.prompt',
    'player_item.add_all_effigies_qty.title',
    'player_item.add_all_effigies_qty.prompt',
]
def _clean_uv_locks():
    for p in [Path.cwd() / 'uv.lock', PROJECT_ROOT / 'uv.lock']:
        if p.exists():
            p.unlink()

def remove_old_keys_from_all():
    for lang_code in list(LANGUAGES.keys()) + ['en_US']:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        if not lang_file.exists():
            continue
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        removed = [key for key in OLD_KEYS if data.pop(key, None) is not None]
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if removed:
            print(f'  {lang_code}: removed {len(removed)} keys')
def add_english_keys():
    lang_file = PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json'
    with open(lang_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key, english_text in NEW_TRANSLATIONS.items():
        data[key] = english_text
    with open(lang_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def translate_text(text: str, target_lang: str) -> str:
    translator = GoogleTranslator(source='en', target=target_lang)
    return translator.translate(text)
def add_keys_to_language(lang_code: str, lang_info: dict) -> bool:
    try:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        had_failure = False
        for key, english_text in NEW_TRANSLATIONS.items():
            try:
                translated = translate_text(english_text, lang_info['code'])
                data[key] = translated
            except Exception as e:
                print(f'  [WARN] {key}: translate failed ({e}), using English fallback')
                data[key] = english_text
                had_failure = True
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return not had_failure
    except Exception as e:
        print(f'  [ERROR] File-level failure: {e}')
        return False
def main():
    _clean_uv_locks()
    print('\n' + '=' * 60)
    print('  UPDATING TRANSLATION KEYS')
    print('=' * 60)
    print('\nRemoving old keys...')
    remove_old_keys_from_all()
    print('\nEnglish (en_US)...')
    add_english_keys()
    print('  [OK] Success')
    print('\nTranslating to other languages (parallel processing)...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
        future_to_lang = {executor.submit(add_keys_to_language, lang_code, lang_info): lang_code for lang_code, lang_info in LANGUAGES.items()}
        for future in concurrent.futures.as_completed(future_to_lang):
            lang_code = future_to_lang[future]
            lang_info = LANGUAGES[lang_code]
            try:
                success = future.result()
                print(f"  {lang_info['name']} ({lang_code}): {('[OK] Success' if success else '[ERROR] Failed')}")
            except Exception as e:
                print(f"  {lang_info['name']} ({lang_code}): [ERROR] {e}")
    _clean_uv_locks()
    print('\n' + '=' * 60)
    print('  DONE')
    print('=' * 60)
if __name__ == '__main__':
    main()
