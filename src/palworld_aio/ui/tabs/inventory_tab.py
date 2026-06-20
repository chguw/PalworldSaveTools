import os
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QLabel, QPushButton, QFrame, QDialog, QLineEdit, QListWidget, QListWidgetItem, QSpinBox, QMessageBox, QTabWidget, QSizePolicy, QAbstractItemView, QMenu, QToolTip, QListView, QProgressBar, QComboBox, QApplication, QInputDialog
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer, QThread
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor, QColor, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate
from i18n import t
from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLE, STATS_PANEL_STYLE, MENU_STYLE, PICKER_BG_STYLE, PICKER_SEARCH_STYLE, PICKER_LIST_STYLE, wrap_tooltip_text, slot_full, slot_rarity, slot_selected, CONTENT_PANEL_STYLE, SLOT_EMPTY_STYLE, SLOT_HOVER_STYLE
from palsav import json_tools
from palworld_aio import constants as _constants
from palworld_aio.inventory.inventory_manager import PlayerInventory, ItemData, get_player_inventory, UI_SLOT_BINDINGS, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS, WEAPON_UNLOCK_ITEMS, INVENTORY_EXPANSION_ITEMS
from palworld_aio.editor.edit_pals import _clean_desc_for_tooltip
from palworld_aio.managers.player_manager import max_all_abilities
from resource_resolver import resource_path
SINGLETON_TYPE_A = {'EPalItemTypeA::Weapon', 'EPalItemTypeA::MonsterEquipWeapon', 'EPalItemTypeA::Armor', 'EPalItemTypeA::Accessory', 'EPalItemTypeA::Glider', 'EPalItemTypeA::CaptureItemModifier'}
from palworld_aio import constants
EQUIP_SLOT_FILTERS = {'weapon': {'type_a': ['EPalItemTypeA::Weapon', 'EPalItemTypeA::MonsterEquipWeapon']}, 'head': {'type_a': 'EPalItemTypeA::Armor', 'type_b': 'EPalItemTypeB::ArmorHead'}, 'body': {'type_a': 'EPalItemTypeA::Armor', 'type_b': 'EPalItemTypeB::ArmorBody'}, 'shield': {'type_a': 'EPalItemTypeA::Armor', 'type_b': 'EPalItemTypeB::Shield'}, 'accessory': {'type_a': 'EPalItemTypeA::Accessory'}, 'glider': {'type_a': 'EPalItemTypeA::Glider'}, 'sphere_mod': {'type_a': 'EPalItemTypeA::CaptureItemModifier'}, 'food': {'type_a': 'EPalItemTypeA::Food'}}
GRID_COLS = 6
GRID_ROWS = 9
SLOT_SIZE = 56
class ItemSlotWidget(QFrame):
    clicked = Signal(object)
    double_clicked = Signal(object)
    context_menu_requested = Signal(object, QPoint)
    def __init__(self, slot_index: int, container_type: str='main', parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.container_type = container_type
        self.slot_data = None
        self.setFixedSize(SLOT_SIZE, SLOT_SIZE)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        self._apply_empty_style()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(40, 40)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.qty_label = QLabel()
        self.qty_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.qty_label.setStyleSheet('font-size: 10px; font-weight: bold; color: white; background: transparent;')
        layout.addWidget(self.qty_label, alignment=Qt.AlignRight)
    def _apply_empty_style(self):
        self.setStyleSheet(slot_full('ItemSlotWidget'))
        self.icon_label.clear()
        self.qty_label.clear()
    def set_item(self, slot_data: dict):
        self.slot_data = slot_data
        if not slot_data or not slot_data.get('item_id'):
            self._apply_empty_style()
            return
        icon_path = slot_data.get('icon_path', '')
        if icon_path:
            pixmap = ItemData.get_item_icon(icon_path, QSize(40, 40))
            self.icon_label.setPixmap(pixmap)
        stack_count = slot_data.get('stack_count', 1)
        if stack_count > 1:
            self.qty_label.setText(str(stack_count))
        else:
            self.qty_label.clear()
        rarity = slot_data.get('rarity', 0)
        self._apply_rarity_style(rarity)
    def _apply_rarity_style(self, rarity: int):
        if rarity <= 0:
            color = '#aaaaaa'
        elif rarity <= 1:
            color = '#4ade80'
        elif rarity <= 2:
            color = '#60a5fa'
        elif rarity <= 3:
            color = '#a855f7'
        else:
            color = '#fbbf24'
        self.setStyleSheet(slot_rarity('ItemSlotWidget', color))
    def clear_item(self):
        self.slot_data = None
        self._apply_empty_style()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.slot_data)
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.slot_data)
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(self.slot_data, event.globalPos())
    def enterEvent(self, event):
        if self.slot_data:
            item_name = self.slot_data.get('item_name', 'Unknown')
            qty = self.slot_data.get('stack_count', 1)
            item_id = self.slot_data.get('item_id', '')
            item_desc = self.slot_data.get('description', '')
            tooltip = f'<b>{item_name}</b><br>Qty: {qty}<br><i>{item_id}</i>'
            if item_desc:
                cleaned = _clean_desc_for_tooltip(item_desc)
                tooltip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(cleaned)}</span>'
            QToolTip.showText(QCursor.pos(), tooltip)
        super().enterEvent(event)
class EquipmentSlotWidget(QFrame):
    item_changed = Signal(str, object)
    double_clicked = Signal(object)
    context_menu_requested = Signal(object, QPoint)
    unlock_requested = Signal(str)
    def __init__(self, slot_name: str, label: str, parent=None):
        super().__init__(parent)
        self.slot_name = slot_name
        self.current_item = None
        self._locked = False
        self._lock_type = None
        self.setFixedSize(56, 70)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui(label)
        self._apply_style()
    def _setup_ui(self, label: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('font-size: 8px; font-weight: bold; color: #aaa;')
        layout.addWidget(self.label)
        icon_container = QWidget()
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(36, 36)
        icon_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.qty_label = QLabel()
        self.qty_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.qty_label.setStyleSheet('font-size: 9px; font-weight: bold; color: white; background: transparent;')
        icon_layout.addWidget(self.qty_label, alignment=Qt.AlignRight)
        layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet('font-size: 7px; color: #888;')
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
    def _apply_style(self):
        self.setStyleSheet(slot_full('EquipmentSlotWidget'))
    def set_item(self, slot_data: dict):
        self.current_item = slot_data
        if not slot_data:
            self.icon_label.clear()
            self.name_label.clear()
            self.qty_label.clear()
            self._apply_style()
            return
        icon_path = slot_data.get('icon_path', '')
        if icon_path:
            pixmap = ItemData.get_item_icon(icon_path, QSize(36, 36))
            self.icon_label.setPixmap(pixmap)
        name = slot_data.get('item_name', '')
        if len(name) > 10:
            name = name[:8] + '..'
        self.name_label.setText(name)
        stack_count = slot_data.get('stack_count', 1)
        category = slot_data.get('category', 'misc')
        if stack_count > 1 or category == 'food':
            self.qty_label.setText(str(stack_count))
        else:
            self.qty_label.clear()
        rarity = slot_data.get('rarity', 0)
        if rarity <= 0:
            color = '#aaaaaa'
        elif rarity <= 1:
            color = '#4ade80'
        elif rarity <= 2:
            color = '#60a5fa'
        elif rarity <= 3:
            color = '#a855f7'
        else:
            color = '#fbbf24'
        self.setStyleSheet(slot_rarity('EquipmentSlotWidget', color))
    def set_locked(self, locked: bool, lock_type: str=None):
        self._locked = locked
        self._lock_type = lock_type if locked else None
        if locked:
            self.setEnabled(True)
            self.setCursor(Qt.PointingHandCursor)
            self.icon_label.setText('🔒')
            self.icon_label.setStyleSheet('font-size: 20px;')
            self.name_label.setText(t('inventory.locked', default='Locked'))
            self.name_label.setStyleSheet('font-size: 7px; color: #faa61a;')
            self.qty_label.clear()
            self.setStyleSheet('EquipmentSlotWidget { background: rgba(255,255,255,0.03); border: 2px dashed #faa61a; border-radius: 8px; } EquipmentSlotWidget:hover { background: rgba(125,211,252,0.06); border: 2px dashed #ffc107; }')
        else:
            self.setEnabled(True)
            self.setCursor(Qt.PointingHandCursor)
            self.icon_label.clear()
            self.icon_label.setStyleSheet('')
            self.name_label.clear()
            self.name_label.setStyleSheet('font-size: 7px; color: #888;')
            self.qty_label.clear()
            self._apply_style()
    def is_locked(self) -> bool:
        return self._locked
    def clear_item(self):
        self.current_item = None
        self.icon_label.clear()
        self.name_label.clear()
        self.qty_label.clear()
        if not self._locked:
            self._apply_style()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._locked:
            self.unlock_requested.emit(self.slot_name)
            return
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self._locked:
            self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self, event):
        if self._locked:
            return
        self.context_menu_requested.emit(self, event.globalPos())
    def enterEvent(self, event):
        if self._locked:
            if self._lock_type == 'food':
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b><br>{t('inventory.unlock_hint_food', default='Click to unlock with AutoMealPouch')}"
            elif self._lock_type == 'accessory':
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b><br>{t('inventory.unlock_hint_accessory', default='Click to unlock with Accessory Slot Item')}"
            elif self._lock_type == 'weapon':
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b><br>{t('inventory.unlock_hint_weapon', default='Click to unlock with Weapon Slot Item')}"
            else:
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b>"
            QToolTip.showText(QCursor.pos(), tooltip)
        elif self.current_item:
            item_name = self.current_item.get('item_name', 'Unknown')
            item_id = self.current_item.get('item_id', '')
            item_desc = self.current_item.get('description', '')
            tooltip = f'<b>{item_name}</b><br><i>{item_id}</i>'
            if item_desc:
                cleaned = _clean_desc_for_tooltip(item_desc)
                tooltip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(cleaned)}</span>'
            QToolTip.showText(QCursor.pos(), tooltip)
        super().enterEvent(event)
def _load_exp_table():
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        levels = sorted(data.keys(), key=int)
        return [data[lvl]['TotalEXP'] for lvl in levels]
    except Exception as e:
        print(f'Error loading EXP table: {e}')
        return [0]
EXP_TABLE = _load_exp_table()
class StatsPanelWidget(QFrame):
    stats_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(160)
        self._stat_values = {}
        self._stat_inputs = {}
        self._stat_name_labels = {}
        self._current_level = 1
        self._current_exp = 0
        self._setup_ui()
        self._apply_style()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        self.stats_title = QLabel(t('inventory.stats', default='Stats'))
        self.stats_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #fff;')
        self.stats_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_title)
        level_frame = QFrame()
        level_layout = QHBoxLayout(level_frame)
        level_layout.setContentsMargins(0, 0, 0, 0)
        level_layout.setSpacing(2)
        minus_btn = QPushButton('-')
        minus_btn.setFixedSize(20, 20)
        minus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
        minus_btn.clicked.connect(self._decrease_level)
        self.level_label = QLabel(t('inventory.level', default='Lv.'))
        self.level_label.setStyleSheet('font-size: 11px; font-weight: bold; color: #aaa;')
        self.level_input = QLineEdit('1')
        self.level_input.setFixedWidth(40)
        self.level_input.setAlignment(Qt.AlignCenter)
        self.level_input.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 3px; padding: 2px; font-size: 12px; font-weight: bold; }')
        self.level_input.returnPressed.connect(self._on_level_input_changed)
        self.level_input.editingFinished.connect(self._on_level_input_changed)
        plus_btn = QPushButton('+')
        plus_btn.setFixedSize(20, 20)
        plus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
        plus_btn.clicked.connect(self._increase_level)
        level_layout.addWidget(minus_btn)
        level_layout.addWidget(self.level_label)
        level_layout.addWidget(self.level_input)
        level_layout.addStretch()
        level_layout.addWidget(plus_btn)
        layout.addWidget(level_frame)
        self.exp_bar = QProgressBar()
        self.exp_bar.setFixedHeight(6)
        self.exp_bar.setRange(0, 100)
        self.exp_bar.setValue(0)
        self.exp_bar.setTextVisible(False)
        self.exp_bar.setStyleSheet('QProgressBar { background-color: #333; border: 1px solid #555; border-radius: 3px; } QProgressBar::chunk { background-color: #43b581; border-radius: 2px; }')
        layout.addWidget(self.exp_bar)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('background-color: #444;')
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        stat_names = [('hp', t('inventory.stats.hp', default='HP'), 0), ('stamina', t('inventory.stats.stamina', default='Stamina'), 0), ('attack', t('inventory.stats.attack', default='Attack'), 0), ('defense', t('inventory.stats.defense', default='Defense'), 0), ('work_speed', t('inventory.stats.work_speed', default='Work'), 0), ('weight', t('inventory.stats.weight', default='Weight'), 0)]
        for key, label, default in stat_names:
            stat_frame = QFrame()
            stat_frame.setFixedHeight(26)
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 2, 0, 2)
            stat_layout.setSpacing(3)
            minus_btn = QPushButton('-')
            minus_btn.setFixedSize(22, 22)
            minus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
            minus_btn.clicked.connect(lambda checked, k=key: self._adjust_stat(k, -1))
            name_label = QLabel(label)
            name_label.setStyleSheet('font-size: 10px; color: #aaa;')
            name_label.setFixedWidth(48)
            stat_input = QLineEdit(str(default))
            stat_input.setFixedWidth(48)
            stat_input.setAlignment(Qt.AlignCenter)
            stat_input.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 3px; padding: 2px; font-size: 11px; } QLineEdit:focus { border-color: rgba(125,211,252,0.4); }')
            stat_input.returnPressed.connect(lambda k=key: self._on_stat_input_changed(k))
            stat_input.editingFinished.connect(lambda k=key: self._on_stat_input_changed(k))
            plus_btn = QPushButton('+')
            plus_btn.setFixedSize(22, 22)
            plus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
            plus_btn.clicked.connect(lambda checked, k=key: self._adjust_stat(k, 1))
            stat_layout.addWidget(minus_btn)
            stat_layout.addWidget(name_label)
            stat_layout.addWidget(stat_input)
            stat_layout.addStretch()
            stat_layout.addWidget(plus_btn)
            layout.addWidget(stat_frame)
            self._stat_name_labels[key] = name_label
            self._stat_inputs[key] = stat_input
            self._stat_values[key] = default
        layout.addStretch()
    def _on_level_input_changed(self):
        try:
            new_level = int(self.level_input.text())
            new_level = max(1, min(80, new_level))
            if new_level != self._current_level:
                self._current_level = new_level
                self._current_exp = EXP_TABLE[self._current_level - 1]
                self._update_level_display()
                self.stats_changed.emit()
        except ValueError:
            self.level_input.setText(str(self._current_level))
    def _increase_level(self):
        if self._current_level < 80:
            self._current_level += 1
            self._current_exp = EXP_TABLE[self._current_level - 1]
            self._update_level_display()
            self.stats_changed.emit()
    def _decrease_level(self):
        if self._current_level > 1:
            self._current_level -= 1
            self._current_exp = EXP_TABLE[self._current_level - 1]
            self._update_level_display()
            self.stats_changed.emit()
    def _update_level_display(self):
        self.level_input.blockSignals(True)
        self.level_input.setText(str(self._current_level))
        self.level_input.blockSignals(False)
        if self._current_level >= 80:
            self.exp_bar.setValue(100)
        else:
            current_level_exp = EXP_TABLE[self._current_level - 1]
            next_level_exp = EXP_TABLE[self._current_level]
            exp_in_level = self._current_exp - current_level_exp
            exp_needed = next_level_exp - current_level_exp
            if exp_needed > 0:
                percent = int(exp_in_level / exp_needed * 100)
                self.exp_bar.setValue(min(100, max(0, percent)))
            else:
                self.exp_bar.setValue(0)
    def _on_stat_input_changed(self, key: str):
        if key not in self._stat_inputs:
            return
        try:
            new_val = int(self._stat_inputs[key].text())
            new_val = max(0, min(9999, new_val))
            if new_val != self._stat_values[key]:
                self._stat_values[key] = new_val
                self.stats_changed.emit()
            else:
                self._stat_inputs[key].blockSignals(True)
                self._stat_inputs[key].setText(str(self._stat_values[key]))
                self._stat_inputs[key].blockSignals(False)
        except ValueError:
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(self._stat_values[key]))
            self._stat_inputs[key].blockSignals(False)
    def _adjust_stat(self, key: str, delta: int):
        if key in self._stat_values:
            new_val = self._stat_values[key] + delta
            new_val = max(0, min(9999, new_val))
            self._stat_values[key] = new_val
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(new_val))
            self._stat_inputs[key].blockSignals(False)
            self.stats_changed.emit()
    def _apply_style(self):
        self.setStyleSheet(STATS_PANEL_STYLE)
    def update_stats(self, stats: dict):
        for key, value in stats.items():
            if key in self._stat_inputs:
                if isinstance(value, str):
                    try:
                        val = int(value.split('/')[0])
                    except:
                        val = 0
                else:
                    val = int(value)
                self._stat_values[key] = val
                self._stat_inputs[key].blockSignals(True)
                self._stat_inputs[key].setText(str(val))
                self._stat_inputs[key].blockSignals(False)
    def get_stats(self) -> dict:
        return {key: val for key, val in self._stat_values.items()}
    def get_level(self) -> int:
        return self._current_level
    def get_exp(self) -> int:
        return self._current_exp
    def set_level(self, level: int, exp_percent: int):
        self._current_level = max(1, min(80, level))
        self._current_exp = EXP_TABLE[self._current_level - 1]
        self._update_level_display()
    def refresh_labels(self):
        stat_names = {'hp': t('inventory.stats.hp', default='HP'), 'stamina': t('inventory.stats.stamina', default='Stamina'), 'attack': t('inventory.stats.attack', default='Attack'), 'defense': t('inventory.stats.defense', default='Defense'), 'work_speed': t('inventory.stats.work_speed', default='Work'), 'weight': t('inventory.stats.weight', default='Weight')}
        self.stats_title.setText(t('inventory.stats', default='Stats'))
        self.level_label.setText(t('inventory.level', default='Lv.'))
        for key, label_name in stat_names.items():
            if key in self._stat_name_labels:
                self._stat_name_labels[key].setText(label_name)
    def clear(self):
        self._current_level = 1
        self._current_exp = 0
        self._update_level_display()
        for key in self._stat_inputs:
            self._stat_values[key] = 0
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText('0')
            self._stat_inputs[key].blockSignals(False)
class InventoryGridWidget(QWidget):
    item_added = Signal(int, str, int)
    item_removed = Signal(int, int)
    item_count_changed = Signal(int, int)
    item_context_menu = Signal(dict, QPoint)
    empty_slot_context_menu = Signal(str, int, QPoint)
    item_double_clicked = Signal(dict)
    empty_slot_double_clicked = Signal(str, int)
    item_selected = Signal(dict)
    add_all_effigies_requested = Signal()
    add_all_key_items_requested = Signal()
    clear_key_items_requested = Signal()
    sort_requested = Signal()
    def __init__(self, container_type: str='main', parent=None):
        super().__init__(parent)
        self.container_type = container_type
        self.slots = {}
        self.current_items = []
        self.max_visible_slots = 42
        self.header_layout = None
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        header = QHBoxLayout()
        self.header_layout = header
        self.tab_label = QLabel(t(f'inventory.{self.container_type}', default=self.container_type.title()))
        self.tab_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.tab_label.setObjectName('sectionHeader')
        self.tab_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.tab_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.tab_label)
        header.addStretch()
        self.sort_btn = QPushButton(t('inventory.sort', default='Sort'))
        self.sort_btn.setFixedHeight(24)
        self.sort_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.clicked.connect(self._sort_items)
        self.effigies_btn = QPushButton(t('inventory.max_all_abilities', default='Max All Abilities'))
        self.effigies_btn.setFixedHeight(24)
        self.effigies_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,191,36,0.25); border-color: rgba(251,191,36,0.5); color: #FFFFFF; }')
        self.effigies_btn.setCursor(Qt.PointingHandCursor)
        self.effigies_btn.clicked.connect(self.add_all_effigies_requested.emit)
        self.effigies_btn.setVisible(self.container_type == 'key_items')
        header.addWidget(self.effigies_btn)
        self.key_items_btn = QPushButton(t('inventory.add_all_key_items', default='Add All Key Items'))
        self.key_items_btn.setFixedHeight(24)
        self.key_items_btn.setStyleSheet('QPushButton { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(99,102,241,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(99,102,241,0.25); border-color: rgba(99,102,241,0.5); color: #FFFFFF; }')
        self.key_items_btn.setCursor(Qt.PointingHandCursor)
        self.key_items_btn.clicked.connect(self.add_all_key_items_requested.emit)
        self.key_items_btn.setVisible(self.container_type == 'key_items')
        header.addWidget(self.key_items_btn)
        self.clear_key_btn = QPushButton(t('inventory.clear_key_btn', default='Clear'))
        self.clear_key_btn.setFixedHeight(24)
        self.clear_key_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.clear_key_btn.setCursor(Qt.PointingHandCursor)
        self.clear_key_btn.setVisible(self.container_type == 'key_items')
        self.clear_key_btn.clicked.connect(self.clear_key_items_requested.emit)
        header.addWidget(self.clear_key_btn)
        self.sort_btn = QPushButton(t('inventory.sort', default='Sort'))
        self.sort_btn.setFixedHeight(24)
        self.sort_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.clicked.connect(self.sort_requested.emit)
        header.addWidget(self.sort_btn)
        main_layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.grid_widget)
        main_layout.addWidget(scroll)
    def set_max_slots(self, max_slots: int):
        if max_slots == self.max_visible_slots and self.slots:
            return
        self.max_visible_slots = max_slots
        for slot in self.slots.values():
            slot.deleteLater()
        self.slots.clear()
        for i in range(max_slots):
            row = i // GRID_COLS
            col = i % GRID_COLS
            slot = ItemSlotWidget(i, self.container_type)
            slot.clicked.connect(self._on_slot_clicked)
            slot.double_clicked.connect(self._on_slot_double_clicked)
            slot.context_menu_requested.connect(self._on_slot_context_menu)
            self.grid_layout.addWidget(slot, row, col)
            self.slots[i] = slot
    def load_items(self, items: list, max_slots: int=None):
        if max_slots is not None:
            self.set_max_slots(max_slots)
        self.current_items = items
        for slot in self.slots.values():
            slot.clear_item()
        for item in items:
            slot_index = item.get('slot_index', 0)
            if slot_index in self.slots:
                self.slots[slot_index].set_item(item)
    def _on_slot_clicked(self, slot_data):
        pass
    def _on_slot_double_clicked(self, slot_data):
        if slot_data:
            self.item_double_clicked.emit(slot_data)
        else:
            sender = self.sender()
            for idx, w in self.slots.items():
                if w == sender:
                    self.empty_slot_double_clicked.emit(self.container_type, idx)
                    break
    def _on_slot_context_menu(self, slot_data, pos):
        if slot_data:
            self.item_context_menu.emit(slot_data, pos)
        else:
            for idx, slot_widget in self.slots.items():
                widget_pos = slot_widget.mapFromGlobal(pos)
                if slot_widget.rect().contains(widget_pos):
                    self.empty_slot_context_menu.emit(self.container_type, idx, pos)
                    break
    def _sort_items(self):
        if not self.current_items:
            return
        sorted_items = sorted(self.current_items, key=lambda x: (x.get('category', 'zzz'), x.get('item_name', '')))
        for i, item in enumerate(sorted_items):
            item['slot_index'] = i
        self.load_items(sorted_items)
    def refresh_labels(self):
        self.tab_label.setText(t(f'inventory.{self.container_type}', default=self.container_type.title()))
        self.sort_btn.setText(t('inventory.sort', default='Sort'))
        self.effigies_btn.setText(t('inventory.max_all_abilities', default='Max All Abilities'))
        self.key_items_btn.setText(t('inventory.add_all_key_items', default='Add All Key Items'))
        self.clear_key_btn.setText(t('inventory.clear_key_btn', default='Clear'))
    def clear(self):
        self.load_items([])
    def get_selected_slot(self):
        return None
    def get_item_count(self, slot_index):
        if slot_index in self.slots:
            slot_widget = self.slots[slot_index]
            slot_data = slot_widget.slot_data
            if slot_data:
                return slot_data.get('stack_count', 0)
        return 0
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
class ItemPickerDialog(QDialog):
    item_selected = Signal(str, int)
    def __init__(self, parent=None, filter_type_a=None, filter_type_b=None, filter_exclude_type_a=None, hide_quantity=False, exclude_assets=None):
        super().__init__(parent)
        self.setWindowTitle(t('inventory.select_item', default='Select Item'))
        self.setMinimumSize(840, 600)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.selected_item = None
        self._filter_type_a = filter_type_a
        self._filter_type_b = filter_type_b
        self._filter_exclude_type_a = filter_exclude_type_a
        self._hide_quantity = hide_quantity
        self._exclude_assets = exclude_assets or set()
        self.setStyleSheet(DARK_THEME_STYLE)
        self._setup_ui()
        self._adjust_width()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        search_layout = QHBoxLayout()
        search_label = QLabel(t('common.search', default='Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('inventory.search_placeholder', default='Type to search items...'))
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(48, 48))
        self.results_list.setSpacing(0)
        self.results_list.setUniformItemSizes(True)
        self.results_list.setGridSize(QSize(80, 80))
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setDragEnabled(False)
        self.results_list.setAcceptDrops(False)
        self.results_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.results_list.setMinimumHeight(350)
        self.results_list.setItemDelegate(RarityBorderDelegate(self.results_list))
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.results_list)
        self.desc_label = QLabel('')
        self.desc_label.setStyleSheet('color: #94a3b8; font-size: 11px; padding: 2px 4px;')
        self.desc_label.setWordWrap(True)
        self.desc_label.setVisible(False)
        self.desc_label.setMaximumHeight(50)
        layout.addWidget(self.desc_label)
        qty_layout = QHBoxLayout()
        self.qty_label = QLabel(t('inventory.quantity', default='Quantity:'))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(1)
        qty_layout.addWidget(self.qty_label)
        qty_layout.addWidget(self.qty_spin)
        if self._hide_quantity:
            self.qty_label.setVisible(False)
            self.qty_spin.setVisible(False)
        qty_layout.addStretch()
        add_btn = QPushButton(t('button.add', default='Add'))
        add_btn.clicked.connect(self._add_item)
        qty_layout.addWidget(add_btn)
        cancel_btn = QPushButton(t('button.cancel', default='Cancel'))
        cancel_btn.clicked.connect(self.reject)
        qty_layout.addWidget(cancel_btn)
        layout.addLayout(qty_layout)
        items = ItemData.get_all_items()
        for item in items:
            type_a = item.get('type_a', '')
            type_b = item.get('type_b', '')
            if self._filter_type_a is not None:
                if isinstance(self._filter_type_a, list):
                    if type_a not in self._filter_type_a:
                        continue
                elif type_a != self._filter_type_a:
                    continue
            if self._filter_type_b is not None:
                if isinstance(self._filter_type_b, list):
                    if type_b not in self._filter_type_b:
                        continue
                elif type_b != self._filter_type_b:
                    continue
            if self._filter_exclude_type_a is not None:
                if isinstance(self._filter_exclude_type_a, list):
                    if type_a in self._filter_exclude_type_a:
                        continue
                elif type_a == self._filter_exclude_type_a:
                    continue
            if item.get('sort_id', 0) == 9999:
                continue
            if item.get('asset', '') in self._exclude_assets:
                continue
            if type_a != 'EPalItemTypeA::Essential':
                if item['asset'].startswith('PalEgg_'):
                    continue
            desc = item.get('description', '').strip()
            if not desc or desc.lower() in ('', 'en text', 'en_text', 'none', '-', '---'):
                continue
            if item.get('name', '') == item.get('asset', ''):
                continue
            if 'en_text' in item.get('name', '').lower():
                continue
            list_item = QListWidgetItem(item.get('name', 'Unknown'))
            list_item.setData(Qt.UserRole, item.get('asset', ''))
            list_item.setData(Qt.UserRole + 2, item.get('rarity', 0))
            list_item.setData(Qt.UserRole + 3, type_a)
            list_item.setData(Qt.UserRole + 4, item.get('description', ''))
            list_item.setData(Qt.UserRole + 5, item.get('type_b', ''))
            icon_path = item.get('icon', '')
            if icon_path:
                pixmap = ItemData.get_item_icon(icon_path, QSize(48, 48))
                list_item.setIcon(QIcon(pixmap))
            item_name = item.get('name', 'Unknown')
            item_id = item.get('asset', '')
            item_desc = item.get('description', '')
            category = item.get('category', 'misc')
            tooltip = f'<b>{item_name}</b><br>ID: {item_id}<br>Category: {category}'
            if item_desc:
                cleaned = _clean_desc_for_tooltip(item_desc)
                tooltip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(cleaned)}</span>'
            list_item.setToolTip(tooltip)
            list_item.setSizeHint(QSize(80, 80))
            self.results_list.addItem(list_item)
    def _filter_items(self, query: str):
        q = query.lower()
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            name = item.text()
            asset = item.data(Qt.UserRole) or ''
            item.setHidden(bool(q and q not in name.lower() and (q not in asset.lower())))
    def _adjust_width(self):
        m = self.layout().contentsMargins()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        scrollbar = 16
        padding = 24
        target_w = m.left() + m.right() + frame_w + scrollbar + padding + 10 * 80
        self.setFixedWidth(target_w)
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item = item.data(Qt.UserRole)
        type_a = item.data(Qt.UserRole + 3) or ''
        type_b = item.data(Qt.UserRole + 5) or ''
        item_desc = item.data(Qt.UserRole + 4) or ''
        is_singleton = type_a in SINGLETON_TYPE_A and type_b != 'EPalItemTypeB::WeaponThrowObject'
        if not self._hide_quantity:
            self.qty_label.setVisible(not is_singleton)
            self.qty_spin.setVisible(not is_singleton)
            if is_singleton:
                self.qty_spin.setValue(1)
        if item_desc:
            self.desc_label.setText(_clean_desc_for_tooltip(item_desc))
            self.desc_label.setVisible(True)
        else:
            self.desc_label.setVisible(False)
    def _on_item_double_clicked(self, item: QListWidgetItem):
        self.selected_item = item.data(Qt.UserRole)
        self._add_item()
    def _add_item(self):
        if self.selected_item:
            self.item_selected.emit(self.selected_item, self.qty_spin.value())
            self.accept()
class PlayerInventoryTab(QWidget):
    unlock_all_map_requested = Signal(list)
    saved = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.inventory = None
        self.modified = False
        self.selected_item = None
        self.current_player_uid = None
        self.current_player_name = None
        self._player_list = []
        self.equip_headers = {}
        self._context_container_type = 'main'
        self._context_slot_index = 0
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(t('inventory.title', default='Player Inventory'))
        self.title_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.title_label.setObjectName('sectionHeader')
        self.title_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.title_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.title_label)
        header.addStretch()
        self.player_select_btn = QPushButton(t('inventory.select_player', default='Select Player...'))
        self.player_select_btn.setMinimumWidth(220)
        self.player_select_btn.setMaximumHeight(28)
        self.player_select_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.player_select_btn.setCursor(Qt.PointingHandCursor)
        self.player_select_btn.clicked.connect(self._open_player_popup)
        header.addWidget(self.player_select_btn)
        main_layout.addLayout(header)
        self.content_area = QFrame()
        self.content_area.setObjectName('inventoryContent')
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setStyleSheet(f'QFrame#inventoryContent {{ {CONTENT_PANEL_STYLE} }}')
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.placeholder_label = QLabel(t('inventory.select_player_hint', default='Select a player to edit their inventory'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setMinimumHeight(400)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setStyleSheet('QLabel { color: #888; font-size: 14px; background: transparent; }')
        content_layout.addWidget(self.placeholder_label, 1)
        inner_content = QHBoxLayout()
        inner_content.setContentsMargins(10, 10, 10, 10)
        inner_content.setSpacing(10)
        self.inv_tabs = QTabWidget()
        self.inv_tabs.setObjectName('inventoryTabs')
        self.main_grid = InventoryGridWidget('main')
        self.main_grid.item_selected.connect(self._on_item_selected)
        self.main_grid.item_context_menu.connect(self._show_item_context_menu)
        self.main_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.main_grid.item_double_clicked.connect(self._delete_item_direct)
        self.main_grid.empty_slot_double_clicked.connect(self._on_empty_slot_double_clicked)
        self.unlock_all_map_btn = QPushButton(t('inventory.unlock_all_map', default='Unlock All Map + Fast Travel'))
        self.unlock_all_map_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(74,222,128,0.25); border-color: rgba(74,222,128,0.5); color: #FFFFFF; }')
        self.unlock_all_map_btn.setCursor(Qt.PointingHandCursor)
        self.unlock_all_map_btn.setFixedHeight(24)
        self.unlock_all_map_btn.clicked.connect(self._on_unlock_all_map_clicked)
        sort_idx = self.main_grid.header_layout.indexOf(self.main_grid.sort_btn)
        self.main_grid.header_layout.insertWidget(sort_idx, self.unlock_all_map_btn)
        self.main_grid.sort_requested.connect(self._on_sort_requested)
        self.inv_loadout_btn = QPushButton(t('inventory.loadouts_btn', default='Loadouts'))
        self.inv_loadout_btn.setFixedHeight(24)
        self.inv_loadout_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.inv_loadout_btn.setCursor(Qt.PointingHandCursor)
        self.inv_loadout_btn.clicked.connect(self._on_inventory_loadout)
        self.main_grid.header_layout.insertWidget(sort_idx, self.inv_loadout_btn)
        self.inv_clear_btn = QPushButton(t('inventory.clear_btn', default='Clear'))
        self.inv_clear_btn.setFixedHeight(24)
        self.inv_clear_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.inv_clear_btn.setCursor(Qt.PointingHandCursor)
        self.inv_clear_btn.clicked.connect(self._clear_all_inventory)
        self.main_grid.header_layout.insertWidget(sort_idx + 2, self.inv_clear_btn)
        self.inv_tabs.addTab(self.main_grid, t('inventory.main', default='Inventory'))
        self.key_grid = InventoryGridWidget('key_items')
        self.key_grid.item_selected.connect(self._on_item_selected)
        self.key_grid.item_context_menu.connect(self._show_item_context_menu)
        self.key_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.key_grid.item_double_clicked.connect(self._delete_item_direct)
        self.key_grid.empty_slot_double_clicked.connect(self._on_empty_slot_double_clicked)
        self.key_grid.add_all_effigies_requested.connect(self._on_add_all_effigies)
        self.key_grid.add_all_key_items_requested.connect(self._on_add_all_key_items)
        self.key_grid.clear_key_items_requested.connect(self._clear_all_key_items)
        self.key_grid.sort_requested.connect(self._on_sort_requested)
        self.inv_tabs.addTab(self.key_grid, t('inventory.key_items', default='Key Items'))
        self.stats_tab = QWidget()
        stats_tab_layout = QVBoxLayout(self.stats_tab)
        stats_tab_layout.setContentsMargins(0, 0, 0, 0)
        stats_tab_layout.addStretch()
        self.stats_panel = StatsPanelWidget()
        self.stats_panel.stats_changed.connect(self._on_stats_changed)
        stats_tab_layout.addWidget(self.stats_panel, alignment=Qt.AlignCenter)
        stats_tab_layout.addStretch()
        self.inv_tabs.addTab(self.stats_tab, t('inventory.stats', default='Stats'))
        inner_content.addWidget(self.inv_tabs, 2)
        equip_wrapper = QWidget()
        self.equip_wrapper = equip_wrapper
        equip_wrapper.setMinimumWidth(400)
        equip_wrapper_layout = QVBoxLayout(equip_wrapper)
        equip_wrapper_layout.setContentsMargins(4, 0, 4, 0)
        equip_wrapper_layout.setSpacing(4)
        equip_header_row = QHBoxLayout()
        equip_header_row.setContentsMargins(0, 0, 0, 0)
        self.equip_title = QLabel(t('inventory.equipment', default='Equipment'))
        self.equip_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #E6EEF6;')
        self.equip_title.setAlignment(Qt.AlignCenter)
        equip_header_row.addWidget(self.equip_title)
        equip_header_row.addStretch()
        self.equip_loadout_btn = QPushButton(t('inventory.equip_loadouts_btn', default='Loadouts'))
        self.equip_loadout_btn.setFixedHeight(22)
        self.equip_loadout_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.equip_loadout_btn.setCursor(Qt.PointingHandCursor)
        self.equip_loadout_btn.clicked.connect(self._on_equipment_loadout)
        equip_header_row.addWidget(self.equip_loadout_btn)
        self.equip_clear_btn = QPushButton(t('inventory.equip_clear_btn', default='Clear'))
        self.equip_clear_btn.setFixedHeight(22)
        self.equip_clear_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.equip_clear_btn.setCursor(Qt.PointingHandCursor)
        self.equip_clear_btn.clicked.connect(self._clear_all_equipment)
        equip_header_row.addWidget(self.equip_clear_btn)
        equip_wrapper_layout.addLayout(equip_header_row)
        equip_scroll = QScrollArea()
        equip_scroll.setWidgetResizable(True)
        equip_scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        equip_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        equip_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        equip_content = QWidget()
        center_layout = QVBoxLayout(equip_content)
        center_layout.setContentsMargins(4, 4, 8, 4)
        center_layout.setSpacing(4)
        self.equip_slots = {}
        equip_main_layout = QHBoxLayout()
        equip_main_layout.setSpacing(8)
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        weapon_header = QLabel(t('inventory.weapon', default='Weapon'))
        weapon_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(weapon_header)
        self.equip_headers['weapon'] = weapon_header
        weapon_grid = QGridLayout()
        weapon_grid.setSpacing(2)
        weapon_grid.setContentsMargins(0, 0, 0, 0)
        for i, (row, col) in enumerate([(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1)]):
            slot = EquipmentSlotWidget(f'weapon{i + 1}', f'W{i + 1}')
            self.equip_slots[f'weapon{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            weapon_grid.addWidget(slot, row, col)
        weapon_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(weapon_grid)
        left_col.addSpacing(8)
        acc_header = QLabel(t('inventory.accessory', default='Accessory'))
        acc_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(acc_header)
        self.equip_headers['accessory'] = acc_header
        acc_grid = QGridLayout()
        acc_grid.setSpacing(2)
        acc_grid.setContentsMargins(0, 0, 0, 0)
        for i, (row, col) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
            slot = EquipmentSlotWidget(f'accessory{i + 1}', f'A{i + 1}')
            self.equip_slots[f'accessory{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            acc_grid.addWidget(slot, row, col)
        acc_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(acc_grid)
        left_col.addSpacing(8)
        food_header = QLabel(t('inventory.food', default='Food'))
        food_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(food_header)
        self.equip_headers['food'] = food_header
        food_grid = QGridLayout()
        food_grid.setSpacing(2)
        food_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(5):
            row, col = (0, i)
            slot = EquipmentSlotWidget(f'food{i + 1}', f'F{i + 1}')
            self.equip_slots[f'food{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            food_grid.addWidget(slot, row, col)
        food_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(food_grid)
        equip_main_layout.addLayout(left_col)
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        head_header = QLabel(t('inventory.head', default='Head'))
        head_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(head_header)
        self.equip_headers['head'] = head_header
        slot = EquipmentSlotWidget('head', 'H1')
        self.equip_slots['head'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        body_header = QLabel(t('inventory.body', default='Body'))
        body_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(body_header)
        self.equip_headers['body'] = body_header
        slot = EquipmentSlotWidget('body', 'B1')
        self.equip_slots['body'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        shield_header = QLabel(t('inventory.shield', default='Shield'))
        shield_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(shield_header)
        self.equip_headers['shield'] = shield_header
        slot = EquipmentSlotWidget('shield', 'S1')
        self.equip_slots['shield'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        glider_header = QLabel(t('inventory.glider', default='Glider'))
        glider_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(glider_header)
        self.equip_headers['glider'] = glider_header
        slot = EquipmentSlotWidget('glider', 'G1')
        self.equip_slots['glider'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        module_header = QLabel(t('inventory.module', default='Module'))
        module_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(module_header)
        self.equip_headers['module'] = module_header
        slot = EquipmentSlotWidget('sphere_mod', 'SM')
        self.equip_slots['sphere_mod'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        for equip_slot in self.equip_slots.values():
            equip_slot.double_clicked.connect(self._on_equip_double_clicked)
        equip_main_layout.addLayout(right_col)
        center_layout.addLayout(equip_main_layout)
        equip_scroll.setWidget(equip_content)
        equip_wrapper_layout.addWidget(equip_scroll)
        inner_content.addWidget(equip_wrapper, 1)
        content_layout.addLayout(inner_content)
        main_layout.addWidget(self.content_area)
        self.inv_tabs.hide()
        equip_wrapper.hide()
    def _on_stats_changed(self):
        if not self.current_player_uid:
            return
        self._save_stats_to_raw_data()
        self._update_player_dropdown_level()
    def refresh_players(self):
        self._player_list = []
        self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        if constants.loaded_level_json:
            from palworld_aio.managers.save_manager import save_manager
            players = save_manager.get_players()
            for uid, name, gid, lastseen, level, *_ in players:
                display_name = f'{name} (Lv.{level})'
                self._player_list.append({'uid': uid, 'name': name, 'level': level, 'display': display_name})
    def _open_player_popup(self):
        if not self._player_list:
            self.refresh_players()
        popup = QWidget()
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        popup.setStyleSheet(PICKER_BG_STYLE)
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        search = QLineEdit()
        search.setPlaceholderText(t('inventory.search_players', default='Search players...'))
        search.setStyleSheet(PICKER_SEARCH_STYLE)
        layout.addWidget(search)
        lst = QListWidget()
        lst.setStyleSheet(PICKER_LIST_STYLE)
        lst.setMaximumHeight(300)
        lst.setMinimumWidth(220)
        clear_item = QListWidgetItem(t('common.clear') if t else '-- clear --')
        lst.addItem(clear_item)
        for player in self._player_list:
            item = QListWidgetItem(player['display'])
            item.setData(Qt.UserRole, player)
            lst.addItem(item)
        search.textChanged.connect(lambda t, l=lst: [l.item(i).setHidden(t.lower() not in l.item(i).text().lower()) for i in range(l.count())])
        layout.addWidget(lst)
        popup.setFixedWidth(self.player_select_btn.width())
        popup.move(self.player_select_btn.mapToGlobal(QPoint(0, self.player_select_btn.height())))
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            popup.adjustSize()
            ph = popup.sizeHint().height()
            if popup.y() + ph > screen_geo.bottom() and popup.y() - ph > screen_geo.top():
                popup.move(popup.x(), popup.y() - ph - self.player_select_btn.height())
        popup.show()
        search.setFocus()
        chosen = None
        def on_select():
            nonlocal chosen
            sel = lst.currentItem()
            if sel:
                if sel.text().startswith('--'):
                    chosen = '__clear__'
                elif sel.data(Qt.UserRole):
                    chosen = sel.data(Qt.UserRole)
            popup.hide()
        lst.itemClicked.connect(on_select)
        search.returnPressed.connect(on_select)
        while popup.isVisible():
            QApplication.processEvents()
            QThread.msleep(5)
        if chosen == '__clear__':
            self._clear_display()
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
            self.current_player_uid = None
            self.current_player_name = None
        elif chosen:
            self.current_player_uid = chosen['uid']
            self.current_player_name = chosen['name']
            self.player_select_btn.setText(chosen['display'])
            self.modified = False
            self._show_inventory()
            self.inventory = get_player_inventory(self.current_player_uid)
            self._refresh_display()
    def _show_inventory(self):
        self.placeholder_label.hide()
        self.inv_tabs.show()
        if hasattr(self, 'equip_wrapper'):
            self.equip_wrapper.show()
    def _clear_display(self):
        self.placeholder_label.show()
        self.inv_tabs.hide()
        if hasattr(self, 'equip_wrapper'):
            self.equip_wrapper.hide()
        self.main_grid.load_items([])
        self.key_grid.load_items([])
        self.stats_panel.clear()
        for slot_widget in self.equip_slots.values():
            slot_widget.clear_item()
    def _on_add_all_effigies(self):
        if not self.current_player_uid:
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.max_all_abilities_confirm.title', default='Max All Abilities'), t('inventory.max_all_abilities_confirm.msg', default='Max all relic abilities for this player?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        max_all_abilities([self.current_player_uid])
        constants.invalidate_container_lookup()
        from palworld_aio.inventory.inventory_manager import get_player_inventory
        self.inventory = get_player_inventory(self.current_player_uid)
        self._refresh_display()
        self._themed_message_box(QMessageBox.Information, t('Done') if t else 'Done', t('inventory.max_all_abilities_done', default='Abilities maxed to maximum rank.'))
    def _on_add_all_key_items(self):
        if not self.inventory:
            return
        all_items = ItemData.get_all_items()
        unlock_assets = set(FOOD_POUCH_ITEMS + ACCESSORY_UNLOCK_ITEMS + WEAPON_UNLOCK_ITEMS)
        key_candidates = [i for i in all_items if i.get('type_a') == 'EPalItemTypeA::Essential' and 'Effigy' not in i.get('name', '') and (i['asset'] not in unlock_assets) and (i.get('sort_id', 0) != 9999) and (i.get('description', '').strip() not in ('', '-')) and (i.get('name', '') != i.get('asset', '')) and ('en_text' not in i.get('name', '').lower())]
        existing_ids = {s.get('item_id') for s in self.inventory.get_container('key').slots}
        to_add = [i for i in key_candidates if i['asset'] not in existing_ids]
        missing_unlocks = []
        for item_id in FOOD_POUCH_ITEMS:
            if item_id not in existing_ids:
                missing_unlocks.append(item_id)
        for item_id in ACCESSORY_UNLOCK_ITEMS:
            if item_id not in existing_ids:
                missing_unlocks.append(item_id)
        for item_id in WEAPON_UNLOCK_ITEMS:
            if item_id not in existing_ids:
                missing_unlocks.append(item_id)
        total = len(to_add) + len(missing_unlocks)
        if not total:
            self._themed_message_box(QMessageBox.Information, t('inventory.add_all_key_items', default='Add All Key Items'), t('inventory.no_new_items', default='All key items already present.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.add_all_key_items_confirm.title', default='Add All Key Items'), t('inventory.add_all_key_items_confirm.msg', count=total, default=f'Add all missing key items? ({total} items)'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        key_container = self.inventory.get_container('key')
        if key_container:
            std_container = key_container._standardized_container
            slots_needed = len(key_container.slots) + total
            if slots_needed > std_container.max_slots:
                new_max = slots_needed + 50
                std_container.expand_capacity(new_max)
                std_container.container_data['value']['SlotNum']['value'] = new_max
        for item_id in missing_unlocks:
            self.inventory.add_item('key', item_id, 1)
        for item in to_add:
            self.inventory.add_item('key', item['asset'], 1)
        key_container = self.inventory.get_container('key')
        if key_container:
            self._update_raw_save_data('key', key_container)
        self._refresh_display()
    def _refresh_display(self):
        if not self.inventory:
            return
        self.inventory._calculate_max_slots()
        max_slots = self.inventory.max_slots
        main_container = self.inventory.get_container('main')
        if main_container:
            self.main_grid.load_items(main_container.slots, max_slots=max_slots)
        key_container = self.inventory.get_container('key')
        if key_container:
            key_slot_count = max(50, len(key_container.slots) + 10)
            self.key_grid.load_items(key_container.slots, max_slots=key_slot_count)
        unlocked_food_slots = self.inventory.get_unlocked_food_slots() if self.inventory else 0
        unlocked_accessory_slots = self.inventory.get_unlocked_accessory_slots() if self.inventory else 2
        unlocked_weapon_slots = self.inventory.get_unlocked_weapon_slots() if self.inventory else 4
        for i in range(1, 6):
            slot_name = f'food{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_food_slots
                slot_widget.set_locked(is_locked, lock_type='food' if is_locked else None)
        for i in range(1, 5):
            slot_name = f'accessory{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_accessory_slots
                slot_widget.set_locked(is_locked, lock_type='accessory' if is_locked else None)
        for i in range(5, 7):
            slot_name = f'weapon{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_weapon_slots
                slot_widget.set_locked(is_locked, lock_type='weapon' if is_locked else None)
        equipment = self.inventory.get_equipment()
        for slot_name, item in equipment.items():
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                if not slot_widget.is_locked():
                    slot_widget.set_item(item)
        self._update_stats()
    def _on_slot_unlock_request(self, slot_name: str):
        if not self.inventory:
            return
        if slot_name.startswith('food'):
            unlocked_food = self.inventory.get_unlocked_food_slots()
            next_pouch_index = unlocked_food
            if next_pouch_index < len(FOOD_POUCH_ITEMS):
                unlock_item_id = FOOD_POUCH_ITEMS[next_pouch_index]
                unlock_item_name = f'AutoMealPouch Tier {next_pouch_index + 1}'
            else:
                self._themed_message_box(QMessageBox.Information, t('inventory.unlock_failed', default='Unlock Failed'), t('inventory.max_food_slots', default='All food slots are already unlocked!'), QMessageBox.Ok)
                return
            slot_type = 'food'
        elif slot_name.startswith('accessory'):
            unlocked_acc = self.inventory.get_unlocked_accessory_slots()
            unlock_index = unlocked_acc - 2
            if unlock_index < len(ACCESSORY_UNLOCK_ITEMS):
                unlock_item_id = ACCESSORY_UNLOCK_ITEMS[unlock_index]
                unlock_item_name = f'Accessory Slot Unlock {unlock_index + 1}'
            else:
                self._themed_message_box(QMessageBox.Information, t('inventory.unlock_failed', default='Unlock Failed'), t('inventory.max_accessory_slots', default='All accessory slots are already unlocked!'), QMessageBox.Ok)
                return
            slot_type = 'accessory'
        elif slot_name.startswith('weapon'):
            unlocked_weapon = self.inventory.get_unlocked_weapon_slots()
            unlock_index = unlocked_weapon - 4
            if unlock_index < len(WEAPON_UNLOCK_ITEMS):
                unlock_item_id = WEAPON_UNLOCK_ITEMS[unlock_index]
                unlock_item_name = f'Weapon Slot Unlock {unlock_index + 1}'
            else:
                self._themed_message_box(QMessageBox.Information, t('inventory.unlock_failed', default='Unlock Failed'), t('inventory.max_weapon_slots', default='All weapon slots are already unlocked!'), QMessageBox.Ok)
                return
            slot_type = 'weapon'
        else:
            return
        slot_display = slot_name.replace('_', ' ').title()
        message = t('inventory.unlock_confirm', slot=slot_display, item=unlock_item_name, default=f'Unlock {slot_display}?\n\nThis will add "{unlock_item_name}" to your key items.')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.unlock_slot', default='Unlock Slot'), message, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.inventory.add_key_item(unlock_item_id):
                key_container = self.inventory.get_container('key')
                if key_container:
                    self._update_raw_save_data('key', key_container)
                self._refresh_display()
    def _on_inventory_loadout(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        def _get_items():
            if not self.inventory:
                return []
            all_items = []
            main_c = self.inventory.get_container('main')
            if main_c:
                all_items.extend(_group_inventory_items(main_c.slots))
            key_c = self.inventory.get_container('key')
            if key_c:
                all_items.extend(_group_inventory_items(key_c.slots))
            return all_items
        def _apply_items(regular, key_items, equipment=None):
            if not self.inventory:
                return
            existing_key_ids = {s['item_id'] for s in (self.inventory.get_container('key').slots if self.inventory.get_container('key') else [])}
            missing_expansion = [e for e in INVENTORY_EXPANSION_ITEMS if e not in existing_key_ids]
            for item in key_items:
                if item['id'] in existing_key_ids:
                    continue
                _merge_or_add_items(self.inventory, 'key', item['id'], item['qty'])
            for item in regular:
                added = _merge_or_add_items(self.inventory, 'main', item['id'], item['qty'])
                if not added and missing_expansion:
                    next_exp = missing_expansion.pop(0)
                    _merge_or_add_items(self.inventory, 'key', next_exp, 1)
                    self.inventory._calculate_max_slots()
                    added = _merge_or_add_items(self.inventory, 'main', item['id'], item['qty'])
            main_c = self.inventory.get_container('main')
            if main_c:
                _consolidate_container_slots(main_c, 'main', SINGLETON_TYPE_A)
                self._update_raw_save_data('main', main_c)
            key_c = self.inventory.get_container('key')
            if key_c:
                _consolidate_container_slots(key_c, 'key', SINGLETON_TYPE_A)
                self._update_raw_save_data('key', key_c)
            self.inventory.save()
            self._refresh_display()
        dlg = InventoryLoadoutDialog(self, _get_items, _apply_items, loadouts_path=_INV_LOADOUTS_PATH)
        dlg.exec()
    def _on_sort_requested(self):
        if not self.inventory:
            return
        sender = self.sender()
        if sender == self.main_grid:
            container = self.inventory.get_container('main')
            ct = 'main'
        elif sender == self.key_grid:
            container = self.inventory.get_container('key')
            ct = 'key'
        else:
            return
        if not container:
            return
        _consolidate_container_slots(container, ct, SINGLETON_TYPE_A)
        self._update_raw_save_data(ct, container)
        self._refresh_display()
    def _on_equipment_loadout(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        def _get_equipment():
            if not self.inventory:
                return {}
            equip = self.inventory.get_equipment()
            result = {}
            for slot_name, slot_data in equip.items():
                if slot_data and slot_data.get('item_id'):
                    result[slot_name] = {'id': slot_data['item_id'], 'qty': slot_data.get('stack_count', 1), 'name': slot_data.get('item_name', slot_data['item_id'])}
            return result
        def _apply_equipment(regular, key_items, equipment=None):
            if not self.inventory:
                return
            if not equipment:
                return
            from palworld_aio.inventory.inventory_manager import UI_SLOT_BINDINGS, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS, WEAPON_UNLOCK_ITEMS
            binding_map = {b['slot_name']: b for b in UI_SLOT_BINDINGS}
            def _ensure_slot_unlocked(slot_name):
                import re
                m = re.match(r'(food|accessory|weapon)(\d+)', slot_name)
                if not m:
                    return
                kind, num_str = m.group(1), int(m.group(2))
                if kind == 'food':
                    unlocked = self.inventory.get_unlocked_food_slots()
                    while num_str > unlocked and unlocked < len(FOOD_POUCH_ITEMS):
                        self.inventory.add_key_item(FOOD_POUCH_ITEMS[unlocked])
                        unlocked += 1
                elif kind == 'accessory':
                    base = 2
                    unlocked = self.inventory.get_unlocked_accessory_slots()
                    while num_str > unlocked and unlocked - base < len(ACCESSORY_UNLOCK_ITEMS):
                        self.inventory.add_key_item(ACCESSORY_UNLOCK_ITEMS[unlocked - base])
                        unlocked += 1
                elif kind == 'weapon':
                    base = 4
                    unlocked = self.inventory.get_unlocked_weapon_slots()
                    while num_str > unlocked and unlocked - base < len(WEAPON_UNLOCK_ITEMS):
                        self.inventory.add_key_item(WEAPON_UNLOCK_ITEMS[unlocked - base])
                        unlocked += 1
            for slot_name, equip_item in equipment.items():
                if slot_name not in binding_map:
                    continue
                _ensure_slot_unlocked(slot_name)
                binding = binding_map[slot_name]
                slot_idx = binding['index']
                container = self.inventory.get_container(binding['container'])
                if not container:
                    continue
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_idx])
                self.inventory.add_item(binding['container'], equip_item['id'], equip_item.get('qty', 1), slot_index=slot_idx)
                self._update_raw_save_data(binding['container'], container)
            self._refresh_display()
        dlg = InventoryLoadoutDialog(self, _get_equipment, _apply_equipment, title=t('inventory.equip_loadouts_title', default='Equipment Loadouts'), loadouts_path=_EQ_LOADOUTS_PATH, key_prefix='inventory.equip')
        dlg.exec()
    def _clear_all_inventory(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_confirm_title', default='Clear Inventory'), t('inventory.clear_confirm_msg', default='Remove all items from inventory? (Key items, equipment, and unlocks will be preserved)'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        for ct in ('main',):
            container = self.inventory.get_container(ct) if self.inventory else None
            if container:
                container.update_slots([])
                self._update_raw_save_data(ct, container)
        if self.inventory:
            self.inventory.save()
        self._refresh_display()
    def _clear_all_key_items(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_key_confirm_title', default='Clear'), t('inventory.clear_key_confirm_msg', default='Remove all key items?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        if not self.inventory:
            return
        key_container = self.inventory.get_container('key')
        if key_container:
            key_container.update_slots([])
            self._update_raw_save_data('key', key_container)
        foodbag = self.inventory.get_container('foodbag')
        if foodbag:
            foodbag.update_slots([])
            self._update_raw_save_data('foodbag', foodbag)
        armor = self.inventory.get_container('armor')
        if armor:
            armor.update_slots([s for s in armor.slots if s.get('slot_index', 0) not in (6, 7)])
            self._update_raw_save_data('armor', armor)
        weapons = self.inventory.get_container('weapons')
        if weapons:
            weapons.update_slots([s for s in weapons.slots if s.get('slot_index', 0) < 4])
            self._update_raw_save_data('weapons', weapons)
        self.inventory._calculate_max_slots()
        main_container = self.inventory.get_container('main')
        if main_container:
            max_slots = self.inventory.max_slots
            main_container.update_slots([s for s in main_container.slots if s.get('slot_index', 0) < max_slots])
            self._update_raw_save_data('main', main_container)
        self.inventory.save()
        self._refresh_display()
    def _clear_all_equipment(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.equip_clear_title', default='Clear Equipment'), t('inventory.equip_clear_msg', default='Remove all equipment from weapon, armor, and food slots?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        for ct in ('weapons', 'armor', 'foodbag'):
            container = self.inventory.get_container(ct) if self.inventory else None
            if container:
                container.update_slots([])
                self._update_raw_save_data(ct, container)
        if self.inventory:
            self.inventory.save()
        self._refresh_display()
    def _on_unlock_all_map_clicked(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.unlock_all_map_confirm.title', default='Unlock All Map + Fast Travel'), t('inventory.unlock_all_map_confirm.msg', count=1, default='Unlock all fast travel points, reveal all map areas, and unlock world map for 1 player?'), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.unlock_all_map_requested.emit([self.current_player_uid])
    def _update_stats(self):
        if not self.current_player_uid or not constants.loaded_level_json:
            return
        uid_clean = str(self.current_player_uid).replace('-', '')
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        stats = {'hp': 100, 'stamina': 100, 'attack': 10, 'defense': 10, 'work_speed': 70, 'weight': '0/500'}
        level = 1
        unused_points = 0
        for entry in char_map:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value'):
                continue
            uid_obj = entry.get('key', {}).get('PlayerUId', {})
            player_uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
            if player_uid == uid_clean:
                level_data = sp_val.get('Level', {})
                if isinstance(level_data, dict):
                    level = level_data.get('value', {}).get('value', 1)
                else:
                    level = 1
                if 'GotStatusPointList' in sp_val:
                    got_status_list = sp_val['GotStatusPointList']['value']['values']
                    stat_map = {'最大HP': 'hp', '最大SP': 'stamina', '攻撃力': 'attack', '防御力': 'defense', '作業速度': 'work_speed', '所持重量': 'weight'}
                    for status_item in got_status_list:
                        stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                        stat_point = status_item['StatusPoint'].get('value', 0) if isinstance(status_item.get('StatusPoint'), dict) else 0
                        if stat_name_jp in stat_map:
                            stat_key = stat_map[stat_name_jp]
                            if stat_key == 'weight':
                                base_weight = 50
                                weight_per_point = 50
                                stats[stat_key] = f'{base_weight + stat_point * weight_per_point}'
                            else:
                                stats[stat_key] = stat_point
                if 'UnusedStatusPoint' in sp_val:
                    unused_points = sp_val['UnusedStatusPoint'].get('value', 0) if isinstance(sp_val.get('UnusedStatusPoint'), dict) else 0
                break
        self.stats_panel.update_stats(stats)
        self.stats_panel.set_level(level, 0)
    def _on_item_selected(self, slot_data):
        self.selected_item = slot_data
    def _show_item_context_menu(self, slot_data, pos):
        if not slot_data:
            return
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction(t('inventory.edit_qty', default='Edit Quantity')).triggered.connect(lambda: self._edit_quantity_for(slot_data))
        menu.addAction(t('inventory.delete_item', default='Delete')).triggered.connect(lambda: self._delete_item(slot_data))
        menu.addSeparator()
        menu.addAction(t('inventory.add_item', default='Add Item')).triggered.connect(self._show_add_item_dialog)
        menu.exec(pos)
    def _show_empty_slot_context_menu(self, container_type: str, slot_index: int, pos):
        self._context_container_type = container_type
        self._context_slot_index = slot_index
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction(t('inventory.add_item', default='Add Item')).triggered.connect(self._show_add_item_dialog)
        menu.addSeparator()
        menu.addAction(t('inventory.clear_slot', default='Clear Slot')).triggered.connect(lambda: self._clear_corrupted_slot(container_type, slot_index))
        menu.exec(pos)
    def _on_empty_slot_double_clicked(self, container_type: str, slot_index: int):
        self._context_container_type = container_type
        self._context_slot_index = slot_index
        self._show_add_item_dialog()
    def _delete_item_direct(self, slot_data: dict):
        if not self.inventory or not slot_data:
            return
        container_type = slot_data.get('container_type', 'main')
        slot_index = slot_data.get('slot_index', 0)
        container = self.inventory.get_container(container_type)
        if container:
            container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
            self._update_raw_save_data(container_type, container)
            self.inventory.save()
            self.selected_item = None
            self._refresh_display()
    def _clear_corrupted_slot(self, container_type: str, slot_index: int):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type_map = {'main': 'main', 'key_items': 'key'}
        actual_container_type = container_type_map.get(container_type, container_type)
        container = self.inventory.get_container(actual_container_type)
        if not container:
            return
        slot_to_remove = None
        for slot in container.slots:
            if slot.get('slot_index') == slot_index:
                slot_to_remove = slot
                break
        if not slot_to_remove:
            return
        item_name = slot_to_remove.get('item_name', 'Unknown')
        msg = t('inventory.clear_corrupted_confirm.msg', item=item_name, default=f'Clear corrupted slot for "{item_name}"?')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_corrupted_confirm.title', default='Clear Corrupted Slot'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
            self._update_raw_save_data_with_recursive_clean(container_type, container, slot_index)
            self.inventory.save()
            self._refresh_display()
    def _themed_message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(buttons)
        msg_box.setStyleSheet(DARK_THEME_STYLE)
        return msg_box.exec()
    def _show_equip_context_menu(self, slot_widget, pos):
        slot_name = slot_widget.slot_name
        current_item = slot_widget.current_item
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        if current_item:
            slot_type = self._get_equip_slot_type(slot_name)
            if slot_type in ('food', 'weapon'):
                menu.addAction(t('inventory.edit_qty', default='Edit Quantity')).triggered.connect(lambda: self._edit_equip_item(slot_name, current_item))
            menu.addAction(t('inventory.clear_slot', default='Clear Slot')).triggered.connect(lambda: self._clear_equip_slot(slot_name, slot_widget))
        else:
            menu.addAction(t('inventory.add_item', default='Add Item')).triggered.connect(lambda: self._add_to_equip_slot(slot_name))
        menu.exec(pos)
    def _on_equip_double_clicked(self, slot_widget):
        slot_name = slot_widget.slot_name
        if slot_widget.current_item:
            container_type = self._get_equip_container_type(slot_name)
            slot_index = self._get_equip_slot_index(slot_name)
            container = self.inventory.get_container(container_type)
            if container:
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
                self._update_raw_save_data_with_recursive_clean(container_type, container, slot_index)
                self.inventory.save()
                self._refresh_display()
        else:
            self._add_to_equip_slot(slot_name)
    def _add_to_equip_slot(self, slot_name: str):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type = self._get_equip_container_type(slot_name)
        if not container_type:
            return
        slot_type = self._get_equip_slot_type(slot_name)
        slot_filter = EQUIP_SLOT_FILTERS.get(slot_type, {})
        exclude_assets = set()
        if slot_type == 'accessory' and self.inventory:
            armor = self.inventory.get_container('armor')
            if armor:
                accessory_indices = {b['index'] for b in UI_SLOT_BINDINGS if b['slot_name'].startswith('accessory')}
                for s in armor.slots:
                    if s.get('slot_index') in accessory_indices:
                        exclude_assets.add(s.get('item_id', ''))
        dialog = ItemPickerDialog(self, filter_type_a=slot_filter.get('type_a'), filter_type_b=slot_filter.get('type_b'), hide_quantity=slot_type not in ('food', 'weapon'), exclude_assets=exclude_assets)
        dialog.item_selected.connect(lambda item_id, qty: self._do_add_to_equip_slot(slot_name, container_type, item_id, qty))
        dialog.exec()
    def _do_add_to_equip_slot(self, slot_name: str, container_type: str, item_id: str, quantity: int):
        if not self.inventory:
            return
        container = self.inventory.get_container(container_type)
        if not container:
            return
        slot_index = self._get_equip_slot_index(slot_name)
        item_info = ItemData.get_item_by_asset(item_id)
        new_slot = {'slot_index': slot_index, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': quantity, 'category': ItemData.get_item_category(item_id), 'container_type': container_type, 'raw_data': None}
        container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index] + [new_slot])
        self._update_raw_save_data(container_type, container)
        self.inventory.save()
        self._refresh_display()
    def _edit_equip_item(self, slot_name: str, current_item: dict):
        current_qty = current_item.get('stack_count', 1)
        dialog = QuantityDialog(current_qty, self)
        if dialog.exec() == QDialog.Accepted:
            new_qty = dialog.get_quantity()
            container_type = self._get_equip_container_type(slot_name)
            slot_index = self._get_equip_slot_index(slot_name)
            if not container_type:
                return
            container = self.inventory.get_container(container_type)
            if container:
                if container.set_item_count(slot_index, new_qty):
                    self._update_raw_save_data(container_type, container)
                    self.inventory.save()
                    self._refresh_display()
    def _clear_equip_slot(self, slot_name: str, slot_widget):
        current_item = slot_widget.current_item
        if not current_item:
            return
        item_name = current_item.get('item_name', 'Unknown')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_slot', default='Clear Slot'), t('inventory.clear_confirm', item=item_name, default=f'Remove "{item_name}" from equipment?'), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            container_type = self._get_equip_container_type(slot_name)
            slot_index = self._get_equip_slot_index(slot_name)
            container = self.inventory.get_container(container_type)
            if container:
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
                self._update_raw_save_data_with_recursive_clean(container_type, container, slot_index)
                self.inventory.save()
                self._refresh_display()
    def _get_equip_slot_type(self, slot_name: str) -> str:
        for prefix in ['weapon', 'accessory', 'food']:
            if slot_name.startswith(prefix):
                return prefix
        return slot_name
    def _get_equip_container_type(self, slot_name: str) -> str:
        for binding in UI_SLOT_BINDINGS:
            if binding.get('slot_name') == slot_name:
                return binding.get('container')
        return None
    def _get_equip_slot_index(self, slot_name: str) -> int:
        for binding in UI_SLOT_BINDINGS:
            if binding.get('slot_name') == slot_name:
                return binding.get('index', 0)
        return 0
    def _show_add_item_dialog(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type = getattr(self, '_context_container_type', 'main')
        if container_type == 'key_items':
            exclude = set(FOOD_POUCH_ITEMS + ACCESSORY_UNLOCK_ITEMS + WEAPON_UNLOCK_ITEMS)
            dialog = ItemPickerDialog(self, filter_type_a='EPalItemTypeA::Essential', exclude_assets=exclude)
        else:
            dialog = ItemPickerDialog(self, filter_exclude_type_a='EPalItemTypeA::Essential')
        dialog.item_selected.connect(self._add_item_to_inventory)
        dialog.exec()
    def _add_item_to_inventory(self, item_id: str, quantity: int):
        if not self.inventory:
            return
        actual_container_type = ItemData.get_target_container(item_id)
        container = self.inventory.get_container(actual_container_type)
        if not container:
            return
        if actual_container_type == 'main':
            max_slots = self.inventory.max_slots if self.inventory else 42
        else:
            max_slots = 100
        existing_indices = set((s.get('slot_index', 0) for s in container.slots))
        if self._context_slot_index not in existing_indices:
            new_slot_index = self._context_slot_index
        else:
            new_slot_index = None
            for i in range(max_slots):
                if i not in existing_indices:
                    new_slot_index = i
                    break
            if new_slot_index is None:
                max_index = max(existing_indices) if existing_indices else -1
                new_slot_index = max_index + 1
        item_info = ItemData.get_item_by_asset(item_id)
        new_slot = {'slot_index': new_slot_index, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': quantity, 'category': ItemData.get_item_category(item_id), 'description': item_info.get('description', ''), 'container_type': actual_container_type, 'raw_data': None}
        container.update_slots(container.slots + [new_slot])
        self._update_raw_save_data(actual_container_type, container)
        self.inventory.save()
        self._refresh_display()
    def _update_raw_save_data(self, container_type: str, container):
        if not self.inventory or not container:
            return
        container_id = self.inventory.containers.get(container_type)
        if not container_id:
            return
        container_id = container_id.container_id if hasattr(container_id, 'container_id') else container_id
        level_json = constants.loaded_level_json
        if not level_json:
            return
        wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        for container_data in item_containers:
            cid = container_data.get('key', {}).get('ID', {}).get('value', '')
            if cid == container_id:
                container_value = container_data.get('value', {})
                slots_data = container_value.get('Slots', {}).get('value', {}).get('values', [])
                modified_slots = {s.get('slot_index'): s for s in container.slots}
                slots_to_remove = []
                for i, raw_slot in enumerate(slots_data):
                    raw_data = raw_slot.get('RawData', {})
                    raw = raw_data.get('value', {})
                    slot_idx = raw.get('slot_index', -1)
                    if 'struct_id' not in raw_data:
                        raw_data['struct_id'] = '00000000000000000000000000000000'
                    if 'custom_type' not in raw_data:
                        raw_data['custom_type'] = '.worldSaveData.ItemContainerSaveData.Value.Slots.Slots.RawData'
                    if slot_idx in modified_slots:
                        mod_slot = modified_slots[slot_idx]
                        raw['count'] = mod_slot.get('stack_count', 1)
                        if 'item' in raw and isinstance(raw['item'], dict):
                            raw['item']['static_id'] = mod_slot.get('item_id', '')
                            mod_raw_data = mod_slot.get('raw_data')
                            if mod_raw_data:
                                mod_item = mod_raw_data.get('RawData', {}).get('value', {}).get('item', {})
                                mod_local = mod_item.get('dynamic_id', {}).get('local_id_in_created_world')
                                if mod_local and mod_local != '00000000-0000-0000-0000-000000000000':
                                    raw['item'].setdefault('dynamic_id', {})['local_id_in_created_world'] = mod_local
                                elif 'dynamic_id' in raw.get('item', {}):
                                    raw['item']['dynamic_id']['local_id_in_created_world'] = '00000000-0000-0000-0000-000000000000'
                        del modified_slots[slot_idx]
                    else:
                        slots_to_remove.append(i)
                for i in reversed(slots_to_remove):
                    slots_data.pop(i)
                for slot_idx, slot in modified_slots.items():
                    if slot.get('raw_data'):
                        new_slot = slot['raw_data']
                        raw = new_slot.get('RawData', {}).get('value', {})
                        raw['slot_index'] = slot_idx
                        raw['count'] = slot.get('stack_count', 1)
                        raw.setdefault('item', {})['static_id'] = slot.get('item_id', '')
                        slots_data.append(new_slot)
                    elif slots_data:
                        import copy
                        template = copy.deepcopy(slots_data[0])
                        raw = template.get('RawData', {}).get('value', {})
                        raw['slot_index'] = slot_idx
                        raw['count'] = slot.get('stack_count', 1)
                        raw.setdefault('item', {})['static_id'] = slot.get('item_id', '')
                        template['RawData'].setdefault('struct_id', '00000000000000000000000000000000')
                        slots_data.append(template)
                    else:
                        new_slot = {'RawData': {'type': 'StructProperty', 'struct_type': 'PalItemSlotSaveData', 'struct_id': '00000000000000000000000000000000', 'value': {'slot_index': slot_idx, 'count': slot.get('stack_count', 1), 'item': {'static_id': slot.get('item_id', ''), 'dynamic_id': {'created_world_id': {'struct_type': 'FGuid', 'value': '00000000000000000000000000000000'}, 'local_id_in_created_world': '00000000000000000000000000000000'}}}}}
                        slots_data.append(new_slot)
                return
    def _delete_selected_item(self):
        if self.selected_item:
            self._delete_item(self.selected_item)
        else:
            QMessageBox.information(self, t('info.title', default='Info'), t('inventory.no_item_selected', default='Please select an item first'))
    def _delete_item(self, slot_data: dict):
        if not self.inventory or not slot_data:
            return
        container_type = slot_data.get('container_type', 'main')
        slot_index = slot_data.get('slot_index', 0)
        item_name = slot_data.get('item_name', 'Unknown')
        msg = t('inventory.delete_confirm.msg', item=item_name, default=f'Delete "{item_name}"?')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.delete_confirm.title', default='Delete Item'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            container = self.inventory.get_container(container_type)
            if container:
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
                self._update_raw_save_data(container_type, container)
                self.inventory.save()
                self.selected_item = None
                self._refresh_display()
    def _edit_quantity(self):
        if self.selected_item:
            self._edit_quantity_for(self.selected_item)
        else:
            QMessageBox.information(self, t('info.title', default='Info'), t('inventory.no_item_selected', default='Please select an item first'))
    def _edit_quantity_for(self, slot_data: dict):
        if not self.inventory or not slot_data:
            return
        current_qty = slot_data.get('stack_count', 1)
        dialog = QuantityDialog(current_qty, self)
        if dialog.exec() == QDialog.Accepted:
            new_qty = dialog.get_quantity()
            container_type = slot_data.get('container_type', 'main')
            slot_index = slot_data.get('slot_index', 0)
            if self.inventory.update_quantity(container_type, slot_index, new_qty):
                self._refresh_display()
    def _update_player_dropdown_level(self):
        if not self.current_player_uid:
            return
        new_level = self.stats_panel.get_level()
        for player in self._player_list:
            if player['uid'] == self.current_player_uid:
                player['level'] = new_level
                player['display'] = f"{player['name']} (Lv.{new_level})"
                self.player_select_btn.setText(player['display'])
                break
    def _save_stats_to_raw_data(self):
        if not self.current_player_uid or not constants.loaded_level_json:
            return
        uid_clean = str(self.current_player_uid).replace('-', '')
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        modified_stats = self.stats_panel.get_stats()
        new_level = self.stats_panel.get_level()
        new_exp = self.stats_panel.get_exp()
        from palworld_aio.managers.player_manager import set_player_level
        set_player_level(self.current_player_uid, new_level)
        if hasattr(self.parent_window, '_refresh_players'):
            self.parent_window._refresh_players()
        if hasattr(self.parent_window, 'pal_editor_tab'):
            self.parent_window.pal_editor_tab.refresh()
        stat_map_reverse = {'hp': '最大HP', 'stamina': '最大SP', 'attack': '攻撃力', 'defense': '防御力', 'work_speed': '作業速度', 'weight': '所持重量'}
        for entry in char_map:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value'):
                continue
            uid_obj = entry.get('key', {}).get('PlayerUId', {})
            player_uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
            if player_uid == uid_clean:
                if 'Exp' in sp_val:
                    sp_val['Exp']['value'] = new_exp
                if 'GotStatusPointList' in sp_val:
                    got_status_list = sp_val['GotStatusPointList']['value']['values']
                    for status_item in got_status_list:
                        stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                        for key, jp_name in stat_map_reverse.items():
                            if jp_name == stat_name_jp and key in modified_stats:
                                if key == 'weight':
                                    weight_val = modified_stats[key]
                                    stat_point = (weight_val - 50) // 50
                                else:
                                    stat_point = modified_stats[key]
                                if 'StatusPoint' in status_item:
                                    status_item['StatusPoint']['value'] = stat_point
                                else:
                                    status_item['StatusPoint'] = {'value': stat_point}
                                break
                return
    def _update_raw_save_data_with_recursive_clean(self, container_type, container, slot_index):
        if not self.inventory or not container:
            return
        container_id = self.inventory.containers.get(container_type)
        if not container_id:
            return
        container_id = container_id.container_id if hasattr(container_id, 'container_id') else container_id
        level_json = constants.loaded_level_json
        if not level_json:
            return
        wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        for container_data in item_containers:
            cid = container_data.get('key', {}).get('ID', {}).get('value', '')
            if cid == container_id:
                container_value = container_data.get('value', {})
                slots_data = container_value.get('Slots', {}).get('value', {}).get('values', [])
                self._remove_slot_from_slots_recursive(slots_data, slot_index)
                return
    def _remove_slot_from_slots_recursive(self, slots_data, slot_index_to_remove):
        if isinstance(slots_data, list):
            i = len(slots_data) - 1
            while i >= 0:
                slot_obj = slots_data[i]
                if isinstance(slot_obj, dict) and 'RawData' in slot_obj:
                    raw_val = slot_obj['RawData'].get('value', {})
                    slot_idx = raw_val.get('slot_index')
                    if slot_idx == slot_index_to_remove:
                        slots_data.pop(i)
                    else:
                        self._remove_slot_from_slots_recursive(slot_obj, slot_index_to_remove)
                else:
                    self._remove_slot_from_slots_recursive(slot_obj, slot_index_to_remove)
                i -= 1
        elif isinstance(slots_data, dict):
            for key in list(slots_data.keys()):
                val = slots_data[key]
                self._remove_slot_from_slots_recursive(val, slot_index_to_remove)
    def _save_changes(self):
        if not self.inventory:
            return
        self._save_stats_to_raw_data()
        self.inventory.save()
        self.saved.emit()
        QMessageBox.information(self, t('success.title', default='Success'), t('inventory.save_success', default='Inventory saved to memory. Use "Save Changes" in the File menu to write to disk.'))
    def load_player(self, uid: str, name: str=None):
        self.refresh_players()
        self.current_player_uid = uid
        self.current_player_name = name or uid
        for player in self._player_list:
            if player['uid'] == uid:
                self.player_select_btn.setText(player['display'])
                break
        self._show_inventory()
        self.modified = False
        self.inventory = get_player_inventory(self.current_player_uid)
        self._refresh_display()
    def refresh_labels(self):
        self.title_label.setText(t('inventory.title', default='Player Inventory'))
        self.stats_panel.refresh_labels()
        self.main_grid.refresh_labels()
        self.key_grid.refresh_labels()
        if hasattr(self, 'inv_loadout_btn'):
            self.inv_loadout_btn.setText(t('inventory.loadouts_btn', default='Loadouts'))
        if hasattr(self, 'inv_clear_btn'):
            self.inv_clear_btn.setText(t('inventory.clear_btn', default='Clear'))
        if hasattr(self, 'equip_loadout_btn'):
            self.equip_loadout_btn.setText(t('inventory.equip_loadouts_btn', default='Loadouts'))
        if hasattr(self, 'equip_clear_btn'):
            self.equip_clear_btn.setText(t('inventory.equip_clear_btn', default='Clear'))
        if hasattr(self, 'unlock_all_map_btn'):
            self.unlock_all_map_btn.setText(t('inventory.unlock_all_map', default='Unlock All Map + Fast Travel'))
        self.inv_tabs.setTabText(0, t('inventory.main', default='Inventory'))
        self.inv_tabs.setTabText(1, t('inventory.key_items', default='Key Items'))
        self.inv_tabs.setTabText(2, t('inventory.stats', default='Stats'))
        if not self.current_player_uid:
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        self.equip_title.setText(t('inventory.equipment', default='Equipment'))
        equip_label_keys = ['weapon', 'accessory', 'food', 'head', 'body', 'shield', 'glider', 'module']
        for key in equip_label_keys:
            if key in self.equip_headers:
                self.equip_headers[key].setText(t(f'inventory.{key}', default=key.title()))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('inventory.select_player_hint', default='Select a player to edit their inventory'))
    def refresh(self):
        self._clear_display()
        self.refresh_players()
class QuantityDialog(QDialog):
    def __init__(self, current_qty: int=1, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('inventory.edit_qty', default='Edit Quantity'))
        self.setFixedSize(280, 120)
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        self.spin_box = QSpinBox()
        self.spin_box.setRange(1, 9999)
        self.spin_box.setValue(current_qty)
        layout.addWidget(self.spin_box)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok', default='OK'))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('button.cancel', default='Cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    def get_quantity(self) -> int:
        return self.spin_box.value()
_INV_LOADOUTS_PATH = os.path.join(_constants.get_src_path(), 'data', 'configs', 'inventory_loadouts.json')
_EQ_LOADOUTS_PATH = os.path.join(_constants.get_src_path(), 'data', 'configs', 'equipment_loadouts.json')
def _group_inventory_items(slots):
    items = {}
    for s in slots:
        item_id = s.get('item_id', '')
        if not item_id:
            continue
        qty = s.get('stack_count', 1)
        items[item_id] = items.get(item_id, 0) + qty
    result = []
    for item_id, qty in items.items():
        info = ItemData.get_item_by_asset(item_id)
        result.append({'id': item_id, 'qty': qty, 'name': info.get('name', item_id), 'type_a': info.get('type_a', '')})
    return result
def _is_key_item(item):
    return item.get('type_a') == 'EPalItemTypeA::Essential'
def _split_regular_key(items):
    reg = [{'id': i['id'], 'qty': i['qty'], 'name': i.get('name', i['id'])} for i in items if not _is_key_item(i)]
    key = [{'id': i['id'], 'qty': i['qty'], 'name': i.get('name', i['id'])} for i in items if _is_key_item(i)]
    return reg, key
def _merge_or_add_items(inventory, container_type, item_id, quantity):
    container = inventory.get_container(container_type)
    if not container:
        return False
    MAX_STACK = 9999
    remaining = quantity
    for s in container.slots:
        if s.get('item_id') == item_id and s.get('stack_count', 0) < MAX_STACK:
            cur = s.get('stack_count', 0)
            can_add = MAX_STACK - cur
            if can_add <= 0:
                continue
            to_add = min(remaining, can_add)
            s['stack_count'] = cur + to_add
            remaining -= to_add
            if remaining <= 0:
                return True
    return inventory.add_item(container_type, item_id, remaining)
def _consolidate_container_slots(container, container_type, singleton_set):
    slots = container.slots
    merged = {}
    singletons = []
    preserved = []
    for s in slots:
        item_id = s.get('item_id', '')
        if not item_id:
            continue
        qty = s.get('stack_count', 1)
        item_info = ItemData.get_item_by_asset(item_id)
        if item_info.get('type_a') in singleton_set:
            singletons.append(s)
        elif item_id == 'Money' and qty > 9999:
            preserved.append(s)
        else:
            merged[item_id] = merged.get(item_id, 0) + qty
    new_slots = []
    idx = 0
    for s in singletons:
        item_id = s.get('item_id', '')
        item_info = ItemData.get_item_by_asset(item_id)
        new_slots.append({'slot_index': idx, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': s.get('stack_count', 1), 'category': ItemData.get_item_category(item_id), 'container_type': container_type, 'raw_data': s.get('raw_data')})
        idx += 1
    for item_id, total_qty in merged.items():
        item_info = ItemData.get_item_by_asset(item_id)
        while total_qty > 0:
            stack = min(total_qty, 9999)
            new_slots.append({'slot_index': idx, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': stack, 'category': ItemData.get_item_category(item_id), 'container_type': container_type, 'raw_data': None})
            idx += 1
            total_qty -= stack
    container.update_slots(new_slots)
    if preserved:
        sc = container._standardized_container
        from palworld_aio.inventory.standardized_container import ContainerSlot
        for s in preserved:
            item_id = s.get('item_id', '')
            qty = s.get('stack_count', 1)
            empty_idx = sc._find_empty_slot()
            if empty_idx is not None:
                while len(sc.slots) <= empty_idx:
                    sc.slots.append(ContainerSlot(slot_index=len(sc.slots)))
                slot = sc.slots[empty_idx]
                slot.item_id = item_id
                slot.count = qty
                slot.dynamic_id = None
                slot.raw_data = slot._create_raw_data()
class InventoryLoadoutDialog(QDialog):
    def __init__(self, parent, get_current_items_fn, apply_loadout_fn, title=None, get_extra_fn=None, loadouts_path=None, key_prefix='inventory'):
        super().__init__(parent)
        self._get_items = get_current_items_fn
        self._apply_fn = apply_loadout_fn
        self._get_extra_fn = get_extra_fn
        self._kp = key_prefix
        base_dir = _constants.get_src_path()
        self._loadouts_path = loadouts_path or os.path.join(base_dir, 'data', 'configs', 'inventory_loadouts.json')
        self.setWindowTitle(title or t(f'{key_prefix}.loadouts_title', default='Inventory Loadouts'))
        self.setMinimumSize(420, 400)
        self.setMaximumSize(520, 500)
        self.setStyleSheet(DARK_THEME_STYLE)
        self._setup_ui()
    def _t(self, key, default='', **kwargs):
        return t(f'{self._kp}_{key}', default=default, **kwargs)
    def _setup_ui(self):
        self._load_loadouts()
        inner = QWidget()
        inner.setStyleSheet('QWidget { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        list_lbl = QLabel(self._t('loadouts_saved', default='Saved Loadouts:'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        il.addWidget(list_lbl)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet('QListWidget { background: rgba(10,14,20,0.95); border: 1px solid rgba(125,211,252,0.15); border-radius: 4px; color: #E2E8F0; font-size: 10px; } QListWidget::item { padding: 6px 8px; } QListWidget::item:hover { background: rgba(125,211,252,0.08); } QListWidget::item:selected { background: rgba(125,211,252,0.15); color: #7DD3FC; }')
        self._refresh_list()
        il.addWidget(self.list_widget, 1)
        info_lbl = QLabel(self._t('loadouts_info', default=''))
        info_lbl.setStyleSheet('font-size: 9px; color: #94a3b8; background: transparent; border: none; padding: 2px 0;')
        info_lbl.setWordWrap(True)
        il.addWidget(info_lbl)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        save_btn = QPushButton(self._t('loadouts_save', default='Save Current'))
        save_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(16,185,129,0.22); color: #FFFFFF; }')
        btn_row.addWidget(save_btn)
        load_btn = QPushButton(self._t('loadouts_apply', default='Apply Selected'))
        load_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.22); color: #FFFFFF; }')
        btn_row.addWidget(load_btn)
        delete_btn = QPushButton(self._t('loadouts_delete_btn', default='Delete'))
        delete_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(251,113,133,0.22); color: #FFFFFF; }')
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        close_btn = QPushButton(self._t('loadouts_close', default='Close'))
        close_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 20px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.16); color: #FFFFFF; }')
        btn_row.addWidget(close_btn)
        il.addLayout(btn_row)
        save_btn.clicked.connect(self._do_save)
        load_btn.clicked.connect(self._do_load)
        delete_btn.clicked.connect(self._do_delete)
        close_btn.clicked.connect(self.accept)
        self.list_widget.itemDoubleClicked.connect(self._do_load)
        dlg_layout = QVBoxLayout(self)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(inner)
    def _load_loadouts(self):
        if os.path.exists(self._loadouts_path):
            try:
                self._loadouts = json_tools.load(self._loadouts_path)
            except Exception:
                self._loadouts = {}
        else:
            self._loadouts = {}
    def _save_loadouts(self):
        try:
            os.makedirs(os.path.dirname(self._loadouts_path), exist_ok=True)
            json_tools.dump(self._loadouts, self._loadouts_path, indent=2)
        except Exception as e:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_save_error', default=f'Failed to save: {e}'))
    def _refresh_list(self):
        self.list_widget.clear()
        for name in sorted(self._loadouts.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            self.list_widget.addItem(item)
    def _do_save(self):
        items = self._get_items()
        if not items:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_no_items', default='No items to save.'))
            return
        name, ok = QInputDialog.getText(self, self._t('loadouts_save_title', default='Save Loadout'), self._t('loadouts_save_prompt', default='Loadout name:'), text='')

        if not ok or not name.strip():
            return
        name = name.strip()
        if isinstance(items, dict):
            reg, key = [], []
            equipment = items
        else:
            reg, key = _split_regular_key(items)
            equipment = {}
        if not equipment and self._get_extra_fn:
            extra = self._get_extra_fn()
            if extra:
                equipment = extra
        data = {'regular': reg, 'key_items': key}
        if equipment:
            data['equipment'] = equipment
        self._loadouts[name] = data
        self._save_loadouts()
        self._refresh_list()
        from loading_manager import show_information
        show_information(self, self.windowTitle(), self._t('loadouts_saved_ok', name=name, default=f'Loadout "{name}" saved.'))
    def _do_load(self):
        sel = self.list_widget.currentItem()
        if not sel:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_select_first', default='Select a loadout first.'))
            return
        name = sel.data(Qt.UserRole)
        data = self._loadouts.get(name)
        if not data:
            return
        self._apply_fn(data.get('regular', []), data.get('key_items', []), data.get('equipment', {}))
        from loading_manager import show_information
        show_information(self, self.windowTitle(), self._t('loadouts_applied', name=name, default=f'Loadout "{name}" applied.'))
    def _do_delete(self):
        sel = self.list_widget.currentItem()
        if not sel:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_select_first', default='Select a loadout first.'))
            return
        name = sel.data(Qt.UserRole)
        from loading_manager import show_question
        if not show_question(self, self.windowTitle(), self._t('loadouts_delete_confirm', name=name, default=f'Delete "{name}"?')):
            return
        self._loadouts.pop(name, None)
        self._save_loadouts()
        row = self.list_widget.row(sel)
        self.list_widget.takeItem(row)
        from loading_manager import show_information
        show_information(self, self.windowTitle(), self._t('loadouts_deleted', name=name, default=f'Loadout "{name}" deleted.'))