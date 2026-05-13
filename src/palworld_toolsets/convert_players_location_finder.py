import sys, os, gc, time
from import_libs import *
from loading_manager import run_with_loading, show_information
from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication, QFileDialog
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'palworld_save_tools', 'commands'))
from convert import main as convert_main
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
def convert_single_file(args):
    src, dst, ext = args
    try:
        old_argv = sys.argv
        try:
            if ext == 'sav':
                sys.argv = ['convert', src, '--output', dst, '--force']
            else:
                sys.argv = ['convert', src, '--output', dst, '--force']
            convert_main()
            return (src, dst, True, None)
        finally:
            sys.argv = old_argv
    except Exception as e:
        return (src, dst, False, str(e))
def convert_sav_to_json(input_file, output_file):
    old_argv = sys.argv
    try:
        sys.argv = ['convert', input_file, '--output', output_file, '--force']
        convert_main()
    finally:
        sys.argv = old_argv
def convert_json_to_sav(input_file, output_file):
    old_argv = sys.argv
    try:
        sys.argv = ['convert', input_file, '--output', output_file, '--force']
        convert_main()
    finally:
        sys.argv = old_argv
def pick_players_folder():
    app = QApplication.instance() or QApplication(sys.argv)
    folder = QFileDialog.getExistingDirectory(None, 'Select Players Folder', '')
    if folder and os.path.basename(folder) == 'Players':
        return folder
    print('Invalid folder or no folder selected.')
    return None
def convert_players_location_finder(ext):
    players_folder = pick_players_folder()
    if not players_folder:
        return False
    files_to_convert = []
    for root, _, files in os.walk(players_folder):
        for file in files:
            path = os.path.join(root, file)
            if ext == 'sav' and file.endswith('.json'):
                files_to_convert.append((path, path.replace('.json', '.sav'), ext))
            elif ext == 'json' and file.endswith('.sav'):
                files_to_convert.append((path, path.replace('.sav', '.json'), ext))
    if not files_to_convert:
        print('No valid files found for conversion.')
        return True
    loop = QEventLoop()
    converted_count = 0
    failed_count = 0
    def task():
        nonlocal converted_count, failed_count
        cpu_count = os.cpu_count() or 1
        max_workers = min(len(files_to_convert), max(8, cpu_count * 4))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(convert_single_file, args) for args in files_to_convert]
            for future in as_completed(futures):
                src, dst, success, error = future.result()
                if success:
                    print(f'Converted {src} to {dst}')
                    converted_count += 1
                else:
                    print(f'Failed to convert {src}: {error}')
                    failed_count += 1
        gc.collect()
    run_with_loading(lambda _: loop.quit(), task)
    loop.exec()
    time.sleep(0.5)
    parent = QApplication.activeWindow()
    if failed_count > 0:
        message = t('tool.convert.players_done_with_errors', count=converted_count, failed=failed_count)
    else:
        message = t('tool.convert.players_done', count=converted_count)
    show_information(parent, t('tool.convert.done'), message)
    return True
def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['sav', 'json']:
        print('Usage: script.py <sav|json>')
        exit(1)
    if not convert_players_location_finder(sys.argv[1]):
        exit(1)
if __name__ == '__main__':
    main()