import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QFrame, QMenu, QDialog, QListWidget, QListWidgetItem, QCheckBox, QMessageBox, QApplication, QLineEdit
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QPixmap, QCursor, QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.ui.styles import PICKER_SEARCH_STYLE
from palworld_aio.inventory_manager import ItemData
from palworld_aio.ui.inventory_tab import ItemSlotWidget, GRID_COLS
CONTAINER_TYPE_MAP = {4: 'WeaponLoadOutContainerId', 6: 'WeaponLoadOutContainerId', 9: 'PlayerEquipArmorContainerId', 5: 'FoodEquipContainerId', 42: 'CommonContainerId'}
def get_container_type_display(slot_count):
    if slot_count in (4, 6):
        return 'Weapons'
    elif slot_count == 9:
        return 'Armor'
    elif slot_count == 5:
        return 'Food'
    elif slot_count >= 42:
        return 'Main Inventory'
    else:
        return f'Container ({slot_count} slots)'
def get_container_icon(slot_count):
    if slot_count in (4, 6):
        return '⚔️'
    elif slot_count == 9:
        return '🛡️'
    elif slot_count == 5:
        return '🍖'
    elif slot_count >= 42:
        return '🎒'
    else:
        return '📦'
class ContainerSlotWidget(QFrame):
    clicked = Signal(dict)
    context_menu_requested = Signal(dict, QPoint)
    def __init__(self, container_data: dict, parent=None):
        super().__init__(parent)
        self.container_data = container_data
        self.setFixedSize(280, 100)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        header_layout = QHBoxLayout()
        icon_label = QLabel(get_container_icon(self.container_data.get('slot_count', 0)))
        icon_label.setStyleSheet('font-size: 20px;')
        header_layout.addWidget(icon_label)
        type_label = QLabel(get_container_type_display(self.container_data.get('slot_count', 0)))
        type_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #ffffff;')
        header_layout.addWidget(type_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        id_label = QLabel(self.container_data.get('id', ''))
        id_label.setStyleSheet('font-size: 9px; color: #999999; font-family: monospace;')
        id_label.setWordWrap(True)
        layout.addWidget(id_label)
        stats_layout = QHBoxLayout()
        slots_text = f"Slots: {self.container_data.get('slot_count', 0)}"
        slots_label = QLabel(slots_text)
        slots_label.setStyleSheet('font-size: 10px; color: #aaaaaa;')
        stats_layout.addWidget(slots_label)
        item_count = self.container_data.get('item_count', 0)
        items_text = f'Items: {item_count}'
        items_label = QLabel(items_text)
        if item_count > 0:
            items_label.setStyleSheet('font-size: 10px; font-weight: bold; color: #4ade80;')
        else:
            items_label.setStyleSheet('font-size: 10px; color: #666666;')
        stats_layout.addWidget(items_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        self._apply_style()
    def _apply_style(self):
        item_count = self.container_data.get('item_count', 0)
        if item_count > 0:
            border_color = 'rgba(74, 222, 128, 0.5)'
            bg_color = 'rgba(30, 40, 35, 0.9)'
        else:
            border_color = 'rgba(255, 255, 255, 0.15)'
            bg_color = 'rgba(30, 35, 45, 0.8)'
        self.setStyleSheet(f'\n            ContainerSlotWidget {{\n                background-color: {bg_color};\n                border: 1px solid {border_color};\n                border-radius: 6px;\n            }}\n            ContainerSlotWidget:hover {{\n                background-color: rgba(50, 60, 70, 0.9);\n                border: 1px solid rgba(125, 211, 252, 0.4);\n            }}\n        ')
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.container_data)
        super().mousePressEvent(event)
    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(self.container_data, event.globalPos())
class ContainerContentsDialog(QDialog):
    def __init__(self, container_data: dict, parent=None):
        super().__init__(parent)
        self.container_data = container_data
        cid = container_data.get('id', '')
        self.setWindowTitle(f"Container Contents - {cid[:8]}...")
        self.setMinimumSize(600, 500)
        self.setStyleSheet('\n            QDialog {\n                background-color: rgba(18, 20, 24, 0.95);\n                border: 1px solid rgba(125, 211, 252, 0.2);\n            }\n        ')
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        header = QHBoxLayout()
        icon_label = QLabel(get_container_icon(self.container_data.get('slot_count', 0)))
        icon_label.setStyleSheet('font-size: 24px;')
        header.addWidget(icon_label)
        info_text = f"<b>{get_container_type_display(self.container_data.get('slot_count', 0))}</b> | {self.container_data.get('slot_count', 0)} slots | {self.container_data.get('item_count', 0)} items"
        info_label = QLabel(info_text)
        info_label.setStyleSheet('font-size: 13px; color: #e2e8f0;')
        header.addWidget(info_label)
        header.addStretch()
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #aaa; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; font-size: 14px; } QPushButton:hover { background: rgba(255,80,80,0.2); color: #ff6b6b; }')
        close_btn.clicked.connect(self.accept)
        header.addWidget(close_btn)
        layout.addLayout(header)
        cid_label = QLabel(self.container_data.get('id', ''))
        cid_label.setStyleSheet('font-size: 10px; color: #666; font-family: monospace; padding-left: 4px;')
        layout.addWidget(cid_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)
        items = self.container_data.get('items', [])
        if items:
            for i, item in enumerate(items):
                row = i // GRID_COLS
                col = i % GRID_COLS
                slot = ItemSlotWidget(i, 'container')
                slot.set_item(item)
                self.grid_layout.addWidget(slot, row, col)
        else:
            empty = QLabel('No items in this container')
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet('color: #555; font-style: italic; font-size: 14px; padding: 40px;')
            self.grid_layout.addWidget(empty, 0, 0, 1, GRID_COLS)
class _InlineContainerPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self._current_container_id = None
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        header = QHBoxLayout()
        self._icon_label = QLabel()
        self._icon_label.setStyleSheet('font-size: 20px;')
        header.addWidget(self._icon_label)
        self._info_label = QLabel()
        self._info_label.setStyleSheet('font-size: 12px; color: #e2e8f0; font-weight: bold;')
        header.addWidget(self._info_label)
        header.addStretch()
        self._container_id_label = QLabel()
        self._container_id_label.setStyleSheet('font-size: 9px; color: #666; font-family: monospace;')
        header.addWidget(self._container_id_label)
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #aaa; border: 1px solid rgba(255,255,255,0.1); border-radius: 11px; font-size: 12px; } QPushButton:hover { background: rgba(255,80,80,0.2); color: #ff6b6b; }')
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setFixedHeight(220)
        grid_widget = QWidget()
        self._grid_layout = QGridLayout(grid_widget)
        self._grid_layout.setHorizontalSpacing(2)
        self._grid_layout.setVerticalSpacing(4)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)
        self.setStyleSheet('_InlineContainerPanel { background: rgba(18, 20, 24, 0.8); border: 1px solid rgba(125, 211, 252, 0.2); border-radius: 8px; }')
    def show_container(self, container_data: dict):
        self._current_container_id = container_data.get('id', '')
        self._icon_label.setText(get_container_icon(container_data.get('slot_count', 0)))
        self._info_label.setText(f"{get_container_type_display(container_data.get('slot_count', 0))} | {container_data.get('slot_count', 0)} slots | {container_data.get('item_count', 0)} items")
        self._container_id_label.setText(container_data.get('id', ''))
        for i in reversed(range(self._grid_layout.count())):
            w = self._grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        items = container_data.get('items', [])
        if items:
            for i, item in enumerate(items):
                row = i // GRID_COLS
                col = i % GRID_COLS
                slot = ItemSlotWidget(i, 'container')
                slot.set_item(item)
                self._grid_layout.addWidget(slot, row, col)
        else:
            empty = QLabel('No items in this container')
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet('color: #555; font-style: italic; font-size: 13px; padding: 20px;')
            self._grid_layout.addWidget(empty, 0, 0, 1, GRID_COLS)
        self.setVisible(True)
class UnassignedContainersTab(QWidget):
    container_selected = Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.containers = []
        self.container_widgets = {}
        self.containers_dict = {}
        self.matching_containers = set()
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        header_layout = QHBoxLayout()
        title_label = QLabel(t('containers.tab_title') if t else 'Unassigned Containers')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #ffffff;')
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.show_items_only_checkbox = QCheckBox(t('containers.show_items_only') if t else 'Show only containers with items')
        self.show_items_only_checkbox.setStyleSheet('color: #e0e0e0;')
        self.show_items_only_checkbox.stateChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.show_items_only_checkbox)
        self.show_once_only_checkbox = QCheckBox(t('containers.show_once_only') if t else 'Show only appearing once')
        self.show_once_only_checkbox.setStyleSheet('color: #e0e0e0;')
        self.show_once_only_checkbox.stateChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.show_once_only_checkbox)
        refresh_btn = QPushButton(t('containers.refresh') if t else 'Refresh')
        refresh_btn.setFixedSize(80, 28)
        refresh_btn.clicked.connect(self.load_containers)
        header_layout.addWidget(refresh_btn)
        search_label = QLabel(t('containers.search') if t else 'Search:')
        search_label.setStyleSheet('color: #e0e0e0;')
        header_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('containers.search_placeholder') if t else 'Search items...')
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet(PICKER_SEARCH_STYLE)
        self.search_input.returnPressed.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        search_btn = QPushButton(t('containers.search_btn') if t else 'Search')
        search_btn.setFixedSize(70, 28)
        search_btn.clicked.connect(self._on_search)
        header_layout.addWidget(search_btn)
        main_layout.addLayout(header_layout)
        self._inline_panel = _InlineContainerPanel()
        main_layout.addWidget(self._inline_panel)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        scroll.setWidget(self.grid_widget)
        main_layout.addWidget(scroll)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('font-size: 11px; color: #888888;')
        main_layout.addWidget(self.status_label)
    def _on_filter_changed(self):
        self._apply_filter()
    def _on_search(self):
        query = self.search_input.text().strip().lower()
        if not query:
            self._apply_filter()
            return
        if not constants.loaded_level_json:
            return
        self.status_label.setText(t('containers.searching') if t else 'Searching...')
        QApplication.processEvents()
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            matching_container_ids = set()
            for cont in item_containers:
                try:
                    cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                    if not cont_id:
                        continue
                    cont_id_clean = str(cont_id).replace('-', '').lower()
                    if cont_id_clean in self.containers_dict:
                        slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
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
                            item_data = ItemData.get_item_by_asset(static_id)
                            item_name = item_data.get('name', '').lower()
                            if query in item_name or query in static_id.lower():
                                matching_container_ids.add(cont_id_clean)
                                break
                except:
                    continue
            self.matching_containers = matching_container_ids
            self._apply_filter()
        except Exception as e:
            self.status_label.setText(f'Search error: {str(e)}')
    def _apply_filter(self):
        show_items_only = self.show_items_only_checkbox.isChecked()
        show_once_only = self.show_once_only_checkbox.isChecked()
        query = self.search_input.text().strip().lower()
        has_search = bool(query)
        for cont_id, widget in self.container_widgets.items():
            container_info = self.containers_dict.get(cont_id, {})
            item_count = container_info.get('item_count', 0)
            appears_once = container_info.get('appears_once', False)
            visible = True
            if show_items_only and item_count == 0:
                visible = False
            if show_once_only and (not appears_once):
                visible = False
            if has_search and cont_id not in self.matching_containers:
                visible = False
            widget.setVisible(visible)
        visible_count = sum((1 for w in self.container_widgets.values() if w.isVisible()))
        self.status_label.setText(f'Showing {visible_count} of {len(self.containers)} containers')
    def load_containers(self):
        for widget in self.container_widgets.values():
            widget.deleteLater()
        self.container_widgets.clear()
        self.containers = []
        self.containers_dict = {}
        if not constants.loaded_level_json:
            self.status_label.setText(t('containers.no_save_loaded') if t else 'No save loaded')
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
            char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
            for cc in char_containers:
                try:
                    cont_id = cc.get('key', {}).get('ID', {}).get('value', '')
                    if cont_id:
                        all_referenced_ids.add(str(cont_id).replace('-', '').lower())
                except:
                    pass
            guild_item_storages = wsd.get('GuildItemStorageSaveData', {}).get('value', {})
            if isinstance(guild_item_storages, dict):
                for g in guild_item_storages.get('values', []):
                    try:
                        storage = g.get('RawData', {}).get('value', {})
                        container_id = storage.get('container_id', {}).get('value', {}).get('ID', {})
                        if container_id:
                            cont_id = str(container_id).replace('-', '').lower()
                            if cont_id:
                                all_referenced_ids.add(cont_id)
                    except:
                        pass
            char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
            for entry in char_map:
                try:
                    save_param_val = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    slot_id = save_param_val.get('SlotId', {})
                    slot_val = slot_id.get('value', {})
                    container_id_obj = slot_val.get('ContainerId', {})
                    container_id_val = container_id_obj.get('value', {})
                    container_id = container_id_val.get('ID', {})
                    cont_id = container_id.get('value', '')
                    if cont_id:
                        all_referenced_ids.add(str(cont_id).replace('-', '').lower())
                except:
                    pass
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
                        if not raw_data:
                            continue
                        item_info = raw_data.get('item', {})
                        if item_info and item_info.get('static_id'):
                            item_count += 1
                    appears_once = container_id_counts.get(cont_id_clean, 0) == 1
                    container_info = {'id': str(cont_id), 'id_clean': cont_id_clean, 'slot_count': slot_count, 'item_count': item_count, 'items': [], 'appears_once': appears_once}
                    self.containers.append(container_info)
                    self.containers_dict[cont_id_clean] = container_info
                except Exception as e:
                    continue
            self.containers.sort(key=lambda x: (-x['slot_count'], -x['item_count']))
            row = 0
            col = 0
            max_cols = 4
            for container_info in self.containers:
                widget = ContainerSlotWidget(container_info)
                widget.clicked.connect(self._on_container_clicked)
                widget.context_menu_requested.connect(self._on_container_context_menu)
                self.grid_layout.addWidget(widget, row, col)
                self.container_widgets[container_info['id_clean']] = widget
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            self._apply_filter()
        except Exception as e:
            self.status_label.setText(f'Error loading containers: {str(e)}')
    def _on_container_clicked(self, container_data):
        self.container_selected.emit(container_data)
        cont_id = container_data.get('id_clean', '')
        if not constants.loaded_level_json:
            return
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            for cont in item_containers:
                cid_check = cont.get('key', {}).get('ID', {}).get('value', '')
                if not cid_check:
                    continue
                cid_clean = str(cid_check).replace('-', '').lower()
                if cid_clean != cont_id:
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
        self._inline_panel.show_container(container_data)
    def _on_container_context_menu(self, container_data, pos):
        menu = QMenu(self)
        menu.setStyleSheet('\n            QMenu {\n                background-color: rgba(18, 20, 24, 0.95);\n                border: 1px solid rgba(125, 211, 252, 0.3: 4px);\n                border-radius;\n                color: #e2e8f0;\n                padding: 4px;\n            }\n            QMenu::item:selected {\n                background-color: rgba(59, 142, 208, 0.3);\n            }\n        ')
        view_action = menu.addAction(t('containers.view_contents') if t else 'View Contents')
        copy_action = menu.addAction(t('containers.copy_id') if t else 'Copy Container ID')
        action = menu.exec_(pos)
        if action == view_action:
            self._on_container_clicked(container_data)
        elif action == copy_action:
            cont_id = container_data.get('id', '')
        clipboard = QApplication.clipboard()
        clipboard.setText(cont_id)
        QMessageBox.information(self, t('containers.copied') if t else 'Copied', t('containers.id_copied') if t else f'Container ID copied to clipboard:\n{cont_id}')