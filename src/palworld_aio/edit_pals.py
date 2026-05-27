import os
import math
from palworld_save_tools import json_tools
import uuid
import threading
from functools import partial
import shiboken6
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout, QCheckBox, QFrame, QTabWidget, QScrollArea, QWidget, QGridLayout, QListWidget, QListWidgetItem, QInputDialog, QTableWidget, QApplication, QProgressBar, QAbstractItemView, QCompleter, QGraphicsOpacityEffect, QMenu, QStyledItemDelegate, QSizePolicy, QStyle, QStackedWidget
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QPointF, QEvent, QSize, QRect, QRectF, QThread
from PySide6.QtGui import QIcon, QFont, QPixmap, QRegion, QCursor, QPainter, QPainterPath, QPen, QBrush, QFontMetrics, QPalette, QColor, QShortcut, QKeySequence, QLinearGradient
from i18n import t
from loading_manager import show_information, show_warning, show_question
import nerdfont as nf
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, sav_to_gvasfile, gvasfile_to_sav, extract_value, format_character_key, json_to_sav, calculate_max_hp, get_pal_data, safe_dict_get, safe_nested_get, resolve_name
from palworld_aio.ui.styles import DIALOG_STYLE, PICKER_BG_STYLE, PICKER_SEARCH_STYLE, PICKER_LIST_STYLE, INPUT_DIALOG_STYLE, TOOLTIP_STYLE, wrap_tooltip_text
from palworld_aio.ui.sidebar_widget import NerdBtn
_PAL_STYLESHEET = '\nQWidget#palRoot {\n    background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,\n        stop:0 rgba(8,10,16,0.98),stop:0.5 rgba(6,12,20,0.98),stop:1 rgba(4,8,16,0.98));\n}\nQWidget#partyPanel {\n    background: rgba(12,16,24,0.85);\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 8px;\n}\nQWidget#partyPanel QLabel {\n    color: #C8D8E8;\n}\nQWidget#palboxPanel {\n    background: rgba(12,16,24,0.85);\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 8px;\n}\nQWidget#palInfoPanel {\n    background: rgba(12,16,24,0.85);\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 8px;\n}\nQWidget#palInfoPanel QLabel {\n    color: #C8D8E8;\n}\nQLabel#boxHeader {\n    font-size: 18px;\n    font-weight: 700;\n    color: #7DD3FC;\n    padding: 4px 8px;\n    background: rgba(125,211,252,0.06);\n    border-radius: 4px;\n    min-width: 80px;\n    qproperty-alignment: AlignCenter;\n}\nQPushButton#navBtn {\n    background: rgba(125,211,252,0.08);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 14px;\n    font-size: 14px;\n    font-weight: 600;\n    min-width: 32px;\n}\nQPushButton#navBtn:hover {\n    background: rgba(125,211,252,0.18);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQPushButton#navBtn:pressed {\n    background: rgba(125,211,252,0.1);\n}\n'
def _load_pal_exp_table():
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'pal_exp_table.json')
        return json_tools.load(path)
    except Exception as e:
        print(f'Error loading PAL_EXP_TABLE: {e}')
        return {}
PAL_EXP_TABLE = _load_pal_exp_table()
_FRIENDSHIP_THRESHOLDS = None
def _ensure_friendship_thresholds():
    global _FRIENDSHIP_THRESHOLDS
    if _FRIENDSHIP_THRESHOLDS is not None:
        return _FRIENDSHIP_THRESHOLDS
    _FRIENDSHIP_THRESHOLDS = []
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'friendship.json')
        data = json_tools.load(path)
        entries = []
        for v in data.values():
            r = v.get('FriendshipRank', -1)
            if r >= 0:
                entries.append((r, v.get('RequiredPoint', 0)))
        entries.sort()
        _FRIENDSHIP_THRESHOLDS = [pt for _, pt in entries]
    except Exception as e:
        print(f'Error loading friendship data: {e}')
        _FRIENDSHIP_THRESHOLDS = [0, 6000, 13000, 21000, 30000, 40000, 55000, 80000, 110000, 150000, 200000]
    return _FRIENDSHIP_THRESHOLDS
_PAL_BASE_DATA_CACHE = {}
def _load_pal_base_data():
    if _PAL_BASE_DATA_CACHE:
        return _PAL_BASE_DATA_CACHE
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'characters.json')
        data = json_tools.load(path)
        for p in data.get('pals', []):
            a = p.get('asset', '').lower()
            if not a:
                continue
            _PAL_BASE_DATA_CACHE[a] = p
        for a, p in list(_PAL_BASE_DATA_CACHE.items()):
            if p.get('elements') or 'boss_' in a:
                continue
            boss_key = f'boss_{a}'
            boss_entry = _PAL_BASE_DATA_CACHE.get(boss_key)
            if boss_entry and boss_entry.get('elements'):
                p = dict(p)
                p['elements'] = boss_entry['elements']
                if boss_entry.get('stats'):
                    p['stats'] = {**boss_entry['stats'], **p.get('stats', {})}
                _PAL_BASE_DATA_CACHE[a] = p
        return _PAL_BASE_DATA_CACHE
    except Exception as e:
        print(f'Error loading pal base data: {e}')
        return {}
def get_pal_base_data(cid):
    cache = _load_pal_base_data()
    key = cid.lower().replace('boss_', '').replace('b_o_s_s_', '')
    entry = cache.get(key)
    if entry:
        return entry
    for ckey, centry in cache.items():
        if key in ckey or ckey in key:
            return centry
    return None
class FramelessDialog(QDialog):
    def __init__(self, title_key='edit_pals.title', parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_position = QPoint()
        self._maximized = False
        self._normal_geometry = None
        self.container = QWidget(self)
        self.container.setObjectName('editPalsContainer')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.container)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.title_bar = QWidget(self.container)
        self.title_bar.setObjectName('editPalsTitleBar')
        self.title_bar.setFixedHeight(48)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(16, 0, 8, 0)
        self.icon_label = QLabel('🐾')
        self.icon_label.setObjectName('titleBarIcon')
        title_layout.addWidget(self.icon_label)
        self.title_label = QLabel(t(title_key))
        self.title_label.setObjectName('titleBarTitle')
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.minimize_btn = QPushButton('−')
        self.minimize_btn.setObjectName('titleBarMinimize')
        self.minimize_btn.setFixedSize(36, 28)
        self.minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.minimize_btn)
        self.maximize_btn = QPushButton('□')
        self.maximize_btn.setObjectName('titleBarMaximize')
        self.maximize_btn.setFixedSize(36, 28)
        self.maximize_btn.clicked.connect(self._toggle_maximize)
        title_layout.addWidget(self.maximize_btn)
        self.close_btn = QPushButton('×')
        self.close_btn.setObjectName('titleBarClose')
        self.close_btn.setFixedSize(36, 28)
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.close_btn)
        container_layout.addWidget(self.title_bar)
        self.content_widget = QWidget(self.container)
        self.content_widget.setObjectName('editPalsContent')
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 12, 16, 16)
        container_layout.addWidget(self.content_widget)
        self._apply_styles()
        self.title_bar.installEventFilter(self)
    def _apply_styles(self):
        self.setStyleSheet('\n            QWidget#editPalsContainer {\n                background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,\n                            stop:0 rgba(12,14,18,0.98),stop:0.5 rgba(10,16,22,0.98),stop:1 rgba(8,12,18,0.98));\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 12px;\n            }\n            QWidget#editPalsTitleBar {\n                background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:0,\n                            stop:0 rgba(125,211,252,0.08),stop:1 rgba(167,139,250,0.08));\n                border: none;\n                border-top-left-radius: 12px;\n                border-top-right-radius: 12px;\n            }\n            QLabel#titleBarIcon {\n                font-size: 20px;\n                padding: 0px 4px;\n            }\n            QLabel#titleBarTitle {\n                font-size: 14px;\n                font-weight: 700;\n                color: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:0,\n                            stop:0 #7DD3FC,stop:1 #A78BFA);\n                padding: 0px 8px;\n            }\n            QPushButton#titleBarMinimize,QPushButton#titleBarMaximize {\n                background: transparent;\n                border: none;\n                color: #A6B8C8;\n                font-size: 16px;\n                font-weight: bold;\n                border-radius: 4px;\n            }\n            QPushButton#titleBarMinimize:hover,QPushButton#titleBarMaximize:hover {\n                background: rgba(255,255,255,0.1);\n                color: #FFFFFF;\n            }\n            QPushButton#titleBarClose {\n                background: transparent;\n                border: none;\n                color: #FB7185;\n                font-size: 20px;\n                font-weight: bold;\n                border-radius: 4px;\n            }\n            QPushButton#titleBarClose:hover {\n                background: rgba(251,113,133,0.2);\n            }\n            QWidget#editPalsContent {\n                background: transparent;\n            }\n        ')
    def _toggle_maximize(self):
        if self._maximized:
            self.showNormal()
            self._maximized = False
            self.maximize_btn.setText('□')
        else:
            self._normal_geometry = self.geometry()
            self.showMaximized()
            self._maximized = True
            self.maximize_btn.setText('❐')
    def eventFilter(self, obj, event):
        if obj == self.title_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    event.accept()
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() == Qt.LeftButton and self._drag_position:
                    self.move(event.globalPosition().toPoint() - self._drag_position)
                    event.accept()
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                self._toggle_maximize()
                event.accept()
                return True
        return super().eventFilter(obj, event)
    def set_title(self, title_key):
        self.title_label.setText(t(title_key))
    def set_title_text(self, text):
        self.title_label.setText(text)
class StarButton(QPushButton):
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mouseReleaseEvent(event)
        else:
            event.ignore()
class StrokedLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._text_color = Qt.white
    def setStyleSheet(self, style):
        super().setStyleSheet(style)
        if 'color:' in style:
            try:
                import re
                color_match = re.search('color:\\s*([^;]+)', style)
                if color_match:
                    color_str = color_match.group(1).strip()
                    if color_str.startswith('#'):
                        self._text_color = QColor(color_str)
                    elif color_str in ['white', 'black', 'red', 'blue', 'green', 'yellow', 'purple', 'pink']:
                        color_map = {'white': Qt.white, 'black': Qt.black, 'red': Qt.red, 'blue': Qt.blue, 'green': Qt.green, 'yellow': Qt.yellow, 'purple': QColor('#7DD3FC'), 'pink': QColor('#FB7185')}
                        self._text_color = color_map.get(color_str, Qt.white)
            except:
                pass
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        bg = QColor(0, 0, 0, 180)
        border = QColor(125, 211, 252, 64)
        painter.setBrush(bg)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(rect, 3, 3)
        path = QPainterPath()
        font = self.font()
        pen = QPen(Qt.black, 2)
        pen.setJoinStyle(Qt.RoundJoin)
        metrics = QFontMetrics(font)
        text_w = metrics.horizontalAdvance(self.text())
        x = (self.width() - text_w) // 2
        y = (self.height() + metrics.ascent() - metrics.descent()) // 2
        path.addText(x, y, font, self.text())
        painter.strokePath(path, pen)
        painter.fillPath(path, QBrush(self._text_color))
_ICON_CACHE = {}
_PIXMAP_CACHE = {}
_CACHE_LOCK = threading.Lock()
_PAL_ICON_LOOKUP = None
_PAL_ICON_LOOKUP_NPC = None
def _ensure_pal_icon_lookup():
    global _PAL_ICON_LOOKUP, _PAL_ICON_LOOKUP_NPC
    if _PAL_ICON_LOOKUP is not None:
        return
    _PAL_ICON_LOOKUP = {}
    _PAL_ICON_LOOKUP_NPC = {}
    base_dir = constants.get_base_path()
    try:
        paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'characters.json')
        paldata = json_tools.load(paldata_path)
        for pal in paldata.get('pals', []):
            asset = pal.get('asset', '').lower()
            icon = pal.get('icon', '')
            if asset and icon:
                _PAL_ICON_LOOKUP[asset] = os.path.join(base_dir, 'resources', 'game_data', icon.lstrip('/'))
    except Exception:
        pass
    try:
        npcdata_path = os.path.join(base_dir, 'resources', 'game_data', 'characters.json')
        npcdata = json_tools.load(npcdata_path)
        for npc in npcdata.get('npcs', []):
            asset = npc.get('asset', '').lower()
            icon = npc.get('icon', '')
            if asset and icon:
                _PAL_ICON_LOOKUP_NPC[asset] = os.path.join(base_dir, 'resources', 'game_data', icon.lstrip('/'))
    except Exception:
        pass
def _lookup_icon_in_data(asset_name: str, base_dir: str) -> str | None:
    _ensure_pal_icon_lookup()
    path = _PAL_ICON_LOOKUP.get(asset_name.lower())
    if path and os.path.exists(path):
        return path
    path = _PAL_ICON_LOOKUP_NPC.get(asset_name.lower())
    if path and os.path.exists(path):
        return path
    return None
def _get_pal_icon_path(character_id):
    base_dir = constants.get_base_path()
    cid_lower = character_id.lower()
    with _CACHE_LOCK:
        if cid_lower in _ICON_CACHE:
            return _ICON_CACHE[cid_lower]
    icon_path = _lookup_icon_in_data(cid_lower, base_dir)
    if not icon_path or not os.path.exists(icon_path):
        cid_stripped = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
        if cid_stripped != cid_lower:
            icon_path = _lookup_icon_in_data(cid_stripped, base_dir)
    if not icon_path or not os.path.exists(icon_path):
        cid_for_guess = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
        icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', f'{cid_for_guess}.webp')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'T_icon_unknown.webp')
    with _CACHE_LOCK:
        _ICON_CACHE[cid_lower] = icon_path
    return icon_path
def _get_cached_pixmap(icon_path, size=64):
    if not icon_path or not os.path.exists(icon_path):
        return None
    pixmap_key = f'{icon_path}_{size}x{size}'
    with _CACHE_LOCK:
        cached = _PIXMAP_CACHE.get(pixmap_key)
        if cached is not None:
            return cached
    pixmap = QPixmap(icon_path)
    if pixmap.isNull():
        return None
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if scaled.isNull():
        return None
    with _CACHE_LOCK:
        _PIXMAP_CACHE[pixmap_key] = scaled
    return scaled
class PalIcon(QFrame):
    clicked = Signal()
    rightClicked = Signal(int, str)
    entered = Signal()
    left = Signal()
    def __init__(self, pal_data=None, tab=None, slot_index=0, tab_name='', parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.slot_index = slot_index
        self.tab_name = tab_name
        self.selected = False
        self.setFixedSize(64, 64)
        self.setObjectName('palIconNew')
        self._setup_ui()
        self.setAcceptDrops(False)
        self.setMouseTracking(True)
    def enterEvent(self, event):
        self.entered.emit()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)
    def _get_raw_data(self):
        if not self.pal_data:
            return None
        try:
            if 'data' in self.pal_data:
                return self.pal_data['data']
            elif 'value' in self.pal_data:
                return safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            return self.pal_data
        except Exception:
            return None
    def _setup_ui(self):
        self._clear_ui()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bg = QWidget(self)
        bg.setObjectName('slotBg')
        bg.setStyleSheet('QWidget#slotBg { background: transparent; }')
        self.bg = bg
        raw = self._get_raw_data()
        if not raw or not isinstance(raw, dict):
            self.setStyleSheet('QFrame#palIconNew { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; }')
            return
        cid = extract_value(raw, 'CharacterID', '')
        level = extract_value(raw, 'Level', 1)
        nick = extract_value(raw, 'NickName', '')
        gender_data = extract_value(raw, 'Gender', {})
        if isinstance(gender_data, dict) and 'value' in gender_data:
            gender = gender_data['value']
        elif isinstance(gender_data, str):
            gender = gender_data
        else:
            gender = 'EPalGenderType::Female'
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        icon_path = _get_pal_icon_path(cid)
        pix = _get_cached_pixmap(icon_path, 48)
        icon_label = QLabel(self)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(48, 48)
        icon_label.setStyleSheet('background: transparent; border: none;')
        if pix:
            icon_label.setPixmap(pix)
        icon_label.move(8, 6)
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_label.show()
        self._elem_badge = QLabel(self)
        self._elem_badge.setFixedSize(12, 12)
        self._elem_badge.move(50, 4)
        self._elem_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        base_el_data = get_pal_base_data(cid)
        if base_el_data:
            els = base_el_data.get('elements', {})
            if els:
                en = next(iter(els))
                ep = _get_element_pixmap(en, 'small', 12)
                if ep:
                    self._elem_badge.setPixmap(ep)
        self._elem_badge.show()
        level_label = StrokedLabel(f'Lv{level}')
        level_label.setStyleSheet('color: #FFFFFF; font-size: 9px; font-weight: bold; background: transparent;')
        level_label.setFixedSize(32, 14)
        level_label.move(2, 48)
        level_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        level_label.show()
        if is_boss:
            badge = QLabel('α', self)
            badge.setStyleSheet('color: #F59E0B; font-size: 12px; font-weight: bold; background: rgba(0,0,0,0.6); border-radius: 8px; border: 1px solid rgba(245,158,11,0.4);')
            badge.setFixedSize(18, 18)
            badge.setAlignment(Qt.AlignCenter)
            badge.move(2, 2)
            badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            badge.show()
        elif is_lucky:
            badge = QLabel('☆', self)
            badge.setStyleSheet('color: #A78BFA; font-size: 14px; font-weight: bold; background: rgba(0,0,0,0.6); border-radius: 8px; border: 1px solid rgba(167,139,250,0.4);')
            badge.setFixedSize(18, 18)
            badge.setAlignment(Qt.AlignCenter)
            badge.move(2, 2)
            badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            badge.show()
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        if nick:
            pal_name = f'{nick}'
        tip = f'{pal_name} [Lv.{level}]'
        base = get_pal_base_data(cid)
        if base and base.get('description'):
            tip += f'\n\n{wrap_tooltip_text(base["description"])}'
        self.setToolTip(tip)
        self.setStyleSheet('QFrame#palIconNew { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; } QFrame#palIconNew:hover { background: rgba(125,211,252,0.08); border: 1px solid rgba(125,211,252,0.25); }')
        self.bg.lower()
    def _clear_ui(self):
        for child in self.findChildren((QLabel, QWidget)):
            if child is not self.bg and child.objectName() != 'slotBg':
                try:
                    child.deleteLater()
                except RuntimeError:
                    pass
        QApplication.processEvents()
        self.update()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def contextMenuEvent(self, event):
        if self.pal_data:
            self.clicked.emit()
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
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('QFrame#palIconNew { background: rgba(125,211,252,0.12); border: 2px solid #7DD3FC; border-radius: 6px; }')
        else:
            self.setStyleSheet('QFrame#palIconNew { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; } QFrame#palIconNew:hover { background: rgba(125,211,252,0.08); border: 1px solid rgba(125,211,252,0.25); }')
    def update_display(self):
        self._setup_ui()
    def hide_badges(self):
        pass
    def update_character_id(self, new_cid):
        if not self.pal_data:
            return
        try:
            raw = self._get_raw_data()
            if not isinstance(raw, dict):
                return
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': new_cid}
            self.update_display()
        except Exception:
            pass
    def update_boss_status(self, is_boss):
        self.update_display()
    def update_rare_status(self, is_lucky):
        self.update_display()
class PalCardWidget(QFrame):
    clicked = Signal()
    def __init__(self, pal_data=None, parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.selected = False
        self.setObjectName('palCardNew')
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def _get_raw_data(self):
        if not self.pal_data:
            return None
        try:
            if 'data' in self.pal_data:
                return self.pal_data['data']
            return safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
        except Exception:
            return None
    def _setup_ui(self):
        for child in self.findChildren(QWidget):
            child.deleteLater()
        raw = self._get_raw_data()
        self.setFixedHeight(72)
        if not raw or not isinstance(raw, dict):
            self.setStyleSheet('QFrame#palCardNew { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; }')
            return
        cid = extract_value(raw, 'CharacterID', '')
        level = extract_value(raw, 'Level', 1)
        nick = extract_value(raw, 'NickName', '')
        hp = extract_value(raw, 'Hp', 0)
        max_hp = extract_value(raw, 'MaxHp', hp)
        if max_hp <= 0:
            max_hp = hp if hp > 0 else 100
        exp = extract_value(raw, 'Exp', 0)
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        if nick:
            pal_name = f'{nick}'
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        icon_path = _get_pal_icon_path(cid)
        pix = _get_cached_pixmap(icon_path, 48)
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        if pix:
            icon_label.setPixmap(pix)
        icon_label.setStyleSheet('background: transparent; border: none;')
        layout.addWidget(icon_label)
        info = QVBoxLayout()
        info.setSpacing(2)
        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_lbl = QLabel(pal_name)
        name_lbl.setStyleSheet('color: #E2E8F0; font-size: 13px; font-weight: 600; background: transparent;')
        name_row.addWidget(name_lbl)
        lvl_lbl = QLabel(f'Lv.{level}')
        lvl_lbl.setStyleSheet('color: #7DD3FC; font-size: 11px; font-weight: 700; background: transparent;')
        name_row.addWidget(lvl_lbl)
        base_el_data = get_pal_base_data(cid)
        if base_el_data:
            els = base_el_data.get('elements', {})
            for en in els:
                ep = _get_element_pixmap(en, 'small', 12)
                if ep:
                    el_icon = QLabel()
                    el_icon.setFixedSize(12, 12)
                    el_icon.setPixmap(ep)
                    el_icon.setStyleSheet('background: transparent; border: none;')
                    name_row.addWidget(el_icon)
                break
        name_row.addStretch()
        info.addLayout(name_row)
        hp_bar = QFrame()
        hp_bar.setFixedHeight(8)
        hp_ratio = hp / max_hp if max_hp > 0 else 0
        hp_bar.setStyleSheet(f'background: rgba(55,65,81,0.5); border-radius: 4px; border: 1px solid rgba(16,185,129,0.2);')
        hp_fill = QFrame(hp_bar)
        hp_fill.setFixedHeight(6)
        w = int(max(4, hp_ratio * 200))
        hp_fill.setFixedWidth(w)
        hp_fill.move(1, 1)
        hp_fill.setStyleSheet(f'background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 3px;')
        info.addWidget(hp_bar)
        exp_bar = QFrame()
        exp_bar.setFixedHeight(6)
        exp_ratio = min(exp / 1000.0, 1.0) if exp else 0
        exp_bar.setStyleSheet('background: rgba(55,65,81,0.5); border-radius: 3px; border: 1px solid rgba(99,102,241,0.15);')
        exp_fill = QFrame(exp_bar)
        exp_fill.setFixedHeight(4)
        ew = int(max(4, exp_ratio * 200))
        exp_fill.setFixedWidth(ew)
        exp_fill.move(1, 1)
        exp_fill.setStyleSheet('background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366F1,stop:1 #818CF8); border-radius: 2px;')
        info.addWidget(exp_bar)
        layout.addLayout(info)
        lock_btn = QPushButton('🔓')
        lock_btn.setFixedSize(24, 24)
        lock_btn.setStyleSheet('QPushButton { background: transparent; border: none; font-size: 14px; color: rgba(255,255,255,0.3); } QPushButton:hover { color: #FFFFFF; }')
        lock_btn.setCheckable(True)
        layout.addWidget(lock_btn)
        self.setStyleSheet('QFrame#palCardNew { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; } QFrame#palCardNew:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('QFrame#palCardNew { background: rgba(125,211,252,0.1); border: 2px solid #7DD3FC; border-radius: 8px; }')
        else:
            self.setStyleSheet('QFrame#palCardNew { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; } QFrame#palCardNew:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
class PartySlotWidget(QFrame):
    clicked = Signal()
    rightClicked = Signal(int, str)
    entered = Signal()
    left = Signal()
    def __init__(self, pal_data=None, slot_index=0, parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.slot_index = slot_index
        self.selected = False
        self.setObjectName('partySlot')
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._lvl_overlay = None
        self._build()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._lvl_overlay and shiboken6.isValid(self._lvl_overlay) and (not self._lvl_overlay.isHidden()):
            self._lvl_overlay.move(8, self.height() - 14)
        if hasattr(self, '_badges') and self._badges:
            badge_x = self.width() - 6
            badge_y = 4
            for badge in self._badges:
                if shiboken6.isValid(badge) and (not badge.isHidden()):
                    bw = badge.width()
                    badge.move(badge_x - bw, badge_y if bw >= 14 else badge_y + 1)
                    badge_x -= bw + 2
        if hasattr(self, '_el_badges') and self._el_badges:
            el_x = 6
            el_y = 5
            for badge in self._el_badges:
                if shiboken6.isValid(badge) and (not badge.isHidden()):
                    badge.move(el_x, el_y)
                    el_x += 14
    def enterEvent(self, event):
        self.entered.emit()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def contextMenuEvent(self, event):
        if self.pal_data:
            self._context_click = True
            self.clicked.emit()
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
        self._lvl_overlay = None
        old_layout = self.layout()
        if old_layout:
            QWidget().setLayout(old_layout)
        for child in self.findChildren(QWidget):
            child.deleteLater()
        raw = self._get_raw()
        if not raw or not isinstance(raw, dict):
            self.setStyleSheet('QFrame#partySlot { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; }')
            return
        cid = extract_value(raw, 'CharacterID', '')
        level = extract_value(raw, 'Level', 1)
        nick = extract_value(raw, 'NickName', '')
        exp = extract_value(raw, 'Exp', 0)
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        if nick:
            pal_name = f'{nick}'
        tip = f'{pal_name} [Lv.{level}]'
        base = get_pal_base_data(cid)
        if base and base.get('description'):
            tip += f'<br><br>{wrap_tooltip_text(base["description"])}'
        self.setToolTip(tip)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        is_imported = extract_value(raw, 'bImportedCharacter', False)
        is_awake = bool(extract_value(raw, 'bIsAwakening', False))
        fav_idx = extract_value(raw, 'FavoriteIndex', 0)
        hp_val = safe_nested_get(raw, ['Hp', 'value', 'Value', 'value'], 0)
        max_hp = safe_nested_get(raw, ['MaxHP', 'value', 'Value', 'value'], 0)
        if max_hp <= 0:
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            friendship_rank = 0
            thr = _ensure_friendship_thresholds()
            for r in range(len(thr) - 1, 0, -1):
                if trust_points >= thr[r]:
                    friendship_rank = r
                    break
            rank_raw = extract_value(raw, 'Rank', 0)
            condenser_rank = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            base = get_pal_base_data(cid)
            if base:
                max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, friendship_rank, condenser_rank, is_awake)
        if max_hp <= 0:
            max_hp = hp_val if hp_val > 0 else 1
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(6)
        icon_path = _get_pal_icon_path(cid)
        pix = _get_cached_pixmap(icon_path, 48)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        if pix:
            icon_lbl.setPixmap(pix)
        icon_lbl.setStyleSheet('background: transparent; border: none;')
        layout.addWidget(icon_lbl)
        lvl_overlay = QLabel(f'{level}', self)
        lvl_overlay.setFixedSize(20, 12)
        lvl_overlay.setAlignment(Qt.AlignCenter)
        lvl_overlay.setStyleSheet('color: #7DD3FC; font-size: 9px; font-weight: bold; background: rgba(0,0,0,0.7); border: 1px solid rgba(125,211,252,0.25); border-radius: 3px;')
        lvl_overlay.move(8, self.height() - 14)
        lvl_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        lvl_overlay.show()
        self._lvl_overlay = lvl_overlay
        info = QVBoxLayout()
        info.setSpacing(1)
        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        name_lbl = QLabel(f'Lv.{level} {pal_name}')
        name_lbl.setStyleSheet('color: #E2E8F0; font-size: 12px; font-weight: 600; background: transparent;')
        name_row.addWidget(name_lbl)
        name_row.addStretch()
        info.addLayout(name_row)
        hp_pct = int(min(hp_val / max_hp * 100, 100)) if max_hp > 0 else 0
        self.hp_bar = QProgressBar()
        self.hp_bar.setFixedHeight(6)
        self.hp_bar.setRange(0, 100)
        self.hp_bar.setValue(hp_pct)
        self.hp_bar.setTextVisible(True)
        self.hp_bar.setFormat(f'{int(hp_val) // 1000} / {int(max_hp) // 1000}')
        self.hp_bar.setStyleSheet('QProgressBar { background: rgba(55,65,81,0.5); border: 1px solid rgba(16,185,129,0.15); border-radius: 3px; text-align: center; font-size: 6px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 2px; }')
        info.addWidget(self.hp_bar)
        exp_bar = QFrame()
        exp_bar.setFixedHeight(4)
        exp_ratio = min(exp / 1000.0, 1.0) if exp else 0
        exp_bar.setStyleSheet('background: rgba(55,65,81,0.5); border-radius: 2px; border: 1px solid rgba(99,102,241,0.1);')
        exp_fill = QFrame(exp_bar)
        exp_fill.setFixedHeight(3)
        exp_fill.setFixedWidth(int(max(3, exp_ratio * 180)))
        exp_fill.move(1, 1)
        exp_fill.setStyleSheet('background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366F1,stop:1 #818CF8); border-radius: 1px;')
        info.addWidget(exp_bar)
        layout.addLayout(info)
        self._badges = []
        self._el_badges = []
        badge_x = self.width() - 6
        badge_y = 4
        el_x = 6
        el_y = 5
        if fav_idx and int(fav_idx) > 0:
            lock_key = f'lock_{int(fav_idx)}'
            lock_pix = _get_ui_icon_pixmap(lock_key, 14) or _get_ui_icon_pixmap('lock_1', 14) or _get_ui_icon_pixmap('lock', 14)
            if lock_pix:
                fav_badge = QLabel(self)
                fav_badge.setPixmap(lock_pix)
                fav_badge.setFixedSize(14, 14)
                fav_badge.setStyleSheet('background: transparent; border: none;')
            else:
                fav_badge = QLabel('🔒', self)
                fav_badge.setStyleSheet('font-size: 9px; color: rgba(255,255,255,0.65); background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 7px;')
                fav_badge.setFixedSize(14, 14)
                fav_badge.setAlignment(Qt.AlignCenter)
            fav_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            fav_badge.move(badge_x - 14, badge_y)
            fav_badge.show()
            self._badges.append(fav_badge)
            badge_x -= 16
        if is_imported:
            dna_pix = _get_ui_icon_pixmap('dna', 12)
            if dna_pix:
                dna_icon = QLabel(self)
                dna_icon.setFixedSize(14, 14)
                dna_icon.setAlignment(Qt.AlignCenter)
                dna_icon.setPixmap(dna_pix)
                dna_icon.setStyleSheet('background: transparent; border: none;')
            else:
                dna_icon = QLabel('🧬', self)
                dna_icon.setFixedSize(14, 14)
                dna_icon.setAlignment(Qt.AlignCenter)
                dna_icon.setStyleSheet('font-size: 9px; background: transparent;')
            dna_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
            dna_icon.move(badge_x - 14, badge_y)
            dna_icon.show()
            self._badges.append(dna_icon)
            badge_x -= 16
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
            awake_badge.move(badge_x - 12, badge_y + 1)
            awake_badge.show()
            self._badges.append(awake_badge)
            badge_x -= 14
        if is_boss:
            boss_pix = _get_boss_alpha_pixmap(14)
            if boss_pix:
                boss_badge = QLabel(self)
                boss_badge.setPixmap(boss_pix)
                boss_badge.setFixedSize(14, 14)
                boss_badge.setAlignment(Qt.AlignCenter)
                boss_badge.setStyleSheet('background: transparent; border: none;')
                boss_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
                boss_badge.move(badge_x - 14, badge_y)
                boss_badge.show()
                self._badges.append(boss_badge)
                badge_x -= 16
        elif is_lucky:
            shiny_pix = _get_boss_shiny_pixmap(14)
            if shiny_pix:
                lucky_badge = QLabel(self)
                lucky_badge.setPixmap(shiny_pix)
                lucky_badge.setFixedSize(14, 14)
                lucky_badge.setAlignment(Qt.AlignCenter)
                lucky_badge.setStyleSheet('background: transparent; border: none;')
                lucky_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
                lucky_badge.move(badge_x - 14, badge_y)
                lucky_badge.show()
                self._badges.append(lucky_badge)
                badge_x -= 16
        base_el_data = get_pal_base_data(cid)
        if base_el_data:
            els = base_el_data.get('elements', {})
            for en in els:
                ep = _get_element_pixmap(en, 'small', 12)
                if ep:
                    el_icon = QLabel(self)
                    el_icon.setFixedSize(12, 12)
                    el_icon.setPixmap(ep)
                    el_icon.setStyleSheet('background: transparent; border: none;')
                    el_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
                    el_icon.move(el_x, el_y)
                    el_icon.show()
                    self._el_badges.append(el_icon)
                    el_x += 14
        self.setStyleSheet('QFrame#partySlot { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; } QFrame#partySlot:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('QFrame#partySlot { background: rgba(125,211,252,0.1); border: 2px solid #7DD3FC; border-radius: 8px; }')
        else:
            self.setStyleSheet('QFrame#partySlot { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; } QFrame#partySlot:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
    def update_display(self):
        self._build()
class PalboxSlotWidget(QFrame):
    clicked = Signal()
    rightClicked = Signal(int, str)
    entered = Signal()
    left = Signal()
    def __init__(self, pal_data=None, slot_index=0, parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.slot_index = slot_index
        self.selected = False
        self.setObjectName('palboxSlot')
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
        self.entered.emit()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def contextMenuEvent(self, event):
        if self.pal_data:
            self._context_click = True
            self.clicked.emit()
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
        for c in list(self._children):
            c.deleteLater()
        self._children = []
        raw = self._get_raw()
        if not raw or not isinstance(raw, dict):
            return
        cid = extract_value(raw, 'CharacterID', '')
        level = extract_value(raw, 'Level', 1)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        is_awake = extract_value(raw, 'bIsAwakening', False)
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
        is_imported = extract_value(raw, 'bImportedCharacter', False)
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
        fav_idx = extract_value(raw, 'FavoriteIndex', 0)
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
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        tip = f'{pal_name} [Lv.{level}]'
        base = get_pal_base_data(cid)
        if base and base.get('description'):
            tip += f'<br><br>{wrap_tooltip_text(base["description"])}'
        self.setToolTip(tip)
        self.setStyleSheet('QFrame#palboxSlot { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; } QFrame#palboxSlot:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
        self.resizeEvent(None)
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('QFrame#palboxSlot { background: rgba(125,211,252,0.1); border: 2px solid #7DD3FC; border-radius: 6px; }')
        else:
            self.setStyleSheet('QFrame#palboxSlot { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; } QFrame#palboxSlot:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
    def update_display(self):
        self._build()
class _ShinyStar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filled = True
        self._shining = False
        self._phase = 0.0
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background: transparent;')
    def set_filled(self, filled):
        self._filled = filled
        self.update()
    def set_phase(self, phase):
        self._phase = phase
        if self._shining:
            self.update()
    def start_shine(self):
        self._shining = True
        self.update()
    def stop_shine(self):
        self._shining = False
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        font = QFont()
        font.setPixelSize(14)
        painter.setFont(font)
        rect = self.rect()
        if not self._filled:
            painter.setPen(QColor(255, 215, 0, 40))
            painter.drawText(rect, Qt.AlignCenter, '★')
            painter.end()
            return
        painter.setPen(QColor('#FFD700'))
        painter.drawText(rect, Qt.AlignCenter, '★')
        if self._shining:
            w = rect.width()
            h = rect.height()
            text_path = QPainterPath()
            text_path.addText(0, 0, font, '★')
            br = text_path.boundingRect()
            ox = (w - br.width()) / 2 - br.x()
            oy = (h - br.height()) / 2 - br.y()
            text_path.translate(ox, oy)
            painter.setClipPath(text_path)
            sweep_x = self._phase * w * 1.4 - w * 0.2
            band = w * 0.14
            grad = QLinearGradient(sweep_x, rect.bottom(), sweep_x + band, rect.top())
            grad.setColorAt(0, QColor(255, 255, 200, 0))
            grad.setColorAt(0.5, QColor(255, 255, 255, 200))
            grad.setColorAt(1, QColor(255, 255, 200, 0))
            painter.fillRect(rect, grad)
        painter.end()
class _CircularIcon(QWidget):
    def __init__(self, size=80, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setFixedSize(size, size)
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()
    def clear(self):
        self._pixmap = None
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        path = QPainterPath()
        r = self.rect()
        path.addEllipse(r.adjusted(2, 2, -2, -2))
        painter.setClipPath(path)
        if self._pixmap and (not self._pixmap.isNull()):
            scaled = self._pixmap.scaled(r.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (r.width() - scaled.width()) // 2
            y = (r.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillPath(path, QBrush(QColor(30, 35, 45)))
            painter.setPen(QPen(QColor(100, 110, 130), 1))
            painter.setFont(QFont('Segoe UI', 16))
            painter.drawText(r, Qt.AlignCenter, '?')
_SKILL_EXCLUSION_NAMES = ['unknown skills', 'unknown skill', 'en_text', 'en text']
_SKILL_EXCLUSION_PATTERNS = ['Predator', 'RaidCutter', '_GYM_', 'PartnerSkill', 'Unique_', 'Funnel_', 'Human_', 'Scratch', 'Throw', 'WorkAttack', 'SelfDestruct_Bee', 'Weapon_Use', 'CreepingBubble']
_SKILL_DATA = None
_ELEMENT_DATA = None
def _ensure_element_data():
    global _ELEMENT_DATA
    if _ELEMENT_DATA is not None:
        return _ELEMENT_DATA
    _ELEMENT_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'skills.json')
        js = json_tools.load(path)
        for e in js.get('elements', []):
            if isinstance(e, dict) and 'name' in e:
                _ELEMENT_DATA[e['name'].lower()] = e
    except Exception:
        pass
    return _ELEMENT_DATA
def _get_element_pixmap(element_name, variant='small', size=16):
    if not element_name:
        return None
    data = _ensure_element_data()
    entry = data.get(element_name.lower(), {})
    icons = entry.get('icons', {})
    icon_rel = icons.get(variant, '')
    if not icon_rel:
        return None
    base_dir = constants.get_base_path()
    full_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel.lstrip('/'))
    if not os.path.exists(full_path):
        webp_path = os.path.splitext(full_path)[0] + '.webp'
        if os.path.exists(webp_path):
            full_path = webp_path
    return _get_cached_pixmap(full_path, size)
_UI_ICONS_DATA = None
def _ensure_ui_icons_data():
    global _UI_ICONS_DATA
    if _UI_ICONS_DATA is not None:
        return _UI_ICONS_DATA
    _UI_ICONS_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'uidata.json')
        js = json_tools.load(path)
        for key, icon_rel in js.get('ui_icons', {}).items():
            full_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel.lstrip('/'))
            if not os.path.exists(full_path):
                webp_path = os.path.splitext(full_path)[0] + '.webp'
                if os.path.exists(webp_path):
                    full_path = webp_path
            _UI_ICONS_DATA[key] = full_path
    except Exception:
        pass
    return _UI_ICONS_DATA
def _get_boss_alpha_pixmap(size=14):
    base_dir = constants.get_base_path()
    path = os.path.join(base_dir, 'resources', 'boss_alpha.webp')
    return _get_cached_pixmap(path, size)
def _get_boss_shiny_pixmap(size=14):
    base_dir = constants.get_base_path()
    path = os.path.join(base_dir, 'resources', 'boss_shiny.webp')
    return _get_cached_pixmap(path, size)
def _get_awake_pixmap(size=14):
    base_dir = constants.get_base_path()
    path = os.path.join(base_dir, 'resources', 'UI', 'pst_flame_icon.webp')
    return _get_cached_pixmap(path, size)
_BOSS_PREFIXES = ('BOSS_', 'PREDATOR_', 'GYM_', 'RAID_')
_PREFIX_LABELS = (' (Boss)', ' (Predator)', ' (Gym)', ' (Raid)', ' (Police)', ' (Summon)')
def _strip_prefix_label(name: str) -> str:
    for label in _PREFIX_LABELS:
        if name.endswith(label):
            return name[:-len(label)]
    return name
def _composite_badge(pixmap, badge_pixmap, icon_size):
    result = QPixmap(pixmap)
    painter = QPainter(result)
    bw = badge_pixmap.width()
    bh = badge_pixmap.height()
    painter.drawPixmap(2, 2, badge_pixmap)
    painter.end()
    return result
def _get_ui_icon_pixmap(icon_key, size=16):
    data = _ensure_ui_icons_data()
    icon_path = data.get(icon_key, '')
    if not icon_path:
        return None
    return _get_cached_pixmap(icon_path, size)
def _ensure_skill_data():
    global _SKILL_DATA
    if _SKILL_DATA is not None:
        return
    _SKILL_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'skills.json')
        js = json_tools.load(path)
        for s in js.get('skills', []):
            if isinstance(s, dict) and 'asset' in s:
                _SKILL_DATA[s['asset'].lower()] = s
    except Exception:
        pass
_PASSIVE_DATA = None
def _ensure_passive_data():
    global _PASSIVE_DATA
    if _PASSIVE_DATA is not None:
        return
    _PASSIVE_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'skills.json')
        js = json_tools.load(path)
        for p in js.get('passives', []):
            if isinstance(p, dict) and 'asset' in p:
                _PASSIVE_DATA[p['asset'].lower()] = p
    except Exception:
        pass
def _learn_all_skills_raw(raw):
    _ensure_skill_data()
    mastered = []
    for asset_lower, skill_info in _SKILL_DATA.items():
        name = skill_info.get('name', '')
        if any((exc in name.lower() for exc in _SKILL_EXCLUSION_NAMES)):
            continue
        original_asset = skill_info.get('asset', asset_lower)
        if any((pat.lower() in original_asset.lower() for pat in _SKILL_EXCLUSION_PATTERNS)):
            continue
        mastered.append(f'EPalWazaID::{original_asset}')
    ew_data = raw.get('EquipWaza', {})
    e_list = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
    if isinstance(e_list, list):
        for s in e_list:
            if s and s not in mastered:
                mastered.append(s)
    seen = set()
    mastered_unique = []
    for skill in mastered:
        if skill not in seen:
            seen.add(skill)
            mastered_unique.append(skill)
    raw['MasteredWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': mastered_unique}, 'type': 'ArrayProperty'}
def _toggle_boss_raw(raw, enable):
    cid = extract_value(raw, 'CharacterID', '')
    if enable:
        if not cid.upper().startswith('BOSS_'):
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'BOSS_' + cid}
        raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': False}
    elif cid.upper().startswith('BOSS_'):
        raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[5:]}
def _toggle_lucky_raw(raw, enable):
    raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': enable}
    if enable:
        cid = extract_value(raw, 'CharacterID', '')
        if cid.upper().startswith('BOSS_'):
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[5:]}
def _toggle_awake_raw(raw, enable):
    raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': enable}
def _toggle_dna_raw(raw, enable):
    raw['bImportedCharacter'] = {'id': None, 'type': 'BoolProperty', 'value': enable}
def _set_fav_raw(raw, idx):
    raw['FavoriteIndex'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': idx}}
def _max_stats_raw(raw):
    raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
    raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
    raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
    raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
    raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
    raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
    raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
    raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 5}}
    raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
    raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
def build_pal_context_menu(parent, raw):
    from PySide6.QtWidgets import QMenu
    menu = QMenu(parent)
    menu.setObjectName('editPalsContextMenu')
    cid = extract_value(raw, 'CharacterID', '') if raw else ''
    is_boss = cid.upper().startswith('BOSS_')
    is_lucky = extract_value(raw, 'IsRarePal', False) if raw else False
    is_awake = extract_value(raw, 'bIsAwakening', False) if raw else False
    is_dna = extract_value(raw, 'bImportedCharacter', False) if raw else False
    fav_idx = extract_value(raw, 'FavoriteIndex', 0) if raw else 0
    boss_action = menu.addAction(t('edit_pals.ctx.boss_alpha'))
    boss_action.setCheckable(True)
    boss_action.setChecked(is_boss)
    lucky_action = menu.addAction(t('edit_pals.ctx.lucky_shiny'))
    lucky_action.setCheckable(True)
    lucky_action.setChecked(is_lucky)
    awake_action = menu.addAction(t('edit_pals.ctx.awakened'))
    awake_action.setCheckable(True)
    awake_action.setChecked(is_awake)
    dna_action = menu.addAction(t('edit_pals.ctx.imported'))
    dna_action.setCheckable(True)
    dna_action.setChecked(is_dna)
    menu.addSeparator()
    fav_sub = QMenu(t('edit_pals.ctx.lock_level'), menu)
    fav_sub.setObjectName('editPalsContextMenu')
    lock_actions = []
    for i in range(4):
        sub_a = fav_sub.addAction(f'{t("edit_pals.ctx.lock_level")} {i}')
        sub_a.setCheckable(True)
        sub_a.setChecked(fav_idx == i)
        lock_actions.append(sub_a)
    fav_action = menu.addAction(t('edit_pals.ctx.favorited'))
    fav_action.setMenu(fav_sub)
    menu.addSeparator()
    max_action = menu.addAction(t('edit_pals.ctx.max_all_stats'))
    learn_action = menu.addAction(t('edit_pals.ctx.learn_all_moves'))
    menu.addSeparator()
    delete_action = menu.addAction(t('edit_pals.delete'))
    actions = {'boss': boss_action, 'lucky': lucky_action, 'awake': awake_action, 'dna': dna_action, 'fav': (fav_action, lock_actions), 'max': max_action, 'learn': learn_action, 'delete': delete_action}
    return (menu, actions)
def _fp64(value):
    return {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(value), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
def _byte(value):
    return {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': int(value)}}
def _guid(value):
    eu = '00000000-0000-0000-0000-000000000000'
    return {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': str(value), 'type': 'StructProperty'}
def _generate_pal_save_param(character_id, nickname, owner_uid, container_id, slot_index, group_id=None):
    if group_id is None:
        group_id = str(uuid.uuid4()).upper()
    instance_id = str(uuid.uuid4()).upper()
    empty_uuid = '00000000-0000-0000-0000-000000000000'
    time_val = 638486453957560000
    return {'key': {'PlayerUId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': empty_uuid, 'type': 'StructProperty'}, 'InstanceId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': instance_id, 'type': 'StructProperty'}, 'DebugName': {'id': None, 'type': 'StrProperty', 'value': ''}}, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'object': {'SaveParameter': {'struct_type': 'PalIndividualCharacterSaveParameter', 'struct_id': empty_uuid, 'id': None, 'value': {'CharacterID': {'id': None, 'type': 'NameProperty', 'value': character_id}, 'Gender': {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': 'EPalGenderType::Female'}}, 'NickName': {'id': None, 'type': 'StrProperty', 'value': nickname}, 'EquipWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': [f'EPalWazaID::Unique_{character_id}_Roll'] if character_id == 'SheepBall' else []}, 'type': 'ArrayProperty'}, 'MasteredWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'Hp': {'struct_type': 'FixedPoint64', 'struct_id': empty_uuid, 'id': None, 'value': {'Value': {'id': None, 'value': calculate_max_hp(get_pal_data(character_id), 1, 100, 0, character_id.upper().startswith('BOSS_'), False), 'type': 'Int64Property'}}, 'type': 'StructProperty'}, 'Talent_HP': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'Talent_Shot': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'Talent_Defense': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'FullStomach': {'id': None, 'type': 'FloatProperty', 'value': 150.0}, 'PassiveSkillList': {'array_type': 'NameProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'OwnedTime': {'struct_type': 'DateTime', 'struct_id': empty_uuid, 'id': None, 'value': time_val, 'type': 'StructProperty'}, 'OwnerPlayerUId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': owner_uid, 'type': 'StructProperty'}, 'OldOwnerPlayerUIds': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'OldOwnerPlayerUIds', 'prop_type': 'StructProperty', 'values': [owner_uid], 'type_name': 'Guid', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'SlotId': {'struct_type': 'PalCharacterSlotId', 'struct_id': empty_uuid, 'id': None, 'value': {'ContainerId': {'struct_type': 'PalContainerId', 'struct_id': empty_uuid, 'id': None, 'value': {'ID': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': container_id, 'type': 'StructProperty'}}, 'type': 'StructProperty'}, 'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}}, 'type': 'StructProperty'}, 'GotStatusPointList': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotStatusPointList', 'prop_type': 'StructProperty', 'values': [{'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大HP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大SP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '攻撃力'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '所持重量'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '捕獲率'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '作業速度'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'GotExStatusPointList': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotExStatusPointList', 'prop_type': 'StructProperty', 'values': [{'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大HP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大SP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '攻撃力'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '所持重量'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '作業速度'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'LastNickNameModifierPlayerUid': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': owner_uid, 'type': 'StructProperty'}}, 'type': 'StructProperty'}}, 'unknown_bytes': [0, 0, 0, 0], 'group_id': group_id, 'trailing_bytes': [0, 0, 0, 0]}, 'custom_type': '.worldSaveData.CharacterSaveParameterMap.Value.RawData', 'type': 'ArrayProperty'}}}
class CornerBracketWidget(QFrame):
    def __init__(self, border_color='#7DD3FC', parent=None):
        super().__init__(parent)
        self._border_color = QColor(border_color)
        self.setObjectName('cornerBracket')
        self.setStyleSheet('QFrame#cornerBracket { background: rgba(10,14,20,0.95); border: none; }')
        self.setFixedSize(56, 64)
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._border_color, 2)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        w, h = (self.width(), self.height())
        bl = 10
        painter.drawLine(0, bl, 0, 0)
        painter.drawLine(0, 0, bl, 0)
        painter.drawLine(w - bl, 0, w, 0)
        painter.drawLine(w, 0, w, bl)
        painter.drawLine(0, h - bl, 0, h)
        painter.drawLine(0, h, bl, h)
        painter.drawLine(w - bl, h, w, h)
        painter.drawLine(w, h, w, h - bl)
class PortraitBracketWidget(QWidget):
    def __init__(self, corner_color='#7DD3FC', parent=None):
        super().__init__(parent)
        self._corner_color = QColor(corner_color)
        self.setAttribute(Qt.WA_TranslucentBackground)
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._corner_color, 1.5)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        w, h = (self.width(), self.height())
        bl = 14
        painter.drawLine(0, bl, 0, 0)
        painter.drawLine(0, 0, bl, 0)
        painter.drawLine(w - bl, 0, w, 0)
        painter.drawLine(w, 0, w, bl)
        painter.drawLine(0, h - bl, 0, h)
        painter.drawLine(0, h, bl, h)
        painter.drawLine(w - bl, h, w, h)
        painter.drawLine(w, h, w, h - bl)
class SANTrackerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 100
        self.setFixedHeight(10)
        self.setMinimumWidth(50)
        self.setAttribute(Qt.WA_TranslucentBackground)
    def setValue(self, value):
        self._value = max(0, min(100, int(value)))
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = (self.width(), self.height())
        bar_h = 2
        y = (h - bar_h) // 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 35, 30))
        painter.drawRoundedRect(0, y, w, bar_h, 1, 1)
        gradient = QLinearGradient(0, 0, w, 0)
        gradient.setColorAt(0, QColor('#10B981'))
        gradient.setColorAt(1, QColor('#34D399'))
        painter.setBrush(gradient)
        fill_w = int(w * self._value / 100)
        if fill_w > 0:
            painter.drawRoundedRect(0, y, fill_w, bar_h, 1, 1)
        painter.setPen(QPen(QColor(16, 185, 129, 40), 1))
        for i in range(1, 5):
            tx = w * i // 5
            painter.drawLine(tx, y - 1, tx, y + bar_h + 1)
class SkillSlotFrame(QFrame):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = (self.width(), self.height())
        d = int(h * 0.2679)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 25, 35, 40))
        painter.drawRoundedRect(0, 0, w, h, 3, 3)
        path = QPainterPath()
        path.moveTo(w - d, 0)
        path.lineTo(w, 0)
        path.lineTo(w, h)
        path.closeSubpath()
        painter.setBrush(QColor(30, 38, 50, 60))
        painter.drawPath(path)
class GlowRing(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self._awakened = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(33)
        self.setStyleSheet('QFrame { background: transparent; border: none; }')
    def set_awakened(self, awakened):
        self._awakened = awakened
        if awakened:
            self._timer.start()
        else:
            self._timer.stop()
        self.update()
    def _animate(self):
        self._phase = (self._phase + 0.06) % (2 * math.pi)
        self.update()
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = (self.width(), self.height())
        cx, cy = (w / 2.0, h / 2.0)
        radius = min(w, h) / 2.0 - 1.5
        if self._awakened:
            pulse = (math.sin(self._phase) + 1.0) / 2.0
            for i in range(4, 0, -1):
                r = radius + i * 0.8
                alpha = int((28 + 30 * pulse) / i)
                hue_shift = int(30 * pulse) - i * 5
                red = min(255, 255)
                green = min(255, max(0, 160 - hue_shift))
                blue = min(255, max(0, 0))
                painter.setPen(QPen(QColor(red, green, blue, alpha), 1.0 + i * 0.4))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(cx, cy), r, r)
            painter.setPen(QPen(QColor('#FFB800'), 2.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
        else:
            painter.setPen(QPen(QColor(125, 211, 252, 115), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
class RotatingCircleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0.0
        self._pixmap = None
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'outer_frame_circle.webp')
        self._pixmap = QPixmap(path)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(33)
        self._timer.start()
        self.setStyleSheet('background: transparent; border: none;')
    def _tick(self):
        self._angle = (self._angle - 1.8) % 360.0
        self.update()
    def paintEvent(self, event):
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        pw, ph = (self._pixmap.width(), self._pixmap.height())
        scaled = self._pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        sw, sh = (scaled.width(), scaled.height())
        cx, cy = (self.width() / 2.0, self.height() / 2.0)
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        painter.drawPixmap(int(-sw / 2), int(-sh / 2), scaled)
        painter.end()
class PassiveEffectOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim_mode = None
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(33)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background: transparent; border: none;')
        self.hide()
    def set_mode(self, mode):
        self._anim_mode = mode
        self._phase = 0.0
        if mode:
            self._timer.start()
            self.show()
        else:
            self._timer.stop()
            self.hide()
        self.update()
    def _tick(self):
        self._phase = (self._phase + 0.03) % 10000.0
        self.update()
    def paintEvent(self, event):
        if not self._anim_mode:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = (self.width(), self.height())
        painter.setClipRect(QRectF(2, 2, w - 4, h - 4).toAlignedRect())
        if self._anim_mode == 'world_tree':
            cols = 6
            col_w = w / cols
            trail_h = h * 0.55
            cycle = h + trail_h
            speed = h * 0.9
            for c in range(cols):
                cx = c * col_w + 2
                head_y = (cycle - (self._phase * speed + c * h * 0.18)) % cycle
                for i in range(15):
                    y = head_y - i * 5.5
                    if y < 0:
                        y += cycle
                    if 0 <= y < h:
                        alpha = max(0, 160 - i * 13)
                        painter.fillRect(QRectF(cx, y, col_w - 3, 2.2), QColor(168, 85, 247, alpha))
                for i in range(4):
                    y = head_y + i * 3.5
                    if y >= cycle:
                        y -= cycle
                    if 0 <= y < h:
                        alpha = 180 - i * 45
                        painter.fillRect(QRectF(cx, y, col_w - 3, 2.2), QColor(192, 132, 252, alpha))
        elif self._anim_mode == 'legend':
            sweep_x = self._phase * 1.04 * w % (w * 1.4) - w * 0.2
            grad = QLinearGradient(sweep_x, 0, sweep_x + w * 0.35, 0)
            grad.setColorAt(0, QColor(125, 211, 252, 0))
            grad.setColorAt(0.5, QColor(125, 211, 252, 50))
            grad.setColorAt(1, QColor(125, 211, 252, 0))
            painter.fillRect(QRectF(0, 0, w, h), grad)
        painter.end()
_anim_phase = 0.0
class _PassiveSkillDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        rank = index.data(Qt.UserRole + 1)
        if rank is None:
            super().paint(painter, option, index)
            painter.restore()
            return
        tc = index.data(Qt.UserRole + 3) or '#FFFFFF'
        bd = index.data(Qt.UserRole + 4) or '#FFFFFFFF'
        border = QColor(bd)
        text_color = QColor(tc)
        selected = option.state & QStyle.State_Selected
        if selected:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(59, 142, 208, 89)))
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
        else:
            fill = QColor(bd)
            color_a = fill.darker(250)
            color_a.setAlpha(min(255, fill.alpha()))
            color_b = QColor(fill.red(), fill.green(), fill.blue(), min(255, fill.alpha() + 60))
            grad = QLinearGradient(rect.x(), 0, rect.x() + rect.width(), 0)
            grad.setColorAt(0, color_a)
            grad.setColorAt(0.5, color_b)
            grad.setColorAt(1, color_a)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
            border_pen = QPen(border)
            border_pen.setWidthF(1.5)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(rect).adjusted(1, 2, -1, -2), 4, 4)
            if rank >= 4:
                is_wt = index.data(Qt.UserRole + 2)
                if is_wt:
                    self._paint_world_tree(painter, rect)
                else:
                    self._paint_legend_sweep(painter, rect)
        painter.setPen(QPen(text_color))
        text_rect = QRectF(rect.x() + 8, rect.y(), rect.width() - 12, rect.height())
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, index.data(Qt.DisplayRole))
        painter.restore()
    def _paint_legend_sweep(self, painter, rect):
        w = rect.width()
        ph = _anim_phase * 1.04 * w % (w * 1.4) - w * 0.2
        sweep = QLinearGradient(rect.x() + ph, 0, rect.x() + ph + w * 0.35, 0)
        sweep.setColorAt(0, QColor(125, 211, 252, 0))
        sweep.setColorAt(0.5, QColor(125, 211, 252, 40))
        sweep.setColorAt(1, QColor(125, 211, 252, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sweep))
        painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
    def _paint_world_tree(self, painter, rect):
        w, h = (rect.width(), rect.height())
        cols = 9
        col_w = w / cols
        trail_h = h * 0.55
        cycle = h + trail_h
        speed = h * 0.7
        for c in range(cols):
            cx = rect.x() + c * col_w + 1
            head_y = (cycle - (_anim_phase * speed + c * h * 0.12)) % cycle
            for i in range(6):
                y = head_y - i * 3.0
                if y < 0:
                    y += cycle
                yy = rect.y() + y
                if rect.y() <= yy < rect.y() + h:
                    alpha = max(0, 140 - i * 25)
                    painter.fillRect(QRectF(cx, yy, col_w - 2, 1.5), QColor(168, 85, 247, alpha))
            for i in range(2):
                y = head_y + i * 2.5
                if y >= cycle:
                    y -= cycle
                yy = rect.y() + y
                if rect.y() <= yy < rect.y() + h:
                    alpha = 160 - i * 80
                    painter.fillRect(QRectF(cx, yy, col_w - 2, 1.5), QColor(192, 132, 252, alpha))
    def sizeHint(self, option, index):
        return QSize(200, 28)
class PalInfoWidget(QFrame):
    _ELEMENT_MAP = {'Normal': ('⚪', '#9CA3AF'), 'Fire': ('🔥', '#EF4444'), 'Water': ('💧', '#3B82F6'), 'Leaf': ('🌿', '#4ADE80'), 'Grass': ('🌿', '#4ADE80'), 'Electricity': ('⚡', '#FBBF24'), 'Electric': ('⚡', '#FBBF24'), 'Ice': ('❄️', '#67E8F9'), 'Earth': ('🪨', '#A78BFA'), 'Ground': ('🪨', '#A78BFA'), 'Dark': ('🌑', '#6B21A8'), 'Dragon': ('🐉', '#818CF8')}
    _ELEMENT_COLORS = {'Normal': '#9CA3AF', 'Fire': '#EF4444', 'Water': '#3B82F6', 'Leaf': '#4ADE80', 'Grass': '#4ADE80', 'Electricity': '#FBBF24', 'Electric': '#FBBF24', 'Ice': '#67E8F9', 'Earth': '#A78BFA', 'Ground': '#A78BFA', 'Dark': '#6B21A8', 'Dragon': '#818CF8'}
    NATIVE_WORK_ORDER = ('EmitFlame', 'Watering', 'Seeding', 'GenerateElectricity', 'Handcraft', 'Collection', 'Deforest', 'Mining', 'ProductMedicine', 'Cool', 'Transport', 'MonsterFarm')
    _WORK_SUITABILITY_DISPLAY = {'EmitFlame': 'Kindling', 'Watering': 'Watering', 'Seeding': 'Seeding', 'GenerateElectricity': 'Electricity', 'Handcraft': 'Handiwork', 'Collection': 'Harvesting', 'Deforest': 'Lumbering', 'Mining': 'Mining', 'ProductMedicine': 'Medicine', 'Cool': 'Cooling', 'Transport': 'Transport', 'MonsterFarm': 'Farming'}
    _WORK_SUITABILITY_ICON_KEYS = ['palwork_00', 'palwork_01', 'palwork_02', 'palwork_03', 'palwork_04', 'palwork_05', 'palwork_06', 'palwork_07', 'palwork_08', 'palwork_10', 'palwork_11', 'palwork_12']
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pal = None
        self.last_clicked_data = None
        self._hovered_data = None
        self.setObjectName('palInfoPanel')
        self._raw = None
        self._build()
        self.installEventFilter(self)
    def set_hover_pal(self, pal_data):
        self._hovered_data = pal_data
        if pal_data is None:
            self._update_stack_state()
            self._clear_display()
            return
        self._update_stack_state()
        self._update_display(pal_data)
    def set_clicked_pal(self, pal_data):
        self.last_clicked_data = pal_data
        if pal_data is None:
            self._update_stack_state()
            self._clear_display()
            return
        self._update_stack_state()
        self._update_display(pal_data)
    def clear_hover(self):
        self._hovered_data = None
        if self.last_clicked_data is not None:
            self._update_display(self.last_clicked_data)
            return
        self._update_stack_state()
        self._clear_display()
    def _update_stack_state(self):
        if self._hovered_data is None and self.last_clicked_data is None:
            self._no_data_overlay.show()
            self._data_scroll.hide()
        else:
            self._no_data_overlay.hide()
            self._data_scroll.show()
    def _clear_display(self):
        self.name_lbl.setText('--')
        self.level_num_lbl.setText('--')
        self.next_lbl.setText('0')
        self.exp_header_bar.setValue(0)
        self.trust_bar.setValue(0)
        self.trust_bar.setFormat('-- / --')
        self.hp_bar.setValue(0)
        self.hp_bar.setFormat('--')
        self.hunger_bar.setValue(0)
        self.hunger_bar.setFormat('-- / --')
        self.san_bar.setValue(0)
        self.san_bar.setFormat('-- / --')
        self.atk_lbl.setText('--')
        self.def_lbl.setText('--')
        self.wspd_lbl.setText('--')
        for icon_lbl, (val_lbl, _, val_badge) in zip(self.work_icon_labels, self.work_icon_values):
            icon_lbl.setStyleSheet('background: transparent; border: none;')
            eff = icon_lbl.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                eff.setOpacity(0.06)
            val_lbl.setText('')
            val_lbl.setStyleSheet('font-size: 8px; font-weight: 700; color: transparent; background: transparent; border: none;')
            val_badge.setStyleSheet('background: transparent; border: none;')
        gender_def = _get_ui_icon_pixmap('gender_female', 18)
        if gender_def:
            self.gender_icon.setIcon(QIcon(gender_def))
        self.gender_icon.setStyleSheet('QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; } QPushButton:hover { background: rgba(255,255,255,0.08); }')
        while self.type_icons_layout.count():
            item = self.type_icons_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        for fc in self.food_icon_labels:
            fc.setStyleSheet('background: transparent; border: none;')
            foff = _get_ui_icon_pixmap('food_off', 12)
            if foff:
                fc.setPixmap(foff)
            eff = fc.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                eff.setOpacity(0.14)
        self.partner_name_lbl.setText('--')
        self.partner_lvl_lbl.setText('Lv --')
        self.partner_desc_lbl.setText('Select a pal to view details')
        while self.active_skills_list.count():
            item = self.active_skills_list.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        for s in self.passive_slots:
            s.setText('--')
            s.setStyleSheet('font-size: 9px; font-weight: 700; color: rgba(255,255,255,0.3); background: transparent; border: none;')
            parent_frame = s.parentWidget()
            if parent_frame and parent_frame.objectName() == 'passiveCard':
                parent_frame.setStyleSheet('QFrame#passiveCard { background: rgba(255,255,255,0.03); border: none; border-radius: 4px; }')
        for i in range(len(self.passive_cards)):
            self._set_passive_overlay(i, None)
        self.stat_plus_lbl.setText('--')
        self.soul_buildup_icon.clear()
        self.iv_icon.clear()
        self.soul_row_icon.clear()
        self._stop_star_shine()
        for sl in self.star_labels:
            sl.set_filled(False)
            sl.stop_shine()
        self.portrait_icon.clear()
        self.dna_overlay.hide()
        self.lock_overlay.hide()
        self.boss_overlay.hide()
        self.lucky_overlay.hide()
        self.awake_overlay.hide()
        self.portrait_ring.set_awakened(False)
        self._update_stack_state()
    def _set_passive_overlay(self, index, mode):
        if index >= len(self.passive_cards) or index >= len(self.passive_overlays):
            return
        card = self.passive_cards[index]
        overlay = self.passive_overlays[index]
        overlay.setGeometry(0, 0, card.width(), card.height())
        overlay.set_mode(mode)
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        scroll = QScrollArea()
        self._data_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 4px; background: rgba(255,255,255,0.02); border-radius: 2px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.15); border-radius: 2px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.3); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }')
        inner = QWidget()
        inner.setObjectName('palInfoInner')
        inner.setStyleSheet('QWidget#palInfoInner { background: rgba(8,10,16,0.98); border: 1px solid rgba(30,40,55,0.9); border-radius: 6px; }')
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 2, 4, 2)
        inner_layout.setSpacing(0)
        self._build_header(inner_layout)
        self._build_body(inner_layout)
        self._build_skills(inner_layout)
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        self._no_data_overlay = QLabel(t('pal_editor.no_pal_data') if t else 'No Pal Data', self)
        self._no_data_overlay.setAlignment(Qt.AlignCenter)
        self._no_data_overlay.setStyleSheet('font-size: 16px; font-weight: 700; color: rgba(255,255,255,0.18); background: rgba(8,10,16,0.98); border: 1px solid rgba(30,40,55,0.9); border-radius: 6px;')
        self._no_data_overlay.show()
        scroll.hide()
        self._c_shortcut = QShortcut(QKeySequence(Qt.Key_C), self)
        self._c_shortcut.activated.connect(self._toggle_skills_view)
        self._showing_active_skills = True
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_no_data_overlay'):
            self._no_data_overlay.setGeometry(self.rect())
    def _toggle_skills_view(self):
        self._showing_active_skills = not self._showing_active_skills
        self.active_skills_frame.setVisible(self._showing_active_skills)
        self.partner_frame.setVisible(not self._showing_active_skills)
    def _build_header(self, parent):
        header = QWidget()
        header.setStyleSheet('background: transparent; border: none;')
        hrow = QHBoxLayout()
        hrow.setContentsMargins(0, 0, 0, 0)
        hrow.setSpacing(2)
        hrow.setAlignment(Qt.AlignLeft)
        level_box = CornerBracketWidget('#7DD3FC')
        lv_layout = QVBoxLayout(level_box)
        lv_layout.setContentsMargins(2, 2, 2, 2)
        lv_layout.setSpacing(0)
        lv_label = QLabel(t('pal_editor.level') if t else 'LEVEL')
        self._lv_label = lv_label
        lv_label.setAlignment(Qt.AlignCenter)
        lv_label.setStyleSheet('font-size: 6px; font-weight: 600; color: #7DD3FC; letter-spacing: 2px; background: transparent; border: none;')
        lv_layout.addWidget(lv_label)
        self.level_num_lbl = QLabel('80')
        self.level_num_lbl.setAlignment(Qt.AlignCenter)
        self.level_num_lbl.setStyleSheet('font-size: 20px; font-weight: 800; color: #FFFFFF; background: transparent; border: none;')
        self.level_num_lbl.setCursor(Qt.PointingHandCursor)
        self.level_num_lbl.installEventFilter(self)
        lv_layout.addWidget(self.level_num_lbl)
        hrow.addWidget(level_box, 0, Qt.AlignTop)
        name_col = QWidget()
        name_col.setStyleSheet('background: transparent; border: none;')
        name_col.setMinimumWidth(180)
        name_col.setMaximumWidth(350)
        nc_layout = QVBoxLayout(name_col)
        nc_layout.setContentsMargins(0, 0, 0, 0)
        nc_layout.setSpacing(0)
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(4)
        self.name_lbl = QLabel('Gobfinned')
        self.name_lbl.setStyleSheet('font-size: 14px; font-weight: 700; color: #FFFFFF; background: transparent; border: none;')
        self.name_lbl.setCursor(Qt.PointingHandCursor)
        self.name_lbl.setWordWrap(True)
        self.name_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.name_lbl.installEventFilter(self)
        name_row.addWidget(self.name_lbl, 1)
        self.type_icons_container = QWidget()
        self.type_icons_container.setStyleSheet('background: transparent; border: none;')
        self.type_icons_layout = QHBoxLayout(self.type_icons_container)
        self.type_icons_layout.setContentsMargins(0, 0, 0, 0)
        self.type_icons_layout.setSpacing(2)
        self.type_icons_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        name_row.addWidget(self.type_icons_container)
        nc_layout.addLayout(name_row)
        nc_layout.addStretch()
        next_row = QHBoxLayout()
        next_row.setContentsMargins(0, 0, 0, 0)
        next_row.setSpacing(3)
        next_label = QLabel('NEXT')
        next_label.setStyleSheet('font-size: 8px; font-weight: 600; color: #9CA3AF; background: transparent; border: none;')
        next_row.addWidget(next_label)
        self.next_lbl = QLabel('0')
        self.next_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
        next_row.addWidget(self.next_lbl)
        next_row.addStretch()
        self.gender_icon = QPushButton()
        self.gender_icon.setFixedSize(18, 18)
        self.gender_icon.setIconSize(QSize(14, 14))
        gender_def = _get_ui_icon_pixmap('gender_female', 14)
        if gender_def:
            self.gender_icon.setIcon(QIcon(gender_def))
        self.gender_icon.setStyleSheet('QPushButton { background: transparent; border: none; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 3px; }')
        self.gender_icon.setCursor(Qt.PointingHandCursor)
        self.gender_icon.clicked.connect(self._on_gender_click)
        next_row.addWidget(self.gender_icon)
        base_dir = constants.get_base_path()
        self.info_boss_btn = QPushButton()
        self.info_boss_btn.setIcon(QIcon(os.path.join(base_dir, 'resources', 'boss_alpha.webp')))
        self.info_boss_btn.setIconSize(QSize(14, 14))
        self.info_boss_btn.setCheckable(True)
        self.info_boss_btn.setFixedSize(18, 18)
        self.info_boss_btn.setStyleSheet('QPushButton { background: transparent; border: none; } QPushButton:checked { background: rgba(245,158,11,0.2); border: 1px solid #F59E0B; border-radius: 3px; } QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 3px; }')
        self.info_boss_btn.setCursor(Qt.PointingHandCursor)
        self.info_boss_btn.clicked.connect(self._on_boss_toggle)
        next_row.addWidget(self.info_boss_btn)
        self.info_lucky_btn = QPushButton()
        self.info_lucky_btn.setIcon(QIcon(os.path.join(base_dir, 'resources', 'boss_shiny.webp')))
        self.info_lucky_btn.setIconSize(QSize(14, 14))
        self.info_lucky_btn.setCheckable(True)
        self.info_lucky_btn.setFixedSize(18, 18)
        self.info_lucky_btn.setStyleSheet('QPushButton { background: transparent; border: none; } QPushButton:checked { background: rgba(168,85,247,0.2); border: 1px solid #A855F7; border-radius: 3px; } QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 3px; }')
        self.info_lucky_btn.setCursor(Qt.PointingHandCursor)
        self.info_lucky_btn.clicked.connect(self._on_lucky_toggle)
        next_row.addWidget(self.info_lucky_btn)
        self.info_awake_btn = QPushButton()
        self.info_awake_btn.setCheckable(True)
        self.info_awake_btn.setFixedSize(18, 18)
        self.info_awake_btn.setIconSize(QSize(14, 14))
        awake_icon = _get_awake_pixmap(14)
        if awake_icon:
            self.info_awake_btn.setIcon(QIcon(awake_icon))
        else:
            self.info_awake_btn.setText('🔥')
        self.info_awake_btn.setStyleSheet('QPushButton { background: transparent; border: none; font-size: 10px; } QPushButton:checked { background: rgba(251,191,36,0.2); border: 1px solid #FBBF24; border-radius: 3px; } QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 3px; }')
        self.info_awake_btn.setCursor(Qt.PointingHandCursor)
        self.info_awake_btn.clicked.connect(self._on_awake_toggle)
        next_row.addWidget(self.info_awake_btn)
        self.info_max_btn = NerdBtn(nf.icons['nf-md-database_arrow_up'])
        self.info_max_btn.setFixedSize(18, 18)
        self.info_max_btn.setStyleSheet('QPushButton { font-size: 12px; padding: 0px; margin: 0px; background: transparent; color: #4ADE80; border: none; } QPushButton:hover { background: rgba(74,222,128,0.15); color: #FFFFFF; border-radius: 3px; }')
        self.info_max_btn.setCursor(Qt.PointingHandCursor)
        self.info_max_btn.clicked.connect(self._on_max_click)
        next_row.addWidget(self.info_max_btn)
        self.info_dna_btn = QPushButton()
        self.info_dna_btn.setCheckable(True)
        self.info_dna_btn.setFixedSize(18, 18)
        self.info_dna_btn.setIconSize(QSize(14, 14))
        dna_icon = _get_ui_icon_pixmap('dna', 14)
        if dna_icon:
            self.info_dna_btn.setIcon(QIcon(dna_icon))
        self.info_dna_btn.setStyleSheet('QPushButton { background: transparent; border: none; } QPushButton:checked { background: rgba(34,211,238,0.2); border: 1px solid #22D3EE; border-radius: 3px; } QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 3px; }')
        self.info_dna_btn.setCursor(Qt.PointingHandCursor)
        self.info_dna_btn.clicked.connect(self._on_dna_toggle)
        next_row.addWidget(self.info_dna_btn)
        self.info_fav_btn = QPushButton()
        self.info_fav_btn.setFixedSize(18, 18)
        self.info_fav_btn.setIconSize(QSize(14, 14))
        self.info_fav_btn.setStyleSheet('QPushButton { background: transparent; border: none; } QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 3px; }')
        self.info_fav_btn.setCursor(Qt.PointingHandCursor)
        self.info_fav_btn.clicked.connect(self._on_fav_toggle)
        next_row.addWidget(self.info_fav_btn)
        nc_layout.addLayout(next_row)
        hrow.addWidget(name_col, 0, Qt.AlignTop)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(1)
        header_layout.addLayout(hrow)
        self.exp_header_bar = QProgressBar()
        self.exp_header_bar.setFixedHeight(3)
        self.exp_header_bar.setRange(0, 100)
        self.exp_header_bar.setValue(0)
        self.exp_header_bar.setTextVisible(False)
        self.exp_header_bar.setStyleSheet('QProgressBar { background: rgba(40,30,40,0.4); border: none; border-radius: 1px; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #EC4899,stop:1 #F472B6); border-radius: 1px; }')
        header_layout.addWidget(self.exp_header_bar)
        parent.addWidget(header)

    def _on_portrait_context_menu(self, pos):
        if not self._raw:
            return
        menu, actions = build_pal_context_menu(self, self._raw)
        fav_action, lock_actions = actions['fav']
        for i, sub_a in enumerate(lock_actions):
            sub_a.triggered.connect(partial(self._on_fav_set, i))
        action = menu.exec(self.bracket_wrapper.mapToGlobal(pos))
        if action == actions['boss']:
            self._on_boss_toggle()
        elif action == actions['lucky']:
            self._on_lucky_toggle()
        elif action == actions['awake']:
            self._on_awake_toggle()
        elif action == actions['dna']:
            self._on_dna_toggle()
        elif action == actions['max']:
            self._on_max_click()
        elif action == actions['learn']:
            try:
                self._learn_all_skills()
                show_information(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_success'))
            except Exception:
                show_warning(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_fail'))
        elif action == actions['delete']:
            pass

    def _on_fav_set(self, idx):
        if not self._raw:
            return
        self._raw['FavoriteIndex'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': idx}}
        self._refresh()

    def _build_body(self, parent):
        body = QWidget()
        body.setStyleSheet('background: transparent; border: none;')
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(2)

        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(4)

        left_col = QWidget()
        left_col.setStyleSheet('background: transparent; border: none;')
        left_col.setFixedWidth(110)
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)

        self.star_container = QWidget()
        self.star_container.setCursor(Qt.PointingHandCursor)
        self.star_container.installEventFilter(self)
        star_layout = QHBoxLayout(self.star_container)
        star_layout.setContentsMargins(0, 0, 0, 0)
        star_layout.setSpacing(1)
        star_layout.setAlignment(Qt.AlignCenter)
        self.star_labels = []
        for i in range(4):
            sl = _ShinyStar()
            self.star_labels.append(sl)
            star_layout.addWidget(sl)
        self._star_shine_timer = QTimer(self)
        self._star_shine_timer.timeout.connect(self._tick_star_shine)
        self._star_shine_phase = 0.0
        left_layout.addWidget(self.star_container)

        portrait_frame = QFrame()
        self.portrait_frame = portrait_frame
        portrait_frame.setFixedSize(88, 88)
        portrait_frame.setObjectName('portraitGlow')
        portrait_frame.setStyleSheet('QFrame#portraitGlow { background: qradialgradient(cx:0.5,cy:0.5,radius:0.6,fx:0.5,fy:0.5,stop:0 rgba(125,211,252,0.12),stop:0.4 rgba(125,211,252,0.04),stop:1 transparent); border: none; border-radius: 44px; }')
        portrait_frame.setContextMenuPolicy(Qt.CustomContextMenu)
        portrait_frame.customContextMenuRequested.connect(self._on_portrait_context_menu)
        pf_layout = QVBoxLayout(portrait_frame)
        pf_layout.setContentsMargins(2, 2, 2, 2)
        pf_layout.setAlignment(Qt.AlignCenter)
        self.bracket_wrapper = PortraitBracketWidget()
        self.bracket_wrapper.setFixedSize(80, 80)
        bw_layout = QVBoxLayout(self.bracket_wrapper)
        bw_layout.setContentsMargins(2, 2, 2, 2)
        bw_layout.setAlignment(Qt.AlignCenter)
        self.portrait_ring = GlowRing()
        self.portrait_ring.setFixedSize(72, 72)
        ring_layout = QVBoxLayout(self.portrait_ring)
        ring_layout.setContentsMargins(0, 0, 0, 0)
        self.portrait_icon = _CircularIcon(68)
        ring_layout.addWidget(self.portrait_icon, 0, Qt.AlignCenter)
        bw_layout.addWidget(self.portrait_ring, 0, Qt.AlignCenter)
        self.dna_overlay = QLabel(self.bracket_wrapper)
        self.dna_overlay.setFixedSize(14, 14)
        self.dna_overlay.setAlignment(Qt.AlignCenter)
        self.dna_overlay.setAttribute(Qt.WA_TranslucentBackground)
        dna_pix = _get_ui_icon_pixmap('dna', 12)
        if dna_pix:
            self.dna_overlay.setPixmap(dna_pix)
        self.dna_overlay.setStyleSheet('background: transparent; border: none;')
        self.dna_overlay.move(4, 62)
        self.dna_overlay.hide()
        self.lock_overlay = QLabel(self.bracket_wrapper)
        self.lock_overlay.setFixedSize(14, 14)
        self.lock_overlay.setAlignment(Qt.AlignCenter)
        self.lock_overlay.setStyleSheet('font-size: 9px; color: rgba(255,255,255,0.65); background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 7px;')
        self.lock_overlay.setText('\U0001F512')
        self.lock_overlay.move(62, 4)
        self.lock_overlay.hide()
        self.boss_overlay = QLabel(self.bracket_wrapper)
        self.boss_overlay.setFixedSize(14, 14)
        self.boss_overlay.setAlignment(Qt.AlignCenter)
        self.boss_overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.boss_overlay.setStyleSheet('background: transparent; border: none;')
        self.boss_overlay.move(4, 4)
        self.boss_overlay.hide()
        self.lucky_overlay = QLabel(self.bracket_wrapper)
        self.lucky_overlay.setFixedSize(14, 14)
        self.lucky_overlay.setAlignment(Qt.AlignCenter)
        self.lucky_overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.lucky_overlay.setStyleSheet('background: transparent; border: none;')
        self.lucky_overlay.move(4, 4)
        self.lucky_overlay.hide()
        self.awake_overlay = QLabel(self.bracket_wrapper)
        self.awake_overlay.setFixedSize(14, 14)
        self.awake_overlay.setAlignment(Qt.AlignCenter)
        self.awake_overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.awake_overlay.setStyleSheet('background: transparent; border: none;')
        awake_overlay_pix = _get_awake_pixmap(12)
        if awake_overlay_pix:
            self.awake_overlay.setPixmap(awake_overlay_pix)
        else:
            self.awake_overlay.setStyleSheet('font-size: 10px; background: transparent; border: none;')
            self.awake_overlay.setText('\U0001F525')
        self.awake_overlay.move(62, 62)
        self.awake_overlay.hide()
        self.rotating_circle = RotatingCircleWidget(self.bracket_wrapper)
        self.rotating_circle.setFixedSize(80, 80)
        self.rotating_circle.move(0, 0)
        self.rotating_circle.show()
        self.rotating_circle.lower()
        pf_layout.addWidget(self.bracket_wrapper, 0, Qt.AlignCenter)
        left_layout.addWidget(portrait_frame, 0, Qt.AlignCenter)

        soul_row = QHBoxLayout()
        soul_row.setContentsMargins(0, 0, 0, 0)
        soul_row.setSpacing(2)
        soul_row.setAlignment(Qt.AlignCenter)
        self.soul_buildup_icon = QLabel()
        self.soul_buildup_icon.setFixedSize(12, 12)
        self.soul_buildup_icon.setStyleSheet('background: transparent; border: none;')
        buildup_pix = _get_ui_icon_pixmap('buildup', 12)
        if buildup_pix:
            self.soul_buildup_icon.setPixmap(buildup_pix)
        soul_row.addWidget(self.soul_buildup_icon)
        self.stat_plus_lbl = QLabel('+60')
        self.stat_plus_lbl.setAlignment(Qt.AlignCenter)
        self.stat_plus_lbl.setStyleSheet('font-size: 11px; font-weight: 700; color: #7DD3FC; background: transparent; border: none;')
        self.stat_plus_lbl.setCursor(Qt.PointingHandCursor)
        self.stat_plus_lbl.installEventFilter(self)
        soul_row.addWidget(self.stat_plus_lbl)
        left_layout.addLayout(soul_row, 1)

        ivs_row = QHBoxLayout()
        ivs_row.setSpacing(4)
        self.iv_icon = QLabel()
        self.iv_icon.setFixedSize(12, 12)
        self.iv_icon.setStyleSheet('background: transparent; border: none;')
        iv_pix = _get_ui_icon_pixmap('talent_checker', 12)
        if iv_pix:
            self.iv_icon.setPixmap(iv_pix)
        ivs_row.addWidget(self.iv_icon)
        self.ivs_hp_lbl = QLabel('100')
        self.ivs_hp_lbl.setFixedWidth(24)
        self.ivs_hp_lbl.setAlignment(Qt.AlignCenter)
        self.ivs_hp_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.ivs_hp_lbl.setCursor(Qt.PointingHandCursor)
        self.ivs_hp_lbl.installEventFilter(self)
        ivs_row.addWidget(self.ivs_hp_lbl)
        self.ivs_atk_lbl = QLabel('100')
        self.ivs_atk_lbl.setFixedWidth(24)
        self.ivs_atk_lbl.setAlignment(Qt.AlignCenter)
        self.ivs_atk_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.ivs_atk_lbl.setCursor(Qt.PointingHandCursor)
        self.ivs_atk_lbl.installEventFilter(self)
        ivs_row.addWidget(self.ivs_atk_lbl)
        self.ivs_def_lbl = QLabel('100')
        self.ivs_def_lbl.setFixedWidth(24)
        self.ivs_def_lbl.setAlignment(Qt.AlignCenter)
        self.ivs_def_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.ivs_def_lbl.setCursor(Qt.PointingHandCursor)
        self.ivs_def_lbl.installEventFilter(self)
        ivs_row.addWidget(self.ivs_def_lbl)
        ivs_row.addStretch()
        left_layout.addLayout(ivs_row, 1)

        souls_row = QHBoxLayout()
        souls_row.setSpacing(4)
        self.soul_row_icon = QLabel()
        self.soul_row_icon.setFixedSize(12, 12)
        self.soul_row_icon.setStyleSheet('background: transparent; border: none;')
        srp = _get_ui_icon_pixmap('buildup', 12)
        if srp:
            self.soul_row_icon.setPixmap(srp)
        souls_row.addWidget(self.soul_row_icon)
        self.soul_hp_lbl = QLabel('0')
        self.soul_hp_lbl.setFixedWidth(22)
        self.soul_hp_lbl.setAlignment(Qt.AlignCenter)
        self.soul_hp_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.soul_hp_lbl.setCursor(Qt.PointingHandCursor)
        self.soul_hp_lbl.installEventFilter(self)
        souls_row.addWidget(self.soul_hp_lbl)
        self.soul_atk_lbl = QLabel('0')
        self.soul_atk_lbl.setFixedWidth(22)
        self.soul_atk_lbl.setAlignment(Qt.AlignCenter)
        self.soul_atk_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.soul_atk_lbl.setCursor(Qt.PointingHandCursor)
        self.soul_atk_lbl.installEventFilter(self)
        souls_row.addWidget(self.soul_atk_lbl)
        self.soul_def_lbl = QLabel('0')
        self.soul_def_lbl.setFixedWidth(22)
        self.soul_def_lbl.setAlignment(Qt.AlignCenter)
        self.soul_def_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.soul_def_lbl.setCursor(Qt.PointingHandCursor)
        self.soul_def_lbl.installEventFilter(self)
        souls_row.addWidget(self.soul_def_lbl)
        self.soul_craft_lbl = QLabel('0')
        self.soul_craft_lbl.setFixedWidth(22)
        self.soul_craft_lbl.setAlignment(Qt.AlignCenter)
        self.soul_craft_lbl.setStyleSheet('font-size: 8px; font-weight: 600; color: #FFFFFF; background: transparent; border: none; padding: 1px 0px;')
        self.soul_craft_lbl.setCursor(Qt.PointingHandCursor)
        self.soul_craft_lbl.installEventFilter(self)
        souls_row.addWidget(self.soul_craft_lbl)
        souls_row.addStretch()
        left_layout.addLayout(souls_row, 1)

        columns.addWidget(left_col)

        right_col = QWidget()
        right_col.setStyleSheet('background: transparent; border: none;')
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(1)

        trust_row = QHBoxLayout()
        trust_row.setSpacing(0)
        trust_icon = QLabel()
        trust_icon.setFixedSize(14, 14)
        trust_icon.setAlignment(Qt.AlignCenter)
        trust_icon.setAttribute(Qt.WA_TranslucentBackground)
        trust_icon.setStyleSheet('background: transparent; border: none;')
        trust_pix = _get_ui_icon_pixmap('friendship', 10)
        if trust_pix:
            trust_icon.setPixmap(trust_pix)
        trust_row.addWidget(trust_icon)
        self.trust_bar = QProgressBar()
        self.trust_bar.setFixedHeight(18)
        self.trust_bar.setRange(0, 100)
        self.trust_bar.setValue(0)
        self.trust_bar.setTextVisible(True)
        self.trust_bar.setStyleSheet('QProgressBar { background: rgba(30,20,25,0.6); border: 1px solid rgba(244,114,182,0.20); border-radius: 2px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #EC4899,stop:1 #F472B6); border-radius: 2px; }')
        trust_row.addWidget(self.trust_bar, 1)
        right_layout.addLayout(trust_row, 1)

        hp_row = QHBoxLayout()
        hp_row.setSpacing(0)
        hp_icon = QLabel('\u2665')
        hp_icon.setFixedSize(14, 14)
        hp_icon.setAlignment(Qt.AlignCenter)
        hp_icon.setStyleSheet('font-size: 8px; color: #EF4444; background: transparent; border: none;')
        hp_row.addWidget(hp_icon)
        self.hp_bar = QProgressBar()
        self.hp_bar.setFixedHeight(18)
        self.hp_bar.setRange(0, 100)
        self.hp_bar.setValue(100)
        self.hp_bar.setTextVisible(True)
        self.hp_bar.setStyleSheet('QProgressBar { background: rgba(20,40,30,0.6); border: 1px solid rgba(16,185,129,0.2); border-radius: 2px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 2px; }')
        hp_row.addWidget(self.hp_bar, 1)
        right_layout.addLayout(hp_row, 1)

        hunger_row = QHBoxLayout()
        hunger_row.setSpacing(0)
        hunger_icon = QLabel('\u26AC')
        hunger_icon.setFixedSize(14, 14)
        hunger_icon.setAlignment(Qt.AlignCenter)
        hunger_icon.setStyleSheet('font-size: 8px; color: #F59E0B; background: transparent; border: none;')
        hunger_row.addWidget(hunger_icon)
        self.hunger_bar = QProgressBar()
        self.hunger_bar.setFixedHeight(18)
        self.hunger_bar.setRange(0, 100)
        self.hunger_bar.setValue(53)
        self.hunger_bar.setTextVisible(True)
        self.hunger_bar.setStyleSheet('QProgressBar { background: rgba(40,30,20,0.6); border: 1px solid rgba(245,158,11,0.2); border-radius: 2px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #F59E0B,stop:1 #FBBF24); border-radius: 2px; }')
        hunger_row.addWidget(self.hunger_bar, 1)
        right_layout.addLayout(hunger_row, 1)

        san_row = QHBoxLayout()
        san_row.setSpacing(0)
        san_icon = QLabel('\u2726')
        san_icon.setFixedSize(14, 14)
        san_icon.setAlignment(Qt.AlignCenter)
        san_icon.setStyleSheet('font-size: 8px; color: #10B981; background: transparent; border: none;')
        san_row.addWidget(san_icon)
        self.san_bar = QProgressBar()
        self.san_bar.setFixedHeight(18)
        self.san_bar.setRange(0, 100)
        self.san_bar.setValue(100)
        self.san_bar.setTextVisible(True)
        self.san_bar.setStyleSheet('QProgressBar { background: rgba(20,30,40,0.6); border: 1px solid rgba(56,189,248,0.2); border-radius: 2px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #38BDF8,stop:1 #7DD3FC); border-radius: 2px; }')
        san_row.addWidget(self.san_bar, 1)
        right_layout.addLayout(san_row, 1)

        stats_q = QFrame()
        stats_q.setStyleSheet('background: transparent; border: none;')
        stats_grid = QGridLayout(stats_q)
        stats_grid.setContentsMargins(4, 1, 4, 1)
        stats_grid.setSpacing(2)
        atk_icon = QLabel('\u2694')
        atk_icon.setFixedSize(14, 14)
        atk_icon.setAlignment(Qt.AlignCenter)
        atk_icon.setStyleSheet('font-size: 9px; color: #EF4444; background: transparent; border: none;')
        stats_grid.addWidget(atk_icon, 0, 0, Qt.AlignVCenter)
        atk_label = QLabel(t('pal_editor.attack') if t else 'Attack')
        self._atk_label = atk_label
        atk_label.setStyleSheet('font-size: 9px; color: #9CA3AF; background: transparent; border: none;')
        stats_grid.addWidget(atk_label, 0, 1, Qt.AlignVCenter)
        self.atk_lbl = QLabel('3599')
        self.atk_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.atk_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        stats_grid.addWidget(self.atk_lbl, 0, 2, Qt.AlignVCenter)
        def_icon = QLabel('\u2696')
        def_icon.setFixedSize(14, 14)
        def_icon.setAlignment(Qt.AlignCenter)
        def_icon.setStyleSheet('font-size: 9px; color: #3B82F6; background: transparent; border: none;')
        stats_grid.addWidget(def_icon, 1, 0, Qt.AlignVCenter)
        def_label = QLabel(t('pal_editor.defense') if t else 'Defense')
        self._def_label = def_label
        def_label.setStyleSheet('font-size: 9px; color: #9CA3AF; background: transparent; border: none;')
        stats_grid.addWidget(def_label, 1, 1, Qt.AlignVCenter)
        self.def_lbl = QLabel('2791')
        self.def_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.def_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        stats_grid.addWidget(self.def_lbl, 1, 2, Qt.AlignVCenter)
        wspd_icon = QLabel('\u2692')
        wspd_icon.setFixedSize(14, 14)
        wspd_icon.setAlignment(Qt.AlignCenter)
        wspd_icon.setStyleSheet('font-size: 9px; color: #A78BFA; background: transparent; border: none;')
        stats_grid.addWidget(wspd_icon, 2, 0, Qt.AlignVCenter)
        wspd_label = QLabel(t('pal_editor.work_speed') if t else 'Work Speed')
        self._wspd_label = wspd_label
        wspd_label.setStyleSheet('font-size: 9px; color: #9CA3AF; background: transparent; border: none;')
        stats_grid.addWidget(wspd_label, 2, 1, Qt.AlignVCenter)
        self.wspd_lbl = QLabel('127')
        self.wspd_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.wspd_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        stats_grid.addWidget(self.wspd_lbl, 2, 2, Qt.AlignVCenter)
        right_layout.addWidget(stats_q)

        columns.addWidget(right_col, 1)
        body_layout.addLayout(columns)

        suit_card = QFrame()
        suit_card.setObjectName('suitFoodCard')
        suit_card.setStyleSheet('QFrame#suitFoodCard { background: rgba(255,255,255,0.02); border: 1px solid rgba(125,211,252,0.1); border-radius: 4px; }')
        card_layout = QVBoxLayout(suit_card)
        card_layout.setContentsMargins(4, 1, 4, 1)
        card_layout.setSpacing(1)
        self.work_icons_container = QWidget()
        self.work_icons_container.setObjectName('wsIcons')
        self.work_icons_container.setStyleSheet('background: transparent; border: none;')
        self.work_icons_layout = QHBoxLayout(self.work_icons_container)
        self.work_icons_layout.setContentsMargins(0, 0, 0, 0)
        self.work_icons_layout.setSpacing(2)
        self.work_icon_labels = []
        self.work_icon_values = []
        for idx, ws_key in enumerate(self.NATIVE_WORK_ORDER):
            wc = QWidget()
            wc.setObjectName('wsWidget')
            wc.setStyleSheet('background: transparent; border: none;')
            wc.setFixedWidth(24)
            vl = QVBoxLayout(wc)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(0)
            ic = QLabel()
            ic.setAlignment(Qt.AlignCenter)
            ic.setFixedSize(22, 22)
            ic.setAttribute(Qt.WA_TranslucentBackground)
            ic.setStyleSheet('background: transparent; border: none;')
            palwork_key = self._WORK_SUITABILITY_ICON_KEYS[idx]
            ws_pix = _get_ui_icon_pixmap(palwork_key, 18)
            if ws_pix:
                ic.setPixmap(ws_pix)
                opacity_effect = QGraphicsOpacityEffect()
                opacity_effect.setOpacity(0.06)
                ic.setGraphicsEffect(opacity_effect)
            vl.addWidget(ic, 0, Qt.AlignCenter)
            wl_badge = QFrame()
            wl_badge.setObjectName('wsBadge')
            wl_badge.setStyleSheet('background: transparent; border: none;')
            wl_badge.setFixedHeight(14)
            bd_layout = QVBoxLayout(wl_badge)
            bd_layout.setContentsMargins(2, 0, 2, 0)
            bd_layout.setAlignment(Qt.AlignCenter)
            wl = QLabel('')
            wl.setAlignment(Qt.AlignCenter)
            wl.setStyleSheet('font-size: 8px; font-weight: 700; color: transparent; background: transparent; border: none;')
            wl.setFixedHeight(10)
            bd_layout.addWidget(wl)
            vl.addWidget(wl_badge, 0, Qt.AlignCenter)
            self.work_icons_layout.addWidget(wc)
            self.work_icon_labels.append(ic)
            self.work_icon_values.append((wl, ws_key, wl_badge))
        self.work_icons_layout.addStretch()
        card_layout.addWidget(self.work_icons_container)
        food_row = QHBoxLayout()
        food_row.setSpacing(2)
        food_row.addStretch()
        self.food_icon_labels = []
        for i in range(10):
            fc = QLabel()
            fc.setFixedSize(14, 14)
            fc.setAlignment(Qt.AlignCenter)
            fc.setAttribute(Qt.WA_TranslucentBackground)
            fc.setStyleSheet('background: transparent; border: none;')
            food_off_pix = _get_ui_icon_pixmap('food_off', 12)
            if food_off_pix:
                fc.setPixmap(food_off_pix)
                opacity = QGraphicsOpacityEffect()
                opacity.setOpacity(0.14)
                fc.setGraphicsEffect(opacity)
            food_row.addWidget(fc)
            self.food_icon_labels.append(fc)
        card_layout.addLayout(food_row)
        body_layout.addWidget(suit_card)

        parent.addWidget(body, 1)

    def _build_skills(self, parent):
        skill_box = QFrame()
        skill_box.setObjectName('skillBox')
        skill_box.setStyleSheet('QFrame#skillBox { background: rgba(10,16,24,0.95); border: 1.5px solid rgba(125,211,252,0.3); border-radius: 5px; }')
        sb_layout = QVBoxLayout(skill_box)
        sb_layout.setContentsMargins(4, 2, 4, 2)
        sb_layout.setSpacing(3)

        self.partner_frame = QFrame()
        self.partner_frame.setObjectName('partnerBox')
        self.partner_frame.hide()
        self.partner_frame.setStyleSheet('QFrame#partnerBox { background: transparent; border: none; }')
        partner_layout = QVBoxLayout(self.partner_frame)
        partner_layout.setContentsMargins(0, 0, 0, 0)
        partner_layout.setSpacing(1)
        pheader = QHBoxLayout()
        pheader.setSpacing(4)
        self.partner_name_lbl = QLabel('Aerial Missile')
        self.partner_name_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #7DD3FC; background: transparent; border: none;')
        pheader.addWidget(self.partner_name_lbl)
        self.partner_lvl_lbl = QLabel('Lv 5')
        self.partner_lvl_lbl.setStyleSheet('font-size: 9px; font-weight: 600; color: #F59E0B; background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.15); border-radius: 3px; padding: 0 4px;')
        pheader.addWidget(self.partner_lvl_lbl)
        pheader.addStretch()
        c_icon = QLabel('[C]')
        c_icon.setFixedSize(22, 16)
        c_icon.setAlignment(Qt.AlignCenter)
        c_icon.setStyleSheet('font-size: 8px; font-weight: 700; color: #7DD3FC; background: rgba(125,211,252,0.08); border: 1px solid rgba(125,211,252,0.2); border-radius: 3px;')
        pheader.addWidget(c_icon)
        partner_layout.addLayout(pheader)
        self.partner_desc_lbl = QLabel('Fires a barrage of missiles at nearby enemies, dealing massive damage and knocking them back.')
        self.partner_desc_lbl.setWordWrap(True)
        self.partner_desc_lbl.setStyleSheet('font-size: 8px; color: #9CA3AF; background: transparent; border: none; padding: 0 2px;')
        partner_layout.addWidget(self.partner_desc_lbl)

        self.active_skills_frame = QFrame()
        self.active_skills_frame.setObjectName('activeSkillsBox')
        self.active_skills_frame.setStyleSheet('QFrame#activeSkillsBox { background: transparent; border: none; }')
        as_layout = QVBoxLayout(self.active_skills_frame)
        as_layout.setContentsMargins(0, 0, 0, 0)
        as_layout.setSpacing(2)
        as_header = QHBoxLayout()
        as_header.setSpacing(4)
        as_title = QLabel(t('pal_editor.active_skills') if t else 'Active Skills')
        self._as_title = as_title
        as_title.setStyleSheet('font-size: 9px; font-weight: 700; color: #7DD3FC; background: transparent; border: none;')
        as_header.addWidget(as_title)
        as_header.addStretch()
        as_c_icon = QLabel('[C]')
        as_c_icon.setFixedSize(22, 14)
        as_c_icon.setAlignment(Qt.AlignCenter)
        as_c_icon.setStyleSheet('font-size: 7px; font-weight: 700; color: #7DD3FC; background: rgba(125,211,252,0.08); border: 1px solid rgba(125,211,252,0.2); border-radius: 3px;')
        as_header.addWidget(as_c_icon)
        as_layout.addLayout(as_header)
        self.active_skills_list = QVBoxLayout()
        self.active_skills_list.setContentsMargins(0, 0, 0, 0)
        self.active_skills_list.setSpacing(2)
        as_layout.addLayout(self.active_skills_list)
        self.active_skills_frame.setFixedHeight(100)

        sb_layout.addWidget(self.active_skills_frame)
        self.partner_frame.setFixedHeight(100)
        sb_layout.addWidget(self.partner_frame)

        passive_title = QLabel(t('pal_editor.passive_skills') if t else 'Passive Skills')
        self._passive_title = passive_title
        passive_title.setStyleSheet('font-size: 9px; font-weight: 700; color: #7DD3FC; background: transparent; border: none;')
        sb_layout.addWidget(passive_title)

        pg = QWidget()
        pg.setStyleSheet('background: transparent; border: none;')
        pg_layout = QGridLayout(pg)
        pg_layout.setContentsMargins(0, 0, 0, 0)
        pg_layout.setSpacing(2)
        _, _, default_tc = PalFrame._RANK_COLORS[1]
        default_bg = PalFrame._RANK_COLORS[1][0]
        placeholder_names = ['Runner', 'Swift', 'Legend', 'Surge of the World Tree']
        self.passive_slots = []
        self.passive_cards = []
        for i, pname in enumerate(placeholder_names):
            card = QFrame()
            card.setObjectName('passiveCard')
            card._passive_index = i
            card._pal_info = self
            card.setFixedHeight(26)
            card.setStyleSheet(f'QFrame#passiveCard {{ background: {default_bg}; border: none; border-radius: 4px; }}')
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(6, 0, 6, 0)
            card_layout.setSpacing(2)
            card_layout.setAlignment(Qt.AlignVCenter)
            plbl = QLabel(pname)
            plbl.setStyleSheet(f'font-size: 9px; font-weight: 700; color: {default_tc}; background: transparent; border: none;')
            card_layout.addWidget(plbl, 1)
            chev = QLabel('❯❯❯')
            chev.setStyleSheet(f'font-size: 6px; color: rgba(255,255,255,0.15); background: transparent; border: none; letter-spacing: -1px;')
            card_layout.addWidget(chev)
            card.setCursor(Qt.PointingHandCursor)
            btn = QPushButton('', card)
            btn.setStyleSheet('QPushButton { background: transparent; border: none; }')
            btn.setCursor(Qt.PointingHandCursor)
            btn.setGeometry(0, 0, 100, 100)
            btn.clicked.connect(lambda checked=None, idx=i: self._on_passive_click(idx))
            row, col = (i // 2, i % 2)
            pg_layout.addWidget(card, row, col)
            self.passive_slots.append(plbl)
            self.passive_cards.append(card)
        self.passive_overlays = []
        for i, card in enumerate(self.passive_cards):
            overlay = PassiveEffectOverlay(card)
            self.passive_overlays.append(overlay)
        sb_layout.addWidget(pg)

        parent.addWidget(skill_box)
    def _update_display(self, pal_data):
        try:
            if 'data' in pal_data:
                raw = pal_data['data']
            elif 'value' in pal_data:
                raw = safe_nested_get(pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            else:
                raw = pal_data
            if not isinstance(raw, dict):
                return
            self._raw = raw
            _ensure_skill_data()
            _ensure_passive_data()
            cid = extract_value(raw, 'CharacterID', '')
            level = extract_value(raw, 'Level', 1)
            nick = extract_value(raw, 'NickName', '')
            pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
            if nick:
                full = nick
            else:
                full = pal_name
            self.name_lbl.setText(full)
            self.level_num_lbl.setText(str(level))
            gender_data = extract_value(raw, 'Gender', {})
            if isinstance(gender_data, dict) and 'value' in gender_data:
                gender = gender_data['value']
            elif isinstance(gender_data, str):
                gender = gender_data
            else:
                gender = 'EPalGenderType::Female'
            is_male = 'Male' in gender
            gender_key = 'gender_male' if is_male else 'gender_female'
            gender_color = '#7DD3FC' if is_male else '#FB7185'
            gender_pix = _get_ui_icon_pixmap(gender_key, 18)
            if gender_pix:
                self.gender_icon.setIcon(QIcon(gender_pix))
            base = get_pal_base_data(cid)
            while self.type_icons_layout.count():
                item = self.type_icons_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            if base:
                elements = base.get('elements', {})
                if elements:
                    for elem_name in elements:
                        elem_pix = _get_element_pixmap(elem_name, 'small', 16)
                        elem_color = self._ELEMENT_MAP.get(elem_name, ('☆', '#A78BFA'))[1]
                        if elem_pix:
                            badge = QLabel()
                            badge.setFixedSize(16, 16)
                            badge.setAlignment(Qt.AlignCenter)
                            badge.setPixmap(elem_pix)
                            badge.setStyleSheet(f'background: transparent; border: 1px solid {elem_color}40; border-radius: 8px;')
                            badge.setAttribute(Qt.WA_TranslucentBackground)
                        else:
                            elem_data = self._ELEMENT_MAP.get(elem_name, ('☆', '#A78BFA'))
                            badge = QLabel(elem_data[0])
                            badge.setFixedSize(16, 16)
                            badge.setAlignment(Qt.AlignCenter)
                            badge.setStyleSheet(f'font-size: 11px; font-weight: bold; color: {elem_color}; background: transparent; border: 1px solid {elem_color}40; border-radius: 8px;')
                        self.type_icons_layout.addWidget(badge)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            is_imported = extract_value(raw, 'bImportedCharacter', False)
            fav_idx = extract_value(raw, 'FavoriteIndex', 0)
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            trust_rank = 0
            thr = _ensure_friendship_thresholds()
            for r in range(len(thr) - 1, 0, -1):
                if trust_points >= thr[r]:
                    trust_rank = r
                    break
            rank_raw = extract_value(raw, 'Rank', 0)
            condenser_rank = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            is_awake = bool(extract_value(raw, 'bIsAwakening', False))
            hp_val = safe_nested_get(raw, ['Hp', 'value', 'Value', 'value'], 0)
            max_hp = safe_nested_get(raw, ['MaxHP', 'value', 'Value', 'value'], 0)
            if max_hp <= 0 and base:
                max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser_rank, is_awake)
            if max_hp <= 0:
                max_hp = hp_val if hp_val > 0 else 1
            atk_val = extract_value(raw, 'Attack', 0)
            def_val = extract_value(raw, 'Defense', 0)
            wspd_val = extract_value(raw, 'WorkSpeed', 0)
            hunger_full = extract_value(raw, 'FullStomach', 0)
            exp_val = extract_value(raw, 'Exp', 0)
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            trust_progress = 0
            trust_next = 0
            thr = _ensure_friendship_thresholds()
            if trust_rank < len(thr) - 1:
                current_threshold = thr[trust_rank]
                next_threshold = thr[trust_rank + 1]
                trust_span = next_threshold - current_threshold
                trust_progress = min((trust_points - current_threshold) / trust_span * 100, 100)
                trust_next = next_threshold
            else:
                trust_progress = 100
                trust_next = 0
            stats = base.get('stats', {}) if base else {}
            base_hp = stats.get('hp', 100)
            base_atk = stats.get('melee_attack', 100)
            base_def = stats.get('defense', 100)
            base_craft = stats.get('craft_speed', 100)
            base_stomach = stats.get('max_full_stomach', 300)
            base_food = stats.get('food_amount', 5)
            if atk_val == 0:
                atk_val = base_atk
            if def_val == 0:
                def_val = base_def
            if wspd_val == 0:
                wspd_val = base_craft
            ws = base.get('work_suitabilities', {}) if base else {}
            for i, (icon_lbl, (val_lbl, ws_key, val_badge)) in enumerate(zip(self.work_icon_labels, self.work_icon_values)):
                ws_level = ws.get(ws_key, 0)
                if ws_level > 0:
                    icon_lbl.setStyleSheet('background: rgba(74,222,128,0.15); border: 1px solid rgba(74,222,128,0.25); border-radius: 3px;')
                    eff = icon_lbl.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(1.0)
                    val_lbl.setText(str(ws_level))
                    val_lbl.setStyleSheet('font-size: 8px; font-weight: 700; color: #4ADE80; background: transparent; border: none;')
                    val_badge.setStyleSheet('background: rgba(0,0,0,0.45); border: 1px solid rgba(74,222,128,0.2); border-radius: 2px;')
                else:
                    icon_lbl.setStyleSheet('background: transparent; border: none;')
                    eff = icon_lbl.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(0.06)
                    val_lbl.setText('')
                    val_lbl.setStyleSheet('font-size: 8px; font-weight: 700; color: transparent; background: transparent; border: none;')
                    val_badge.setStyleSheet('background: transparent; border: none;')
            hunger_max = float(base_stomach) if base_stomach else 300.0
            hp_pct = int(min(hp_val / max_hp * 100, 100))
            hunger_pct = int(min(hunger_full / hunger_max * 100, 100))
            exp_pct = int(min(exp_val / 1000.0 * 100, 100))
            self.hp_bar.setValue(hp_pct)
            self.hp_bar.setFormat(f'{int(hp_val) // 1000} / {int(max_hp) // 1000}')
            self.hunger_bar.setValue(hunger_pct)
            self.hunger_bar.setFormat(f'{int(hunger_full)} / {int(hunger_max)}')
            self.exp_header_bar.setValue(exp_pct)
            self.next_lbl.setText(str(int(exp_val)))
            san_val = extract_value(raw, 'SanityValue', 100.0)
            san_pct = int(min(float(san_val), 100))
            self.san_bar.setValue(san_pct)
            self.san_bar.setFormat(f'{int(san_val)} / 100')
            self.trust_bar.setValue(int(trust_progress))
            self.trust_bar.setFormat('MAX' if trust_rank >= 10 else f'{int(trust_points)} / {int(trust_next)}')
            self.atk_lbl.setText(str(int(atk_val)))
            self.def_lbl.setText(str(int(def_val)))
            self.wspd_lbl.setText(str(int(wspd_val)))
            talent_hp_val = extract_value(raw, 'Talent_HP', 0)
            talent_shot_val = extract_value(raw, 'Talent_Shot', 0)
            talent_def_val = extract_value(raw, 'Talent_Defense', 0)
            rank_hp_val = extract_value(raw, 'Rank_HP', 0)
            rank_atk_val = extract_value(raw, 'Rank_Attack', 0)
            rank_def_val = extract_value(raw, 'Rank_Defence', 0)
            rank_craft_val = extract_value(raw, 'Rank_CraftSpeed', 0)
            self.ivs_hp_lbl.setText(str(talent_hp_val))
            self.ivs_atk_lbl.setText(str(talent_shot_val))
            self.ivs_def_lbl.setText(str(talent_def_val))
            self.soul_hp_lbl.setText(str(rank_hp_val))
            self.soul_atk_lbl.setText(str(rank_atk_val))
            self.soul_def_lbl.setText(str(rank_def_val))
            self.soul_craft_lbl.setText(str(rank_craft_val))
            food_val = max(0, min(int(base_food), 10))
            for i, fc in enumerate(self.food_icon_labels):
                fc.setStyleSheet('background: transparent; border: none;')
                if i >= food_val:
                    foff = _get_ui_icon_pixmap('food_off', 12)
                    if foff:
                        fc.setPixmap(foff)
                    eff = fc.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(0.14)
                else:
                    fon = _get_ui_icon_pixmap('food_on', 12)
                    if fon:
                        fc.setPixmap(fon)
                    eff = fc.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(1.0)
            if is_imported:
                self.dna_overlay.show()
            else:
                self.dna_overlay.hide()
            if is_boss:
                bp = _get_boss_alpha_pixmap(16)
                if bp:
                    self.boss_overlay.setPixmap(bp)
                self.boss_overlay.show()
                self.lucky_overlay.hide()
            elif is_lucky:
                sp = _get_boss_shiny_pixmap(16)
                if sp:
                    self.lucky_overlay.setPixmap(sp)
                self.lucky_overlay.show()
                self.boss_overlay.hide()
            else:
                self.boss_overlay.hide()
                self.lucky_overlay.hide()
            is_awakening = extract_value(raw, 'bIsAwakening', False)
            self.awake_overlay.setVisible(bool(is_awakening))
            if fav_idx and int(fav_idx) > 0:
                lock_key = f'lock_{min(int(fav_idx), 3)}'
                lock_pix = _get_ui_icon_pixmap(lock_key, 16) or _get_ui_icon_pixmap('lock_1', 16) or _get_ui_icon_pixmap('lock', 16)
                if lock_pix:
                    self.lock_overlay.setPixmap(lock_pix)
                    self.lock_overlay.setStyleSheet('background: transparent; border: none;')
                self.lock_overlay.show()
            else:
                self.lock_overlay.hide()
            self.portrait_ring.set_awakened(bool(is_awakening))
            self.info_boss_btn.blockSignals(True)
            self.info_boss_btn.setChecked(is_boss)
            self.info_boss_btn.blockSignals(False)
            self.info_lucky_btn.blockSignals(True)
            self.info_lucky_btn.setChecked(is_lucky)
            self.info_lucky_btn.blockSignals(False)
            self.info_awake_btn.blockSignals(True)
            self.info_awake_btn.setChecked(bool(is_awakening))
            self.info_awake_btn.blockSignals(False)
            self.info_dna_btn.blockSignals(True)
            self.info_dna_btn.setChecked(bool(is_imported))
            self.info_dna_btn.blockSignals(False)
            fav_idx_val = int(fav_idx) if fav_idx else 0
            lock_icon_key = f'lock_{min(fav_idx_val, 3)}' if fav_idx_val > 0 else 'lock_0'
            fav_pix = _get_ui_icon_pixmap(lock_icon_key, 18) or _get_ui_icon_pixmap('lock_0', 18)
            if fav_pix:
                self.info_fav_btn.setIcon(QIcon(fav_pix))
                self.info_fav_btn.setText('')
            else:
                self.info_fav_btn.setIcon(QIcon())
                self.info_fav_btn.setText('★' * fav_idx_val if fav_idx_val else '★')
            if fav_idx_val >= 1 and fav_idx_val <= 3:
                self.info_fav_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); border: 1px solid #FBBF24; border-radius: 4px; } QPushButton:hover { background: rgba(251,191,36,0.25); }')
            else:
                self.info_fav_btn.setStyleSheet('QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; } QPushButton:hover { background: rgba(255,255,255,0.08); }')
            soul_total = sum((int(x) for x in (rank_hp_val, rank_atk_val, rank_def_val, rank_craft_val) if str(x).isdigit()))
            self.stat_plus_lbl.setText(f'+{soul_total}')
            bp = _get_ui_icon_pixmap('buildup', 14)
            if bp:
                self.soul_buildup_icon.setPixmap(bp)
                self.soul_row_icon.setPixmap(bp)
            ivp = _get_ui_icon_pixmap('talent_checker', 14)
            if ivp:
                self.iv_icon.setPixmap(ivp)
            rank_raw = extract_value(raw, 'Rank', 0)
            rank_int = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            star_count = max(0, rank_int - 1)
            for i, sl in enumerate(self.star_labels):
                sl.set_filled(i < star_count)
            if star_count >= 4:
                self._start_star_shine()
            else:
                self._stop_star_shine()
            icon_path = _get_pal_icon_path(cid)
            pix = _get_cached_pixmap(icon_path, 80)
            if pix:
                self.portrait_icon.setPixmap(pix)
            tip = f'{pal_name} [Lv.{level}]'
            if base and base.get('description'):
                tip += f'<br><br>{wrap_tooltip_text(base["description"])}'
            # Set tooltip on portrait_frame to ensure unified tooltip style
            self.portrait_frame.setToolTip(tip)
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            while self.active_skills_list.count():
                item = self.active_skills_list.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            for i in range(3):
                e = e_list[i] if i < len(e_list) else ''
                if isinstance(e, dict):
                    e = e.get('value', '')
                if e:
                    w_clean = e.split('::')[-1].lower()
                    move_name = PalFrame._SKILLMAP.get(w_clean, e.split('::')[-1])
                    skill_info = _SKILL_DATA.get(w_clean, {}) if isinstance(_SKILL_DATA, dict) else {}
                    skill_elem = skill_info.get('element', 'Normal')
                    skill_power = skill_info.get('power', 0)
                    elem_color = self._ELEMENT_COLORS.get(skill_elem, '#9CA3AF')
                else:
                    move_name = '--'
                    skill_elem = ''
                    skill_power = 0
                    elem_color = '#4A4A50'
                slot = SkillSlotFrame()
                slot.setStyleSheet('QFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; }')
                slot.setFixedHeight(26)
                slot.setCursor(Qt.PointingHandCursor)
                slot.installEventFilter(self)
                slot._skill_slot_idx = i
                slot_layout = QHBoxLayout(slot)
                slot_layout.setContentsMargins(6, 0, 6, 0)
                slot_layout.setSpacing(4)
                slot_layout.setAlignment(Qt.AlignVCenter)
                name_lbl = QLabel(move_name)
                name_lbl.setStyleSheet('font-size: 9px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
                slot_layout.addWidget(name_lbl, 1)
                elem_badge = QLabel()
                elem_badge.setFixedSize(18, 18)
                elem_badge.setAlignment(Qt.AlignCenter)
                if skill_elem:
                    elem_pix = _get_element_pixmap(skill_elem, 'small', 16)
                    if elem_pix:
                        elem_badge.setScaledContents(True)
                        elem_badge.setPixmap(elem_pix)
                        elem_badge.setStyleSheet('background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 2px; padding: 1px; margin: 0px;')
                    else:
                        elem_badge.setText(skill_elem[:4])
                        elem_badge.setStyleSheet(f'font-size: 6px; font-weight: 700; color: {elem_color}; background: rgba(255,255,255,0.04); border: 1px solid {elem_color}40; border-radius: 2px;')
                else:
                    elem_badge.setStyleSheet('background: transparent; border: none;')
                slot_layout.addWidget(elem_badge)
                power_lbl = QLabel(str(skill_power) if skill_power else '--')
                power_lbl.setFixedWidth(24)
                power_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                power_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: #F59E0B; background: transparent; border: none;')
                slot_layout.addWidget(power_lbl)
                if e and skill_info:
                    tip_parts = [f'<b>{move_name}</b>', f'Element: {skill_elem}', f'Power: {skill_power}']
                    cd = skill_info.get('cooldown', 0)
                    if cd:
                        tip_parts.append(f'Cooldown: {cd}s')
                    desc = skill_info.get('description', '')
                    if desc:
                        tip_parts.append('')
                        tip_parts.append(desc)
                    slot.setToolTip('<br>'.join(tip_parts))
                self.active_skills_list.addWidget(slot)
            p_skills = raw.get('PassiveSkillList', {})
            if isinstance(p_skills, dict):
                p_list = p_skills.get('value', {}).get('values', [])
            elif isinstance(p_skills, list):
                p_list = p_skills
            else:
                p_list = []
            for i in range(4):
                display_name = '--'
                tc = 'rgba(255,255,255,0.3)'
                bg = 'rgba(255,255,255,0.03)'
                bd = 'rgba(255,255,255,0.06)'
                anim_mode = None
                p_val = None
                p_clean = ''
                if i < len(p_list) and p_list[i]:
                    p_val = p_list[i]
                    if isinstance(p_val, dict):
                        p_val = p_val.get('value', '')
                    if p_val and hasattr(p_val, 'lower'):
                        p_clean = p_val.lower()
                    else:
                        p_clean = str(p_val) if p_val else ''
                    display_name = PalFrame._PASSMAP.get(p_clean, str(p_val))
                    bg, bd, tc = PalFrame._passive_rank_color(p_clean)
                    rank = PalFrame._PASSRANK.get(p_clean, 1)
                    is_world_tree = 'world' in display_name.lower() and 'tree' in display_name.lower()
                    if is_world_tree:
                        anim_mode = 'world_tree'
                    elif rank >= 4:
                        anim_mode = 'legend'
                self.passive_slots[i].setText(display_name)
                self.passive_slots[i].setStyleSheet(f'font-size: 9px; font-weight: 700; color: {tc}; background: transparent; border: none;')
                parent_frame = self.passive_slots[i].parentWidget()
                if parent_frame and parent_frame.objectName() == 'passiveCard':
                    parent_frame.setStyleSheet(f'QFrame#passiveCard {{ background: {bg}; border: 1.5px solid {bd}; border-radius: 4px; padding: 3px 6px; }}')
                if i < len(self.passive_cards):
                    self._set_passive_overlay(i, anim_mode)
                parent_frame.setStyleSheet(
                    parent_frame.styleSheet() +
                    '\nQToolTip { background: rgba(18,20,24,0.98); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }'
                )
                if p_clean:
                    p_info = _PASSIVE_DATA.get(p_clean, {}) if isinstance(_PASSIVE_DATA, dict) else {}
                    p_desc = p_info.get('description', '')
                    tip_parts = [f'<b style="color:{tc}">{display_name}</b>']
                    rank_labels = {1: 'Common', 2: 'Rare', 4: 'Epic', -99: 'Negative'}
                    tip_parts.append(f"<i>{rank_labels.get(rank, f'Rank {rank}')}</i>")
                    if p_desc:
                        p_desc = p_desc.replace('{CharacterName}', 'Pal')
                        for ei in range(1, 5):
                            ev = p_info.get(f'effect{ei}', 0)
                            ev_str = str(int(ev)) if isinstance(ev, float) and ev == int(ev) else f'{ev:.0f}' if isinstance(ev, float) else str(ev)
                            p_desc = p_desc.replace(f'{{EffectValue{ei}}}', ev_str)
                        tip_parts.append('')
                        tip_parts.append(p_desc)
                    parent_frame.setToolTip('<br>'.join(tip_parts))
            pskill_name = base.get('partner_skill', '') if base else ''
            pal_desc = base.get('description', '') if base else ''
            self.partner_name_lbl.setText(pskill_name or pal_name)
            self.partner_lvl_lbl.setText(f'Lv {max(1, condenser_rank)}')
            self.partner_desc_lbl.setText(pal_desc or f'Partner skill for {pal_name}. Effects scale with level.')
        except Exception:
            import traceback
            traceback.print_exc()
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
            if obj is self.name_lbl:
                self._on_name_click()
                return True
            if obj is self.star_container:
                self._on_star_click()
                return True
            if obj is self.level_num_lbl or obj is self.stat_plus_lbl:
                self._on_level_click()
                return True
            if obj in (self.ivs_hp_lbl, self.ivs_atk_lbl, self.ivs_def_lbl):
                self._on_talent_click(obj)
                return True
            if obj in (self.soul_hp_lbl, self.soul_atk_lbl, self.soul_def_lbl, self.soul_craft_lbl):
                self._on_soul_click(obj)
                return True
            if hasattr(obj, '_skill_slot_idx'):
                self._on_active_skill_click(obj._skill_slot_idx)
                return True
        return super().eventFilter(obj, event)
    def _on_name_click(self):
        if not self._raw:
            return
        current = extract_value(self._raw, 'NickName', '')
        dlg = QInputDialog(self)
        dlg.setWindowTitle(t('edit_pals.rename_pal'))
        dlg.setLabelText(t('edit_pals.nickname') + ':')
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setTextValue(current or '')
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            text = dlg.textValue()
            if text is not None:
                self._raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': text.strip()}
                self._refresh()
    def _on_gender_click(self):
        if not self._raw:
            return
        gv = extract_value(self._raw, 'Gender', {})
        if isinstance(gv, dict) and 'value' in gv:
            gender = gv['value']
        else:
            gender = str(gv)
        new_g = 'EPalGenderType::Male' if 'Female' in str(gender) else 'EPalGenderType::Female'
        self._raw['Gender'] = {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': new_g}}
        self._refresh()
    def _on_star_click(self):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'Rank', 0))
        cycle = [1, 2, 3, 4, 5]
        try:
            idx = cycle.index(cur)
            new_r = cycle[(idx + 1) % len(cycle)]
        except ValueError:
            new_r = 1
        self._raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': new_r}}
        self._recalc_hp()
    def _start_star_shine(self):
        self._star_shine_phase = 0.0
        for sl in self.star_labels:
            sl.start_shine()
        self._star_shine_timer.start(16)
    def _stop_star_shine(self):
        self._star_shine_timer.stop()
        for sl in self.star_labels:
            sl.stop_shine()
    def _tick_star_shine(self):
        self._star_shine_phase = (self._star_shine_phase + 0.0032) % 1.0
        for sl in self.star_labels:
            sl.set_phase(self._star_shine_phase)
    def _on_level_click(self):
        if not self._raw:
            return
        cur = self._raw.get('Level', {}).get('value', {}).get('value', 1)
        try:
            cur = int(cur)
        except (TypeError, ValueError):
            cur = 1
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Set Level')
        dlg.setLabelText('Level (1-80):')
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(1, 80)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            self._set_level(dlg.intValue())
    def _set_level(self, value):
        raw = self._raw
        cid = extract_value(raw, 'CharacterID', '')
        raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
        try:
            base_dir = constants.get_base_path()
            exp_table_path = os.path.join(base_dir, 'resources', 'game_data', 'pal_exp_table.json')
            exp_table = json_tools.load(exp_table_path)
            exp_val = exp_table[str(value)]['PalTotalEXP']
        except Exception:
            exp_val = 0
        raw['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
        talent_hp = extract_value(raw, 'Talent_HP', 0)
        rank_hp = extract_value(raw, 'Rank_HP', 0)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        trust_points = extract_value(raw, 'FriendshipPoint', 0)
        friendship_rank = 0
        thr = _ensure_friendship_thresholds()
        for r in range(len(thr) - 1, 0, -1):
            if int(trust_points) >= thr[r]:
                friendship_rank = r
                break
        base = get_pal_base_data(cid)
        if base:
            rank_raw = extract_value(raw, 'Rank', 0)
            condenser_rank = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            is_awake_val = bool(extract_value(raw, 'bIsAwakening', False))
            new_max_hp = calculate_max_hp(base, value, talent_hp, rank_hp, is_boss, is_lucky, friendship_rank, condenser_rank, is_awake_val)
            raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(new_max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            raw['MaxHP'] = raw['Hp']
        self._refresh()
    def _on_talent_click(self, lbl):
        if not self._raw:
            return
        mapping = {self.ivs_hp_lbl: ('Talent_HP', 0, 100), self.ivs_atk_lbl: ('Talent_Shot', 0, 100), self.ivs_def_lbl: ('Talent_Defense', 0, 100)}
        key, lo, hi = mapping.get(lbl, ('Talent_HP', 0, 100))
        cur = int(extract_value(self._raw, key, 0))
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Set Talent')
        dlg.setLabelText(f'{key} (0-100):')
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(lo, hi)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            self._raw[key] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': dlg.intValue()}}
            self._recalc_hp()
    def _on_soul_click(self, lbl):
        if not self._raw:
            return
        mapping = {self.soul_hp_lbl: ('Rank_HP', 0, 20), self.soul_atk_lbl: ('Rank_Attack', 0, 20), self.soul_def_lbl: ('Rank_Defence', 0, 20), self.soul_craft_lbl: ('Rank_CraftSpeed', 0, 20)}
        key, lo, hi = mapping.get(lbl, ('Rank_HP', 0, 20))
        cur = int(extract_value(self._raw, key, 0))
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Set Soul')
        dlg.setLabelText(f'{key} (0-20):')
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(lo, hi)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            self._raw[key] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': dlg.intValue()}}
            self._recalc_hp()
    def _on_active_skill_click(self, slot_idx):
        if not self._raw:
            return
        if slot_idx < 0 or slot_idx >= 3:
            return
        self._show_skill_picker(t('edit_pals.active_skills'), PalFrame._SKILLMAP, slot_idx, is_active=True)
    def _on_passive_click(self, slot_idx):
        if not self._raw:
            return
        if slot_idx < 0 or slot_idx >= 4:
            return
        self._show_skill_picker(t('edit_pals.passives'), PalFrame._PASSMAP, slot_idx, is_active=False)
    def _show_skill_picker(self, title, skill_map, slot_idx, is_active):
        try:
            import gc
            gc.collect()
            popup = QWidget()
            popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
            self._popup = popup
            popup.setStyleSheet(PICKER_BG_STYLE)
            layout = QVBoxLayout(popup)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(2)
            search = QLineEdit()
            search.setPlaceholderText('Search...')
            search.setStyleSheet(PICKER_SEARCH_STYLE)
            layout.addWidget(search)
            lst = QListWidget()
            lst.setStyleSheet(PICKER_LIST_STYLE)
            lst.setMaximumHeight(300)
            lst.setMinimumWidth(220)
            clear_item = QListWidgetItem(t('common.clear') if t else '-- clear --')
            lst.addItem(clear_item)
            names = sorted(skill_map.values())
            _ensure_skill_data()
            for name in names:
                if not name:
                    continue
                item = QListWidgetItem(name)
                if is_active:
                    asset = None
                    for a, n in skill_map.items():
                        if n == name:
                            asset = a
                            break
                    if asset:
                        key = asset.split('::')[-1].lower()
                        if any((pat.lower() in key for pat in _SKILL_EXCLUSION_PATTERNS)):
                            continue
                        info = _SKILL_DATA.get(key, {}) if isinstance(_SKILL_DATA, dict) else {}
                        elem = info.get('element', 'Normal')
                        pwr = info.get('power', 0)
                        epix = _get_element_pixmap(elem, 'small', 16)
                        if epix:
                            item.setIcon(QIcon(epix))
                        item.setText(f'{pwr} - {name}')
                        item.setData(Qt.UserRole, name)
                        tip_parts = [f'<b>{name}</b>', f'Element: {elem}', f'Power: {pwr}']
                        cd = info.get('cooldown', 0)
                        if cd:
                            tip_parts.append(f'Cooldown: {cd}s')
                        desc = info.get('description', '')
                        if desc:
                            tip_parts.append('')
                            tip_parts.append(desc)
                        item.setToolTip('<br>'.join(tip_parts))
                else:
                    asset = None
                    for a, n in skill_map.items():
                        if n == name:
                            asset = a
                            break
                    if asset:
                        rank = PalFrame._PASSRANK.get(asset.lower(), 1)
                        item.setData(Qt.UserRole, asset.lower())
                        item.setData(Qt.UserRole + 1, rank)
                        is_wt = 'world' in name.lower() and 'tree' in name.lower()
                        item.setData(Qt.UserRole + 2, is_wt)
                        bg, bd, tc = PalFrame._passive_rank_color(asset.lower())
                        item.setData(Qt.UserRole + 3, tc)
                        item.setData(Qt.UserRole + 4, bd)
                        item.setForeground(QColor(tc))
                        _ensure_passive_data()
                        p_info = _PASSIVE_DATA.get(asset.lower(), {}) if isinstance(_PASSIVE_DATA, dict) else {}
                        p_desc = p_info.get('description', '')
                        rank_labels = {1: 'Common', 2: 'Rare', 4: 'Epic', -99: 'Negative'}
                        tip_parts = [f'<b style="color:{tc}">{name}</b>', f"<i>{rank_labels.get(rank, f'Rank {rank}')}</i>"]
                        if p_desc:
                            p_desc = p_desc.replace('{CharacterName}', 'Pal')
                            for ei in range(1, 5):
                                ev = p_info.get(f'effect{ei}', 0)
                                ev_str = str(int(ev)) if isinstance(ev, float) and ev == int(ev) else f'{ev:.0f}' if isinstance(ev, float) else str(ev)
                                p_desc = p_desc.replace(f'{{EffectValue{ei}}}', ev_str)
                            tip_parts.append('')
                            tip_parts.append(p_desc)
                        item.setToolTip('<br>'.join(tip_parts))
                lst.addItem(item)
            if not is_active:
                lst.setItemDelegate(_PassiveSkillDelegate(lst))
            cur_data = self._raw.get('EquipWaza' if is_active else 'PassiveSkillList', {})
            cur_list = cur_data.get('value', {}).get('values', []) if isinstance(cur_data, dict) else cur_data if isinstance(cur_data, list) else []
            cur_val = cur_list[slot_idx] if slot_idx < len(cur_list) else ''
            if cur_val:
                if isinstance(cur_val, dict):
                    cur_val = cur_val.get('value', '')
                if cur_val and hasattr(cur_val, 'lower'):
                    display = skill_map.get(cur_val.lower(), cur_val)
                    for i in range(lst.count()):
                        item = lst.item(i)
                        found = False
                        if is_active:
                            found = item.data(Qt.UserRole) == display
                        else:
                            found = item.text() == display
                        if found:
                            lst.setCurrentRow(i)
                            break
            search.textChanged.connect(lambda t, l=lst: [l.item(i).setHidden(t.lower() not in l.item(i).text().lower()) for i in range(l.count())])
            layout.addWidget(lst)
            popup.move(QCursor.pos())
            popup.show()
            search.setFocus()
            if not is_active:
                anim_timer = QTimer(popup)
                def _tick_anim():
                    global _anim_phase
                    _anim_phase = (_anim_phase + 0.03) % 10000.0
                    lst.viewport().update()
                anim_timer.timeout.connect(_tick_anim)
                anim_timer.start(33)
            chosen = None
            def on_select():
                nonlocal chosen
                sel = lst.currentItem()
                chosen = None
                if sel:
                    if is_active and sel.data(Qt.UserRole):
                        chosen = sel.data(Qt.UserRole)
                    else:
                        chosen = sel.text()
                popup.hide()
            lst.itemClicked.connect(on_select)
            search.returnPressed.connect(on_select)
            while popup.isVisible():
                QApplication.processEvents()
                QThread.msleep(5)
            if not is_active:
                anim_timer.stop()
            self._popup = None
            if not chosen:
                return
            if chosen.startswith('--'):
                asset = ''
            else:
                asset = None
                for a, n in skill_map.items():
                    if n == chosen:
                        asset = a
                        break
                if not asset:
                    return
            QTimer.singleShot(0, lambda a=asset, s=slot_idx, ia=is_active: self._set_active_skill(s, a) if ia else self._set_passive_skill(s, a))
        except Exception:
            import traceback
            traceback.print_exc()
            return
    def _set_active_skill(self, slot_idx, asset):
        ew_data = self._raw.get('EquipWaza', {})
        cur = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
        if not isinstance(cur, list):
            cur = []
        while len(cur) <= slot_idx:
            cur.append('')
        cur[slot_idx] = asset
        self._raw['EquipWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': cur[:3]}, 'type': 'ArrayProperty'}
        self._refresh()
    def _set_passive_skill(self, slot_idx, asset):
        ps_data = self._raw.get('PassiveSkillList', {})
        cur = ps_data.get('value', {}).get('values', []) if isinstance(ps_data, dict) else ps_data if isinstance(ps_data, list) else []
        if not isinstance(cur, list):
            cur = []
        while len(cur) <= slot_idx:
            cur.append('')
        cur[slot_idx] = asset
        self._raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': cur[:4]}, 'type': 'ArrayProperty'}
        self._refresh()
    def _learn_all_skills(self):
        if not self._raw:
            return
        _learn_all_skills_raw(self._raw)
        self._refresh()
    def _on_boss_toggle(self):
        if not self._raw:
            return
        cid = extract_value(self._raw, 'CharacterID', '')
        if self.info_boss_btn.isChecked():
            if not cid.upper().startswith('BOSS_'):
                self._raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'BOSS_' + cid}
                if self.info_lucky_btn.isChecked():
                    self.info_lucky_btn.setChecked(False)
                    self._raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': False}
        elif cid.upper().startswith('BOSS_'):
            self._raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[5:]}
        self._recalc_hp()
    def _on_lucky_toggle(self):
        if not self._raw:
            return
        is_lucky = self.info_lucky_btn.isChecked()
        self._raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': is_lucky}
        if is_lucky:
            self.info_boss_btn.setChecked(False)
            cid = extract_value(self._raw, 'CharacterID', '')
            if cid.upper().startswith('BOSS_'):
                self._raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[5:]}
        self._recalc_hp()
    def _on_awake_toggle(self):
        if not self._raw:
            return
        is_awake = self.info_awake_btn.isChecked()
        self._raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': is_awake}
        self._recalc_hp()
    def _recalc_hp(self):
        cur_level = int(extract_value(self._raw, 'Level', 1))
        self._set_level(cur_level)
    def _on_fav_toggle(self):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'FavoriteIndex', 0))
        nxt = cur + 1 if cur < 3 else 0
        self._raw['FavoriteIndex'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': nxt}}
        self._refresh()
    def _on_dna_toggle(self):
        if not self._raw:
            return
        is_dna = self.info_dna_btn.isChecked()
        self._raw['bImportedCharacter'] = {'id': None, 'type': 'BoolProperty', 'value': is_dna}
        self._refresh()
    def _on_max_click(self):
        if not self._raw:
            return
        self._raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
        self._raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
        self._raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
        self._raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
        self._raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
        self._raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
        self._raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
        self._raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 5}}
        self._raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
        self._raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
        self._set_level(80)
    def _refresh(self):
        if self.last_clicked_data:
            self._update_display(self.last_clicked_data)
        parent = self.parent()
        while parent:
            if hasattr(parent, 'tools_tab'):
                parent.tools_tab.refresh()
                break
            if hasattr(parent, '_update_party_slots'):
                parent._update_party_slots()
            if hasattr(parent, 'palbox_slots') and hasattr(parent, 'party_slots'):
                for slot in parent.palbox_slots + parent.party_slots:
                    if hasattr(slot, 'pal_data') and slot.pal_data is self.last_clicked_data:
                        slot.update_display()
                        slot.set_selected(True)
                        break
                if parent.selected_pal_slot:
                    ptype, idx = parent.selected_pal_slot
                    if ptype == 'party':
                        parent._highlight_party_slot(idx)
                    elif ptype == 'palbox':
                        parent._highlight_palbox_slot(idx)
                break
            parent = parent.parent()

    def refresh_labels(self):
        self._no_data_overlay.setText(t('pal_editor.no_pal_data') if t else 'No Pal Data')
        if hasattr(self, '_lv_label'):
            self._lv_label.setText(t('pal_editor.level') if t else 'LEVEL')
        if hasattr(self, '_atk_label'):
            self._atk_label.setText(t('pal_editor.attack') if t else 'Attack')
        if hasattr(self, '_def_label'):
            self._def_label.setText(t('pal_editor.defense') if t else 'Defense')
        if hasattr(self, '_wspd_label'):
            self._wspd_label.setText(t('pal_editor.work_speed') if t else 'Work Speed')
        if hasattr(self, '_as_title'):
            self._as_title.setText(t('pal_editor.active_skills') if t else 'Active Skills')
        if hasattr(self, '_passive_title'):
            self._passive_title.setText(t('pal_editor.passive_skills') if t else 'Passive Skills')
class PalEditorWidget(QWidget):
    _process_lock = threading.Lock()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player_uid = None
        self.player_name = None
        self.party_container = None
        self.palbox_container = None
        self.player_sav_path = None
        self.dps_file_path = None
        self.dps_loaded = False
        self.party_pals = {}
        self.palbox_pals = []
        self.current_box_index = 1
        self.selected_pal_slot = None
        self._hovered_pal = None
        self._clicked_pal = None
        self.palbox_pal_dict = {}
        self._setup_ui()
        self._setup_hotkeys()
    def _setup_hotkeys(self):
        self.prev_box_shortcut = QShortcut(QKeySequence(Qt.Key_Q), self)
        self.prev_box_shortcut.activated.connect(self._prev_box)
        self.next_box_shortcut = QShortcut(QKeySequence(Qt.Key_E), self)
        self.next_box_shortcut.activated.connect(self._next_box)
        self.edit_shortcut = QShortcut(QKeySequence(Qt.Key_F), self)
        self.edit_shortcut.activated.connect(self._focus_pal_info)
    def _setup_ui(self):
        self.setObjectName('palRoot')
        self.setStyleSheet(_PAL_STYLESHEET)
        app = QApplication.instance()
        if app:
            current = app.styleSheet() or ''
            if 'QToolTip' not in current:
                app.setStyleSheet(current + TOOLTIP_STYLE)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        party_panel = QWidget()
        party_panel.setObjectName('partyPanel')
        party_panel.setFixedWidth(240)
        party_layout = QVBoxLayout(party_panel)
        party_layout.setContentsMargins(6, 6, 6, 6)
        party_layout.setSpacing(4)
        party_header = QLabel(t('pal_editor.party') if t else 'PARTY')
        self._party_header = party_header
        party_header.setStyleSheet('font-size: 12px; font-weight: 700; color: #7DD3FC; letter-spacing: 2px; border-bottom: 1px solid rgba(125,211,252,0.12); padding-bottom: 4px;')
        party_layout.addWidget(party_header)
        self.party_slots = []
        for i in range(5):
            slot = PartySlotWidget(None, i)
            slot.clicked.connect(partial(self._on_party_slot_clicked, i))
            slot.rightClicked.connect(self._on_slot_right_clicked)
            slot.entered.connect(partial(self._on_party_slot_entered, i))
            slot.left.connect(self._on_party_slot_left)
            party_layout.addWidget(slot)
            self.party_slots.append(slot)
        root.addWidget(party_panel)
        palbox_panel = QWidget()
        palbox_panel.setObjectName('palboxPanel')
        palbox_layout = QVBoxLayout(palbox_panel)
        palbox_layout.setContentsMargins(6, 6, 6, 6)
        palbox_layout.setSpacing(6)
        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        self.box_label = QLabel(t('pal_editor.box', n=1) if t else 'Box 1')
        self.box_label.setObjectName('boxHeader')
        self.box_label.setFixedWidth(90)
        self.box_label.setAlignment(Qt.AlignCenter)
        header_row.addWidget(self.box_label)
        header_row.addStretch()
        self.prev_box_btn = QPushButton('◀')
        self.prev_box_btn.setObjectName('navBtn')
        self.prev_box_btn.setFixedSize(32, 28)
        self.prev_box_btn.clicked.connect(self._prev_box)
        header_row.addWidget(self.prev_box_btn)
        self.next_box_btn = QPushButton('▶')
        self.next_box_btn.setObjectName('navBtn')
        self.next_box_btn.setFixedSize(32, 28)
        self.next_box_btn.clicked.connect(self._next_box)
        header_row.addWidget(self.next_box_btn)
        palbox_layout.addLayout(header_row)
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_scroll.setStyleSheet('QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 6px; background: rgba(255,255,255,0.03); border-radius: 3px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.2); border-radius: 3px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.4); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }')
        self.grid_scroll.viewport().installEventFilter(self)
        grid_container = QWidget()
        grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.palbox_slots = []
        for row in range(5):
            self.grid_layout.setRowStretch(row, 1)
            for col in range(6):
                self.grid_layout.setColumnStretch(col, 1)
                idx = row * 6 + col
                slot = PalboxSlotWidget(None, idx)
                slot.clicked.connect(partial(self._on_palbox_slot_clicked, idx))
                slot.rightClicked.connect(self._on_slot_right_clicked)
                slot.entered.connect(partial(self._on_palbox_slot_entered, idx))
                slot.left.connect(self._on_palbox_slot_left)
                self.grid_layout.addWidget(slot, row, col)
                self.palbox_slots.append(slot)
        self.grid_scroll.setWidget(grid_container)
        palbox_layout.addWidget(self.grid_scroll)
        root.addWidget(palbox_panel, 1)
        self.pal_info = PalInfoWidget()
        self.pal_info.setMinimumWidth(340)
        root.addWidget(self.pal_info)
    def _prev_box(self):
        if self.current_box_index > 1:
            self.current_box_index -= 1
        else:
            self.current_box_index = 32
        self.box_label.setText(t('pal_editor.box', n=self.current_box_index) if t else f'Box {self.current_box_index}')
        self._update_palbox_page()
    def _next_box(self):
        if self.current_box_index < 32:
            self.current_box_index += 1
        else:
            self.current_box_index = 1
        self.box_label.setText(t('pal_editor.box', n=self.current_box_index) if t else f'Box {self.current_box_index}')
        self._update_palbox_page()
    def _on_party_slot_clicked(self, idx):
        slot = self.party_slots[idx]
        is_context = getattr(slot, '_context_click', False)
        if is_context:
            slot._context_click = False
        if idx in self.party_pals:
            pal = self.party_pals[idx]
            if not is_context and self._clicked_pal is pal and self.selected_pal_slot == ('party', idx):
                self._clicked_pal = None
                self.selected_pal_slot = None
                self._clear_party_highlight()
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                return
            self._clicked_pal = pal
            self.pal_info.set_clicked_pal(pal)
            self.selected_pal_slot = ('party', idx)
            self._highlight_party_slot(idx)
            self._clear_palbox_highlight()
    def _on_party_slot_entered(self, idx):
        if idx in self.party_pals:
            pal = self.party_pals[idx]
            self._hovered_pal = pal
            self.pal_info.set_hover_pal(pal)
    def _on_party_slot_left(self):
        self.pal_info.clear_hover()
    def _on_palbox_slot_clicked(self, idx):
        slot = self.palbox_slots[idx]
        is_context = getattr(slot, '_context_click', False)
        if is_context:
            slot._context_click = False
        pals_on_page = self._get_palbox_page_pals()
        if idx < len(pals_on_page) and pals_on_page[idx] is not None:
            if not is_context and self._clicked_pal is pals_on_page[idx] and self.selected_pal_slot == ('palbox', idx):
                self._clicked_pal = None
                self.selected_pal_slot = None
                self._clear_palbox_highlight()
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                return
            self._clicked_pal = pals_on_page[idx]
            self.pal_info.set_clicked_pal(pals_on_page[idx])
            self.selected_pal_slot = ('palbox', idx)
            self._highlight_palbox_slot(idx)
            self._clear_party_highlight()
    def _on_palbox_slot_entered(self, idx):
        pals_on_page = self._get_palbox_page_pals()
        if idx < len(pals_on_page) and pals_on_page[idx] is not None:
            self._hovered_pal = pals_on_page[idx]
            self.pal_info.set_hover_pal(pals_on_page[idx])
    def _on_palbox_slot_left(self):
        self.pal_info.clear_hover()
    def _on_slot_right_clicked(self, slot_index, action):
        sender = self.sender()
        is_party = sender in self.party_slots
        raw = sender._get_raw() if hasattr(sender, '_get_raw') else None
        if action == 'delete':
            self._delete_pal_at_slot(slot_index, is_party)
        elif action == 'add_new':
            self._add_new_pal_at_slot(slot_index)
        elif action == 'boss_toggle':
            if raw:
                cid = extract_value(raw, 'CharacterID', '')
                is_boss = cid.upper().startswith('BOSS_')
                _toggle_boss_raw(raw, not is_boss)
                self.pal_info._refresh()
                sender.update_display()
        elif action == 'lucky_toggle':
            if raw:
                is_lucky = extract_value(raw, 'IsRarePal', False)
                _toggle_lucky_raw(raw, not is_lucky)
                self.pal_info._refresh()
                sender.update_display()
        elif action == 'awake_toggle':
            if raw:
                is_awake = extract_value(raw, 'bIsAwakening', False)
                _toggle_awake_raw(raw, not is_awake)
                self.pal_info._refresh()
                sender.update_display()
        elif action == 'dna_toggle':
            if raw:
                is_dna = extract_value(raw, 'bImportedCharacter', False)
                _toggle_dna_raw(raw, not is_dna)
                self.pal_info._refresh()
                sender.update_display()
        elif action.startswith('fav_set_'):
            if raw:
                idx = int(action.split('_')[-1])
                _set_fav_raw(raw, idx)
                self.pal_info._refresh()
                sender.update_display()
        elif action == 'max_all_stats':
            if raw:
                self.pal_info._on_max_click()
        elif action == 'learn_all':
            if raw:
                try:
                    _learn_all_skills_raw(raw)
                    self.pal_info._refresh()
                    sender.update_display()
                    show_information(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_success'))
                except Exception:
                    show_warning(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_fail'))
    def _delete_pal_at_slot(self, slot_index, is_party=None):
        if is_party is None:
            is_party = self.selected_pal_slot and self.selected_pal_slot[0] == 'party'
        if is_party:
            if slot_index in self.party_pals:
                pal = self.party_pals[slot_index]
                reply = show_question(self, t('edit_pals.confirm_delete'), 'Delete this pal?')
                if not reply:
                    return
                try:
                    cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                    if pal in cmap:
                        cmap.remove(pal)
                except Exception:
                    pass
                del self.party_pals[slot_index]
                self._update_party_slots()
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                self._update_dashboard_stats()
        else:
            abs_idx = (self.current_box_index - 1) * 30 + slot_index
            if abs_idx in self.palbox_pal_dict:
                pal = self.palbox_pal_dict[abs_idx]
                reply = show_question(self, t('edit_pals.confirm_delete'), 'Delete this pal?')
                if not reply:
                    return
                try:
                    cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                    if pal in cmap:
                        cmap.remove(pal)
                except Exception:
                    pass
                del self.palbox_pal_dict[abs_idx]
                self._update_palbox_page()
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                self._update_dashboard_stats()
    def _add_new_pal_at_slot(self, slot_index):
        sender = self.sender()
        is_party = sender in self.party_slots
        dlg = PalCreateDialog(self, is_party, slot_index)
        if dlg.exec() == QDialog.Accepted and dlg.created_item:
            self._update_party_slots()
            self._update_palbox_page()
            self._update_dashboard_stats()
    def _focus_pal_info(self):
        self.pal_info.setFocus()
    def _highlight_party_slot(self, idx):
        for i, slot in enumerate(self.party_slots):
            slot.set_selected(i == idx)
    def _highlight_palbox_slot(self, idx):
        for i, slot in enumerate(self.palbox_slots):
            slot.set_selected(i == idx)
    def _clear_party_highlight(self):
        for slot in self.party_slots:
            slot.set_selected(False)
    def _clear_palbox_highlight(self):
        for slot in self.palbox_slots:
            slot.set_selected(False)
    def _get_palbox_page_pals(self):
        start = (self.current_box_index - 1) * 30
        result = []
        for offset in range(30):
            abs_idx = start + offset
            result.append(self.palbox_pal_dict.get(abs_idx))
        return result
    def _update_palbox_page(self):
        page_pals = self._get_palbox_page_pals()
        for i, slot in enumerate(self.palbox_slots):
            slot.pal_data = page_pals[i] if i < len(page_pals) else None
            slot.update_display()
            slot.set_selected(False)
    def set_player(self, player_uid, player_name):
        self.player_uid = player_uid
        self.player_name = player_name
        self._get_container_ids()
        PalFrame._load_maps()
        self._load_pals()
    def _get_container_ids(self):
        self.party_container = None
        self.palbox_container = None
        self.player_sav_path = None
        self.dps_file_path = None
        self.dps_loaded = False
        players_dir = os.path.join(constants.current_save_path, 'Players')
        target_uid = self.player_uid.replace('-', '').lower()
        if os.path.exists(players_dir):
            for filename in os.listdir(players_dir):
                if filename.endswith('.sav') and '_dps' not in filename:
                    p_uid_raw = filename.replace('.sav', '').lower()
                    if p_uid_raw == target_uid:
                        self.player_sav_path = os.path.join(players_dir, filename)
                        try:
                            p_gvas = sav_to_gvasfile(self.player_sav_path)
                            p_prop = p_gvas.properties.get('SaveData', {})
                            save_data = p_prop.get('value', {}) if isinstance(p_prop, dict) else {}
                            self.party_container = safe_nested_get(save_data, ['OtomoCharacterContainerId', 'value', 'ID', 'value'])
                            self.palbox_container = safe_nested_get(save_data, ['PalStorageContainerId', 'value', 'ID', 'value'])
                        except Exception as e:
                            print(f'Error loading player container IDs: {e}')
                            self.party_container = None
                            self.palbox_container = None
                elif filename.endswith('.sav') and '_dps' in filename:
                    p_uid_raw = filename.replace('_dps.sav', '').lower()
                    if p_uid_raw == target_uid:
                        self.dps_file_path = os.path.join(players_dir, filename)
    def clear(self):
        self.player_uid = None
        self.player_name = None
        self.party_container = None
        self.palbox_container = None
        self.dps_loaded = False
        self.party_pals = {}
        self.palbox_pal_dict = {}
        self.current_box_index = 1
        self.selected_pal_slot = None
        self._hovered_pal = None
        self._clicked_pal = None
        for slot in self.party_slots:
            slot.pal_data = None
            slot.update_display()
            slot.set_selected(False)
        for slot in self.palbox_slots:
            slot.pal_data = None
            slot.update_display()
            slot.set_selected(False)
        self.box_label.setText(t('pal_editor.box', n=1) if t else 'Box 1')
        self.pal_info.last_clicked_data = None
        self.pal_info._hovered_data = None
        self.pal_info._clear_display()
    def refresh(self):
        self._process_pending_changes()
        if self.player_uid:
            self._load_pals()
    def _process_pending_changes(self):
        pass

    def _update_dashboard_stats(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'tools_tab'):
                parent.tools_tab.refresh()
                break
            parent = parent.parent() if parent.parent() else None

    def refresh_labels(self):
        if hasattr(self, '_party_header'):
            self._party_header.setText(t('pal_editor.party') if t else 'PARTY')
        if hasattr(self, 'box_label'):
            self.box_label.setText(t('pal_editor.box', n=self.current_box_index) if t else f'Box {self.current_box_index}')
        if hasattr(self, 'pal_info') and self.pal_info:
            self.pal_info.refresh_labels()
    def _load_pals(self):
        if not constants.loaded_level_json:
            return
        PalFrame._load_maps()
        try:
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        except (KeyError, TypeError) as e:
            print(f'Error accessing CharacterSaveParameterMap: {e}')
            return
        if not cmap:
            return
        self.party_pals = {}
        self.palbox_pal_dict = {}
        target_uid = self.player_uid.replace('-', '').lower() if self.player_uid else ''
        target_party = str(self.party_container).lower() if self.party_container else ''
        target_palbox = str(self.palbox_container).lower() if self.palbox_container else ''
        for item in cmap:
            try:
                raw = item.get('value', {}).get('RawData', {}).get('value', {})
                if not raw:
                    continue
                raw = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
                if not raw:
                    continue
                if 'IsPlayer' in raw:
                    continue
                owner_uid = raw.get('OwnerPlayerUId', {}).get('value')
                owner_uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else ''
                if not owner_uid_str or owner_uid_str != target_uid:
                    continue
                slot_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                slot_id_str = str(slot_id).lower() if slot_id else ''
                slot_index = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                if slot_id_str == target_party:
                    self.party_pals[slot_index] = item
                elif slot_id_str == target_palbox:
                    self.palbox_pal_dict[slot_index] = item
            except (KeyError, TypeError, AttributeError):
                continue
        self._update_party_slots()
        self._update_palbox_page()
    def _update_party_slots(self):
        for slot in self.party_slots:
            slot.pal_data = None
        for idx, pal in self.party_pals.items():
            if 0 <= idx < len(self.party_slots):
                self.party_slots[idx].pal_data = pal
        for slot in self.party_slots:
            slot.update_display()
            slot.set_selected(False)
    def eventFilter(self, obj, event):
        if obj == self.grid_scroll.viewport() and event.type() == QEvent.Type.Wheel:
            if event.angleDelta().y() < 0:
                self._next_box()
            else:
                self._prev_box()
            event.accept()
            return True
        return super().eventFilter(obj, event)
    def closeEvent(self, event):
        super().closeEvent(event)
class EditPalsDialog(FramelessDialog):
    def __init__(self, player_uid, player_name, parent=None):
        super().__init__('edit_pals.title', parent)
        self.player_uid = player_uid
        self.player_name = player_name
        self.set_title_text(f"{t('edit_pals.title')} - {player_name}")
        self.setModal(True)
        self.setMinimumSize(1200, 800)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.pal_editor_widget = PalEditorWidget()
        self.content_layout.addWidget(self.pal_editor_widget)
        self.pal_editor_widget.set_player(player_uid, player_name)
def delete_pal_from_all(pal_id):
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return {'pals_removed': 0, 'affected_count': 0}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd['CharacterSaveParameterMap']['value']
    container_lookup = constants.get_container_lookup()
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    pals_removed = 0
    affected_players = set()
    affected_bases = set()
    container_to_owner = {}
    for entry in cmap:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            owner_uid = sp.get('OwnerPlayerUId', {}).get('value')
            group_id = raw.get('group_id', '')
            slot_data = sp.get('SlotId', {}).get('value', {})
            container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            if container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                if owner_uid and str(owner_uid).replace('-', '').lower() not in ['000000000000000000000000000', '']:
                    container_to_owner[container_id_norm] = {'type': 'player', 'uid': owner_uid}
                elif group_id:
                    container_to_owner[container_id_norm] = {'type': 'base', 'group_id': group_id}
        except:
            continue
    instances_to_remove = []
    for idx, entry in enumerate(cmap):
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            character_id = sp.get('CharacterID', {}).get('value', '')
            if not character_id or character_id.lower() != pal_id.lower():
                continue
            key = entry.get('key', {})
            instance_id = key.get('InstanceId', {}).get('value', '') if hasattr(key, 'get') else ''
            if not instance_id:
                continue
            slot_data = sp.get('SlotId', {}).get('value', {})
            container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            owner_info = None
            if container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                owner_info = container_to_owner.get(container_id_norm)
            instances_to_remove.append((idx, instance_id, owner_info))
        except:
            continue
    for remove_idx, (cmap_idx, instance_id, owner_info) in enumerate(instances_to_remove):
        try:
            if owner_info and container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                container_data = container_lookup.get(container_id_norm)
                if container_data:
                    slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    slots = [s for s in slots if s.get('RawData', {}).get('instance_id', '') != instance_id]
                    container_data['value']['Slots']['value']['values'] = slots
            cmap_entry = cmap[cmap_idx - remove_idx]
            cmap.remove(cmap_entry)
            pals_removed += 1
            if owner_info:
                if owner_info['type'] == 'player':
                    affected_players.add(owner_info['uid'])
                elif owner_info['type'] == 'base':
                    affected_bases.add(owner_info['group_id'])
            if owner_info and owner_info.get('group_id'):
                for group_entry in group_map:
                    g_raw = group_entry.get('value', {}).get('RawData', {}).get('value', {})
                    if g_raw.get('group_id') == owner_info['group_id']:
                        handle_ids = g_raw.get('individual_character_handle_ids', [])
                        handle_ids = [h for h in handle_ids if h.get('instance_id') != instance_id]
                        g_raw['individual_character_handle_ids'] = handle_ids
                        break
        except Exception as e:
            print(f'Error removing pal instance: {e}')
            continue
    constants.invalidate_container_lookup()
    affected_count = len(affected_players) + len(affected_bases)
    return {'pals_removed': pals_removed, 'affected_count': affected_count}
def remove_skill_from_all_pals(active_skill_id=None, passive_skill_id=None):
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return {'skills_removed': 0, 'pals_affected': 0}
    cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
    skills_removed = 0
    pals_affected = 0
    active_skill_full = f'EPalWazaID::{active_skill_id}' if active_skill_id else None
    for entry in cmap:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            pal_skills_removed = 0
            if active_skill_full:
                equip_waza = sp.get('EquipWaza', {})
                if equip_waza:
                    skill_values = equip_waza.get('value', {}).get('values', [])
                    original_count = len(skill_values)
                    skill_values = [s for s in skill_values if s.lower() != active_skill_full.lower()]
                    if len(skill_values) < original_count:
                        equip_waza['value']['values'] = skill_values
                        pal_skills_removed += original_count - len(skill_values)
                mastered_waza = sp.get('MasteredWaza', {})
                if mastered_waza:
                    mastered_values = mastered_waza.get('value', {}).get('values', [])
                    original_mastered = len(mastered_values)
                    mastered_values = [s for s in mastered_values if s.lower() != active_skill_full.lower()]
                    if len(mastered_values) < original_mastered:
                        mastered_waza['value']['values'] = mastered_values
                        pal_skills_removed += original_mastered - len(mastered_values)
            if passive_skill_id:
                passive_list = sp.get('PassiveSkillList', {})
                if passive_list:
                    skill_values = passive_list.get('value', {}).get('values', [])
                    original_count = len(skill_values)
                    skill_values = [s for s in skill_values if s.lower() != passive_skill_id.lower()]
                    if len(skill_values) < original_count:
                        passive_list['value']['values'] = skill_values
                        pal_skills_removed += original_count - len(skill_values)
            if pal_skills_removed > 0:
                skills_removed += pal_skills_removed
                pals_affected += 1
        except Exception as e:
            print(f'Error processing pal for skill removal: {e}')
            continue
    return {'skills_removed': skills_removed, 'pals_affected': pals_affected}
class _PalSlotDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        has_badge = index.data(Qt.UserRole + 1)
        if has_badge:
            badge = _get_boss_alpha_pixmap(14)
            if badge and (not badge.isNull()):
                painter.drawPixmap(option.rect.x() + 6, option.rect.y() + 6, badge)
class PalCreateDialog(QDialog):
    def __init__(self, pal_editor, is_party, slot_index, parent=None):
        super().__init__(parent)
        self.pal_editor = pal_editor
        self.is_party = is_party
        self.slot_index = slot_index
        self.created_item = None
        container_name = t('edit_pals.party') if is_party else t('edit_pals.palbox')
        self.setWindowTitle(f'Create New Pal in {container_name} Slot {slot_index}')
        self.setModal(True)
        self.setMinimumSize(840, 600)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setStyleSheet(DIALOG_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('Search:'))
        search_edit = QLineEdit()
        search_edit.setPlaceholderText('Type to filter pals...')
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        self.pal_list = QListWidget()
        self.pal_list.setViewMode(QListWidget.IconMode)
        self.pal_list.setIconSize(QSize(48, 48))
        self.pal_list.setSpacing(0)
        self.pal_list.setUniformItemSizes(True)
        self.pal_list.setGridSize(QSize(80, 80))
        self.pal_list.setResizeMode(QListWidget.Adjust)
        self.pal_list.setDragEnabled(False)
        self.pal_list.setAcceptDrops(False)
        self.pal_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.pal_list.setMinimumHeight(350)
        self.pal_list.setItemDelegate(_PalSlotDelegate(self.pal_list))
        self.selected_pal = {'asset': None, 'name': None}
        pal_descs = {}
        try:
            base_dir = constants.get_base_path()
            cp = os.path.join(base_dir, 'resources', 'game_data', 'characters.json')
            cd = json_tools.load(cp)
            for p in cd.get('pals', []):
                if isinstance(p, dict) and p.get('description'):
                    pal_descs[p['asset'].lower()] = p['description']
        except:
            pass
        def on_select(item):
            if item:
                self.selected_pal['asset'] = item.data(Qt.UserRole)
                self.selected_pal['name'] = item.text()
        self.pal_list.itemClicked.connect(on_select)
        self.pal_list.itemDoubleClicked.connect(lambda item: (on_select(item), self.accept()))
        for asset, name in sorted(PalFrame._NAMEMAP.items()):
            li = QListWidgetItem(name)
            li.setData(Qt.UserRole, asset)
            pix = _get_cached_pixmap(_get_pal_icon_path(asset), 48)
            if pix:
                li.setIcon(QIcon(pix))
            pdesc = pal_descs.get(asset.lower(), '')
            tip = f'<b>{name}</b><br>ID: {asset}'
            if pdesc:
                tip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(pdesc)}</span>'
            li.setToolTip(tip)
            li.setSizeHint(QSize(80, 80))
            is_variant = any((asset.upper().startswith(p) for p in _BOSS_PREFIXES))
            if is_variant:
                badge = _get_boss_alpha_pixmap(14)
                if badge and (not badge.isNull()):
                    li.setData(Qt.UserRole + 1, True)
            self.pal_list.addItem(li)
        search_edit.textChanged.connect(lambda t: [self.pal_list.item(i).setHidden(t.lower() not in self.pal_list.item(i).text().lower()) for i in range(self.pal_list.count())])
        layout.addWidget(self.pal_list)
        m = layout.contentsMargins()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        self.setFixedWidth(m.left() + m.right() + frame_w + 16 + 24 + 10 * 80)
        nick_layout = QHBoxLayout()
        nick_layout.addWidget(QLabel('Nickname:'))
        self.nick_edit = QLineEdit()
        self.nick_edit.setPlaceholderText('Optional')
        nick_layout.addWidget(self.nick_edit)
        nick_layout.addStretch()
        ok_btn = QPushButton('Create')
        ok_btn.clicked.connect(self._on_create)
        nick_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('edit_pals.cancel'))
        cancel_btn.clicked.connect(self.reject)
        nick_layout.addWidget(cancel_btn)
        layout.addLayout(nick_layout)
    def _on_create(self):
        if not self.selected_pal['asset']:
            show_warning(self, 'Error', t('edit_pals.error_select_pal_type'))
            return
        cid = self.selected_pal['asset']
        nick = self.nick_edit.text().strip() or f"🆕{self.selected_pal['name']}"
        container_id = self.pal_editor.party_container if self.is_party else self.pal_editor.palbox_container
        container_name = t('edit_pals.party') if self.is_party else t('edit_pals.palbox')
        if not container_id:
            show_warning(self, 'Error', 'Container not found.')
            return
        owner_uid = self.pal_editor.player_uid
        group_id = None
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        if 'GroupSaveDataMap' in wsd:
            for g in wsd['GroupSaveDataMap']['value']:
                for p in g['value']['RawData']['value'].get('players', []):
                    if str(p['player_uid']) == owner_uid:
                        group_id = g['value']['RawData']['value']['group_id']
                        break
                if group_id:
                    break
        if not group_id:
            show_warning(self, 'Error', t('edit_pals.error_no_guild'))
            return
        pal_item = _generate_pal_save_param(cid, nick, owner_uid, container_id, self.slot_index, group_id)
        instance_id = pal_item['key']['InstanceId']['value']
        cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        cmap.append(pal_item)
        char_containers = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
        for cont in char_containers:
            if safe_nested_get(cont, ['key', 'ID', 'value']) == container_id:
                slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], [])
                slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': self.slot_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                break
        if 'GroupSaveDataMap' in wsd:
            for g in wsd['GroupSaveDataMap']['value']:
                if g['value']['RawData']['value']['group_id'] == group_id:
                    hids = g['value']['RawData']['value'].get('individual_character_handle_ids', [])
                    hids.append({'guid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id})
                    g['value']['RawData']['value']['individual_character_handle_ids'] = hids
                    break
        if self.is_party:
            self.pal_editor.party_pals[self.slot_index] = pal_item
        else:
            abs_idx = (self.pal_editor.current_box_index - 1) * 30 + self.slot_index
            self.pal_editor.palbox_pal_dict[abs_idx] = pal_item
        self.created_item = {'character_id': cid, 'nickname': nick, 'container_id': container_id, 'slot_index': self.slot_index, 'pal_item': pal_item}
        self.accept()
class PalFrame(QFrame):
    _maps_loaded = False
    _NAMEMAP = {}
    _PASSMAP = {}
    _PASSRANK = {}
    _PASSFLAGS = {}
    _SKILLMAP = {}
    _RANK_COLORS = {-99: ('qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5C1515,stop:0.5 #8A2020,stop:1 #5C1515)', '#7FFF5050', '#FF5555'), 1: ('rgba(255,255,255,0.12)', '#7FFFFFFF', '#FFFFFF'), 2: ('qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5C4033,stop:0.5 #8B6914,stop:1 #5C4033)', '#7FFFD700', '#FFD700'), 4: ('qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D3B66,stop:0.5 #1A6B8A,stop:1 #0D3B66)', '#7F7DD3FC', '#7DD3FC')}
    @classmethod
    def _passive_rank_color(cls, asset_lower):
        rank = cls._PASSRANK.get(asset_lower, 1)
        if rank <= 0:
            return cls._RANK_COLORS[-99]
        if rank >= 4:
            return cls._RANK_COLORS[4]
        if rank >= 2:
            return cls._RANK_COLORS[2]
        return cls._RANK_COLORS[1]
    @classmethod
    def _is_pal_passive(cls, asset_lower):
        flags = cls._PASSFLAGS.get(asset_lower, {})
        if not flags.get('invoke_always', False):
            return False
        if flags.get('category', '') != 'EPalPassiveCategory::SortDisplayable':
            return False
        if flags.get('add_weapon', False) or flags.get('add_armor', False) or flags.get('add_accessory', False):
            return False
        return True
    _maps_loaded_lock = threading.Lock()
    @classmethod
    def _load_maps(cls):
        if cls._maps_loaded:
            return
        with cls._maps_loaded_lock:
            if cls._maps_loaded:
                return
            base_dir = constants.get_base_path()
        def load_map(fname, key):
            try:
                fp = os.path.join(base_dir, 'resources', 'game_data', fname)
                js = json_tools.load(fp)
                if not isinstance(js, dict):
                    return {}
                data = js.get(key, [])
                result = {}
                for x in data:
                    if isinstance(x, dict) and 'asset' in x and ('name' in x):
                        result[x['asset'].lower()] = x['name']
                return result
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {}
        cls._PASSMAP = load_map('skills.json', 'passives')
        cls._SKILLMAP = load_map('skills.json', 'skills')
        PALMAP = load_map('characters.json', 'pals')
        NPCMAP = load_map('characters.json', 'npcs')
        cls._NAMEMAP = {**PALMAP, **NPCMAP}
        cls._PASSFLAGS = {}
        try:
            fp = os.path.join(base_dir, 'resources', 'game_data', 'skills.json')
            js = json_tools.load(fp)
            if isinstance(js, dict):
                data = js.get('passives', [])
                for x in data:
                    if isinstance(x, dict) and 'asset' in x:
                        asset_lower = x['asset'].lower()
                        if 'rank' in x:
                            cls._PASSRANK[asset_lower] = x['rank']
                        cls._PASSFLAGS[asset_lower] = {'add_pal': x.get('add_pal', False), 'add_rare_pal': x.get('add_rare_pal', False), 'add_world_tree_pal': x.get('add_world_tree_pal', False), 'add_mutation_pal': x.get('add_mutation_pal', False), 'add_armor': x.get('add_armor', False), 'add_accessory': x.get('add_accessory', False), 'add_weapon': x.get('add_weapon', False), 'invoke_always': x.get('invoke_always', False), 'category': x.get('category', '')}
        except Exception:
            pass
        cls._PASSMAP = {k: v for k, v in cls._PASSMAP.items() if not any((exc in v.lower() for exc in _SKILL_EXCLUSION_NAMES))}
        cls._PASSMAP = {passive_id: name for passive_id, name in cls._PASSMAP.items() if cls._is_pal_passive(passive_id)}
        cls._maps_loaded = True
    def __init__(self, pal_item, parent=None):
        super().__init__(parent)
        self._load_maps()
        self.pal_item = pal_item
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(400, 150)
        self.setMaximumSize(400, 150)
        self._setup_ui()
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        image_label = QLabel('No Image')
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedSize(80, 80)
        image_label.setStyleSheet('QLabel { border: 2px solid #ccc; border-radius: 40px; background-color: #f0f0f0; padding: 5px; }')
        layout.addWidget(image_label)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        name_label = QLabel('Unknown Pal')
        name_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        right_layout.addWidget(name_label)
        level_exp_layout = QHBoxLayout()
        level_exp_layout.setSpacing(10)
        level_label = QLabel('Level: ?')
        level_label.setStyleSheet('font-size: 12px;')
        level_exp_layout.addWidget(level_label)
        exp_label = QLabel('Exp: ?')
        exp_label.setStyleSheet('font-size: 12px;')
        level_exp_layout.addWidget(exp_label)
        level_exp_layout.addStretch()
        right_layout.addLayout(level_exp_layout)
        stats_label = QLabel('HP: ? ATK: ? DEF: ?')
        stats_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(stats_label)
        moves_label = QLabel('Moves: None')
        moves_label.setWordWrap(True)
        moves_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(moves_label)
        passives_label = QLabel('Passives: None')
        passives_label.setWordWrap(True)
        passives_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(passives_label)
        right_layout.addStretch()
        layout.addLayout(right_layout)
        self.name_label = name_label
        self.level_label = level_label
        self.exp_label = exp_label
        self.stats_label = stats_label
        self.moves_label = moves_label
        self.passives_label = passives_label
        self._load_pal_data()
    def _load_pal_data(self):
        self.update_pal_data(self.pal_item)
    def update_pal_data(self, pal_item):
        self.pal_item = pal_item
        if not pal_item:
            self.name_label.setText('No Pals')
            self.level_label.setText('Level: -')
            self.exp_label.setText('Exp: -')
            self.stats_label.setText('HP: - ATK: - DEF: -')
            self.moves_label.setText('Moves: None')
            self.passives_label.setText('Passives: None')
            return
        try:
            raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            cid = extract_value(raw, 'CharacterID', '')
            character_key = format_character_key(cid)
            level = extract_value(raw, 'Level', 1)
            exp = extract_value(raw, 'Exp', 0)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            rank_attack = extract_value(raw, 'Rank_Attack', 0)
            rank_defense = extract_value(raw, 'Rank_Defence', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            hp = extract_value(raw, 'Hp', 0)
            atk = extract_value(raw, 'Attack', 0)
            defense = extract_value(raw, 'Defense', 0)
            passive_skill_data = raw.get('PassiveSkillList', {})
            if isinstance(passive_skill_data, dict):
                p_list = passive_skill_data.get('value', {}).get('values', [])
            elif isinstance(passive_skill_data, list):
                p_list = passive_skill_data
            nick = extract_value(raw, 'NickName', '')
            pal_name = _strip_prefix_label(resolve_name(cid, self._NAMEMAP) or cid)
            if nick:
                pal_name = nick
            self.name_label.setText(pal_name)
            self.name_label.repaint()
            self.repaint()
            self.level_label.setText(f'Level: {level}')
            self.exp_label.setText(f'Exp: {exp}')
            self.stats_label.setText(f'HP: {hp} ATK: {atk} DEF: {defense}')
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            moves = []
            for w in e_list:
                if w:
                    w_clean = w.split('::')[-1].lower()
                    move_name = self._SKILLMAP.get(w_clean, w.split('::')[-1])
                    moves.append(move_name)
            self.moves_label.setText(f"Moves: {(','.join(moves) if moves else 'None')}")
            passives = [self._PASSMAP.get(p.lower(), p) for p in p_list]
            self.passives_label.setText(f"Passives: {(','.join(passives) if passives else 'None')}")
        except Exception as e:
            pass