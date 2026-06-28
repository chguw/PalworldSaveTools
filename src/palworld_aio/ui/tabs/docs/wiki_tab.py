import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QScrollArea,
    QFrame, QGridLayout, QAbstractItemView, QStyleOptionButton, QStylePainter, QStyle
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject
from PySide6.QtGui import QPixmap, QIcon, QCursor, QFont, QPainter, QColor, QBrush
from i18n import t
from palworld_aio import constants
from palworld_aio.inventory.inventory_manager import ItemData
from palworld_aio.editor.pal_editor.icons import _get_element_pixmap
from resource_resolver import resource_path

_CATEGORIES = [
    ('pals', 'docs.wiki.pals', 'characters.json', 'pals'),
    ('items', 'docs.wiki.items', 'items.json', 'items'),
    ('buildings', 'docs.wiki.buildings', 'world.json', 'structures'),
    ('active_skills', 'docs.wiki.active_skills', 'skills.json', 'skills'),
    ('passive_skills', 'docs.wiki.passive_skills', 'skills.json', 'passives'),
    ('technologies', 'docs.wiki.technologies', 'world.json', 'technology'),
    ('elements', 'docs.wiki.elements', 'skills.json', 'elements'),
    ('work_suitability', 'docs.wiki.work_suitability', 'work_suitability.json', 'work_types'),
]

_CAT_BTN_STYLE = (
    "QPushButton { background: transparent; color: #94a3b8; border: none; "
    "border-radius: 4px; font-size: 11px; }"
    "QPushButton:hover { background: rgba(125,211,252,0.06); color: #e2e8f0; }"
    "QPushButton[active=true] { background: rgba(125,211,252,0.08); color: #7DD3FC; font-weight: 600; }"
)

_SEARCH_STYLE = (
    "QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid "
    "rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 8px; font-size: 11px; }"
    "QLineEdit:focus { border-color: rgba(125,211,252,0.4); }"
)

_LIST_STYLE = (
    "QListWidget { background: transparent; border: 1px solid rgba(125,211,252,0.1); "
    "border-radius: 6px; color: #e2e8f0; font-size: 11px; }"
    "QListWidget::item { padding: 4px 6px; border-radius: 3px; }"
    "QListWidget::item:selected { background: rgba(125,211,252,0.12); color: #7DD3FC; }"
    "QListWidget::item:hover { background: rgba(125,211,252,0.06); }"
)

_DETAIL_STYLE = (
    "QLabel#detailTitle { font-size: 14px; font-weight: bold; color: #e2e8f0; padding: 4px 0; }"
    "QLabel#detailAsset { font-size: 10px; font-family: monospace; color: #6b7280; }"
    "QLabel#detailLabel { font-size: 10px; color: #6b7280; font-weight: 600; }"
    "QLabel#detailValue { font-size: 11px; color: #e2e8f0; }"
    "QLabel#detailDesc { font-size: 11px; color: #94a3b8; padding: 6px; }"
)

_ICON_SIZE = 36
_LIST_ICON_SIZE = 28


class CatBtn(QPushButton):
    def paintEvent(self, event):
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        fm = p.fontMetrics()
        text_r = fm.boundingRect(self.text())
        tx = 14
        ty = (self.height() - text_r.height()) // 2 - text_r.y()
        p.setPen(self.palette().color(self.foregroundRole()))
        p.drawText(tx, ty, self.text())
        if self.property('active'):
            pw, ph = (3, 16)
            px, py = (0, (self.height() - ph) // 2)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
        p.end()


def _load_json(filename, key):
    base_dir = constants.get_base_path()
    fp = resource_path(base_dir, 'game_data', filename)
    if not os.path.exists(fp):
        return []
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(key, [])


_FIELD_DEFS = {
    'pals': [
        ('name', 'Name', 'text'),
        ('asset', 'Code', 'mono'),
        ('icon', 'Icon', 'icon'),
        ('elements', 'Elements', 'elements'),
        ('stats.hp', 'HP', 'int'),
        ('stats.meal_attack', 'Melee Atk', 'int'),
        ('stats.shot_attack', 'Shot Atk', 'int'),
        ('stats.defense', 'Defense', 'int'),
        ('stats.rarity', 'Rarity', 'int'),
        ('stats.zukan_index', 'Paldeck #', 'int'),
        ('work_suitabilities', 'Work', 'works'),
        ('partner_skill', 'Partner Skill', 'text'),
        ('description', 'Description', 'desc'),
    ],
    'items': [
        ('name', 'Name', 'text'),
        ('asset', 'Code', 'mono'),
        ('icon', 'Icon', 'icon'),
        ('type_a_display', 'Category', 'text'),
        ('type_b_display', 'Subcategory', 'text'),
        ('rarity', 'Rarity', 'int'),
        ('price', 'Price', 'int'),
        ('weight', 'Weight', 'float'),
        ('max_stack', 'Max Stack', 'int'),
        ('rank', 'Rank', 'int'),
        ('restore_satiety', 'Satiety', 'int'),
        ('restore_sanity', 'Sanity', 'int'),
        ('durability', 'Durability', 'int'),
        ('description', 'Description', 'desc'),
    ],
    'buildings': [
        ('name', 'Name', 'text'),
        ('asset', 'Code', 'mono'),
        ('icon', 'Icon', 'icon'),
        ('type_a_display', 'Category', 'text'),
        ('required_work_amount', 'Work Required', 'int'),
        ('rank', 'Rank', 'int'),
        ('hp', 'HP', 'int'),
        ('defense', 'Defense', 'int'),
        ('belongs_to_base', 'Base Required', 'bool'),
        ('install_max_per_base', 'Max per Base', 'int'),
        ('is_paintable', 'Paintable', 'bool'),
        ('materials', 'Materials', 'materials'),
        ('description', 'Description', 'desc'),
    ],
    'active_skills': [
        ('name', 'Name', 'text'),
        ('asset', 'Code', 'mono'),
        ('element', 'Element', 'text'),
        ('power', 'Power', 'int'),
        ('display_power', 'Display Power', 'int'),
        ('cooldown', 'Cooldown', 'float'),
        ('category', 'Type', 'text'),
        ('min_range', 'Min Range', 'int'),
        ('max_range', 'Max Range', 'int'),
        ('effect_type_1', 'Effect 1', 'text'),
        ('effect_value_1', 'Effect Value 1', 'int'),
        ('strength', 'Strength', 'text'),
        ('description', 'Description', 'desc'),
    ],
    'passive_skills': [
        ('name', 'Name', 'text'),
        ('asset', 'Code', 'mono'),
        ('rank', 'Rank', 'int'),
        ('description', 'Effect', 'desc'),
        ('effect1', 'Value 1', 'float'),
        ('efftype1', 'Type 1', 'text'),
        ('effect2', 'Value 2', 'float'),
        ('efftype2', 'Type 2', 'text'),
    ],
    'technologies': [
        ('name', 'Name', 'text'),
        ('asset', 'Code', 'mono'),
        ('icon', 'Icon', 'icon'),
        ('type', 'Type', 'text'),
        ('level_cap', 'Level Required', 'int'),
        ('tier', 'Tier', 'int'),
        ('cost', 'Cost', 'int'),
        ('is_boss_tech', 'Boss Tech', 'bool'),
        ('unlock_item_recipes', 'Unlocks Items', 'list'),
        ('unlock_build_objects', 'Unlocks Buildings', 'list'),
        ('description', 'Description', 'desc'),
    ],
    'elements': [
        ('name', 'Name', 'text'),
        ('display', 'Display Name', 'text'),
        ('index', 'Index', 'int'),
        ('color', 'Color', 'color'),
        ('icons', 'Icons', 'icon_paths'),
    ],
    'work_suitability': [
        ('id', 'ID', 'text'),
        ('display_name', 'Name', 'text'),
        ('icon', 'Icon', 'icon'),
        ('index', 'Index', 'int'),
    ],
}


class WikiDetailPanel(QScrollArea):
    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet(
            "QScrollArea { border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; background: rgba(0,0,0,0.1); }"
        )
        self._category_id = category_id
        self._container = QWidget()
        self._layout = QGridLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(4)
        self.setWidget(self._container)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(64, 64)
        self._icon_label.setAlignment(Qt.AlignCenter)

        self._title_label = QLabel()
        self._title_label.setObjectName('detailTitle')

        self._asset_label = QLabel()
        self._asset_label.setObjectName('detailAsset')
        self._asset_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._field_labels = {}
        self._value_labels = {}

        self._clear()

    def _clear(self):
        for i in reversed(range(self._layout.count())):
            w = self._layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._field_labels.clear()
        self._value_labels.clear()

    def show_item(self, item_data):
        self._clear()
        fields = _FIELD_DEFS.get(self._category_id, [])

        row = 0
        icon_path = None
        name = ''

        for field_key, label, ftype in fields:
            val = self._get_nested(item_data, field_key)
            if val is None or val == '' or val == 'None':
                continue

            if ftype == 'icon':
                icon_path = val if isinstance(val, str) and val else None
            elif ftype == 'text' and field_key == 'name':
                name = str(val)
                title = QLabel(str(val))
                title.setObjectName('detailTitle')
                self._layout.addWidget(title, row, 0, 1, 2)
                row += 1
            elif ftype == 'mono':
                lbl = QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{val}</span>')
                lbl.setTextFormat(Qt.RichText)
                self._layout.addWidget(lbl, row, 0, 1, 2)
                row += 1
            elif ftype == 'desc':
                desc = QLabel(str(val))
                desc.setObjectName('detailDesc')
                desc.setWordWrap(True)
                self._layout.addWidget(desc, row, 0, 1, 2)
                row += 1
            elif ftype == 'elements':
                if isinstance(val, dict):
                    ew = QWidget()
                    el = QHBoxLayout(ew)
                    el.setContentsMargins(0, 0, 0, 0)
                    el.setSpacing(4)
                    for ename in val:
                        px = _get_element_pixmap(ename.lower(), 'small', 20)
                        if px:
                            il = QLabel()
                            il.setPixmap(px)
                            el.addWidget(il)
                        dl = val[ename].get('name', ename) if isinstance(val[ename], dict) else ename
                        el.addWidget(QLabel(dl))
                    el.addStretch()
                    self._layout.addWidget(QLabel('Elements:'), row, 0)
                    self._layout.addWidget(ew, row, 1)
                    row += 1
            elif ftype == 'works':
                if isinstance(val, dict):
                    active = {k: v for k, v in val.items() if isinstance(v, (int, float)) and v > 0}
                    if active:
                        from palworld_aio.editor.pal_editor.pal_info_widget import PalInfoWidget
                        _ws_map = PalInfoWidget._WORK_SUITABILITY_DISPLAY
                        parts = []
                        for k, v in active.items():
                            dname = _ws_map.get(k, k)
                            parts.append(f'{dname} Lv.{int(v)}')
                        wlbl = QLabel(', '.join(parts))
                        wlbl.setObjectName('detailValue')
                        wlbl.setWordWrap(True)
                        self._layout.addWidget(QLabel('Work Suitability:'), row, 0)
                        self._layout.addWidget(wlbl, row, 1)
                        row += 1
            elif ftype == 'materials':
                if isinstance(val, list) and val:
                    parts = [f'{m.get("id","?")} x{m.get("count",0)}' for m in val if m.get('id')]
                    mlbl = QLabel(', '.join(parts))
                    mlbl.setObjectName('detailValue')
                    mlbl.setWordWrap(True)
                    self._layout.addWidget(QLabel('Materials:'), row, 0)
                    self._layout.addWidget(mlbl, row, 1)
                    row += 1
            elif ftype == 'bool':
                blbl = QLabel('Yes' if val else 'No')
                blbl.setObjectName('detailValue')
                self._layout.addWidget(QLabel(f'{label}:'), row, 0)
                self._layout.addWidget(blbl, row, 1)
                row += 1
            elif ftype == 'color':
                color_frame = QFrame()
                color_frame.setFixedSize(20, 20)
                color_frame.setStyleSheet(f'background: {val}; border-radius: 3px; border: 1px solid rgba(255,255,255,0.1);')
                hlbl = QLabel(str(val))
                hlbl.setObjectName('detailValue')
                hlbl.setStyleSheet('font-family: monospace; font-size: 10px;')
                hlbl.setFixedHeight(20)
                cw = QWidget()
                cl = QHBoxLayout(cw)
                cl.setContentsMargins(0, 0, 0, 0)
                cl.setSpacing(4)
                cl.addWidget(color_frame)
                cl.addWidget(hlbl)
                cl.addStretch()
                self._layout.addWidget(QLabel('Color:'), row, 0)
                self._layout.addWidget(cw, row, 1)
                row += 1
            elif ftype == 'icon_paths':
                if isinstance(val, dict):
                    iw = QWidget()
                    il = QHBoxLayout(iw)
                    il.setContentsMargins(0, 0, 0, 0)
                    il.setSpacing(6)
                    for iname, ipath in val.items():
                        if isinstance(ipath, str) and ipath.startswith('/icons/'):
                            base_dir = constants.get_base_path()
                            fp = resource_path(base_dir, 'game_data', ipath.lstrip('/'))
                            base_fp = fp.rsplit('.', 1)[0]
                            px = None
                            for try_fp in (fp, base_fp + '.webp', base_fp + '.png'):
                                if os.path.exists(try_fp):
                                    px = QPixmap(try_fp)
                                    break
                            if px and not px.isNull():
                                lbl = QLabel()
                                lbl.setPixmap(px.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                                lbl.setToolTip(iname)
                                il.addWidget(lbl)
                    il.addStretch()
                    self._layout.addWidget(QLabel('Icons:'), row, 0)
                    self._layout.addWidget(iw, row, 1)
                    row += 1
            elif ftype == 'list':
                if isinstance(val, list) and val:
                    llbl = QLabel(', '.join(str(x) for x in val))
                    llbl.setObjectName('detailValue')
                    llbl.setWordWrap(True)
                    self._layout.addWidget(QLabel(f'{label}:'), row, 0)
                    self._layout.addWidget(llbl, row, 1)
                    row += 1
            elif ftype == 'int':
                vlbl = QLabel(str(val))
                vlbl.setObjectName('detailValue')
                self._layout.addWidget(QLabel(f'{label}:'), row, 0)
                self._layout.addWidget(vlbl, row, 1)
                row += 1
            elif ftype == 'float':
                vlbl = QLabel(f'{val:.1f}')
                vlbl.setObjectName('detailValue')
                self._layout.addWidget(QLabel(f'{label}:'), row, 0)
                self._layout.addWidget(vlbl, row, 1)
                row += 1
            elif ftype == 'text':
                vlbl = QLabel(str(val))
                vlbl.setObjectName('detailValue')
                vlbl.setWordWrap(True)
                self._layout.addWidget(QLabel(f'{label}:'), row, 0)
                self._layout.addWidget(vlbl, row, 1)
                row += 1

        self._layout.setRowStretch(row, 1)

    def _get_nested(self, data, path):
        parts = path.split('.')
        cur = data
        for p in parts:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
        return cur


class WikiCategoryPage(QWidget):
    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self._category_id = category_id
        self._all_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText(t('docs.wiki.search') if t else 'Search...')
        self._search.setStyleSheet(_SEARCH_STYLE)
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setStyleSheet(_LIST_STYLE)
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.setSpacing(0)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, 1)

        self._detail = WikiDetailPanel(self._category_id)
        self._detail.setMinimumHeight(120)
        layout.addWidget(self._detail, 1)

    def load_data(self, items):
        self._all_data = items
        self._list.clear()
        self._detail.show_item({'name': t('docs.wiki.select_hint') if t else 'Select an item to view details'})
        for item in items:
            name = item.get('name', item.get('display_name', item.get('id', '?')))
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, items.index(item))
            icon_path = item.get('icon', '')
            if icon_path:
                pixmap = self._load_icon(icon_path)
                if pixmap and not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap.scaled(_LIST_ICON_SIZE, _LIST_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            self._list.addItem(list_item)

    def _load_icon(self, icon_path):
        if not icon_path:
            return None
        if icon_path.startswith('/icons/'):
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', icon_path.lstrip('/'))
            if os.path.exists(fp):
                return QPixmap(fp)
            fp_webp = fp.rsplit('.', 1)[0] + '.webp'
            if os.path.exists(fp_webp):
                return QPixmap(fp_webp)
            fp_png = fp.rsplit('.', 1)[0] + '.png'
            if os.path.exists(fp_png):
                return QPixmap(fp_png)
        return None

    def _filter(self, query):
        q = query.lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            idx = item.data(Qt.UserRole)
            if idx is not None and idx < len(self._all_data):
                data = self._all_data[idx]
                name = data.get('name', data.get('display_name', data.get('id', '')))
                asset = data.get('asset', '')
                visible = not q or q in name.lower() or q in asset.lower()
                item.setHidden(not visible)
            else:
                item.setHidden(True)

    def _on_selection_changed(self, current, previous):
        if not current:
            self._detail.show_item({'name': t('docs.wiki.select_hint') if t else 'Select an item to view details'})
            return
        idx = current.data(Qt.UserRole)
        if idx is not None and idx < len(self._all_data):
            self._detail.show_item(self._all_data[idx])

    def refresh_labels(self):
        self._search.setPlaceholderText(t('docs.wiki.search') if t else 'Search...')
        if not self._list.currentItem():
            self._detail.show_item({'name': t('docs.wiki.select_hint') if t else 'Select an item to view details'})


class WikiDataLoader(QObject):
    dataReady = Signal(dict)
    error = Signal(str)

    def __init__(self, categories):
        super().__init__()
        self._categories = categories

    def run(self):
        try:
            result = {}
            for cat_id, i18n_key, fname, data_key in self._categories:
                items = _load_json(fname, data_key)
                result[cat_id] = items
            self.dataReady.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class WikiTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._pages = {}
        self._loaded = False
        self._setup_ui()
        self._start_loading()

    def _start_loading(self):
        self._thread = QThread()
        self._worker = WikiDataLoader(_CATEGORIES)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.dataReady.connect(self._on_data_loaded)
        self._worker.dataReady.connect(self._thread.quit)
        self._worker.dataReady.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._worker.error.connect(self._on_load_error)
        self._thread.start()

    def _on_data_loaded(self, data):
        for cat_id, items in data.items():
            if cat_id in self._pages:
                self._pages[cat_id].load_data(items)
        self._loaded = True

    def _on_load_error(self, msg):
        self._loaded = True

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 4, 6)
        left_layout.setSpacing(2)

        self._cat_btns = {}
        for cat_id, i18n_key, fname, data_key in _CATEGORIES:
            btn = CatBtn(t(i18n_key) if t else i18n_key)
            btn.setProperty('active', False)
            btn.setStyleSheet(_CAT_BTN_STYLE)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, c=cat_id: self._switch_category(c))
            self._cat_btns[cat_id] = btn
            left_layout.addWidget(btn)

        left_layout.addStretch()
        left_panel.setFixedWidth(160)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 6, 6, 6)
        right_layout.setSpacing(0)

        self._cat_stack = QStackedWidget()
        for cat_id, i18n_key, fname, data_key in _CATEGORIES:
            page = WikiCategoryPage(cat_id)
            self._pages[cat_id] = page
            self._cat_stack.addWidget(page)

        right_layout.addWidget(self._cat_stack, 1)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([160, 600])
        layout.addWidget(splitter, 1)

        if _CATEGORIES:
            self._switch_category(_CATEGORIES[0][0])

    def _load_all_data(self):
        for cat_id, i18n_key, fname, data_key in _CATEGORIES:
            items = _load_json(fname, data_key)
            self._pages[cat_id].load_data(items)

    def _switch_category(self, cat_id):
        if cat_id in self._pages:
            idx = [c[0] for c in _CATEGORIES].index(cat_id)
            self._cat_stack.setCurrentIndex(idx)
        for cid, btn in self._cat_btns.items():
            active = cid == cat_id
            btn.setProperty('active', active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh(self):
        pass

    def refresh_labels(self):
        for cat_id, i18n_key, fname, data_key in _CATEGORIES:
            if cat_id in self._cat_btns:
                self._cat_btns[cat_id].setText(t(i18n_key) if t else i18n_key)
            if cat_id in self._pages:
                self._pages[cat_id].refresh_labels()







