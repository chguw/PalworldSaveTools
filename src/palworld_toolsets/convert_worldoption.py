import sys, os, glob, gc, threading, time
from import_libs import *
from loading_manager import run_with_loading, show_information
from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication, QFileDialog
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'palworld_save_tools', 'commands'))
from convert import main as convert_main
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
def file_picker(ext):
    app = QApplication.instance() or QApplication(sys.argv)
    path = None
    if ext == 'sav':
        path, _ = QFileDialog.getOpenFileName(None, 'Select WorldOption.json', '', 'WorldOption.json (WorldOption.json)')
    elif ext == 'json':
        path, _ = QFileDialog.getOpenFileName(None, 'Select WorldOption.sav', '', 'WorldOption.sav (WorldOption.sav)')
    return path
def convert_worldoption_to_json():
    return convert_worldoption('json')
def convert_worldoption_to_sav():
    return convert_worldoption('sav')
def convert_worldoption(ext):
    worldoption_file = file_picker(ext)
    if not worldoption_file:
        return False
    loop = QEventLoop()
    if ext == 'sav':
        output_path = worldoption_file.replace('.json', '.sav')
        if output_path.endswith('.sav.sav'):
            output_path = output_path[:-4]
        def task():
            convert_json_to_sav(worldoption_file, output_path)
            gc.collect()
    else:
        output_path = worldoption_file.replace('.sav', '.json')
        def task():
            convert_sav_to_json(worldoption_file, output_path)
            gc.collect()
    run_with_loading(lambda _: loop.quit(), task)
    loop.exec()
    time.sleep(0.5)
    print(f'Converted {worldoption_file} to {output_path}')
    parent = QApplication.activeWindow()
    show_information(parent, t('tool.convert.done'), t('tool.convert.worldoption_done', source=worldoption_file, target=output_path))
    return True
def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['sav', 'json']:
        print('Usage: script.py <sav|json>')
        exit(1)
    if not convert_worldoption(sys.argv[1]):
        exit(1)
if __name__ == '__main__':
    main()