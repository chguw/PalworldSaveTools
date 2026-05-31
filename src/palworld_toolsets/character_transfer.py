from import_libs import *
from loading_manager import show_information, show_warning
from PySide6.QtWidgets import QHeaderView, QWidget, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QApplication, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
import os
from palworld_save_tools.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES
from palworld_save_tools.gvas import GvasFile
from palworld_aio.ui.styles import ThemeManager
from palworld_aio.container_ownership import ContainerOwnership
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
_TRANSFER_STEPS = {'character': True, 'tech_data': True, 'inventory': True, 'guild': True, 'pals': True, 'dynamics': True, 'timestamps': True}
player_list_cache = []
def _load_sav(path):
    with open(path, 'rb') as f:
        raw_gvas, save_type = decompress_sav_to_gvas(f.read())
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    gvas_file.save_type = save_type
    return gvas_file
def _write_sav(gvas_file, path):
    data = gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES)
    t = getattr(gvas_file, 'save_type', 50)
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(compress_gvas_to_sav(data, t))
    os.replace(tmp, path)
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def format_last_seen(last_online_time, current_tick):
    try:
        if last_online_time is None or last_online_time == 0:
            return 'Unknown'
        diff = (current_tick - last_online_time) / 10000000.0
        days = int(diff // 86400)
        hours = int(diff % 86400 // 3600)
        mins = int(diff % 3600 // 60)
        if days > 0:
            return f'{days}d {hours}h'
        elif hours > 0:
            return f'{hours}h {mins}m'
        else:
            return f'{mins}m'
    except:
        return 'Unknown'
def get_player_level_from_cspm(level_json, player_uid):
    try:
        player_uid_clean = str(player_uid).lower().replace('-', '')
        char_map = level_json.get('CharacterSaveParameterMap', {}).get('value', [])
        uid_level_map = {}
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if not sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                key = entry.get('key', {})
                uid_obj = key.get('PlayerUId', {})
                uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
                if uid:
                    uid_clean = uid.lower().replace('-', '')
                    level = extract_value(sp_val, 'Level', 1)
                    uid_level_map[uid_clean] = int(level) if level is not None else 1
            except Exception:
                continue
        return uid_level_map.get(player_uid_clean, 1)
    except Exception:
        return 1
def get_player_pals_count_from_cspm(level_json, player_uid):
    try:
        player_uid_clean = str(player_uid).lower().replace('-', '')
        char_map = level_json.get('CharacterSaveParameterMap', {}).get('value', [])
        ownership = ContainerOwnership.build(char_map, level_json.get('CharacterContainerSaveData', {}).get('value', []))
        pal_count = 0
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                inst_val = entry.get('key', {}).get('InstanceId', {}).get('value')
                owner_uid_obj = sp_val.get('OwnerPlayerUId', {})
                owner_uid = str(owner_uid_obj.get('value', '') if isinstance(owner_uid_obj, dict) else owner_uid_obj) if owner_uid_obj else ''
                if ownership.get_effective_owner(inst_val, owner_uid) == player_uid_clean:
                    pal_count += 1
            except Exception:
                continue
        return pal_count
    except Exception:
        return 0
level_sav_path, t_level_sav_path = (None, None)
level_json, host_json, targ_lvl, targ_json = (None, None, None, None)
target_gvas_file, targ_json_gvas = (None, None)
source_is_post_v1 = None
target_is_post_v1 = None
selected_source_player, selected_target_player = (None, None)
source_guild_dict, target_guild_dict = (dict(), dict())
source_world_tick, target_world_tick = (0, 0)
def safe_uuid_str(u):
    if isinstance(u, str):
        return u
    if hasattr(u, 'hex'):
        return str(u)
    from uuid import UUID
    if isinstance(u, bytes) and len(u) == 16:
        return str(UUID(bytes=u))
    return str(u)
def as_uuid(val):
    return str(val).lower() if val else ''
def are_equal_uuids(a, b):
    return as_uuid(a) == as_uuid(b)
def fast_deepcopy(obj):
    return pickle.loads(pickle.dumps(obj, -1))
def _is_post_v1_save(wsd):
    try:
        for c in wsd.get('CharacterSaveParameterMap', {}).get('value', []):
            sp = c['value']['RawData']['value']['object']['SaveParameter']
            if sp['value'].get('IsPlayer', {}).get('value', False):
                return 'ExpTableMigrationVersion' in sp['value']
        return 'BossSpawnerSaveData' in wsd
    except:
        return False
_PRE_ONLY_SP_FIELDS = {'SanityValue'}
_POST_ONLY_SP_FIELDS = {'ExpTableMigrationVersion', 'bApplyShieldDamage'}
def _normalize_save_parameter(sp_value, from_pre_to_post):
    if from_pre_to_post:
        for field in _PRE_ONLY_SP_FIELDS:
            sp_value.pop(field, None)
        if 'ExpTableMigrationVersion' not in sp_value:
            sp_value['ExpTableMigrationVersion'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
        if 'bApplyShieldDamage' not in sp_value:
            sp_value['bApplyShieldDamage'] = {'id': None, 'value': False, 'type': 'BoolProperty'}
    else:
        for field in _POST_ONLY_SP_FIELDS:
            sp_value.pop(field, None)
        if 'SanityValue' not in sp_value:
            sp_value['SanityValue'] = {'id': None, 'value': 100.0, 'type': 'FloatProperty'}
_PRE_TO_POST_PLAYER_FIELDS = {'CompletedQuestArray': 'CompletedQuestArray_FullRelease', 'OrderedQuestArray': 'OrderedQuestArray_FullRelease'}
_POST_TO_PRE_PLAYER_FIELDS = {v: k for k, v in _PRE_TO_POST_PLAYER_FIELDS.items()}
_PRE_ONLY_PLAYER_FIELDS = {'OtomoOrder', 'bIsSelectedInitMapPoint'}
_POST_ONLY_PLAYER_FIELDS = {'LastOnlineDateTime', 'PlayerPlatform'}
def _normalize_player_save_data(save_data, from_pre_to_post):
    if from_pre_to_post:
        rename_map, strip_set, defaults = (_PRE_TO_POST_PLAYER_FIELDS, _PRE_ONLY_PLAYER_FIELDS, {'LastOnlineDateTime': 0, 'PlayerPlatform': 'Steam'})
    else:
        rename_map, strip_set, defaults = (_POST_TO_PRE_PLAYER_FIELDS, _POST_ONLY_PLAYER_FIELDS, {})
    for old_key, new_key in rename_map.items():
        if old_key in save_data:
            save_data[new_key] = save_data.pop(old_key)
    for field in strip_set:
        save_data.pop(field, None)
    for field, default in defaults.items():
        if field not in save_data:
            save_data[field] = {'id': None, 'value': default, 'type': 'IntProperty' if isinstance(default, int) else 'StrProperty'}
_PRE_ONLY_LEVEL_FIELDS = {'FixedWeaponDestroySaveData'}
_POST_ONLY_LEVEL_FIELDS = {'BossSpawnerSaveData'}
def _normalize_level_data(wsd, from_pre_to_post):
    if from_pre_to_post:
        for field in _PRE_ONLY_LEVEL_FIELDS:
            wsd.pop(field, None)
        for field in _POST_ONLY_LEVEL_FIELDS:
            if field not in wsd:
                wsd[field] = {'value': []}
    else:
        for field in _POST_ONLY_LEVEL_FIELDS:
            wsd.pop(field, None)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen.center())
    win.move(geo.topLeft())
class CharacterTransferWindow(QWidget):
    message_signal = Signal(str, str)
    def __init__(self):
        super().__init__()
        self.setObjectName('central')
        self.source_player_list = None
        self.target_player_list = None
        self.source_level_path_label = None
        self.target_level_path_label = None
        self.current_selection_label = None
        self.source_search_entry = None
        self.target_search_entry = None
        self.message_signal.connect(self.show_message)
        self.setup_ui()
        global source_player_list, target_player_list, source_level_path_label, target_level_path_label, current_selection_label
        source_player_list = self.source_player_list
        target_player_list = self.target_player_list
        source_level_path_label = self.source_level_path_label
        target_level_path_label = self.target_level_path_label
        current_selection_label = self.current_selection_label
    def closeEvent(self, event):
        global level_json, host_json, targ_lvl, targ_json
        global target_gvas_file, targ_json_gvas, player_list_cache
        global modified_target_players, modified_targets_data
        level_json = None
        host_json = None
        targ_lvl = None
        targ_json = None
        target_gvas_file = None
        targ_json_gvas = None
        modified_target_players = set()
        modified_targets_data = {}
        import gc
        gc.collect()
        event.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    def setup_ui(self):
        self.setWindowTitle(t('tool.character_transfer'))
        self.setFixedSize(1200, 640)
        self.load_styles()
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass_frame = QFrame()
        glass_frame.setObjectName('glass')
        glass_layout = QVBoxLayout(glass_frame)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        src_btn = QPushButton(f"{t('Select Source Level File')}")
        src_btn.setToolTip(t('character_transfer.source_tooltip'))
        src_btn.clicked.connect(self.source_level_file)
        file_row.addWidget(src_btn)
        tgt_btn = QPushButton(f"{t('Select Target Level File')}")
        tgt_btn.setToolTip(t('character_transfer.target_tooltip'))
        tgt_btn.clicked.connect(self.target_level_file)
        file_row.addWidget(tgt_btn)
        glass_layout.addLayout(file_row)
        paths_row = QHBoxLayout()
        self.source_level_path_label = QLabel(t('character_transfer.no_source_selected'))
        self.source_level_path_label.setWordWrap(True)
        self.source_level_path_label.setMinimumWidth(480)
        paths_row.addWidget(self.source_level_path_label)
        self.target_level_path_label = QLabel(t('character_transfer.no_target_selected'))
        self.target_level_path_label.setWordWrap(True)
        self.target_level_path_label.setMinimumWidth(480)
        paths_row.addWidget(self.target_level_path_label)
        glass_layout.addLayout(paths_row)
        trees_layout = QHBoxLayout()
        trees_layout.setSpacing(14)
        source_panel = QFrame()
        source_panel.setStyleSheet('QFrame { background-color: transparent; }')
        source_panel_layout = QVBoxLayout(source_panel)
        source_panel_layout.setContentsMargins(6, 6, 6, 6)
        source_panel_layout.setSpacing(8)
        source_title = QLabel(t('character_transfer.source_players'))
        source_title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        source_title.setAlignment(Qt.AlignCenter)
        source_panel_layout.addWidget(source_title)
        self.source_search_entry = QLineEdit()
        self.source_search_entry.setPlaceholderText(t('character_transfer.search_source_players'))
        self.source_search_entry.textChanged.connect(lambda txt: self.filter_treeview(self.source_player_list, txt, True))
        source_panel_layout.addWidget(self.source_search_entry)
        self.source_player_list = QTreeWidget()
        self.source_player_list.setHeaderLabels([t('Guild ID'), t('GUID'), t('Name'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.source_player_list.itemSelectionChanged.connect(self.on_selection_of_source_player)
        self.source_player_list.setSortingEnabled(True)
        src_header = self.source_player_list.header()
        src_header.setSectionResizeMode(0, QHeaderView.Stretch)
        src_header.setSectionResizeMode(1, QHeaderView.Stretch)
        src_header.setSectionResizeMode(2, QHeaderView.Stretch)
        src_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        src_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        src_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        source_panel_layout.addWidget(self.source_player_list, 1)
        trees_layout.addWidget(source_panel, 1)
        target_panel = QFrame()
        target_panel.setStyleSheet('QFrame { background-color: transparent; }')
        target_panel_layout = QVBoxLayout(target_panel)
        target_panel_layout.setContentsMargins(6, 6, 6, 6)
        target_panel_layout.setSpacing(8)
        target_title = QLabel(t('character_transfer.target_players'))
        target_title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        target_title.setAlignment(Qt.AlignCenter)
        target_panel_layout.addWidget(target_title)
        self.target_search_entry = QLineEdit()
        self.target_search_entry.setPlaceholderText(t('character_transfer.search_target_players'))
        self.target_search_entry.textChanged.connect(lambda txt: self.filter_treeview(self.target_player_list, txt, False))
        target_panel_layout.addWidget(self.target_search_entry)
        self.target_player_list = QTreeWidget()
        self.target_player_list.setHeaderLabels([t('Guild ID'), t('GUID'), t('Name'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.target_player_list.itemSelectionChanged.connect(self.on_selection_of_target_player)
        self.target_player_list.setSortingEnabled(True)
        tgt_header = self.target_player_list.header()
        tgt_header.setSectionResizeMode(0, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(1, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(2, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tgt_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tgt_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        target_panel_layout.addWidget(self.target_player_list, 1)
        trees_layout.addWidget(target_panel, 1)
        glass_layout.addLayout(trees_layout)
        self.current_selection_label = QLabel(t('character_transfer.selection_none'))
        self.current_selection_label.setWordWrap(True)
        self.current_selection_label.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(self.current_selection_label)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)
        transfer_all_btn = QPushButton(t('Transfer All'))
        transfer_all_btn.setToolTip(t('character_transfer.transfer_all_tooltip'))
        transfer_all_btn.clicked.connect(self.transfer_all_characters)
        actions_row.addWidget(transfer_all_btn)
        transfer_btn = QPushButton(t('Transfer'))
        transfer_btn.setToolTip(t('character_transfer.transfer_tooltip'))
        transfer_btn.clicked.connect(lambda: self.main(skip_msgbox=False))
        actions_row.addWidget(transfer_btn)
        save_btn = QPushButton(t('Save Changes'))
        save_btn.setToolTip(t('character_transfer.save_tooltip'))
        save_btn.clicked.connect(self.finalize_save)
        actions_row.addWidget(save_btn)
        glass_layout.addLayout(actions_row)
        tip_label = QLabel(t('character_transfer.tip'))
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setFont(QFont('Segoe UI', 9))
        glass_layout.addWidget(tip_label)
        warning_label = QLabel(t('warning.world_id'))
        warning_label.setFont(QFont('Segoe UI', 9))
        warning_label.setStyleSheet('color: #ffaa00;')
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setWordWrap(True)
        glass_layout.addWidget(warning_label)
        main_layout.addWidget(glass_frame)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
    def load_styles(self):
        ThemeManager.load_styles(self)
    def filter_treeview(self, tree, query, is_source):
        query = query.lower()
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            visible = any((query in item.text(col).lower() for col in range(item.columnCount())))
            item.setHidden(not visible)
    def source_level_file(self):
        try:
            source_level_file()
        except Exception as e:
            print(f'GUI: Error calling source_level_file: {e}')
    def target_level_file(self):
        try:
            target_level_file()
        except Exception as e:
            print(f'GUI: Error calling target_level_file: {e}')
    def on_selection_of_source_player(self):
        try:
            on_selection_of_source_player()
        except Exception:
            selected_items = self.source_player_list.selectedItems()
            global selected_source_player
            if selected_items:
                selected_source_player = selected_items[0].text(1)
            else:
                selected_source_player = None
            self.current_selection_label.setText(t('character_transfer.selection_status', source=selected_source_player or 'N/A', target=selected_target_player or 'N/A'))
    def on_selection_of_target_player(self):
        try:
            on_selection_of_target_player()
        except Exception:
            selected_items = self.target_player_list.selectedItems()
            global selected_target_player
            if selected_items:
                selected_target_player = selected_items[0].text(1)
            else:
                selected_target_player = None
            self.current_selection_label.setText(t('character_transfer.selection_status', source=selected_source_player or 'N/A', target=selected_target_player or 'N/A'))
    def transfer_all_characters(self):
        try:
            transfer_all_characters()
        except Exception as e:
            print(f'GUI wrapper transfer_all_characters error: {e}')
    def main(self, skip_msgbox=False):
        try:
            return main(skip_msgbox=skip_msgbox)
        except Exception as e:
            print(f'GUI wrapper main error: {e}')
            return False
    def show_message(self, title, message):
        show_information(None, title, message)
    def finalize_save(self):
        try:
            finalize_save(self)
        except Exception as e:
            print(f'GUI finalize_save error: {e}')
def load_json_files():
    global host_json_gvas, targ_json_gvas, host_json, targ_json
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas:
        return False
    host_json = host_json_gvas.properties
    target_uid = selected_target_player or selected_source_player
    targ_json_gvas = load_player_file(t_level_sav_path, target_uid)
    if not targ_json_gvas:
        return False
    targ_json = targ_json_gvas.properties
    return True
def gather_inventory_ids(json_data):
    inv_info = json_data['SaveData']['value']['InventoryInfo']['value']
    return {'main': inv_info['CommonContainerId']['value']['ID']['value'], 'key': inv_info['EssentialContainerId']['value']['ID']['value'], 'weps': inv_info['WeaponLoadOutContainerId']['value']['ID']['value'], 'armor': inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'], 'foodbag': inv_info['FoodEquipContainerId']['value']['ID']['value'], 'pals': json_data['SaveData']['value']['PalStorageContainerId']['value']['ID']['value'], 'otomo': json_data['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']}
modified_target_players = set()
modified_targets_data = {}
def transfer_all_characters():
    def worker():
        import time
        global selected_source_player, selected_target_player, host_guid, targ_uid, host_json, host_json_gvas, targ_json, targ_json_gvas
        total_players = source_player_list.topLevelItemCount()
        print(f'Starting bulk transfer for {total_players} players...')
        total_start = time.perf_counter()
        if source_is_post_v1 is not None and target_is_post_v1 is not None and (source_is_post_v1 != target_is_post_v1):
            _normalize_level_data(targ_lvl, target_is_post_v1)
        for i in range(total_players):
            player_start = time.perf_counter()
            item = source_player_list.topLevelItem(i)
            player_uuid = item.text(1)
            if player_uuid in modified_target_players:
                continue
            selected_source_player = player_uuid
            selected_target_player = player_uuid
            try:
                host_guid = UUID.from_str(selected_source_player)
                targ_uid = UUID.from_str(selected_target_player)
            except Exception as e:
                print(f'UUID Error for {player_uuid}: {e}')
                continue
            host_json_gvas = None
            host_json_gvas = load_player_file(level_sav_path, selected_source_player)
            if not host_json_gvas:
                continue
            player_level = get_player_level_from_cspm(level_json, selected_source_player)
            if player_level < 2:
                print(f'[SKIP] {player_uuid} - Player level {player_level} < 2 (not leveled up)')
                continue
            host_json = host_json_gvas.properties
            try:
                targ_json_gvas = load_player_file(t_level_sav_path, selected_target_player)
                if targ_json_gvas is None:
                    targ_json_gvas = fast_deepcopy(host_json_gvas)
            except:
                targ_json_gvas = fast_deepcopy(host_json_gvas)
            targ_json = targ_json_gvas.properties
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['character']:
                transfer_character_only(host_guid, targ_uid)
            t_char = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['tech_data']:
                transfer_tech_and_data()
            t_tech = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['inventory']:
                transfer_inventory_only()
            t_inv = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['guild']:
                transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict)
            t_guild = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['pals']:
                transfer_pals_only()
            t_pals = time.perf_counter() - t0
            if _TRANSFER_STEPS['timestamps']:
                sync_player_timestamps(targ_uid, targ_lvl)
            modified_target_players.add(selected_target_player)
            modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas, selected_source_player)
            print(f'[{i + 1}/{total_players}]{player_uuid} | Char: {t_char:.3f}s | Inv: {t_inv:.3f}s | Pals: {t_pals:.3f}s | Total: {time.perf_counter() - player_start:.3f}s')
        if _TRANSFER_STEPS['dynamics']:
            gather_and_update_dynamic_containers()
        print(f'Bulk transfer completed in {time.perf_counter() - total_start:.2f}s.')
    def on_bulk_finished():
        load_players(targ_lvl, is_source=False)
        global selected_source_player, selected_target_player, host_guid, targ_uid, exported_map
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        current_selection_label.setText('Source: None,Target: None')
        source_player_list.clearSelection()
        target_player_list.clearSelection()
        show_information(None, t('Transfer Successful'), t('All players transferred!'))
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    on_bulk_finished()
def main(skip_msgbox=False, skip_gui=False):
    global host_guid, targ_uid, exported_map, selected_source_player, selected_target_player
    if not all([level_sav_path, t_level_sav_path, selected_source_player]):
        print('Error! Please have level files and source player selected before starting transfer.')
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    if not selected_target_player:
        selected_target_player = selected_source_player
    if selected_target_player in modified_target_players:
        print(f'Player {selected_target_player} already transferred.Skipping duplicate transfer.')
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player)
    except Exception as e:
        print(f'UUID Error: Invalid UUID format: {e}')
        return
    if not load_json_files():
        print('Load Error: Failed to load JSON files.')
        return
    source_player_level = get_player_level_from_cspm(level_json, selected_source_player)
    if source_player_level < 2:
        print(f'Error: Source player must be at least level 2. Current level: {source_player_level}')
        error_msg = t('character_transfer.source_player_level_2', level=source_player_level) if source_player_level > 0 else t('character_transfer.source_player_not_leveled')
        show_warning(None, t('Error!'), error_msg)
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    if selected_target_player and selected_target_player != selected_source_player:
        target_player_level = get_player_level_from_cspm(targ_lvl, selected_target_player)
        if target_player_level < 2:
            print(f'Error: Target player must be at least level 2. Current level: {target_player_level}')
            error_msg = t('character_transfer.target_player_level_2', level=target_player_level) if target_player_level > 0 else t('character_transfer.target_player_not_leveled')
            show_warning(None, t('Error!'), error_msg)
            selected_source_player = None
            selected_target_player = None
            host_guid = None
            targ_uid = None
            exported_map = None
            if not skip_gui:
                current_selection_label.setText('Source: None,Target: None')
                source_player_list.clearSelection()
                target_player_list.clearSelection()
            return False
    src_players_folder = os.path.join(os.path.dirname(level_sav_path), 'Players')
    tgt_players_folder = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
    os.makedirs(tgt_players_folder, exist_ok=True)
    if source_is_post_v1 is not None and target_is_post_v1 is not None and (source_is_post_v1 != target_is_post_v1):
        _normalize_level_data(targ_lvl, target_is_post_v1)
    if _TRANSFER_STEPS['character']:
        if not transfer_character_only(host_guid, targ_uid):
            print('[FAIL]Character + containers')
            return
        print('[SUCCESS]Character + containers')
    if _TRANSFER_STEPS['tech_data']:
        if not transfer_tech_and_data():
            print('[FAIL]Tech + data')
            return
        print('[SUCCESS]Tech + data')
    if _TRANSFER_STEPS['inventory']:
        if not transfer_inventory_only():
            print('[FAIL]Inventory')
            return
        print('[SUCCESS]Inventory')
    if _TRANSFER_STEPS['guild']:
        if not transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict):
            print('[FAIL]Guild transfer')
            return
        print('[SUCCESS]Guild transfer')
    if _TRANSFER_STEPS['pals']:
        if not transfer_pals_only():
            print('[FAIL]Pals')
            return
        print('[SUCCESS]Pals')
    if _TRANSFER_STEPS['dynamics']:
        gather_and_update_dynamic_containers()
    if _TRANSFER_STEPS['timestamps']:
        sync_player_timestamps(targ_uid, targ_lvl)
    modified_target_players.add(selected_target_player)
    modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas, selected_source_player)
    if not skip_gui:
        load_players(targ_lvl, is_source=False)
    selected_source_player = None
    selected_target_player = None
    host_guid = None
    targ_uid = None
    exported_map = None
    if not skip_gui:
        current_selection_label.setText('Source: None,Target: None')
        source_player_list.clearSelection()
        target_player_list.clearSelection()
    if not skip_msgbox:
        show_information(None, t('Transfer Successful'), t("Transfer successful in memory! Hit 'Save Changes' to save."))
def _normalize_lid(lid):
    if hasattr(lid, 'raw_bytes'):
        s = str(lid).lower()
        return '' if s.replace('-', '') == '00000000000000000000000000000000' else s
    if isinstance(lid, bytes):
        if lid == b'\x00' * 16:
            return ''
        from uuid import UUID
        try:
            return str(UUID(bytes=lid)).lower()
        except:
            return lid.hex().lower()
    if isinstance(lid, str):
        stripped = lid.replace('-', '').lower()
        return '' if stripped == '00000000000000000000000000000000' else lid.lower()
    return ''
def _bump_guid_str(s, used):
    t = str.maketrans('0123456789abcdef', '123456789abcdef0')
    bumped = s.translate(t)
    while bumped in used:
        bumped = bumped.translate(t)
    used.add(bumped)
    return bumped
def _collect_container_ids(player_json):
    try:
        ii = player_json['SaveData']['value']['InventoryInfo']['value']
        return {ii['CommonContainerId']['value']['ID']['value'], ii['EssentialContainerId']['value']['ID']['value'], ii['WeaponLoadOutContainerId']['value']['ID']['value'], ii['PlayerEquipArmorContainerId']['value']['ID']['value'], ii['FoodEquipContainerId']['value']['ID']['value']}
    except:
        return set()
def _collect_dynamic_ids(container, needed_set):
    for slot in container.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
        try:
            item = slot.get('RawData', {}).get('value', {}).get('item', {})
            if not isinstance(item, dict):
                continue
            dyn_id = item.get('dynamic_id', {})
            if not isinstance(dyn_id, dict):
                continue
            lid = dyn_id.get('local_id_in_created_world', '')
            norm = _normalize_lid(lid)
            if norm:
                needed_set.add(norm)
        except:
            continue

_session_transferred_dynamics = set()
_session_id_map = {}

def gather_and_update_dynamic_containers():
    global targ_lvl, dynamic_guids
    from palworld_save_tools.archive import UUID as PalUUID
    src_container_ids = _collect_container_ids(host_json)
    tgt_container_ids = _collect_container_ids(targ_json)
    src_char_ids = set()
    tgt_char_ids = set()
    if host_json and 'SaveData' in host_json:
        hsd = host_json['SaveData']['value']
        src_char_ids.add(hsd['PalStorageContainerId']['value']['ID']['value'])
        src_char_ids.add(hsd['OtomoCharacterContainerId']['value']['ID']['value'])
    if targ_json and 'SaveData' in targ_json:
        tsd = targ_json['SaveData']['value']
        tgt_char_ids.add(tsd['PalStorageContainerId']['value']['ID']['value'])
        tgt_char_ids.add(tsd['OtomoCharacterContainerId']['value']['ID']['value'])
    for _, (pj, _, _) in modified_targets_data.items():
        ids = _collect_container_ids(pj)
        src_container_ids |= ids
        tgt_container_ids |= ids
    for _, (pj, _, _) in modified_targets_data.items():
        pj_sd = pj['SaveData']['value']
        cids = {pj_sd['PalStorageContainerId']['value']['ID']['value'], pj_sd['OtomoCharacterContainerId']['value']['ID']['value']}
        src_char_ids |= cids
        tgt_char_ids |= cids
    all_needed_ids = src_container_ids | src_char_ids | tgt_container_ids | tgt_char_ids
    needed = set()
    for container_type in ['ItemContainerSaveData', 'CharacterContainerSaveData']:
        for c in level_json.get(container_type, {}).get('value', []):
            try:
                if c['key']['ID']['value'] not in all_needed_ids:
                    continue
            except:
                continue
            _collect_dynamic_ids(c, needed)
        for c in targ_lvl.get(container_type, {}).get('value', []):
            try:
                if c['key']['ID']['value'] not in all_needed_ids:
                    continue
            except:
                continue
            _collect_dynamic_ids(c, needed)
    src_containers = level_json['DynamicItemSaveData']['value']['values']
    tgt_containers = targ_lvl['DynamicItemSaveData']['value']['values']
    dynamic_guids = set()
    existing = set()
    tgt_dict = {}
    existing = set()
    for dc in tgt_containers:
        try:
            norm = _normalize_lid(dc['RawData']['value']['id']['local_id_in_created_world'])
            if norm:
                existing.add(norm)
        except:
            continue
    id_map = dict(_session_id_map)
    for dc in src_containers:
        try:
            lid = dc['RawData']['value']['id']['local_id_in_created_world']
            if isinstance(lid, bytes) and lid == b'\x00' * 16:
                continue
            norm = _normalize_lid(lid)
            if not norm or norm not in needed:
                continue
        except:
            continue
        if norm in _session_transferred_dynamics:
            continue
        bumped = _bump_guid_str(norm, existing)
        copy = fast_deepcopy(dc)
        copy['RawData']['value']['id']['local_id_in_created_world'] = PalUUID.from_str(bumped)
        dynamic_guids.add(lid)
        tgt_dict[bumped] = copy
        id_map[norm] = bumped
        _session_transferred_dynamics.add(norm)
        _session_id_map[norm] = bumped
    preserved_map = {}
    for dc in tgt_containers:
        try:
            lid = dc['RawData']['value']['id']['local_id_in_created_world']
            norm = _normalize_lid(lid)
            if norm and norm not in needed:
                preserved_map[norm] = dc
        except:
            continue
    tgt_dict.update(preserved_map)
    all_container_ids = src_container_ids | tgt_container_ids | src_char_ids | tgt_char_ids
    remap_count = 0
    for container_type in ['ItemContainerSaveData', 'CharacterContainerSaveData']:
        for c in targ_lvl.get(container_type, {}).get('value', []):
            try:
                if c['key']['ID']['value'] not in all_container_ids:
                    continue
            except:
                continue
            for slot in c.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
                try:
                    raw = slot.get('RawData', {})
                    if not isinstance(raw, dict):
                        continue
                    val = raw.get('value', {})
                    if not isinstance(val, dict):
                        continue
                    if 'item' not in val:
                        continue
                    item = val.get('item', {})
                    if not isinstance(item, dict):
                        continue
                    dyn_id = item.get('dynamic_id', {})
                    if not isinstance(dyn_id, dict) or not dyn_id:
                        continue
                    lid = dyn_id.get('local_id_in_created_world', '')
                    norm = _normalize_lid(lid)
                    if not norm:
                        continue
                    if norm in id_map:
                        dyn_id['local_id_in_created_world'] = PalUUID.from_str(id_map[norm])
                        remap_count += 1
                except:
                    continue
    if remap_count:
        print(f'[DYNAMICS] Remapped: {remap_count}')
    targ_lvl['DynamicItemSaveData']['value']['values'] = list(tgt_dict.values())
def sync_player_timestamps(targ_uid, target_lvl):
    global target_world_tick
    try:
        if not target_world_tick:
            return False
        t_uid_str = str(targ_uid).lower()
        if 'CharacterSaveParameterMap' in target_lvl:
            for char in target_lvl['CharacterSaveParameterMap']['value']:
                if str(char['key']['PlayerUId']['value']).lower() == t_uid_str:
                    raw = char['value']['RawData']['value']
                    raw['last_online_real_time'] = target_world_tick
                    if 'object' in raw and 'SaveParameter' in raw['object']:
                        params = raw['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime' in params:
                            params['LastOnlineRealTime']['value'] = target_world_tick
        if 'GroupSaveDataMap' in target_lvl:
            for gdata in target_lvl['GroupSaveDataMap']['value']:
                try:
                    raw_g = gdata['value']['RawData']['value']
                    for p_info in raw_g.get('players', []):
                        if str(p_info.get('player_uid')).lower() == t_uid_str:
                            if 'player_info' in p_info:
                                p_info['player_info']['last_online_real_time'] = target_world_tick
                except:
                    continue
        return True
    except:
        return False
from palworld_save_tools.archive import UUID as PalUUID
from palworld_save_tools.archive import FArchiveWriter
def _new_guid():
    return PalUUID(os.urandom(16))
def _rebuild_opaque_bytes(raw):
    try:
        from palworld_save_tools.archive import FArchiveReader
        opaque = bytes(raw['_opaque_all_remaining_bytes'])
        v1 = raw.get('_v1_header')
        if v1:
            opaque = opaque[len(v1):]
        r = FArchiveReader(opaque, debug=False)
        nw = FArchiveWriter()
        if opaque[:4] == b'\x00\x00\x00\x00':
            nw.write(r.read(4))
        nw.guid(raw['admin_player_uid'])
        nw.write(r.read(4 + 4 + 2 + 4 + 4 + 4 + 4))
        r.i32()
        players = raw.get('players', [])
        nw.i32(len(players))
        for p in players:
            nw.i64(p['player_info']['last_online_real_time'])
            nw.fstring(p['player_info']['player_name'])
            nw.write(b'\x00' * 31)
        nw.write(r.read_to_end())
        raw['_opaque_all_remaining_bytes'] = [int(b) for b in nw.bytes()]
    except Exception as e:
        print(f'_rebuild_opaque_bytes error: {e}')
def _set_player_groupid(targ_json, group_id):
    sd = targ_json['SaveData']['value']
    sd['GroupId'] = {
        'id': None,
        'value': group_id,
        'type': 'StructProperty',
        'struct_type': 'Guid',
        'struct_id': '00000000-0000-0000-0000-000000000000'
    }
def transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict, target_world_tick=None):
    try:
        if 'GroupSaveDataMap' not in targ_lvl or targ_lvl['GroupSaveDataMap'].get('value') is None:
            return False
        guilds = targ_lvl['GroupSaveDataMap']['value']
        if not source_guild_dict:
            return False
        target_guild = None
        for g in guilds:
            raw = g.get('value', {}).get('RawData', {}).get('value', {})
            if any((str(p.get('player_uid')) == str(targ_uid) for p in raw.get('players', []))):
                target_guild = g
                break
        source_player = None
        source_entry = None
        for g in source_guild_dict.values():
            raw = g.get('value', {}).get('RawData', {}).get('value', {})
            for p in raw.get('players', []):
                if p.get('player_uid') == host_guid:
                    source_player = fast_deepcopy(p)
                    source_entry = g
                    break
            if source_entry:
                break
        if source_entry is None:
            return False
        if source_player:
            source_player['player_uid'] = targ_uid
            if 'player_info' in source_player:
                source_player['player_info']['last_online_real_time'] = target_world_tick or 0
        if target_guild:
            target_raw = target_guild['value']['RawData']['value']
            target_raw['players'] = [p for p in target_raw.get('players', []) if str(p.get('player_uid')) != str(targ_uid)]
            if source_player:
                target_raw['players'].append(source_player)
            if str(target_raw.get('admin_player_uid')) == str(host_guid):
                target_raw['admin_player_uid'] = targ_uid
            if '_opaque_all_remaining_bytes' in target_raw:
                _rebuild_opaque_bytes(target_raw)
            _set_player_groupid(targ_json, target_raw.get('group_id'))
            return True
        print('[GUILD] CANNOT CREATE NEW GUILD DUE A BUG')
        return False
    except Exception as e:
        print(f'[GUILD ERROR] {e}')
        return False
def transfer_tech_and_data():
    try:
        src_sd = host_json['SaveData']['value']
        tgt_sd = targ_json['SaveData']['value']
        tech_keys = ['SkillMap', 'PlayerTechData', 'player_tech_data']
        for k in tech_keys:
            if k in src_sd:
                tgt_sd[k] = fast_deepcopy(src_sd[k])
        appearance_keys = ['PlayerCustomName', 'PlayerCustomNameCharacterName', 'PlayerCustomNameCharacterName2', 'PlayerCustomNameCharacterName3']
        for k in appearance_keys:
            if k in src_sd:
                tgt_sd[k] = fast_deepcopy(src_sd[k])
        for k in ['PlayerCharacterAppearanceData', 'PlayerCustomName', 'PlayerCustomNameCharacterName', 'PlayerCustomNameCharacterName2', 'PlayerCustomNameCharacterName3', 'PlayerInputAllowDieData', 'PlayerTechnologyData', 'PlayerTechnologyData2', 'TechnologyPoint', 'TechnologyPoint2', 'BossTechnologyPoint', 'AdditionalTechnologyPoint']:
            if k in src_sd:
                tgt_sd[k] = fast_deepcopy(src_sd[k])
        record_keys = ['PlayerCaptureRecordData', 'PlayerCaptureRecordData2', 'PlayerDefeatBossRecordData', 'PlayerDiscoverMapData', 'PlayerExploreMapData', 'PlayerExploreMapData2', 'PlayerMapPingData', 'PlayerDungeonData', 'PlayerDungeonData2', 'BuildObjectMapData', 'SkyPresetData', 'PlayerSpawnLocationData']
        for k in record_keys:
            if k in src_sd:
                tgt_sd[k] = fast_deepcopy(src_sd[k])
        if source_is_post_v1 is not None and target_is_post_v1 is not None and (source_is_post_v1 != target_is_post_v1):
            _normalize_player_save_data(tgt_sd, target_is_post_v1)
        return True
    except Exception as e:
        print(f'[FAIL] transfer_tech_and_data: {e}')
        return False
def transfer_character_only(host_guid, targ_uid):
    host_instance_id = host_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    exported_map = None
    for character_save_param in level_json['CharacterSaveParameterMap']['value']:
        try:
            uid = character_save_param['key']['PlayerUId']['value']
            inst = character_save_param['key']['InstanceId']['value']
            if uid == host_guid and inst == host_instance_id:
                exported_map = character_save_param
                break
        except:
            pass
    if not exported_map:
        print(f'[ERROR]Could not find exported_map for {host_guid}')
        return False
    targ_instance_id = targ_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    char_list = targ_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    updated = False
    for c in char_list:
        key = c.get('key', {})
        if key.get('PlayerUId', {}).get('value') == targ_uid:
            c['value'] = fast_deepcopy(exported_map['value'])
            c['key']['InstanceId']['value'] = targ_instance_id
            if source_is_post_v1 is not None and target_is_post_v1 is not None and (source_is_post_v1 != target_is_post_v1):
                _normalize_save_parameter(c['value']['RawData']['value']['object']['SaveParameter']['value'], target_is_post_v1)
            sp = c['value'].get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
            if 'OwnerPlayerUId' in sp:
                sp['OwnerPlayerUId']['value'] = targ_uid
            ind = sp.get('IndividualId', {}).get('value')
            if ind:
                ind['InstanceId']['value'] = targ_instance_id
                ind['PlayerUId']['value'] = targ_uid
            updated = True
            break
    if not updated:
        new_entry = fast_deepcopy(exported_map)
        new_entry['key']['PlayerUId']['value'] = targ_uid
        new_entry['key']['InstanceId']['value'] = targ_instance_id
        if source_is_post_v1 is not None and target_is_post_v1 is not None and (source_is_post_v1 != target_is_post_v1):
            _normalize_save_parameter(new_entry['value']['RawData']['value']['object']['SaveParameter']['value'], target_is_post_v1)
        sp = new_entry['value'].get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
        if 'OwnerPlayerUId' in sp:
            sp['OwnerPlayerUId']['value'] = targ_uid
        ind = sp.get('IndividualId', {}).get('value')
        if ind:
            ind['InstanceId']['value'] = targ_instance_id
            ind['PlayerUId']['value'] = targ_uid
        char_list.append(new_entry)
    targ_lvl.setdefault('CharacterContainerSaveData', {'value': []})
    targ_lvl.setdefault('ItemContainerSaveData', {'value': []})
    host_save = host_json['SaveData']['value']
    src_char_ids = {host_save['PalStorageContainerId']['value']['ID']['value'], host_save['OtomoCharacterContainerId']['value']['ID']['value']}
    inv_info = host_save['InventoryInfo']['value']
    src_item_ids = {inv_info['CommonContainerId']['value']['ID']['value'], inv_info['EssentialContainerId']['value']['ID']['value'], inv_info['WeaponLoadOutContainerId']['value']['ID']['value'], inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'], inv_info['FoodEquipContainerId']['value']['ID']['value']}
    for container_list, src_ids in (('CharacterContainerSaveData', src_char_ids), ('ItemContainerSaveData', src_item_ids)):
        existing_ids = {c.get('key', {}).get('ID', {}).get('value') for c in targ_lvl[container_list]['value']}
        for c in level_json.get(container_list, {}).get('value', []):
            cid = c['key']['ID']['value']
            if cid in src_ids and cid not in existing_ids:
                targ_lvl[container_list]['value'].append(fast_deepcopy(c))
    return True
def transfer_inventory_only():
    try:
        inv_src = gather_inventory_ids(host_json)
        inv_tgt = gather_inventory_ids(targ_json)
    except:
        return False
    inv_lookup_src = {v: k for k, v in inv_src.items()}
    inv_lookup_tgt = {v: k for k, v in inv_tgt.items()}
    containers_src = {}
    containers_tgt = {}
    for c in level_json.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in inv_lookup_src:
            containers_src[inv_lookup_src[cid]] = c
    for c in targ_lvl.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in inv_lookup_tgt:
            containers_tgt[inv_lookup_tgt[cid]] = c
    found_keys = set(containers_tgt.keys())
    for k in ['main', 'key', 'weps', 'armor', 'foodbag']:
        if k in containers_src and k not in containers_tgt:
            for sc in level_json.get('ItemContainerSaveData', {}).get('value', []):
                if sc['key']['ID']['value'] == inv_src[k]:
                    targ_lvl['ItemContainerSaveData']['value'].append(fast_deepcopy(sc))
                    containers_tgt[k] = targ_lvl['ItemContainerSaveData']['value'][-1]
                    break
        if k in containers_src and k in containers_tgt:
            containers_tgt[k]['value'] = fast_deepcopy(containers_src[k]['value'])
    return True
def transfer_pals_only():
    global host_guid, targ_uid
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player or selected_source_player)
    except:
        return False
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    used_ids = set()
    for ch in targ_lvl.get('CharacterSaveParameterMap', {}).get('value', []):
        used_ids.add(str(ch['key']['InstanceId']['value']))
    def bump_guid_str(s):
        v = str(s).lower()
        t = str.maketrans('0123456789abcdef', '123456789abcdef0')
        bumped = v.translate(t)
        while bumped in used_ids:
            bumped = bumped.translate(t)
        used_ids.add(bumped)
        return bumped
    targ_guild_id = zero
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        plist = raw.get('players', [])
        if any((str(p.get('player_uid')) == str(targ_uid) for p in plist)):
            targ_guild_id = raw.get('group_id', zero)
            break
    ownership = ContainerOwnership.build(level_json.get('CharacterSaveParameterMap', {}).get('value', []), level_json.get('CharacterContainerSaveData', {}).get('value', []))
    src_params = []
    id_map = {}
    for ch in level_json['CharacterSaveParameterMap']['value']:
        try:
            v = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            owner = v.get('OwnerPlayerUId')
            inst_id = ch['key']['InstanceId']['value']
            if not ownership.belongs_to_player(inst_id, owner, host_guid):
                continue
            old_inst = inst_id
            bumped = bump_guid_str(old_inst)
            new_inst = UUID.from_str(bumped)
            id_map[str(old_inst)] = new_inst
            cp = fast_deepcopy(ch)
            cp['key']['InstanceId']['value'] = new_inst
            cp_raw = cp['value']['RawData']['value']
            cp_raw['group_id'] = str(targ_guild_id)
            pv = cp_raw['object']['SaveParameter']['value']
            if 'OwnerPlayerUId' not in pv:
                pv['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': targ_uid, 'type': 'StructProperty'}
            else:
                pv['OwnerPlayerUId']['value'] = targ_uid
            for k in ['OldOwnerPlayerUIds', 'MapObjectConcreteInstanceIdAssignedToExpedition']:
                pv.pop(k, None)
            src_params.append(cp)
        except:
            continue
    try:
        s_pal_id = host_json['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        s_oto_id = host_json['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']
        t_pal_id = targ_json['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        t_oto_id = targ_json['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']
        ids_to_find = {s_pal_id, s_oto_id}
        src_containers = {c['key']['ID']['value']: c for c in level_json['CharacterContainerSaveData']['value'] if c['key']['ID']['value'] in ids_to_find}
        ids_to_find_targ = {t_pal_id, t_oto_id}
        targ_containers = {c['key']['ID']['value']: c for c in targ_lvl['CharacterContainerSaveData']['value'] if c['key']['ID']['value'] in ids_to_find_targ}
        src_pal, src_oto = (src_containers.get(s_pal_id), src_containers.get(s_oto_id))
        tgt_pal, tgt_oto = (targ_containers.get(t_pal_id), targ_containers.get(t_oto_id))
    except:
        return False
    if not all([src_pal, src_oto, tgt_pal, tgt_oto]):
        return False
    param_map_by_inst = {str(p['key']['InstanceId']['value']): p for p in src_params}
    def remap_slots(slots, new_cid):
        for idx, slot in enumerate(slots):
            raw = slot.get('RawData', {}).get('value', {})
            old = str(raw.get('instance_id', ''))
            if old in id_map:
                new_i = id_map[old]
                raw['instance_id'] = new_i
                p = param_map_by_inst.get(str(new_i))
                if p:
                    pv = p['value']['RawData']['value']['object']['SaveParameter']['value']
                    pv['SlotId']['value']['ContainerId']['value']['ID']['value'] = new_cid
                    pv['SlotId']['value']['SlotIndex']['value'] = slot.get('SlotIndex', {}).get('value', idx)
    new_box = fast_deepcopy(src_pal['value']['Slots']['value'].get('values', []))
    remap_slots(new_box, t_pal_id)
    tgt_pal['value']['Slots']['value']['values'] = new_box
    new_oto = fast_deepcopy(src_oto['value']['Slots']['value'].get('values', []))
    remap_slots(new_oto, t_oto_id)
    tgt_oto['value']['Slots']['value']['values'] = new_oto
    tgt_pal['value']['SlotNum']['value'] = src_pal['value']['SlotNum']['value']
    tgt_oto['value']['SlotNum']['value'] = src_oto['value']['SlotNum']['value']
    targ_uid_str = str(targ_uid)
    t_chars = targ_lvl['CharacterSaveParameterMap']['value']
    new_map = [ch for ch in t_chars if str(get_val_safe(ch).get('OwnerPlayerUId', {}).get('value')) != targ_uid_str]
    new_map += src_params
    targ_lvl['CharacterSaveParameterMap']['value'] = new_map
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        if raw.get('group_id') == targ_guild_id:
            handles = raw.get('individual_character_handle_ids', [])
            handles[:] = [h for h in handles if str(h.get('instance_id', '')) not in id_map]
            seen = {}
            unique_handles = []
            for h in handles:
                try:
                    inst = str(h['instance_id'])
                    if inst not in seen:
                        seen[inst] = True
                        unique_handles.append(h)
                except:
                    unique_handles.append(h)
            handles[:] = unique_handles
            for new_inst in id_map.values():
                handles.append({'guid': zero, 'instance_id': new_inst})
            break
    return True
def get_val_safe(p):
    try:
        return p['value']['RawData']['value']['object']['SaveParameter']['value']
    except:
        return {}
def finalize_save_task():
    errors = []
    try:
        _write_sav(target_gvas_file, t_level_sav_path)
    except Exception as e:
        errors.append(f'Level.sav: {e}')
    for target_uid, (json_data, gvas_obj, src_uid) in modified_targets_data.items():
        try:
            tgt_dir = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
            os.makedirs(tgt_dir, exist_ok=True)
            _write_sav(gvas_obj, os.path.join(tgt_dir, f'{target_uid.upper()}.sav'))
        except Exception as e:
            errors.append(f'Player {target_uid}: {e}')
    if errors:
        print(f"[ERROR] Save errors: {'; '.join(errors)}")
        return False
    return True
def select_file():
    return QFileDialog.getOpenFileName(None, 'Select Palworld Save File', '', 'Palworld Saves(*.sav *.json);;All Files(*)')[0]
def load_player_file(level_sav_path, player_uid, use_source_folder=False):
    base_folder = os.path.dirname(level_sav_path)
    if use_source_folder:
        base_folder = os.path.join(base_folder, 'Players')
    else:
        base_folder = os.path.join(base_folder, 'Players')
    player_file_path = os.path.join(base_folder, f'{player_uid.upper()}.sav')
    if not os.path.exists(player_file_path):
        player_file_path = os.path.join(os.path.dirname(level_sav_path), '../Players', f'{player_uid.upper()}.sav')
    if not os.path.exists(player_file_path):
        base_folder = os.path.normpath(os.path.join(os.path.dirname(level_sav_path), '..', 'Players'))
        player_file_path = os.path.join(base_folder, f'{player_uid.upper()}.sav')
    if not os.path.exists(player_file_path):
        global host_json_gvas
        if host_json_gvas is not None:
            clone = fast_deepcopy(host_json_gvas)
            clone.save_type = getattr(host_json_gvas, 'save_type', 50)
            sd = clone.properties['SaveData']['value']
            sd['PlayerUId']['value'] = player_uid
            sd['IndividualId']['value']['PlayerUId']['value'] = player_uid
            sd['IndividualId']['value']['InstanceId']['value'] = str(uuid.uuid4()).upper()
            if 'LastSaveDate' in sd:
                sd['LastSaveDate']['value'] = int(time.time() * 10000000)
            print(f'Synthesized player data for {player_uid} in memory')
            return clone
        print(f'Error!', f'Player file {player_file_path} not present.')
        return None
    if not os.path.exists(player_file_path):
        print(f'Error!', f'Invalid file {player_file_path}')
        return
    return _load_sav(player_file_path)
def load_players(save_json, is_source):
    guild_dict = source_guild_dict if is_source else target_guild_dict
    if guild_dict:
        guild_dict.clear()
    players = {}
    for group_data in save_json['GroupSaveDataMap']['value']:
        if group_data['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            rdv = group_data['value']['RawData']['value']
            if 'values' in rdv:
                continue
            group_id = rdv['group_id']
            players[group_id] = rdv['players']
            guild_dict[group_id] = group_data
    list_box = source_player_list if is_source else target_player_list
    list_box.clear()
    current_tick = source_world_tick if is_source else target_world_tick
    cspm_json = level_json if is_source else targ_lvl
    for guild_id, player_items in players.items():
        for player_item in player_items:
            playerUId = ''.join(safe_uuid_str(player_item['player_uid']).split('-')).upper()
            player_name = player_item.get('player_name', (player_item.get('player_info') or {}).get('player_name', ''))
            player_level = get_player_level_from_cspm(cspm_json, playerUId)
            player_pals_count = get_player_pals_count_from_cspm(cspm_json, playerUId)
            last_online_time = player_item.get('player_info', {}).get('last_online_real_time', 0)
            last_seen = format_last_seen(last_online_time, current_tick)
            item = QTreeWidgetItem([safe_uuid_str(guild_id), playerUId, player_name, str(player_level), str(player_pals_count), last_seen])
            list_box.addTopLevelItem(item)
def source_level_file():
    global level_sav_path, level_json, selected_source_player, _session_transferred_dynamics, _session_id_map
    _session_transferred_dynamics.clear()
    _session_id_map.clear()
    tmp = select_file()
    if not tmp:
        return
    if not tmp.endswith('Level.sav'):
        show_warning(None, t('Error!'), t('This is NOT Level.sav.Please select Level.sav file.'))
        return
    level_json = None
    import gc
    gc.collect()
    def task():
        global source_world_tick
        print('Now loading the data from Source Save...')
        gvas_file = _load_sav(tmp)
        wsd = gvas_file.properties['worldSaveData']['value']
        try:
            source_world_tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        except:
            source_world_tick = 0
        return (tmp, wsd)
    def on_finished(result):
        global level_sav_path, level_json, selected_source_player, source_is_post_v1
        if result is None:
            show_warning(None, t('Error!'), t('Invalid file,must be Level.sav!'))
            return
        path, wsd = result
        level_sav_path = path
        level_json = wsd
        source_is_post_v1 = _is_post_v1_save(wsd)
        source_level_path_label.setText(path)
        selected_source_player = None
        load_players(wsd, True)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
        print('Done loading the data from Source Save!')
        if source_is_post_v1 and target_is_post_v1 is not None and (not target_is_post_v1):
            show_warning(None, t('Warning'), t('character_transfer.post_to_pre_blocked'))
    run_with_loading(on_finished, task)
def target_level_file():
    global t_level_sav_path, targ_lvl, target_gvas_file, selected_target_player
    global modified_target_players, modified_targets_data, _session_transferred_dynamics, _session_id_map
    _session_transferred_dynamics.clear()
    _session_id_map.clear()
    tmp = select_file()
    if not tmp:
        return
    if not tmp.endswith('Level.sav'):
        show_warning(None, t('Error!'), t('This is NOT Level.sav.Please select Level.sav file.'))
        return
    targ_lvl = None
    target_gvas_file = None
    modified_target_players = set()
    modified_targets_data = {}
    import gc
    gc.collect()
    def task():
        global target_world_tick
        print('Now loading the data from Target Save...')
        gvas_file = _load_sav(tmp)
        wsd = gvas_file.properties['worldSaveData']['value']
        try:
            target_world_tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        except:
            target_world_tick = 0
        return (tmp, gvas_file, wsd)
    def on_finished(result):
        global t_level_sav_path, targ_lvl, target_gvas_file, selected_target_player, target_is_post_v1
        if result is None:
            show_warning(None, t('Error!'), t('Invalid file,must be Level.sav!'))
            return
        path, gvas_file, wsd = result
        t_level_sav_path = path
        target_gvas_file = gvas_file
        targ_lvl = wsd
        target_is_post_v1 = _is_post_v1_save(wsd)
        target_level_path_label.setText(path)
        backup_whole_directory(os.path.dirname(path), 'Backups/Character Transfer')
        selected_target_player = None
        load_players(wsd, False)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
        print('Done loading the data from Target Save!')
        if source_is_post_v1 is not None and source_is_post_v1 and (not target_is_post_v1):
            show_warning(None, t('Warning'), t('character_transfer.post_to_pre_blocked'))
    run_with_loading(on_finished, task)
def on_selection_of_source_player():
    global selected_source_player
    selections = source_player_list.selectedItems()
    if selections:
        selected_source_player = selections[0].text(1)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
def on_selection_of_target_player():
    global selected_target_player
    selections = target_player_list.selectedItems()
    if selections:
        selected_target_player = selections[0].text(1)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
def sort_treeview_column(treeview, col_index, reverse):
    data = [(treeview.set(child, col_index), child) for child in treeview.get_children('')]
    data.sort(reverse=reverse, key=lambda x: x[0])
    for index, (_, item) in enumerate(data):
        treeview.move(item, '', index)
    treeview.heading(col_index, command=lambda: sort_treeview_column(treeview, col_index, not reverse))
def filter_treeview(tree, query, is_source):
    query = query.lower()
    if is_source:
        if not hasattr(filter_treeview, 'source_original_rows'):
            filter_treeview.source_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.source_original_rows
    else:
        if not hasattr(filter_treeview, 'target_original_rows'):
            filter_treeview.target_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.target_original_rows
    for row in original_rows:
        tree.reattach(row, '', 'end')
    for row in tree.get_children():
        values = tree.item(row, 'values')
        if any((query in str(value).lower() for value in values)):
            tree.reattach(row, '', 'end')
        else:
            tree.detach(row)
def finalize_save(window):
    try:
        def on_finished(success):
            if success:
                show_information(None, t('Success'), t('Transfer complete and backup created!'))
                print('Done saving all modified target players!')
        run_with_loading(on_finished, finalize_save_task)
    except Exception as e:
        print(f'Exception in finalize_save: {e}')
def character_transfer():
    return CharacterTransferWindow()
if __name__ == '__main__':
    app = QApplication([])
    w = CharacterTransferWindow()
    w.show()
    sys.exit(app.exec())