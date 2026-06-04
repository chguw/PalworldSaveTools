import os
import re
from palsav import json_tools
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QGroupBox, QMessageBox, QAbstractItemView, QListView, QTabWidget, QCheckBox, QWidget, QStyledItemDelegate, QFrame
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QCursor
from i18n import t
from palworld_aio import constants
from palworld_aio.edit_pals import PalFrame, _get_boss_alpha_pixmap, _composite_badge, _BOSS_PREFIXES, _get_element_pixmap, _ensure_element_data, _resolve_partner_desc, _partner_desc_to_html, PalInfoWidget
from palworld_aio.ui.skill_picker import SkillPicker
from palworld_aio.ui.styles import DIALOG_STYLE as DARK_THEME_STYLE, PICKER_BG_STYLE, PICKER_SEARCH_STYLE, PICKER_LIST_STYLE
class PalSlotDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        has_badge = index.data(Qt.UserRole + 1)
        if has_badge:
            badge = _get_boss_alpha_pixmap(14)
            if badge and (not badge.isNull()):
                painter.drawPixmap(option.rect.x() + 6, option.rect.y() + 6, badge)
class PlayerPalActionDialog(QDialog):
    pal_action_selected = Signal(str, str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('player_pal.title') if t else 'Bulk Pal Management')
        self.setMinimumSize(900, 650)
        self.selected_pal_id = None
        self.selected_pal_name = None
        self.selected_active_skill_id = None
        self.selected_active_skill_name = None
        self.selected_passive_skill_id = None
        self.selected_passive_skill_name = None
        self._icon_pixmap_cache = {}
        self._setup_ui()
        self._load_data()
    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self.tab_widget = QTabWidget()
        self.delete_pal_tab = self._create_delete_pal_tab()
        self.tab_widget.addTab(self.delete_pal_tab, t('player_pal.delete_pal_tab') if t else 'Delete Pal')
        self.remove_skills_tab = self._create_remove_skills_tab()
        self.tab_widget.addTab(self.remove_skills_tab, t('player_pal.remove_skills_tab') if t else 'Remove Skills')
        layout.addWidget(self.tab_widget)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.status_label)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.reject)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    def _create_delete_pal_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        search_group = QGroupBox(t('player_pal.search_pal') if t else 'Search Pal')
        search_layout = QVBoxLayout()
        search_bar_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.pal_search_input = QLineEdit()
        self.pal_search_input.setPlaceholderText(t('player_pal.search_placeholder') if t else 'Type to search pals...')
        self.pal_search_input.textChanged.connect(self._search_pals)
        search_bar_layout.addWidget(search_label)
        search_bar_layout.addWidget(self.pal_search_input)
        search_bar_layout.addStretch()
        search_layout.addLayout(search_bar_layout)
        self.pal_list = QListWidget()
        self.pal_list.setViewMode(QListView.IconMode)
        self.pal_list.setIconSize(QSize(48, 48))
        self.pal_list.setSpacing(0)
        self.pal_list.setUniformItemSizes(True)
        self.pal_list.setGridSize(QSize(84, 84))
        self.pal_list.setResizeMode(QListWidget.Adjust)
        self.pal_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pal_list.setDragEnabled(False)
        self.pal_list.setAcceptDrops(False)
        self.pal_list.setItemDelegate(PalSlotDelegate(self.pal_list))
        self.pal_list.itemClicked.connect(self._on_pal_clicked)
        search_layout.addWidget(self.pal_list)
        self.pal_info_label = QLabel(t('player_pal.select_pal') if t else 'Select a pal to delete from everywhere')
        self.pal_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        search_layout.addWidget(self.pal_info_label)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        action_layout = QHBoxLayout()
        self.delete_pal_btn = QPushButton(t('player_pal.delete_pal') if t else 'Delete All Selected Pal')
        self.delete_pal_btn.clicked.connect(self._on_delete_pal)
        self.delete_pal_btn.setEnabled(False)
        action_layout.addWidget(self.delete_pal_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        return tab
    def _create_remove_skills_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        active_group = QGroupBox(t('player_pal.active_skills') if t else 'Active Skill')
        active_layout = QHBoxLayout()
        self.active_skill_btn = QPushButton(t('player_pal.select_active') if t else 'Select Active Skill')
        self.active_skill_btn.clicked.connect(self._on_active_skill_pick)
        active_layout.addWidget(self.active_skill_btn)
        self.active_skill_label = QLabel(t('player_pal.no_active_selected') if t else 'No active skill selected')
        self.active_skill_label.setStyleSheet('color: #888; padding: 5px;')
        self.active_skill_label.setWordWrap(True)
        active_layout.addWidget(self.active_skill_label, 1)
        active_layout.addStretch()
        self.active_clear_btn = QPushButton('X')
        self.active_clear_btn.setFixedSize(22, 22)
        self.active_clear_btn.setStyleSheet('QPushButton { background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid rgba(239,68,68,0.2); border-radius: 11px; font-size: 10px; font-weight: bold; } QPushButton:hover { background: rgba(239,68,68,0.25); }')
        self.active_clear_btn.clicked.connect(self._clear_active_skill)
        self.active_clear_btn.setVisible(False)
        active_layout.addWidget(self.active_clear_btn)
        active_group.setLayout(active_layout)
        layout.addWidget(active_group)
        passive_group = QGroupBox(t('player_pal.passive_skills') if t else 'Passive Skill')
        passive_layout = QHBoxLayout()
        self.passive_skill_btn = QPushButton(t('player_pal.select_passive') if t else 'Select Passive Skill')
        self.passive_skill_btn.clicked.connect(self._on_passive_skill_pick)
        passive_layout.addWidget(self.passive_skill_btn)
        self.passive_skill_label = QLabel(t('player_pal.no_passive_selected') if t else 'No passive skill selected')
        self.passive_skill_label.setStyleSheet('color: #888; padding: 5px;')
        self.passive_skill_label.setWordWrap(True)
        passive_layout.addWidget(self.passive_skill_label, 1)
        passive_layout.addStretch()
        self.passive_clear_btn = QPushButton('X')
        self.passive_clear_btn.setFixedSize(22, 22)
        self.passive_clear_btn.setStyleSheet('QPushButton { background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid rgba(239,68,68,0.2); border-radius: 11px; font-size: 10px; font-weight: bold; } QPushButton:hover { background: rgba(239,68,68,0.25); }')
        self.passive_clear_btn.clicked.connect(self._clear_passive_skill)
        self.passive_clear_btn.setVisible(False)
        passive_layout.addWidget(self.passive_clear_btn)
        passive_group.setLayout(passive_layout)
        layout.addWidget(passive_group)
        scope_group = QGroupBox(t('player_pal.scope') if t else 'Apply To')
        scope_layout = QVBoxLayout()
        self.skills_player_pals_checkbox = QCheckBox(t('player_pal.player_pals') if t else 'Player Pals (Party + Palbox)')
        self.skills_player_pals_checkbox.setChecked(True)
        self.skills_player_pals_checkbox.setEnabled(False)
        scope_layout.addWidget(self.skills_player_pals_checkbox)
        self.skills_base_pals_checkbox = QCheckBox(t('player_pal.base_pals') if t else 'Base Pals (All bases)')
        self.skills_base_pals_checkbox.setChecked(True)
        self.skills_base_pals_checkbox.setEnabled(False)
        scope_layout.addWidget(self.skills_base_pals_checkbox)
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)
        self.skills_info_label = QLabel(t('player_pal.select_skill_info') if t else 'Select active and/or passive skills to remove from ALL pals everywhere.')
        self.skills_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        self.skills_info_label.setWordWrap(True)
        layout.addWidget(self.skills_info_label)
        action_layout = QHBoxLayout()
        self.remove_skills_btn = QPushButton(t('player_pal.remove_skills') if t else 'Remove Selected Skills from All Pals')
        self.remove_skills_btn.clicked.connect(self._on_remove_skills)
        self.remove_skills_btn.setEnabled(False)
        action_layout.addWidget(self.remove_skills_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        return tab
    def _load_data(self):
        PalFrame._load_maps()
        self._build_pal_icon_map()
        self._display_pals()
    def _build_pal_icon_map(self):
        self._pal_icon_map = {}
        self._pal_desc_map = {}
        self._pal_passives_map = {}
        self._pal_main_value_map = {}
        self._pal_overwrite_effect_map = {}
        base_dir = constants.get_base_path()
        try:
            paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'characters.json')
            paldata = json_tools.load(paldata_path)
            for pal in paldata.get('pals', []):
                asset = pal.get('asset', '').lower()
                icon_rel = pal.get('icon', '')
                if icon_rel:
                    icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel.lstrip('/'))
                    if os.path.exists(icon_path):
                        self._pal_icon_map[asset] = icon_path
                desc = pal.get('description', '')
                if desc:
                    self._pal_desc_map[asset] = desc
                passives = pal.get('passives', [])
                if passives:
                    self._pal_passives_map[asset] = passives
                mv = pal.get('active_skill_main_value', [])
                if mv:
                    self._pal_main_value_map[asset] = mv
                ov = pal.get('active_skill_overwrite_effect', [])
                if ov:
                    self._pal_overwrite_effect_map[asset] = ov
        except:
            pass
    def _get_pal_icon(self, pal_id):
        asset = pal_id.lower()
        icon_path = self._pal_icon_map.get(asset)
        if not icon_path:
            base_dir = constants.get_base_path()
            icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'T_icon_unknown.webp')
        if icon_path in self._icon_pixmap_cache:
            return self._icon_pixmap_cache[icon_path]
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._icon_pixmap_cache[icon_path] = pixmap
            return pixmap
        return None
    def _display_pals(self):
        self._search_pals('')
    def _search_pals(self, query=None):
        if query is None:
            query = self.pal_search_input.text()
        query_lower = query.lower()
        self.pal_list.clear()
        for asset, name in sorted(PalFrame._NAMEMAP.items(), key=lambda x: x[1]):
            asset_lower = asset.lower()
            if any((asset_lower.startswith(p) for p in ('summon_', 'quest_', 'raid_', 'predator_', 'police_'))):
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
            elif zukan < 0:
                continue
            if query_lower and query_lower not in name.lower() and (query_lower not in asset.lower()):
                continue
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, asset)
            tip = f'<b>{name}</b><br>({asset})'
            pdesc = self._pal_desc_map.get(asset.lower(), '')
            passives = self._pal_passives_map.get(asset.lower(), [])
            if pdesc:
                resolved = _resolve_partner_desc(pdesc, passives, 0, self._pal_main_value_map.get(asset.lower()), self._pal_overwrite_effect_map.get(asset.lower()))
                elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
                html_desc = _partner_desc_to_html(resolved, elem_colors, tooltip=True)
                tip += f'<br><br>{html_desc}'
            list_item.setToolTip(tip)
            pixmap = self._get_pal_icon(asset)
            if pixmap and (not pixmap.isNull()):
                list_item.setIcon(QIcon(pixmap))
            if any((asset.upper().startswith(p) for p in _BOSS_PREFIXES)):
                list_item.setData(Qt.UserRole + 1, True)
            list_item.setSizeHint(QSize(84, 84))
            self.pal_list.addItem(list_item)
    def _on_pal_clicked(self, item):
        self.selected_pal_id = item.data(Qt.UserRole)
        self.selected_pal_name = item.text()
        self.pal_info_label.setText(f'{self.selected_pal_name}: {self.selected_pal_id}')
        self.pal_info_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        self.delete_pal_btn.setEnabled(True)
    def _on_active_skill_pick(self):
        picker = SkillPicker(self)
        pos = self.active_skill_btn.mapToGlobal(self.active_skill_btn.rect().bottomLeft())
        result = picker.pick(PalFrame._SKILLMAP, True, pos=pos, use_exclusions=True)
        if result is None:
            return
        if result == '':
            self._clear_active_skill()
            return
        self.selected_active_skill_id = result
        self.selected_active_skill_name = PalFrame._SKILLMAP.get(result, result)
        self.active_skill_label.setText(f'Active: {self.selected_active_skill_name}')
        self.active_skill_label.setStyleSheet('color: #7DD3FC; font-weight: bold; padding: 5px;')
        self.active_clear_btn.setVisible(True)
        self._update_remove_button()
    def _on_passive_skill_pick(self):
        picker = SkillPicker(self)
        pos = self.passive_skill_btn.mapToGlobal(self.passive_skill_btn.rect().bottomLeft())
        result = picker.pick(PalFrame._PASSMAP, False, pos=pos, use_exclusions=True)
        if result is None:
            return
        if result == '':
            self._clear_passive_skill()
            return
        self.selected_passive_skill_id = result
        self.selected_passive_skill_name = PalFrame._PASSMAP.get(result, result)
        asset_lower = (self.selected_passive_skill_id or '').lower()
        rank = PalFrame._PASSRANK.get(asset_lower, 1)
        tc = PalFrame._passive_rank_color(asset_lower)[2]
        self.passive_skill_label.setText(f'Passive: {self.selected_passive_skill_name}')
        self.passive_skill_label.setStyleSheet(f'color: {tc}; font-weight: bold; padding: 5px;')
        self.passive_clear_btn.setVisible(True)
        self._update_remove_button()
    def _clear_active_skill(self):
        self.selected_active_skill_id = None
        self.selected_active_skill_name = None
        self.active_skill_label.setText(t('player_pal.no_active_selected') if t else 'No active skill selected')
        self.active_skill_label.setStyleSheet('color: #888; padding: 5px;')
        self.active_clear_btn.setVisible(False)
        self._update_remove_button()
    def _clear_passive_skill(self):
        self.selected_passive_skill_id = None
        self.selected_passive_skill_name = None
        self.passive_skill_label.setText(t('player_pal.no_passive_selected') if t else 'No passive skill selected')
        self.passive_skill_label.setStyleSheet('color: #888; padding: 5px;')
        self.passive_clear_btn.setVisible(False)
        self._update_remove_button()
    def _update_remove_button(self):
        has_active = self.selected_active_skill_id is not None
        has_passive = self.selected_passive_skill_id is not None
        self.remove_skills_btn.setEnabled(has_active or has_passive)
        if has_active and has_passive:
            self.remove_skills_btn.setText(t('player_pal.remove_both_skills') if t else 'Remove Both Skills from All Pals')
        elif has_active:
            self.remove_skills_btn.setText(t('player_pal.remove_active_skill') if t else 'Remove Active Skill from All Pals')
        elif has_passive:
            self.remove_skills_btn.setText(t('player_pal.remove_passive_skill') if t else 'Remove Passive Skill from All Pals')
    def _on_delete_pal(self):
        if not self.selected_pal_id:
            return
        reply = QMessageBox.question(self, t('player_pal.confirm_delete_all') if t else 'Confirm Delete All', t('player_pal.confirm_delete_all_msg').format(pal_name=self.selected_pal_name) if t else f'Delete ALL "{self.selected_pal_name}" pals from everywhere (players + bases)? This cannot be undone!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            action = f'delete_pal:{self.selected_pal_id}'
            self.pal_action_selected.emit('all', action, [])
            self._refresh_after_action()
    def _on_remove_skills(self):
        if not self.selected_active_skill_id and (not self.selected_passive_skill_id):
            QMessageBox.warning(self, t('player_pal.no_skill_selected') if t else 'No Skill Selected', t('player_pal.select_skill_first') if t else 'Please select at least one skill.')
            return
        skill_names = []
        if self.selected_active_skill_name:
            skill_names.append(f'Active: {self.selected_active_skill_name}')
        if self.selected_passive_skill_name:
            skill_names.append(f'Passive: {self.selected_passive_skill_name}')
        msg = t('player_pal.confirm_remove_all_msg').format(skills='\n- '.join(skill_names)) if t else f"Remove the following skills from ALL pals (players + bases)?\n- {'\n- '.join(skill_names)}\n\nThis will also remove them from learned skills lists. This cannot be undone!"
        reply = QMessageBox.question(self, t('player_pal.confirm_remove_all') if t else 'Confirm Remove Skills', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            action = f"remove_all:{self.selected_active_skill_id or ''}:{self.selected_passive_skill_id or ''}"
            self.pal_action_selected.emit('all', action, [])
            self._refresh_after_action()
    def _refresh_after_action(self):
        self.status_label.setText(t('player_pal.action_complete').format(item_name='Operation') if t else 'Operation completed successfully!')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        QTimer.singleShot(3000, lambda: self.status_label.setText(''))
    def refresh_labels(self):
        self.setWindowTitle(t('player_pal.title') if t else 'Bulk Pal Management')
        self.tab_widget.setTabText(0, t('player_pal.delete_pal_tab') if t else 'Delete Pal')
        self.tab_widget.setTabText(1, t('player_pal.remove_skills_tab') if t else 'Remove Skills')
        for group in self.findChildren(QGroupBox):
            title = group.title()
            if 'search' in title.lower() or 'pal' in title.lower():
                if 'search' in title.lower():
                    group.setTitle(t('player_pal.search_pal') if t else 'Search Pal')
            elif 'active' in title.lower():
                group.setTitle(t('player_pal.active_skills') if t else 'Active Skill')
            elif 'passive' in title.lower():
                group.setTitle(t('player_pal.passive_skills') if t else 'Passive Skill')
            elif 'scope' in title.lower() or 'apply' in title.lower():
                group.setTitle(t('player_pal.scope') if t else 'Apply To')
        self.pal_search_input.setPlaceholderText(t('player_pal.search_placeholder') if t else 'Type to search pals...')
        self.active_skill_btn.setText(t('player_pal.select_active') if t else 'Select Active Skill')
        self.passive_skill_btn.setText(t('player_pal.select_passive') if t else 'Select Passive Skill')
        if not self.selected_active_skill_name:
            self.active_skill_label.setText(t('player_pal.no_active_selected') if t else 'No active skill selected')
        if not self.selected_passive_skill_name:
            self.passive_skill_label.setText(t('player_pal.no_passive_selected') if t else 'No passive skill selected')
        if self.selected_pal_id:
            self.pal_info_label.setText(f'{self.selected_pal_name}: {self.selected_pal_id}')
        else:
            self.pal_info_label.setText(t('player_pal.select_pal') if t else 'Select a pal to delete from everywhere')
        self.skills_info_label.setText(t('player_pal.select_skill_info') if t else 'Select active and/or passive skills to remove from ALL pals everywhere.')
        self.skills_player_pals_checkbox.setText(t('player_pal.player_pals') if t else 'Player Pals (Party + Palbox)')
        self.skills_base_pals_checkbox.setText(t('player_pal.base_pals') if t else 'Base Pals (All bases)')
        self.delete_pal_btn.setText(t('player_pal.delete_pal') if t else 'Delete All Selected Pal')
        self._update_remove_button()