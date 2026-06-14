import os
import sys
from functools import partial
from palsav import json_tools
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QScrollArea, QGridLayout, QGroupBox, QMenu, QHeaderView, QMessageBox, QFileDialog, QInputDialog, QDialog, QCheckBox, QSpinBox, QDoubleSpinBox, QSizePolicy, QAbstractItemView, QSpacerItem, QTabWidget, QTabBar, QStyleOptionTab, QStyle, QApplication, QStyledItemDelegate, QListWidget, QListWidgetItem, QLineEdit, QListView, QStackedWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint, QRect, QEvent, QMargins, QThread
from PySide6.QtGui import QPixmap, QIcon, QFont, QAction, QCursor, QPainter, QColor, QBrush, QPen, QLinearGradient, QPalette, QMouseEvent, QWheelEvent, QResizeEvent, QPaintEvent, QContextMenuEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QDrag
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import QMimeData
from boot_paths import RESOURCES_DIR
_resources_path = str(RESOURCES_DIR)
if _resources_path not in sys.path:
    sys.path.insert(0, _resources_path)
from i18n import t
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from palworld_aio.base_inventory_manager import BaseInventoryManager, get_container_image_path, find_item_locations_efficient
from palworld_aio.widgets import StatsPanel
from palworld_aio.ui.inventory_tab import InventoryGridWidget, ItemPickerDialog, InventoryLoadoutDialog, _group_inventory_items, _consolidate_container_slots, SINGLETON_TYPE_A
from resource_resolver import resource_path
from palworld_aio.ui.styled_combo import StyledCombo
from palworld_aio.utils import format_duration_short
from i18n import t
from palworld_aio.inventory_manager import ItemData
from palworld_aio.ui.styles import MENU_STYLE, DIALOG_STYLE as _DIALOG_STYLE, INPUT_DIALOG_STYLE, PICKER_SEARCH_STYLE, wrap_tooltip_text, CONTENT_PANEL_STYLE, slot_full, slot_selected
from palworld_aio.edit_pals import _clean_desc_for_tooltip, build_pal_context_menu, _get_cached_pixmap, _get_pal_icon_path, safe_nested_get, extract_value, resolve_name, get_pal_base_data, _resolve_partner_desc, _partner_desc_to_html, StrokedLabel, _get_element_pixmap, PalFrame, _strip_prefix_label, PalInfoWidget, _get_boss_alpha_pixmap, _get_boss_shiny_pixmap, _get_awake_pixmap, _get_ui_icon_pixmap, _generate_pal_save_param, _toggle_boss_raw, _toggle_lucky_raw, _toggle_awake_raw, _toggle_dna_raw, _set_fav_raw, _learn_all_skills_raw, _show_learned_moves_dialog, _register_pal_instance_to_guild
from palworld_aio.base_inventory_manager import get_base_worker_pals
class RarityBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        rarity = index.data(Qt.UserRole + 2)
        if rarity is None:
            return
        if rarity <= 0:
            color = QColor('#aaaaaa')
        elif rarity <= 1:
            color = QColor('#4ade80')
        elif rarity <= 2:
            color = QColor('#60a5fa')
        elif rarity <= 3:
            color = QColor('#a855f7')
        else:
            color = QColor('#fbbf24')
        painter.save()
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        rect = option.rect.adjusted(4, 4, -4, -4)
        painter.drawRoundedRect(rect, 4, 4)
        painter.restore()
class GuildItemPickerDialog(QDialog):
    item_action_selected = Signal(str, str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('base_inventory.select_item_action') if t else 'Item Actions')
        self.setMinimumSize(1200, 650)
        self.selected_item_id = None
        self.selected_item_name = None
        self.guild_locations = {}
        self.guild_item_counts = {}
        self.setStyleSheet(_DIALOG_STYLE)
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        search_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('base_inventory.search_items') if t else 'Type to search items...')
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(48, 48))
        self.results_list.setSpacing(0)
        self.results_list.setUniformItemSizes(True)
        self.results_list.setGridSize(QSize(80, 80))
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_list.setItemDelegate(RarityBorderDelegate(self.results_list))
        self.results_list.setDragEnabled(False)
        self.results_list.viewport().setAcceptDrops(False)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.itemDoubleClicked.connect(self._on_find_containers)
        left_layout.addWidget(self.results_list)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        info_frame = QFrame()
        info_frame.setStyleSheet('background: rgba(0,0,0,0.15); border-radius: 4px;')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(5, 2, 5, 2)
        info_layout.setSpacing(0)
        self.info_label = QLabel(t('base_inventory.select_item') if t else 'Select an item to perform actions')
        self.info_label.setStyleSheet('color: #888; font-style: italic; padding: 2px;')
        info_layout.addWidget(self.info_label)
        self.code_label = QLabel('')
        self.code_label.setStyleSheet('color: #6b7280; font-size: 10px; font-family: monospace; padding: 0 2px;')
        self.code_label.setVisible(False)
        info_layout.addWidget(self.code_label)
        self.desc_label = QLabel('')
        self.desc_label.setStyleSheet('color: #94a3b8; font-size: 11px; padding: 0 2px;')
        self.desc_label.setWordWrap(True)
        self.desc_label.setVisible(False)
        info_layout.addWidget(self.desc_label)
        right_layout.addWidget(info_frame, 3)
        guilds_group = QGroupBox(t('base_inventory.select_guilds') if t else 'Select Guilds')
        guilds_inner_layout = QVBoxLayout()
        guild_buttons_layout = QHBoxLayout()
        guild_buttons_layout.setSpacing(5)
        self.select_all_btn = QPushButton(t('base_inventory.select_all_guilds') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_guilds)
        self.select_all_btn.setEnabled(False)
        self.deselect_all_btn = QPushButton(t('base_inventory.deselect_all_guilds') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_guilds)
        self.deselect_all_btn.setEnabled(False)
        self.remove_btn = QPushButton(t('base_inventory.remove_item_btn') if t else 'Remove Item')
        self.remove_btn.clicked.connect(self._on_remove_item)
        self.remove_btn.setEnabled(False)
        guild_buttons_layout.addWidget(self.select_all_btn)
        guild_buttons_layout.addWidget(self.deselect_all_btn)
        guild_buttons_layout.addWidget(self.remove_btn)
        guild_buttons_layout.addStretch()
        guilds_inner_layout.addLayout(guild_buttons_layout)
        self.guild_list = QListWidget()
        self.guild_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.guild_list.setEnabled(False)
        guilds_inner_layout.addWidget(self.guild_list)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('background: rgba(255,255,255,0.1); max-height: 1px; margin: 4px 0;')
        guilds_inner_layout.addWidget(sep)
        stats_container = QWidget()
        stats_container_layout = QHBoxLayout(stats_container)
        stats_container_layout.setContentsMargins(0, 2, 0, 0)
        stats_container_layout.setSpacing(8)
        self.stats_total_label = QLabel(f"{(t('base_inventory.total') if t else 'Total')}: 0")
        self.stats_total_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        stats_container_layout.addWidget(self.stats_total_label)
        self.stats_guilds_label = QLabel(f"{(t('base_inventory.guilds') if t else 'Guilds')}: 0")
        self.stats_guilds_label.setStyleSheet('font-size: 12px;')
        stats_container_layout.addWidget(self.stats_guilds_label)
        self.stats_avg_label = QLabel(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: 0.0")
        self.stats_avg_label.setStyleSheet('font-size: 12px;')
        stats_container_layout.addWidget(self.stats_avg_label)
        stats_container_layout.addStretch()
        guilds_inner_layout.addWidget(stats_container)
        guilds_group.setLayout(guilds_inner_layout)
        right_layout.addWidget(guilds_group, 7)
        btn_layout = QHBoxLayout()
        self.find_btn = QPushButton(t('base_inventory.find_containers') if t else 'Find Containers')
        self.find_btn.clicked.connect(self._on_find_containers)
        self.find_btn.setEnabled(False)
        btn_layout.addWidget(self.find_btn)
        btn_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        right_layout.addLayout(btn_layout)
        content_layout.addWidget(left_widget, 3)
        content_layout.addWidget(right_widget, 2)
        layout.addLayout(content_layout)
        items = ItemData.get_all_items()
        for item in items:
            if item.get('sort_id', 0) == 9999:
                continue
            if item['asset'].startswith('PalEgg_') or item['asset'].startswith('YakushimaParts'):
                continue
            name = item.get('name', 'Unknown')
            asset = item.get('asset', '')
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, asset)
            list_item.setData(Qt.UserRole + 1, name)
            list_item.setData(Qt.UserRole + 2, item.get('rarity', 0))
            list_item.setData(Qt.UserRole + 3, item.get('description', ''))
            item_desc = item.get('description', '')
            tip = f'<b>{name}</b><br>({asset})'
            if item_desc:
                cleaned = _clean_desc_for_tooltip(item_desc)
                tip += f'<br><br>{wrap_tooltip_text(cleaned)}'
            list_item.setToolTip(tip)
            icon_path = item.get('icon', '')
            if icon_path:
                pixmap = ItemData.get_item_icon(icon_path, QSize(48, 48))
                if not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap))
            list_item.setSizeHint(QSize(80, 80))
            self.results_list.addItem(list_item)
    def _filter_items(self, query: str):
        q = query.lower()
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            name = item.text()
            asset = item.data(Qt.UserRole) or ''
            item.setHidden(bool(q and q not in name.lower() and (q not in asset.lower())))
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item_id = item.data(Qt.UserRole)
        self.selected_item_name = item.data(Qt.UserRole + 1)
        item_desc = item.data(Qt.UserRole + 3) or ''
        self.info_label.setText(self.selected_item_name)
        self.info_label.setStyleSheet('color: #4ade80; font-weight: bold; font-size: 13px; padding: 2px;')
        self.code_label.setText(self.selected_item_id)
        self.code_label.setVisible(True)
        if item_desc:
            self.desc_label.setText(_clean_desc_for_tooltip(item_desc))
            self.desc_label.setVisible(True)
        else:
            self.desc_label.setVisible(False)
        self.find_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self._load_guilds_for_item()
    def _load_guilds_for_item(self):
        self.guild_list.clear()
        self.guild_locations = {}
        self.guild_item_counts = {}
        if not self.selected_item_id:
            return
        try:
            from palworld_aio.base_inventory_manager import find_item_locations_efficient, get_item_economy_stats
            item_locations = find_item_locations_efficient(self.selected_item_id)
            stats = get_item_economy_stats(self.selected_item_id)
            if stats:
                guild_details = stats.get('guild_details', [])
                for gd in guild_details:
                    guild_id = gd.get('guild_id', '')
                    count = gd.get('count', 0)
                    if guild_id:
                        self.guild_item_counts[guild_id] = count
            if item_locations:
                base_guild_lookup = constants.base_guild_lookup
                for guild_id_normalized, bases in item_locations.items():
                    guild_name = 'Unknown Guild'
                    for gid, ginfo in base_guild_lookup.items():
                        if str(ginfo.get('GuildID', '')).replace('-', '').lower() == guild_id_normalized:
                            guild_name = ginfo.get('GuildName', 'Unknown Guild')
                            break
                    self.guild_locations[guild_id_normalized] = {'name': guild_name, 'bases': bases}
                    count = self.guild_item_counts.get(guild_id_normalized, 0)
                    display_text = f'{guild_name}: {count}'
                    list_item = QListWidgetItem(display_text)
                    list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                    list_item.setCheckState(Qt.Checked)
                    list_item.setData(Qt.UserRole, guild_id_normalized)
                    self.guild_list.addItem(list_item)
                self.guild_list.setEnabled(True)
                self.select_all_btn.setEnabled(True)
                self.deselect_all_btn.setEnabled(True)
                total = stats.get('total_count', 0) if stats else 0
                guilds = stats.get('guilds_with_item', 0) if stats else 0
                avg = stats.get('avg_per_guild', 0.0) if stats else 0.0
                self.stats_total_label.setText(f"{(t('base_inventory.total') if t else 'Total')}: {total}")
                self.stats_guilds_label.setText(f"{(t('base_inventory.guilds') if t else 'Guilds')}: {guilds}")
                self.stats_avg_label.setText(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: {avg:.1f}")
            else:
                self.guild_list.addItem(t('base_inventory.no_guilds') if t else 'No guilds found with this item')
                self.guild_list.setEnabled(False)
                self.select_all_btn.setEnabled(False)
                self.deselect_all_btn.setEnabled(False)
                self.stats_total_label.setText(f"{(t('base_inventory.total') if t else 'Total')}: 0")
                self.stats_guilds_label.setText(f"{(t('base_inventory.guilds') if t else 'Guilds')}: 0")
                self.stats_avg_label.setText(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: 0.0")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.guild_list.addItem(t('base_inventory.no_guilds') if t else 'Error loading guilds')
            self.guild_list.setEnabled(False)
    def _select_all_guilds(self):
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)
    def _deselect_all_guilds(self):
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)
    def _get_selected_guild_ids(self):
        selected_guilds = []
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_guilds.append(item.data(Qt.UserRole))
        return selected_guilds
    def _on_find_containers(self):
        if self.selected_item_id:
            selected_guilds = self._get_selected_guild_ids()
            self.item_action_selected.emit(self.selected_item_id, 'find', selected_guilds)
    def _on_remove_item(self):
        if not self.selected_item_id:
            return
        selected_guilds = self._get_selected_guild_ids()
        if not selected_guilds:
            show_warning(self, t('base_inventory.no_guilds_selected') if t else 'No guilds selected', t('base_inventory.no_guilds_selected') if t else 'Please select at least one guild.')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(t('base_inventory.remove_from_guilds') if t else 'Remove from Guilds')
        dialog.setMinimumSize(300, 120)
        dialog.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(dialog)
        label = QLabel(t('base_inventory.choose_remove_type') if t else 'Choose remove type:')
        layout.addWidget(label)
        remove_pct_btn = QPushButton(t('base_inventory.remove_pct_option') if t else 'Remove Percentage')
        remove_pct_btn.clicked.connect(lambda: self._do_remove_pct(dialog, selected_guilds))
        layout.addWidget(remove_pct_btn)
        remove_all_btn = QPushButton(t('base_inventory.remove_all_option') if t else 'Remove All')
        remove_all_btn.clicked.connect(lambda: self._do_remove_all(dialog, selected_guilds))
        layout.addWidget(remove_all_btn)
        dialog.exec()
    def _do_remove_pct(self, dialog, selected_guilds):
        dialog.accept()
        dlg = QInputDialog(self)
        dlg.setWindowTitle(t('base_inventory.remove_percentage') if t else 'Remove Percentage')
        dlg.setLabelText(t('base_inventory.enter_percentage') if t else 'Enter percentage to remove (1-100):')
        dlg.setIntValue(50)
        dlg.setIntRange(1, 100)
        dlg.setIntStep(10)
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        ok = dlg.exec() == QDialog.Accepted
        pct = dlg.intValue() if ok else 50
        if ok:
            self.item_action_selected.emit(self.selected_item_id, f'remove_pct:{pct}', selected_guilds)
    def _do_remove_all(self, dialog, selected_guilds):
        dialog.accept()
        item_name = self.selected_item_name or 'this item'
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(t('base_inventory.confirm_remove_all') if t else 'Confirm Remove')
        msg_box.setText(t('base_inventory.confirm_remove_all_msg').format(item_name=item_name) if t else f'Remove all "{item_name}" from selected guilds?')
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet(_DIALOG_STYLE)
        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            self.item_action_selected.emit(self.selected_item_id, 'remove_all', selected_guilds)
class GuildStructurePickerDialog(QDialog):
    structure_action_selected = Signal(str, str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('base_inventory.select_structure_action') if t else 'Structure Actions')
        self.setMinimumSize(1200, 650)
        self.selected_structure_asset = None
        self.selected_structure_name = None
        self.guild_locations = {}
        self.guild_structure_counts = {}
        self.setStyleSheet(_DIALOG_STYLE)
        self._setup_ui()
        self._load_structure_data()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        search_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('base_inventory.search_structures') if t else 'Type to search structures...')
        self.search_input.textChanged.connect(self._filter_structures)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(48, 48))
        self.results_list.setSpacing(0)
        self.results_list.setUniformItemSizes(True)
        self.results_list.setGridSize(QSize(80, 80))
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(False)
        self.results_list.viewport().setAcceptDrops(False)
        self.results_list.itemClicked.connect(self._on_structure_clicked)
        self.results_list.itemDoubleClicked.connect(self._on_find_bases)
        left_layout.addWidget(self.results_list)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        info_frame = QFrame()
        info_frame.setStyleSheet('background: rgba(0,0,0,0.15); border-radius: 4px;')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(5, 2, 5, 2)
        info_layout.setSpacing(0)
        self.info_label = QLabel(t('base_inventory.select_structure') if t else 'Select a structure to perform actions')
        self.info_label.setStyleSheet('color: #888; font-style: italic; padding: 2px;')
        info_layout.addWidget(self.info_label)
        self.code_label = QLabel('')
        self.code_label.setStyleSheet('color: #6b7280; font-size: 10px; font-family: monospace; padding: 0 2px;')
        self.code_label.setVisible(False)
        info_layout.addWidget(self.code_label)
        right_layout.addWidget(info_frame, 3)
        guilds_group = QGroupBox(t('base_inventory.select_guilds') if t else 'Select Guilds')
        guilds_inner_layout = QVBoxLayout()
        guild_buttons_layout = QHBoxLayout()
        guild_buttons_layout.setSpacing(5)
        self.select_all_btn = QPushButton(t('base_inventory.select_all_guilds') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_guilds)
        self.select_all_btn.setEnabled(False)
        self.deselect_all_btn = QPushButton(t('base_inventory.deselect_all_guilds') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_guilds)
        self.deselect_all_btn.setEnabled(False)
        self.find_btn = QPushButton(t('base_inventory.find_bases') if t else 'Find Bases')
        self.find_btn.clicked.connect(self._on_find_bases)
        self.find_btn.setEnabled(False)
        self.delete_btn = QPushButton(t('base_inventory.delete_structure_btn') if t else 'Delete Structure')
        self.delete_btn.clicked.connect(self._on_delete_structure)
        self.delete_btn.setEnabled(False)
        guild_buttons_layout.addWidget(self.select_all_btn)
        guild_buttons_layout.addWidget(self.deselect_all_btn)
        guild_buttons_layout.addWidget(self.find_btn)
        guild_buttons_layout.addWidget(self.delete_btn)
        guild_buttons_layout.addStretch()
        guilds_inner_layout.addLayout(guild_buttons_layout)
        self.guild_list = QListWidget()
        self.guild_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.guild_list.setEnabled(False)
        guilds_inner_layout.addWidget(self.guild_list)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('background: rgba(255,255,255,0.1); max-height: 1px; margin: 4px 0;')
        guilds_inner_layout.addWidget(sep)
        stats_container = QWidget()
        stats_container_layout = QHBoxLayout(stats_container)
        stats_container_layout.setContentsMargins(0, 2, 0, 0)
        stats_container_layout.setSpacing(8)
        self.stats_total_label = QLabel(f"{(t('base_inventory.total') if t else 'Total')}: 0")
        self.stats_total_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        stats_container_layout.addWidget(self.stats_total_label)
        self.stats_guilds_label = QLabel(f"{(t('base_inventory.guilds') if t else 'Guilds')}: 0")
        self.stats_guilds_label.setStyleSheet('font-size: 12px;')
        stats_container_layout.addWidget(self.stats_guilds_label)
        self.stats_avg_label = QLabel(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: 0.0")
        self.stats_avg_label.setStyleSheet('font-size: 12px;')
        stats_container_layout.addWidget(self.stats_avg_label)
        stats_container_layout.addStretch()
        guilds_inner_layout.addWidget(stats_container)
        guilds_group.setLayout(guilds_inner_layout)
        right_layout.addWidget(guilds_group, 7)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        right_layout.addLayout(btn_layout)
        content_layout.addWidget(left_widget, 3)
        content_layout.addWidget(right_widget, 2)
        layout.addLayout(content_layout)
    def _load_structure_data(self):
        from palworld_aio.base_inventory_manager import load_structure_data
        sd = load_structure_data()
        structures = sd.get('structures', [])
        base_path = constants.get_base_path()
        for s in structures:
            name = s.get('name', '')
            asset = s.get('asset', '')
            if name == '---' or not asset or name == 'en Text':
                continue
            asset_lower = asset.lower()
            name_lower = name.lower()
            if any((asset_lower.startswith(p) or name_lower.startswith(p) for p in ('common', 'enemycamp', 'palegg', 'pickupitem', 'damagable', 'destroyable', 'treasurebox', 'yakushima', 'dev_itemchest', 'altar_raidbossarea', 'antiair', 'banyan', 'deathpenaltychest', 'decal', 'dummyfoliage', 'oilrig', 'palbox_raidbossarea', 'meteordrop_', 'supplydrop', 'table1', 'droppedcharacter', 'trap_movingpanel', 'woodcrusher', 'palstorage_terminal', 'house_1'))) or any((q in asset_lower or q in name_lower for q in ('_grade', '_test', '_autoturret'))):
                continue
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, asset)
            list_item.setData(Qt.UserRole + 1, name)
            icon_rel = s.get('icon', '')
            if icon_rel:
                icon_clean = icon_rel.lstrip('/')
                icon_abs = resource_path(base_path, 'game_data', icon_clean)
                if os.path.exists(icon_abs):
                    pixmap = QPixmap(icon_abs)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        list_item.setIcon(QIcon(scaled))
            tip = f'<b>{name}</b><br>({asset})'
            list_item.setToolTip(tip)
            list_item.setSizeHint(QSize(80, 80))
            self.results_list.addItem(list_item)
    def _filter_structures(self, query: str):
        q = query.lower()
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            name = item.text()
            asset = item.data(Qt.UserRole) or ''
            item.setHidden(bool(q and q not in name.lower() and (q not in asset.lower())))
    def _on_structure_clicked(self, item: QListWidgetItem):
        self.selected_structure_asset = item.data(Qt.UserRole)
        self.selected_structure_name = item.data(Qt.UserRole + 1)
        self.info_label.setText(self.selected_structure_name)
        self.info_label.setStyleSheet('color: #4ade80; font-weight: bold; font-size: 13px; padding: 2px;')
        self.code_label.setText(self.selected_structure_asset)
        self.code_label.setVisible(True)
        self.find_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self._load_guilds_for_structure()
    def _load_guilds_for_structure(self):
        self.guild_list.clear()
        self.guild_locations = {}
        self.guild_structure_counts = {}
        if not self.selected_structure_asset:
            return
        try:
            from palworld_aio.base_inventory_manager import find_structure_locations_efficient, get_structure_economy_stats
            locations = find_structure_locations_efficient(self.selected_structure_asset)
            stats = get_structure_economy_stats(self.selected_structure_asset)
            if stats:
                guild_details = stats.get('guild_details', [])
                for gd in guild_details:
                    gid = gd.get('guild_id', '')
                    count = gd.get('count', 0)
                    if gid:
                        self.guild_structure_counts[gid] = count
            if locations:
                base_guild_lookup = constants.base_guild_lookup
                for guild_id_normalized, bases in locations.items():
                    guild_name = 'Unknown Guild'
                    for gid_key, ginfo in base_guild_lookup.items():
                        if str(ginfo.get('GuildID', '')).replace('-', '').lower() == guild_id_normalized:
                            guild_name = ginfo.get('GuildName', 'Unknown Guild')
                            break
                    self.guild_locations[guild_id_normalized] = {'name': guild_name, 'bases': bases}
                    count = self.guild_structure_counts.get(guild_id_normalized, 0)
                    display_text = f'{guild_name}: {count}'
                    list_item = QListWidgetItem(display_text)
                    list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                    list_item.setCheckState(Qt.Checked)
                    list_item.setData(Qt.UserRole, guild_id_normalized)
                    self.guild_list.addItem(list_item)
                self.guild_list.setEnabled(True)
                self.select_all_btn.setEnabled(True)
                self.deselect_all_btn.setEnabled(True)
                total = stats.get('total_count', 0) if stats else 0
                guilds = stats.get('guilds_with_item', 0) if stats else 0
                avg = stats.get('avg_per_guild', 0.0) if stats else 0.0
                self.stats_total_label.setText(f"{(t('base_inventory.total') if t else 'Total')}: {total}")
                self.stats_guilds_label.setText(f"{(t('base_inventory.guilds') if t else 'Guilds')}: {guilds}")
                self.stats_avg_label.setText(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: {avg:.1f}")
            else:
                self.guild_list.addItem(t('base_inventory.no_structures') if t else 'No structures found')
                self.guild_list.setEnabled(False)
                self.select_all_btn.setEnabled(False)
                self.deselect_all_btn.setEnabled(False)
                self.stats_total_label.setText(f"{(t('base_inventory.total') if t else 'Total')}: 0")
                self.stats_guilds_label.setText(f"{(t('base_inventory.guilds') if t else 'Guilds')}: 0")
                self.stats_avg_label.setText(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: 0.0")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.guild_list.addItem(t('base_inventory.no_structures') if t else 'Error loading guilds')
            self.guild_list.setEnabled(False)
    def _select_all_guilds(self):
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)
    def _deselect_all_guilds(self):
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)
    def _get_selected_guild_ids(self):
        selected = []
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected
    def _on_find_bases(self):
        if self.selected_structure_asset:
            selected_guilds = self._get_selected_guild_ids()
            self.structure_action_selected.emit(self.selected_structure_asset, 'find', selected_guilds)
    def _on_delete_structure(self):
        if not self.selected_structure_asset:
            return
        selected_guilds = self._get_selected_guild_ids()
        if not selected_guilds:
            show_warning(self, t('base_inventory.no_guilds_selected') if t else 'No guilds selected', t('base_inventory.no_guilds_selected') if t else 'Please select at least one guild.')
            return
        structure_name = self.selected_structure_name or self.selected_structure_asset
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(t('base_inventory.confirm_delete_structures') if t else 'Confirm Delete Structures')
        msg_box.setText(t('base_inventory.confirm_delete_structures_msg').format(structure_name=structure_name) if t else f'Are you sure you want to delete ALL "{structure_name}" from selected guilds? This action cannot be undone.')
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet(_DIALOG_STYLE)
        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            self.structure_action_selected.emit(self.selected_structure_asset, 'delete_all', selected_guilds)
class EconomyStatsDialog(QDialog):
    def __init__(self, stats, item_name=None, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.item_name = item_name or stats.get('item_id', 'Unknown')
        title = t('base_inventory.economy_title').format(item_name=self.item_name) if t else f'Economy Stats: {self.item_name}'
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(_DIALOG_STYLE)
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        display_name = self.item_name
        header_text = t('base_inventory.economy_for').format(item_name=display_name) if t else f'Economy Stats for {display_name}'
        header = QLabel(header_text)
        header.setStyleSheet('font-size: 14px; font-weight: bold; padding: 10px;')
        layout.addWidget(header)
        summary_group = QGroupBox(t('base_inventory.summary') if t else 'Summary')
        summary_layout = QVBoxLayout()
        total = self.stats.get('total_count', 0)
        guilds = self.stats.get('guilds_with_item', 0)
        avg = self.stats.get('avg_per_guild', 0)
        summary_layout.addWidget(QLabel(f"<b>{(t('base_inventory.total') if t else 'Total')}:</b> {total}"))
        summary_layout.addWidget(QLabel(f"<b>{(t('base_inventory.guilds_with_item') if t else 'Guilds with item')}:</b> {guilds}"))
        summary_layout.addWidget(QLabel(f"<b>{(t('base_inventory.avg_per_guild') if t else 'Average per guild')}:</b> {avg:.1f}"))
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        details_group = QGroupBox(t('base_inventory.per_guild') if t else 'Per Guild Breakdown')
        details_layout = QVBoxLayout()
        guild_details = self.stats.get('guild_details', [])
        guild_list = QListWidget()
        for gd in guild_details:
            guild_list.addItem(f"{gd.get('guild_name', 'Unknown')}: {gd.get('count', 0)}")
        if not guild_details:
            guild_list.addItem(t('base_inventory.no_guilds') if t else 'No guilds found with this item')
        details_layout.addWidget(guild_list)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
class ContainerSlotModificationDialog(QDialog):
    def __init__(self, parent=None, current_slots=0, current_items=0):
        super().__init__(parent)
        self.current_slots = current_slots
        self.current_items = current_items
        self.new_slot_count = current_slots
        self._setup_ui()
    def _setup_ui(self):
        self.setWindowTitle(t('base_inventory.modify_container_slots') if t else 'Modify Container Slots')
        self.setModal(True)
        self.setMinimumWidth(350)
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        status_group = QGroupBox(t('base_inventory.current_status') if t else 'Current Status')
        status_layout = QVBoxLayout()
        current_slots_label = QLabel(t('base_inventory.current_slots').format(count=self.current_slots) if t else f'Current Slots: {self.current_slots}')
        current_slots_label.setStyleSheet('font-weight: bold;')
        status_layout.addWidget(current_slots_label)
        current_items_label = QLabel(t('base_inventory.current_items').format(count=self.current_items) if t else f'Current Items: {self.current_items}')
        current_items_label.setStyleSheet('font-weight: bold;')
        status_layout.addWidget(current_items_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        input_group = QGroupBox(t('base_inventory.new_slot_count') if t else 'New Slot Count')
        input_layout = QVBoxLayout()
        self.slot_spinbox = QSpinBox()
        self.slot_spinbox.setMinimum(1)
        self.slot_spinbox.setMaximum(999)
        self.slot_spinbox.setValue(self.current_slots)
        self.slot_spinbox.valueChanged.connect(self._on_slot_count_changed)
        input_layout.addWidget(self.slot_spinbox)
        self.warning_label = QLabel('')
        self.warning_label.setStyleSheet('color: #ff6b6b; font-weight: bold;')
        self.warning_label.setVisible(False)
        input_layout.addWidget(self.warning_label)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.ok_button = QPushButton(t('base_inventory.ok') if t else 'OK')
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        cancel_button = QPushButton(t('base_inventory.cancel') if t else 'Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        self._update_validation()
    def _on_slot_count_changed(self, value):
        self.new_slot_count = value
        self._update_validation()
    def _update_validation(self):
        if self.new_slot_count < self.current_items:
            self.warning_label.setText(t('base_inventory.warning_cannot_reduce_below_items').format(item_count=self.current_items) if t else f'Warning: Cannot reduce slots below current item count ({self.current_items})')
            self.warning_label.setVisible(True)
            self.ok_button.setEnabled(False)
        elif self.new_slot_count == self.current_slots:
            self.warning_label.setText(t('base_inventory.no_change_needed') if t else 'No change needed - slot count is the same')
            self.warning_label.setVisible(True)
            self.ok_button.setEnabled(False)
        else:
            self.warning_label.setVisible(False)
            self.ok_button.setEnabled(True)
    def _on_ok_clicked(self):
        self.accept()
    def get_slot_count(self):
        return self.new_slot_count
class ContainerListWidget(QTreeWidget):
    container_selected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(0)
        self.setAlternatingRowColors(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setSortingEnabled(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.setStyleSheet(f'\n            QTreeWidget {{\n                background: transparent;\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 10px;\n                color: #e0e0e0;\n                outline: none;\n            }}\n            QTreeWidget::item {{\n                padding: 6px;\n                margin: 1px 2px;\n                border: 1px solid rgba(255,255,255,0.08);\n                border-radius: 8px;\n                background: rgba(255,255,255,0.03);\n            }}\n            QTreeWidget::item:selected {{\n                background: rgba(125,211,252,0.1);\n                border: 2px solid #7DD3FC;\n            }}\n            QTreeWidget::item:hover {{\n                background: rgba(125,211,252,0.06);\n                border-color: rgba(125,211,252,0.2);\n            }}\n            QTreeWidget::item:selected:hover {{\n                background: rgba(125,211,252,0.1);\n            }}\n            QTreeWidget::branch {{\n                background-color: transparent;\n            }}\n        ')
    def clear(self):
        super().clear()
        self.setHeaderHidden(True)
    def add_container(self, container_info):
        item = QTreeWidgetItem()
        item.setText(0, '')
        item.setData(0, Qt.UserRole, container_info['id'])
        item.setSizeHint(0, QSize(300, 80))
        self.addTopLevelItem(item)
        self.setItemWidget(item, 0, self._create_container_widget(container_info))
    def _create_container_widget(self, container_info):
        widget = QWidget()
        widget.setStyleSheet('background: transparent;')
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        image_label = QLabel()
        image_label.setFixedSize(60, 60)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet(f'QLabel {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; }}')
        image_path = get_container_image_path(container_info['type'])
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled)
            else:
                image_label.setText('📦')
        else:
            image_label.setText('📦')
        layout.addWidget(image_label)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_label = QLabel(container_info['name'])
        name_label.setStyleSheet('QLabel { font-weight: bold; font-size: 12px; color: #ffffff; background: transparent; }')
        info_layout.addWidget(name_label)
        details_layout = QHBoxLayout()
        details_layout.setSpacing(10)
        slots_label = QLabel(t('base_inventory.slots_count').format(count=container_info['slot_count']) if t else f"Slots: {container_info['slot_count']}")
        slots_label.setStyleSheet('QLabel { font-size: 11px; color: #cccccc; background: transparent; }')
        details_layout.addWidget(slots_label)
        info_layout.addLayout(details_layout)
        id_label = QLabel(container_info['id'])
        id_label.setStyleSheet('QLabel { font-size: 11px; color: #999999; background: transparent; }')
        info_layout.addWidget(id_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        return widget
    def update_slot_count_label(self, container_id, new_count):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == container_id:
                widget = self.itemWidget(item, 0)
                if widget:
                    for child in widget.findChildren(QLabel):
                        if 'Slots' in child.text() or 'slots' in child.text() or f"Slots:" in child.text():
                            child.setText(t('base_inventory.slots_count').format(count=new_count) if t else f'Slots: {new_count}')
                            break
                break
    def _on_selection_changed(self):
        selected_items = self.selectedItems()
        if selected_items:
            container_id = selected_items[0].data(0, Qt.UserRole)
            self.container_selected.emit(container_id)
    def _show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            container_id = item.data(0, Qt.UserRole)
            menu = QMenu(self)
            menu.setStyleSheet(MENU_STYLE)
            add_item_action = menu.addAction(t('base_inventory.add_item') if t else 'Add Item')
            add_item_action.triggered.connect(lambda: self._add_item_debug(container_id))
            clear_container_action = menu.addAction(t('base_inventory.clear_container') if t else 'Clear Container')
            clear_container_action.triggered.connect(lambda: self._clear_container_debug(container_id))
            modify_slots_action = menu.addAction(t('base_inventory.modify_container_slots') if t else 'Modify Container Slots')
            modify_slots_action.triggered.connect(lambda: self._modify_container_slots_debug(container_id))
            delete_container_action = menu.addAction(t('base_inventory.delete_container') if t else 'Delete Container')
            delete_container_action.triggered.connect(lambda: self._delete_container_debug(container_id))
            menu.exec(self.viewport().mapToGlobal(position))
        else:
            pass
    def _view_container_details(self, container_id):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == container_id:
                widget = self.itemWidget(item, 0)
                if widget:
                    container_info = None
                    parent = self.parent()
                    if hasattr(parent, 'manager'):
                        container_info = next((c for c in parent.manager.containers if c['id'] == container_id), None)
                    if container_info:
                        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
                        dialog = QDialog(self)
                        dialog.setWindowTitle(t('base_inventory.container_details') if t else 'Container Details')
                        dialog.setModal(True)
                        dialog.setStyleSheet(_DIALOG_STYLE)
                        layout = QVBoxLayout(dialog)
                        details_text = f"\n                        <h3>{container_info['name']}</h3>\n                        <p><b>Type:</b> {container_info['type']}</p>\n                        <p><b>Slots:</b> {container_info['slot_count']}</p>\n                        <p><b>Location:</b> {container_info['location']}</p>\n                        <p><b>Container ID:</b> {container_info['id']}</p>\n                        "
                        label = QLabel(details_text)
                        label.setTextFormat(Qt.RichText)
                        layout.addWidget(label)
                        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
                        buttons.accepted.connect(dialog.accept)
                        layout.addWidget(buttons)
                        dialog.exec()
    def _refresh_container(self, container_id):
        parent = self.parent()
        if hasattr(parent, 'manager'):
            parent.manager.refresh_container(container_id)
            if hasattr(parent, '_refresh_container_ui'):
                parent._refresh_container_ui()
    def _export_container(self, container_id):
        parent = self.parent()
        if hasattr(parent, 'manager'):
            container_data = parent.manager.export_container(container_id)
            if container_data:
                file_path, _ = QFileDialog.getSaveFileName(self, t('base_inventory.export_container') if t else 'Export Container', f'container_{container_id[:8]}.json', 'JSON Files (*.json)')
                if file_path:
                    try:
                        json_tools.dump(container_data, file_path, indent=2, ensure_ascii=False)
                        parent._show_info(t('base_inventory.export_success') if t else 'Container exported successfully')
                    except Exception as e:
                        parent._show_warning(f'Failed to export container: {str(e)}')
    def _add_item(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_add_item'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            base_inventory_tab.manager.select_container(container_id)
            base_inventory_tab._add_item()
        except Exception as e:
            self._show_warning(f'Failed to add item: {str(e)}')
    def _delete_container(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_delete_container'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            base_inventory_tab.manager.select_container(container_id)
            base_inventory_tab._delete_container(container_id)
        except Exception as e:
            self._show_warning(f'Failed to delete container: {str(e)}')
    def _clear_container(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_clear_container'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            if show_question(self, t('base_inventory.clear_container') if t else 'Clear Container', t('base_inventory.clear_container_confirm') if t else 'Are you sure you want to clear all items from this container?'):
                if base_inventory_tab.manager.clear_container(container_id):
                    base_inventory_tab.manager.select_container(container_id)
                    base_inventory_tab._refresh_container_ui()
                    base_inventory_tab._show_info(t('base_inventory.container_cleared') if t else 'Container cleared successfully')
                else:
                    base_inventory_tab._show_warning(t('base_inventory.failed_to_clear_container') if t else 'Failed to clear container')
        except Exception as e:
            self._show_warning(f'Failed to clear container: {str(e)}')
    def _modify_container_slots(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_modify_container_slots'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            base_inventory_tab.manager.select_container(container_id)
            base_inventory_tab._modify_container_slots()
        except Exception as e:
            import traceback
            traceback.print_exc()
    def _add_item_debug(self, container_id):
        self._add_item(container_id)
    def _clear_container_debug(self, container_id):
        self._clear_container(container_id)
    def _modify_container_slots_debug(self, container_id):
        self._modify_container_slots(container_id)
    def _delete_container_debug(self, container_id):
        self._delete_container(container_id)
class ContainerInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container_info = None
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        header_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(80, 80)
        self.image_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.image_label)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        self.name_label = QLabel('Container Name')
        self.name_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        info_layout.addWidget(self.name_label)
        self.slots_label = QLabel(t('base_inventory.slots_count').format(count=0) if t else 'Slots: 0')
        self.slots_label.setStyleSheet('font-size: 12px;')
        info_layout.addWidget(self.slots_label)
        self.id_label = QLabel('Unknown')
        self.id_label.setStyleSheet('font-size: 12px;')
        info_layout.addWidget(self.id_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        self.items_count_label = QLabel(t('base_inventory.items').format(count=0) if t else 'Items: 0')
        self.items_count_label.setStyleSheet('font-size: 12px; font-weight: bold;')
        stats_layout.addWidget(self.items_count_label)
        self.empty_slots_label = QLabel(t('base_inventory.empty').format(count=0) if t else 'Empty: 0')
        self.empty_slots_label.setStyleSheet('font-size: 12px; font-weight: bold;')
        stats_layout.addWidget(self.empty_slots_label)
        layout.addLayout(stats_layout)
        self._update_styles()
    def set_container_info(self, container_info):
        self.container_info = container_info
        self._update_content()
    def _update_content(self):
        if not self.container_info:
            return
        self.name_label.setText(self.container_info['name'])
        self.slots_label.setText(t('base_inventory.slots_count').format(count=self.container_info['slot_count']) if t else f"Slots: {self.container_info['slot_count']}")
        self.id_label.setText(self.container_info['id'])
        image_path = get_container_image_path(self.container_info['type'])
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText('📦')
        else:
            self.image_label.setText('📦')
    def _update_styles(self):
        self.setStyleSheet(f'\n                QWidget {{\n                    {CONTENT_PANEL_STYLE}\n                    color: #e0e0e0;\n                }}\n                QLabel {{\n                    color: #e0e0e0;\n                }}\n                QLabel[bold="true"] {{\n                    font-weight: bold;\n                }}\n            ')
class _BasePalIcon(QFrame):
    clicked = Signal(int)
    rightClicked = Signal(int, str)
    entered = Signal(int)
    left = Signal()
    def __init__(self, pal_data=None, slot_index=0, parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.slot_index = slot_index
        self.selected = False
        self.setObjectName('basePalSlot')
        self.setMinimumSize(56, 56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._children = []
        self._build()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, '_children'):
            return
        w, h = (self.width(), self.height())
        for c in self._children:
            try:
                kind = c._slot_child_kind
                cw, ch = (c.width(), c.height())
                if kind == 'icon':
                    c.move((w - cw) // 2, (h - ch) // 2)
                elif kind == 'boss':
                    c.move(2, 2)
                elif kind == 'element0':
                    c.move(w - cw - 2, 2)
                elif kind == 'element1':
                    c.move(w - cw - 2, 12)
                elif kind == 'dna':
                    c.move(2, h - ch - 2)
                elif kind == 'lock':
                    c.move((w - cw) // 2, 1)
                elif kind == 'level':
                    c.move((w - cw) // 2, h - ch - 3)
                elif kind == 'awake':
                    c.move(w - cw - 2, h - ch - 2)
            except Exception:
                pass
    def enterEvent(self, event):
        self.entered.emit(self.slot_index)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.slot_index)
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.pal_data:
                self.rightClicked.emit(self.slot_index, 'delete_direct')
            else:
                self.rightClicked.emit(self.slot_index, 'add_new')
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self, event):
        if self.pal_data:
            self.clicked.emit(self.slot_index)
            raw = self._get_raw()
            if not raw:
                return
            menu, actions = build_pal_context_menu(self, raw)
            action = menu.exec(event.globalPos())
            if action == actions['boss']:
                self.rightClicked.emit(self.slot_index, 'boss_toggle')
            elif action == actions['lucky']:
                self.rightClicked.emit(self.slot_index, 'lucky_toggle')
            elif action == actions['awake']:
                self.rightClicked.emit(self.slot_index, 'awake_toggle')
            elif action == actions['dna']:
                self.rightClicked.emit(self.slot_index, 'dna_toggle')
            elif action in actions['fav'][1]:
                idx = actions['fav'][1].index(action)
                self.rightClicked.emit(self.slot_index, f'fav_set_{idx}')
            elif action == actions['max']:
                self.rightClicked.emit(self.slot_index, 'max_all_stats')
            elif action == actions['learn']:
                self.rightClicked.emit(self.slot_index, 'learn_all')
            elif action == actions['learned']:
                self.rightClicked.emit(self.slot_index, 'learnt_skills')
            elif action == actions['bulk_sync_pal']:
                self.rightClicked.emit(self.slot_index, 'bulk_sync_pal')
            elif action == actions['delete']:
                self.rightClicked.emit(self.slot_index, 'delete')
        else:
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self)
            menu.setObjectName('editPalsContextMenu')
            add_action = menu.addAction(t('edit_pals.add_new_pal'))
            action = menu.exec(event.globalPos())
            if action == add_action:
                self.rightClicked.emit(self.slot_index, 'add_new')
    def _get_raw(self):
        if not self.pal_data:
            return None
        try:
            if 'data' in self.pal_data:
                return self.pal_data['data']
            return safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
        except Exception:
            return None
    def _build(self):
        was_selected = self.selected
        for c in list(self._children):
            c.deleteLater()
        self._children = []
        raw = self._get_raw()
        if not raw or not isinstance(raw, dict):
            self.setStyleSheet(slot_full('QFrame#basePalSlot'))
            self.setToolTip('')
            return
        cid = extract_value(raw, 'CharacterID', '')
        level = extract_value(raw, 'Level', 1)
        nick = extract_value(raw, 'NickName', '')
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        is_awake = bool(extract_value(raw, 'bIsAwakening', False))
        is_imported = bool(extract_value(raw, 'bImportedCharacter', False))
        fav_idx = extract_value(raw, 'FavoriteIndex', 0)
        icon_path = _get_pal_icon_path(cid)
        pix = _get_cached_pixmap(icon_path, 38)
        icon_lbl = QLabel(self)
        icon_lbl.setFixedSize(38, 38)
        icon_lbl.setAlignment(Qt.AlignCenter)
        if pix:
            icon_lbl.setPixmap(pix)
        icon_lbl.setStyleSheet('background: transparent; border: none;')
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_lbl._slot_child_kind = 'icon'
        icon_lbl.show()
        self._children.append(icon_lbl)
        base_el_data = get_pal_base_data(cid)
        if base_el_data:
            els = list(base_el_data.get('elements', {}))
            for ei, en in enumerate(els[:2]):
                ep = _get_element_pixmap(en, 'small', 8 if len(els) > 1 else 10)
                if ep:
                    eb = QLabel(self)
                    eb.setFixedSize(10, 10)
                    eb.setAlignment(Qt.AlignCenter)
                    eb.setPixmap(ep)
                    eb.setStyleSheet('background: transparent; border: none;')
                    eb.setAttribute(Qt.WA_TransparentForMouseEvents)
                    eb._slot_child_kind = f'element{ei}'
                    eb.show()
                    self._children.append(eb)
        level_lbl = StrokedLabel(f'{level}', self)
        level_lbl.setStyleSheet('color: #7DD3FC; font-size: 8px; font-weight: bold; background: rgba(0,0,0,0.7); border: 1px solid rgba(125,211,252,0.25); border-radius: 3px; padding: 0 3px;')
        level_lbl.setFixedSize(18, 11)
        level_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        level_lbl._slot_child_kind = 'level'
        level_lbl.show()
        self._children.append(level_lbl)
        if is_boss:
            boss_pix = _get_boss_alpha_pixmap(14)
            if boss_pix:
                badge = QLabel(self)
                badge.setPixmap(boss_pix)
                badge.setFixedSize(14, 14)
                badge.setAlignment(Qt.AlignCenter)
                badge.setStyleSheet('background: transparent; border: none;')
                badge.setAttribute(Qt.WA_TransparentForMouseEvents)
                badge._slot_child_kind = 'boss'
                badge.show()
                self._children.append(badge)
        elif is_lucky:
            shiny_pix = _get_boss_shiny_pixmap(14)
            if shiny_pix:
                badge = QLabel(self)
                badge.setPixmap(shiny_pix)
                badge.setFixedSize(14, 14)
                badge.setAlignment(Qt.AlignCenter)
                badge.setStyleSheet('background: transparent; border: none;')
                badge.setAttribute(Qt.WA_TransparentForMouseEvents)
                badge._slot_child_kind = 'boss'
                badge.show()
                self._children.append(badge)
        if is_awake:
            awake_pix = _get_awake_pixmap(12)
            if awake_pix:
                awake_badge = QLabel(self)
                awake_badge.setPixmap(awake_pix)
                awake_badge.setFixedSize(12, 12)
                awake_badge.setAlignment(Qt.AlignCenter)
                awake_badge.setStyleSheet('background: transparent; border: none;')
            else:
                awake_badge = QLabel('🔥', self)
                awake_badge.setStyleSheet('font-size: 9px; background: transparent;')
                awake_badge.setFixedSize(12, 12)
                awake_badge.setAlignment(Qt.AlignCenter)
            awake_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            awake_badge._slot_child_kind = 'awake'
            awake_badge.show()
            self._children.append(awake_badge)
        if is_imported:
            dna_pix = _get_ui_icon_pixmap('dna', 12)
            if dna_pix:
                dna_badge = QLabel(self)
                dna_badge.setPixmap(dna_pix)
                dna_badge.setFixedSize(14, 14)
                dna_badge.setAlignment(Qt.AlignCenter)
                dna_badge.setAttribute(Qt.WA_TranslucentBackground)
                dna_badge.setStyleSheet('background: transparent; border: none;')
                dna_badge._slot_child_kind = 'dna'
                dna_badge.show()
                self._children.append(dna_badge)
        if fav_idx and int(fav_idx) > 0:
            lock_key = f'lock_{int(fav_idx)}'
            lock_pix = _get_ui_icon_pixmap(lock_key, 14) or _get_ui_icon_pixmap('lock_1', 14) or _get_ui_icon_pixmap('lock', 14)
            if not lock_pix:
                lock_badge = QLabel('🔒', self)
                lock_badge.setStyleSheet('font-size: 9px; color: rgba(255,255,255,0.65); background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 7px;')
                lock_badge.setFixedSize(14, 14)
                lock_badge.setAlignment(Qt.AlignCenter)
            else:
                lock_badge = QLabel(self)
                lock_badge.setPixmap(lock_pix)
                lock_badge.setFixedSize(14, 14)
                lock_badge.setStyleSheet('background: transparent; border: none;')
            lock_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            lock_badge._slot_child_kind = 'lock'
            lock_badge.show()
            self._children.append(lock_badge)
        PalFrame._load_maps()
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        if nick:
            pal_name = nick
        tip = f'{pal_name} [Lv.{level}]'
        base = get_pal_base_data(cid)
        if base:
            pskill_desc = base.get('description', '')
            if pskill_desc:
                _p = raw.get('PassiveSkillList', {})
                if isinstance(_p, dict):
                    _pl = _p.get('value', {}).get('values', [])
                elif isinstance(_p, list):
                    _pl = _p
                else:
                    _pl = []
                _cr = int(extract_value(raw, 'Rank', 0)) if isinstance(extract_value(raw, 'Rank', 0), (int, float)) else 0
                _res = _resolve_partner_desc(pskill_desc, _pl, _cr, base.get('active_skill_main_value'), base.get('active_skill_overwrite_effect'), base.get('passives', []))
                el_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
                _ht = _partner_desc_to_html(_res, el_colors, tooltip=True)
                tip += f'<br><br>{_ht}'
        self.setToolTip(tip)
        self.setStyleSheet(slot_full('QFrame#basePalSlot'))
        if was_selected:
            self.setStyleSheet(slot_selected('QFrame#basePalSlot'))
        self.resizeEvent(None)
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet(slot_selected('QFrame#basePalSlot'))
        else:
            self.setStyleSheet(slot_full('QFrame#basePalSlot'))
    def update_display(self):
        self._build()
class BasePalsContentWidget(QFrame):
    COLS = 6
    ROWS = 5
    SLOTS_PER_PAGE = 30
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('basePalsContent')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(400)
        self.setStyleSheet('QFrame#basePalsContent { border: none; background: transparent; }')
        self._pals = []
        self._icons = []
        self._selected_idx = -1
        self._current_base_id = None
        self._current_page = 1
        self._total_pages = 1
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.placeholder = QLabel(t('base_inventory.base_pals_empty') if t else 'Select a Guild/Base to view working pals')
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setMinimumHeight(400)
        self.placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder.setStyleSheet('QLabel { color: #888; font-size: 14px; background: transparent; }')
        layout.addWidget(self.placeholder, 1)
        self.hsplit = QHBoxLayout()
        self.hsplit.setSpacing(4)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        grid_container = QWidget()
        grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid = QGridLayout(grid_container)
        self.grid.setHorizontalSpacing(2)
        self.grid.setVerticalSpacing(4)
        self.grid.setContentsMargins(0, 0, 0, 0)
        for row in range(self.ROWS):
            self.grid.setRowStretch(row, 1)
            for col in range(self.COLS):
                self.grid.setColumnStretch(col, 1)
                slot = _BasePalIcon(None, row * self.COLS + col)
                slot.clicked.connect(self._on_pal_clicked)
                slot.rightClicked.connect(self._on_pal_right_clicked)
                slot.entered.connect(self._on_pal_hovered)
                slot.left.connect(self._on_pal_hover_left)
                self.grid.addWidget(slot, row, col)
                self._icons.append(slot)
        self.grid_container_widget = grid_container
        grid_container.installEventFilter(self)
        left_layout.addWidget(grid_container)
        page_row = QHBoxLayout()
        page_row.setSpacing(6)
        self.prev_page_btn = QPushButton('◀')
        self.prev_page_btn.setFixedSize(28, 24)
        self.prev_page_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.18); color: #FFFFFF; } QPushButton:disabled { background: rgba(100,100,100,0.1); color: #666; border-color: rgba(255,255,255,0.05); }')
        self.prev_page_btn.clicked.connect(self._prev_page)
        page_row.addWidget(self.prev_page_btn)
        self.page_label = QLabel('Page 1/1')
        self.page_label.setStyleSheet('font-size: 11px; font-weight: 600; color: #7DD3FC; padding: 0 4px;')
        page_row.addWidget(self.page_label)
        self.next_page_btn = QPushButton('▶')
        self.next_page_btn.setFixedSize(28, 24)
        self.next_page_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.18); color: #FFFFFF; } QPushButton:disabled { background: rgba(100,100,100,0.1); color: #666; border-color: rgba(255,255,255,0.05); }')
        self.next_page_btn.clicked.connect(self._next_page)
        page_row.addWidget(self.next_page_btn)
        page_row.addStretch()
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #7DD3FC; padding: 2px 4px;')
        page_row.addWidget(self.stats_label)
        left_layout.addLayout(page_row)
        self.hsplit.addWidget(left_panel, 1)
        right_panel = QWidget()
        right_panel.setFixedWidth(350)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.pal_info = PalInfoWidget()
        self.pal_info.pal_data_changed.connect(self._on_pal_info_changed)
        right_layout.addWidget(self.pal_info)
        self.hsplit.addWidget(right_panel, 0)
        layout.addLayout(self.hsplit)
        self.grid_container_widget.hide()
        self.stats_label.hide()
        self.page_label.hide()
        self.prev_page_btn.hide()
        self.next_page_btn.hide()
    def set_pals(self, pals_data, base_id=None):
        self._pals = pals_data
        self._current_base_id = base_id
        self._current_page = 1
        self._total_pages = max(1, (len(self._pals) + self.SLOTS_PER_PAGE - 1) // self.SLOTS_PER_PAGE)
        self._selected_idx = -1
        self.pal_info.set_clicked_pal(None)
        self.pal_info._clear_display()
        self._rebuild()
    def clear(self, clear_base=True):
        self._pals = []
        self._current_page = 1
        self._total_pages = 1
        if clear_base:
            self._current_base_id = None
        self._rebuild()
    def refresh_labels(self):
        page_text = t('base_inventory.page') if t else None
        if page_text:
            try:
                self.page_label.setText(page_text.format(page=self._current_page, total=self._total_pages))
            except (KeyError, ValueError):
                self.page_label.setText(page_text)
        else:
            self.page_label.setText(f'Page {self._current_page}/{self._total_pages}')
        if self._pals:
            self.stats_label.setText(t('base_inventory.working_pals_count').format(count=self._pal_count()) if t else f'Working Pals: {self._pal_count()}')
        if hasattr(self, 'pal_info') and self.pal_info:
            self.pal_info.refresh_labels()
    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._update_page()
    def _next_page(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._update_page()
    def _update_page(self):
        start = (self._current_page - 1) * self.SLOTS_PER_PAGE
        for i, slot in enumerate(self._icons):
            pal_idx = start + i
            if pal_idx < len(self._pals) and self._pals[pal_idx] is not None:
                slot.pal_data = self._pals[pal_idx]['character_entry']
            else:
                slot.pal_data = None
            slot.slot_index = i
            slot.update_display()
        page_text = t('base_inventory.page') if t else None
        if page_text:
            try:
                self.page_label.setText(page_text.format(page=self._current_page, total=self._total_pages))
            except (KeyError, ValueError):
                self.page_label.setText(page_text)
        else:
            self.page_label.setText(f'Page {self._current_page}/{self._total_pages}')
        self.prev_page_btn.setEnabled(self._current_page > 1)
        self.next_page_btn.setEnabled(self._current_page < self._total_pages)
        self._selected_idx = -1
    def _rebuild(self):
        self._total_pages = max(1, (self._pal_count() + self.SLOTS_PER_PAGE - 1) // self.SLOTS_PER_PAGE)
        if self._pal_count() > 0 and self._pal_count() % self.SLOTS_PER_PAGE == 0:
            self._total_pages += 1
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        if self._pal_count() == 0:
            if self._current_base_id:
                self.placeholder.hide()
                self.grid_container_widget.show()
                self.stats_label.show()
                self.page_label.hide()
                self.prev_page_btn.hide()
                self.next_page_btn.hide()
                self.stats_label.setText(t('base_inventory.working_pals_count').format(count=0) if t else 'Working Pals: 0')
                self._selected_idx = -1
                self.pal_info.set_clicked_pal(None)
                self.pal_info._clear_display()
                self._update_page()
                return
            self.placeholder.show()
            self.grid_container_widget.hide()
            self.stats_label.hide()
            self.page_label.hide()
            self.prev_page_btn.hide()
            self.next_page_btn.hide()
            self._selected_idx = -1
            self.pal_info.set_clicked_pal(None)
            self.pal_info._clear_display()
            return
        self.placeholder.hide()
        self.grid_container_widget.show()
        self.stats_label.show()
        self.page_label.show()
        self.prev_page_btn.show()
        self.next_page_btn.show()
        self.stats_label.setText(t('base_inventory.working_pals_count').format(count=self._pal_count()) if t else f'Working Pals: {self._pal_count()}')
        self._update_page()
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and self._total_pages > 1:
            if event.angleDelta().y() < 0:
                self._next_page()
            else:
                self._prev_page()
            return True
        return super().eventFilter(obj, event)
    def _pal_count(self):
        return sum((1 for p in self._pals if p is not None))
    def _grid_idx_to_pal_idx(self, grid_idx):
        return (self._current_page - 1) * self.SLOTS_PER_PAGE + grid_idx
    def _select_pal(self, idx):
        pal_idx = self._grid_idx_to_pal_idx(idx)
        pal = self._pals[pal_idx] if pal_idx < len(self._pals) and self._pals[pal_idx] is not None else None
        if self._selected_idx >= 0:
            prev = self.grid.itemAt(self._selected_idx)
            if prev and prev.widget():
                prev.widget().set_selected(False)
        if pal:
            if self._selected_idx == idx:
                self._selected_idx = -1
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                return
            self._selected_idx = idx
            item = self.grid.itemAt(idx)
            if item and item.widget():
                item.widget().set_selected(True)
            self.pal_info.set_clicked_pal(pal['character_entry'])
        else:
            self._selected_idx = -1
            self.pal_info.set_clicked_pal(None)
    def _on_pal_hovered(self, idx):
        pal_idx = self._grid_idx_to_pal_idx(idx)
        pal = self._pals[pal_idx] if pal_idx < len(self._pals) and self._pals[pal_idx] is not None else None
        if pal:
            self.pal_info.set_hover_pal(pal['character_entry'])
    def _on_pal_hover_left(self):
        self.pal_info.clear_hover()
    def _on_pal_clicked(self, idx):
        self._select_pal(idx)
    def _add_new_pal(self):
        from palworld_aio.edit_pals import PalCreateDialog, _generate_pal_save_param
        PalFrame._load_maps()
        stub = type('Stub', (), {'party_container': None, 'palbox_container': '00000000-0000-0000-0000-000000000000', 'player_uid': '00000000-0000-0000-0000-000000000000', 'current_box_index': 1, 'palbox_pal_dict': {}})()
        dlg = PalCreateDialog(stub, False, 0)
        from PySide6.QtWidgets import QPushButton
        for btn in dlg.findChildren(QPushButton):
            if btn.text() in ('Create', t('edit_pals.create')):
                try:
                    btn.clicked.disconnect()
                except:
                    pass
                btn.clicked.connect(lambda checked, d=dlg: d.accept())
                break
        try:
            dlg.pal_list.itemDoubleClicked.disconnect()
        except:
            pass
        dlg.pal_list.itemDoubleClicked.connect(lambda item: (
            dlg.selected_pal.update({'asset': item.data(Qt.UserRole), 'name': item.text()}),
            dlg.accept()
        ))
        if dlg.exec() == QDialog.Accepted and dlg.selected_pal['asset']:
            cid = dlg.selected_pal['asset']
            nick = dlg.nick_edit.text().strip() or ''
            if self._current_base_id:
                from palworld_aio.base_inventory_manager import get_base_worker_container_id
                container_id = get_base_worker_container_id(self._current_base_id)
            else:
                container_id = '00000000-0000-0000-0000-000000000000'
            import uuid
            instance_id = str(uuid.uuid4()).upper()
            slot_idx = next((i for i, p in enumerate(self._pals) if p is None), len(self._pals))
            entry = _generate_pal_save_param(cid, nick, '00000000-0000-0000-0000-000000000000', container_id, slot_idx)
            instance_id = entry.get('key', {}).get('InstanceId', {}).get('value', instance_id)
            guild_id = None
            parent = self.parent()
            while parent:
                if hasattr(parent, '_current_guild_id'):
                    guild_id = parent._current_guild_id
                    break
                parent = parent.parent()
            if constants.loaded_level_json:
                try:
                    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
                    cmap.append(entry)
                    if container_id and container_id != '00000000-0000-0000-0000-000000000000':
                        char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
                        for cont in char_containers:
                            if str(cont.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() == container_id.replace('-', '').lower():
                                slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                                slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                                current_slot_num = cont.get('value', {}).get('SlotNum', {}).get('value', 0)
                                if len(slots) > current_slot_num:
                                    cont['value']['SlotNum']['value'] = len(slots)
                                break
                    if guild_id:
                        _register_pal_instance_to_guild(instance_id, guild_id)
                except Exception:
                    pass
            new_pal = {'slot_index': 0, 'instance_id': instance_id, 'character_entry': entry}
            if slot_idx < len(self._pals):
                self._pals[slot_idx] = new_pal
            else:
                self._pals.append(new_pal)
            self._rebuild()
            self._trigger_save()
            self._refresh_dashboard()
    def _trigger_save(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, '_trigger_auto_save'):
                parent._trigger_auto_save()
                break
            parent = parent.parent()
    def _refresh_dashboard(self):
        app = QApplication.instance()
        if app is None:
            return
        for w in app.topLevelWidgets():
            if hasattr(w, 'tools_tab'):
                w.tools_tab.refresh()
                break
    def _delete_base_pal(self, pal_idx):
        import gc
        pal = self._pals[pal_idx]
        try:
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            if pal['character_entry'] in cmap:
                cmap.remove(pal['character_entry'])
        except Exception:
            pass
        self._pals[pal_idx] = None
        self._rebuild()
        self.pal_info.last_clicked_data = None
        self.pal_info._hovered_data = None
        self.pal_info._clear_display()
        self._refresh_dashboard()
    def _on_pal_info_changed(self):
        for icon in self._icons:
            icon.update_display()
    def _on_pal_right_clicked(self, idx, action):
        pal_idx = self._grid_idx_to_pal_idx(idx)
        pal = self._pals[pal_idx] if pal_idx < len(self._pals) and self._pals[pal_idx] is not None else None
        if not pal:
            if action == 'add_new':
                self._add_new_pal()
                return
            return
        raw = safe_nested_get(pal['character_entry'], ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
        if not raw:
            return
        if action == 'boss_toggle':
            cur_is_boss = extract_value(raw, 'CharacterID', '').upper().startswith('BOSS_')
            _toggle_boss_raw(raw, not cur_is_boss)
        elif action == 'lucky_toggle':
            cur = extract_value(raw, 'IsRarePal', False)
            _toggle_lucky_raw(raw, not cur)
        elif action == 'awake_toggle':
            cur = bool(extract_value(raw, 'bIsAwakening', False))
            _toggle_awake_raw(raw, not cur)
        elif action == 'dna_toggle':
            cur = bool(extract_value(raw, 'bImportedCharacter', False))
            _toggle_dna_raw(raw, not cur)
        elif action == 'max_all_stats':
            from palworld_aio.edit_pals import _max_stats_raw
            _max_stats_raw(raw)
        elif action.startswith('fav_set_'):
            fav_val = int(action.split('_')[-1])
            _set_fav_raw(raw, fav_val)
        elif action == 'learn_all':
            try:
                _learn_all_skills_raw(raw)
                show_information(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_success'))
            except Exception:
                show_warning(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_fail'))
        elif action == 'learnt_skills':
            _show_learned_moves_dialog(raw, self)
        elif action == 'bulk_sync_pal':
            from palworld_aio.edit_pals import _get_raw_from_item, BulkSyncPalDialog
            stub = type('Stub', (), {'party_pals': {}, 'palbox_pal_dict': {}, 'pal_info': type('Stub', (), {'_refresh': lambda self: None})(), '_update_party_slots': lambda self: None, '_update_palbox_page': lambda self: None})()
            cid = extract_value(raw, 'CharacterID', '')
            base_id = cid.lower().replace('boss_', '')
            affected = []
            for p in self._pals:
                pr = _get_raw_from_item(p['character_entry'])
                if pr and pr is not raw and (extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id):
                    affected.append(p['character_entry'])
            dlg = BulkSyncPalDialog(pal['character_entry'], stub, self, candidates=affected)
            display_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
            for child in dlg.findChildren(QLabel):
                text = child.text()
                if 'found' in text.lower() or text.startswith(t('edit_pals.bulk_sync_found', count=0, name='').split('{')[0] if t else 'Found'):
                    child.setText(t('edit_pals.bulk_sync_found', count=len(affected), name=display_name) if t else f'Found {len(affected)} pals matching {display_name}')
                    break
            if dlg.exec() == QDialog.Accepted:
                for icon in self._icons:
                    icon.update_display()
        elif action == 'delete':
            reply = show_question(self, t('edit_pals.confirm_delete'), 'Delete this pal?')
            if not reply:
                return
            self._delete_base_pal(pal_idx)
            return
        elif action == 'delete_direct':
            self._delete_base_pal(pal_idx)
            return
        item = self.grid.itemAt(idx)
        if item and item.widget():
            item.widget().update_display()
        self.pal_info.set_clicked_pal(pal['character_entry'])
class BaseInventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = parent
        self.manager = BaseInventoryManager()
        self.selected_item_id = None
        self.selected_item_name = None
        self._current_guild_id = None
        self._current_guild_name = ''
        self._current_base_id = None
        self._current_base_name = ''
        self._guilds_data = []
        self._bases_data = []
        self._setup_ui()
        self._setup_connections()
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.setInterval(2000)
        self._auto_save_timer.timeout.connect(self._auto_save_changes)
    def _restore_container_selection(self, previous_container_id=None):
        if not previous_container_id:
            if self.container_list.topLevelItemCount() > 0:
                self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
            return
        for i in range(self.container_list.topLevelItemCount()):
            item = self.container_list.topLevelItem(i)
            if item.data(0, Qt.UserRole) == previous_container_id:
                self.container_list.setCurrentItem(item)
                return
        if self.container_list.topLevelItemCount() > 0:
            self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
    def refresh_labels(self):
        if hasattr(self, 'title_label'):
            self.title_label.setText(t('base_inventory.title', default='Base Inventory'))
        if hasattr(self, 'container_label'):
            self.container_label.setText(t('base_inventory.select_container') if t else 'Containers:')
        if hasattr(self, 'guild_button'):
            if self._current_guild_name:
                self.guild_button.setText(self._current_guild_name)
            else:
                self.guild_button.setText(t('base_inventory.select_guild') if t else 'Select Guild')
        if hasattr(self, 'base_button'):
            if self._current_base_name:
                self.base_button.setText(self._current_base_name)
            else:
                self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
        if hasattr(self, 'item_button'):
            if self.selected_item_id and self.selected_item_name:
                self.item_button.setText(self.selected_item_name)
            else:
                self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
        if hasattr(self, 'clear_item_button'):
            self.clear_item_button.setVisible(bool(self.selected_item_id))
            self.clear_item_button.setToolTip(t('base_inventory.clear_item') if t else 'Clear Item Filter')
        if hasattr(self, 'structure_button'):
            self.structure_button.setText(t('base_inventory.all_structures') if t else 'All Structures')
        if hasattr(self, 'inventory_grid'):
            self.inventory_grid.refresh_labels()
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('base_inventory.select_guild_base_hint', default='Select a Guild/Base to edit their inventory'))
        if hasattr(self, 'inv_tab_btn'):
            self.inv_tab_btn.setText(t('base_inventory.tab_inventory') if t else 'Inventory')
        if hasattr(self, 'pals_tab_btn'):
            self.pals_tab_btn.setText(t('base_inventory.tab_base_pals') if t else 'Base Pals')
        if hasattr(self, 'base_inv_loadout_btn'):
            self.base_inv_loadout_btn.setText(t('inventory.loadouts_btn', default='Loadouts'))
        if hasattr(self, 'base_inv_clear_btn'):
            self.base_inv_clear_btn.setText(t('inventory.clear_btn', default='Clear'))
        if hasattr(self, 'base_pals_widget'):
            self.base_pals_widget.refresh_labels()
        current_container_id = None
        if self.manager.current_container:
            current_container_id = self.manager.current_container.get('id')
        if self._current_base_id:
            self._load_containers_for_base(self._current_base_id)
            self._restore_container_selection(current_container_id)
        self._update_container_stats()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(t('base_inventory.title', default='Base Inventory'))
        self.title_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.title_label.setObjectName('sectionHeader')
        self.title_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label)
        self.guild_button = QPushButton(t('base_inventory.select_guild') if t else 'Select Guild')
        self.guild_button.setMinimumWidth(160)
        self.guild_button.setMaximumHeight(28)
        self.guild_button.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.guild_button.setCursor(Qt.PointingHandCursor)
        self.guild_button.clicked.connect(self._show_guild_popup)
        header_layout.addWidget(self.guild_button)
        self.base_button = QPushButton(t('base_inventory.select_base') if t else 'Select Base')
        self.base_button.setMinimumWidth(140)
        self.base_button.setMaximumHeight(28)
        self.base_button.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; } QPushButton:disabled { background: rgba(100,100,100,0.1); color: #666; border-color: rgba(255,255,255,0.05); }')
        self.base_button.setCursor(Qt.PointingHandCursor)
        self.base_button.clicked.connect(self._show_base_popup)
        header_layout.addWidget(self.base_button)
        self.inv_tab_btn = QPushButton(t('base_inventory.tab_inventory') if t else 'Inventory')
        self.inv_tab_btn.setFixedHeight(28)
        self.inv_tab_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.2); color: #fff; border: 1px solid rgba(125,211,252,0.4); border-radius: 6px; padding: 4px 12px; font-weight: 700; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.25); }')
        self.inv_tab_btn.setCursor(Qt.PointingHandCursor)
        self.inv_tab_btn.clicked.connect(lambda: self._switch_tab(0))
        header_layout.addWidget(self.inv_tab_btn)
        self.pals_tab_btn = QPushButton(t('base_inventory.tab_base_pals') if t else 'Base Pals')
        self.pals_tab_btn.setFixedHeight(28)
        self.pals_tab_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.pals_tab_btn.setCursor(Qt.PointingHandCursor)
        self.pals_tab_btn.clicked.connect(lambda: self._switch_tab(1))
        header_layout.addWidget(self.pals_tab_btn)
        header_layout.addStretch()
        self.item_button = QPushButton(t('base_inventory.all_items') if t else 'All Items')
        self.item_button.setMinimumWidth(100)
        self.item_button.setMaximumHeight(28)
        self.item_button.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.item_button.setCursor(Qt.PointingHandCursor)
        self.item_button.clicked.connect(self._show_item_picker)
        header_layout.addWidget(self.item_button)
        self.clear_item_button = QPushButton('×')
        self.clear_item_button.setFixedWidth(24)
        self.clear_item_button.setFixedHeight(28)
        self.clear_item_button.setStyleSheet('QPushButton { background: rgba(255,80,80,0.4); color: #fff; border: none; border-radius: 4px; font-weight: bold; font-size: 14px; } QPushButton:hover { background: rgba(255,80,80,0.7); }')
        self.clear_item_button.setCursor(Qt.PointingHandCursor)
        self.clear_item_button.setToolTip(t('base_inventory.clear_item') if t else 'Clear Item Filter')
        self.clear_item_button.clicked.connect(self._clear_item_filter)
        self.clear_item_button.setVisible(False)
        header_layout.addWidget(self.clear_item_button)
        self.structure_button = QPushButton(t('base_inventory.all_structures') if t else 'All Structures')
        self.structure_button.setMinimumWidth(120)
        self.structure_button.setMaximumHeight(28)
        self.structure_button.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.structure_button.setCursor(Qt.PointingHandCursor)
        self.structure_button.clicked.connect(self._show_structure_picker)
        header_layout.addWidget(self.structure_button)
        layout.addLayout(header_layout)
        self.content_area = QFrame()
        self.content_area.setObjectName('baseInventoryContent')
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setStyleSheet(f'QFrame#baseInventoryContent {{ {CONTENT_PANEL_STYLE} }}')
        layout.addWidget(self.content_area, 1)
        content_area_layout = QVBoxLayout(self.content_area)
        content_area_layout.setContentsMargins(0, 0, 0, 0)
        content_area_layout.setSpacing(0)
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet('QStackedWidget { border: none; background: transparent; }')
        content_area_layout.addWidget(self.content_stack)
        self.inventory_page = QFrame()
        inv_layout = QVBoxLayout(self.inventory_page)
        inv_layout.setContentsMargins(10, 10, 10, 10)
        inv_layout.setSpacing(0)
        self.placeholder_label = QLabel(t('base_inventory.select_guild_base_hint', default='Select a Guild/Base to edit their inventory'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setMinimumHeight(400)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setStyleSheet('QLabel { color: #888; font-size: 14px; background: transparent; }')
        inv_layout.addWidget(self.placeholder_label, 1)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        self.container_label = QLabel(t('base_inventory.select_container') if t else 'Containers:')
        self.container_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        left_layout.addWidget(self.container_label)
        self.container_list = ContainerListWidget(self)
        self.container_list.container_selected.connect(self._on_container_selected)
        left_layout.addWidget(self.container_list)
        self.container_info = ContainerInfoWidget()
        left_layout.addWidget(self.container_info)
        self.splitter.addWidget(left_panel)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        self.inventory_grid = InventoryGridWidget()
        right_layout.addWidget(self.inventory_grid)
        self.base_inv_loadout_btn = QPushButton(t('inventory.loadouts_btn', default='Loadouts'))
        self.base_inv_loadout_btn.setFixedHeight(24)
        self.base_inv_loadout_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.base_inv_loadout_btn.setCursor(Qt.PointingHandCursor)
        self.base_inv_loadout_btn.clicked.connect(self._on_inventory_loadout)
        self.inventory_grid.header_layout.insertWidget(self.inventory_grid.header_layout.indexOf(self.inventory_grid.sort_btn), self.base_inv_loadout_btn)
        self.base_inv_clear_btn = QPushButton(t('inventory.clear_btn', default='Clear'))
        self.base_inv_clear_btn.setFixedHeight(24)
        self.base_inv_clear_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.base_inv_clear_btn.setCursor(Qt.PointingHandCursor)
        self.base_inv_clear_btn.clicked.connect(self._clear_container)
        self.inventory_grid.header_layout.insertWidget(self.inventory_grid.header_layout.indexOf(self.inventory_grid.sort_btn) + 1, self.base_inv_clear_btn)
        self.inventory_grid.sort_requested.connect(self._on_base_sort_requested)
        self.splitter.addWidget(right_panel)
        inv_layout.addWidget(self.splitter)
        self.splitter.hide()
        self.splitter.setSizes([300, 700])
        self.content_stack.addWidget(self.inventory_page)
        self.base_pals_widget = BasePalsContentWidget()
        self.content_stack.addWidget(self.base_pals_widget)
        self._current_tab = 0
    def _switch_tab(self, index):
        self._current_tab = index
        self.content_stack.setCurrentIndex(index)
        inv_active = index == 0
        pals_active = index == 1
        self.inv_tab_btn.setStyleSheet(f"QPushButton {{ background: rgba(125,211,252,{('0.2' if inv_active else '0.12')}); color: {('#fff' if inv_active else '#7DD3FC')}; border: 1px solid rgba(125,211,252,{('0.4' if inv_active else '0.2')}); border-radius: 6px; padding: 4px 12px; font-weight: {('700' if inv_active else '600')}; font-size: 12px; }} QPushButton:hover {{ background: rgba(125,211,252,0.25); }}")
        self.pals_tab_btn.setStyleSheet(f"QPushButton {{ background: rgba(125,211,252,{('0.2' if pals_active else '0.12')}); color: {('#fff' if pals_active else '#7DD3FC')}; border: 1px solid rgba(125,211,252,{('0.4' if pals_active else '0.2')}); border-radius: 6px; padding: 4px 12px; font-weight: {('700' if pals_active else '600')}; font-size: 12px; }} QPushButton:hover {{ background: rgba(125,211,252,0.25); }}")
        if pals_active and self._current_base_id:
            from palworld_aio.base_inventory_manager import get_base_worker_pals
            pals = get_base_worker_pals(self._current_base_id)
            self.base_pals_widget.set_pals(pals, self._current_base_id)
        can_filter = inv_active
        self.item_button.setVisible(can_filter)
        self.clear_item_button.setVisible(can_filter and bool(self.selected_item_id))
        self.structure_button.setVisible(can_filter)
    def _create_styled_combo(self):
        combo = StyledCombo()
        combo.setMinimumWidth(180)
        combo.setMaxVisibleItems(12)
        return combo
    def _setup_connections(self):
        self.inventory_grid.item_context_menu.connect(self._show_item_context_menu)
        self.inventory_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.inventory_grid.item_double_clicked.connect(self._remove_item_from_slot)
        self.inventory_grid.empty_slot_double_clicked.connect(lambda ct, idx: self._add_item_to_slot(idx))
        self.inventory_grid.item_added.connect(self._trigger_auto_save)
        self.inventory_grid.item_removed.connect(self._trigger_auto_save)
        self.inventory_grid.item_count_changed.connect(self._trigger_auto_save)
    def _show_content(self):
        self.placeholder_label.hide()
        self.splitter.show()
    def _clear_display(self):
        self.splitter.hide()
        self.placeholder_label.show()
        self.container_list.clear()
        self.container_info.set_container_info(None)
        self.inventory_grid.clear()
        self.base_pals_widget.clear()
    def _update_theme(self):
        self.setStyleSheet('\n                QWidget {\n                    background-color: #121418;\n                    color: #e0e0e0;\n                }\n                QComboBox {\n                    background-color: rgba(30, 35, 45, 0.8);\n                    border: 1px solid rgba(255, 255, 255, 0.2);\n                    border-radius: 4px;\n                    padding: 4px 8px;\n                    color: #e0e0e0;\n                }\n                QComboBox::drop-down {\n                    border-left: 1px solid rgba(255, 255, 255, 0.2);\n                }\n                QPushButton {\n                    background-color: rgba(74, 144, 226, 0.8);\n                    border: 1px solid rgba(74, 144, 226, 1.0);\n                    border-radius: 4px;\n                    padding: 6px 12px;\n                    color: white;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: rgba(74, 144, 226, 1.0);\n                }\n                QPushButton:pressed {\n                    background-color: rgba(50, 120, 200, 1.0);\n                }\n                QSplitter::handle {\n                    background-color: rgba(255, 255, 255, 0.1);\n                }\n                QSplitter::handle:hover {\n                    background-color: rgba(255, 255, 255, 0.2);\n                }\n            ')
    def refresh(self):
        self.selected_item_id = None
        self.selected_item_name = None
        self._load_guilds()
        self._load_items()
        self.refresh_labels()
        if hasattr(self._main_window, 'parent') and hasattr(self._main_window.parent, 'results_widget'):
            pass
    def _show_guild_popup(self):
        popup = QWidget()
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        popup.setMinimumWidth(260)
        popup.setStyleSheet('QWidget { background: rgba(18,20,24,0.98); border: 1px solid rgba(125,211,252,0.2); border-radius: 8px; }')
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        search = QLineEdit()
        search.setPlaceholderText(t('common.search') if t else 'Search...')
        search.setStyleSheet(PICKER_SEARCH_STYLE)
        layout.addWidget(search)
        list_widget = QListWidget()
        list_widget.setStyleSheet('QListWidget { background: transparent; color: #e2e8f0; border: none; font-size: 12px; } QListWidget::item { padding: 3px 8px; border-radius: 3px; } QListWidget::item:hover { background: rgba(59,142,208,0.2); } QListWidget::item:selected { background: rgba(59,142,208,0.35); }')
        list_widget.setMaximumHeight(300)
        layout.addWidget(list_widget)
        clear_item = QListWidgetItem(t('common.clear') if t else '-- clear --')
        clear_item.setData(Qt.UserRole, '__clear__')
        list_widget.addItem(clear_item)
        for guild in self._guilds_data:
            item = QListWidgetItem(f"{guild['name']} (Level {guild['level']})")
            item.setData(Qt.UserRole, guild['id'])
            list_widget.addItem(item)
        def apply_filter(text):
            q = text.lower()
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(bool(q and q not in item.text().lower()))
        search.textChanged.connect(apply_filter)
        def select_guild(item):
            if item:
                guild_id = item.data(Qt.UserRole)
                if guild_id == '__clear__':
                    self._clear_guild_selection()
                elif guild_id:
                    self._on_guild_changed(guild_id)
            popup.close()
        list_widget.itemClicked.connect(select_guild)
        popup.move(self.guild_button.mapToGlobal(self.guild_button.rect().bottomLeft()))
        popup.show()
    def _clear_guild_selection(self):
        self._current_guild_id = None
        self._current_guild_name = ''
        self.guild_button.setText(t('base_inventory.select_guild') if t else 'Select Guild')
        self._bases_data = []
        self._current_base_id = None
        self._current_base_name = ''
        self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
        self._clear_display()
    def _show_base_popup(self):
        if not self._current_guild_id:
            return
        popup = QWidget()
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        popup.setMinimumWidth(260)
        popup.setStyleSheet('QWidget { background: rgba(18,20,24,0.98); border: 1px solid rgba(125,211,252,0.2); border-radius: 8px; }')
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        search = QLineEdit()
        search.setPlaceholderText(t('common.search') if t else 'Search...')
        search.setStyleSheet(PICKER_SEARCH_STYLE)
        layout.addWidget(search)
        list_widget = QListWidget()
        list_widget.setStyleSheet('QListWidget { background: transparent; color: #e2e8f0; border: none; font-size: 12px; } QListWidget::item { padding: 3px 8px; border-radius: 3px; } QListWidget::item:hover { background: rgba(59,142,208,0.2); } QListWidget::item:selected { background: rgba(59,142,208,0.35); }')
        list_widget.setMaximumHeight(300)
        layout.addWidget(list_widget)
        clear_item = QListWidgetItem(t('common.clear') if t else '-- clear --')
        clear_item.setData(Qt.UserRole, '__clear__')
        list_widget.addItem(clear_item)
        for base in self._bases_data:
            item = QListWidgetItem(f"{base['guild_name']} - Base {base['id'][:8]}")
            item.setData(Qt.UserRole, base['id'])
            list_widget.addItem(item)
        def apply_filter(text):
            q = text.lower()
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(bool(q and q not in item.text().lower()))
        search.textChanged.connect(apply_filter)
        def select_base(item):
            if item:
                base_id = item.data(Qt.UserRole)
                if base_id == '__clear__':
                    self._clear_base_selection()
                elif base_id:
                    self._on_base_changed(base_id)
            popup.close()
        list_widget.itemClicked.connect(select_base)
        popup.move(self.base_button.mapToGlobal(self.base_button.rect().bottomLeft()))
        popup.show()
    def _clear_base_selection(self):
        self._current_base_id = None
        self._current_base_name = ''
        self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
        self._clear_display()
    def _load_guilds(self):
        self._guilds_data = []
        self._bases_data = []
        self._current_guild_id = None
        self._current_guild_name = ''
        self._current_base_id = None
        self._current_base_name = ''
        self.guild_button.setText(t('base_inventory.select_guild') if t else 'Select Guild')
        self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
        guilds = self.manager.load_guilds()
        if not guilds:
            self.guild_button.setText(t('base_inventory.no_save_loaded') if t else 'No save file loaded')
            self.guild_button.setEnabled(False)
            self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
            self.base_button.setEnabled(False)
            self._clear_display()
            return
        guilds_with_bases = []
        for guild in guilds:
            bases = self.manager.load_bases_for_guild(guild['id'])
            if bases:
                guilds_with_bases.append(guild)
        if not guilds_with_bases:
            self._guilds_data = guilds
            self.guild_button.setText(t('base_inventory.no_guilds_with_bases') if t else 'No guilds with bases found')
            self.guild_button.setEnabled(True)
            self.base_button.setText(t('base_inventory.no_bases_available') if t else 'No bases available')
            self.base_button.setEnabled(False)
            self._clear_display()
            return
        self._guilds_data = guilds_with_bases
        self.guild_button.setEnabled(True)
        self.base_button.setEnabled(True)
        self._clear_display()
    def _on_guild_changed(self, guild_id):
        if guild_id is None:
            self._bases_data = []
            self._current_base_id = None
            self._current_base_name = ''
            self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
            self._clear_display()
            return
        self._current_guild_id = guild_id
        guild = next((g for g in self._guilds_data if str(g['id']) == str(guild_id)), None)
        self._current_guild_name = f"{guild['name']} (Level {guild['level']})" if guild else str(guild_id)
        self.guild_button.setText(self._current_guild_name)
        guild_id_key = str(guild_id).replace('-', '').lower()
        if hasattr(self, '_item_locations') and self._item_locations and guild_id_key and (guild_id_key in self._item_locations):
            self._load_bases_for_guild_filtered(guild_id)
        else:
            self._load_bases_for_guild(guild_id)
    def _load_bases_for_guild(self, guild_id):
        self._bases_data = []
        self._current_base_id = None
        self._current_base_name = ''
        bases = self.manager.load_bases_for_guild(guild_id)
        if not bases:
            self.base_button.setText(t('base_inventory.no_bases_found') if t else 'No bases found for this guild')
            self.base_button.setEnabled(False)
            self._clear_display()
            return
        self._bases_data = bases
        self.base_button.setEnabled(True)
        self._on_base_changed(bases[0]['id'])
    def _load_bases_for_guild_filtered(self, guild_id):
        self._bases_data = []
        self._current_base_id = None
        self._current_base_name = ''
        guild_id_key = str(guild_id).replace('-', '').lower() if guild_id else None
        if hasattr(self, '_item_locations') and guild_id_key and (guild_id_key in self._item_locations):
            filtered_bases = self._item_locations[guild_id_key]
            if filtered_bases:
                all_bases = self.manager.load_bases_for_guild(guild_id)
                self._bases_data = [base for base in all_bases if str(base['id']).replace('-', '').lower() in filtered_bases]
                if self._bases_data:
                    self.base_button.setEnabled(True)
                    self._on_base_changed(self._bases_data[0]['id'])
                else:
                    self.base_button.setText(t('base_inventory.no_bases_with_item') if t else 'No bases found with this item')
                    self.base_button.setEnabled(False)
                    self._clear_display()
            else:
                self.base_button.setText(t('base_inventory.no_bases_with_item') if t else 'No bases found with this item')
                self.base_button.setEnabled(False)
                self._clear_display()
        else:
            self._load_bases_for_guild(guild_id)
    def _on_base_changed(self, base_id):
        if base_id is None:
            self._current_base_id = None
            self._current_base_name = ''
            self.base_button.setText(t('base_inventory.select_base') if t else 'Select Base')
            self._clear_display()
            return
        self._current_base_id = base_id
        base = next((b for b in self._bases_data if str(b['id']) == str(base_id)), None)
        self._current_base_name = f"{base.get('guild_name', '')} - Base {str(base_id)[:8]}" if base else str(base_id)[:8]
        self.base_button.setText(self._current_base_name)
        guild_id_key = str(self._current_guild_id).replace('-', '').lower() if self._current_guild_id else None
        base_id_key = str(base_id).replace('-', '').lower()
        if hasattr(self, '_item_locations') and self._item_locations and guild_id_key and (guild_id_key in self._item_locations) and base_id_key and (base_id_key in self._item_locations.get(guild_id_key, {})):
            self._load_containers_for_base_filtered(base_id)
        else:
            self._load_containers_for_base(base_id)
        pals = get_base_worker_pals(base_id)
        self.base_pals_widget.set_pals(pals, base_id)
    def _load_containers_for_base(self, base_id):
        self.container_list.clear()
        guild_id = self._current_guild_id
        if guild_id:
            bases = self.manager.load_bases_for_guild(guild_id)
            base_info = next((b for b in bases if str(b['id']) == str(base_id)), None)
            if base_info:
                self.manager.current_base = base_info
        containers = self.manager.load_containers_for_base(base_id)
        for container in containers:
            self.container_list.add_container(container)
        if containers:
            if self.container_list.topLevelItemCount() > 0:
                self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
        else:
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
        self._show_content()
    def _load_containers_for_base_filtered(self, base_id):
        self.container_list.clear()
        guild_id = self._current_guild_id
        guild_id_key = str(guild_id).replace('-', '').lower() if guild_id else None
        base_id_key = str(base_id).replace('-', '').lower() if base_id else None
        if hasattr(self, '_item_locations') and self._item_locations and guild_id_key and (guild_id_key in self._item_locations):
            guild_data = self._item_locations[guild_id_key]
            if isinstance(guild_data, dict):
                if base_id_key and base_id_key in guild_data:
                    filtered_containers = guild_data[base_id_key]
                    if filtered_containers:
                        all_containers = self.manager.load_containers_for_base(base_id)
                        for container in all_containers:
                            container_id_key = str(container['id']).replace('-', '').lower()
                            if container_id_key in filtered_containers:
                                self.container_list.add_container(container)
                        if self.container_list.topLevelItemCount() > 0:
                            self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
                    else:
                        self.container_info.set_container_info(None)
                        self.inventory_grid.clear()
                    self._show_content()
                else:
                    self._load_containers_for_base(base_id)
            else:
                self._load_containers_for_base(base_id)
        else:
            self._load_containers_for_base(base_id)
    def _on_inventory_loadout(self):
        if not self.manager.inventory_container:
            from loading_manager import show_warning
            show_warning(self, t('base_inventory.loadouts_title', default='Inventory Loadouts'), t('base_inventory.select_container_first', default='Please select a container first'))
            return
        def _get_items():
            if not self.manager.inventory_container:
                return []
            return _group_inventory_items(self.manager.inventory_container.get_items())
        def _apply_items(regular, key_items, equipment=None):
            if not self.manager.inventory_container:
                return
            sc = self.manager.inventory_container._standardized_container
            for item in regular + key_items:
                slot_idx = self.manager.find_empty_slot()
                while slot_idx == -1 and sc.max_slots < 999:
                    sc.expand_capacity(sc.max_slots + 1)
                    self.manager.expand_container_capacity(self.manager.current_container['id'], sc.max_slots)
                    for c in self.manager.containers:
                        if c['id'] == self.manager.current_container['id']:
                            c['slot_count'] = sc.max_slots
                            break
                    self.container_list.update_slot_count_label(self.manager.current_container['id'], sc.max_slots)
                    self._on_container_selected(self.manager.current_container['id'])
                    slot_idx = self.manager.find_empty_slot()
                if slot_idx == -1:
                    break
                self.manager.add_item_to_slot(slot_idx, item['id'], item['qty'])
            _consolidate_container_slots(self.manager.inventory_container, 'main', SINGLETON_TYPE_A)
            self.manager.save_changes()
            self._refresh_container_ui()
        base_loadouts_path = os.path.join(constants.get_src_path(), 'data', 'configs', 'base_inventory_loadouts.json')
        dlg = InventoryLoadoutDialog(self, _get_items, _apply_items, loadouts_path=base_loadouts_path)
        dlg.exec()
    def _on_base_sort_requested(self):
        if not self.manager.inventory_container:
            return
        _consolidate_container_slots(self.manager.inventory_container, 'main', SINGLETON_TYPE_A)
        self.manager.save_changes()
        self._refresh_container_ui()
    def _on_container_selected(self, container_id):
        container_info = next((c for c in self.manager.containers if c['id'] == container_id), None)
        if container_info:
            self.container_info.set_container_info(container_info)
            inventory_container = self.manager.select_container(container_id)
            if inventory_container:
                items = inventory_container.get_items()
                max_slots = container_info['slot_count']
                self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
            else:
                self.inventory_grid.clear()
        else:
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
    def _update_container_stats(self):
        if self.manager.current_container and self.manager.inventory_container:
            filled_slots = self.manager.get_items_count()
            empty_slots = self.manager.get_empty_slots_count()
            self.container_info.items_count_label.setText(t('base_inventory.items').format(count=filled_slots) if t else f'Items: {filled_slots}')
            self.container_info.empty_slots_label.setText(t('base_inventory.empty').format(count=empty_slots) if t else f'Empty: {empty_slots}')
    def _on_item_count_changed(self, slot_index, new_count):
        self._update_container_stats()
    def _add_item(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        dialog = ItemPickerDialog(self, filter_exclude_type_a='EPalItemTypeA::Essential')
        dialog.item_selected.connect(lambda item_id, qty: self._do_add_item(item_id, qty))
        dialog.exec()
    def _do_add_item(self, item_id: str, count: int):
        if item_id and count > 0:
            empty_slot_index = self.manager.find_empty_slot()
            if empty_slot_index == -1:
                self._show_warning(t('base_inventory.container_full') if t else 'Container is full!')
                return
            if self.manager.add_item_to_slot(empty_slot_index, item_id, count):
                self._refresh_container_ui()
                self._update_container_stats()
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.failed_to_add_item') if t else 'Failed to add item')
    def _remove_item(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        self._show_info(t('base_inventory.use_context_menu') if t else 'Right-click on an item to remove it')
    def _clear_container(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        if show_question(self, t('base_inventory.clear_container') if t else 'Clear Container', t('base_inventory.clear_container_confirm') if t else 'Are you sure you want to clear all items from this container?'):
            container_id = self.manager.current_container['id'] if self.manager.current_container else None
            if container_id:
                if self.manager.clear_container(container_id):
                    self.manager.select_container(container_id)
                    self._refresh_container_ui()
                    self._update_container_stats()
                    self._show_info(t('base_inventory.container_cleared') if t else 'Container cleared successfully')
                else:
                    self._show_warning(t('base_inventory.failed_to_clear_container') if t else 'Failed to clear container')
            else:
                self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
    def _delete_container(self, container_id):
        container_info = next((c for c in self.manager.containers if c['id'] == container_id), None)
        if not container_info:
            return
        is_guild_chest = container_info.get('is_guild_chest', False)
        if is_guild_chest:
            self._show_warning('Cannot delete Guild Chest')
            return
        if show_question(self, t('base_inventory.delete_container') if t else 'Delete Container', t('base_inventory.delete_container_confirm') if t else 'Are you sure you want to delete this container and its map object? This action cannot be undone.'):
            if self.manager.delete_container(container_id):
                base_id = container_info.get('base_id')
                if base_id:
                    self._load_containers_for_base(base_id)
                    self._restore_container_selection()
                self._show_info(t('base_inventory.container_deleted') if t else 'Container deleted successfully')
            else:
                self._show_warning(t('base_inventory.failed_to_clear_container') if t else 'Failed to delete container')
    def _save_changes(self):
        if not self.manager.save_changes():
            self._show_warning(t('base_inventory.save_failed') if t else 'Failed to save changes')
            return
        self._show_info(t('base_inventory.save_success') if t else 'Changes saved successfully')
    def _refresh_container_ui(self):
        if self.manager.current_container:
            inventory_container = self.manager.select_container(self.manager.current_container['id'])
            if inventory_container:
                items = inventory_container.get_items()
                max_slots = inventory_container.get_max_slots()
                self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
    def _refresh_all(self):
        previous_guild_id = self._current_guild_id
        previous_base_id = self._current_base_id
        self._load_guilds()
        if previous_guild_id:
            self._on_guild_changed(previous_guild_id)
            if previous_base_id:
                self._on_base_changed(previous_base_id)
    def _filter_guilds_and_bases_by_item(self):
        if not self.selected_item_id:
            self._reset_filters()
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        start_time = time.time()
        try:
            item_locations = find_item_locations_efficient(self.selected_item_id)
            self._guilds_data = []
            if item_locations:
                all_guilds = self.manager.load_guilds()
                for guild in all_guilds:
                    guild_id_key = str(guild['id']).replace('-', '').lower()
                    if guild_id_key in item_locations:
                        self._guilds_data.append(guild)
                self._item_locations = item_locations
                if self._guilds_data:
                    self._on_guild_changed(self._guilds_data[0]['id'])
            else:
                display_name = self.selected_item_name or self._get_item_name(self.selected_item_id)
                message = t('base_inventory.no_guilds_with_item').format(item_name=display_name) if t else f'No guilds found with {display_name}'
                self._show_info(message)
                self._reset_filters()
                self.selected_item_id = None
                self.selected_item_name = None
                self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
                self.clear_item_button.setVisible(False)
        finally:
            QApplication.restoreOverrideCursor()
            elapsed = time.time() - start_time
            if elapsed > 0.5:
                if hasattr(self._main_window, 'status_bar'):
                    self._main_window.status_bar.showMessage(f'Item filter completed in {elapsed:.2f}s', 3000)
    def _reset_filters(self):
        self._item_locations = None
        self._load_guilds()
    def _load_items(self):
        if self.selected_item_id and self.selected_item_name:
            self.item_button.setText(self.selected_item_name)
            self.clear_item_button.setVisible(True)
        else:
            self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
            self.clear_item_button.setVisible(False)
    def _get_all_items(self):
        try:
            from palworld_aio.inventory_manager import ItemData
            all_items_list = ItemData.get_all_items()
            return {item.get('asset', ''): item.get('name', item.get('asset', '')) for item in all_items_list if item.get('asset')}
        except:
            pass
        all_items = {}
        all_guilds = self.manager.load_guilds()
        if all_guilds:
            for guild in all_guilds:
                guild_id = guild['id']
                bases = self.manager.load_bases_for_guild(guild_id)
                for base in bases:
                    base_id = base['id']
                    containers = self.manager.load_containers_for_base(base_id)
                    for container in containers:
                        container_id = container['id']
                        inventory_container = self.manager.select_container(container_id)
                        if inventory_container:
                            items = inventory_container.get_items()
                            for item in items:
                                item_id = item.get('item_id')
                                if item_id and item_id != '':
                                    item_name = item.get('item_name', item_id)
                                    all_items[item_id] = item_name
        return all_items
    def _show_info(self, message):
        show_information(self, t('info.title') if t else 'Information', message)
    def _show_warning(self, message):
        show_warning(self, t('warning.title') if t else 'Warning', message)
    def _show_item_context_menu(self, slot_data, pos):
        if not slot_data:
            return
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction(t('base_inventory.edit_quantity') if t else 'Edit Quantity', lambda: self._edit_item_quantity(slot_data))
        menu.addAction(t('base_inventory.remove_item') if t else 'Remove Item', lambda: self._remove_item_from_slot(slot_data))
        menu.addSeparator()
        menu.addAction(t('base_inventory.clear_container') if t else 'Clear Container', self._clear_container)
        menu.exec(pos)
    def _show_empty_slot_context_menu(self, container_type, slot_index, pos):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction(t('base_inventory.add_item') if t else 'Add Item', lambda: self._add_item_to_slot(slot_index))
        menu.addAction(t('base_inventory.clear_container') if t else 'Clear Container', self._clear_container)
        menu.exec(pos)
    def _edit_item_quantity(self, slot_data):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        current_count = slot_data.get('stack_count', 0)
        dlg = QInputDialog(self)
        dlg.setWindowTitle(t('base_inventory.edit_quantity') if t else 'Edit Quantity')
        dlg.setLabelText(t('base_inventory.current_count') if t else f'Current count: {current_count}')
        dlg.setIntValue(current_count)
        dlg.setIntRange(0, 9999)
        dlg.setIntStep(1)
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        ok = dlg.exec() == QDialog.Accepted
        new_count = dlg.intValue() if ok else current_count
        if ok:
            slot_index = slot_data.get('slot_index', 0)
            if self.manager.update_item_count(slot_index, new_count):
                inventory_container = self.manager.select_container(self.manager.current_container['id'])
                if inventory_container:
                    items = inventory_container.get_items()
                    max_slots = inventory_container.get_max_slots()
                    self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
            else:
                self._show_warning(t('base_inventory.failed_to_update_quantity') if t else 'Failed to update quantity')
    def _remove_item_from_slot(self, slot_data):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        slot_index = slot_data.get('slot_index', 0)
        item_name = slot_data.get('item_name', 'Unknown')
        if self.manager.remove_item(slot_index, 999999):
            inventory_container = self.manager.select_container(self.manager.current_container['id'])
            if inventory_container:
                items = inventory_container.get_items()
                max_slots = inventory_container.get_max_slots()
                self.inventory_grid.load_items(items, max_slots=max_slots)
            self._update_container_stats()
        else:
            self._show_warning(t('base_inventory.failed_to_remove_item') if t else 'Failed to remove item')
    def _add_item_to_slot(self, slot_index):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        dialog = ItemPickerDialog(self, filter_exclude_type_a='EPalItemTypeA::Essential')
        dialog.item_selected.connect(lambda item_id, qty: self._do_add_item_to_slot(slot_index, item_id, qty))
        dialog.exec()
    def _do_add_item_to_slot(self, slot_index: int, item_id: str, count: int):
        if item_id and count > 0:
            if self.manager.add_item_to_slot(slot_index, item_id, count):
                inventory_container = self.manager.select_container(self.manager.current_container['id'])
                if inventory_container:
                    items = inventory_container.get_items()
                    max_slots = inventory_container.get_max_slots()
                    self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.failed_to_add_item') if t else 'Failed to add item')
    def _trigger_auto_save(self):
        if self.manager.inventory_container:
            self._auto_save_timer.start()
    def _auto_save_changes(self):
        if not self.manager.inventory_container:
            return
        try:
            if self.manager.save_changes():
                if hasattr(self._main_window, 'status_bar'):
                    self._main_window.status_bar.showMessage(t('base_inventory.auto_save_success') if t else 'Auto-saved changes', 2000)
            else:
                self._show_warning(t('base_inventory.auto_save_failed') if t else 'Auto-save failed - changes not saved')
        except Exception as e:
            self._show_warning(f'Auto-save error: {str(e)}')
    def _show_item_picker(self):
        dialog = GuildItemPickerDialog(self)
        dialog.item_action_selected.connect(self._on_item_action_selected)
        dialog.exec()
    def _on_item_action_selected(self, item_id: str, action: str, guild_ids: list=None):
        item_name = self._get_item_name(item_id)
        if action == 'find':
            if item_name:
                self.selected_item_id = item_id
                self.selected_item_name = item_name
                self.item_button.setText(item_name)
                self.clear_item_button.setVisible(True)
                self._filter_guilds_and_bases_by_item()
        elif action == 'economy':
            from palworld_aio.base_inventory_manager import get_item_economy_stats
            stats = get_item_economy_stats(item_id)
            if stats:
                dialog = EconomyStatsDialog(stats, item_name, self)
                dialog.exec()
            else:
                self._show_warning(t('base_inventory.economy_failed') if t else 'Failed to get economy stats')
        elif action.startswith('remove_pct:'):
            percentage = int(action.split(':')[1])
            from palworld_aio.base_inventory_manager import remove_item_from_guilds
            result = remove_item_from_guilds(item_id, percentage, guild_ids)
            if result and result.get('removed', 0) > 0:
                guilds_count = len(guild_ids) if guild_ids else 0
                msg = t('base_inventory.items_removed').format(count=result.get('removed', 0), guilds=guilds_count) if t else f"Removed {result.get('removed', 0)} items from {guilds_count} guilds"
                containers = result.get('containers_affected', 0)
                if containers > 0:
                    msg += f" ({(t('base_inventory.containers_affected').format(count=containers) if t else f'{containers} containers affected')})"
                self._show_info(msg)
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.no_items_removed') if t else 'No items found to remove')
        elif action == 'remove_all':
            from palworld_aio.base_inventory_manager import remove_item_from_guilds
            result = remove_item_from_guilds(item_id, None, guild_ids)
            if result and result.get('removed', 0) > 0:
                guilds_count = len(guild_ids) if guild_ids else 0
                msg = t('base_inventory.items_removed').format(count=result.get('removed', 0), guilds=guilds_count) if t else f"Removed {result.get('removed', 0)} items from {guilds_count} guilds"
                containers = result.get('containers_affected', 0)
                if containers > 0:
                    msg += f" ({(t('base_inventory.containers_affected').format(count=containers) if t else f'{containers} containers affected')})"
                self._show_info(msg)
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.no_items_removed') if t else 'No items found to remove')
    def _get_item_name(self, item_id: str) -> str:
        if not item_id:
            return item_id
        try:
            from palworld_aio.inventory_manager import ItemData
            item_data = ItemData.get_item_by_asset(item_id)
            if item_data and item_data.get('name'):
                return item_data['name']
        except:
            pass
        try:
            all_items = self._get_all_items()
            if item_id in all_items:
                return all_items[item_id]
        except:
            pass
        return item_id.replace('_', ' ').replace('EPalStaticItemId::', '').title()
    def _clear_item_filter(self):
        self.selected_item_id = None
        self.selected_item_name = None
        self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
        self.clear_item_button.setVisible(False)
        self._reset_filters()
    def _show_structure_picker(self):
        dialog = GuildStructurePickerDialog(self)
        dialog.structure_action_selected.connect(self._on_structure_action_selected)
        dialog.exec()
    def _on_structure_action_selected(self, structure_asset: str, action: str, guild_ids: list=None):
        structure_name = structure_asset.replace('_', ' ').title()
        if action == 'find':
            self._filter_guilds_and_bases_by_structure(structure_asset)
        elif action == 'delete_all':
            from palworld_aio.base_inventory_manager import remove_structure_from_guilds
            result = remove_structure_from_guilds(structure_asset, guild_ids)
            if result and result.get('removed', 0) > 0:
                guilds_count = len(guild_ids) if guild_ids else 0
                msg = t('base_inventory.structures_removed').format(count=result.get('removed', 0), guilds=guilds_count) if t else f"Removed {result.get('removed', 0)} structures from {guilds_count} guilds"
                containers = result.get('containers_affected', 0)
                if containers > 0:
                    msg += f" ({(t('base_inventory.structures_affected').format(count=containers) if t else f'{containers} containers affected')})"
                self._show_info(msg)
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.no_structures_removed') if t else 'No structures found to remove')
    def _filter_guilds_and_bases_by_structure(self, structure_asset):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            from palworld_aio.base_inventory_manager import find_structure_locations_efficient
            locations = find_structure_locations_efficient(structure_asset)
            self._guilds_data = []
            if locations:
                all_guilds = self.manager.load_guilds()
                for guild in all_guilds:
                    guild_id_key = str(guild['id']).replace('-', '').lower()
                    if guild_id_key in locations:
                        self._guilds_data.append(guild)
                if self._guilds_data:
                    self._on_guild_changed(self._guilds_data[0]['id'])
                    if hasattr(self._main_window, 'status_bar'):
                        self._main_window.status_bar.showMessage(f'Found {structure_asset} in {len(self._guilds_data)} guild(s)', 3000)
            else:
                self._show_info(t('base_inventory.no_structures') if t else f'No guilds found with this structure')
                self._load_guilds()
        finally:
            QApplication.restoreOverrideCursor()
    def _modify_container_slots(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        container_info = self.manager.current_container
        if not container_info:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        container_id = container_info['id']
        from palworld_aio import constants
        constants.invalidate_container_lookup()
        self.manager.select_container(container_id)
        container_info = self.manager.current_container
        if not container_info:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        current_slots = container_info['slot_count']
        current_items = self.manager.get_items_count()
        dialog = ContainerSlotModificationDialog(self, current_slots, current_items)
        if dialog.exec() == QDialog.Accepted:
            new_slot_count = dialog.get_slot_count()
            if new_slot_count != current_slots:
                if self.manager.expand_container_capacity(container_info['id'], new_slot_count):
                    current_container_id = container_info['id']
                    base_id = self._current_base_id
                    if base_id:
                        self._load_containers_for_base(base_id)
                        self._restore_container_selection(current_container_id)
            self._trigger_save()