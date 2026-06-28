import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QScrollArea,
    QFrame, QGridLayout, QAbstractItemView, QStyleOptionButton, QStylePainter, QStyle,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QCursor, QPainter, QColor, QBrush
from i18n import t
from palworld_aio import constants
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

_BASE = "QPushButton { background: transparent; color: #94a3b8; border: none; border-radius: 4px; font-size: 11px; }"
_BASE += "QPushButton:hover { background: rgba(125,211,252,0.06); color: #e2e8f0; }"
_BASE += "QPushButton[active=true] { background: rgba(125,211,252,0.08); color: #7DD3FC; font-weight: 600; }"
_SEARCH_S = "QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 8px; font-size: 11px; } QLineEdit:focus { border-color: rgba(125,211,252,0.4); }"
_LIST_S = "QListWidget { background: transparent; border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; color: #e2e8f0; font-size: 11px; } QListWidget::item { padding: 4px 6px; border-radius: 3px; } QListWidget::item:selected { background: rgba(125,211,252,0.12); color: #7DD3FC; } QListWidget::item:hover { background: rgba(125,211,252,0.06); }"
_DETAIL_S = "QScrollArea { border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; background: rgba(0,0,0,0.1); }"
_CARD_S = "background: rgba(255,255,255,0.04); border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; padding: 8px;"

_LIST_ICON = 28

def _load_json(filename, key):
    base_dir = constants.get_base_path()
    fp = resource_path(base_dir, 'game_data', filename)
    if not os.path.exists(fp):
        return []
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(key, [])

def _icon(icon_path, size=_LIST_ICON):
    if not icon_path:
        return None
    base_dir = constants.get_base_path()
    fp = resource_path(base_dir, 'game_data', icon_path.lstrip('/')) if icon_path.startswith('/icons/') else resource_path(base_dir, 'game_data', 'icons', icon_path)
    if os.path.exists(fp):
        px = QPixmap(fp)
        if not px.isNull():
            return px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    base = fp.rsplit('.', 1)[0]
    for ext in ('.webp', '.png'):
        p = base + ext
        if os.path.exists(p):
            px = QPixmap(p)
            if not px.isNull():
                return px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None

def _get(data, path):
    for p in path.split('.'):
        if isinstance(data, dict):
            data = data.get(p)
        else:
            return None
    return data

def _v(text):
    if text is None or text == 'None':
        return None
    return str(text)

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
        tr = fm.boundingRect(self.text())
        tx, ty = 14, (self.height() - tr.height()) // 2 - tr.y()
        p.setPen(self.palette().color(self.foregroundRole()))
        p.drawText(tx, ty, self.text())
        if self.property('active'):
            pw, ph = 3, 16
            px, py = 0, (self.height() - ph) // 2
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
        p.end()


class WikiDetailPanel(QScrollArea):
    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet(_DETAIL_S)
        self._cat = category_id
        self._c = QWidget()
        self._l = QVBoxLayout(self._c)
        self._l.setContentsMargins(16, 16, 16, 16)
        self._l.setSpacing(8)
        self.setWidget(self._c)

    def _clr(self):
        for i in reversed(range(self._l.count())):
            w = self._l.itemAt(i).widget()
            if w:
                w.deleteLater()

    def _hl(self, text, size=16, bold=True, color='#e2e8f0'):
        lbl = QLabel(text)
        lbl.setStyleSheet(f'font-size:{size}px;font-weight:{"bold" if bold else "normal"};color:{color};')
        lbl.setWordWrap(True)
        return lbl

    def _kv(self, k, v):
        w = QWidget()
        lo = QHBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)
        kl = QLabel(k)
        kl.setStyleSheet('font-size:10px;color:#6b7280;font-weight:600;')
        vl = QLabel(_v(v) or '')
        vl.setStyleSheet('font-size:11px;color:#e2e8f0;')
        vl.setWordWrap(True)
        lo.addWidget(kl)
        lo.addWidget(vl, 1)
        return w

    def _card(self, label, value, icon_px=None):
        f = QFrame()
        f.setStyleSheet(_CARD_S)
        lo = QVBoxLayout(f)
        lo.setContentsMargins(10, 8, 10, 8)
        lo.setSpacing(2)
        if icon_px:
            il = QLabel()
            il.setPixmap(icon_px)
            il.setFixedSize(20, 20)
            lo.addWidget(il, 0, Qt.AlignLeft)
        ll = QLabel(label)
        ll.setStyleSheet('font-size:10px;color:#6b7280;')
        lo.addWidget(ll)
        vl = QLabel(str(value))
        vl.setStyleSheet('font-size:18px;font-weight:600;color:#e2e8f0;')
        lo.addWidget(vl)
        return f

    def _badge(self, text, color='#7DD3FC'):
        l = QLabel(text)
        l.setStyleSheet(f'background:rgba(125,211,252,0.08);color:{color};border-radius:4px;padding:2px 8px;font-size:11px;')
        return l

    def _sep(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet('color:rgba(125,211,252,0.15);')
        return f

    def _render_pal(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        elements = _get(d, 'elements')
        work = _get(d, 'work_suitabilities')
        partner = _get(d, 'partner_skill') or ''
        stats = _get(d, 'stats') or {}
        zukan = _get(d, 'stats.zukan_index')

        # header
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 64)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(64, 64)
            hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(2)
        nrow = QHBoxLayout()
        nrow.setSpacing(8)
        nrow.addWidget(self._hl(name, 18))
        if isinstance(elements, dict):
            for ename in elements:
                px = _get_element_pixmap(ename.lower(), 'small', 20)
                if px:
                    el = QLabel()
                    el.setPixmap(px)
                    el.setFixedSize(20, 20)
                    nrow.addWidget(el)
        if zukan:
            nrow.addWidget(self._hl(f'#{zukan}', 12, False, '#6b7280'))
        nl.addLayout(nrow)
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)

        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

        self._l.addWidget(self._sep())

        # stat cards
        stat_defs = [
            ('HP', stats.get('hp', ''), None),
            ('Melee Atk', stats.get('meal_attack', ''), None),
            ('Shot Atk', stats.get('shot_attack', ''), None),
            ('Defense', stats.get('defense', ''), None),
            ('Rarity', stats.get('rarity', ''), None),
        ]
        sw = QWidget()
        sl = QHBoxLayout(sw)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(8)
        for lbl, val, _ in stat_defs:
            sl.addWidget(self._card(lbl, val if val is not None else ''))
        self._l.addWidget(sw)

        # work suitability
        if isinstance(work, dict):
            active = {k: v for k, v in work.items() if isinstance(v, (int, float)) and v > 0}
            if active:
                from palworld_aio.editor.pal_editor.pal_info_widget import PalInfoWidget
                ws_map = PalInfoWidget._WORK_SUITABILITY_DISPLAY
                ww = QWidget()
                wl = QHBoxLayout(ww)
                wl.setContentsMargins(0, 0, 0, 0)
                wl.setSpacing(6)
                wl.addWidget(QLabel('Work:'))
                wl.addWidget(self._hl('Work Suitability', 11, True, '#94a3b8'))
                for k, v in active.items():
                    dname = ws_map.get(k, k)
                    wl.addWidget(self._badge(f'{dname} Lv.{int(v)}'))
                wl.addStretch()
                self._l.addWidget(ww)

        if partner:
            self._l.addWidget(self._kv('Partner Skill', partner))

    def _render_item(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.addWidget(self._hl(name, 18))
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)
        stat_pairs = [
            ('Category', _get(d, 'type_a_display')),
            ('Subcategory', _get(d, 'type_b_display')),
            ('Rarity', _get(d, 'rarity')),
            ('Price', _get(d, 'price')),
        ]
        gw = QWidget()
        gl = QHBoxLayout(gw)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(8)
        for lbl, val in stat_pairs:
            gl.addWidget(self._card(lbl, val if val is not None else ''))
        self._l.addWidget(gw)
        extra_pairs = [
            ('Weight', _get(d, 'weight')),
            ('Max Stack', _get(d, 'max_stack')),
            ('Rank', _get(d, 'rank')),
            ('Satiety', _get(d, 'restore_satiety')),
            ('Sanity', _get(d, 'restore_sanity')),
            ('Durability', _get(d, 'durability')),
        ]
        ew = QWidget()
        el = QHBoxLayout(ew)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(8)
        for lbl, val in extra_pairs:
            if val is not None:
                el.addWidget(self._card(lbl, val))
        if el.count() > 0:
            el.addStretch()
            self._l.addWidget(ew)
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

    def _render_building(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.addWidget(self._hl(name, 18))
        sub = _get(d, 'type_a_display')
        if sub or code:
            txt = f'{sub} / {code}' if sub and code else (sub or code)
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;">{txt}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)
        stat_pairs = [
            ('Rank', _get(d, 'rank')),
            ('HP', _get(d, 'hp')),
            ('Defense', _get(d, 'defense')),
            ('Work Required', _get(d, 'required_work_amount')),
        ]
        sw = QWidget()
        sl = QHBoxLayout(sw)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(8)
        for lbl, val in stat_pairs:
            if val is not None:
                sl.addWidget(self._card(lbl, val))
        if sl.count() > 0:
            sl.addStretch()
            self._l.addWidget(sw)
        extra = []
        if _get(d, 'belongs_to_base') is not None:
            extra.append(('Base Required', 'Yes' if _get(d, 'belongs_to_base') else 'No'))
        if _get(d, 'install_max_per_base') is not None:
            extra.append(('Max per Base', _get(d, 'install_max_per_base')))
        if _get(d, 'is_paintable') is not None:
            extra.append(('Paintable', 'Yes' if _get(d, 'is_paintable') else 'No'))
        if extra:
            ew = QWidget()
            el = QHBoxLayout(ew)
            el.setContentsMargins(0, 0, 0, 0)
            el.setSpacing(8)
            for lbl, val in extra:
                el.addWidget(self._card(lbl, val))
            el.addStretch()
            self._l.addWidget(ew)
        materials = _get(d, 'materials')
        if isinstance(materials, list) and materials:
            self._l.addWidget(self._hl('Materials', 12, True, '#94a3b8'))
            mw = QWidget()
            ml = QHBoxLayout(mw)
            ml.setContentsMargins(0, 0, 0, 0)
            ml.setSpacing(6)
            for m in materials:
                mid = m.get('id', '?')
                cnt = m.get('count', 0)
                ml.addWidget(self._badge(f'{mid} x{cnt}', '#e2e8f0'))
            ml.addStretch()
            self._l.addWidget(mw)

    def _render_element(self, d):
        name = _get(d, 'name') or ''
        display = _get(d, 'display') or name
        color = _get(d, 'color') or ''
        icons = _get(d, 'icons')
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        if isinstance(icons, dict):
            first_icon = None
            for v in icons.values():
                if isinstance(v, str):
                    first_icon = v
                    break
            if first_icon:
                ip = _icon(first_icon, 48)
                if ip:
                    il = QLabel()
                    il.setPixmap(ip)
                    il.setFixedSize(48, 48)
                    hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nrow = QHBoxLayout()
        nrow.setSpacing(8)
        nrow.addWidget(self._hl(display, 18))
        if color:
            cf = QFrame()
            cf.setFixedSize(16, 16)
            cf.setStyleSheet(f'background:{color};border-radius:3px;')
            nrow.addWidget(cf)
        nl.addLayout(nrow)
        if name:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{name}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)
        if isinstance(icons, dict):
            self._l.addWidget(self._hl('Icons', 12, True, '#94a3b8'))
            iw = QWidget()
            il = QHBoxLayout(iw)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(8)
            for iname, ipath in icons.items():
                px = _icon(ipath, 32)
                if px:
                    lbl = QLabel()
                    lbl.setPixmap(px)
                    lbl.setFixedSize(32, 32)
                    lbl.setToolTip(iname)
                    il.addWidget(lbl)
            il.addStretch()
            self._l.addWidget(iw)

    def _render_work(self, d):
        name = _get(d, 'display_name') or _get(d, 'id') or ''
        desc = _get(d, 'description') or ''
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        hl.addWidget(self._hl(name, 18))
        hl.addStretch()
        self._l.addWidget(h)
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

    def _render_generic(self, d):
        name = d.get('name', d.get('display_name', d.get('id', 'Select an item')))
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(d.get('icon', ''), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        hl.addWidget(self._hl(name, 18))
        code = d.get('asset', '')
        if code:
            hl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addStretch()
        self._l.addWidget(h)
        for k, v in d.items():
            if k in ('name', 'asset', 'icon'):
                continue
            if isinstance(v, (str, int, float, bool)):
                self._l.addWidget(self._kv(k.replace('_', ' ').title(), v))
            elif isinstance(v, list) and v and all(isinstance(x, str) for x in v):
                self._l.addWidget(self._kv(k.replace('_', ' ').title(), ', '.join(v)))

    def show_item(self, data):
        self._clr()
        if data is None or not isinstance(data, dict):
            return
        if self._cat == 'pals':
            self._render_pal(data)
        elif self._cat == 'items':
            self._render_item(data)
        elif self._cat == 'buildings':
            self._render_building(data)
        elif self._cat == 'elements':
            self._render_element(data)
        elif self._cat == 'work_suitability':
            self._render_work(data)
        else:
            self._render_generic(data)
        self._l.addStretch(1)


class WikiCategoryPage(QWidget):
    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self._cat = category_id
        self._all_data = []
        self._loaded = False
        self._setup_ui()

    def _setup_ui(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        sp = QSplitter(Qt.Horizontal)

        lp = QWidget()
        ll = QVBoxLayout(lp)
        ll.setContentsMargins(6, 6, 4, 6)
        ll.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText(t('docs.wiki.search') if t else 'Search...')
        self._search.setStyleSheet(_SEARCH_S)
        self._search.textChanged.connect(self._filter)
        ll.addWidget(self._search)

        self._list = QListWidget()
        self._list.setStyleSheet(_LIST_S)
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.currentItemChanged.connect(self._on_sel)
        self._list.setSpacing(0)
        ll.addWidget(self._list, 1)

        lp.setMinimumWidth(180)
        sp.addWidget(lp)

        self._detail = WikiDetailPanel(self._cat)
        sp.addWidget(self._detail)

        sp.setSizes([260, 500])
        lo.addWidget(sp, 1)

    def load(self):
        idx = [c[0] for c in _CATEGORIES].index(self._cat)
        _, _, fname, data_key = _CATEGORIES[idx]
        items = _load_json(fname, data_key)
        self._all_data = items
        self._loaded = True
        self._list.clear()
        for i, item in enumerate(items):
            name = item.get('name', item.get('display_name', item.get('id', '?')))
            li = QListWidgetItem(name)
            li.setData(Qt.UserRole, i)
            ip = _icon(item.get('icon', ''))
            if ip:
                li.setIcon(QIcon(ip))
            self._list.addItem(li)

    def _filter(self, q):
        q = q.lower()
        for i in range(self._list.count()):
            it = self._list.item(i)
            idx = it.data(Qt.UserRole)
            if idx is not None and idx < len(self._all_data):
                d = self._all_data[idx]
                name = d.get('name', d.get('display_name', d.get('id', '')))
                asset = d.get('asset', '')
                it.setHidden(bool(q) and q not in name.lower() and q not in asset.lower())
            else:
                it.setHidden(True)

    def _on_sel(self, cur, prev):
        if not cur:
            return
        idx = cur.data(Qt.UserRole)
        if idx is not None and idx < len(self._all_data):
            self._detail.show_item(self._all_data[idx])

    def refresh_labels(self):
        self._search.setPlaceholderText(t('docs.wiki.search') if t else 'Search...')
        self._detail.show_item({})


class WikiTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._pages = {}
        self._setup_ui()
        if _CATEGORIES:
            self._switch_category(_CATEGORIES[0][0])

    def _setup_ui(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        sp = QSplitter(Qt.Horizontal)

        lp = QWidget()
        ll = QVBoxLayout(lp)
        ll.setContentsMargins(6, 6, 4, 6)
        ll.setSpacing(2)

        self._cat_btns = {}
        for cat_id, i18n_key, *_ in _CATEGORIES:
            btn = CatBtn(t(i18n_key) if t else i18n_key)
            btn.setProperty('active', False)
            btn.setStyleSheet(_BASE)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, c=cat_id: self._switch_category(c))
            self._cat_btns[cat_id] = btn
            ll.addWidget(btn)

        ll.addStretch()
        lp.setFixedWidth(160)
        sp.addWidget(lp)

        rp = QWidget()
        rl = QVBoxLayout(rp)
        rl.setContentsMargins(4, 6, 6, 6)
        rl.setSpacing(0)

        self._cat_stack = QStackedWidget()
        for cat_id, *_ in _CATEGORIES:
            pg = WikiCategoryPage(cat_id)
            self._pages[cat_id] = pg
            self._cat_stack.addWidget(pg)

        rl.addWidget(self._cat_stack, 1)
        sp.addWidget(rp)

        sp.setStretchFactor(0, 0)
        sp.setStretchFactor(1, 1)
        sp.setSizes([160, 600])
        lo.addWidget(sp, 1)

    def _switch_category(self, cat_id):
        if cat_id in self._pages:
            idx = [c[0] for c in _CATEGORIES].index(cat_id)
            self._cat_stack.setCurrentIndex(idx)
            pg = self._pages[cat_id]
            if not pg._loaded:
                pg.load()
        for cid, btn in self._cat_btns.items():
            active = cid == cat_id
            btn.setProperty('active', active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh(self):
        pass

    def refresh_labels(self):
        for cat_id, i18n_key, *_ in _CATEGORIES:
            if cat_id in self._cat_btns:
                self._cat_btns[cat_id].setText(t(i18n_key) if t else i18n_key)
            if cat_id in self._pages:
                self._pages[cat_id].refresh_labels()
