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
}
OLD_KEYS = [
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
            json.dump(data, f, ensure_ascii=False, indent=2)
        if removed:
            print(f'  {lang_code}: removed {len(removed)} keys')
def add_english_keys():
    lang_file = PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json'
    with open(lang_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key, english_text in NEW_TRANSLATIONS.items():
        data[key] = english_text
    with open(lang_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def translate_text(text: str, target_lang: str) -> str:
    translator = GoogleTranslator(source='en', target=target_lang)
    return translator.translate(text)
def add_keys_to_language(lang_code: str, lang_info: dict) -> bool:
    try:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for key, english_text in NEW_TRANSLATIONS.items():
            translated = translate_text(english_text, lang_info['code'])
            data[key] = translated
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'  [ERROR] Failed: {e}')
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
