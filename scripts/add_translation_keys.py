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
NEW_TRANSLATIONS = {
    'tools.save_loaded': 'Save Loaded',
    'tools.drop_title': 'Drop Level.sav to Load Save',
    'tools.drop_hint_overlay': "Or click the 'Load Save' button above",
    'loading.success': 'Operation Completed Successfully',
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
    'inventory.add_all_effigies': 'Add All Effigies',
    'inventory.add_all_key_items': 'Add All Key Items',
    'inventory.add_all_effigies_confirm.title': 'Add All Effigies',
    'inventory.add_all_effigies_confirm.msg': 'Add all 13 effigy types to key items?',
    'inventory.add_all_key_items_confirm.title': 'Add All Key Items',
    'inventory.add_all_key_items_confirm.msg': 'Add all missing key items? ({count} items)',
    'inventory.no_new_items': 'All key items already present.',
    'player_item.no_effigies_found': 'No effigies found.',
    'inventory.add_all_effigies_qty.title': 'Add All Effigies',
    'inventory.add_all_effigies_qty.prompt': 'How many of each effigy type?',
    'player_item.add_all_effigies_qty.title': 'Add All Effigies',
    'player_item.add_all_effigies_qty.prompt': 'How many of each effigy type?',
    'inventory.unlock_all_map': 'Unlock All Map + Fast Travel',
    'inventory.select_player_first': 'Please select a player first.',
    'inventory.unlock_all_map_confirm.title': 'Unlock All Map + Fast Travel',
    'inventory.unlock_all_map_confirm.msg': 'Unlock all fast travel points, reveal all map areas, and unlock world map for {count} player(s)?',
    'inventory.unlock_all_map_success.title': 'Unlock All Map',
    'inventory.unlock_all_map_success.msg': 'Unlock all map completed successfully!',
    'inventory.unlock_all_map_bulk_success.msg': 'Unlocked map + fast travel for {count} player(s).',
    'xgp.err.admin_required.title': 'Admin Required',
    'xgp.err.admin_required.msg': 'Please restart as Administrator.',
    'xgp.admin_warning.title': 'Administrator privileges required',
    'xgp.admin_warning.msg': 'This operation will:\n• Stop Xbox Gaming Services (GamingServices.exe)\n• Restart them after conversion\n\nYour game may be affected if running. Continue?',
    'xgp.msg.world_rename_info': 'Your world name "{old}" will be carried over to the Game Pass save.\nYou can rename it on the next screen if you like.',
    'xgp.ui.available_saves': 'Available Saves ▼',
    'xgp.ui.select_save_placeholder': 'Select a save...',
    'xgp.ui.select_xgp_folder': 'Select XGP Save Folder',
    'xgp.ui.select_steam_folder': 'Select Steam Save Folder to Transfer',
    'xgp.ui.select_destination': 'Select where to place converted save',
    'xgp.err.import_failed.title': 'Import Failed',
    'xgp.err.not_windows': 'Xbox Game Pass save management is only available on Windows.',
    'xgp.msg.all_converted_success': 'All {total} save files converted successfully.',
    'xgp.msg.some_converted_success': 'Successfully converted {successful} out of {total} save files.',
    'xgp.msg.conversion_done.title': 'Conversion Done',
    'xgp.msg.conversion_failed.title': 'Conversion Failed',
    'xgp.msg.no_saves_converted': 'No save files were converted successfully.',
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
    for p in [Path.cwd() / 'uv.lock', PROJECT_ROOT / 'uv.lock']:
        if p.exists():
            p.unlink()
