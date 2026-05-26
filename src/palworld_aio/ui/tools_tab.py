import os
import sys
from palworld_save_tools import json_tools
import traceback
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem, QGridLayout, QApplication, QDialog, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor, QDragEnterEvent, QDropEvent, QDragLeaveEvent, QPainter, QColor, QPen, QPainterPath
from i18n import t
from loading_manager import show_critical
from palworld_aio import constants
from palworld_aio.ui.styles import ThemeManager
def load_tool_icons():
    icon_file = os.path.join(constants.get_src_path(), 'data', 'configs', 'toolicon.json')
    if not os.path.exists(icon_file):
        return {}
    try:
        data = json_tools.load(icon_file)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
CONVERTING_TOOL_KEYS = ['tool.convert.saves', 'tool.convert.gamepass.steam', 'tool.convert.steamid', 'tool.restore_map']
MANAGEMENT_TOOL_KEYS = ['tool.slot_injector', 'tool.modify_save', 'tool.character_transfer', 'tool.fix_host_save']
TOOL_DESCRIPTIONS = {'tool.convert.saves': 'tool.convert.saves.desc', 'tool.convert.gamepass.steam': 'tool.convert.gamepass.steam.desc', 'tool.convert.steamid': 'tool.convert.steamid.desc', 'tool.restore_map': 'tool.restore_map.desc', 'tool.slot_injector': 'tool.slot_injector.desc', 'tool.modify_save': 'tool.modify_save.desc', 'tool.character_transfer': 'tool.character_transfer.desc', 'tool.fix_host_save': 'tool.fix_host_save.desc'}
def center_window(win):
    win_center = win.frameGeometry().center()
    screen = QApplication.screenAt(win_center)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen_geometry.center())
    win.move(geo.topLeft())
def center_on_parent(dialog):
    parent = dialog.parent()
    dialog.adjustSize()
    size = dialog.size()
    if not size.isValid() or size.width() < 100 or size.height() < 50:
        min_size = dialog.minimumSize()
        if min_size.isValid() and min_size.width() > 0 and (min_size.height() > 0):
            size = min_size
        else:
            size = QSize(400, 300)
    if parent and hasattr(parent, 'geometry'):
        parent_rect = parent.geometry()
        parent_center = parent_rect.center()
        screen = QApplication.screenAt(parent_center)
        if screen is None:
            screen = QApplication.primaryScreen()
        dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
        dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
        screen_geometry = screen.availableGeometry()
        dialog_x = max(screen_geometry.x(), min(dialog_x, screen_geometry.right() - size.width()))
        dialog_y = max(screen_geometry.y(), min(dialog_y, screen_geometry.bottom() - size.height()))
        dialog.move(dialog_x, dialog_y)
    else:
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        dialog_x = screen_geometry.x() + (screen_geometry.width() - size.width()) // 2
        dialog_y = screen_geometry.y() + (screen_geometry.height() - size.height()) // 2
        dialog.move(dialog_x, dialog_y)
class ConversionOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_option = None
        self.setWindowTitle(t('tool.convert.saves') if t else 'Convert Save Files')
        self.setModal(True)
        self.setFixedWidth(380)
        self._setup_ui()
        self._load_theme()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass = QFrame()
        glass.setObjectName('glass')
        glass_layout = QVBoxLayout(glass)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        title_label = QLabel(t('tool.convert.saves') if t else 'Convert Save Files')
        title_label.setFont(QFont('Segoe UI', 13, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(title_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName('dialogSeparator')
        glass_layout.addWidget(separator)
        glass_layout.addSpacing(4)
        options = [('tool.convert.any.to_json', 0), ('tool.convert.any.to_sav', 1)]
        for key, index in options:
            btn = QPushButton(t(key) if t else key)
            btn.setObjectName('dialogOption')
            btn.setFixedHeight(36)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, idx=index: self._on_option_selected(idx))
            glass_layout.addWidget(btn)
        glass_layout.addStretch(1)
        cancel_btn = QPushButton(t('Cancel') if t else 'Cancel')
        cancel_btn.setObjectName('dialogCancel')
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        glass_layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(glass)
    def _on_option_selected(self, index):
        self.selected_option = index
        self.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    def _load_theme(self):
        ThemeManager.apply_to_widget(self)
class ToolCard(QFrame):
    clicked = Signal()
    def __init__(self, label_text, tooltip_text, description_text=None, icon_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName('toolCard')
        self.setProperty('class', 'toolCard')
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setObjectName('toolCardIcon')
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if pix.width() > 40 or pix.height() > 40:
                pix = pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pix)
        else:
            default_icon = os.path.join(constants.get_base_path(), 'resources', 'pal.ico')
            if os.path.exists(default_icon):
                pix = QPixmap(default_icon)
                if pix.width() > 40 or pix.height() > 40:
                    pix = pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(pix)
        layout.addWidget(self.icon_label)
        text_column = QVBoxLayout()
        text_column.setSpacing(4)
        text_column.addStretch()
        self.title_label = QLabel(label_text)
        self.title_label.setToolTip(tooltip_text)
        self.title_label.setFont(QFont(constants.FONT_FAMILY, 11, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.title_label.setObjectName('toolCardTitle')
        text_column.addWidget(self.title_label)
        if description_text:
            self.desc_label = QLabel(description_text)
            self.desc_label.setFont(QFont(constants.FONT_FAMILY, 9))
            self.desc_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.desc_label.setObjectName('toolCardDesc')
            self.desc_label.setWordWrap(True)
            text_column.addWidget(self.desc_label)
        else:
            self.desc_label = None
        text_column.addStretch()
        layout.addLayout(text_column, 1)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
class DropOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(False)
        self._drop_text = t('tools.drop_title') if t else 'Drop Level.sav to Load Save'
        self._drop_hint = t('tools.drop_hint_overlay') if t else "Or click the 'Load Save' button above"
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(5, 8, 12, 220))
        inner = self.rect().adjusted(30, 30, -30, -30)
        path = QPainterPath()
        path.addRoundedRect(QRectF(inner), 20, 20)
        painter.fillPath(path, QColor(34, 197, 94, 25))
        pen = QPen(QColor(34, 197, 94, 255))
        pen.setWidth(4)
        pen.setDashPattern([12, 6])
        painter.setPen(pen)
        painter.drawPath(path)
        box_h = inner.height()
        center_y = inner.y() + box_h / 2
        icon_font = QFont('Segoe UI', 52, QFont.Bold)
        painter.setFont(icon_font)
        painter.setPen(QColor(34, 197, 94, 255))
        icon_rect = QRectF(inner.x(), center_y - 80, inner.width(), 60)
        painter.drawText(icon_rect, Qt.AlignHCenter | Qt.AlignBottom, '📁')
        font = QFont('Segoe UI', 22, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 255))
        text_rect = QRectF(inner.x(), center_y - 10, inner.width(), 40)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignCenter, self._drop_text)
        font_small = QFont('Segoe UI', 13)
        painter.setFont(font_small)
        painter.setPen(QColor(166, 184, 200, 255))
        hint_rect = QRectF(inner.x(), center_y + 40, inner.width(), 30)
        painter.drawText(hint_rect, Qt.AlignHCenter | Qt.AlignTop, self._drop_hint)
class ToolsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.tool_icons = load_tool_icons()
        self.tool_buttons = []
        self._section_titles = []
        self._drag_hover_active = False
        self.setAcceptDrops(True)
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        upper_row = QHBoxLayout()
        upper_row.setSpacing(14)
        upper_row.addWidget(self._create_save_card(), alignment=Qt.AlignTop)
        upper_row.addWidget(self._create_overview_panel(), stretch=1)
        main_layout.addLayout(upper_row, stretch=1)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(14)
        footer_row.addWidget(self._create_section('tools.section.converting', CONVERTING_TOOL_KEYS, self._run_converting_tool), stretch=1)
        footer_row.addWidget(self._create_section('tools.section.management', MANAGEMENT_TOOL_KEYS, self._run_management_tool), stretch=1)
        main_layout.addLayout(footer_row)

        self._drop_overlay = DropOverlay(self)
        self._drop_overlay.setVisible(False)
        self._drop_overlay.lower()
        self._setup_save_manager_connection()

    def _create_header_bar(self):
        return QWidget()

    def _create_save_card(self):
        card = QFrame()
        card.setObjectName('saveCard')
        card.setFixedWidth(340)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        icon_label = QLabel('📁')
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 36px; border: none; background: transparent;')
        card_layout.addWidget(icon_label)

        self._save_status_label = QLabel(t('dashboard.no_save') if t else 'No Save Loaded')
        self._save_status_label.setAlignment(Qt.AlignCenter)
        self._save_status_label.setWordWrap(True)
        self._save_status_label.setStyleSheet('font-size: 15px; font-weight: 700; color: #e2e8f0; border: none; background: transparent;')
        card_layout.addWidget(self._save_status_label)

        self._save_path_label = QPushButton(t('tools.no_save_loaded') if t else 'No save loaded')
        self._save_path_label.setObjectName('savePathLabel')
        self._save_path_label.setFlat(True)
        self._save_path_label.setCursor(QCursor(Qt.PointingHandCursor))
        self._save_path_label.setStyleSheet('font-size: 11px; color: rgba(148,163,184,0.6); border: none; background: transparent; text-align: center;')
        self._save_path_label.clicked.connect(lambda: self._on_save_path_label_clicked())
        card_layout.addWidget(self._save_path_label)

        self._load_btn = QPushButton(t('menu.file.load_save') if t else 'Load Save')
        self._load_btn.setObjectName('loadSaveBtn')
        self._load_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._load_btn.setMinimumHeight(42)
        self._load_btn.clicked.connect(self._on_load_save_clicked)
        self._load_btn.setStyleSheet('QPushButton { font-size: 14px; font-weight: 700; }')
        card_layout.addWidget(self._load_btn)

        self._drag_hint_label = QLabel(t('tools.drag_hint') if t else 'or drag & drop a Level.sav file here')
        self._drag_hint_label.setAlignment(Qt.AlignCenter)
        self._drag_hint_label.setWordWrap(True)
        self._drag_hint_label.setStyleSheet('font-size: 11px; color: rgba(148,163,184,0.4); border: none; background: transparent;')
        card_layout.addWidget(self._drag_hint_label)

        card_layout.addStretch()
        return card

    def _create_overview_panel(self):
        self._overview_panel = QFrame()
        self._overview_panel.setObjectName('overviewPanel')
        self._overview_stack = QStackedWidget(self._overview_panel)
        overview_layout = QVBoxLayout(self._overview_panel)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.addWidget(self._overview_stack)

        welcome = self._create_welcome_panel()
        self._overview_stack.addWidget(welcome)

        self._stats_panel = self._create_stats_panel()
        self._overview_stack.addWidget(self._stats_panel)

        self._overview_stack.setCurrentIndex(0)
        return self._overview_panel

    def _create_welcome_panel(self):
        panel = QFrame()
        panel.setObjectName('welcomePanel')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        layout.addStretch(1)

        logo = QLabel()
        p = os.path.join(constants.get_src_path(), '..', 'resources', 'Xenolord.webp')
        if os.path.exists(p):
            pix = QPixmap(p)
            logo.setPixmap(pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet('border: none; background: transparent;')
        layout.addWidget(logo)

        self._welcome_title = QLabel(t('dashboard.welcome_title') if t else 'Palworld Save Tools')
        self._welcome_title.setAlignment(Qt.AlignCenter)
        self._welcome_title.setStyleSheet('font-size: 22px; font-weight: 700; color: #e2e8f0; border: none; background: transparent;')
        layout.addWidget(self._welcome_title)

        self._welcome_tips = QLabel(t('dashboard.welcome_tips') if t else
            '📁 Click <b>Load Save</b> to open your Level.sav\n'
            '🖱️ Or drag & drop a save file onto this window\n'
            '🔧 Then use the tools below to manage your world'
        )
        self._welcome_tips.setAlignment(Qt.AlignCenter)
        self._welcome_tips.setWordWrap(True)
        self._welcome_tips.setStyleSheet('font-size: 13px; color: rgba(148,163,184,0.8); border: none; background: transparent; line-height: 1.6;')
        layout.addWidget(self._welcome_tips)

        layout.addStretch(1)
        return panel

    def _create_stats_panel(self):
        panel = QFrame()
        panel.setObjectName('statsPanel')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._overview_header = QLabel(t('dashboard.overview') if t else 'World Overview')
        self._overview_header.setAlignment(Qt.AlignCenter)
        self._overview_header.setStyleSheet('font-size: 16px; font-weight: 700; color: #7DD3FC; border: none; background: transparent;')
        layout.addWidget(self._overview_header)

        grid = QGridLayout()
        grid.setSpacing(12)

        self._stat_cards = {}
        self._stat_label_refs = {}
        stats = [
            ('players', '👥', 'dashboard.stat_players', '0'),
            ('guilds', '🛡️', 'dashboard.stat_guilds', '0'),
            ('bases', '🏠', 'dashboard.stat_bases', '0'),
            ('pals', '🐉', 'dashboard.stat_pals', '0'),
        ]
        for idx, (key, icon, label_key, default) in enumerate(stats):
            card = self._create_stat_card(icon, t(label_key) if t else label_key, default)
            grid.addWidget(card, idx // 2, idx % 2)
            self._stat_cards[key] = card
            self._stat_label_refs[key] = label_key

        layout.addLayout(grid)
        layout.addStretch()
        return panel

    def _create_stat_card(self, icon, label, value):
        card = QFrame()
        card.setObjectName('statCard')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(4)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 28px; border: none; background: transparent;')
        card_layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName('statValue')
        value_label.setStyleSheet('font-size: 22px; font-weight: 700; color: #e2e8f0; border: none; background: transparent;')
        card._value_label = value_label
        card_layout.addWidget(value_label)

        name_label = QLabel(label)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet('font-size: 11px; color: rgba(148,163,184,0.6); border: none; background: transparent;')
        card_layout.addWidget(name_label)

        return card

    def _update_stats(self):
        if not hasattr(constants, 'loaded_level_json') or not constants.loaded_level_json:
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        group_data = wsd.get('GroupSaveDataMap', {}).get('value', [])
        base_data = wsd.get('BaseCampSaveData', {}).get('value', [])
        char_data = wsd.get('CharacterSaveParameterMap', {}).get('value', [])

        total_players = sum(len(g['value']['RawData']['value'].get('players', [])) for g in group_data
                            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild')
        total_guilds = sum(1 for g in group_data
                           if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild')
        total_bases = len(base_data)
        total_pals = sum(1 for c in char_data
                         if c.get('value', {}).get('RawData', {}).get('value', {}).get('object', {})
                         .get('SaveParameter', {}).get('struct_type') == 'PalIndividualCharacterSaveParameter'
                         and not c.get('value', {}).get('RawData', {}).get('value', {}).get('object', {})
                         .get('SaveParameter', {}).get('value', {}).get('IsPlayer', {}).get('value'))

        try:
            self._stat_cards['players']._value_label.setText(str(total_players))
            self._stat_cards['guilds']._value_label.setText(str(total_guilds))
            self._stat_cards['bases']._value_label.setText(str(total_bases))
            self._stat_cards['pals']._value_label.setText(str(total_pals))
        except Exception:
            pass

    def _on_save_path_label_clicked(self):
        if constants.current_save_path:
            import subprocess
            subprocess.Popen(['explorer', '/select,', os.path.join(constants.current_save_path, 'Level.sav')])

    def _setup_save_manager_connection(self):
        from palworld_aio.save_manager import save_manager
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                save_manager.load_finished.disconnect(self._on_save_load_finished)
            except (TypeError, RuntimeError):
                pass
        save_manager.load_finished.connect(self._on_save_load_finished)
    def _on_load_save_clicked(self):
        if hasattr(self, 'parent_window') and self.parent_window:
            self.parent_window._load_save()
    def _on_save_load_finished(self, success):
        if success:
            if hasattr(self, '_save_path_label') and hasattr(constants, 'current_save_path') and constants.current_save_path:
                self._save_path_label.setText(constants.current_save_path)
                self._save_status_label.setText(t('tools.save_loaded') if t else 'Save Loaded')
                self._save_status_label.setStyleSheet('font-size: 15px; font-weight: 700; color: #22c55e; border: none; background: transparent;')
            self._update_stats()
            if hasattr(self, '_overview_stack'):
                self._overview_stack.setCurrentIndex(1)
    def _create_section(self, section_key, tool_keys, run_handler):
        section_frame = QFrame()
        section_frame.setObjectName('glass')
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(14, 10, 14, 10)
        section_layout.setSpacing(8)
        title = QLabel(t(section_key) if t else section_key)
        title.setObjectName('sectionHeader')
        title.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self._section_titles.append((title, section_key))
        section_layout.addWidget(title, alignment=Qt.AlignLeft)
        grid = QGridLayout()
        grid.setSpacing(8)
        for idx, key in enumerate(tool_keys):
            icon_path = self._get_tool_icon_path(key)
            desc_key = TOOL_DESCRIPTIONS.get(key)
            desc_text = t(desc_key) if desc_key and t else None
            card = ToolCard(t(key) if t else key, t(key) if t else key, desc_text, icon_path)
            card.clicked.connect(lambda i=idx, h=run_handler: h(i))
            row = idx // 2
            col = idx % 2
            grid.addWidget(card, row, col)
            self.tool_buttons.append((card, key))
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        section_layout.addLayout(grid, stretch=1)
        return section_frame
    def _get_tool_icon_path(self, tool_key):
        if tool_key in self.tool_icons:
            icon_name = self.tool_icons[tool_key]
            icon_dir = os.path.join(constants.get_src_path(), 'data', 'icon')
            for ext in ['.ico', '.png']:
                icon_path = os.path.join(icon_dir, f'{icon_name}{ext}')
                if os.path.exists(icon_path):
                    return icon_path
        return None
    def _import_and_call(self, module_name, function_name, *args):
        try:
            src_path = constants.get_src_path()
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            import importlib
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            return func(*args) if args else func()
        except Exception as e:
            print(f'Error importing/calling {module_name}.{function_name}: {e}')
            traceback.print_exc()
            show_critical(self, t('Error') if t else 'Error', f'Failed to run tool: {e}')
            raise
    def _run_converting_tool(self, index):
        try:
            dialog = None
            if index == 0:
                options_dialog = ConversionOptionsDialog(self)
                self._animate_dialog_slide_in(options_dialog)
                result = options_dialog.exec()
                if result == QDialog.Accepted and options_dialog.selected_option is not None:
                    if options_dialog.selected_option == 0:
                        self._import_and_call('palworld_toolsets.convert_generic', 'convert_generic', 'json')
                    elif options_dialog.selected_option == 1:
                        self._import_and_call('palworld_toolsets.convert_generic', 'convert_generic', 'sav')
            elif index == 1:
                dialog = self._import_and_call('palworld_toolsets.game_pass_save_fix', 'game_pass_save_fix')
            elif index == 2:
                dialog = self._import_and_call('palworld_toolsets.convertids', 'convert_steam_id')
            elif index == 3:
                dialog = self._import_and_call('palworld_toolsets.restore_map', 'restore_map')
            if dialog is not None:
                self._animate_dialog_slide_in(dialog)
                if not hasattr(self, '_active_dialogs'):
                    self._active_dialogs = []
                self._active_dialogs.append(dialog)
        except Exception as e:
            print(f'Error running converting tool {index}: {e}')
    def _run_management_tool(self, index):
        try:
            dialog = None
            if index == 0:
                dialog = self._import_and_call('palworld_toolsets.slot_injector', 'slot_injector')
            elif index == 1:
                dialog = self._import_and_call('palworld_toolsets.modify_save', 'modify_save')
            elif index == 2:
                dialog = self._import_and_call('palworld_toolsets.character_transfer', 'character_transfer')
            elif index == 3:
                dialog = self._import_and_call('palworld_toolsets.fix_host_save', 'fix_host_save')
            if dialog is not None:
                self._animate_dialog_slide_in(dialog)
                if not hasattr(self, '_active_dialogs'):
                    self._active_dialogs = []
                self._active_dialogs.append(dialog)
        except Exception as e:
            print(f'Error running management tool {index}: {e}')
    def _animate_dialog_slide_in(self, dialog):
        if dialog is None:
            return
        dialog.setWindowFlags(dialog.windowFlags() | Qt.Dialog)
        parent_window = self.window()
        if parent_window:
            dialog.setParent(parent_window)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.Window)
        dialog.adjustSize()
        center_window(dialog)
        dialog.setWindowOpacity(0.0)
        dialog.show()
        self.fade_animation = QPropertyAnimation(dialog, b'windowOpacity')
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    self._drag_hover_active = True
                    self._drop_overlay.setVisible(True)
                    self._drop_overlay.raise_()
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    event.acceptProposedAction()
                    return
        super().dragMoveEvent(event)
    def dragLeaveEvent(self, event):
        self._drag_hover_active = False
        self._drop_overlay.setVisible(False)
        super().dragLeaveEvent(event)
    def dropEvent(self, event):
        self._drag_hover_active = False
        self._drop_overlay.setVisible(False)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    self._load_save_from_path(file_path)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)
    def _load_save_from_path(self, path):
        from palworld_aio.save_manager import save_manager
        save_manager.load_save(path=path, parent=self)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_drop_overlay'):
            self._drop_overlay.setGeometry(self.rect())
    def refresh_labels(self):
        if hasattr(self, '_load_btn') and self._load_btn:
            self._load_btn.setText(t('menu.file.load_save') if t else 'Load Save')
        if hasattr(self, '_save_path_label') and self._save_path_label:
            if not (hasattr(constants, 'current_save_path') and constants.current_save_path):
                self._save_path_label.setText(t('tools.no_save_loaded') if t else 'No save loaded')
                self._save_status_label.setText(t('dashboard.no_save') if t else 'No Save Loaded')
                self._save_status_label.setStyleSheet('font-size: 15px; font-weight: 700; color: #e2e8f0; border: none; background: transparent;')
            else:
                self._save_status_label.setText(t('tools.save_loaded') if t else 'Save Loaded')
                self._save_status_label.setStyleSheet('font-size: 15px; font-weight: 700; color: #22c55e; border: none; background: transparent;')
        if hasattr(self, '_drag_hint_label') and self._drag_hint_label:
            self._drag_hint_label.setText(t('tools.drag_hint') if t else 'or drag & drop a Level.sav file here')
        for title_label, section_key in self._section_titles:
            title_label.setText(t(section_key) if t else section_key)
        for card, key in self.tool_buttons:
            label = t(key) if t else key
            card.title_label.setText(label)
            card.title_label.setToolTip(label)
            desc_key = TOOL_DESCRIPTIONS.get(key)
            if desc_key and hasattr(card, 'desc_label') and card.desc_label:
                card.desc_label.setText(t(desc_key) if t else '')
        if hasattr(self, '_welcome_title') and self._welcome_title:
            self._welcome_title.setText(t('dashboard.welcome_title') if t else 'Palworld Save Tools')
        if hasattr(self, '_welcome_tips') and self._welcome_tips:
            self._welcome_tips.setText(t('dashboard.welcome_tips') if t else '')
        if hasattr(self, '_stat_label_refs'):
            for key, label_key in self._stat_label_refs.items():
                if key in self._stat_cards:
                    self._stat_cards[key].layout().itemAt(2).widget().setText(t(label_key) if t else label_key)
        if hasattr(self, '_overview_header'):
            self._overview_header.setText(t('dashboard.overview') if t else 'World Overview')
        if hasattr(self, '_drop_overlay'):
            self._drop_overlay._drop_text = t('tools.drop_title') if t else 'Drop Level.sav to Load Save'
            self._drop_overlay._drop_hint = t('tools.drop_hint_overlay') if t else "Or click the 'Load Save' button above"
            self._drop_overlay.update()
    def refresh(self):
        pass