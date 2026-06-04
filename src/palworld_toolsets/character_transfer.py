from import_libs import *
from loading_manager import show_information, show_warning
from PySide6.QtWidgets import QHeaderView, QWidget, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QApplication, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
import os
from palsav.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palsav.paltypes import PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES
from palsav.gvas import GvasFile
from palworld_aio.ui.styles import ThemeManager
from palworld_aio.container_ownership import ContainerOwnership
from palworld_aio.inventory_manager import PlayerInventory
from palworld_aio.edit_pals import _generate_pal_save_param
from palworld_aio import constants
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
        global _induction_mode, _induction_guild_choice, _selected_target_guild_id
        level_json = None
        host_json = None
        targ_lvl = None
        targ_json = None
        target_gvas_file = None
        targ_json_gvas = None
        modified_target_players = set()
        modified_targets_data = {}
        _induction_mode = False
        _induction_guild_choice = None
        _selected_target_guild_id = None
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
        self._induction_active = False
        self._target_player_header = ['Guild ID', 'GUID', 'Name', 'Level', 'Pals', 'Last Seen']
        self._target_guild_header = ['Guild Name', 'Guild ID', 'Members', 'Bases', '', '']
        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)
        transfer_all_btn = QPushButton(t('Transfer All'))
        transfer_all_btn.setToolTip(t('character_transfer.transfer_all_tooltip'))
        transfer_all_btn.clicked.connect(self.transfer_all_characters)
        actions_row.addWidget(transfer_all_btn)
        self.induct_btn = QPushButton('Induct Character')
        self.induct_btn.setToolTip('Induct source character as a NEW player into the target world')
        self.induct_btn.clicked.connect(self.do_induct)
        actions_row.addWidget(self.induct_btn)
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
            if self._induction_active:
                on_selection_of_target_guild()
            else:
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
    def do_induct(self):
        global selected_source_player, _induction_guild_choice, _selected_target_guild_id
        try:
            if not self._induction_active:
                if not targ_lvl:
                    show_warning(None, t('Error!'), 'Please load the Target Level.sav first.')
                    return
                self._induction_active = True
                self.induct_btn.setText('Confirm Induction')
                self.target_player_list.itemSelectionChanged.disconnect()
                self.target_player_list.itemSelectionChanged.connect(self.on_selection_of_target_player)
                self._switch_target_to_guilds()
                current_selection_label.setText('Select a target guild, then click "Confirm Induction" again.')
                return
            if not _induction_guild_choice:
                show_warning(None, t('Error!'), 'Please select a target guild or "Create New Solo Guild".')
                return
            result = induct_character(skip_msgbox=False)
            if result:
                self._induction_active = False
                self._switch_target_to_players()
                self.induct_btn.setText('Induct Character')
                selected_source_player = None
                _induction_guild_choice = None
                _selected_target_guild_id = None
                self.source_player_list.clearSelection()
                self.target_player_list.clearSelection()
                current_selection_label.setText('Source: None,Target: None')
            else:
                self._induction_active = False
                self._switch_target_to_players()
                self.induct_btn.setText('Induct Character')
                _induction_guild_choice = None
                _selected_target_guild_id = None
        except Exception as e:
            print(f'GUI do_induct error: {e}')
            self._induction_active = False
            self._switch_target_to_players()
            self.induct_btn.setText('Induct Character')
    def _switch_target_to_guilds(self):
        target_title = self.target_player_list.parent().findChild(QLabel)
        if target_title:
            target_title.setText('Target Guilds')
        self.target_search_entry.setPlaceholderText('Search target guilds...')
        self.target_player_list.setHeaderLabels(self._target_guild_header)
        self.target_player_list.clear()
        load_target_guilds_into_tree()
    def _switch_target_to_players(self):
        target_title = self.target_player_list.parent().findChild(QLabel)
        if target_title:
            target_title.setText(t('character_transfer.target_players'))
        self.target_search_entry.setPlaceholderText(t('character_transfer.search_target_players'))
        self.target_player_list.setHeaderLabels(self._target_player_header)
        self.target_player_list.clear()
        if targ_lvl:
            load_players(targ_lvl, is_source=False)
def load_json_files():
    global host_json_gvas, targ_json_gvas, host_json, targ_json
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas:
        return False
    host_json = host_json_gvas.properties
    target_uid = selected_target_player or selected_source_player
    targ_json_gvas = load_player_file(t_level_sav_path, target_uid)
    if not targ_json_gvas:
        print(f'Target player file for {target_uid} not found. Player does not exist in target world. Load the game once with this save, then run the transfer again.')
        return False
    targ_json = targ_json_gvas.properties
    return True
def gather_inventory_ids(json_data):
    inv_info = json_data['SaveData']['value']['InventoryInfo']['value']
    ids = {'main': inv_info['CommonContainerId']['value']['ID']['value'], 'key': inv_info['EssentialContainerId']['value']['ID']['value'], 'weps': inv_info['WeaponLoadOutContainerId']['value']['ID']['value'], 'armor': inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'], 'foodbag': inv_info['FoodEquipContainerId']['value']['ID']['value'], 'drop': inv_info.get('DropSlotContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'pals': json_data['SaveData']['value']['PalStorageContainerId']['value']['ID']['value'], 'otomo': json_data['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']}
    return {k: v for k, v in ids.items() if v}
def scan_source_inventory(host_json, level_json):
    inv_ids = gather_inventory_ids(host_json)
    inv_lookup = {v: k for k, v in inv_ids.items()}
    type_map = {'main': 'main', 'key': 'key', 'weps': 'weapons', 'armor': 'armor', 'foodbag': 'foodbag'}
    items = []
    for c in level_json.get('ItemContainerSaveData', {}).get('value', []):
        try:
            cid = c['key']['ID']['value']
            container_type = inv_lookup.get(cid)
            mapped = type_map.get(container_type)
            if not mapped:
                continue
            slots = c.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            for slot in slots:
                raw = slot.get('RawData', {}).get('value', {})
                item_data = raw.get('item', {})
                static_id = item_data.get('static_id', '')
                if not static_id:
                    continue
                count = raw.get('count', 0)
                slot_idx = raw.get('slot_index', 0)
                items.append({'container_type': mapped, 'item_id': static_id, 'count': count, 'slot_index': slot_idx})
        except:
            continue
    return items
def migrate_inventory_via_player_inventory(target_uid, items, t_level_sav_path, targ_lvl):
    old_level = getattr(constants, 'loaded_level_json', None)
    old_path = getattr(constants, 'current_save_path', None)
    try:
        constants.loaded_level_json = {'properties': {'worldSaveData': {'value': targ_lvl}}}
        constants.current_save_path = os.path.dirname(t_level_sav_path)
        inv = PlayerInventory(target_uid)
        if not inv.load():
            return False
        needed = {}
        for item in items:
            needed.setdefault(item['container_type'], []).append(item['slot_index'])
        for ctype, slots in needed.items():
            container = inv.get_container(ctype)
            if container and hasattr(container, '_standardized_container'):
                max_needed = max(slots) + 1
                if max_needed > container._standardized_container.max_slots:
                    container._standardized_container.expand_capacity(max_needed)
                    sd = container._standardized_container.container_data.get('value', {})
                    sn = sd.get('SlotNum', {})
                    if sn:
                        sn['value'] = max_needed
        for item in items:
            inv.add_item(item['container_type'], item['item_id'], item['count'], item['slot_index'])
        inv.save()
        return True
    finally:
        constants.loaded_level_json = old_level
        constants.current_save_path = old_path
def scan_source_pals(host_guid, level_json, host_json):
    host_sd = host_json['SaveData']['value']
    pal_ctr = host_sd['PalStorageContainerId']['value']['ID']['value']
    oto_ctr = host_sd['OtomoCharacterContainerId']['value']['ID']['value']
    pal_ctr_s = str(pal_ctr).lower()
    oto_ctr_s = str(oto_ctr).lower()
    ownership = ContainerOwnership.build(level_json.get('CharacterSaveParameterMap', {}).get('value', []), level_json.get('CharacterContainerSaveData', {}).get('value', []))
    pals = []
    for ch in level_json['CharacterSaveParameterMap']['value']:
        try:
            v = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            owner = v.get('OwnerPlayerUId')
            inst_id = ch['key']['InstanceId']['value']
            if not ownership.belongs_to_player(inst_id, owner, host_guid):
                continue
            slot_cid = v.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            slot_cid_s = str(slot_cid).lower() if slot_cid else ''
            slot_idx = v.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
            if slot_cid_s == pal_ctr_s:
                is_palbox = True
            elif slot_cid_s == oto_ctr_s:
                is_palbox = False
            else:
                continue
            group_id = ch.get('value', {}).get('RawData', {}).get('value', {}).get('group_id', '')
            pals.append({'source_entry': ch, 'save_parameter': v, 'instance_id': inst_id, 'is_palbox': is_palbox, 'slot_index': slot_idx, 'group_id': group_id})
        except:
            continue
    return pals
def migrate_pal_via_api(pal_data, target_uid, targ_lvl, target_player_json, target_guild_id):
    sd = target_player_json['SaveData']['value']
    pal_ctr = sd['PalStorageContainerId']['value']['ID']['value']
    oto_ctr = sd['OtomoCharacterContainerId']['value']['ID']['value']
    container_id = pal_ctr if pal_data['is_palbox'] else oto_ctr
    src_sp = pal_data['save_parameter']
    cid = extract_value(src_sp, 'CharacterID', '')
    nick = extract_value(src_sp, 'NickName', '')
    slot_idx = pal_data['slot_index']
    skeleton = _generate_pal_save_param(cid, nick, target_uid, container_id, slot_idx, target_guild_id)
    instance_id = skeleton['key']['InstanceId']['value']
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
    new_inst_str = bump_guid_str(instance_id)
    from palsav.archive import UUID as PalUUID
    new_instance = PalUUID.from_str(new_inst_str)
    skeleton['key']['InstanceId']['value'] = new_instance
    sp = skeleton['value']['RawData']['value']['object']['SaveParameter']['value']
    for k, v in src_sp.items():
        if k in ('OwnerPlayerUId', 'IndividualId', 'SlotId'):
            continue
        sp[k] = fast_deepcopy(v)
    sp['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': target_uid, 'type': 'StructProperty'}
    sp['SlotId']['value']['SlotIndex']['value'] = slot_idx
    sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = container_id
    for k in ['OldOwnerPlayerUIds', 'MapObjectConcreteInstanceIdAssignedToExpedition', 'SanityValue', 'HungerType', 'PhysicalHealth', 'WorkerSick', 'CurrentWorkSuitability', 'FoodWithStatusEffect', 'Tiemr_FoodWithStatusEffect', 'FoodRegeneEffectInfo', 'ArenaRestoreParameter', 'WorkSuitabilityOptionInfo']:
        sp.pop(k, None)
    cmap = targ_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    cmap.append(skeleton)
    char_containers = targ_lvl.setdefault('CharacterContainerSaveData', {}).setdefault('value', [])
    found = False
    for cont in char_containers:
        if cont.get('key', {}).get('ID', {}).get('value') == container_id:
            slots = cont.setdefault('value', {}).setdefault('Slots', {}).setdefault('value', {}).setdefault('values', [])
            slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': new_instance, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
            found = True
            break
    if not found:
        char_containers.append({'key': {'ID': {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': container_id, 'type': 'StructProperty'}}, 'value': {'Slots': {'id': None, 'value': {'values': [{'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': new_instance, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}], 'type': 'ArrayProperty'}, 'key_type': 'None', 'value_type': 'StructProperty'}, 'type': 'StructProperty'}})
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    for g in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        if g['value']['RawData']['value']['group_id'] == target_guild_id:
            hids = g['value']['RawData']['value'].setdefault('individual_character_handle_ids', [])
            hids.append({'guid': zero, 'instance_id': new_instance})
            break
    return True
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
                    print(f'[SKIP] {player_uuid} - Player does not exist in target world. Run the transfer again after loading the game once.')
                    continue
            except:
                print(f'[SKIP] {player_uuid} - Player does not exist in target world. Run the transfer again after loading the game once.')
                continue
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
from palsav.archive import UUID as PalUUID
from palsav.archive import FArchiveWriter
def _new_guid():
    return PalUUID(os.urandom(16))
def _set_player_groupid(targ_json, group_id):
    sd = targ_json['SaveData']['value']
    sd['GroupId'] = {'id': None, 'value': group_id, 'type': 'StructProperty', 'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000'}
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
            _set_player_groupid(targ_json, target_raw.get('group_id'))
            return True
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
    _drop = inv_info.get('DropSlotContainerId', {}).get('value', {}).get('ID', {}).get('value')
    if _drop:
        src_item_ids.add(_drop)
    for container_list, src_ids in (('CharacterContainerSaveData', src_char_ids), ('ItemContainerSaveData', src_item_ids)):
        existing_ids = {c.get('key', {}).get('ID', {}).get('value') for c in targ_lvl[container_list]['value']}
        for c in level_json.get(container_list, {}).get('value', []):
            cid = c['key']['ID']['value']
            if cid in src_ids and cid not in existing_ids:
                targ_lvl[container_list]['value'].append(fast_deepcopy(c))
    return True
def transfer_inventory_only():
    try:
        items = scan_source_inventory(host_json, level_json)
        if not items:
            return True
        return migrate_inventory_via_player_inventory(str(targ_uid), items, t_level_sav_path, targ_lvl)
    except Exception as e:
        print(f'[FAIL] transfer_inventory_only: {e}')
        return False
def transfer_pals_only():
    global host_guid, targ_uid
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player or selected_source_player)
    except:
        return False
    from palsav.archive import UUID as PalUUID
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    target_guild_id = zero
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        plist = raw.get('players', [])
        if any((str(p.get('player_uid')) == str(targ_uid) for p in plist)):
            target_guild_id = raw.get('group_id', zero)
            break
    targ_uid_str = str(targ_uid)
    removed_instances = set()
    cmap = targ_lvl.get('CharacterSaveParameterMap', {}).get('value', [])
    new_cmap = []
    for ch in cmap:
        v = get_val_safe(ch)
        if str(v.get('OwnerPlayerUId', {}).get('value')) == targ_uid_str:
            removed_instances.add(str(ch['key']['InstanceId']['value']))
        else:
            new_cmap.append(ch)
    cmap[:] = new_cmap
    targ_sd = targ_json['SaveData']['value']
    t_pal_id = targ_sd['PalStorageContainerId']['value']['ID']['value']
    t_oto_id = targ_sd['OtomoCharacterContainerId']['value']['ID']['value']
    for cont in targ_lvl.get('CharacterContainerSaveData', {}).get('value', []):
        cid = cont.get('key', {}).get('ID', {}).get('value')
        if cid in (t_pal_id, t_oto_id):
            slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            if slots:
                slots[:] = [s for s in slots if str(s.get('RawData', {}).get('value', {}).get('instance_id', '')) not in removed_instances]
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        if raw.get('group_id') == target_guild_id:
            handles = raw.get('individual_character_handle_ids', [])
            if handles:
                handles[:] = [h for h in handles if str(h.get('instance_id', '')) not in removed_instances]
            break
    source_pals = scan_source_pals(host_guid, level_json, host_json)
    for pal_data in source_pals:
        if not migrate_pal_via_api(pal_data, targ_uid, targ_lvl, targ_json, target_guild_id):
            print(f"[FAIL] Pal migration failed for instance {pal_data['instance_id']}")
            return False
    return True
def get_val_safe(p):
    try:
        return p['value']['RawData']['value']['object']['SaveParameter']['value']
    except:
        return {}
def finalize_save_task():
    errors = []
    if modified_targets_data or modified_target_players:
        try:
            _write_sav(target_gvas_file, t_level_sav_path)
        except Exception as e:
            errors.append(f'Level.sav: {e}')
            print(f"[ERROR] Level.sav write failed: {e}")
            return False
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
        print(f'Error! Player file {player_file_path} not present.')
        return None
    if not os.path.exists(player_file_path):
        print(f'Error! Invalid file {player_file_path}')
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
    global level_sav_path, level_json, selected_source_player
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
    global modified_target_players, modified_targets_data
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
_induction_mode = False
_induction_guild_choice = None
_selected_target_guild_id = None
def load_target_guilds():
    global target_guild_dict
    target_guild_dict.clear()
    guilds = []
    for g in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        try:
            raw = g['value']['RawData']['value']
            if 'values' in raw:
                continue
            gtype = g['value']['GroupType']['value']['value']
            if gtype != 'EPalGroupType::Guild':
                continue
            gid = raw.get('group_id', '')
            gname = raw.get('guild_name', '')
            players = raw.get('players', [])
            bases = raw.get('base_ids', [])
            target_guild_dict[gid] = g
            guilds.append({'group_id': gid, 'guild_name': gname, 'player_count': len(players), 'base_count': len(bases)})
        except:
            continue
    return guilds
def load_target_guilds_into_tree():
    target_player_list.clear()
    new_guild_item = QTreeWidgetItem(['(Create New Solo Guild)', '(auto)', '0', '0', '', ''])
    target_player_list.addTopLevelItem(new_guild_item)
    guilds = load_target_guilds()
    for g in guilds:
        item = QTreeWidgetItem([g['guild_name'], safe_uuid_str(g['group_id']), str(g['player_count']), str(g['base_count']), '', ''])
        target_player_list.addTopLevelItem(item)
def on_selection_of_target_guild():
    global _induction_guild_choice, _selected_target_guild_id
    selections = target_player_list.selectedItems()
    if selections:
        text0 = selections[0].text(0)
        if text0 == '(Create New Solo Guild)':
            _induction_guild_choice = 'new'
            _selected_target_guild_id = None
        else:
            _induction_guild_choice = 'existing'
            _selected_target_guild_id = selections[0].text(1)
    else:
        _induction_guild_choice = None
        _selected_target_guild_id = None
    current_selection_label.setText(f'Source: {selected_source_player}, Target Guild: {_selected_target_guild_id or _induction_guild_choice or "N/A"}')
def mint_induction_ids(source_container_ids):
    remap = {'container_ids': {}, 'dynamic_ids': {}}
    for ctype in ['main', 'key', 'weps', 'armor', 'foodbag', 'drop', 'pals', 'otomo']:
        old_id = source_container_ids.get(ctype, '')
        if old_id:
            remap['container_ids'][str(old_id).lower()] = _new_guid()
    return remap
def build_player_skeleton(src_host_json_gvas, remap, target_guild_id, src_is_post_v1, tgt_is_post_v1):
    skeleton_gvas = fast_deepcopy(src_host_json_gvas)
    sd = skeleton_gvas.properties['SaveData']['value']
    inv_info = sd.get('InventoryInfo', {}).get('value', {})
    inv_map = {'CommonContainerId': 'main', 'EssentialContainerId': 'key', 'WeaponLoadOutContainerId': 'weps', 'PlayerEquipArmorContainerId': 'armor', 'FoodEquipContainerId': 'foodbag', 'DropSlotContainerId': 'drop'}
    for field, ctype in inv_map.items():
        if field in inv_info:
            old_cid = inv_info[field].get('value', {}).get('ID', {}).get('value', '')
            new_cid = remap['container_ids'].get(str(old_cid).lower())
            if new_cid:
                inv_info[field]['value']['ID']['value'] = new_cid
    for field in ['PalStorageContainerId', 'OtomoCharacterContainerId']:
        if field in sd:
            old_cid = sd[field].get('value', {}).get('ID', {}).get('value', '')
            new_cid = remap['container_ids'].get(str(old_cid).lower())
            if new_cid:
                sd[field]['value']['ID']['value'] = new_cid
    _set_player_groupid(skeleton_gvas.properties, target_guild_id)
    if src_is_post_v1 is not None and tgt_is_post_v1 is not None and (src_is_post_v1 != tgt_is_post_v1):
        _normalize_player_save_data(sd, tgt_is_post_v1)
    return skeleton_gvas
def induct_character_entry(src_level_json, host_guid, host_json_data, target_guild_id, src_is_post_v1, tgt_is_post_v1):
    host_instance_id = host_json_data['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    exported_map = None
    for character_save_param in src_level_json['CharacterSaveParameterMap']['value']:
        try:
            uid = character_save_param['key']['PlayerUId']['value']
            inst = character_save_param['key']['InstanceId']['value']
            if str(uid) == str(host_guid) and str(inst) == str(host_instance_id):
                exported_map = character_save_param
                break
        except:
            pass
    if not exported_map:
        print(f'[ERROR] Could not find source character entry for {host_guid}')
        return False
    new_entry = fast_deepcopy(exported_map)
    raw = new_entry['value']['RawData']['value']
    raw['group_id'] = target_guild_id
    sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
    if src_is_post_v1 is not None and tgt_is_post_v1 is not None and (src_is_post_v1 != tgt_is_post_v1):
        _normalize_save_parameter(sp, tgt_is_post_v1)
    cmap = targ_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    cmap.append(new_entry)
    return True
def induct_item_containers(src_level_json, host_json_data, remap, target_lvl):
    host_sd = host_json_data['SaveData']['value']
    inv_info = host_sd['InventoryInfo']['value']
    src_item_ids = set()
    for field in ['CommonContainerId', 'EssentialContainerId', 'WeaponLoadOutContainerId', 'PlayerEquipArmorContainerId', 'FoodEquipContainerId', 'DropSlotContainerId']:
        cid = inv_info.get(field, {}).get('value', {}).get('ID', {}).get('value', '')
        if cid:
            src_item_ids.add(str(cid).lower())
    target_containers = target_lvl.setdefault('ItemContainerSaveData', {}).setdefault('value', [])
    existing_target_ids = set()
    for c in target_containers:
        cid = c.get('key', {}).get('ID', {}).get('value', '')
        if cid:
            existing_target_ids.add(str(cid).lower())
    added = 0
    for c in src_level_json.get('ItemContainerSaveData', {}).get('value', []):
        try:
            old_cid = c['key']['ID']['value']
            old_cid_lower = str(old_cid).lower()
            if old_cid_lower not in src_item_ids:
                continue
            new_cid = remap['container_ids'].get(old_cid_lower)
            if not new_cid:
                continue
            new_cid_lower = str(new_cid).lower()
            if new_cid_lower in existing_target_ids:
                continue
            new_container = fast_deepcopy(c)
            new_container['key']['ID']['value'] = new_cid
            slots = new_container.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            for slot in slots:
                raw = slot.get('RawData', {}).get('value', {})
                item = raw.get('item', {})
                dyn_id = item.get('dynamic_id', {})
                local_id = dyn_id.get('local_id_in_created_world', '')
                if local_id and str(local_id).lower() != '00000000-0000-0000-0000-000000000000':
                    old_dyn = str(local_id).lower()
                    if old_dyn not in remap['dynamic_ids']:
                        remap['dynamic_ids'][old_dyn] = _new_guid()
                    dyn_id['local_id_in_created_world'] = remap['dynamic_ids'][old_dyn]
            target_containers.append(new_container)
            existing_target_ids.add(new_cid_lower)
            added += 1
        except Exception as e:
            print(f'[WARN] Item container skip {old_cid_lower if "old_cid_lower" in dir() else "?"}: {e}')
            continue
    print(f'[INFO] Inducted {added} item containers ({len(src_item_ids)} source IDs)')
    return True
def induct_character_containers(src_level_json, host_json_data, remap, target_lvl):
    host_sd = host_json_data['SaveData']['value']
    src_char_ids = set()
    for field in ['PalStorageContainerId', 'OtomoCharacterContainerId']:
        cid = host_sd.get(field, {}).get('value', {}).get('ID', {}).get('value', '')
        if cid:
            src_char_ids.add(str(cid).lower())
    target_containers = target_lvl.setdefault('CharacterContainerSaveData', {}).setdefault('value', [])
    existing_target_ids = set()
    for c in target_containers:
        cid = c.get('key', {}).get('ID', {}).get('value', '')
        if cid:
            existing_target_ids.add(str(cid).lower())
    for c in src_level_json.get('CharacterContainerSaveData', {}).get('value', []):
        try:
            old_cid = c['key']['ID']['value']
            old_cid_lower = str(old_cid).lower()
            if old_cid_lower not in src_char_ids:
                continue
            new_cid = remap['container_ids'].get(old_cid_lower)
            if not new_cid:
                continue
            new_cid_lower = str(new_cid).lower()
            if new_cid_lower in existing_target_ids:
                continue
            new_container = fast_deepcopy(c)
            new_container['key']['ID']['value'] = new_cid
            _slots_val = new_container.get('value', {}).get('Slots', {}).get('value', {})
            if isinstance(_slots_val, dict) and 'values' in _slots_val:
                _slots_val['values'] = []
            target_containers.append(new_container)
            existing_target_ids.add(new_cid_lower)
        except:
            continue
    return True
def induct_dynamic_items(src_level_json, remap, target_lvl):
    if not remap['dynamic_ids']:
        return True
    dyn_save = target_lvl.get('DynamicItemSaveData')
    if not dyn_save:
        return True
    target_values = dyn_save.get('value', {}).get('values', [])
    source_values = src_level_json.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    old_dyn_set = set(remap['dynamic_ids'].keys())
    for item_entry in source_values:
        try:
            raw = item_entry.get('RawData', {}).get('value', {})
            item_id = raw.get('id', {})
            local_id = item_id.get('local_id_in_created_world', '')
            if local_id and str(local_id).lower() in old_dyn_set:
                new_item = fast_deepcopy(item_entry)
                new_raw = new_item['RawData']['value']
                new_raw['id']['local_id_in_created_world'] = remap['dynamic_ids'][str(local_id).lower()]
                target_values.append(new_item)
        except:
            continue
    return True
def induct_pals(src_level_json, host_guid, host_json_data, remap, target_guild_id, target_lvl):
    source_pals = scan_source_pals(host_guid, src_level_json, host_json_data)
    if not source_pals:
        return True
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    used_ids = set()
    for ch in target_lvl.get('CharacterSaveParameterMap', {}).get('value', []):
        used_ids.add(str(ch['key']['InstanceId']['value']).lower())
    cmap = target_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    char_containers = target_lvl.setdefault('CharacterContainerSaveData', {}).setdefault('value', [])
    guild_entry = None
    for g in target_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw_gid = g.get('value', {}).get('RawData', {}).get('value', {}).get('group_id', '')
        if str(raw_gid).lower() == str(target_guild_id).lower():
            guild_entry = g
            break
    for pal_data in source_pals:
        try:
            old_inst = str(pal_data['instance_id'])
            old_slot_cid = pal_data['save_parameter'].get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
            new_slot_cid = remap['container_ids'].get(str(old_slot_cid).lower())
            if not new_slot_cid:
                continue
            new_inst = str(_new_guid())
            while new_inst.lower() in used_ids:
                new_inst = str(_new_guid())
            used_ids.add(new_inst.lower())
            remap['instance_ids'][old_inst.lower()] = new_inst
            src_entry = pal_data['source_entry']
            new_entry = fast_deepcopy(src_entry)
            new_entry['key']['InstanceId']['value'] = PalUUID.from_str(new_inst)
            raw = new_entry['value']['RawData']['value']
            raw['group_id'] = target_guild_id
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if 'SlotId' in sp:
                sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = new_slot_cid
            for k in ['MapObjectConcreteInstanceIdAssignedToExpedition', 'WorkerSick', 'CurrentWorkSuitability', 'FoodWithStatusEffect', 'Tiemr_FoodWithStatusEffect', 'ArenaRestoreParameter', 'WorkSuitabilityOptionInfo']:
                sp.pop(k, None)
            cmap.append(new_entry)
            _new_slot = {'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': pal_data['slot_index']}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': zero, 'instance_id': PalUUID.from_str(new_inst), 'permission_tribe_id': 0, 'unknown_bytes': b'\x00\x00\x00\x00\x00'}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': b'\x01\x00\x00\x008\x0b\x00\xdeII\xd7\xce\x97\xdf-\x99\xc0\xc1\xc3i\x01\x00\x00\x00'}, 'type': 'ArrayProperty'}}
            found = False
            for cont in char_containers:
                if str(cont.get('key', {}).get('ID', {}).get('value', '')).lower() == str(new_slot_cid).lower():
                    slots = cont.setdefault('value', {}).setdefault('Slots', {}).setdefault('value', {}).setdefault('values', [])
                    slots.append(_new_slot)
                    found = True
                    break
            if not found:
                char_containers.append({'key': {'ID': {'struct_type': 'Guid', 'struct_id': zero, 'id': None, 'value': new_slot_cid, 'type': 'StructProperty'}}, 'value': {'bReferenceSlot': {'id': None, 'type': 'BoolProperty', 'value': False}, 'Slots': {'id': None, 'value': {'values': [_new_slot], 'type': 'ArrayProperty'}, 'key_type': 'None', 'value_type': 'StructProperty'}, 'SlotNum': {'id': None, 'type': 'IntProperty', 'value': pal_data['slot_index'] + 1}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': b''}, 'type': 'ArrayProperty'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': b''}, 'type': 'ArrayProperty'}}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': b''}, 'type': 'ArrayProperty'}})
            if guild_entry:
                hids = guild_entry['value']['RawData']['value'].setdefault('individual_character_handle_ids', [])
                hids.append({'guid': host_guid, 'instance_id': PalUUID.from_str(new_inst)})
        except Exception as e:
            print(f'[WARN] Pal induction failed for instance {pal_data.get("instance_id", "?")}: {e}')
            continue
    return True
def create_solo_guild(target_lvl, host_guid, host_instance_id, player_name, target_world_tick):
    new_guild_id = _new_guid()
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    uid_str = str(host_guid).upper().replace('-', '')
    guild_name_val = player_name or 'Solo Guild'
    _zero_bytes4 = b'\x00\x00\x00\x00'
    _guild_cv = b'\x07\x00\x00\x00\x00'
    guild_entry = {'key': new_guild_id, 'value': {'GroupType': {'id': None, 'value': {'type': 'EPalGroupType', 'value': 'EPalGroupType::Guild'}, 'type': 'EnumProperty'}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'group_type': 'EPalGroupType::Guild', 'group_id': new_guild_id, 'group_name': uid_str, 'individual_character_handle_ids': [{'guid': host_guid, 'instance_id': host_instance_id}], 'org_type': 0, 'leading_bytes': _zero_bytes4, 'base_ids': [], 'unknown_1': 0, 'base_camp_level': 1, 'map_object_instance_ids_base_camp_points': [], 'guild_name': guild_name_val, 'last_guild_name_modifier_player_uid': host_guid, 'unknown_2': _zero_bytes4, 'admin_player_uid': host_guid, 'players': [{'player_uid': host_guid, 'player_info': {'last_online_real_time': target_world_tick or 0, 'player_name': guild_name_val}}], 'trailing_bytes': _zero_bytes4}, 'custom_type': '.worldSaveData.GroupSaveDataMap', 'type': 'ArrayProperty'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': _guild_cv}, 'type': 'ArrayProperty'}}}
    guilds = target_lvl.setdefault('GroupSaveDataMap', {}).setdefault('value', [])
    guilds.append(guild_entry)
    guild_extra = target_lvl.setdefault('GuildExtraSaveDataMap', {}).setdefault('value', [])
    existing_extra = {str(g.get('key', '')) for g in guild_extra}
    if str(new_guild_id) not in existing_extra:
        _expedition_cv = b'\x03\x00\x00\x00\x00\x00\x00\x00\x00'
        guild_extra.append({'key': new_guild_id, 'value': {'GuildItemStorage': {'struct_type': 'PalGuildItemStorageSaveData', 'struct_id': zero, 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'container_id': '00000000-0000-0000-0000-000000000000'}, 'custom_type': '.worldSaveData.GuildExtraSaveDataMap.Value.GuildItemStorage.RawData', 'type': 'ArrayProperty'}}, 'type': 'StructProperty'}, 'Lab': {'struct_type': 'PalGuildLabSaveData', 'struct_id': zero, 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'research_info': [], 'current_research_id': 'None'}, 'custom_type': '.worldSaveData.GuildExtraSaveDataMap.Value.Lab.RawData', 'type': 'ArrayProperty'}}, 'type': 'StructProperty'}, 'Expedition': {'id': None, 'value': {'values': _expedition_cv}, 'type': 'ArrayProperty'}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': b''}, 'type': 'ArrayProperty'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': b''}, 'type': 'ArrayProperty'}}})
    return new_guild_id
def induct_into_guild(target_lvl, host_guid, host_instance_id, player_name, target_guild_id, target_world_tick):
    guild_entry = None
    for g in target_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = g.get('value', {}).get('RawData', {}).get('value', {})
        if str(raw.get('group_id', '')).lower() == str(target_guild_id).lower():
            guild_entry = g
            break
    if not guild_entry:
        return False
    raw = guild_entry['value']['RawData']['value']
    players = raw.setdefault('players', [])
    for p in players:
        if str(p.get('player_uid', '')).lower() == str(host_guid).lower():
            players.remove(p)
            break
    players.append({'player_uid': host_guid, 'player_info': {'last_online_real_time': target_world_tick or 0, 'player_name': player_name or 'Player'}})
    hids = raw.setdefault('individual_character_handle_ids', [])
    hids.append({'guid': host_guid, 'instance_id': host_instance_id})
    return True
def validate_induction(target_lvl, host_guid, remap, target_guild_id):
    errors = []
    host_lower = str(host_guid).lower()
    cspm = target_lvl.get('CharacterSaveParameterMap', {}).get('value', [])
    player_entries = 0
    for entry in cspm:
        try:
            key_uid = str(entry['key']['PlayerUId']['value']).lower()
            if key_uid == host_lower:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                if sp.get('IsPlayer', {}).get('value', False):
                    player_entries += 1
                raw_gid = entry['value']['RawData']['value'].get('group_id', '')
                if str(raw_gid).lower() != str(target_guild_id).lower():
                    errors.append(f'Character entry group_id mismatch: {raw_gid} != {target_guild_id}')
        except:
            continue
    if player_entries == 0:
        errors.append('No player entry found in CharacterSaveParameterMap for source UID')
    elif player_entries > 1:
        errors.append(f'Multiple player entries ({player_entries}) found for source UID')
    found_in_guild = False
    for g in target_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = g.get('value', {}).get('RawData', {}).get('value', {})
        for p in raw.get('players', []):
            if str(p.get('player_uid', '')).lower() == host_lower:
                found_in_guild = True
                break
        if found_in_guild:
            break
    if not found_in_guild:
        errors.append('Source UID not found in any guild players[] roster')
    item_containers = target_lvl.get('ItemContainerSaveData', {}).get('value', [])
    char_containers = target_lvl.get('CharacterContainerSaveData', {}).get('value', [])
    all_container_ids = set()
    for c in item_containers + char_containers:
        cid = c.get('key', {}).get('ID', {}).get('value', '')
        if cid:
            all_container_ids.add(str(cid).lower())
    for old_cid, new_cid in remap['container_ids'].items():
        if str(new_cid).lower() not in all_container_ids:
            errors.append(f'Container ID {new_cid} (from {old_cid}) not found in target containers')
    for entry in cspm:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            if sp.get('IsPlayer', {}).get('value', False):
                continue
            owner = str(sp.get('OwnerPlayerUId', {}).get('value', '')).lower()
            if owner != host_lower:
                continue
            slot_cid = sp.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
            if slot_cid and str(slot_cid).lower() not in all_container_ids:
                errors.append(f'Pal SlotId references non-existent container: {slot_cid}')
            raw_gid = entry['value']['RawData']['value'].get('group_id', '')
            if str(raw_gid).lower() != str(target_guild_id).lower():
                errors.append(f'Pal group_id mismatch: {raw_gid} != {target_guild_id}')
        except:
            continue
    return errors
def induct_character(skip_msgbox=False, skip_gui=False):
    global host_guid, host_json, host_json_gvas
    global remap, exported_map
    if not all([level_sav_path, t_level_sav_path, selected_source_player]):
        print('Error! Please have both level files and source player selected.')
        return False
    if not _induction_guild_choice:
        print('Error! Please select a target guild or "Create New Solo Guild".')
        return False
    try:
        host_guid = UUID.from_str(selected_source_player)
    except Exception as e:
        print(f'UUID Error: Invalid source UUID format: {e}')
        return False
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas:
        print('Error: Could not load source player .sav file.')
        return False
    host_json = host_json_gvas.properties
    host_instance_id = host_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    source_player_level = get_player_level_from_cspm(level_json, selected_source_player)
    if source_player_level < 2:
        print(f'Error: Source player must be at least level 2. Current level: {source_player_level}')
        if not skip_gui:
            show_warning(None, t('Error!'), f'Source player must be at least level 2 (current: {source_player_level}).')
        return False
    tgt_players_folder = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
    os.makedirs(tgt_players_folder, exist_ok=True)
    source_container_ids = gather_inventory_ids(host_json)
    create_new = (_induction_guild_choice == 'new')
    remap = mint_induction_ids(source_container_ids)
    remap['instance_ids'] = {}
    host_lower = str(host_guid).lower()
    for ch in targ_lvl.get('CharacterSaveParameterMap', {}).get('value', []):
        if str(ch['key']['PlayerUId']['value']).lower() == host_lower:
            print(f'[WARNING] Source UID {host_guid} already exists in target CharacterSaveParameterMap.')
            break
    player_name = ''
    try:
        for ch in level_json.get('CharacterSaveParameterMap', {}).get('value', []):
            if str(ch['key']['PlayerUId']['value']).lower() == host_lower:
                sp = ch['value']['RawData']['value']['object']['SaveParameter']['value']
                player_name = sp.get('NickName', {}).get('value', '')
                break
    except:
        pass
    if not player_name:
        try:
            nick = host_json['SaveData']['value'].get('NickName', {})
            player_name = nick.get('value', '') if isinstance(nick, dict) else str(nick)
        except:
            pass
    if not player_name:
        player_name = 'Player'
    if source_is_post_v1 is not None and target_is_post_v1 is not None and (source_is_post_v1 != target_is_post_v1):
        _normalize_level_data(targ_lvl, target_is_post_v1)
    print('[STEP 1/10] Creating guild / resolving guild membership...')
    if create_new:
        target_guild_id = create_solo_guild(targ_lvl, host_guid, host_instance_id, player_name, target_world_tick)
        print('[SUCCESS] Created new solo guild')
    else:
        target_guild_id = _selected_target_guild_id
        if not induct_into_guild(targ_lvl, host_guid, host_instance_id, player_name, target_guild_id, target_world_tick):
            print('[FAIL] Guild induction')
            return False
        print('[SUCCESS] Added to existing guild')
    if not target_guild_id:
        print('[ERROR] No target guild ID resolved.')
        return False
    skeleton_gvas = build_player_skeleton(host_json_gvas, remap, target_guild_id, source_is_post_v1, target_is_post_v1)
    skeleton_sd = skeleton_gvas.properties
    print('[STEP 2/10] Inducting character entry...')
    if not induct_character_entry(level_json, host_guid, host_json, target_guild_id, source_is_post_v1, target_is_post_v1):
        print('[FAIL] Character entry induction')
        return False
    print('[SUCCESS] Character entry inducted')
    print('[STEP 3/10] Transferring tech & data...')
    old_targ_json = targ_json
    globals()['targ_json'] = skeleton_sd
    if not transfer_tech_and_data():
        print('[FAIL] Tech + data transfer')
        globals()['targ_json'] = old_targ_json
        return False
    globals()['targ_json'] = skeleton_sd
    print('[SUCCESS] Tech + data transferred')
    print('[STEP 4/10] Inducting item containers...')
    if not induct_item_containers(level_json, host_json, remap, targ_lvl):
        print('[FAIL] Item containers')
        return False
    print('[SUCCESS] Item containers inducted')
    print('[STEP 5/10] Inducting character containers...')
    if not induct_character_containers(level_json, host_json, remap, targ_lvl):
        print('[FAIL] Character containers')
        return False
    print('[SUCCESS] Character containers inducted')
    print('[STEP 6/10] Inducting dynamic items...')
    if not induct_dynamic_items(level_json, remap, targ_lvl):
        print('[FAIL] Dynamic items')
        return False
    print('[SUCCESS] Dynamic items inducted')
    print('[STEP 7/10] Inducting pals...')
    if not induct_pals(level_json, host_guid, host_json, remap, target_guild_id, targ_lvl):
        print('[FAIL] Pal induction')
        return False
    print('[SUCCESS] Pals inducted')
    print('[STEP 8/10] Syncing timestamps...')
    sync_player_timestamps(host_guid, targ_lvl)
    print('[SUCCESS] Timestamps synced')
    print('[STEP 9/10] Validating graph integrity...')
    validation_errors = validate_induction(targ_lvl, host_guid, remap, target_guild_id)
    if validation_errors:
        print(f'[WARNING] Validation found {len(validation_errors)} issue(s):')
        for err in validation_errors:
            print(f'  - {err}')
    else:
        print('[SUCCESS] All validation checks passed')
    print('[STEP 10/10] Registering for save...')
    uid_str = str(host_guid).upper().replace('-', '')
    modified_target_players.add(uid_str)
    modified_targets_data[uid_str] = (fast_deepcopy(skeleton_sd), skeleton_gvas, selected_source_player)
    if not skip_gui:
        load_players(targ_lvl, is_source=False)
    if not skip_msgbox:
        show_information(None, t('Transfer Successful'), t("Induction successful in memory! Hit 'Save Changes' to save."))
    globals()['targ_json'] = old_targ_json
    return True
def character_transfer():
    return CharacterTransferWindow()
if __name__ == '__main__':
    app = QApplication([])
    w = CharacterTransferWindow()
    w.show()
    sys.exit(app.exec())