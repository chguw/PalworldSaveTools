import os
from functools import partial
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QEvent, QObject, QPoint, QTimer
from PySide6.QtGui import QPixmap
from i18n import t
import nerdfont as nf
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from resource_resolver import resource_path
from palworld_aio.utils import extract_value, safe_nested_get, calculate_max_hp
from palworld_aio.ui.chrome.styles import slot_full, slot_selected, TOOLTIP_STYLE, INPUT_DIALOG_STYLE
from palworld_aio.ui.dialogs.skill_picker import SkillPicker
from palsav import json_tools
from . import data as _data
from . import icons as _icons
from .data import _ensure_passive_data, _ensure_friendship_thresholds, _ensure_skill_data
from .pal_ops import _get_effective_work_suitabilities, _set_work_suitability, _learn_all_skills_raw, _toggle_boss_raw, _toggle_lucky_raw
from .widgets import PassiveEffectOverlay
from .legacy_frame import PalFrame
from .icons import _strip_prefix_label


class PalInfoHandlerMixin:
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if obj is self.name_lbl:
                    self._on_name_click()
                    return True
                if hasattr(obj, '_star_idx'):
                    self._on_star_click(obj._star_idx)
                    return True
                if obj is self.level_num_lbl:
                    self._on_level_click()
                    return True
                if obj is self.trust_bar or obj is self.trust_icon:
                    self._on_trust_click()
                    return True
                if obj in (self.ivs_hp_lbl, self.ivs_atk_lbl, self.ivs_def_lbl):
                    self._on_talent_click(obj)
                    return True
                if obj in (self.soul_hp_lbl, self.soul_atk_lbl, self.soul_def_lbl, self.soul_craft_lbl):
                    self._on_soul_click(obj)
                    return True
                if hasattr(obj, '_skill_slot_idx'):
                    self._on_active_skill_click(obj._skill_slot_idx, obj.mapToGlobal(QPoint(0, obj.height())))
                    return True
                if hasattr(obj, '_ws_key') and obj._ws_key:
                    self._on_work_skill_click(obj._ws_key, obj)
                    return True
            elif event.button() == Qt.RightButton:
                if hasattr(obj, '_skill_slot_idx'):
                    self._set_active_skill(obj._skill_slot_idx, '')
                    return True
                if hasattr(obj, '_passive_index'):
                    self._set_passive_skill(obj._passive_index, '')
                    return True
        if event.type() == QEvent.Type.Enter and hasattr(obj, '_stat_tip_text') and hasattr(self, '_stat_tip'):
            self._stat_tip.setText(obj._stat_tip_text)
            self._stat_tip.adjustSize()
            g = obj.mapToGlobal(QPoint(obj.width() + 4, 0))
            screen = QApplication.primaryScreen().availableGeometry()
            if g.x() + self._stat_tip.width() > screen.right() - 4:
                g.setX(obj.mapToGlobal(QPoint(-self._stat_tip.width() - 4, 0)).x())
            self._stat_tip.move(g)
            self._stat_tip.show()
            return True
        if event.type() == QEvent.Type.Leave:
            if hasattr(self, '_stat_tip') and self._stat_tip.isVisible():
                self._stat_tip.hide()
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
                self._raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': text}
                self._refresh()

    def _on_gender_click(self):
        if not self._raw:
            return
        gender_data = extract_value(self._raw, 'Gender', {})
        if isinstance(gender_data, dict) and 'value' in gender_data:
            current = gender_data['value']
        elif isinstance(gender_data, str):
            current = gender_data
        else:
            current = 'EPalGenderType::Female'
        new = 'EPalGenderType::Male' if 'Female' in current else 'EPalGenderType::Female'
        self._raw['Gender'] = {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': new}}
        self._refresh()

    def _on_star_click(self, star_idx):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'Rank', 0))
        new_r = star_idx + 2
        if new_r == cur:
            new_r = 1
        self._raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': new_r}}
        self._recalc_hp()
        self._refresh()

    def _start_star_shine(self):
        if hasattr(self, '_star_shine_timer') and self._star_shine_timer:
            return
        self._star_shine_timer = QTimer()
        self._star_shine_timer.timeout.connect(self._tick_star_shine)
        self._star_shine_timer.start(1200)

    def _stop_star_shine(self):
        if hasattr(self, '_star_shine_timer') and self._star_shine_timer:
            self._star_shine_timer.stop()
            self._star_shine_timer = None

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

    def _on_work_skill_click(self, ws_key, lbl):
        if not self._raw:
            return
        effective = _get_effective_work_suitabilities(self._raw)
        cur = effective.get(ws_key, 0)
        cid = extract_value(self._raw, 'CharacterID', '')
        base_data = _data.get_pal_base_data(cid)
        ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
        base_level = ws_base.get(ws_key, 0)
        display_name = self._WORK_SUITABILITY_DISPLAY.get(ws_key, ws_key)
        dlg = QInputDialog(self)
        dlg.setWindowTitle(f"{display_name} {t('edit_pals.work_skill_level')}")
        dlg.setLabelText(t('edit_pals.work_skill_level_msg', skill=display_name))
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(base_level, 10)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            new_level = dlg.intValue()
            _set_work_suitability(self._raw, ws_key, new_level)
            self._refresh()

    def _on_trust_click(self):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'FriendshipPoint', 0))
        dlg = QInputDialog(self)
        cur_rank = 0
        thr = _ensure_friendship_thresholds()
        for r in range(len(thr) - 1, 0, -1):
            if cur >= thr[r]:
                cur_rank = r
                break
        dlg = QInputDialog(self)
        dlg.setWindowTitle(t('edit_pals.set_trust'))
        dlg.setLabelText(t('edit_pals.set_trust_rank_msg'))
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(0, 10)
        dlg.setIntValue(cur_rank)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            rank = dlg.intValue()
            fp = thr[rank] if rank < len(thr) else 200000
            self._raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': fp}
            self._recalc_hp()

    def _set_level(self, value):
        raw = self._raw
        cid = extract_value(raw, 'CharacterID', '')
        raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
        try:
            base_dir = constants.get_base_path()
            exp_table_path = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
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
        base = _data.get_pal_base_data(cid)
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

    def _on_active_skill_click(self, slot_idx, pos=None):
        cid = extract_value(self._raw, 'CharacterID', '') if self._raw else ''
        self._show_skill_picker(t('edit_pals.select_skill'), PalFrame._SKILLMAP, slot_idx, True, pos, pal_asset=cid)

    def _on_passive_click(self, slot_idx, pos=None):
        self._show_skill_picker(t('edit_pals.select_passive'), PalFrame._PASSMAP, slot_idx, False, pos)

    def _show_skill_picker(self, title, skill_map, slot_idx, is_active, pos=None, pal_asset=None):
        picker = SkillPicker(self)
        try:
            cur_data = self._raw.get('EquipWaza' if is_active else 'PassiveSkillList', {})
            cur_list = cur_data.get('value', {}).get('values', []) if isinstance(cur_data, dict) else cur_data if isinstance(cur_data, list) else []
            cur_val = cur_list[slot_idx] if slot_idx < len(cur_list) else ''
            if isinstance(cur_val, dict):
                cur_val = cur_val.get('value', '')
        except Exception:
            cur_val = ''
        skip_items = set()
        try:
            if is_active:
                ew = self._raw.get('EquipWaza', {})
                ew_list = ew.get('value', {}).get('values', []) if isinstance(ew, dict) else ew if isinstance(ew, list) else []
                for v in ew_list:
                    if v:
                        key = v.split('::')[-1].lower() if '::' in v else v.lower()
                        skip_items.add(key)
            else:
                ps = self._raw.get('PassiveSkillList', {})
                ps_list = ps.get('value', {}).get('values', []) if isinstance(ps, dict) else ps if isinstance(ps, list) else []
                for v in ps_list:
                    clean = v['value'] if isinstance(v, dict) else v
                    if clean:
                        skip_items.add(clean.lower())
        except Exception:
            pass
        result = picker.pick(skill_map, is_active, pos=pos, current_value=cur_val if isinstance(cur_val, str) else '', skip_items=skip_items, pal_asset=pal_asset)
        if result is None:
            return
        if result == '':
            asset = ''
        else:
            asset = None
            for a, n in skill_map.items():
                if n == result:
                    asset = a
                    break
            if not asset:
                asset_lower = result.lower()
                if asset_lower in skill_map:
                    asset = result
                else:
                    return
        QTimer.singleShot(0, lambda a=asset, s=slot_idx, ia=is_active: self._set_active_skill(s, a) if ia else self._set_passive_skill(s, a))

    def _set_active_skill(self, slot_idx, asset):
        if not self._raw:
            return
        ew_data = self._raw.get('EquipWaza', {})
        cur = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
        if not isinstance(cur, list):
            cur = []
        while len(cur) <= slot_idx:
            cur.append('')
        if asset and '::' not in asset:
            asset = f'EPalWazaID::{asset}'
        cur[slot_idx] = asset
        cur = [s for s in cur if s]
        self._raw['EquipWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': cur[:3]}, 'type': 'ArrayProperty'}
        self._refresh()

    def _set_passive_skill(self, slot_idx, asset):
        if not self._raw:
            return
        ps_data = self._raw.get('PassiveSkillList', {})
        cur = ps_data.get('value', {}).get('values', []) if isinstance(ps_data, dict) else ps_data if isinstance(ps_data, list) else []
        if not isinstance(cur, list):
            cur = []
        while len(cur) <= slot_idx:
            cur.append('')
        cur[slot_idx] = asset
        self._raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': cur[:4]}, 'type': 'ArrayProperty'}
        self._refresh()

    def _get_current_passive_list(self):
        if not self._raw:
            return []
        ps = self._raw.get('PassiveSkillList', {})
        cur = ps.get('value', {}).get('values', []) if isinstance(ps, dict) else ps if isinstance(ps, list) else []
        result = []
        for v in cur:
            clean = v['value'] if isinstance(v, dict) else v
            result.append(clean if isinstance(clean, str) else '')
        return result

    def _on_passive_loadout(self):
        base_dir = constants.get_src_path()
        loadouts_path = os.path.join(base_dir, 'data', 'configs', 'passive_loadouts.json')
        _ensure_passive_data()
        if os.path.exists(loadouts_path):
            try:
                loadouts = json_tools.load(loadouts_path)
            except Exception:
                loadouts = {}
        else:
            loadouts = {}
        from palworld_aio.editor.dialogs import ThemedDialog
        dlg = ThemedDialog(self)
        dlg.setWindowTitle(t('edit_pals.passive_loadouts'))
        dlg.setMinimumSize(420, 400)
        dlg.setMaximumSize(520, 500)
        inner = QWidget()
        inner.setStyleSheet('QWidget { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        list_lbl = QLabel(t('edit_pals.loadouts_saved'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        il.addWidget(list_lbl)
        list_widget = QListWidget()
        list_widget.setMouseTracking(True)
        list_widget.setStyleSheet('QListWidget { background: rgba(10,14,20,0.95); border: 1px solid rgba(125,211,252,0.15); border-radius: 4px; color: #E2E8F0; font-size: 10px; } QListWidget::item { padding: 6px 8px; } QListWidget::item:hover { background: rgba(125,211,252,0.08); } QListWidget::item:selected { background: rgba(125,211,252,0.15); color: #7DD3FC; }')
        for name in sorted(loadouts.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            list_widget.addItem(item)
        il.addWidget(list_widget, 1)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        save_btn = QPushButton(t('edit_pals.loadouts_save'))
        save_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(16,185,129,0.22); color: #FFFFFF; }')
        btn_row.addWidget(save_btn)
        load_btn = QPushButton(t('edit_pals.loadouts_apply'))
        load_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.22); color: #FFFFFF; }')
        btn_row.addWidget(load_btn)
        delete_btn = QPushButton(t('edit_pals.loadouts_delete_btn'))
        delete_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(251,113,133,0.22); color: #FFFFFF; }')
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        close_btn = QPushButton(t('edit_pals.loadouts_close'))
        close_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 20px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.16); color: #FFFFFF; }')
        btn_row.addWidget(close_btn)
        il.addLayout(btn_row)
        def _do_save():
            cur_list = self._get_current_passive_list()
            if not cur_list or all((not p for p in cur_list)):
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_no_passives'))
                return
            name, ok = QInputDialog.getText(dlg, t('edit_pals.loadouts_save_title'), t('edit_pals.loadouts_save_prompt'), text='')
            if not ok or not name.strip():
                return
            name = name.strip()
            loadouts[name] = cur_list
            try:
                os.makedirs(os.path.dirname(loadouts_path), exist_ok=True)
                json_tools.dump(loadouts, loadouts_path, indent=2)
            except Exception as e:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_save_error', error=str(e)))
                return
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            list_widget.addItem(item)
            show_information(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_saved_ok', name=name))
        def _do_load():
            sel = list_widget.currentItem()
            if not sel:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_select_first'))
                return
            name = sel.data(Qt.UserRole)
            passive_list = loadouts.get(name)
            if not passive_list:
                return
            if not self._raw:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_no_pal'))
                return
            self._raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': passive_list[:4]}, 'type': 'ArrayProperty'}
            self._refresh()
            show_information(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_applied', name=name))
        def _do_delete():
            sel = list_widget.currentItem()
            if not sel:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_select_first'))
                return
            name = sel.data(Qt.UserRole)
            confirm = show_question(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_delete_confirm', name=name))
            if not confirm:
                return
            loadouts.pop(name, None)
            try:
                json_tools.dump(loadouts, loadouts_path, indent=2)
            except Exception as e:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_delete_error', error=str(e)))
                return
            row = list_widget.row(sel)
            list_widget.takeItem(row)
            show_information(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_deleted', name=name))
        save_btn.clicked.connect(_do_save)
        load_btn.clicked.connect(_do_load)
        delete_btn.clicked.connect(_do_delete)
        close_btn.clicked.connect(dlg.accept)
        _hover_frame = None
        def _build_hover_frame(passive_list):
            nonlocal _hover_frame
            if _hover_frame is not None:
                try:
                    _hover_frame.close()
                    _hover_frame.deleteLater()
                except RuntimeError:
                    pass
            _hover_frame = QFrame(None)
            _hover_frame.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.ToolTip)
            _hover_frame.setAttribute(Qt.WA_ShowWithoutActivating)
            _hover_frame.setAttribute(Qt.WA_TranslucentBackground)
            _hover_frame.setStyleSheet('QFrame { background: rgba(10,14,20,0.98); border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; }')
            fl = QVBoxLayout(_hover_frame)
            fl.setContentsMargins(6, 4, 6, 6)
            fl.setSpacing(2)
            _ensure_passive_data()
            pg = QWidget()
            pg.setStyleSheet('background: transparent; border: none;')
            pgl = QGridLayout(pg)
            pgl.setContentsMargins(0, 0, 0, 0)
            pgl.setSpacing(2)
            pgl.setColumnStretch(0, 1)
            pgl.setColumnStretch(1, 1)
            for i in range(4):
                p_clean = ''
                display_name = '--'
                tc = 'rgba(255,255,255,0.3)'
                bg = 'rgba(255,255,255,0.03)'
                bd = 'rgba(255,255,255,0.06)'
                anim_mode = None
                icon_path = ''
                p_info = {}
                rank = 1
                if i < len(passive_list) and passive_list[i]:
                    p_val = passive_list[i]
                    if isinstance(p_val, dict):
                        p_val = p_val.get('value', '')
                    p_clean = str(p_val).lower() if p_val else ''
                    display_name = PalFrame._PASSMAP.get(p_clean, str(p_val))
                    bg, bd, tc = PalFrame._passive_rank_color(p_clean)
                    rank = PalFrame._PASSRANK.get(p_clean, 1)
                    if rank >= 5:
                        anim_mode = 'world_tree'
                    elif rank >= 4:
                        anim_mode = 'legend'
                    p_info = _data._PASSIVE_DATA.get(p_clean, {}) if isinstance(_data._PASSIVE_DATA, dict) else {}
                    icon_path = p_info.get('icon', '') if isinstance(p_info, dict) else ''
                card = QFrame()
                card.setObjectName('hCard')
                card.setFixedHeight(26)
                card.setStyleSheet(f'QFrame#hCard {{ background: {bg}; border: 1.5px solid {bd}; border-radius: 4px; padding: 3px 6px; }}')
                cl = QHBoxLayout(card)
                cl.setContentsMargins(6, 0, 6, 0)
                cl.setSpacing(2)
                cl.setAlignment(Qt.AlignVCenter)
                plbl = QLabel(display_name)
                plbl.setStyleSheet(f'font-size: 9px; font-weight: 700; color: {tc}; background: transparent; border: none;')
                cl.addWidget(plbl, 1)
                cl.addStretch()
                if icon_path:
                    full_path = resource_path(constants.get_base_path(), 'game_data', icon_path.lstrip('/'))
                    pix = _icons._get_cached_pixmap(full_path, 14)
                    if pix:
                        ilbl = QLabel()
                        ilbl.setFixedSize(14, 14)
                        ilbl.setPixmap(pix)
                        ilbl.setStyleSheet('background: transparent; border: none;')
                        cl.addWidget(ilbl)
                if anim_mode:
                    ov = PassiveEffectOverlay(card)
                    ov.setGeometry(0, 0, 200, 26)
                    ov.set_mode(anim_mode)
                if p_clean:
                    tip_parts = [f'<b style="color:{tc}">{display_name}</b>']
                    rank_labels = {1: 'Common', 2: 'Rare', 3: 'Rare', 4: 'Epic', 5: 'Epic', -99: 'Negative'}
                    tip_parts.append(f"<i>{rank_labels.get(rank, f'Rank {rank}')}</i>")
                    p_desc = p_info.get('description', '')
                    if p_desc:
                        p_desc = p_desc.replace('{CharacterName}', 'Pal')
                        for ei in range(1, 5):
                            ev = p_info.get(f'effect{ei}', 0)
                            ev_str = str(int(ev)) if isinstance(ev, float) and ev == int(ev) else f'{ev:.0f}' if isinstance(ev, float) else str(ev)
                            p_desc = p_desc.replace(f'{{EffectValue{ei}}}', ev_str)
                        tip_parts.append('')
                        tip_parts.append(p_desc)
                    card.setToolTip('<br>'.join(tip_parts))
                pgl.addWidget(card, i // 2, i % 2)
            fl.addWidget(pg)
            _hover_frame.adjustSize()
            if _hover_frame.width() < 340:
                _hover_frame.setFixedWidth(340)
        def _on_item_enter(item):
            nonlocal _hover_frame
            name = item.data(Qt.UserRole)
            passive_list = loadouts.get(name)
            if not passive_list:
                return
            _build_hover_frame(passive_list)
            if not _hover_frame:
                return
            item_rect = list_widget.visualItemRect(item)
            global_pos = list_widget.mapToGlobal(item_rect.topRight())
            screen = QApplication.primaryScreen().availableGeometry()
            fw = _hover_frame.width()
            x = min(global_pos.x() + 6, screen.right() - fw - 4)
            y = global_pos.y()
            _hover_frame.move(x, y)
            _hover_frame.show()
        def _on_item_leave():
            nonlocal _hover_frame
            if _hover_frame is not None:
                try:
                    _hover_frame.close()
                    _hover_frame.hide()
                except RuntimeError:
                    pass
        class _HoverFilter(QObject):
            def __init__(self, parent, callback):
                super().__init__(parent)
                self._cb = callback
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Leave:
                    self._cb()
                return super().eventFilter(obj, event)
        list_widget.viewport().installEventFilter(_HoverFilter(list_widget, _on_item_leave))
        list_widget.itemEntered.connect(_on_item_enter)
        list_widget.itemDoubleClicked.connect(_do_load)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(inner)
        dlg.exec()
        if _hover_frame is not None:
            try:
                _hover_frame.close()
                _hover_frame.deleteLater()
            except RuntimeError:
                pass

    def _learn_all_skills(self):
        if not self._raw:
            return
        _learn_all_skills_raw(self._raw)
        self._refresh()

    def _on_boss_toggle(self):
        if not self._raw:
            return
        cid = extract_value(self._raw, 'CharacterID', '')
        can_enable, can_disable = _data._pal_can_toggle_boss(cid)
        is_boss = cid.upper().startswith('BOSS_')
        if (is_boss and not can_disable) or (not is_boss and not can_enable):
            self.info_boss_btn.blockSignals(True)
            self.info_boss_btn.setChecked(is_boss)
            self.info_boss_btn.blockSignals(False)
            return
        _toggle_boss_raw(self._raw, self.info_boss_btn.isChecked())
        is_lucky = extract_value(self._raw, 'IsRarePal', False)
        self.info_lucky_btn.blockSignals(True)
        self.info_lucky_btn.setChecked(is_lucky)
        self.info_lucky_btn.blockSignals(False)
        self._recalc_hp()

    def _on_lucky_toggle(self):
        if not self._raw:
            return
        cid = extract_value(self._raw, 'CharacterID', '')
        can_enable, can_disable = _data._pal_can_toggle_boss(cid)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(self._raw, 'IsRarePal', False)
        if is_lucky:
            if is_boss and not can_disable:
                self.info_lucky_btn.blockSignals(True)
                self.info_lucky_btn.setChecked(True)
                self.info_lucky_btn.blockSignals(False)
                return
        else:
            if not is_boss and not can_enable:
                return
        _toggle_lucky_raw(self._raw, self.info_lucky_btn.isChecked())
        cid = extract_value(self._raw, 'CharacterID', '')
        is_boss = cid.upper().startswith('BOSS_')
        self.info_boss_btn.blockSignals(True)
        self.info_boss_btn.setChecked(is_boss)
        self.info_boss_btn.blockSignals(False)
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
        cid = extract_value(self._raw, 'CharacterID', '')
        base_data = _data.get_pal_base_data(cid)
        ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
        for k, v in ws_base.items():
            if v > 0:
                _set_work_suitability(self._raw, k, 10)
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
            try:
                parent = parent.parentWidget() if hasattr(parent, 'parentWidget') else parent.parent()
            except TypeError:
                break
            if parent is None:
                break
        try:
            self.pal_data_changed.emit()
        except:
            pass

    def refresh_labels(self):
        self._no_data_overlay.setText(t('pal_editor.no_pal_data') if t else 'No Pal Data')
        if hasattr(self, 'partner_desc_lbl'):
            self.partner_desc_lbl.setText(t('pal_editor.no_pal_data') if t else 'No Pal Data')
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
        if hasattr(self, '_c_icon'):
            self._c_icon.setToolTip(t('edit_pals.toggle_skills_hint'))
        if hasattr(self, '_as_c_icon'):
            self._as_c_icon.setToolTip(t('edit_pals.toggle_skills_hint'))
        if hasattr(self, '_l_icon'):
            self._l_icon.setToolTip(t('edit_pals.loadouts_hint'))
