from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame, QSizePolicy, QPushButton, QListWidget, QListWidgetItem, QApplication
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont, QCursor
from i18n import t
from palworld_aio.edit_pals import PalEditorWidget
from palworld_aio import constants
class PalEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_player_uid = None
        self.current_player_name = None
        self._player_list = []
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        header = QHBoxLayout()
        self.title_label = QLabel(t('pal_editor.title'))
        self.title_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.title_label.setObjectName('sectionHeader')
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
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area)
    def _create_content_area(self):
        frame = QFrame()
        frame.setObjectName('palEditorContent')
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setStyleSheet('QFrame#palEditorContent { background: rgba(18,20,24,0.65); border: 1px solid rgba(125,211,252,0.15); border-radius: 10px; }')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        self.placeholder_label = QLabel(t('pal_editor.select_player_hint', default='Select a player to edit their pals'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setMinimumHeight(400)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setStyleSheet('QLabel { color: #A6B8C8; font-size: 14px; background: transparent; }')
        layout.addWidget(self.placeholder_label)
        self.pal_editor_widget = PalEditorWidget()
        self.pal_editor_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pal_editor_widget.hide()
        layout.addWidget(self.pal_editor_widget)
        return frame
    def _open_player_popup(self):
        if not self._player_list:
            self._load_players()
        popup = QWidget()
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        popup.setStyleSheet('QWidget { background: rgba(18,20,24,0.98); border: 1px solid rgba(125,211,252,0.2); border-radius: 8px; }')
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        search = QLineEdit()
        search.setPlaceholderText(t('inventory.search_players', default='Search players...'))
        search.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 4px 8px; font-size: 12px; }')
        layout.addWidget(search)
        lst = QListWidget()
        lst.setStyleSheet('QListWidget { background: transparent; color: #e2e8f0; border: none; font-size: 12px; } QListWidget::item { padding: 3px 8px; border-radius: 3px; } QListWidget::item:hover { background: rgba(59,142,208,0.2); } QListWidget::item:selected { background: rgba(59,142,208,0.35); }')
        lst.setMaximumHeight(300)
        lst.setMinimumWidth(220)
        clear_item = QListWidgetItem('-- clear --')
        lst.addItem(clear_item)
        for player in self._player_list:
            item = QListWidgetItem(player['display'])
            item.setData(Qt.UserRole, player)
            lst.addItem(item)
        search.textChanged.connect(lambda t, l=lst: [l.item(i).setHidden(t.lower() not in l.item(i).text().lower()) for i in range(l.count())])
        layout.addWidget(lst)
        popup.move(QCursor.pos())
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
            self._clear_editor()
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        elif chosen:
            self.current_player_uid = chosen['uid']
            self.current_player_name = chosen['name']
            self.player_select_btn.setText(chosen['display'])
            self._show_editor()
    def _show_editor(self):
        if self.current_player_uid:
            self.placeholder_label.hide()
            self.pal_editor_widget.show()
            self.pal_editor_widget.set_player(self.current_player_uid, self.current_player_name)
    def _clear_editor(self):
        self.pal_editor_widget.hide()
        self.pal_editor_widget.clear()
        self.placeholder_label.show()
    def refresh(self):
        self._load_players()
    def _load_players(self):
        self._player_list = []
        self._clear_editor()
        if constants.loaded_level_json:
            from palworld_aio.save_manager import save_manager
            players = save_manager.get_players()
            for uid, name, gid, lastseen, level in players:
                display_name = f'{name} (Lv.{level})'
                self._player_list.append({'uid': uid, 'name': name, 'level': level, 'display': display_name})
        self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
    def refresh_labels(self):
        if hasattr(self, 'title_label'):
            self.title_label.setText(t('pal_editor.title'))
        if hasattr(self, 'player_select_btn') and (not self.current_player_uid):
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('pal_editor.select_player_hint', default='Select a player to edit their pals'))
        if hasattr(self, 'pal_editor_widget'):
            self.pal_editor_widget.refresh_labels()