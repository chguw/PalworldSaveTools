from import_libs import *
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav

from loading_manager import show_critical, run_with_loading
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QTimer
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio import constants
from palworld_toolsets.game_pass_save_fix import find_valid_saves
import os, time, shutil
savegames_path = os.path.join(os.environ['LOCALAPPDATA'], 'Pal', 'Saved', 'SaveGames')
restore_map_path = os.path.join('.', 'Backups', 'Restore Map')
os.makedirs(restore_map_path, exist_ok=True)
def backup_local_data(subfolder_path):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join(restore_map_path, timestamp, os.path.basename(subfolder_path))
    os.makedirs(backup_folder, exist_ok=True)
    backup_file = os.path.join(backup_folder, 'LocalData.sav')
    original_local_data = os.path.join(subfolder_path, 'LocalData.sav')
    if os.path.exists(original_local_data):
        shutil.copy(original_local_data, backup_file)
        print(t('Backup created at: {backup_file}', backup_file=backup_file))
def clear_fog_in_local_data(path):
    from palsav.io import load_sav
    gvas = load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
    d = gvas.dump()
    sd = d['properties']['SaveData']['value']
    if 'WorldMapUISaveDataMap' in sd:
        for entry in sd['WorldMapUISaveDataMap']['value']:
            mask = entry['value']['MaskTextureData']['value']
            mask['values'] = b'\x00' * len(mask['values'])
        print('  WorldMapUISaveDataMap fog cleared')
    elif 'WorldMapMaskTextureV4' in sd:
        mask = sd['WorldMapMaskTextureV4']['value']
        mask['values'] = b'\x00' * len(mask['values'])
        print('  WorldMapMaskTextureV4 fog cleared')
    hl = sd.get('Local_HiddenLocationFlagMap', {}).get('value', [])
    for entry in hl:
        entry['value'] = False
    print(f'  Hidden locations set: {len(hl)} entries')
    ng = GvasFile.load(d)
    from palsav.io import save_sav
    save_sav(ng, path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def clear_fog_in_all_subfolders():
    updated_count = 0
    valid_saves = find_valid_saves(savegames_path)
    for subfolder_path in valid_saves:
        target_path = os.path.join(subfolder_path, 'LocalData.sav')
        if os.path.exists(target_path):
                    backup_local_data(subfolder_path)
                    print(t('Clearing fog in: {path}', path=subfolder_path))
                    clear_fog_in_local_data(target_path)
                    updated_count += 1
    if constants.loaded_level_json and constants.current_save_path:
        local_path = os.path.join(constants.current_save_path, 'LocalData.sav')
        if os.path.exists(local_path):
            backup_local_data(constants.current_save_path)
            print(t('Clearing fog in: {path}', path=constants.current_save_path))
            clear_fog_in_local_data(local_path)
            updated_count += 1
    print('=' * 80)
    print(t('Total worlds/servers updated: {copied_count}', copied_count=updated_count))
    print('=' * 80)
def center_window(win):
    win_center = win.frameGeometry().center()
    from PySide6.QtWidgets import QApplication
    screen = QApplication.screenAt(win_center)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen_geometry.center())
    win.move(geo.topLeft())
def restore_map():
    class RestoreMapDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(t('tool.restore_map'))
            self.setFixedSize(640, 320)
            self.load_styles()
            try:
                if ICON_PATH and os.path.exists(ICON_PATH):
                    self.setWindowIcon(QIcon(ICON_PATH))
            except Exception:
                pass
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(12)
            glass_frame = QFrame()
            glass_frame.setObjectName('glass')
            glass_layout = QVBoxLayout(glass_frame)
            glass_layout.setContentsMargins(14, 14, 14, 14)
            glass_layout.setSpacing(12)
            tip_label = QLabel(t('Warning: This will perform the following actions:'))
            tip_label.setFont(QFont(constants.FONT_FAMILY, 12, QFont.Bold))
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setStyleSheet('color: #FF6347;')
            glass_layout.addWidget(tip_label)
            steps_layout = QVBoxLayout()
            step_font = QFont(constants.FONT_FAMILY, 10)
            step1_label = QLabel(t('1.Clear fog from each existing LocalData.sav'))
            step1_label.setFont(step_font)
            step1_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step1_label)
            step2_label = QLabel(t('2.Create backups of each LocalData.sav before modifying'))
            step2_label.setFont(step_font)
            step2_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step2_label)
            step3_label = QLabel(t('3.Preserve all existing map data (icons, markers, etc.)'))
            step3_label.setFont(step_font)
            step3_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step3_label)
            glass_layout.addLayout(steps_layout)
            self.result_label = QLabel('')
            self.result_label.setAlignment(Qt.AlignCenter)
            self.result_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
            self.result_label.setStyleSheet('color: #7FFF00;')
            glass_layout.addWidget(self.result_label)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            import nerdfont as nf
            self.xgp_btn = QPushButton(f"{nf.icons['nf-fa-xbox']} Clear XGP Fog")
            self.xgp_btn.setFont(QFont(constants.FONT_FAMILY, 12))
            self.xgp_btn.setMinimumSize(140, 40)
            self.xgp_btn.clicked.connect(self.on_xgp_clear_fog)
            button_layout.addWidget(self.xgp_btn)
            self.yes_button = QPushButton(t('Yes'))
            self.yes_button.setFont(QFont(constants.FONT_FAMILY, 12))
            self.yes_button.setMinimumSize(120, 40)
            self.yes_button.clicked.connect(self.on_yes)
            button_layout.addWidget(self.yes_button)
            self.no_button = QPushButton(t('No'))
            self.no_button.setFont(QFont(constants.FONT_FAMILY, 12))
            self.no_button.setMinimumSize(120, 40)
            self.no_button.clicked.connect(self.on_no)
            button_layout.addWidget(self.no_button)
            button_layout.addStretch()
            glass_layout.addLayout(button_layout)
            main_layout.addWidget(glass_frame)
            center_window(self)
            self.setModal(True)
        def showEvent(self, event):
            super().showEvent(event)
            if not event.spontaneous():
                self.activateWindow()
                self.raise_()
        def on_xgp_clear_fog(self):
            from palworld_xgp_import.gamepass_manager import (
                pick_xgp_world, extract_save_to_temp,
            )
            pick = pick_xgp_world(self, 'Clear XGP Fog')
            if not pick:
                return
            cpath, save_id, index = pick
            import tempfile as _tf, shutil as _sh
            tmp = _tf.mkdtemp(prefix='pst_rm_xgp_')
            extracted = extract_save_to_temp(cpath, index, save_id, tmp)
            level_path = extracted.get('Level.sav')
            local_path = extracted.get('LocalData.sav')
            if not level_path or not local_path or not os.path.isfile(local_path):
                _sh.rmtree(tmp, ignore_errors=True)
                show_critical(self, t('Error'), 'Required save files not found.')
                return
            old_name = 'World'
            _mp = extracted.get('LevelMeta.sav')
            if _mp and os.path.isfile(_mp):
                try:
                    from palworld_aio.utils import sav_to_gvasfile
                    old_name = sav_to_gvasfile(_mp).properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'World')
                except Exception:
                    pass
            new_name, ok = QInputDialog.getText(self, 'Save as New World',
                f'World name (original: "{old_name}"):',
                QLineEdit.Normal, f'{old_name} (cleared fog)')
            if not ok or not new_name.strip():
                _sh.rmtree(tmp, ignore_errors=True)
                return
            run_with_loading(
                callback=lambda _: self._xgp_clear_done(),
                func=self._xgp_clear_work,
                tmp=tmp, cpath=cpath, level_path=level_path, new_name=new_name,
                save_id=save_id,
                parent=self,
            )
        def _xgp_clear_work(self, tmp, cpath, level_path, new_name, save_id):
            from palworld_xgp_import.gamepass_manager import save_xgp_changes
            from palworld_aio.utils import sav_to_gvas_wrapper, wrapper_to_sav
            import shutil as _sh
            old_level = constants.loaded_level_json
            old_path = constants.current_save_path
            old_xgp_path = constants.xgp_container_path
            old_xgp_id = constants.xgp_save_id
            old_xgp_flag = constants.xgp_loaded
            constants.loaded_level_json = sav_to_gvas_wrapper(level_path)
            constants.current_save_path = tmp
            constants.xgp_container_path = cpath
            constants.xgp_save_id = save_id
            constants.xgp_loaded = True
            try:
                backup_local_data(tmp)
                clear_fog_in_all_subfolders()
                wrapper_to_sav(constants.loaded_level_json, level_path)
                save_xgp_changes(
                    container_path=cpath,
                    current_save_path=tmp,
                    new_world_name=new_name.strip(),
                )
            finally:
                if old_level:
                    constants.loaded_level_json = old_level
                    constants.current_save_path = old_path
                    constants.xgp_container_path = old_xgp_path
                    constants.xgp_save_id = old_xgp_id
                    constants.xgp_loaded = old_xgp_flag
                else:
                    constants.loaded_level_json = None
                    constants.current_save_path = None
                    constants.xgp_container_path = None
                    constants.xgp_save_id = None
                    constants.xgp_loaded = False
                _sh.rmtree(tmp, ignore_errors=True)
        def _xgp_clear_done(self):
            self.result_label.setText(t('XGP fog cleared!'))
            self.xgp_btn.setEnabled(False)
            self.yes_button.setEnabled(False)
            self.no_button.setEnabled(False)
            QTimer.singleShot(2000, self.accept)
        def on_yes(self):
            run_with_loading(
                callback=lambda _: self._on_clear_done(),
                func=clear_fog_in_all_subfolders,
                parent=self,
            )
        def _on_clear_done(self):
            self.result_label.setText(t('Fog cleared successfully!'))
            self.yes_button.setEnabled(False)
            self.no_button.setEnabled(False)
            QTimer.singleShot(2000, self.accept)
        def on_no(self):
            self.reject()
        def load_styles(self):
            ThemeManager.load_styles(self)
    dialog = RestoreMapDialog()
    return dialog
def main():
    import sys
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    dialog = restore_map()
    dialog.exec()
    if not QApplication.instance().closingDown():
        try:
            if not app.instance():
                app.exec()
        except Exception:
            pass
if __name__ == '__main__':
    main()