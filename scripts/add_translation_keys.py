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
    subprocess.check_call(['pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}}
NEW_TRANSLATIONS = {
    'tools.drop_title': 'Drop Level.sav to Load Save',
    'tools.drop_hint_overlay': "Or click the 'Load Save' button above",
    'loading.success': 'Save Loaded Successfully',
    'loading.cancel': 'ESC to cancel',
    'tools.drag_hint': 'or drag & drop a Level.sav file here',
    'dashboard.overview': 'World Overview',
    'dashboard.no_save': 'No Save Loaded',
    'dashboard.welcome_title': 'Palworld Save Tools',
    'dashboard.welcome_tips': '📁 Click <b>Load Save</b> to open your Level.sav\n🖱️ Or drag & drop a save file onto this window\n🔧 Then use the tools below to manage your world',
    'dashboard.stat_players': 'Players',
    'dashboard.stat_guilds': 'Guilds',
    'dashboard.stat_bases': 'Bases',
    'dashboard.stat_pals': 'Pals',
    'sidebar.locked': 'Load a save file first',
    'character_transfer.source_tooltip': 'Select the Level.sav file to use as the source (host).',
    'character_transfer.target_tooltip': 'Select the Level.sav file to use as the target.',
    'character_transfer.transfer_all_tooltip': 'Transfer all characters from source to target (in memory).',
    'character_transfer.transfer_tooltip': 'Transfer the selected character(s).',
    'character_transfer.save_tooltip': 'Write changes to target Level.sav and player files.',
    'character_transfer.selection_none': 'Source: N/A, Target: N/A',
    'character_transfer.selection_status': 'Source: {source}, Target: {target}',
}
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
    print('  ADDING TRANSLATION KEYS')
    print('=' * 60)
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