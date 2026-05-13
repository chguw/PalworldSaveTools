import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QFrame, QMenu, QListWidget, QListWidgetItem, QComboBox, QApplication, QSplitter, QMessageBox, QWidget
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.inventory_manager import ItemData
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
from .container_ids_tab import ContainerSlotWidget, ContainerContentsDialog, get_container_type_display, get_container_icon
CONTAINER_TYPES = [('CommonContainerId', 'container_selector.slot_main', 'Main'), ('EssentialContainerId', 'container_selector.slot_key', 'Key'), ('WeaponLoadOutContainerId', 'container_selector.slot_weapons', 'Weapons'), ('PlayerEquipArmorContainerId', 'container_selector.slot_armor', 'Armor'), ('FoodEquipContainerId', 'container_selector.slot_food', 'Food')]
class ContainerSelectorDialog(QDialog):
    def __init__(self, player_uid, player_name, parent=None):
        super().__init__(parent)
        self.player_uid = player_uid
        self.player_name = player_name
        self.orphaned_containers = []
        self.container_widgets = {}
        self.selected_containers = {ct[0]: None for ct in CONTAINER_TYPES}
        self.slot_labels = {}
        self.setMinimumSize(1000, 600)
        self._setup_ui()
    def _setup_ui(self):
        self.setWindowTitle(t('container_selector.title', player_name=self.player_name))
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
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
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        instruction_label = QLabel(t('container_selector.instruction'))
        instruction_label.setStyleSheet('font-size: 12px; color: #e0e0e0; margin-bottom: 8px;')
        instruction_label.setWordWrap(True)
        left_layout.addWidget(instruction_label)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('font-size: 11px; color: #7dd3fc;')
        left_layout.addWidget(self.status_label)
        container_scroll = QScrollArea()
        container_scroll.setWidgetResizable(True)
        container_scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        container_scroll.setWidget(self.grid_widget)
        left_layout.addWidget(container_scroll)
        right_panel = QWidget()
        right_panel.setStyleSheet('background: rgba(20, 25, 35, 0.8); border-radius: 6px;')
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(8)
        right_title = QLabel(t('container_selector.assign_slots'))
        right_title.setStyleSheet('font-size: 14px; font-weight: bold; color: #ffffff; margin-bottom: 10px;')
        right_layout.addWidget(right_title)
        instruction = QLabel(t('container_selector.select_instruction'))
        instruction.setStyleSheet('font-size: 11px; color: #aaa; margin-bottom: 10px;')
        instruction.setWordWrap(True)
        right_layout.addWidget(instruction)
        self.slot_labels = {}
        for container_type, trans_key, display_name in CONTAINER_TYPES:
            slot_frame = QFrame()
            slot_frame.setStyleSheet('background: rgba(40, 45, 55, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px;')
            slot_layout = QHBoxLayout(slot_frame)
            slot_layout.setContentsMargins(10, 8, 10, 8)
            slot_layout.setSpacing(8)
            label = QLabel(t(trans_key))
            label.setStyleSheet('font-size: 11px; color: #e0e0e0; font-weight: 500;')
            slot_layout.addWidget(label)
            status_layout = QHBoxLayout()
            status_layout.setSpacing(8)
            status_label = QLabel(t('container_selector.auto_none'))
            status_label.setStyleSheet('font-size: 10px; color: #7dd3fc; font-weight: 500;')
            status_label.setMinimumWidth(200)
            status_label.setMaximumWidth(200)
            status_layout.addWidget(status_label)
            clear_btn = QPushButton('×')
            clear_btn.setFixedSize(20, 20)
            clear_btn.setStyleSheet('\n                QPushButton {\n                    background: rgba(255, 80, 80, 0.6);\n                    color: #ffffff;\n                    border: none;\n                    border-radius: 4px;\n                    font-size: 14px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background: rgba(255, 100, 100, 0.8);\n                }\n            ')
            clear_btn.clicked.connect(lambda ct=container_type: self._clear_slot(ct))
            clear_btn.setToolTip(t('container_selector.clear_slot'))
            status_layout.addWidget(clear_btn)
            slot_layout.addLayout(status_layout)
            right_layout.addWidget(slot_frame)
            self.slot_labels[container_type] = status_label
        right_layout.addStretch()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        main_layout.addWidget(splitter)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        self.update_btn = QPushButton(t('container_selector.update_btn'))
        self.update_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(74, 222, 128, 0.8);\n                color: #ffffff;\n                border: none;\n                border-radius: 6px;\n                padding: 10px 24px;\n                font-weight: 600;\n                font-size: 13px;\n            }\n            QPushButton:hover {\n                background: rgba(74, 222, 128, 1.0);\n            }\n            QPushButton:disabled {\n                background: rgba(100, 100, 100, 0.3);\n                color: rgba(255,255,255,0.3);\n            }\n        ')
        self.update_btn.clicked.connect(self._update_container_ids)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)
        cancel_btn = QPushButton(t('container_selector.cancel_btn'))
        cancel_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(255, 80, 80, 0.8);\n                color: #ffffff;\n                border: none;\n                border-radius: 6px;\n                padding: 10px 24px;\n                font-weight: 600;\n                font-size: 13px;\n            }\n            QPushButton:hover {\n                background: rgba(255, 80, 80, 1.0);\n            }\n        ')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        self.load_containers()
    def _clear_slot(self, container_type):
        container_info = self.orphaned_containers_dict.get(self.selected_containers.get(container_type), {})
        item_count = container_info.get('item_count', 0)
        slot_count = container_info.get('slot_count', 0)
        type_name = get_container_type_display(slot_count)
        self.selected_containers[container_type] = None
        slot_label = self.slot_labels.get(container_type)
        if slot_label:
            display_text = f'{type_name}: Auto'
            slot_label.setText(display_text)
            slot_label.setStyleSheet('font-size: 10px; color: #7dd3fc; font-weight: 500;')
        self._update_selection_display()
        has_selection = any((v is not None for v in self.selected_containers.values()))
        self.update_btn.setEnabled(has_selection)
    def _on_combo_changed(self, container_type, index):
        if index == 0:
            self.selected_containers[container_type] = None
        else:
            container_id = self.slot_combos[container_type].itemData(index)
            self.selected_containers[container_type] = container_id
        self._update_selection_display()
        has_selection = any((v is not None for v in self.selected_containers.values()))
        self.update_btn.setEnabled(has_selection)
    def _update_selection_display(self):
        for container_id, widget in self.container_widgets.items():
            widget.setStyleSheet(self._get_container_style(container_id))
    def _get_container_style(self, container_id, is_selected=False):
        container_info = self.orphaned_containers_dict.get(container_id, {})
        item_count = container_info.get('item_count', 0)
        slot_count = container_info.get('slot_count', 0)
        if item_count > 0:
            border_color = 'rgba(74, 222, 128, 0.5)'
            bg_color = 'rgba(30, 40, 35, 0.9)'
        else:
            border_color = 'rgba(255, 255, 255, 0.15)'
            bg_color = 'rgba(30, 35, 45, 0.8)'
        style = f'\n            ContainerSlotWidget {{\n                background-color: {bg_color};\n                border: 1px solid {border_color};\n                border-radius: 6px;\n            }}\n            ContainerSlotWidget:hover {{\n                background-color: rgba(50, 60, 70, 0.9);\n                border: 1px solid rgba(125, 211, 252, 0.4);\n            }}\n        '
        return style
    def load_containers(self):
        for widget in self.container_widgets.values():
            widget.deleteLater()
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
                        cont_id_clean = str(cont_id).replace('-', '').lower()
                        container_id_counts[cont_id_clean] += 1
                except:
                    pass
            all_referenced_ids = set()
            char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
            for entry in char_map:
                try:
                    save_param_val = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    slot_id = save_param_val.get('SlotId', {})
                    slot_val = slot_id.get('value', {})
                    container_id_obj = slot_val.get('ContainerId', {})
                    container_id_val = container_id_obj.get('value', {})
                    container_id = container_id_val.get('ID', {})
                    if container_id:
                        all_referenced_ids.add(str(container_id.get('value', '')).replace('-', '').lower())
                except:
                    pass
            char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
            for cc in char_containers:
                try:
                    cont_id = cc.get('key', {}).get('ID', {}).get('value', '')
                    if cont_id:
                        all_referenced_ids.add(str(cont_id).replace('-', '').lower())
                except:
                    pass
            group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
            for group in group_data_list:
                try:
                    raw = group.get('value', {}).get('RawData', {}).get('value', {})
                    for key in ['worker_character_handle_ids', 'individual_character_handle_ids']:
                        if key in raw:
                            for handle in raw[key]:
                                if 'ContainerId' in handle:
                                    cid = handle['ContainerId'].get('ID', {}).get('value', '')
                                    if cid:
                                        all_referenced_ids.add(str(cid).replace('-', '').lower())
                except:
                    pass
            self.orphaned_containers_dict = {}
            for cont in item_containers:
                try:
                    cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                    if not cont_id:
                        continue
                    cont_id_clean = str(cont_id).replace('-', '').lower()
                    if cont_id_clean in all_referenced_ids:
                        continue
                    slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    slot_count = len(slots)
                    item_count = 0
                    for slot in slots:
                        raw_data = slot.get('RawData', {}).get('value', {})
                        if raw_data:
                            item_info = raw_data.get('item', {})
                            if item_info and item_info.get('static_id'):
                                item_count += 1
                    if item_count == 0:
                        continue
                    appears_once = container_id_counts.get(cont_id_clean, 0) == 1
                    container_info = {'id': str(cont_id), 'id_clean': cont_id_clean, 'slot_count': slot_count, 'item_count': item_count, 'items': [], 'appears_once': appears_once}
                    self.orphaned_containers.append(container_info)
                    self.orphaned_containers_dict[cont_id_clean] = container_info
                except Exception as e:
                    continue
            self.orphaned_containers.sort(key=lambda x: (-x['slot_count'], -x['item_count']))
            row = 0
            col = 0
            max_cols = 1
            for container_info in self.orphaned_containers:
                widget = ContainerSlotWidget(container_info)
                widget.clicked.connect(self._on_container_clicked)
                widget.context_menu_requested.connect(self._on_container_context_menu)
                self.grid_layout.addWidget(widget, row, col)
                self.container_widgets[container_info['id_clean']] = widget
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            self.status_label.setText(t('container_selector.found_containers', count=len(self.orphaned_containers)))
        except Exception as e:
            self.status_label.setText(f'Error: {str(e)}')
    def _on_container_clicked(self, container_data):
        pass
    def _on_container_context_menu(self, container_data, pos):
        menu = QMenu(self)
        menu.setStyleSheet('\n            QMenu {\n                background-color: rgba(18, 20, 24, 0.95);\n                border: 1px solid rgba(125, 211, 252, 0.3);\n                border-radius: 4px;\n                color: #e2e8f0;\n                padding: 4px;\n            }\n            QMenu::item:selected {\n                background-color: rgba(59, 142, 208, 0.3);\n            }\n        ')
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
            self._show_container_contents(container_data)
        elif action:
            action_text = action.text()
            if action_text == t('container_selector.select_as_main'):
                self._select_container_for_slot('CommonContainerId', cont_id)
            elif action_text == t('container_selector.select_as_key'):
                self._select_container_for_slot('EssentialContainerId', cont_id)
            elif action_text == t('container_selector.select_as_weapons'):
                self._select_container_for_slot('WeaponLoadOutContainerId', cont_id)
            elif action_text == t('container_selector.select_as_armor'):
                self._select_container_for_slot('PlayerEquipArmorContainerId', cont_id)
            elif action_text == t('container_selector.select_as_food'):
                self._select_container_for_slot('FoodEquipContainerId', cont_id)
    def _select_container_for_slot(self, container_type, container_id):
        container_info = self.orphaned_containers_dict.get(container_id, {})
        item_count = container_info.get('item_count', 0)
        slot_count = container_info.get('slot_count', 0)
        type_name = get_container_type_display(slot_count)
        self.selected_containers[container_type] = container_id
        slot_label = self.slot_labels.get(container_type)
        if slot_label:
            display_text = f'{type_name}: {container_id[:8]}... ({item_count} items)'
            slot_label.setText(display_text)
            slot_label.setStyleSheet('font-size: 10px; color: #ffffff; font-weight: 600;')
        self._update_selection_display()
        has_selection = any((v is not None for v in self.selected_containers.values()))
        self.update_btn.setEnabled(has_selection)
    def _show_container_contents(self, container_data):
        cont_id = container_data.get('id_clean', '')
        if not constants.loaded_level_json:
            return
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            for cont in item_containers:
                cont_id_check = cont.get('key', {}).get('ID', {}).get('value', '')
                if not cont_id_check:
                    continue
                cont_id_clean = str(cont_id_check).replace('-', '').lower()
                if cont_id_clean != cont_id:
                    continue
                slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                items = []
                for slot in slots:
                    raw_data = slot.get('RawData', {}).get('value', {})
                    if not raw_data:
                        continue
                    item_info = raw_data.get('item', {})
                    if not item_info:
                        continue
                    static_id = item_info.get('static_id', '')
                    if not static_id:
                        continue
                    count = raw_data.get('count', 1)
                    item_data = ItemData.get_item_by_asset(static_id)
                    items.append({'item_id': static_id, 'item_name': item_data.get('name', static_id), 'stack_count': count, 'icon_path': item_data.get('icon', '')})
                container_data['items'] = items
                break
        except:
            pass
        dialog = ContainerContentsDialog(container_data, self)
        dialog.exec()
    def _update_container_ids(self):
        container_ids = {}
        for container_type, selected_id in self.selected_containers.items():
            if selected_id is not None:
                container_ids[container_type] = selected_id
        if not container_ids:
            QMessageBox.warning(self, 'Warning', 'Please select at least one container to update.')
            return
        from palworld_aio.func_manager import update_player_container_ids
        success = update_player_container_ids(self.player_uid, container_ids)
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, 'Error', 'Failed to update container IDs.')
    def get_selected_container_ids(self):
        return self.selected_containers.copy()