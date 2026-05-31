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
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}}
NEW_TRANSLATIONS = {'inventory.add_all_effigies': 'Add All Effigies', 'inventory.add_all_effigies_confirm.title': 'Add All Effigies', 'inventory.add_all_effigies_confirm.msg': 'Add all {count} effigy types to key items?', 'inventory.add_all_effigies_done': 'Added effigies to key items.', 'player_item.no_effigies_found': 'No effigies found.', 'inventory.add_all_effigies_qty.title': 'Add All Effigies', 'inventory.add_all_effigies_qty.prompt': 'How many of each effigy type?', 'player_item.add_all_effigies_qty.title': 'Add All Effigies', 'player_item.add_all_effigies_qty.prompt': 'How many of each effigy type?', 'paldefender.title': 'PalDefender — Base Kill Command Generator', 'paldefender.filter_mode': 'Filter Mode:', 'paldefender.inactivity_only': 'Inactivity', 'paldefender.max_level_only': 'Max Level', 'paldefender.both': 'Both', 'paldefender.inactivity_days': 'Inactive ≥', 'paldefender.max_level': 'Max Level ≤', 'paldefender.skip_exclusions': 'Skip excluded guilds/bases', 'paldefender.hide_no_bases': 'Hide guilds with no bases', 'paldefender.scan': 'Scan Guilds', 'paldefender.select_all': 'Select All', 'paldefender.deselect_all': 'Deselect All', 'paldefender.col_guild': 'Guild', 'paldefender.col_guild_uid': 'Guild UID', 'paldefender.col_bases': 'Bases', 'paldefender.col_members': 'Members', 'paldefender.col_inactive': 'Least Active', 'paldefender.col_level': 'Max Level', 'paldefender.col_player_uid': 'Player UID', 'paldefender.col_pals': 'Pals', 'paldefender.generate': 'Generate Kill Commands', 'paldefender.close': 'Close', 'paldefender.last_online': 'Last Online', 'paldefender.level_label': 'Level'}
OLD_KEYS = ['inventory.max_all_abilities', 'inventory.max_all_abilities_confirm.title', 'inventory.max_all_abilities_confirm.msg', 'inventory.max_all_abilities_done', 'inventory.max_all_abilities_done.title', 'inventory.max_all_abilities_done.bulk', 'paldefender.filter_type', 'paldefender.instructions', 'paldefender.output', 'paldefender.max_level_label', 'paldefender.inactivity', 'paldefender_opened']
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