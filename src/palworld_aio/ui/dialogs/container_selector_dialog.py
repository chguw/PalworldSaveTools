import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QFrame, QMenu, QListWidget, QListWidgetItem, QComboBox, QApplication, QSplitter, QMessageBox, QWidget, QTabBar
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.inventory.inventory_manager import ItemData
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
from ..tabs.container_ids_tab import ContainerSlotWidget, get_container_type_display, get_container_icon
from ..tabs.inventory_tab import ItemSlotWidget, GRID_COLS, InventoryGridWidget, EquipmentSlotWidget, EQUIP_SLOT_FILTERS
CONTAINER_TYPES = [('CommonContainerId', 'container_selector.slot_main', 'Regular Inventory'), ('EssentialContainerId', 'container_selector.slot_key', 'Key Items'), ('WeaponLoadOutContainerId', 'container_selector.slot_weapons', 'Weapons'), ('PlayerEquipArmorContainerId', 'container_selector.slot_armor', 'Armor'), ('FoodEquipContainerId', 'container_selector.slot_food', 'Food Bag')]
INVENTORY_CONTAINER_TYPES = {'CommonContainerId', 'EssentialContainerId'}
EQUIPMENT_CONTAINER_TYPES = {'WeaponLoadOutContainerId', 'PlayerEquipArmorContainerId', 'FoodEquipContainerId'}
INV_VIEWS = [('regular', 'Regular Inventory'), ('equipment', 'Equipped Inventory'), ('key', 'Key Items')]
_COL_BG = 'background: rgba(18, 20, 24, 0.65); border: 1px solid rgba(125, 211, 252, 0.15); border-radius: 8px;'
_COL_HEADER = 'font-size: 13px; font-weight: bold; color: #e2e8f0; padding: 4px 0;'
class ContainerSelectorDialog(QDialog):
    def __init__(self, player_uid, player_name, parent=None):
        super().__init__(parent)
        self.player_uid = player_uid
        self.player_name = player_name
        self.orphaned_containers = []
        self.container_widgets = {}
        self.selected_containers = {ct[0]: None for ct in CONTAINER_TYPES}
        self.slot_labels = {}
        self._active_inv_slot = 'CommonContainerId'
        self._inv_grids = {}
        self.setMinimumSize(1200, 700)
        self._setup_ui()
    def _make_vertical_divider(self):
        d = QFrame()
        d.setFrameShape(QFrame.VLine)
        d.setStyleSheet('background: rgba(125,211,252,0.1); max-width: 1px;')
        return d
    def _setup_ui(self):
        self.setWindowTitle(t('container_selector.title', player_name=self.player_name))
        self.setStyleSheet('QDialog { background: rgba(14,16,20,0.95); }')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        header_frame = QFrame()
        header_frame.setStyleSheet('background: rgba(30, 35, 45, 0.8); border-radius: 6px; padding: 8px;')
        header_layout = QHBoxLayout(header_frame)
        name_label = QLabel(f"{t('container_selector.title', player_name=self.player_name)}")
        name_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #ffffff;')
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        uid_label = QLabel(f'UID: {self.player_uid[:8]}...')
        uid_label.setStyleSheet('font-size: 11px; color: #999999; font-family: monospace;')
        header_layout.addWidget(uid_label)
        main_layout.addWidget(header_frame)
        cols = QHBoxLayout()
        cols.setSpacing(8)
        cols.addWidget(self._build_left_column(), 2)
        cols.addWidget(self._make_vertical_divider())
        cols.addWidget(self._build_mid_column(), 2)
        cols.addWidget(self._make_vertical_divider())
        cols.addWidget(self._build_right_column(), 3)
        main_layout.addLayout(cols, 1)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 6, 0, 0)
        self.update_btn = QPushButton(t('container_selector.update_btn'))
        self.update_btn.setStyleSheet('QPushButton { background: rgba(74, 222, 128, 0.8); color: #ffffff; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; font-size: 13px; } QPushButton:hover { background: rgba(74, 222, 128, 1.0); } QPushButton:disabled { background: rgba(100, 100, 100, 0.3); color: rgba(255,255,255,0.3); }')
        self.update_btn.clicked.connect(self._update_container_ids)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)
        cancel_btn = QPushButton(t('container_selector.cancel_btn'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255, 80, 80, 0.8); color: #ffffff; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; font-size: 13px; } QPushButton:hover { background: rgba(255, 80, 80, 1.0); }')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        self.load_containers()
        self._load_player_inventories()
    def _build_left_column(self):
        panel = QFrame()
        panel.setStyleSheet(_COL_BG)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        title = QLabel(t('container_selector.player_inventory'))
        title.setStyleSheet(_COL_HEADER)
        layout.addWidget(title)
        tab_bar = QTabBar()
        tab_bar.setStyleSheet('QTabBar { font-size: 11px; } QTabBar::tab { background: rgba(40,45,55,0.5); color: #aaa; border: 1px solid rgba(255,255,255,0.05); border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 6px 14px; margin-right: 2px; } QTabBar::tab:selected { background: rgba(59,130,246,0.2); color: #fff; border-color: rgba(59,130,246,0.3); } QTabBar::tab:hover:!selected { background: rgba(255,255,255,0.05); color: #ddd; }')
        for key, label in INV_VIEWS:
            tab_bar.addTab(label)
        tab_bar.currentChanged.connect(self._on_inv_tab_changed)
        layout.addWidget(tab_bar)
        self._inv_stack = QWidget()
        self._inv_stack_layout = QVBoxLayout(self._inv_stack)
        self._inv_stack_layout.setContentsMargins(0, 0, 0, 0)
        self._inv_grids = {}
        for key, label in INV_VIEWS:
            if key == 'equipment':
                g = self._build_equipment_widget()
            else:
                g = InventoryGridWidget('player_' + key)
                g.tab_label.setVisible(False)
                g.header_layout.setContentsMargins(0, 0, 0, 0)
                for i in range(g.header_layout.count()):
                    w = g.header_layout.itemAt(i).widget()
                    if w and hasattr(w, 'setVisible'):
                        w.setVisible(False)
            g.setVisible(False)
            self._inv_grids[key] = g
            self._inv_stack_layout.addWidget(g)
        layout.addWidget(self._inv_stack, 1)
        self._slot_assignment_header = QLabel(t('container_selector.assign_slots'))
        self._slot_assignment_header.setStyleSheet('font-size: 12px; font-weight: bold; color: #94a3b8; padding-top: 8px;')
        layout.addWidget(self._slot_assignment_header)
        self.slot_labels = {}
        for container_type, trans_key, display_name in CONTAINER_TYPES:
            sf = QFrame()
            sf.setFixedHeight(32)
            sf.setStyleSheet('background: rgba(40, 45, 55, 0.4); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px;')
            sl = QHBoxLayout(sf)
            sl.setContentsMargins(8, 4, 8, 4)
            lbl = QLabel(f'  {display_name}')
            lbl.setStyleSheet('font-size: 10px; color: #ccc; font-weight: 500;')
            sl.addWidget(lbl)
            sl.addStretch()
            st = QLabel(t('container_selector.auto_none'))
            st.setStyleSheet('font-size: 9px; color: #7dd3fc;')
            sl.addWidget(st)
            cb = QPushButton('×')
            cb.setFixedSize(16, 16)
            cb.setStyleSheet('QPushButton { background: rgba(255,80,80,0.5); color: #fff; border: none; border-radius: 3px; font-size: 10px; } QPushButton:hover { background: rgba(255,80,80,0.8); }')
            cb.clicked.connect(lambda ct=container_type: self._clear_slot(ct))
            sl.addWidget(cb)
            layout.addWidget(sf)
            self.slot_labels[container_type] = st
        layout.addStretch()
        return panel
    def _build_mid_column(self):
        panel = QFrame()
        panel.setStyleSheet(_COL_BG)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        title = QLabel(t('container_selector.unconnected_pool'))
        title.setStyleSheet(_COL_HEADER)
        layout.addWidget(title)
        self._mid_tab_bar = QTabBar()
        self._mid_tab_bar.setStyleSheet('QTabBar { font-size: 11px; } QTabBar::tab { background: rgba(40,45,55,0.5); color: #aaa; border: 1px solid rgba(255,255,255,0.05); border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 4px 10px; margin-right: 2px; } QTabBar::tab:selected { background: rgba(59,130,246,0.2); color: #fff; border-color: rgba(59,130,246,0.3); } QTabBar::tab:hover:!selected { background: rgba(255,255,255,0.05); color: #ddd; }')
        self._mid_tab_bar.addTab('Regular Inventory')
        self._mid_tab_bar.addTab('Equipped')
        self._mid_tab_bar.addTab('Key Items')
        self._mid_tab_bar.currentChanged.connect(self._on_mid_tab_changed)
        layout.addWidget(self._mid_tab_bar)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('font-size: 10px; color: #7dd3fc;')
        layout.addWidget(self.status_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll, 1)
        return panel
    def _build_right_column(self):
        panel = QFrame()
        panel.setStyleSheet(_COL_BG)
        panel.setMinimumWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        self._preview_header = QLabel(t('container_selector.container_preview'))
        self._preview_header.setStyleSheet(_COL_HEADER)
        layout.addWidget(self._preview_header)
        self._preview_info = QLabel('')
        self._preview_info.setStyleSheet('font-size: 10px; color: #94a3b8;')
        layout.addWidget(self._preview_info)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._preview_grid_widget = QWidget()
        self._preview_grid_layout = QGridLayout(self._preview_grid_widget)
        self._preview_grid_layout.setHorizontalSpacing(2)
        self._preview_grid_layout.setVerticalSpacing(4)
        self._preview_grid_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._preview_grid_widget)
        layout.addWidget(scroll, 1)
        return panel
    def _on_inv_tab_changed(self, idx):
        for key, g in self._inv_grids.items():
            g.setVisible(False)
        key = INV_VIEWS[idx][0]
        self._inv_grids[key].setVisible(True)
        ct_map = {'regular': 'CommonContainerId', 'equipment': 'WeaponLoadOutContainerId', 'key': 'EssentialContainerId'}
        self._active_inv_slot = ct_map.get(key, 'CommonContainerId')
    def _build_equipment_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(4, 4, 8, 4)
        cl.setSpacing(4)
        self._equip_slots = {}
        equip_main = QHBoxLayout()
        equip_main.setSpacing(8)
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        weapon_header = QLabel('Weapons')
        weapon_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(weapon_header)
        weapon_grid = QGridLayout()
        weapon_grid.setSpacing(2)
        weapon_grid.setContentsMargins(0, 0, 0, 0)
        for i, (r, c) in enumerate([(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1)]):
            slot = EquipmentSlotWidget(f'weapon{i + 1}', f'W{i + 1}')
            self._equip_slots[f'weapon{i + 1}'] = slot
            weapon_grid.addWidget(slot, r, c)
        weapon_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(weapon_grid)
        left_col.addSpacing(6)
        acc_header = QLabel('Accessory')
        acc_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(acc_header)
        acc_grid = QGridLayout()
        acc_grid.setSpacing(2)
        acc_grid.setContentsMargins(0, 0, 0, 0)
        for i, (r, c) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
            slot = EquipmentSlotWidget(f'accessory{i + 1}', f'A{i + 1}')
            self._equip_slots[f'accessory{i + 1}'] = slot
            acc_grid.addWidget(slot, r, c)
        acc_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(acc_grid)
        left_col.addSpacing(6)
        food_header = QLabel('Food')
        food_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(food_header)
        food_grid = QGridLayout()
        food_grid.setSpacing(2)
        food_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(5):
            slot = EquipmentSlotWidget(f'food{i + 1}', f'F{i + 1}')
            self._equip_slots[f'food{i + 1}'] = slot
            food_grid.addWidget(slot, 0, i)
        food_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(food_grid)
        equip_main.addLayout(left_col)
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        for label, key in [('Head', 'head'), ('Body', 'body'), ('Shield', 'shield'), ('Glider', 'glider'), ('Module', 'sphere_mod')]:
            h = QLabel(label)
            h.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
            right_col.addWidget(h)
            slot = EquipmentSlotWidget(key, label[0])
            self._equip_slots[key] = slot
            right_col.addWidget(slot)
        equip_main.addLayout(right_col)
        cl.addLayout(equip_main)
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return w
    def _clear_slot(self, container_type):
        container_info = self.orphaned_containers_dict.get(self.selected_containers.get(container_type), {})
        self.selected_containers[container_type] = None
        lbl = self.slot_labels.get(container_type)
        if lbl:
            lbl.setText(t('container_selector.auto_none'))
            lbl.setStyleSheet('font-size: 9px; color: #7dd3fc;')
        self._update_selection_display()
        self.update_btn.setEnabled(any((v is not None for v in self.selected_containers.values())))
    def _update_selection_display(self):
        for cid, w in self.container_widgets.items():
            w.setStyleSheet(self._get_container_style(cid))
    def _get_container_style(self, container_id, is_selected=False):
        info = self.orphaned_containers_dict.get(container_id, {})
        ic = info.get('item_count', 0)
        bc = 'rgba(74, 222, 128, 0.5)' if ic > 0 else 'rgba(255, 255, 255, 0.15)'
        bg = 'rgba(30, 40, 35, 0.9)' if ic > 0 else 'rgba(30, 35, 45, 0.8)'
        return f'ContainerSlotWidget {{ background-color: {bg}; border: 1px solid {bc}; border-radius: 6px; }} ContainerSlotWidget:hover {{ background-color: rgba(50, 60, 70, 0.9); border: 1px solid rgba(125, 211, 252, 0.4); }}'
    def load_containers(self):
        for w in self.container_widgets.values():
            w.deleteLater()
        self.container_widgets.clear()
        self.orphaned_containers = []
        if not constants.loaded_level_json:
            self.status_label.setText(t('containers.no_save_loaded'))
            return
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            from collections import Counter
            container_id_counts = Counter()
            for cont in item_containers:
                try:
                    cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                    if cont_id:
                        container_id_counts[str(cont_id).replace('-', '').lower()] += 1
                except:
                    pass
            all_referenced_ids = set()
            char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
            for entry in char_map:
                try:
                    sv = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    sid = sv.get('SlotId', {}).get('value', {})
                    cid = sid.get('ContainerId', {}).get('value', {}).get('ID', {})
                    if cid:
                        all_referenced_ids.add(str(cid.get('value', '')).replace('-', '').lower())
                except:
                    pass
            for cc in wsd.get('CharacterContainerSaveData', {}).get('value', []):
                try:
                    cid = cc.get('key', {}).get('ID', {}).get('value', '')
                    if cid:
                        all_referenced_ids.add(str(cid).replace('-', '').lower())
                except:
                    pass
            for group in wsd.get('GroupSaveDataMap', {}).get('value', []):
                try:
                    raw = group.get('value', {}).get('RawData', {}).get('value', {})
                    for key in ['worker_character_handle_ids', 'individual_character_handle_ids']:
                        for handle in raw.get(key, []):
                            cid = handle.get('ContainerId', {}).get('ID', {}).get('value', '')
                            if cid:
                                all_referenced_ids.add(str(cid).replace('-', '').lower())
                except:
                    pass
            player_owned_ids = set()
            try:
                uid_clean = self.player_uid.replace('-', '').lower()
                players_dir = os.path.join(os.path.dirname(constants.loaded_level_path), 'Players')
                if os.path.isdir(players_dir):
                    for fname in os.listdir(players_dir):
                        if not fname.endswith('.sav') or fname.endswith('_dps.sav'):
                            continue
                        if fname.replace('.sav', '').lower() == uid_clean:
                            gv = sav_to_gvasfile(os.path.join(players_dir, fname))
                            sd = gv.properties.get('SaveData', {}).get('value', {})
                            inv_info = sd.get('InventoryInfo', {}).get('value', {})
                            for ct, _, _ in CONTAINER_TYPES:
                                cid_obj = inv_info.get(ct, {}).get('value', {}).get('ID', {})
                                cid = cid_obj.get('value', '') if isinstance(cid_obj, dict) else str(cid_obj)
                                if cid:
                                    player_owned_ids.add(str(cid).replace('-', '').lower())
                            break
            except:
                pass
            self.orphaned_containers_dict = {}
            for cont in item_containers:
                try:
                    cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                    if not cont_id:
                        continue
                    cid_clean = str(cont_id).replace('-', '').lower()
                    if cid_clean in all_referenced_ids or cid_clean in player_owned_ids:
                        continue
                    slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    slot_count = len(slots)
                    item_count = sum((1 for s in slots if s.get('RawData', {}).get('value', {}).get('item', {}).get('static_id')))
                    if item_count == 0 or slot_count <= 1:
                        continue
                    ct = self._categorize_container(cont)
                    info = {'id': str(cont_id), 'id_clean': cid_clean, 'slot_count': slot_count, 'item_count': item_count, 'items': [], 'container_type': ct, 'appears_once': container_id_counts.get(cid_clean, 0) == 1}
                    self.orphaned_containers.append(info)
                    self.orphaned_containers_dict[cid_clean] = info
                except:
                    continue
            self.orphaned_containers.sort(key=lambda x: (-x['slot_count'], -x['item_count']))
            for i, info in enumerate(self.orphaned_containers):
                w = ContainerSlotWidget(info)
                w.clicked.connect(self._on_container_clicked)
                w.context_menu_requested.connect(self._on_container_context_menu)
                r, c = divmod(i, 1)
                self.grid_layout.addWidget(w, r, c)
                self.container_widgets[info['id_clean']] = w
            self._apply_mid_filter()
        except Exception as e:
            self.status_label.setText(f'Error: {str(e)}')
    def _on_mid_tab_changed(self, idx):
        self._apply_mid_filter()
    def _apply_mid_filter(self):
        idx = self._mid_tab_bar.currentIndex()
        for cid, w in self.container_widgets.items():
            ct = self.orphaned_containers_dict.get(cid, {}).get('container_type', 'regular')
            ct_map = {0: 'regular', 1: 'equipment', 2: 'key'}
            w.setVisible(ct == ct_map.get(idx, 'regular'))
        visible = sum((1 for w in self.container_widgets.values() if w.isVisible()))
        self.status_label.setText(t('container_selector.found_containers', count=visible))
    def _categorize_slot_count(self, slot_count):
        return 'regular'
    def _categorize_container(self, container):
        slots = container.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
        has_equip = False
        has_regular = False
        has_key = False
        for slot in slots:
            rd = slot.get('RawData', {}).get('value', {})
            if not rd:
                continue
            item_info = rd.get('item', {})
            if not item_info:
                continue
            static_id = item_info.get('static_id', '')
            if not static_id:
                continue
            item_data = ItemData.get_item_by_asset(static_id)
            type_a = item_data.get('type_a', '')
            if type_a == 'EPalItemTypeA::Essential':
                has_key = True
            elif type_a in ('EPalItemTypeA::Weapon', 'EPalItemTypeA::MonsterEquipWeapon', 'EPalItemTypeA::Armor', 'EPalItemTypeA::Accessory', 'EPalItemTypeA::Glider', 'EPalItemTypeA::CaptureItemModifier', 'EPalItemTypeA::Food'):
                has_equip = True
            else:
                has_regular = True
        if has_key and (not has_regular) and (not has_equip):
            return 'key'
        if has_equip and (not has_regular) and (not has_key):
            return 'equipment'
        return 'regular'
    def _load_player_inventories(self):
        if not constants.loaded_level_json:
            return
        try:
            uid_clean = self.player_uid.replace('-', '').lower()
            players_dir = os.path.join(os.path.dirname(constants.loaded_level_path), 'Players')
            if not os.path.isdir(players_dir):
                return
            for fname in os.listdir(players_dir):
                if not fname.endswith('.sav') or fname.endswith('_dps.sav'):
                    continue
                if fname.replace('.sav', '').lower() == uid_clean:
                    gv = sav_to_gvasfile(os.path.join(players_dir, fname))
                    sd = gv.properties.get('SaveData', {}).get('value', {})
                    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
                    inv_info = sd.get('InventoryInfo', {}).get('value', {})
                    def _get_items_for(container_type):
                        cid_obj = inv_info.get(container_type, {}).get('value', {}).get('ID', {})
                        cid = cid_obj.get('value', '') if isinstance(cid_obj, dict) else str(cid_obj)
                        cid_str = str(cid).replace('-', '').lower() if cid else ''
                        items = []
                        for cont in item_containers:
                            if str(cont.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() == cid_str:
                                for slot in cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
                                    rd = slot.get('RawData', {}).get('value', {})
                                    if not rd:
                                        continue
                                    item_info = rd.get('item', {})
                                    if not item_info:
                                        continue
                                    sid = item_info.get('static_id', '')
                                    if not sid:
                                        continue
                                    item_data = ItemData.get_item_by_asset(sid)
                                    items.append({'item_id': sid, 'item_name': item_data.get('name', sid), 'stack_count': rd.get('count', 1), 'icon_path': item_data.get('icon', '')})
                                break
                        return items
                    regular_items = _get_items_for('CommonContainerId')
                    key_items = _get_items_for('EssentialContainerId')
                    weapons_items = _get_items_for('WeaponLoadOutContainerId')
                    armor_items = _get_items_for('PlayerEquipArmorContainerId')
                    food_items = _get_items_for('FoodEquipContainerId')
                    equip_items = weapons_items + armor_items + food_items
                    for i, it in enumerate(regular_items):
                        it['slot_index'] = i
                    for i, it in enumerate(key_items):
                        it['slot_index'] = i
                    for i, it in enumerate(equip_items):
                        it['slot_index'] = i
                    g = self._inv_grids.get('regular')
                    if g:
                        g.load_items(regular_items, max(len(regular_items), 42))
                        g.tab_label.setText('Regular Inventory')
                    g = self._inv_grids.get('key')
                    if g:
                        g.load_items(key_items, max(len(key_items), 42))
                        g.tab_label.setText('Key Items')
                    g = self._inv_grids.get('equipment')
                    if g:
                        for slot_name, slot_widget in self._equip_slots.items():
                            slot_widget.clear_item()
                        wsd_cont = wsd.get('ItemContainerSaveData', {}).get('value', [])
                        slot_map = {'weapon1': ('WeaponLoadOutContainerId', 0), 'weapon2': ('WeaponLoadOutContainerId', 1), 'weapon3': ('WeaponLoadOutContainerId', 2), 'weapon4': ('WeaponLoadOutContainerId', 3), 'weapon5': ('WeaponLoadOutContainerId', 4), 'weapon6': ('WeaponLoadOutContainerId', 5), 'head': ('PlayerEquipArmorContainerId', 0), 'body': ('PlayerEquipArmorContainerId', 1), 'shield': ('PlayerEquipArmorContainerId', 4), 'glider': ('PlayerEquipArmorContainerId', 5), 'sphere_mod': ('PlayerEquipArmorContainerId', 8), 'accessory1': ('PlayerEquipArmorContainerId', 2), 'accessory2': ('PlayerEquipArmorContainerId', 3), 'accessory3': ('PlayerEquipArmorContainerId', 6), 'accessory4': ('PlayerEquipArmorContainerId', 7), 'food1': ('FoodEquipContainerId', 0), 'food2': ('FoodEquipContainerId', 1), 'food3': ('FoodEquipContainerId', 2), 'food4': ('FoodEquipContainerId', 3), 'food5': ('FoodEquipContainerId', 4)}
                        equip_items = {}
                        for ct_name in ['WeaponLoadOutContainerId', 'PlayerEquipArmorContainerId', 'FoodEquipContainerId']:
                            cid_obj = inv_info.get(ct_name, {}).get('value', {}).get('ID', {})
                            cid = cid_obj.get('value', '') if isinstance(cid_obj, dict) else str(cid_obj)
                            cid_str = str(cid).replace('-', '').lower() if cid else ''
                            for cont in wsd_cont:
                                if str(cont.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() == cid_str:
                                    for si, slot in enumerate(cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])):
                                        rd = slot.get('RawData', {}).get('value', {})
                                        if not rd:
                                            continue
                                        item_info = rd.get('item', {})
                                        if not item_info:
                                            continue
                                        sid = item_info.get('static_id', '')
                                        if not sid:
                                            continue
                                        item_data = ItemData.get_item_by_asset(sid)
                                        equip_items[ct_name, si] = {'item_id': sid, 'item_name': item_data.get('name', sid), 'stack_count': rd.get('count', 1), 'icon_path': item_data.get('icon', '')}
                                    break
                        for slot_name, (ct, idx) in slot_map.items():
                            sw = self._equip_slots.get(slot_name)
                            if sw:
                                item_data = equip_items.get((ct, idx))
                                sw.set_item(item_data)
                    self._inv_grids['regular'].setVisible(True)
                    self._inv_grids['equipment'].setVisible(False)
                    self._inv_grids['key'].setVisible(False)
                    break
        except:
            pass
    def _on_container_clicked(self, container_data):
        cont_id = container_data.get('id_clean', '')
        if not constants.loaded_level_json:
            return
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            for cont in wsd.get('ItemContainerSaveData', {}).get('value', []):
                cid_check = cont.get('key', {}).get('ID', {}).get('value', '')
                if not cid_check:
                    continue
                if str(cid_check).replace('-', '').lower() != cont_id:
                    continue
                items = []
                for slot in cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
                    rd = slot.get('RawData', {}).get('value', {})
                    if not rd:
                        continue
                    item_info = rd.get('item', {})
                    if not item_info:
                        continue
                    static_id = item_info.get('static_id', '')
                    if not static_id:
                        continue
                    item_data = ItemData.get_item_by_asset(static_id)
                    items.append({'item_id': static_id, 'item_name': item_data.get('name', static_id), 'stack_count': rd.get('count', 1), 'icon_path': item_data.get('icon', '')})
                container_data['items'] = items
                break
        except:
            pass
        self._show_preview(container_data)
    def _show_preview(self, container_data):
        for i in reversed(range(self._preview_grid_layout.count())):
            w = self._preview_grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        ctype = get_container_type_display(container_data.get('slot_count', 0))
        sc = container_data.get('slot_count', 0)
        ic = container_data.get('item_count', 0)
        icon = get_container_icon(container_data.get('slot_count', 0))
        self._preview_header.setText(f'{icon} {ctype}')
        self._preview_info.setText(f"{sc} slots | {ic} items | {container_data.get('id', '')}")
        items = container_data.get('items', [])
        if items:
            for i, item in enumerate(items):
                r, c = divmod(i, GRID_COLS)
                slot = ItemSlotWidget(i, 'preview')
                slot.set_item(item)
                self._preview_grid_layout.addWidget(slot, r, c)
        else:
            empty = QLabel('No items')
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet('color: #555; font-style: italic; font-size: 14px; padding: 40px;')
            self._preview_grid_layout.addWidget(empty, 0, 0, 1, GRID_COLS)
    def _on_container_context_menu(self, container_data, pos):
        menu = QMenu(self)
        menu.setStyleSheet('QMenu { background-color: rgba(18, 20, 24, 0.95); border: 1px solid rgba(125, 211, 252, 0.3); border-radius: 4px; color: #e2e8f0; padding: 4px; } QMenu::item:selected { background-color: rgba(59, 142, 208, 0.3); }')
        view_action = menu.addAction(t('containers.view_contents'))
        menu.addSeparator()
        menu.addAction(t('container_selector.select_as_main'))
        menu.addAction(t('container_selector.select_as_key'))
        menu.addAction(t('container_selector.select_as_weapons'))
        menu.addAction(t('container_selector.select_as_armor'))
        menu.addAction(t('container_selector.select_as_food'))
        action = menu.exec_(pos)
        cont_id = container_data['id']
        if action == view_action:
            self._on_container_clicked(container_data)
        elif action:
            at = action.text()
            if at == t('container_selector.select_as_main'):
                self._select_container_for_slot('CommonContainerId', cont_id)
            elif at == t('container_selector.select_as_key'):
                self._select_container_for_slot('EssentialContainerId', cont_id)
            elif at == t('container_selector.select_as_weapons'):
                self._select_container_for_slot('WeaponLoadOutContainerId', cont_id)
            elif at == t('container_selector.select_as_armor'):
                self._select_container_for_slot('PlayerEquipArmorContainerId', cont_id)
            elif at == t('container_selector.select_as_food'):
                self._select_container_for_slot('FoodEquipContainerId', cont_id)
    def _select_container_for_slot(self, container_type, container_id):
        info = self.orphaned_containers_dict.get(container_id, {})
        ic = info.get('item_count', 0)
        sc = info.get('slot_count', 0)
        tn = get_container_type_display(sc)
        self.selected_containers[container_type] = container_id
        lbl = self.slot_labels.get(container_type)
        if lbl:
            lbl.setText(f'{tn}: {container_id[:8]}... ({ic} items)')
            lbl.setStyleSheet('font-size: 9px; color: #ffffff; font-weight: 600;')
        self._update_selection_display()
        self.update_btn.setEnabled(any((v is not None for v in self.selected_containers.values())))
        self._reload_inv_tab(container_type)
    def _reload_inv_tab(self, container_type):
        ct_to_tab = {'CommonContainerId': 'regular', 'EssentialContainerId': 'key', 'WeaponLoadOutContainerId': 'equipment', 'PlayerEquipArmorContainerId': 'equipment', 'FoodEquipContainerId': 'equipment'}
        tab_key = ct_to_tab.get(container_type)
        if not tab_key:
            return
        assigned_id = self.selected_containers.get(container_type)
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        items = {}
        if assigned_id:
            for cont in item_containers:
                if str(cont.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() == assigned_id.lower().replace('-', '').lower():
                    for idx, slot in enumerate(cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])):
                        rd = slot.get('RawData', {}).get('value', {})
                        if not rd:
                            continue
                        item_info = rd.get('item', {})
                        if not item_info:
                            continue
                        sid = item_info.get('static_id', '')
                        if not sid:
                            continue
                        item_data = ItemData.get_item_by_asset(sid)
                        items[idx] = {'item_id': sid, 'item_name': item_data.get('name', sid), 'stack_count': rd.get('count', 1), 'icon_path': item_data.get('icon', '')}
                    break
        if tab_key == 'equipment':
            ct_map = {'CommonContainerId': 'regular', 'EssentialContainerId': 'key', 'WeaponLoadOutContainerId': 'weapons', 'PlayerEquipArmorContainerId': 'armor', 'FoodEquipContainerId': 'foodbag'}
            for slot_name, slot_widget in self._equip_slots.items():
                slot_widget.clear_item()
            cont_key = ct_map.get(container_type, '')
            from ...inventory.inventory_manager import UI_SLOT_BINDINGS
            for binding in UI_SLOT_BINDINGS:
                if binding['container'] == cont_key:
                    idx = binding['index']
                    sw = self._equip_slots.get(binding['slot_name'])
                    if sw and idx in items:
                        sw.set_item(items[idx])
        else:
            g = self._inv_grids.get(tab_key)
            if g:
                item_list = sorted(items.values(), key=lambda x: x.get('slot_index', 0))
                g.load_items(item_list, max(len(item_list), 42))
    def _update_container_ids(self):
        container_ids = {ct: sid for ct, sid in self.selected_containers.items() if sid is not None}
        if not container_ids:
            QMessageBox.warning(self, 'Warning', 'Please select at least one container to update.')
            return
        from palworld_aio.managers.func_manager import update_player_container_ids
        success = update_player_container_ids(self.player_uid, container_ids)
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, 'Error', 'Failed to update container IDs.')
    def get_selected_container_ids(self):
        return self.selected_containers.copy()