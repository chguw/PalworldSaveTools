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
    'breeding.tab': 'Breeding',
    'breeding.mode.parents': 'Parents',
    'breeding.mode.children': 'Children',
    'breeding.search': 'Search pal...',
    'breeding.egg_hint': 'Palworld Breeding Combos',
    'breeding.hint': 'Click the button above to select a pal and view breeding combinations.',
    'breeding.parents_for': 'Parents for {name}',
    'breeding.children_for': 'Children for {name}',
    'breeding.unique': 'Unique Combos',
    'breeding.formula': 'Formula Combos',
    'breeding.no_breed': 'This pal cannot breed',
    'breeding.no_combos': 'No breeding combos found',
    'breeding.select_pal': 'Select a Pal...',
    'breeding.select_btn': 'Select',
    'breeding.search_placeholder': 'Type to filter pals...',
    'breeding.no_selection': 'Select a pal to see breeding combinations',
    'breeding.page_of': 'Page {n} of {total}',
    'breeding.combo_count': '{n} combo(s)',
    'breeding.prev': '<',
    'breeding.next': '>',
    'breeding.filter': 'Filter results...',
    'base.reassign_guild': 'Reassign to Guild',
    'base.reassign.no_other_guilds': 'No other guilds available.',
    'base.reassign.same_guild': 'Base already belongs to this guild.',
    'base.reassign.success': 'Base reassigned to guild "{name}"',
    'xgp.err.missing_files': 'Save is incomplete. Missing required: {files}\n\nThe game will not recognize this save without all required components. Open the save in PST to export the missing files, or obtain them from a working save.',
    'menu.file.load_xgp_save': 'Load GamePass Save',
    'character_transfer.source_btn': 'Source Save',
    'character_transfer.target_btn': 'Target Save',
    'tools.btn_steam': 'Steam',
    'tools.btn_gamepass': 'GamePass',
    'fix_host_save.player_file_missing': 'Player save file not found for {guid}',
    'character_transfer.player_file_missing': 'Player save file not found for {guid}',
}
OLD_KEYS = []
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
