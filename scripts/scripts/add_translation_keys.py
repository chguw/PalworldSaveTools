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
NEW_TRANSLATIONS = {'base_inventory.page': 'Page {page}/{total}', 'edit_pals.work_skill_level': 'Set Work Skill Level', 'edit_pals.work_skill_level_msg': '{skill} (0-10, 0=remove):', 'edit_pals.work_skill_books_hint': 'Work skill levels are derived from passives and base stats. Use work books to increase them.', 'edit_pals.set_trust': 'Set Trust Level', 'edit_pals.set_trust_rank_msg': 'Trust Rank (0-10):', 'edit_pals.select_pals_to_sync': 'Select pals to sync:', 'edit_pals.bulk_sync_preview': 'Preview (source pal):', 'edit_pals.bulk_sync_no_selection': 'No pals selected for syncing.', 'edit_pals.bulk_sync_cancel': 'Cancel', 'edit_pals.bulk_sync_all': 'All', 'edit_pals.bulk_sync_none': 'None', 'base_inventory.all_structures': 'All Structures', 'base_inventory.select_structure_action': 'Select Structure Action', 'base_inventory.search_structures': 'Search structures...', 'base_inventory.select_structure': 'Select a structure to perform actions', 'base_inventory.delete_structure_btn': 'Delete Structure', 'base_inventory.no_structures': 'No structures found', 'base_inventory.structures_removed': '{count} structures removed from {guilds} guilds', 'base_inventory.no_structures_removed': 'No structures found to remove', 'base_inventory.confirm_delete_structures': 'Confirm Delete Structures', 'base_inventory.confirm_delete_structures_msg': 'Are you sure you want to delete ALL "{structure_name}" from selected guilds? This action cannot be undone.', 'base_inventory.structures_affected': '{count} structures affected', 'base_inventory.find_bases': 'Find Bases'}
OLD_KEYS = []
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
    print('\n' + '=' * 60)
    print('  DONE')
    print('=' * 60)
if __name__ == '__main__':
    main()
    for p in [Path.cwd() / 'uv.lock', PROJECT_ROOT / 'uv.lock']:
        if p.exists():
            p.unlink()