import os
import math
from palworld_save_tools import json_tools
import uuid
import threading
from functools import partial
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout, QCheckBox, QFrame, QTabWidget, QScrollArea, QWidget, QGridLayout, QListWidget, QListWidgetItem, QInputDialog, QTableWidget, QApplication, QProgressBar, QAbstractItemView, QCompleter, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QPointF, QEvent, QSize, QRect
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QIcon, QFont, QPixmap, QRegion, QCursor, QPainter, QPainterPath, QPen, QBrush, QFontMetrics, QPalette, QColor, QShortcut, QKeySequence, QLinearGradient
from i18n import t
from loading_manager import show_information, show_warning, show_question
import nerdfont as nf
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, sav_to_gvasfile, gvasfile_to_sav, extract_value, format_character_key, json_to_sav, calculate_max_hp, get_pal_data, safe_dict_get, safe_nested_get, resolve_name

_PAL_STYLESHEET = '''
QWidget#palRoot {
    background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(8,10,16,0.98),stop:0.5 rgba(6,12,20,0.98),stop:1 rgba(4,8,16,0.98));
}
QWidget#partyPanel {
    background: rgba(12,16,24,0.85);
    border: 1px solid rgba(125,211,252,0.15);
    border-radius: 8px;
}
QWidget#partyPanel QLabel {
    color: #C8D8E8;
}
QWidget#palboxPanel {
    background: rgba(12,16,24,0.85);
    border: 1px solid rgba(125,211,252,0.15);
    border-radius: 8px;
}
QWidget#palInfoPanel {
    background: rgba(12,16,24,0.85);
    border: 1px solid rgba(125,211,252,0.15);
    border-radius: 8px;
}
QWidget#palInfoPanel QLabel {
    color: #C8D8E8;
}
QLabel#boxHeader {
    font-size: 18px;
    font-weight: 700;
    color: #7DD3FC;
    padding: 4px 8px;
    background: rgba(125,211,252,0.06);
    border-radius: 4px;
}
QPushButton#navBtn {
    background: rgba(125,211,252,0.08);
    color: #7DD3FC;
    border: 1px solid rgba(125,211,252,0.2);
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 14px;
    font-weight: 600;
    min-width: 32px;
}
QPushButton#navBtn:hover {
    background: rgba(125,211,252,0.18);
    border-color: rgba(125,211,252,0.4);
    color: #FFFFFF;
}
QPushButton#navBtn:pressed {
    background: rgba(125,211,252,0.1);
}
QPushButton#searchBtn {
    background: rgba(167,139,250,0.12);
    color: #A78BFA;
    border: 1px solid rgba(167,139,250,0.2);
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#searchBtn:hover {
    background: rgba(167,139,250,0.22);
    border-color: rgba(167,139,250,0.4);
    color: #FFFFFF;
}
QPushButton#sortBtn {
    background: rgba(245,158,11,0.12);
    color: #F59E0B;
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#sortBtn:hover {
    background: rgba(245,158,11,0.22);
    border-color: rgba(245,158,11,0.4);
    color: #FFFFFF;
}
QLabel#palNameBig {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#levelBanner {
    font-size: 14px;
    font-weight: 700;
    color: #7DD3FC;
    background: rgba(125,211,252,0.1);
    border: 1px solid rgba(125,211,252,0.2);
    border-radius: 4px;
    padding: 4px 12px;
}
QLabel#statLabel {
    font-size: 11px;
    color: #9CA3AF;
    font-weight: 500;
}
QLabel#statValue {
    font-size: 13px;
    color: #E2E8F0;
    font-weight: 600;
}
QLabel#sectionTitle {
    font-size: 12px;
    font-weight: 600;
    color: #7DD3FC;
    padding-bottom: 2px;
    border-bottom: 1px solid rgba(125,211,252,0.15);
}
QFrame#passiveGold {
    background: rgba(255,215,0,0.12);
    border: 1px solid rgba(255,215,0,0.35);
    border-radius: 4px;
    padding: 4px 8px;
}
QFrame#passiveBlue {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.35);
    border-radius: 4px;
    padding: 4px 8px;
}
QFrame#passiveGreen {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 4px;
    padding: 4px 8px;
}
QFrame#passiveWhite {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 4px;
    padding: 4px 8px;
}
'''

def _load_pal_exp_table():
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'pal_exp_table.json')
        return json_tools.load(path)
    except Exception as e:
        print(f'Error loading PAL_EXP_TABLE: {e}')
        return {}

PAL_EXP_TABLE = _load_pal_exp_table()

_PAL_BASE_DATA_CACHE = {}
def _load_pal_base_data():
    if _PAL_BASE_DATA_CACHE:
        return _PAL_BASE_DATA_CACHE
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'paldata.json')
        data = json_tools.load(path)
        for p in data.get('pals', []):
            a = p.get('asset', '').lower()
            if a:
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
        path = QPainterPath()
        font = self.font()
        pen = QPen(Qt.black, 2)
        pen.setJoinStyle(Qt.RoundJoin)
        metrics = QFontMetrics(font)
        x = self.contentsRect().x() + 3
        y = (self.height() + metrics.ascent() - metrics.descent()) // 2
        path.addText(x, y, font, self.text())
        painter.strokePath(path, pen)
        painter.fillPath(path, QBrush(self._text_color))

_ICON_CACHE = {}
_PIXMAP_CACHE = {}
_CACHE_LOCK = threading.Lock()

def _lookup_icon_in_data(asset_name: str, base_dir: str) -> str | None:
    try:
        paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'paldata.json')
        paldata = json_tools.load(paldata_path)
        for pal in paldata.get('pals', []):
            if pal.get('asset', '').lower() == asset_name:
                icon_rel = pal.get('icon', '')
                if icon_rel:
                    return os.path.join(base_dir, 'resources', 'game_data', icon_rel.lstrip('/'))
    except Exception:
        pass
    try:
        npcdata_path = os.path.join(base_dir, 'resources', 'game_data', 'npcdata.json')
        npcdata = json_tools.load(npcdata_path)
        for npc in npcdata.get('npcs', []):
            if npc.get('asset', '').lower() == asset_name:
                icon_rel = npc.get('icon', '')
                if icon_rel:
                    return os.path.join(base_dir, 'resources', 'game_data', icon_rel.lstrip('/'))
    except Exception:
        pass
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
        pal_name = resolve_name(cid, PalFrame._NAMEMAP) or cid
        if nick:
            pal_name = f'{nick}'
        self.setToolTip(f'{pal_name} [Lv.{level}]')
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
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setObjectName('editPalsContextMenu')
        if self.pal_data:
            delete_action = menu.addAction(t('edit_pals.delete'))
            action = menu.exec(event.globalPos())
            if action == delete_action:
                self.rightClicked.emit(self.slot_index, 'delete')
        else:
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
        pal_name = resolve_name(cid, PalFrame._NAMEMAP) or cid
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
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._build()
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
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setObjectName('editPalsContextMenu')
        if self.pal_data:
            delete_action = menu.addAction(t('edit_pals.delete'))
            action = menu.exec(event.globalPos())
            if action == delete_action:
                self.rightClicked.emit(self.slot_index, 'delete')
        else:
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
        for child in self.findChildren(QWidget):
            child.deleteLater()
        raw = self._get_raw()
        if not raw or not isinstance(raw, dict):
            self.setStyleSheet('QFrame#partySlot { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; }')
            return
        cid = extract_value(raw, 'CharacterID', '')
        level = extract_value(raw, 'Level', 1)
        nick = extract_value(raw, 'NickName', '')
        hp = extract_value(raw, 'Hp', 0)
        max_hp = extract_value(raw, 'MaxHp', hp)
        if max_hp <= 0:
            max_hp = hp if hp > 0 else 100
        exp = extract_value(raw, 'Exp', 0)
        pal_name = resolve_name(cid, PalFrame._NAMEMAP) or cid
        if nick:
            pal_name = f'{nick}'
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
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
        info = QVBoxLayout()
        info.setSpacing(1)
        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        name_lbl = QLabel(f'Lv.{level} {pal_name}')
        name_lbl.setStyleSheet('color: #E2E8F0; font-size: 12px; font-weight: 600; background: transparent;')
        name_row.addWidget(name_lbl)
        if is_boss:
            boss_badge = QLabel('\u03b1')
            boss_badge.setStyleSheet('color: #F59E0B; font-size: 11px; font-weight: bold; background: rgba(245,158,11,0.15); border-radius: 3px; padding: 0 4px;')
            name_row.addWidget(boss_badge)
        elif is_lucky:
            lucky_badge = QLabel('\u2606')
            lucky_badge.setStyleSheet('color: #A78BFA; font-size: 12px; font-weight: bold; background: rgba(167,139,250,0.15); border-radius: 3px; padding: 0 4px;')
            name_row.addWidget(lucky_badge)
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
        lock_btn = QPushButton('🔓')
        lock_btn.setFixedSize(20, 20)
        lock_btn.setStyleSheet('QPushButton { background: transparent; border: none; font-size: 12px; color: rgba(255,255,255,0.3); } QPushButton:hover { color: #FFFFFF; }')
        lock_btn.setCheckable(True)
        name_row.addWidget(lock_btn)
        info.addLayout(name_row)
        hp_bar = QFrame()
        hp_bar.setFixedHeight(6)
        hp_ratio = hp / max_hp if max_hp > 0 else 0
        hp_bar.setStyleSheet('background: rgba(55,65,81,0.5); border-radius: 3px; border: 1px solid rgba(16,185,129,0.15);')
        hp_fill = QFrame(hp_bar)
        hp_fill.setFixedHeight(4)
        hp_fill.setFixedWidth(int(max(4, hp_ratio * 180)))
        hp_fill.move(1, 1)
        hp_fill.setStyleSheet('background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 2px;')
        info.addWidget(hp_bar)
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
        self.setFixedSize(56, 56)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._build()
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
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setObjectName('editPalsContextMenu')
        if self.pal_data:
            delete_action = menu.addAction(t('edit_pals.delete'))
            action = menu.exec(event.globalPos())
            if action == delete_action:
                self.rightClicked.emit(self.slot_index, 'delete')
        else:
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
        for child in self.findChildren(QWidget):
            child.deleteLater()
        raw = self._get_raw()
        if not raw or not isinstance(raw, dict):
            self.setStyleSheet('QFrame#palboxSlot { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 4px; }')
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
        icon_lbl.move(9, 4)
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_lbl.show()
        self._elem_badge = QLabel(self)
        self._elem_badge.setFixedSize(10, 10)
        self._elem_badge.move(44, 2)
        self._elem_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        base_el_data = get_pal_base_data(cid)
        if base_el_data:
            els = base_el_data.get('elements', {})
            if els:
                en = next(iter(els))
                ep = _get_element_pixmap(en, 'small', 10)
                if ep:
                    self._elem_badge.setPixmap(ep)
        self._elem_badge.show()
        level_lbl = StrokedLabel(f'{level}')
        level_lbl.setStyleSheet('color: #FFFFFF; font-size: 8px; font-weight: bold; background: transparent;')
        level_lbl.setFixedSize(16, 10)
        level_lbl.move(3, 44)
        level_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        level_lbl.show()
        if is_boss:
            badge = QLabel('α', self)
            badge.setStyleSheet('color: #F59E0B; font-size: 10px; font-weight: bold; background: rgba(0,0,0,0.6); border: 1px solid rgba(245,158,11,0.3); border-radius: 7px;')
            badge.setFixedSize(14, 14)
            badge.setAlignment(Qt.AlignCenter)
            badge.move(3, 3)
            badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            badge.show()
        elif is_lucky:
            badge = QLabel('☆', self)
            badge.setStyleSheet('color: #A78BFA; font-size: 10px; font-weight: bold; background: rgba(0,0,0,0.6); border: 1px solid rgba(167,139,250,0.3); border-radius: 7px;')
            badge.setFixedSize(14, 14)
            badge.setAlignment(Qt.AlignCenter)
            badge.move(3, 3)
            badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            badge.show()
        if is_awake:
            awake_badge = QLabel('🔥', self)
            awake_badge.setStyleSheet('font-size: 9px; background: transparent;')
            awake_badge.setFixedSize(12, 12)
            awake_badge.setAlignment(Qt.AlignCenter)
            awake_badge.move(42, 40)
            awake_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            awake_badge.show()
        pal_name = resolve_name(cid, PalFrame._NAMEMAP) or cid
        self.setToolTip(f'{pal_name} [Lv.{level}]')
        self.setStyleSheet('QFrame#palboxSlot { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; } QFrame#palboxSlot:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('QFrame#palboxSlot { background: rgba(125,211,252,0.1); border: 2px solid #7DD3FC; border-radius: 6px; }')
        else:
            self.setStyleSheet('QFrame#palboxSlot { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; } QFrame#palboxSlot:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
    def update_display(self):
        self._build()

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
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(r.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (r.width() - scaled.width()) // 2
            y = (r.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillPath(path, QBrush(QColor(30, 35, 45)))
            painter.setPen(QPen(QColor(100, 110, 130), 1))
            painter.setFont(QFont('Segoe UI', 16))
            painter.drawText(r, Qt.AlignCenter, '?')

_SKILL_DATA = None
_ELEMENT_DATA = None

def _ensure_element_data():
    global _ELEMENT_DATA
    if _ELEMENT_DATA is not None:
        return _ELEMENT_DATA
    _ELEMENT_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = os.path.join(base_dir, 'resources', 'game_data', 'elementdata.json')
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
        path = os.path.join(base_dir, 'resources', 'game_data', 'skilldata.json')
        js = json_tools.load(path)
        for s in js.get('skills', []):
            if isinstance(s, dict) and 'asset' in s:
                _SKILL_DATA[s['asset'].lower()] = s
    except Exception:
        pass

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
        w, h = self.width(), self.height()
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
        w, h = self.width(), self.height()
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
        w, h = self.width(), self.height()
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
        w, h = self.width(), self.height()
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
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
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

class PalInfoWidget(QFrame):
    _ELEMENT_MAP = {
        'Normal': ('\u26AA', '#9CA3AF'), 'Fire': ('\U0001F525', '#EF4444'),
        'Water': ('\U0001F4A7', '#3B82F6'), 'Leaf': ('\U0001F33F', '#4ADE80'),
        'Grass': ('\U0001F33F', '#4ADE80'), 'Electricity': ('\u26A1', '#FBBF24'),
        'Electric': ('\u26A1', '#FBBF24'), 'Ice': ('\u2744\uFE0F', '#67E8F9'),
        'Earth': ('\U0001FAA8', '#A78BFA'), 'Ground': ('\U0001FAA8', '#A78BFA'),
        'Dark': ('\U0001F311', '#6B21A8'), 'Dragon': ('\U0001F409', '#818CF8'),
    }
    _ELEMENT_COLORS = {
        'Normal': '#9CA3AF', 'Fire': '#EF4444', 'Water': '#3B82F6',
        'Leaf': '#4ADE80', 'Grass': '#4ADE80', 'Electricity': '#FBBF24',
        'Electric': '#FBBF24', 'Ice': '#67E8F9', 'Earth': '#A78BFA',
        'Ground': '#A78BFA', 'Dark': '#6B21A8', 'Dragon': '#818CF8',
    }
    _TRUST_RANK_THRESHOLDS = [0, 1, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]
    NATIVE_WORK_ORDER = ('EmitFlame', 'Watering', 'Seeding', 'GenerateElectricity', 'Handcraft', 'Collection', 'Deforest', 'Mining', 'ProductMedicine', 'Cool', 'Transport', 'MonsterFarm')
    _WORK_SUITABILITY_DISPLAY = {'EmitFlame': 'Kindling', 'Watering': 'Watering', 'Seeding': 'Seeding', 'GenerateElectricity': 'Electricity', 'Handcraft': 'Handiwork', 'Collection': 'Harvesting', 'Deforest': 'Lumbering', 'Mining': 'Mining', 'ProductMedicine': 'Medicine', 'Cool': 'Cooling', 'Transport': 'Transport', 'MonsterFarm': 'Farming'}
    _WORK_SUITABILITY_ICON_KEYS = ['palwork_00', 'palwork_01', 'palwork_02', 'palwork_03', 'palwork_04', 'palwork_05', 'palwork_06', 'palwork_07', 'palwork_08', 'palwork_10', 'palwork_11', 'palwork_12']
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pal = None
        self.last_clicked_data = None
        self._hovered_data = None
        self.setObjectName('palInfoPanel')
        self._build()
    def set_hover_pal(self, pal_data):
        self._hovered_data = pal_data
        self._update_stack_state()
        if pal_data is not None:
            self._update_display(pal_data)
    def set_clicked_pal(self, pal_data):
        self.last_clicked_data = pal_data
        self._update_stack_state()
        if pal_data is not None:
            self._update_display(pal_data)
    def clear_hover(self):
        self._hovered_data = None
        self._update_stack_state()
        if self.last_clicked_data is not None:
            self._update_display(self.last_clicked_data)
        else:
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
        self.san_bar.setFormat('--%')
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
        gender_def = _get_ui_icon_pixmap('gender_female', 14)
        if gender_def:
            self.gender_icon.setPixmap(gender_def)
        self.gender_icon.setStyleSheet('background: transparent; border-radius: 8px; border: 1px solid rgba(251,113,133,0.2);')
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
        self.partner_desc_lbl.setText('--')
        for i in reversed(range(self.active_skills_list.count())):
            w = self.active_skills_list.itemAt(i)
            if w and w.widget():
                w.widget().deleteLater()
        for s in self.passive_slots:
            s.setText('--')
            s.setStyleSheet('font-size: 9px; font-weight: 700; color: rgba(255,255,255,0.3); background: transparent; border: none;')
            parent_frame = s.parentWidget()
            if parent_frame and parent_frame.objectName() == 'passiveCard':
                parent_frame.setStyleSheet('QFrame#passiveCard { background: rgba(255,255,255,0.03); border: none; border-radius: 4px; }')
        self.star_rating.setText('\u2606\u2606\u2606\u2606')
        self.stat_plus_lbl.setText('--')
        self.portrait_icon.clear()
        self.dna_overlay.hide()
        self.lock_overlay.hide()
        self.portrait_ring.set_awakened(False)
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        scroll = QScrollArea()
        self._data_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 4px; background: rgba(255,255,255,0.02); border-radius: 2px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.15); border-radius: 2px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.3); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }')
        inner = QWidget()
        inner.setObjectName('palInfoInner')
        inner.setStyleSheet('QWidget#palInfoInner { background: rgba(8,10,16,0.98); border: 1px solid rgba(30,40,55,0.9); border-radius: 6px; }')
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(6, 4, 6, 6)
        inner_layout.setSpacing(3)
        self._build_header(inner_layout)
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setStyleSheet('background: rgba(255,90,158,0.35); border: none; max-height: 1px;')
        inner_layout.addWidget(hline)
        self._build_body(inner_layout)
        hline2 = QFrame()
        hline2.setFrameShape(QFrame.HLine)
        hline2.setStyleSheet('background: rgba(125,211,252,0.08); border: none; max-height: 1px;')
        inner_layout.addWidget(hline2)
        self._build_suitability_food(inner_layout)
        hline3 = QFrame()
        hline3.setFrameShape(QFrame.HLine)
        hline3.setStyleSheet('background: rgba(125,211,252,0.08); border: none; max-height: 1px;')
        inner_layout.addWidget(hline3)
        self._build_skills(inner_layout)
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        self._no_data_overlay = QLabel('No Pal Data', self)
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
        self.partner_frame.setVisible(not self._showing_active_skills)
        self.active_skills_frame.setVisible(self._showing_active_skills)
    def _build_header(self, parent):
        header = QWidget()
        header.setStyleSheet('background: transparent; border: none;')
        hrow = QHBoxLayout()
        hrow.setContentsMargins(0, 0, 0, 0)
        hrow.setSpacing(6)
        level_box = CornerBracketWidget('#7DD3FC')
        lv_layout = QVBoxLayout(level_box)
        lv_layout.setContentsMargins(4, 5, 4, 4)
        lv_layout.setSpacing(0)
        lv_label = QLabel('LEVEL')
        lv_label.setAlignment(Qt.AlignCenter)
        lv_label.setStyleSheet('font-size: 7px; font-weight: 600; color: #7DD3FC; letter-spacing: 3px; background: transparent; border: none;')
        lv_layout.addWidget(lv_label)
        self.level_num_lbl = QLabel('80')
        self.level_num_lbl.setAlignment(Qt.AlignCenter)
        self.level_num_lbl.setStyleSheet('font-size: 26px; font-weight: 800; color: #FFFFFF; background: transparent; border: none;')
        lv_layout.addWidget(self.level_num_lbl)
        hrow.addWidget(level_box)
        name_col = QWidget()
        name_col.setStyleSheet('background: transparent; border: none;')
        nc_layout = QVBoxLayout(name_col)
        nc_layout.setContentsMargins(0, 0, 0, 0)
        nc_layout.setSpacing(0)
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(4)
        self.name_lbl = QLabel('Gobfinned')
        self.name_lbl.setStyleSheet('font-size: 14px; font-weight: 700; color: #FFFFFF; background: transparent; border: none;')
        name_row.addWidget(self.name_lbl)
        self.gender_icon = QLabel()
        self.gender_icon.setFixedSize(16, 16)
        self.gender_icon.setAlignment(Qt.AlignCenter)
        self.gender_icon.setAttribute(Qt.WA_TranslucentBackground)
        gender_def = _get_ui_icon_pixmap('gender_female', 14)
        if gender_def:
            self.gender_icon.setPixmap(gender_def)
        self.gender_icon.setStyleSheet('background: transparent; border-radius: 8px; border: 1px solid rgba(251,113,133,0.2);')
        name_row.addWidget(self.gender_icon)
        self.type_icons_container = QWidget()
        self.type_icons_container.setStyleSheet('background: transparent; border: none;')
        self.type_icons_layout = QHBoxLayout(self.type_icons_container)
        self.type_icons_layout.setContentsMargins(0, 0, 0, 0)
        self.type_icons_layout.setSpacing(2)
        self.type_icons_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_row.addWidget(self.type_icons_container)
        name_row.addStretch()
        nc_layout.addLayout(name_row)
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
        nc_layout.addLayout(next_row)
        hrow.addWidget(name_col, 1)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)
        header_layout.addLayout(hrow)
        self.exp_header_bar = QProgressBar()
        self.exp_header_bar.setFixedHeight(3)
        self.exp_header_bar.setRange(0, 100)
        self.exp_header_bar.setValue(0)
        self.exp_header_bar.setTextVisible(False)
        self.exp_header_bar.setStyleSheet('QProgressBar { background: rgba(40,30,40,0.4); border: none; border-radius: 1px; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #EC4899,stop:1 #F472B6); border-radius: 1px; }')
        header_layout.addWidget(self.exp_header_bar)
        parent.addWidget(header)
    def _build_body(self, parent):
        body = QWidget()
        body.setStyleSheet('background: transparent; border: none;')
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)
        left_col = QWidget()
        left_col.setStyleSheet('background: transparent; border: none;')
        left_col.setFixedWidth(112)
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(1)
        self.star_rating = QLabel('\u2605\u2605\u2605\u2605')
        self.star_rating.setAlignment(Qt.AlignCenter)
        self.star_rating.setStyleSheet('font-size: 13px; color: #FFD700; letter-spacing: 2px; background: transparent; border: none;')
        left_layout.addWidget(self.star_rating)
        portrait_frame = QFrame()
        portrait_frame.setFixedSize(104, 104)
        portrait_frame.setObjectName('portraitGlow')
        portrait_frame.setStyleSheet('QFrame#portraitGlow { background: qradialgradient(cx:0.5,cy:0.5,radius:0.6,fx:0.5,fy:0.5,stop:0 rgba(125,211,252,0.12),stop:0.4 rgba(125,211,252,0.04),stop:1 transparent); border: none; border-radius: 52px; }')
        pf_layout = QVBoxLayout(portrait_frame)
        pf_layout.setContentsMargins(4, 4, 4, 4)
        pf_layout.setAlignment(Qt.AlignCenter)
        self.bracket_wrapper = PortraitBracketWidget()
        self.bracket_wrapper.setFixedSize(96, 96)
        bw_layout = QVBoxLayout(self.bracket_wrapper)
        bw_layout.setContentsMargins(2, 2, 2, 2)
        bw_layout.setAlignment(Qt.AlignCenter)
        self.portrait_ring = GlowRing()
        self.portrait_ring.setFixedSize(88, 88)
        ring_layout = QVBoxLayout(self.portrait_ring)
        ring_layout.setContentsMargins(0, 0, 0, 0)
        self.portrait_icon = _CircularIcon(80)
        ring_layout.addWidget(self.portrait_icon, 0, Qt.AlignCenter)
        bw_layout.addWidget(self.portrait_ring, 0, Qt.AlignCenter)
        self.dna_overlay = QLabel(self.bracket_wrapper)
        self.dna_overlay.setFixedSize(16, 16)
        self.dna_overlay.setAlignment(Qt.AlignCenter)
        self.dna_overlay.setAttribute(Qt.WA_TranslucentBackground)
        dna_pix = _get_ui_icon_pixmap('dna', 14)
        if dna_pix:
            self.dna_overlay.setPixmap(dna_pix)
        self.dna_overlay.setStyleSheet('background: transparent; border: none;')
        self.dna_overlay.move(6, 74)
        self.dna_overlay.hide()
        self.lock_overlay = QLabel(self.bracket_wrapper)
        self.lock_overlay.setFixedSize(16, 16)
        self.lock_overlay.setAlignment(Qt.AlignCenter)
        self.lock_overlay.setStyleSheet('font-size: 9px; color: rgba(255,255,255,0.65); background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;')
        self.lock_overlay.setText('\U0001F512')
        self.lock_overlay.move(74, 6)
        self.lock_overlay.hide()
        pf_layout.addWidget(self.bracket_wrapper, 0, Qt.AlignCenter)
        left_layout.addWidget(portrait_frame, 0, Qt.AlignCenter)
        self.stat_plus_lbl = QLabel('+60')
        self.stat_plus_lbl.setAlignment(Qt.AlignCenter)
        self.stat_plus_lbl.setStyleSheet('font-size: 12px; font-weight: 700; color: #7DD3FC; background: transparent; border: none;')
        left_layout.addWidget(self.stat_plus_lbl)
        body_layout.addWidget(left_col)
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
        trust_pix = _get_ui_icon_pixmap('friendship', 12)
        if trust_pix:
            trust_icon.setPixmap(trust_pix)
        trust_row.addWidget(trust_icon)
        self.trust_bar = QProgressBar()
        self.trust_bar.setFixedHeight(14)
        self.trust_bar.setRange(0, 100)
        self.trust_bar.setValue(0)
        self.trust_bar.setTextVisible(True)
        self.trust_bar.setStyleSheet('QProgressBar { background: rgba(30,20,25,0.6); border: 1px solid rgba(244,114,182,0.20); border-radius: 3px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #EC4899,stop:1 #F472B6); border-radius: 2px; }')
        trust_row.addWidget(self.trust_bar, 1)
        right_layout.addLayout(trust_row)
        hp_row = QHBoxLayout()
        hp_row.setSpacing(0)
        hp_icon = QLabel('\u2665')
        hp_icon.setFixedSize(14, 14)
        hp_icon.setAlignment(Qt.AlignCenter)
        hp_icon.setStyleSheet('font-size: 9px; color: #EF4444; background: transparent; border: none;')
        hp_row.addWidget(hp_icon)
        self.hp_bar = QProgressBar()
        self.hp_bar.setFixedHeight(14)
        self.hp_bar.setRange(0, 100)
        self.hp_bar.setValue(100)
        self.hp_bar.setTextVisible(True)
        self.hp_bar.setStyleSheet('QProgressBar { background: rgba(20,40,30,0.6); border: 1px solid rgba(16,185,129,0.2); border-radius: 3px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 2px; }')
        hp_row.addWidget(self.hp_bar, 1)
        right_layout.addLayout(hp_row)
        hunger_row = QHBoxLayout()
        hunger_row.setSpacing(0)
        hunger_icon = QLabel('\u26ac')
        hunger_icon.setFixedSize(14, 14)
        hunger_icon.setAlignment(Qt.AlignCenter)
        hunger_icon.setStyleSheet('font-size: 9px; color: #F59E0B; background: transparent; border: none;')
        hunger_row.addWidget(hunger_icon)
        self.hunger_bar = QProgressBar()
        self.hunger_bar.setFixedHeight(14)
        self.hunger_bar.setRange(0, 100)
        self.hunger_bar.setValue(53)
        self.hunger_bar.setTextVisible(True)
        self.hunger_bar.setStyleSheet('QProgressBar { background: rgba(40,30,20,0.6); border: 1px solid rgba(245,158,11,0.2); border-radius: 3px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #F59E0B,stop:1 #FBBF24); border-radius: 2px; }')
        hunger_row.addWidget(self.hunger_bar, 1)
        right_layout.addLayout(hunger_row)
        san_row = QHBoxLayout()
        san_row.setSpacing(0)
        san_icon = QLabel('\u2726')
        san_icon.setFixedSize(14, 14)
        san_icon.setAlignment(Qt.AlignCenter)
        san_icon.setStyleSheet('font-size: 9px; color: #10B981; background: transparent; border: none;')
        san_row.addWidget(san_icon)
        self.san_bar = QProgressBar()
        self.san_bar.setFixedHeight(14)
        self.san_bar.setRange(0, 100)
        self.san_bar.setValue(100)
        self.san_bar.setTextVisible(True)
        self.san_bar.setStyleSheet('QProgressBar { background: rgba(20,30,40,0.6); border: 1px solid rgba(56,189,248,0.2); border-radius: 3px; text-align: center; font-size: 7px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #38BDF8,stop:1 #7DD3FC); border-radius: 2px; }')
        san_row.addWidget(self.san_bar, 1)
        right_layout.addLayout(san_row)
        stats_q = QFrame()
        stats_q.setStyleSheet('background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 3px;')
        stats_grid = QGridLayout(stats_q)
        stats_grid.setContentsMargins(4, 2, 4, 2)
        stats_grid.setSpacing(1)
        atk_icon = QLabel('\u2694')
        atk_icon.setFixedSize(14, 14)
        atk_icon.setAlignment(Qt.AlignCenter)
        atk_icon.setStyleSheet('font-size: 10px; color: #EF4444; background: transparent; border: none;')
        stats_grid.addWidget(atk_icon, 0, 0, Qt.AlignVCenter)
        atk_label = QLabel('Attack')
        atk_label.setStyleSheet('font-size: 9px; color: #9CA3AF; background: transparent; border: none;')
        stats_grid.addWidget(atk_label, 0, 1, Qt.AlignVCenter)
        self.atk_lbl = QLabel('3599')
        self.atk_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.atk_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        stats_grid.addWidget(self.atk_lbl, 0, 2, Qt.AlignVCenter)
        def_icon = QLabel('\u2696')
        def_icon.setFixedSize(14, 14)
        def_icon.setAlignment(Qt.AlignCenter)
        def_icon.setStyleSheet('font-size: 10px; color: #3B82F6; background: transparent; border: none;')
        stats_grid.addWidget(def_icon, 1, 0, Qt.AlignVCenter)
        def_label = QLabel('Defense')
        def_label.setStyleSheet('font-size: 9px; color: #9CA3AF; background: transparent; border: none;')
        stats_grid.addWidget(def_label, 1, 1, Qt.AlignVCenter)
        self.def_lbl = QLabel('2791')
        self.def_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.def_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        stats_grid.addWidget(self.def_lbl, 1, 2, Qt.AlignVCenter)
        wspd_icon = QLabel('\u2692')
        wspd_icon.setFixedSize(14, 14)
        wspd_icon.setAlignment(Qt.AlignCenter)
        wspd_icon.setStyleSheet('font-size: 10px; color: #A78BFA; background: transparent; border: none;')
        stats_grid.addWidget(wspd_icon, 2, 0, Qt.AlignVCenter)
        wspd_label = QLabel('Work Speed')
        wspd_label.setStyleSheet('font-size: 9px; color: #9CA3AF; background: transparent; border: none;')
        stats_grid.addWidget(wspd_label, 2, 1, Qt.AlignVCenter)
        self.wspd_lbl = QLabel('127')
        self.wspd_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.wspd_lbl.setStyleSheet('font-size: 10px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        stats_grid.addWidget(self.wspd_lbl, 2, 2, Qt.AlignVCenter)
        right_layout.addWidget(stats_q)
        body_layout.addWidget(right_col, 1)
        parent.addWidget(body)
    def _build_suitability_food(self, parent):
        card = QFrame()
        card.setObjectName('suitFoodCard')
        card.setStyleSheet('QFrame#suitFoodCard { background: rgba(255,255,255,0.02); border: 1px solid rgba(125,211,252,0.1); border-radius: 4px; }')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(6, 3, 6, 3)
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
        hline_food = QFrame()
        hline_food.setFrameShape(QFrame.HLine)
        hline_food.setStyleSheet('background: rgba(125,211,252,0.06); border: none; max-height: 1px;')
        card_layout.addWidget(hline_food)
        food_row = QHBoxLayout()
        food_row.setSpacing(2)
        food_title = QLabel('Food')
        food_title.setStyleSheet('font-size: 8px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        food_row.addWidget(food_title)
        food_row.addSpacing(2)
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
        food_row.addStretch()
        card_layout.addLayout(food_row)
        parent.addWidget(card)
    def _build_skills(self, parent):
        skill_outer = QWidget()
        skill_outer.setStyleSheet('background: transparent; border: none;')
        so_layout = QVBoxLayout(skill_outer)
        so_layout.setContentsMargins(0, 0, 0, 0)
        so_layout.setSpacing(2)
        self.partner_frame = QFrame()
        self.partner_frame.setObjectName('partnerBox')
        self.partner_frame.setStyleSheet('QFrame#partnerBox { background: rgba(10,16,24,0.95); border: 1.5px solid rgba(125,211,252,0.3); border-radius: 5px; }')
        partner_layout = QVBoxLayout(self.partner_frame)
        partner_layout.setContentsMargins(6, 4, 6, 4)
        partner_layout.setSpacing(2)
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
        bracket_frame = QFrame()
        bracket_frame.setStyleSheet('background: transparent; border: none;')
        bracket_layout = QHBoxLayout(bracket_frame)
        bracket_layout.setContentsMargins(0, 0, 0, 0)
        bracket_layout.setSpacing(0)
        bracket_l = QLabel('\u276c')
        bracket_l.setStyleSheet('font-size: 14px; font-weight: 100; color: rgba(125,211,252,0.25); background: transparent; border: none;')
        bracket_layout.addWidget(bracket_l)
        self.partner_desc_lbl = QLabel('Fires a barrage of missiles at nearby enemies, dealing massive damage and knocking them back.')
        self.partner_desc_lbl.setWordWrap(True)
        self.partner_desc_lbl.setStyleSheet('font-size: 8px; color: #9CA3AF; background: transparent; border: none; padding: 0 2px;')
        bracket_layout.addWidget(self.partner_desc_lbl, 1)
        bracket_r = QLabel('\u276d')
        bracket_r.setStyleSheet('font-size: 14px; font-weight: 100; color: rgba(125,211,252,0.25); background: transparent; border: none;')
        bracket_layout.addWidget(bracket_r)
        partner_layout.addWidget(bracket_frame)
        self.active_skills_frame = QFrame()
        self.active_skills_frame.setObjectName('activeSkillsBox')
        self.active_skills_frame.setStyleSheet('QFrame#activeSkillsBox { background: rgba(10,16,24,0.95); border: 1.5px solid rgba(125,211,252,0.3); border-radius: 5px; }')
        as_layout = QVBoxLayout(self.active_skills_frame)
        as_layout.setContentsMargins(10, 6, 10, 6)
        as_layout.setSpacing(3)
        as_header = QHBoxLayout()
        as_header.setSpacing(4)
        as_title = QLabel('Active Skills')
        as_title.setStyleSheet('font-size: 10px; font-weight: 700; color: #7DD3FC; background: transparent; border: none;')
        as_header.addWidget(as_title)
        as_header.addStretch()
        as_c_icon = QLabel('[C]')
        as_c_icon.setFixedSize(22, 16)
        as_c_icon.setAlignment(Qt.AlignCenter)
        as_c_icon.setStyleSheet('font-size: 8px; font-weight: 700; color: #7DD3FC; background: rgba(125,211,252,0.08); border: 1px solid rgba(125,211,252,0.2); border-radius: 3px;')
        as_header.addWidget(as_c_icon)
        as_layout.addLayout(as_header)
        self.active_skills_list = QVBoxLayout()
        self.active_skills_list.setContentsMargins(0, 0, 0, 0)
        self.active_skills_list.setSpacing(2)
        as_layout.addLayout(self.active_skills_list)
        so_layout.addWidget(self.active_skills_frame)
        so_layout.addWidget(self.partner_frame)
        self.partner_frame.hide()
        passive_title = QLabel('Passive Skills')
        passive_title.setStyleSheet('font-size: 9px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding-top: 2px;')
        so_layout.addWidget(passive_title)
        pg = QWidget()
        pg.setStyleSheet('background: transparent; border: none;')
        pg_layout = QGridLayout(pg)
        pg_layout.setContentsMargins(0, 0, 0, 0)
        pg_layout.setSpacing(3)
        passive_tiers = [
            ('Runner', 'gold', 'rgba(139,105,20,0.25)'),
            ('Swift', 'legendary', 'rgba(26,107,138,0.25)'),
            ('Legend', 'legendary', 'rgba(26,107,138,0.25)'),
            ('Surge of the World Tree', 'legendary', 'rgba(26,107,138,0.25)'),
        ]
        self.passive_slots = []
        for i, (pname, ptier, bg_fill) in enumerate(passive_tiers):
            card = QFrame()
            card.setObjectName('passiveCard')
            txt_color = '#FFD700' if ptier == 'gold' else '#7DD3FC'
            card.setStyleSheet(f'QFrame#passiveCard {{ background: {bg_fill}; border: none; border-radius: 4px; }}')
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(4, 2, 4, 2)
            card_layout.setSpacing(2)
            plbl = QLabel(pname)
            plbl.setStyleSheet(f'font-size: 9px; font-weight: 700; color: {txt_color}; background: transparent; border: none;')
            card_layout.addWidget(plbl, 1)
            chev = QLabel('\u276f\u276f\u276f')
            chev.setStyleSheet(f'font-size: 6px; color: rgba(255,255,255,0.15); background: transparent; border: none; letter-spacing: -1px;')
            card_layout.addWidget(chev)
            row, col = i // 2, i % 2
            pg_layout.addWidget(card, row, col)
            self.passive_slots.append(plbl)
        so_layout.addWidget(pg)
        parent.addWidget(skill_outer)
    def _update_display(self, pal_data):
        try:
            if 'data' in pal_data:
                raw = pal_data['data']
            elif 'value' in pal_data:
                raw = safe_nested_get(pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            else:
                raw = pal_data
            if not isinstance(raw, dict):
                self._clear_display()
                return
            _ensure_skill_data()
            cid = extract_value(raw, 'CharacterID', '')
            level = extract_value(raw, 'Level', 1)
            nick = extract_value(raw, 'NickName', '')
            pal_name = resolve_name(cid, PalFrame._NAMEMAP) or cid
            if nick:
                pal_name = f'{nick} ({pal_name})'
            self.name_lbl.setText(pal_name)
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
            gender_pix = _get_ui_icon_pixmap(gender_key, 14)
            if gender_pix:
                self.gender_icon.setPixmap(gender_pix)
            self.gender_icon.setStyleSheet(f'background: transparent; border-radius: 8px; border: 1px solid {gender_color}40;')
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
                        elem_color = self._ELEMENT_MAP.get(elem_name, ('\u2606', '#A78BFA'))[1]
                        if elem_pix:
                            badge = QLabel()
                            badge.setFixedSize(16, 16)
                            badge.setAlignment(Qt.AlignCenter)
                            badge.setPixmap(elem_pix)
                            badge.setStyleSheet(f'background: transparent; border: 1px solid {elem_color}40; border-radius: 8px;')
                            badge.setAttribute(Qt.WA_TranslucentBackground)
                        else:
                            elem_data = self._ELEMENT_MAP.get(elem_name, ('\u2606', '#A78BFA'))
                            badge = QLabel(elem_data[0])
                            badge.setFixedSize(16, 16)
                            badge.setAlignment(Qt.AlignCenter)
                            badge.setStyleSheet(f'font-size: 11px; font-weight: bold; color: {elem_color}; background: transparent; border: 1px solid {elem_color}40; border-radius: 8px;')
                        self.type_icons_layout.addWidget(badge)
                else:
                    dud = QLabel('\u2606')
                    dud.setFixedSize(16, 16)
                    dud.setAlignment(Qt.AlignCenter)
                    dud.setStyleSheet('font-size: 11px; font-weight: bold; color: #A78BFA; background: transparent; border-radius: 8px; border: 1px solid rgba(167,139,250,0.2);')
                    self.type_icons_layout.addWidget(dud)
            else:
                dud = QLabel('\u2606')
                dud.setFixedSize(16, 16)
                dud.setAlignment(Qt.AlignCenter)
                dud.setStyleSheet('font-size: 11px; font-weight: bold; color: #A78BFA; background: transparent; border-radius: 8px; border: 1px solid rgba(167,139,250,0.2);')
                self.type_icons_layout.addWidget(dud)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            is_imported = extract_value(raw, 'bImportedCharacter', False)
            fav_idx = extract_value(raw, 'FavoriteIndex', 0)
            hp_val = safe_nested_get(raw, ['Hp', 'value', 'Value', 'value'], 0)
            max_hp = safe_nested_get(raw, ['MaxHP', 'value', 'Value', 'value'], 0)
            if max_hp <= 0 and base:
                max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky)
            if max_hp <= 0:
                max_hp = hp_val if hp_val > 0 else 1
            atk_val = extract_value(raw, 'Attack', 0)
            def_val = extract_value(raw, 'Defense', 0)
            wspd_val = extract_value(raw, 'WorkSpeed', 0)
            hunger_full = extract_value(raw, 'FullStomach', 0)
            exp_val = extract_value(raw, 'Exp', 0)
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            trust_rank = 0
            for r in range(10, 0, -1):
                if trust_points >= self._TRUST_RANK_THRESHOLDS[r]:
                    trust_rank = r
                    break
            trust_progress = 0
            trust_next = 0
            if trust_rank < 10:
                current_threshold = self._TRUST_RANK_THRESHOLDS[trust_rank]
                next_threshold = self._TRUST_RANK_THRESHOLDS[trust_rank + 1]
                trust_span = next_threshold - current_threshold
                trust_progress = min((trust_points - current_threshold) / trust_span * 100, 100)
                trust_next = next_threshold
            else:
                trust_progress = 100
                trust_next = 0
            stats = (base.get('stats', {}) if base else {})
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
            ws = (base.get('work_suitabilities', {}) if base else {})
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
            self.hp_bar.setFormat(f'{int(hp_val) // 1000}')
            self.hunger_bar.setValue(hunger_pct)
            self.hunger_bar.setFormat(f'{int(hunger_full)} / {int(hunger_max)}')
            self.exp_header_bar.setValue(exp_pct)
            self.next_lbl.setText(str(int(exp_val)))
            san_val = extract_value(raw, 'SanityValue', 100.0)
            san_pct = int(min(float(san_val), 100))
            self.san_bar.setValue(san_pct)
            self.san_bar.setFormat(f'{san_pct}%')
            self.trust_bar.setValue(int(trust_progress))
            self.trust_bar.setFormat('MAX' if trust_rank >= 10 else f'{int(trust_points)} / {int(trust_next)}')
            self.atk_lbl.setText(str(int(atk_val)))
            self.def_lbl.setText(str(int(def_val)))
            self.wspd_lbl.setText(str(int(wspd_val)))
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
            is_awakening = extract_value(raw, 'bIsAwakening', False)
            if fav_idx and int(fav_idx) > 0:
                self.lock_overlay.show()
            else:
                self.lock_overlay.hide()
            self.portrait_ring.set_awakened(bool(is_awakening))
            self.stat_plus_lbl.setText(f'+{level}')
            rank_raw = extract_value(raw, 'Rank', 1)
            rank_int = int(rank_raw) if isinstance(rank_raw, (int, float)) else 1
            stars = ''.join(['\u2605' if i < min(rank_int - 1, 4) else '\u2606' for i in range(4)])
            self.star_rating.setText(stars)
            icon_path = _get_pal_icon_path(cid)
            pix = _get_cached_pixmap(icon_path, 80)
            if pix:
                self.portrait_icon.setPixmap(pix)
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            for i in reversed(range(self.active_skills_list.count())):
                w = self.active_skills_list.itemAt(i)
                if w and w.widget():
                    w.widget().deleteLater()
            for i, e in enumerate(e_list[:3]):
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
                slot.setStyleSheet('QFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; padding-right: 12px; }')
                slot_layout = QHBoxLayout(slot)
                slot_layout.setContentsMargins(8, 3, 8, 3)
                slot_layout.setSpacing(6)
                name_lbl = QLabel(move_name)
                name_lbl.setStyleSheet('font-size: 9px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
                slot_layout.addWidget(name_lbl, 1)
                if skill_elem:
                    elem_pix = _get_element_pixmap(skill_elem, 'small', 16)
                    if elem_pix:
                        elem_badge = QLabel()
                        elem_badge.setFixedSize(18, 18)
                        elem_badge.setAlignment(Qt.AlignCenter)
                        elem_badge.setScaledContents(True)
                        elem_badge.setPixmap(elem_pix)
                        elem_badge.setStyleSheet('background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 2px; padding: 1px; margin: 0px;')
                    else:
                        elem_badge = QLabel(skill_elem[:4])
                        elem_badge.setFixedSize(32, 16)
                        elem_badge.setAlignment(Qt.AlignCenter)
                        elem_badge.setStyleSheet(f'font-size: 6px; font-weight: 700; color: {elem_color}; background: rgba(255,255,255,0.04); border: 1px solid {elem_color}40; border-radius: 2px;')
                    slot_layout.addWidget(elem_badge)
                power_lbl = QLabel(str(skill_power) if skill_power else '--')
                power_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                power_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: #F59E0B; background: transparent; border: none;')
                slot_layout.addWidget(power_lbl)
                self.active_skills_list.addWidget(slot)
            p_skills = raw.get('PassiveSkillList', {})
            if isinstance(p_skills, dict):
                p_list = p_skills.get('value', {}).get('values', [])
            elif isinstance(p_skills, list):
                p_list = p_skills
            else:
                p_list = []
            passive_tiers = [
                ('Runner', 'gold', 'qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5C4033,stop:0.5 #8B6914,stop:1 #5C4033)', 'rgba(255,215,0,0.5)', '#FFD700'),
                ('Swift', 'legendary', 'qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D3B66,stop:0.5 #1A6B8A,stop:1 #0D3B66)', 'rgba(125,211,252,0.5)', '#7DD3FC'),
                ('Legend', 'legendary', 'qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D3B66,stop:0.5 #1A6B8A,stop:1 #0D3B66)', 'rgba(125,211,252,0.5)', '#7DD3FC'),
                ('Surge of the World Tree', 'legendary', 'qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D3B66,stop:0.5 #1A6B8A,stop:1 #0D3B66)', 'rgba(125,211,252,0.5)', '#7DD3FC'),
            ]
            for i in range(4):
                display_name = '--'
                tc = 'rgba(255,255,255,0.3)'
                bg = 'rgba(255,255,255,0.03)'
                bd = 'rgba(255,255,255,0.06)'
                if i < len(p_list) and p_list[i]:
                    p_clean = p_list[i].lower()
                    display_name = PalFrame._PASSMAP.get(p_clean, p_list[i])
                    for pname, ptier, pgrad, pbord, ptxt in passive_tiers:
                        if pname.lower() in display_name.lower() or pname.split()[-1].lower() in display_name.lower():
                            bg = pgrad
                            bd = pbord
                            tc = ptxt
                            break
                    if bg == 'rgba(255,255,255,0.03)':
                        tname = display_name.lower()
                        if 'legend' in tname or 'lord' in tname or 'emperor' in tname or 'soul' in tname or 'spirit' in tname:
                            bg = 'qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D3B66,stop:0.5 #1A6B8A,stop:1 #0D3B66)'
                            bd = 'rgba(125,211,252,0.5)'
                            tc = '#7DD3FC'
                        elif 'ferocious' in tname or 'musclehead' in tname or 'burly' in tname:
                            bg = 'qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5C4033,stop:0.5 #8B6914,stop:1 #5C4033)'
                            bd = 'rgba(255,215,0,0.5)'
                            tc = '#FFD700'
                self.passive_slots[i].setText(display_name)
                self.passive_slots[i].setStyleSheet(f'font-size: 9px; font-weight: 700; color: {tc}; background: transparent; border: none;')
                parent_frame = self.passive_slots[i].parentWidget()
                if parent_frame and parent_frame.objectName() == 'passiveCard':
                    parent_frame.setStyleSheet(f'QFrame#passiveCard {{ background: {bg}; border: 1.5px solid {bd}; border-radius: 4px; padding: 3px 6px; }}')
            self.partner_name_lbl.setText(pal_name)
            self.partner_lvl_lbl.setText(f'Lv {level}')
            self.partner_desc_lbl.setText(f'Partner skill for {pal_name}. Effects scale with level.')
        except Exception as e:
            self._clear_display()

class SearchSortDialog(QDialog):
    def __init__(self, mode='search', parent=None):
        super().__init__(parent)
        self.mode = mode
        self.result_data = {}
        self.setWindowTitle('Search' if mode == 'search' else 'Sort')
        self.setModal(True)
        self.setMinimumSize(480, 520)
        self._setup()
        self._apply_style()
        self._setup_shortcuts()
    def _apply_style(self):
        self.setStyleSheet('\n            QDialog {\n                background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,\n                            stop:0 rgba(12,14,18,0.98),stop:0.5 rgba(10,16,22,0.98),stop:1 rgba(8,12,18,0.98));\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 8px;\n            }\n            QLabel { color: #C8D8E8; font-size: 12px; }\n            QComboBox {\n                background: rgba(255,255,255,0.06);\n                color: #E2E8F0;\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 12px;\n                min-height: 20px;\n            }\n            QComboBox::drop-down {\n                border: none;\n                padding-right: 4px;\n            }\n            QComboBox QAbstractItemView {\n                background: rgba(18,20,24,0.98);\n                color: #E2E8F0;\n                border: 1px solid rgba(125,211,252,0.15);\n                selection-background-color: rgba(59,142,208,0.3);\n                outline: none;\n            }\n            QLineEdit {\n                background: rgba(255,255,255,0.06);\n                color: #E2E8F0;\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 4px;\n                padding: 4px 8px;\n                font-size: 12px;\n            }\n            QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n            QCheckBox {\n                color: #C8D8E8;\n                font-size: 12px;\n                spacing: 6px;\n            }\n            QCheckBox::indicator {\n                width: 16px;\n                height: 16px;\n                border-radius: 3px;\n                border: 1px solid rgba(125,211,252,0.2);\n                background: rgba(255,255,255,0.05);\n            }\n            QCheckBox::indicator:checked {\n                background: rgba(125,211,252,0.3);\n                border-color: #7DD3FC;\n            }\n            QPushButton {\n                border-radius: 4px;\n                padding: 6px 16px;\n                font-size: 12px;\n                font-weight: 600;\n            }\n            QPushButton#applyBtn {\n                background: rgba(125,211,252,0.12);\n                color: #7DD3FC;\n                border: 1px solid rgba(125,211,252,0.2);\n            }\n            QPushButton#applyBtn:hover {\n                background: rgba(125,211,252,0.22);\n                border-color: rgba(125,211,252,0.4);\n                color: #FFFFFF;\n            }\n            QPushButton#resetBtn {\n                background: rgba(245,158,11,0.1);\n                color: #F59E0B;\n                border: 1px solid rgba(245,158,11,0.15);\n            }\n            QPushButton#resetBtn:hover {\n                background: rgba(245,158,11,0.2);\n                border-color: rgba(245,158,11,0.3);\n                color: #FFFFFF;\n            }\n            QPushButton#clearBtn {\n                background: rgba(251,113,133,0.1);\n                color: #FB7185;\n                border: 1px solid rgba(251,113,133,0.15);\n                font-size: 11px;\n                padding: 4px 10px;\n            }\n            QPushButton#clearBtn:hover {\n                background: rgba(251,113,133,0.2);\n                color: #FFFFFF;\n            }\n            QGroupBox {\n                border: 1px solid rgba(255,255,255,0.08);\n                border-radius: 6px;\n                margin-top: 8px;\n                padding-top: 16px;\n                font-size: 12px;\n                font-weight: 600;\n                color: #7DD3FC;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                subcontrol-position: top left;\n                padding: 2px 8px;\n                color: #7DD3FC;\n            }\n        ')
    def _setup_shortcuts(self):
        self.shortcut_apply = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.shortcut_apply.activated.connect(self._on_apply)
        self.shortcut_reset = QShortcut(QKeySequence(Qt.Key_R), self)
        self.shortcut_reset.activated.connect(self._on_reset)
    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        header = QLabel('Sort & Filter' if self.mode == 'sort' else 'Search & Filter')
        header.setStyleSheet('font-size: 16px; font-weight: 700; color: #7DD3FC; border-bottom: 1px solid rgba(125,211,252,0.15); padding-bottom: 6px;')
        layout.addWidget(header)
        sort_group = QGroupBox('Sort Type')
        sort_layout = QVBoxLayout(sort_group)
        self.sort_combo = QComboBox()
        sort_options = ['Palpedia No.', 'Level', 'Element', 'Alpha Pal', 'Work Suitability Level', 'Trust', 'Expedition Firepower']
        self.sort_combo.addItems(sort_options)
        sort_layout.addWidget(self.sort_combo)
        layout.addWidget(sort_group)
        filter_group = QGroupBox('Filters')
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(6)
        elem_layout = QHBoxLayout()
        elem_layout.addWidget(QLabel('Element:'))
        self.elem_combo = QComboBox()
        elements = ['Any', 'Neutral', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Ground', 'Dark', 'Dragon']
        self.elem_combo.addItems(elements)
        _elem_disp_to_name = {'Neutral': 'Normal', 'Fire': 'Fire', 'Water': 'Water', 'Grass': 'Leaf', 'Electric': 'Electricity', 'Ice': 'Ice', 'Ground': 'Earth', 'Dark': 'Dark', 'Dragon': 'Dragon'}
        for i, etext in enumerate(elements):
            ekey = _elem_disp_to_name.get(etext)
            if ekey:
                ep = _get_element_pixmap(ekey, 'small', 16)
                if ep:
                    self.elem_combo.setItemIcon(i, QIcon(ep))
        elem_layout.addWidget(self.elem_combo)
        filter_layout.addLayout(elem_layout)
        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(12)
        gender_layout.addWidget(QLabel('Gender:'))
        self.gender_male = QCheckBox('Male')
        self.gender_female = QCheckBox('Female')
        self.gender_male.setChecked(True)
        self.gender_female.setChecked(True)
        gender_layout.addWidget(self.gender_male)
        gender_layout.addWidget(self.gender_female)
        gender_layout.addStretch()
        filter_layout.addLayout(gender_layout)
        work_layout = QHBoxLayout()
        work_layout.addWidget(QLabel('Work Suitability:'))
        self.work_combo = QComboBox()
        work_types = ['Any', 'Planting', 'Watering', 'Handiwork', 'Gathering', 'Lumbering', 'Mining', 'Cooling', 'Transporting', 'Farming', 'Medicine', 'Electricity']
        self.work_combo.addItems(work_types)
        work_layout.addWidget(self.work_combo)
        filter_layout.addLayout(work_layout)
        layout.addWidget(filter_group)
        passive_group = QGroupBox('Passive Skill Filter')
        passive_layout = QHBoxLayout(passive_group)
        self.passive_combo = QComboBox()
        self.passive_combo.setEditable(True)
        self.passive_combo.setMinimumWidth(200)
        self.passive_combo.setInsertPolicy(QComboBox.NoInsert)
        self._populate_passive_skills()
        completer = QCompleter([self.passive_combo.itemText(i) for i in range(self.passive_combo.count())])
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.passive_combo.setCompleter(completer)
        passive_layout.addWidget(self.passive_combo, 1)
        clear_btn = QPushButton('Clear')
        clear_btn.setObjectName('clearBtn')
        clear_btn.clicked.connect(lambda: self.passive_combo.setCurrentText(''))
        passive_layout.addWidget(clear_btn)
        layout.addWidget(passive_group)
        flags_group = QGroupBox('Priority Flags')
        flags_layout = QHBoxLayout(flags_group)
        flags_layout.setSpacing(8)
        self.flag_fav1 = QCheckBox('Favorite I')
        self.flag_fav2 = QCheckBox('Favorite II')
        self.flag_fav3 = QCheckBox('Favorite III')
        self.flag_dna = QCheckBox('DNA Symbol')
        flags_layout.addWidget(self.flag_fav1)
        flags_layout.addWidget(self.flag_fav2)
        flags_layout.addWidget(self.flag_fav3)
        flags_layout.addWidget(self.flag_dna)
        flags_layout.addStretch()
        layout.addWidget(flags_group)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        reset_btn = QPushButton('Restore Default [R]')
        reset_btn.setObjectName('resetBtn')
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        apply_btn = QPushButton('Search/Apply')
        apply_btn.setObjectName('applyBtn')
        apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)
    def _populate_passive_skills(self):
        self.passive_combo.addItem('')
        for name in sorted(PalFrame._PASSMAP.values()):
            self.passive_combo.addItem(name)
    def _on_reset(self):
        self.sort_combo.setCurrentIndex(0)
        self.elem_combo.setCurrentIndex(0)
        self.gender_male.setChecked(True)
        self.gender_female.setChecked(True)
        self.work_combo.setCurrentIndex(0)
        self.passive_combo.setCurrentText('')
        self.flag_fav1.setChecked(False)
        self.flag_fav2.setChecked(False)
        self.flag_fav3.setChecked(False)
        self.flag_dna.setChecked(False)
    def _on_apply(self):
        self.result_data = {
            'sort_type': self.sort_combo.currentText(),
            'element': self.elem_combo.currentText(),
            'gender_male': self.gender_male.isChecked(),
            'gender_female': self.gender_female.isChecked(),
            'work_suitability': self.work_combo.currentText(),
            'passive_skill': self.passive_combo.currentText(),
            'flag_fav1': self.flag_fav1.isChecked(),
            'flag_fav2': self.flag_fav2.isChecked(),
            'flag_fav3': self.flag_fav3.isChecked(),
            'flag_dna': self.flag_dna.isChecked(),
        }
        self.accept()
    def get_results(self):
        return self.result_data if self.result() == QDialog.Accepted else None

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
        self.party_pals = []
        self.palbox_pals = []
        self.current_box_index = 1
        self.selected_pal_slot = None
        self._hovered_pal = None
        self._clicked_pal = None
        self.palbox_pal_dict = {}
        self.party_pals = []
        self._setup_ui()
        self._setup_hotkeys()
    def _setup_hotkeys(self):
        self.prev_box_shortcut = QShortcut(QKeySequence(Qt.Key_Q), self)
        self.prev_box_shortcut.activated.connect(self._prev_box)
        self.next_box_shortcut = QShortcut(QKeySequence(Qt.Key_E), self)
        self.next_box_shortcut.activated.connect(self._next_box)
    def _setup_ui(self):
        self.setObjectName('palRoot')
        self.setStyleSheet(_PAL_STYLESHEET)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        party_panel = QWidget()
        party_panel.setObjectName('partyPanel')
        party_panel.setFixedWidth(240)
        party_layout = QVBoxLayout(party_panel)
        party_layout.setContentsMargins(6, 6, 6, 110)
        party_layout.setSpacing(28)
        party_header = QLabel('PARTY')
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
        party_layout.addStretch()
        root.addWidget(party_panel)
        palbox_panel = QWidget()
        palbox_panel.setObjectName('palboxPanel')
        palbox_layout = QVBoxLayout(palbox_panel)
        palbox_layout.setContentsMargins(6, 6, 6, 6)
        palbox_layout.setSpacing(6)
        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        self.box_label = QLabel('Box 1')
        self.box_label.setObjectName('boxHeader')
        header_row.addWidget(self.box_label)
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
        header_row.addStretch()
        self.search_btn = QPushButton('Search')
        self.search_btn.setObjectName('searchBtn')
        self.search_btn.clicked.connect(self._open_search)
        header_row.addWidget(self.search_btn)
        self.sort_btn = QPushButton('Sort')
        self.sort_btn.setObjectName('sortBtn')
        self.sort_btn.clicked.connect(self._open_sort)
        header_row.addWidget(self.sort_btn)
        palbox_layout.addLayout(header_row)
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(False)
        self.grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.grid_scroll.setStyleSheet('QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 6px; background: rgba(255,255,255,0.03); border-radius: 3px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.2); border-radius: 3px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.4); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }')
        self.grid_scroll.viewport().installEventFilter(self)
        grid_container = QWidget()
        grid_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(30)
        self.grid_layout.setContentsMargins(0, 0, 0, 30)
        self.palbox_slots = []
        for row in range(5):
            self.grid_layout.setRowStretch(row, 0)
            for col in range(6):
                if row == 0:
                    self.grid_layout.setColumnStretch(col, 0)
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
        self.box_label.setText(f'Box {self.current_box_index}')
        self._update_palbox_page()
    def _next_box(self):
        if self.current_box_index < 32:
            self.current_box_index += 1
        else:
            self.current_box_index = 1
        self.box_label.setText(f'Box {self.current_box_index}')
        self._update_palbox_page()
    def _open_search(self):
        dlg = SearchSortDialog(mode='search', parent=self)
        if dlg.exec() == QDialog.Accepted:
            results = dlg.get_results()
    def _open_sort(self):
        dlg = SearchSortDialog(mode='sort', parent=self)
        if dlg.exec() == QDialog.Accepted:
            results = dlg.get_results()
    def _on_party_slot_clicked(self, idx):
        if 0 <= idx < len(self.party_pals):
            pal = self.party_pals[idx]
            self._clicked_pal = pal
            self.pal_info.set_clicked_pal(pal)
            self.selected_pal_slot = ('party', idx)
            self._highlight_party_slot(idx)
            self._clear_palbox_highlight()
    def _on_party_slot_entered(self, idx):
        if 0 <= idx < len(self.party_pals):
            pal = self.party_pals[idx]
            self._hovered_pal = pal
            self.pal_info.set_hover_pal(pal)
    def _on_party_slot_left(self):
        self.pal_info.clear_hover()
    def _on_palbox_slot_clicked(self, idx):
        pals_on_page = self._get_palbox_page_pals()
        if idx < len(pals_on_page) and pals_on_page[idx] is not None:
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
        if self.selected_pal_slot:
            tab_name = self.selected_pal_slot[0]
        elif hasattr(self, '_last_right_click_tab'):
            tab_name = self._last_right_click_tab
        else:
            tab_name = 'palbox'
        if action == 'delete':
            self._delete_pal_at_slot(slot_index)
        elif action == 'add_new':
            self._add_new_pal_at_slot(slot_index)
    def _delete_pal_at_slot(self, slot_index):
        is_party = self.selected_pal_slot and self.selected_pal_slot[0] == 'party'
        if is_party:
            if slot_index < len(self.party_pals):
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
                self.party_pals.pop(slot_index)
                self._update_party_slots()
                self.pal_info._clear_display()
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
                self.pal_info._clear_display()
    def _add_new_pal_at_slot(self, slot_index):
        from palworld_aio.ui.player_pal_dialog import PlayerPalActionDialog
        dlg = PlayerPalActionDialog(self)
        dlg.setModal(True)
        dlg.exec()
        self._load_pals()
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
        self.party_pals = []
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
        self.box_label.setText('Box 1')
        self.pal_info._clear_display()
    def refresh(self):
        self._process_pending_changes()
        if self.player_uid:
            self._load_pals()
    def _process_pending_changes(self):
        pass
    def refresh_labels(self):
        pass
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
        self.party_pals = []
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
                    self.party_pals.append(item)
                elif slot_id_str == target_palbox:
                    self.palbox_pal_dict[slot_index] = item
            except (KeyError, TypeError, AttributeError):
                continue
        self.party_pals.sort(key=lambda x: safe_nested_get(x, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value', 'SlotId', 'value', 'SlotIndex', 'value']) or 0)
        self._update_party_slots()
        self._update_palbox_page()
    def _update_party_slots(self):
        for i, slot in enumerate(self.party_slots):
            if i < len(self.party_pals):
                slot.pal_data = self.party_pals[i]
            else:
                slot.pal_data = None
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

class PalFrame(QFrame):
    _maps_loaded = False
    _NAMEMAP = {}
    _PASSMAP = {}
    _SKILLMAP = {}
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
        cls._PASSMAP = load_map('palpassivedata.json', 'passives')
        cls._SKILLMAP = load_map('skilldata.json', 'skills')
        PALMAP = load_map('paldata.json', 'pals')
        NPCMAP = load_map('npcdata.json', 'npcs')
        cls._NAMEMAP = {**PALMAP, **NPCMAP}
        skill_exclusions = ['unknown skills', 'unknown skill', 'en_text', 'en text']
        cls._SKILLMAP = {k: v for k, v in cls._SKILLMAP.items() if not any((exc in v.lower() for exc in skill_exclusions))}
        cls._PASSMAP = {k: v for k, v in cls._PASSMAP.items() if not any((exc in v.lower() for exc in skill_exclusions))}
        pal_exclusions = ['en_text', 'en text', 'blackfurdragon', 'eleclion', 'darkmutant', 'gym']
        cls._NAMEMAP = {k: v for k, v in cls._NAMEMAP.items() if not any((exc in v.lower() for exc in pal_exclusions)) and (not k.lower().startswith('raid_')) and (not '_oilrig' in k.lower()) and (not 'summon_' in k.lower()) and (not (k.lower().startswith('boss_') and k.lower() in v.lower())) and (not k.lower() in ['blackfurdragon', 'eleclion', 'darkmutant', 'boss_blackfurdragon', 'boss_eleclion', 'boss_darkmutant'])}
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
            pal_name = resolve_name(cid, self._NAMEMAP) or cid
            if nick:
                pal_name = f'{pal_name}({nick})'
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
