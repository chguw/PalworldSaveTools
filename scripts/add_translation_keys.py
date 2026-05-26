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
NEW_TRANSLATIONS = {'base_inventory.title': 'Base Inventory Editor', 'inventory.title': 'Player Inventory Editor', 'character_transfer.post_to_pre_blocked': 'Transfer from post-v1.0 to pre-v1.0 is not supported.\nPost-v1.0 contains new content that does not exist in the target version.', 'tools.section.converting': 'Conversion Tools', 'tools.section.management': 'Management Tools', 'tools.no_save_loaded': 'No save loaded', 'tool.convert.saves.desc': 'Convert save files between JSON and SAV formats', 'tool.convert.gamepass.steam.desc': 'Convert save files between GamePass and Steam versions', 'tool.convert.steamid.desc': 'Convert Steam IDs between different formats', 'tool.restore_map.desc': 'Restore the world map to a previous state', 'tool.slot_injector.desc': 'Inject player save slots into a world save file', 'tool.modify_save.desc': 'Modify and edit save file data directly', 'tool.character_transfer.desc': 'Transfer characters between different saves or servers', 'tool.fix_host_save.desc': 'Repair corrupted or broken host save files', 'pal_editor.party': 'Party', 'pal_editor.box': 'Box {n}', 'pal_editor.level': 'Level', 'pal_editor.attack': 'Attack', 'pal_editor.defense': 'Defense', 'pal_editor.work_speed': 'Work Speed', 'pal_editor.active_skills': 'Active Skills', 'pal_editor.passive_skills': 'Passive Skills', 'common.clear': '-- clear --', 'pal_editor.no_pal_data': 'No Pal Data', 'map.zone_shape.rect': 'Rectangle Zone', 'map.zone_shape.polygon': 'Polygon Zone', 'player_pal.select_active': 'Select Active Skill', 'player_pal.select_passive': 'Select Passive Skill', 'player_pal.no_active_selected': 'No active skill selected', 'player_pal.no_passive_selected': 'No passive skill selected'}
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
                print(f"  {lang_info['name']} ({lang_code}): [ERROR] {(e, 'inventory.unlock_hint_weapon'): \'Click to unlock with Weapon Slot Item\', \'inventory.max_weapon_slots\': \'All weapon slots are already unlocked!\'}")
    print('\n' + '=' * 60)
    print('  DONE')
    print('=' * 60)
if __name__ == '__main__':
    main()