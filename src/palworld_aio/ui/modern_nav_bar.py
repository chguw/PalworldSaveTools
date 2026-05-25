from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QCursor
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-cod-tools': '\uea83', 'nf-cod-globe': '\ueaf0', 'nf-cod-package': '\ueb3f', 'nf-cod-archive': '\ueb07', 'nf-cod-star-full': '\ueb7c', 'nf-cod-organization': '\ueb87', 'nf-cod-shield': '\ueb4b', 'nf-cod-home': '\ueaa2', 'nf-cod-circle-slash': '\uea54'}
from i18n import t
from palworld_aio import constants

ICONS = {
    'tools': nf.icons.get('nf-cod-tools', '\uea83'),
    'map': nf.icons.get('nf-cod-globe', '\ueaf0'),
    'base_inventory': nf.icons.get('nf-cod-package', '\ueb3f'),
    'player_inventory': nf.icons.get('nf-cod-archive', '\ueb07'),
    'pal_editor': nf.icons.get('nf-cod-star-full', '\ueb7c'),
    'players': nf.icons.get('nf-cod-organization', '\ueb87'),
    'guilds': nf.icons.get('nf-cod-shield', '\ueb4b'),
    'bases': nf.icons.get('nf-cod-home', '\ueaa2'),
    'exclusions': nf.icons.get('nf-cod-circle-slash', '\uea54'),
}

class PillButton(QPushButton):
    clicked_with_id = Signal(str)
    def __init__(self, button_id, icon_code, label, parent=None):
        super().__init__(parent)
        self._id = button_id
        self._label = label
        self.setProperty('pillButton', True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFont(QFont('Hack Nerd Font', 18))
        self.setFixedSize(42, 38)
        self.setText(icon_code)
        self.setToolTip(label)
        self.clicked.connect(lambda: self.clicked_with_id.emit(self._id))
    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)
    def set_position(self, pos):
        self.setProperty('pillPosition', pos)
        self.style().unpolish(self)
        self.style().polish(self)

class ModernNavBar(QWidget):
    nav_changed = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('modernNavBar')
        self.setFixedHeight(48)
        self._buttons = {}
        self._active_id = None
        self._setup_ui()
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 5, 16, 5)
        layout.setSpacing(0)
        groups = [
            [
                ('tools', ICONS['tools'], t('tools_tab') if t else 'Tools'),
                ('map', ICONS['map'], t('map.viewer') if t else 'Map'),
            ],
            [
                ('base_inventory', ICONS['base_inventory'], t('base_inventory.tab') if t else 'Base Inventory'),
                ('player_inventory', ICONS['player_inventory'], t('inventory.tab') if t else 'Player Inventory'),
            ],
            [
                ('pal_editor', ICONS['pal_editor'], t('pal_editor.tab') if t else 'Pal Editor'),
            ],
            [
                ('players', ICONS['players'], t('deletion.search_players') if t else 'Players'),
                ('guilds', ICONS['guilds'], t('deletion.search_guilds') if t else 'Guilds'),
                ('bases', ICONS['bases'], t('deletion.search_bases') if t else 'Bases'),
            ],
            [
                ('exclusions', ICONS['exclusions'], t('deletion.menu.exclusions') if t else 'Exclusions'),
            ],
        ]
        first_group = True
        for group in groups:
            if not first_group:
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                sep.setFixedWidth(1)
                sep.setFixedHeight(20)
                sep.setStyleSheet('background: rgba(125, 211, 252, 0.12); border: none;')
                spacer_left = QSpacerItem(8, 1, QSizePolicy.Fixed, QSizePolicy.Minimum)
                spacer_right = QSpacerItem(8, 1, QSizePolicy.Fixed, QSizePolicy.Minimum)
                layout.addSpacerItem(spacer_left)
                layout.addWidget(sep)
                layout.addSpacerItem(spacer_right)
            else:
                first_group = False
            count = len(group)
            for i, (btn_id, icon, label) in enumerate(group):
                btn = PillButton(btn_id, icon, label)
                if count == 1:
                    btn.set_position('single')
                elif i == 0:
                    btn.set_position('first')
                elif i == count - 1:
                    btn.set_position('last')
                else:
                    btn.set_position('middle')
                btn.clicked_with_id.connect(self._on_button_clicked)
                self._buttons[btn_id] = btn
                layout.addWidget(btn)
        layout.addStretch()
    def _on_button_clicked(self, button_id):
        self.set_active(button_id)
        self.nav_changed.emit(button_id)
    def set_active(self, button_id):
        if button_id not in self._buttons:
            return
        self._active_id = button_id
        for bid, btn in self._buttons.items():
            btn.set_active(bid == button_id)
    def refresh_labels(self):
        pass
