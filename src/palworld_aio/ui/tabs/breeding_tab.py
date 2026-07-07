import json
import os
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor, QPixmap
from palworld_aio import constants
from resource_resolver import resource_path
from i18n import t
from palworld_aio.editor.pal_editor import PalCreateDialog
try:
    import nerdfont as nf
    ARROW_RIGHT = nf.icons.get('nf-fa-arrow_right', '\u2192')
    PLUS = nf.icons.get('nf-fa-plus', '+')
    EGG = nf.icons.get('nf-fa-egg', '\u2B55')
except Exception:
    ARROW_RIGHT = '\u2192'
    PLUS = '+'
    EGG = '\u2B55'

_BTN_STYLE = (
    'QPushButton { background: transparent; color: #94a3b8; border: none; '
    'border-bottom: 2px solid transparent; padding: 6px 16px; font-size: 12px; font-weight: 600; }'
    'QPushButton:hover { color: #e2e8f0; }'
    'QPushButton[active=true] { color: #7DD3FC; border-bottom: 2px solid #7DD3FC; }'
)
_CARD_STYLE = 'QFrame { background: transparent; border: none; }'
_SELECT_BTN_STYLE = (
    'QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; '
    'border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 10px 20px; '
    'font-size: 14px; font-weight: 600; }'
    'QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #fff; }'
)


def _fmt(text, name):
    return re.sub(r'\{(\w+)\}', name, text)


class _SelectPalDialog(PalCreateDialog):
    def __init__(self, parent=None):
        from palworld_aio.editor.pal_editor import PalFrame
        PalFrame._load_maps()
        super().__init__(pal_editor=None, is_party=False, slot_index=0, parent=parent)
        self.selected_asset = None
        self.selected_name = None
        self._breeding_ok_btn = None
        self._breeding_cancel_btn = None
        self._convert_to_selector()

    def _convert_to_selector(self):
        self.setWindowTitle(t('breeding.select_pal') if t else 'Select a Pal')
        for btn in self.findChildren(QPushButton):
            txt = btn.text()
            if 'Create' in txt or 'create' in txt:
                btn.setText(t('breeding.select_btn') if t else 'Select')
                btn.clicked.disconnect()
                btn.clicked.connect(self._on_select)
                self._breeding_ok_btn = btn
            elif 'Cancel' in txt or 'cancel' in txt:
                self._breeding_cancel_btn = btn

    def _on_select(self):
        if self.selected_pal and self.selected_pal.get('asset'):
            self.selected_asset = self.selected_pal['asset']
            self.selected_name = self.selected_pal.get('name', self.selected_asset)
            self.accept()

    def _on_create(self):
        self._on_select()


def _icon_pixmap(icon_path, size=40):
    if not icon_path:
        return None
    base_dir = constants.get_base_path()
    rel = icon_path.lstrip('/')
    fp = resource_path(base_dir, 'game_data', rel)
    if not os.path.exists(fp):
        stem, ext = os.path.splitext(rel)
        fp = resource_path(base_dir, 'game_data', stem + ('.webp' if ext == '.png' else '.png'))
    if not os.path.exists(fp):
        return None
    pix = QPixmap(fp)
    if pix.isNull():
        return None
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class PalIconLabel(QLabel):
    def __init__(self, icon_path, size=40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        pix = _icon_pixmap(icon_path, size)
        if pix and not pix.isNull():
            self.setPixmap(pix)
        self.setScaledContents(True)


class BreedingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._breeding_data = None
        self._mode = 'parents'
        self._selected_tribe = None
        self._selected_name = None
        self._selected_icon = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 10)
        layout.setSpacing(8)

        sub_bar = QHBoxLayout()
        sub_bar.setContentsMargins(0, 0, 0, 0)
        sub_bar.setSpacing(0)
        self._sub_btns = {}
        for sid, skey in [('parents', 'Parents'), ('children', 'Children')]:
            btn = QPushButton(t(f'breeding.mode.{sid}') if t else skey)
            btn.setFixedHeight(32)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setProperty('active', False)
            btn.setStyleSheet(_BTN_STYLE)
            btn.clicked.connect(lambda checked, s=sid: self._switch_mode(s))
            self._sub_btns[sid] = btn
            sub_bar.addWidget(btn)
        sub_bar.addStretch()
        layout.addLayout(sub_bar)

        select_row = QHBoxLayout()
        select_row.setContentsMargins(0, 0, 0, 0)
        self._select_btn = QPushButton(f'{EGG}  {t("breeding.select_pal") if t else "Select a Pal..."}')
        self._select_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 13))
        self._select_btn.setStyleSheet(_SELECT_BTN_STYLE)
        self._select_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._select_btn.clicked.connect(self._open_pal_dialog)
        select_row.addWidget(self._select_btn)
        select_row.addStretch()
        self._selected_label = QLabel('')
        self._selected_label.setStyleSheet('color: #7DD3FC; font-size: 14px; font-weight: 600;')
        select_row.addWidget(self._selected_label)
        layout.addLayout(select_row)

        self._hint_label = QLabel(t('breeding.hint') if t else 'Click the button above to select a pal and view breeding combinations.')
        self._hint_label.setStyleSheet('color: #64748b; font-size: 11px; padding: 2px 4px;')
        self._hint_label.setWordWrap(True)
        layout.addWidget(self._hint_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea { background: transparent; } QScrollBar:vertical { width: 6px; }')
        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setSpacing(6)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._results_container)
        layout.addWidget(scroll, 1)

        self._switch_mode('parents')

    def _switch_mode(self, mode):
        self._mode = mode
        for sid, btn in self._sub_btns.items():
            active = sid == mode
            btn.setProperty('active', active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._update_results()

    def _lookup_tribe(self, key):
        if not self._breeding_data:
            return None, {}, ''
        pi = self._breeding_data.get('pal_info', {})
        if key in pi:
            info = pi[key]
            return key, info, info.get('icon', '')
        for k, v in pi.items():
            if k.lower() == key.lower():
                return k, v, v.get('icon', '')
        return None, {}, ''

    def _open_pal_dialog(self):
        dlg = _SelectPalDialog(self)
        if dlg.exec():
            asset = dlg.selected_asset
            tribe, info, icon = self._lookup_tribe(asset)
            if tribe:
                self._selected_tribe = tribe
                self._selected_name = info.get('name', dlg.selected_name)
                self._selected_icon = icon
                self._selected_label.setText(self._selected_name)
            else:
                self._selected_tribe = asset
                self._selected_name = dlg.selected_name
                self._selected_icon = ''
                self._selected_label.setText(dlg.selected_name)
            self._update_results()

    def _update_results(self):
        for i in reversed(range(self._results_layout.count())):
            w = self._results_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        if not self._selected_tribe or not self._breeding_data:
            empty = QLabel(t('breeding.no_selection') if t else 'Select a pal to see breeding combinations')
            empty.setStyleSheet('color: #64748b; font-size: 13px; padding: 20px;')
            empty.setAlignment(Qt.AlignCenter)
            self._results_layout.addWidget(empty)
            return
        bd = self._breeding_data
        pal_info = bd.get('pal_info', {})
        if self._mode == 'parents':
            self._show_parents(self._selected_tribe, self._selected_name, self._selected_icon, bd, pal_info)
        else:
            self._show_children(self._selected_tribe, self._selected_name, self._selected_icon, bd, pal_info)

    def _show_parents(self, target_tribe, target_name, target_icon, bd, pal_info, target_info=None):
        pal_info_map = pal_info
        if target_info is None:
            target_info = pal_info_map.get(target_tribe, {})
        title = QLabel(_fmt(t('breeding.parents_for') if t else 'Parents for {name}', target_name))
        title.setStyleSheet('color: #e2e8f0; font-size: 14px; font-weight: 600; padding: 4px 0;')
        self._results_layout.addWidget(title)

        target_row = QHBoxLayout()
        target_row.setSpacing(8)
        icon_lbl = PalIconLabel(target_icon, 48)
        target_row.addWidget(icon_lbl)
        name_lbl = QLabel(f'<b style="color:#7DD3FC;font-size:15px;">{target_name}</b>')
        name_lbl.setTextFormat(Qt.RichText)
        target_row.addWidget(name_lbl)
        target_row.addStretch()
        tw = QWidget()
        tw.setLayout(target_row)
        self._results_layout.addWidget(tw)

        total = 0
        for ctype, clist, label in [
            ('unique', bd.get('child_to_parents_unique', {}).get(target_tribe, []), t('breeding.unique') if t else 'Unique Combos'),
            ('formula', bd.get('child_to_parents_formula', {}).get(target_tribe, []), t('breeding.formula') if t else 'Formula Combos'),
        ]:
            if not clist:
                continue
            total += len(clist)
            sec = QLabel(f'<b style="color:#94a3b8;font-size:12px;padding:8px 0 2px 0;">{label}</b>')
            sec.setTextFormat(Qt.RichText)
            self._results_layout.addWidget(sec)
            for pair in clist:
                card = self._make_pair_card(pair['parent_a'], pair['parent_b'], target_tribe, pal_info_map)
                self._results_layout.addWidget(card)
        if total == 0:
            if target_info.get('ignore_combi', False):
                msg = QLabel(t('breeding.no_breed') if t else 'This pal cannot breed')
            else:
                msg = QLabel(t('breeding.no_combos') if t else 'No breeding combos found')
            msg.setStyleSheet('color: #64748b; font-size: 12px; padding: 8px;')
            self._results_layout.addWidget(msg)
        count = QLabel(f'<span style="color:#64748b;font-size:11px;">{total} combo(s)</span>')
        count.setTextFormat(Qt.RichText)
        self._results_layout.addWidget(count)

    def _show_children(self, target_tribe, target_name, target_icon, bd, pal_info, target_info=None):
        pal_info_map = pal_info
        if target_info is None:
            target_info = pal_info_map.get(target_tribe, {})
        title = QLabel(_fmt(t('breeding.children_for') if t else 'Children for {name}', target_name))
        title.setStyleSheet('color: #e2e8f0; font-size: 14px; font-weight: 600; padding: 4px 0;')
        self._results_layout.addWidget(title)

        target_row = QHBoxLayout()
        target_row.setSpacing(8)
        icon_lbl = PalIconLabel(target_icon, 48)
        target_row.addWidget(icon_lbl)
        name_lbl = QLabel(f'<b style="color:#7DD3FC;font-size:15px;">{target_name}</b>')
        name_lbl.setTextFormat(Qt.RichText)
        target_row.addWidget(name_lbl)
        target_row.addStretch()
        tw = QWidget()
        tw.setLayout(target_row)
        self._results_layout.addWidget(tw)

        children_map = {}
        for ctype, clist, clabel in [
            ('unique', bd.get('child_to_parents_unique', {}), 'unique'),
            ('formula', bd.get('child_to_parents_formula', {}), 'formula'),
        ]:
            for child_tribe, pairs in clist.items():
                for pair in pairs:
                    if pair['parent_a'] == target_tribe or pair['parent_b'] == target_tribe:
                        partner = pair['parent_b'] if pair['parent_a'] == target_tribe else pair['parent_a']
                        if child_tribe not in children_map:
                            children_map[child_tribe] = {'partner': partner, 'type': ctype}

        total = 0
        for child_tribe, data in sorted(children_map.items(), key=lambda x: pal_info_map.get(x[0], {}).get('name', x[0])):
            total += 1
            partner = data['partner']
            card = self._make_child_card(target_tribe, partner, child_tribe, pal_info_map)
            self._results_layout.addWidget(card)
        if total == 0:
            if target_info.get('ignore_combi', False):
                msg = QLabel(t('breeding.no_breed') if t else 'This pal cannot breed')
            else:
                msg = QLabel(t('breeding.no_combos') if t else 'No breeding combos found')
            msg.setStyleSheet('color: #64748b; font-size: 12px; padding: 8px;')
            self._results_layout.addWidget(msg)
        count = QLabel(f'<span style="color:#64748b;font-size:11px;">{total} child combo(s)</span>')
        count.setTextFormat(Qt.RichText)
        self._results_layout.addWidget(count)

    def _make_pair_card(self, parent_a, parent_b, child, pal_info_map):
        frame = QFrame()
        frame.setStyleSheet(_CARD_STYLE)
        grid = QHBoxLayout(frame)
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setSpacing(0)
        self._add_pal_unit(grid, parent_a, pal_info_map, 1)
        sep1 = QLabel(PLUS)
        sep1.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep1.setStyleSheet('color: #94a3b8; padding: 0 4px;')
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setFixedWidth(36)
        grid.addWidget(sep1)
        self._add_pal_unit(grid, parent_b, pal_info_map, 1)
        sep2 = QLabel(ARROW_RIGHT)
        sep2.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep2.setStyleSheet('color: #7DD3FC; padding: 0 4px;')
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setFixedWidth(36)
        grid.addWidget(sep2)
        self._add_pal_unit(grid, child, pal_info_map, 1)
        return frame

    def _make_child_card(self, parent, partner, child, pal_info_map):
        frame = QFrame()
        frame.setStyleSheet(_CARD_STYLE)
        grid = QHBoxLayout(frame)
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setSpacing(0)
        self._add_pal_unit(grid, parent, pal_info_map, 1)
        sep1 = QLabel(PLUS)
        sep1.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep1.setStyleSheet('color: #94a3b8; padding: 0 4px;')
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setFixedWidth(36)
        grid.addWidget(sep1)
        self._add_pal_unit(grid, partner, pal_info_map, 1)
        sep2 = QLabel(ARROW_RIGHT)
        sep2.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep2.setStyleSheet('color: #7DD3FC; padding: 0 4px;')
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setFixedWidth(36)
        grid.addWidget(sep2)
        self._add_pal_unit(grid, child, pal_info_map, 1)
        return frame

    def _add_pal_unit(self, layout, tribe, pal_info_map, stretch=1):
        info = pal_info_map.get(tribe, {})
        name = info.get('name', tribe)
        icon = info.get('icon', '')
        unit = QHBoxLayout()
        unit.setSpacing(5)
        unit.addStretch(1)
        il = PalIconLabel(icon, 48)
        unit.addWidget(il)
        nl = QLabel(f'<b style="font-size:14px;color:#e2e8f0;">{name}</b>')
        nl.setTextFormat(Qt.RichText)
        unit.addWidget(nl)
        unit.addStretch(1)
        uw = QWidget()
        uw.setLayout(unit)
        layout.addWidget(uw, stretch)

    def _load_data(self):
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'breedingdata.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._breeding_data = json.load(f)
            except Exception:
                self._breeding_data = None
        self._update_results()

    def refresh(self):
        self._load_data()

    def refresh_labels(self):
        for sid, skey in [('parents', 'Parents'), ('children', 'Children')]:
            if sid in self._sub_btns:
                self._sub_btns[sid].setText(t(f'breeding.mode.{sid}') if t else skey)
        self._select_btn.setText(f'{EGG}  {(t("breeding.select_pal") if t else "Select a Pal...")}')
        self._hint_label.setText(t('breeding.hint') if t else 'Click the button above to select a pal and view breeding combinations.')
        self._update_results()
