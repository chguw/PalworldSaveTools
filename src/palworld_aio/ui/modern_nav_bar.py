from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QRect
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

class NavButton(QPushButton):
    clicked_with_id = Signal(str)
    def __init__(self, button_id, icon_code, label, parent=None):
        super().__init__(parent)
        self._id = button_id
        self.setProperty('navButton', True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFont(QFont('Hack Nerd Font', 18))
        self.setFixedSize(40, 38)
        self.setText(icon_code)
        self.setToolTip(label)
        self.clicked.connect(lambda: self.clicked_with_id.emit(self._id))
    def set_active(self, active):
        self.setProperty('active', active)
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
        self._underline = QWidget(self)
        self._underline.setObjectName('navUnderline')
        self._underline.setFixedHeight(3)
        self._underline.hide()
        self._underline.raise_()
        self._anim = QPropertyAnimation(self._underline, b"geometry")
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._setup_ui()
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 5, 14, 5)
        layout.setSpacing(4)
        nav_items = [
            ('tools', ICONS['tools'], t('tools_tab') if t else 'Tools'),
            ('map', ICONS['map'], t('map.viewer') if t else 'Map'),
            ('base_inventory', ICONS['base_inventory'], t('base_inventory.tab') if t else 'Base Inventory'),
            ('player_inventory', ICONS['player_inventory'], t('inventory.tab') if t else 'Player Inventory'),
            ('pal_editor', ICONS['pal_editor'], t('pal_editor.tab') if t else 'Pal Editor'),
            ('players', ICONS['players'], t('deletion.search_players') if t else 'Players'),
            ('guilds', ICONS['guilds'], t('deletion.search_guilds') if t else 'Guilds'),
            ('bases', ICONS['bases'], t('deletion.search_bases') if t else 'Bases'),
            ('exclusions', ICONS['exclusions'], t('deletion.menu.exclusions') if t else 'Exclusions'),
        ]
        for btn_id, icon, label in nav_items:
            btn = NavButton(btn_id, icon, label)
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
        if self.isVisible():
            self._slide_underline(button_id)
    def showEvent(self, event):
        super().showEvent(event)
        if self._active_id:
            self._slide_underline(self._active_id)
    def _slide_underline(self, button_id):
        btn = self._buttons[button_id]
        r = btn.geometry()
        m = 6
        y = self.height() - 4
        h = 3
        target = QRect(r.x() + m, y, r.width() - 2 * m, h)
        if not self._underline.isVisible():
            self._underline.setGeometry(target)
            self._underline.show()
            return
        self._anim.stop()
        self._anim.setStartValue(self._underline.geometry())
        self._anim.setEndValue(target)
        self._anim.start()
    def refresh_labels(self):
        pass
