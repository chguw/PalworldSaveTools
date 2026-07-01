import copy
import os
import re
from PySide6.QtWidgets import QAbstractItemView, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QScrollBar, QSizePolicy, QVBoxLayout, QWidget
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from i18n import t
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import DIALOG_STYLE
from resource_resolver import resource_path
from palworld_aio.utils import extract_value, json_tools, resolve_name, safe_nested_get
from . import data as _data
from .data import _ensure_skill_data
from . import icons as _icons
from .icons import _partner_desc_to_html, _strip_prefix_label
from .pal_ops import _generate_pal_save_param, _get_raw_from_item, _learn_all_skills_raw, _register_pal_instance_to_guild
from .legacy_frame import PalFrame
from .pal_info_widget import PalInfoWidget
from .widgets import FramelessDialog, SkillSlotFrame
from .palbox_slot_widget import _PalSlotDelegate

def _show_learned_moves_dialog(raw, parent):
    if not isinstance(raw, dict):
        return
    mw_data = raw.get('MasteredWaza', {})
    if isinstance(mw_data, dict):
        mw_list = mw_data.get('value', {}).get('values', [])
    elif isinstance(mw_data, list):
        mw_list = mw_data
    else:
        mw_list = []
    dlg = FramelessDialog('edit_pals.learnt_skills_title', parent)
    dlg.set_title_text(t('edit_pals.learnt_skills_title'))
    dlg.setModal(True)
    dlg.setMinimumSize(420, 400)
    dlg.setMaximumSize(500, 600)
    inner = QWidget()
    inner.setObjectName('learntSkillsInner')
    inner.setStyleSheet('QWidget#learntSkillsInner { background: transparent; }')
    il = QVBoxLayout(inner)
    il.setContentsMargins(8, 4, 8, 8)
    il.setSpacing(4)
    _ensure_skill_data()
    count_lbl = QLabel(t('edit_pals.learnt_skills_count', count=len(mw_list)))
    count_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #9CA3AF; background: transparent; border: none; padding: 2px 4px;')
    il.addWidget(count_lbl)
    search_edit = QLineEdit()
    search_edit.setPlaceholderText(t('edit_pals.learnt_skills_search'))
    search_edit.setStyleSheet('QLineEdit { background: rgba(0,0,0,0.3); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 4px 8px; font-size: 11px; } QLineEdit:focus { border-color: rgba(125,211,252,0.5); }')
    il.addWidget(search_edit)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; } QScrollBar:vertical { width: 4px; background: rgba(255,255,255,0.02); border-radius: 2px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.15); border-radius: 2px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.3); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }')
    scroll_ct = QWidget()
    scroll_ct.setObjectName('learntSkillsScrollCt')
    scroll_ct.setStyleSheet('QWidget#learntSkillsScrollCt { background: transparent; border: none; }')
    scl = QVBoxLayout(scroll_ct)
    scl.setContentsMargins(2, 2, 2, 2)
    scl.setSpacing(2)
    scl.addStretch()
    skill_slots = []
    def _make_handler(sv, parent_dlg, slot_widget, outer_layout, count_label):
        def handler(event):
            event.accept()
            sname = PalFrame._SKILLMAP.get(sv.split('::')[-1].lower(), sv.split('::')[-1])
            confirm = show_question(parent_dlg, t('edit_pals.learnt_skills_title'), t('edit_pals.confirm_remove_skill', name=sname))
            if not confirm:
                return
            mw_data = raw.get('MasteredWaza', {})
            if isinstance(mw_data, dict):
                mlist = mw_data.get('value', {}).get('values', [])
            elif isinstance(mw_data, list):
                mlist = mw_data
            else:
                mlist = []
            if sv in mlist:
                mlist.remove(sv)
                new_mw = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': mlist}, 'type': 'ArrayProperty'}
                raw['MasteredWaza'] = new_mw
            outer_layout.removeWidget(slot_widget)
            slot_widget.deleteLater()
            skill_slots[:] = [(s, n) for s, n in skill_slots if s is not slot_widget]
            search_edit.clear()
            remaining = outer_layout.count() - 1
            count_label.setText(t('edit_pals.learnt_skills_count', count=remaining))
            if remaining == 0:
                nl = QLabel('--')
                nl.setAlignment(Qt.AlignCenter)
                nl.setStyleSheet('font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.25); background: transparent; border: none; padding: 20px;')
                outer_layout.insertWidget(0, nl)
        return handler
    def _filter_skills(text):
        text = text.lower()
        visible = 0
        for slot, name_lower in skill_slots:
            if text in name_lower:
                slot.show()
                visible += 1
            else:
                slot.hide()
        count_lbl.setText(t('edit_pals.learnt_skills_count', count=visible))
    search_edit.textChanged.connect(_filter_skills)
    if not mw_list:
        nl = QLabel('--')
        nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet('font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.25); background: transparent; border: none; padding: 20px;')
        scl.insertWidget(0, nl)
    else:
        elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
        for idx, skill_val in enumerate(mw_list):
            if isinstance(skill_val, dict):
                skill_val = skill_val.get('value', '')
            if not skill_val:
                continue
            w_clean = skill_val.split('::')[-1].lower()
            move_name = PalFrame._SKILLMAP.get(w_clean, skill_val.split('::')[-1])
            skill_info = _data._SKILL_DATA.get(w_clean, {}) if isinstance(_data._SKILL_DATA, dict) else {}
            skill_elem = skill_info.get('element', 'Normal')
            skill_power = skill_info.get('power', 0)
            elem_color = elem_colors.get(skill_elem, '#9CA3AF')
            slot = SkillSlotFrame()
            slot.setStyleSheet('SkillSlotFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; } SkillSlotFrame:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
            slot.setFixedHeight(28)
            slot.setCursor(Qt.PointingHandCursor)
            slot._skill_raw_value = skill_val
            slot._skill_idx = idx
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
                ep = _icons._get_element_pixmap(skill_elem, 'small', 16)
                if ep:
                    elem_badge.setScaledContents(True)
                    elem_badge.setPixmap(ep)
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
            if skill_info:
                tip_parts = [f'<b>{move_name}</b>', f'Element: {skill_elem}', f'Power: {skill_power}']
                cd = skill_info.get('cooldown', 0)
                if cd:
                    tip_parts.append(f'Cooldown: {cd}s')
                desc = skill_info.get('description', '')
                if desc:
                    tip_parts.append('')
                    tip_parts.append(desc)
                slot.setToolTip('<br>'.join(tip_parts))
            slot.mousePressEvent = _make_handler(skill_val, dlg, slot, scl, count_lbl)
            scl.insertWidget(scl.count() - 1, slot)
            skill_slots.append((slot, move_name.lower()))
    def _rebuild_list():
        while scl.count() > 1:
            item = scl.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        mw_data = raw.get('MasteredWaza', {})
        if isinstance(mw_data, dict):
            new_mw_list = mw_data.get('value', {}).get('values', [])
        elif isinstance(mw_data, list):
            new_mw_list = mw_data
        else:
            new_mw_list = []
        count_lbl.setText(t('edit_pals.learnt_skills_count', count=len(new_mw_list)))
        search_edit.clear()
        skill_slots.clear()
        if not new_mw_list:
            nl = QLabel('--')
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet('font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.25); background: transparent; border: none; padding: 20px;')
            scl.insertWidget(0, nl)
        else:
            elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
            for idx, skill_val in enumerate(new_mw_list):
                if isinstance(skill_val, dict):
                    skill_val = skill_val.get('value', '')
                if not skill_val:
                    continue
                w_clean = skill_val.split('::')[-1].lower()
                move_name = PalFrame._SKILLMAP.get(w_clean, skill_val.split('::')[-1])
                skill_info = _data._SKILL_DATA.get(w_clean, {}) if isinstance(_data._SKILL_DATA, dict) else {}
                skill_elem = skill_info.get('element', 'Normal')
                skill_power = skill_info.get('power', 0)
                elem_color = elem_colors.get(skill_elem, '#9CA3AF')
                slot = SkillSlotFrame()
                slot.setStyleSheet('SkillSlotFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; } SkillSlotFrame:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
                slot.setFixedHeight(28)
                slot.setCursor(Qt.PointingHandCursor)
                slot._skill_raw_value = skill_val
                slot._skill_idx = idx
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
                    ep = _icons._get_element_pixmap(skill_elem, 'small', 16)
                    if ep:
                        elem_badge.setScaledContents(True)
                        elem_badge.setPixmap(ep)
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
                if skill_info:
                    tip_parts = [f'<b>{move_name}</b>', f'Element: {skill_elem}', f'Power: {skill_power}']
                    cd = skill_info.get('cooldown', 0)
                    if cd:
                        tip_parts.append(f'Cooldown: {cd}s')
                    desc = skill_info.get('description', '')
                    if desc:
                        tip_parts.append('')
                        tip_parts.append(desc)
                    slot.setToolTip('<br>'.join(tip_parts))
                slot.mousePressEvent = _make_handler(skill_val, dlg, slot, scl, count_lbl)
                scl.insertWidget(scl.count() - 1, slot)
                skill_slots.append((slot, move_name.lower()))
    scroll.setWidget(scroll_ct)
    il.addWidget(scroll, 1)
    btn_row = QHBoxLayout()
    learn_all_btn = QPushButton(t('edit_pals.learnt_skills_learn_all'))
    learn_all_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
    learn_all_btn.clicked.connect(lambda: (_learn_all_skills_raw(raw), _rebuild_list()))
    btn_row.addWidget(learn_all_btn)
    btn_row.addStretch()
    close_btn = QPushButton('Close')
    close_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.1); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.2); color: #FFFFFF; }')
    close_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(close_btn)
    il.addLayout(btn_row)
    dlg.content_layout.addWidget(inner)
    dlg.exec()
_EDITABLE_KEYS = {'Level', 'Exp', 'Gender', 'Talent_HP', 'Talent_Shot', 'Talent_Defense', 'Rank_HP', 'Rank_Attack', 'Rank_Defence', 'Rank_CraftSpeed', 'Rank', 'FriendshipPoint', 'IsRarePal', 'bIsAwakening', 'bImportedCharacter', 'FavoriteIndex', 'EquipWaza', 'MasteredWaza', 'PassiveSkillList', 'Hp', 'MaxHP', 'GotWorkSuitabilityAddRankList'}
class BulkSyncPalDialog(FramelessDialog):
    def __init__(self, pal_item, pal_editor, parent=None, candidates=None):
        super().__init__('edit_pals.bulk_sync_pal_title', parent)
        self.pal_editor = pal_editor
        raw = _get_raw_from_item(pal_item)
        if not raw:
            self.reject()
            return
        cid = extract_value(raw, 'CharacterID', '')
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        self.set_title_text(f"{t('edit_pals.bulk_sync_pal_title')} - {pal_name}")
        self.setModal(True)
        self.setMinimumSize(740, 750)
        self._all_candidates = []
        if candidates is not None:
            self._all_candidates = list(candidates)
        else:
            base_id = cid.lower().replace('boss_', '')
            seen = set()
            for pi in list(pal_editor.party_pals.values()):
                pr = _get_raw_from_item(pi)
                if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                    inst_id = str(pi.get('key', {}).get('InstanceId', {}).get('value', ''))
                    if inst_id not in seen:
                        seen.add(inst_id)
                        self._all_candidates.append(pi)
            for pi in pal_editor.palbox_pal_dict.values():
                pr = _get_raw_from_item(pi)
                if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                    inst_id = str(pi.get('key', {}).get('InstanceId', {}).get('value', ''))
                    if inst_id not in seen:
                        seen.add(inst_id)
                        self._all_candidates.append(pi)
        inner = QWidget()
        inner.setStyleSheet('QWidget#bulkSyncInner { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        header = QHBoxLayout()
        header.setSpacing(8)
        icon_path = _icons._get_pal_icon_path(cid)
        pix = _icons._get_cached_pixmap(icon_path, 48)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        if pix:
            icon_lbl.setPixmap(pix)
        icon_lbl.setStyleSheet('background: transparent; border: none;')
        header.addWidget(icon_lbl)
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        name_lbl = QLabel(pal_name)
        name_lbl.setStyleSheet('font-size: 14px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        info_col.addWidget(name_lbl)
        count_lbl = QLabel(t('edit_pals.bulk_sync_found', count=len(self._all_candidates), name=pal_name))
        count_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #9CA3AF; background: transparent; border: none;')
        info_col.addWidget(count_lbl)
        info_col.addStretch()
        header.addLayout(info_col, 1)
        il.addLayout(header)
        body = QHBoxLayout()
        body.setSpacing(6)
        left_col = QVBoxLayout()
        left_col.setSpacing(3)
        pal_list_label = QLabel(t('edit_pals.select_pals_to_sync'))
        pal_list_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        left_col.addWidget(pal_list_label)
        pal_scroll = QScrollArea()
        pal_scroll.setWidgetResizable(True)
        pal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pal_scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; } QScrollBar:vertical { width: 4px; background: rgba(255,255,255,0.02); border-radius: 2px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.15); border-radius: 2px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.3); }')
        pal_list_inner = QWidget()
        pal_list_inner.setStyleSheet('background: transparent; border: none;')
        pal_list_layout = QVBoxLayout(pal_list_inner)
        pal_list_layout.setContentsMargins(2, 2, 2, 2)
        pal_list_layout.setSpacing(2)
        self._checkboxes = []
        for pi in self._all_candidates:
            pr = _get_raw_from_item(pi)
            nick = extract_value(pr, 'NickName', '') if pr else ''
            lv = extract_value(pr, 'Level', 1) if pr else 1
            display = f'Lv.{lv} {nick}' if nick else f'Lv.{lv} {pal_name}'
            cb = ToggleCheckBtn(display)
            cb.setChecked(True)
            pal_list_layout.addWidget(cb)
            self._checkboxes.append(cb)
        pal_scroll.setWidget(pal_list_inner)
        left_col.addWidget(pal_scroll, 1)
        body.addLayout(left_col, 1)
        right_col = QVBoxLayout()
        right_col.setSpacing(3)
        preview_label = QLabel(t('edit_pals.bulk_sync_preview'))
        preview_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        right_col.addWidget(preview_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; } QScrollBar:vertical { width: 4px; background: rgba(255,255,255,0.02); border-radius: 2px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.15); border-radius: 2px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.3); }')
        self._pal_info = PalInfoWidget()
        self._pal_info.set_clicked_pal(pal_item)
        self._pal_info.setStyleSheet(self._pal_info.styleSheet() + '\nQWidget#palInfoInner { border: none; }')
        self._pal_info.setMinimumWidth(0)
        scroll.setWidget(self._pal_info)
        right_col.addWidget(scroll, 1)
        body.addLayout(right_col, 1)
        il.addLayout(body, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.bulk_sync_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        sel_all_btn = QPushButton(t('edit_pals.bulk_sync_all'))
        sel_all_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.15); color: #FFFFFF; }')
        sel_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        btn_row.addWidget(sel_all_btn)
        sel_none_btn = QPushButton(t('edit_pals.bulk_sync_none'))
        sel_none_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.04); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.08); color: #FFFFFF; }')
        sel_none_btn.clicked.connect(lambda: self._set_all_checked(False))
        btn_row.addWidget(sel_none_btn)
        apply_btn = QPushButton(t('edit_pals.bulk_sync_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
        apply_btn.clicked.connect(lambda: self._on_apply(pal_name))
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        self.content_layout.addWidget(inner)
    def _set_all_checked(self, checked):
        for cb in self._checkboxes:
            cb.setChecked(checked)
    def _on_apply(self, pal_name):
        current_raw = self._pal_info._raw if hasattr(self._pal_info, '_raw') and self._pal_info._raw else None
        if not current_raw:
            self.reject()
            return
        selected = []
        for pi, cb in zip(self._all_candidates, self._checkboxes):
            if cb.isChecked():
                selected.append(pi)
        if not selected:
            show_warning(self, 'Bulk Sync', t('edit_pals.bulk_sync_no_selection'))
            return
        for pal_item in selected:
            target_raw = _get_raw_from_item(pal_item)
            if not target_raw:
                continue
            for key in _EDITABLE_KEYS:
                if key in current_raw:
                    target_raw[key] = copy.deepcopy(current_raw[key])
                else:
                    target_raw.pop(key, None)
            if 'EquipWaza' in target_raw:
                ew = target_raw['EquipWaza']
                ew_list = ew.get('value', {}).get('values', []) if isinstance(ew, dict) else ew if isinstance(ew, list) else []
                if isinstance(ew_list, list):
                    normalized = []
                    for v in ew_list:
                        if v and '::' not in v:
                            normalized.append(f'EPalWazaID::{v}')
                        else:
                            normalized.append(v)
                    if isinstance(ew, dict):
                        ew['value']['values'] = normalized
                    else:
                        target_raw['EquipWaza'] = normalized
        self.pal_editor.pal_info._refresh()
        self.pal_editor._update_party_slots()
        self.pal_editor._update_palbox_page()
        show_information(self, 'Bulk Sync', t('edit_pals.bulk_sync_success', count=len(selected), name=pal_name))
        self.accept()
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
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Search:'))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText('Type to filter pals...')
        filter_layout.addWidget(self._search_edit)
        self._show_standard_chk = ToggleCheckBtn(t('edit_pals.show_standard') if t else 'Standard')
        self._show_standard_chk.setChecked(True)
        self._show_standard_chk.toggled.connect(self._filter_pal_list)
        filter_layout.addWidget(self._show_standard_chk)
        self._show_boss_chk = ToggleCheckBtn(t('edit_pals.show_boss') if t else 'Boss')
        self._show_boss_chk.toggled.connect(self._filter_pal_list)
        filter_layout.addWidget(self._show_boss_chk)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
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
        pal_passives = {}
        pal_reference_passives = {}
        pal_main_values = {}
        pal_overwrite_effects = {}
        pal_elements = {}
        self._npc_assets = set()
        self._named_npc_assets = set()
        try:
            base_dir = constants.get_base_path()
            cp = resource_path(base_dir, 'game_data', 'characters.json')
            cd = json_tools.load(cp)
            for p in cd.get('pals', []):
                if isinstance(p, dict):
                    if p.get('description'):
                        pal_descs[p['asset'].lower()] = p['description']
                        pal_passives[p['asset'].lower()] = p.get('passives', [])
                        rp = p.get('reference_passives', [])
                        if rp:
                            pal_reference_passives[p['asset'].lower()] = rp
                        mv = p.get('active_skill_main_value', [])
                        if mv:
                            pal_main_values[p['asset'].lower()] = mv
                        ov = p.get('active_skill_overwrite_effect', [])
                        if ov:
                            pal_overwrite_effects[p['asset'].lower()] = ov
                    elems = p.get('elements', {})
                    if elems:
                        pal_elements[p['asset'].lower()] = elems
            for p in cd.get('npcs', []):
                if isinstance(p, dict) and p.get('asset'):
                    self._npc_assets.add(p['asset'].lower())
            exports_dir = os.path.join(constants.get_base_path(), '..', '..', 'Exports', 'Pal', 'Content', 'Pal', 'DataTable')
            unique_npc_path = os.path.join(exports_dir, 'Character', 'DT_UniqueNPC.json')
            if os.path.exists(unique_npc_path):
                ud = json_tools.load(unique_npc_path)
                urows = {}
                if isinstance(ud, list):
                    for tbl in ud:
                        if isinstance(tbl, dict):
                            urows.update(tbl.get('Rows', {}))
                elif isinstance(ud, dict):
                    urows = ud.get('Rows', {})
                for v in urows.values():
                    if isinstance(v, dict):
                        cid = v.get('CharacterID', '')
                        if cid:
                            self._named_npc_assets.add(cid.lower())
        except:
            pass
        def on_select(item):
            if item:
                self.selected_pal['asset'] = item.data(Qt.UserRole)
                self.selected_pal['name'] = item.text()
        self.pal_list.itemClicked.connect(on_select)
        self.pal_list.itemDoubleClicked.connect(lambda item: (on_select(item), self._on_create()))
        self._pal_descs_cache = pal_descs
        self._pal_passives_cache = pal_passives
        self._pal_reference_passives_cache = pal_reference_passives
        self._pal_main_values_cache = pal_main_values
        self._pal_overwrite_effects_cache = pal_overwrite_effects
        self._pal_elements_cache = pal_elements
        self._filter_pal_list()
        self._search_edit.textChanged.connect(self._filter_pal_list)
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
        ok_btn = QPushButton(t('edit_pals.create'))
        ok_btn.clicked.connect(self._on_create)
        nick_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('edit_pals.cancel'))
        cancel_btn.clicked.connect(self.reject)
        nick_layout.addWidget(cancel_btn)
        layout.addLayout(nick_layout)
    def _filter_pal_list(self):
        search_text = self._search_edit.text().lower() if hasattr(self, '_search_edit') else ''
        show_standard = self._show_standard_chk.isChecked() if hasattr(self, '_show_standard_chk') else True
        show_boss = self._show_boss_chk.isChecked() if hasattr(self, '_show_boss_chk') else False
        self.pal_list.clear()
        for asset, name in sorted(PalFrame._NAMEMAP.items(), key=lambda kv: (kv[1], kv[0])):
            asset_lower = asset.lower()
            if any((asset_lower.startswith(p) for p in ('summon_', 'quest_', 'raid_', 'predator_', 'police_'))):
                continue
            if 'worldtreedragon' in asset_lower:
                continue
            if 'oilrig' in asset_lower:
                continue
            if 'tower' in asset_lower:
                continue
            if '_bossrush' in asset_lower:
                continue
            if asset_lower.startswith('gym_') and (not asset_lower.endswith('_otomo')):
                continue
            otomo_key = asset_lower + '_otomo'
            if otomo_key in PalFrame._NAMEMAP:
                continue
            boss_otomo_key = 'boss_' + asset_lower + '_otomo'
            if boss_otomo_key in PalFrame._NAMEMAP:
                continue
            base_id = asset_lower
            for prefix in ('boss_', 'gym_'):
                if base_id.startswith(prefix):
                    base_id = base_id[len(prefix):]
            base_id = re.sub('_\\d+$', '', base_id)
            base_id = re.sub('_avatar|_servant|_otomo', '', base_id)
            zukan = PalFrame._PAL_ZUKAN.get(base_id, -99)
            if zukan == -99:
                pass
            elif zukan < 0 and 'Yakushima' not in asset and not base_id.startswith('yakushima'):
                continue
            if search_text and search_text not in name.lower() and (search_text not in asset.lower()):
                continue
            is_variant = any((asset.upper().startswith(p) for p in _data._BOSS_PREFIXES))
            if is_variant and not show_boss:
                continue
            if (not is_variant) and not show_standard:
                continue
            li = QListWidgetItem(name)
            li.setData(Qt.UserRole, asset)
            pix = _icons._get_cached_pixmap(_icons._get_pal_icon_path(asset), 48)
            if pix:
                li.setIcon(QIcon(pix))
            pdesc = self._pal_descs_cache.get(asset.lower(), '')
            passives = self._pal_passives_cache.get(asset.lower(), [])
            tip = f'<b>{name}</b><br>ID: {asset}'
            if pdesc:
                resolved = _icons._resolve_partner_desc(pdesc, passives, 0, self._pal_main_values_cache.get(asset.lower()), self._pal_overwrite_effects_cache.get(asset.lower()), passives, reference_passives=self._pal_reference_passives_cache.get(asset.lower(), []))
                elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
                html_desc = _partner_desc_to_html(resolved, elem_colors, tooltip=True)
                tip += f'<br><br>{html_desc}'
            li.setToolTip(tip)
            li.setSizeHint(QSize(80, 80))
            if is_variant:
                badge = _icons._get_boss_alpha_pixmap(14)
                if badge and (not badge.isNull()):
                    li.setData(Qt.UserRole + 1, True)
            elems = self._pal_elements_cache.get(asset.lower(), {})
            if elems:
                li.setData(Qt.UserRole + 2, list(elems.keys())[:2])
            self.pal_list.addItem(li)
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
        slot_to_use = (self.pal_editor.current_box_index - 1) * 30 + self.slot_index if not self.is_party else self.slot_index
        pal_item = _generate_pal_save_param(cid, nick, owner_uid, container_id, slot_to_use, group_id)
        instance_id = pal_item['key']['InstanceId']['value']
        cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        cmap.append(pal_item)
        char_containers = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
        for cont in char_containers:
            if safe_nested_get(cont, ['key', 'ID', 'value']) == container_id:
                slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], [])
                slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_to_use}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                break
        _register_pal_instance_to_guild(instance_id, group_id)
        if self.is_party:
            self.pal_editor.party_pals[self.slot_index] = pal_item
        else:
            self.pal_editor.palbox_pal_dict[slot_to_use] = pal_item
        self.created_item = {'character_id': cid, 'nickname': nick, 'container_id': container_id, 'slot_index': slot_to_use, 'pal_item': pal_item}
        self.accept()