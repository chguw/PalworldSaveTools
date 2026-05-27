from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QStyleOptionButton, QStylePainter, QStyle
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QCursor, QPainter, QColor, QBrush, QFontMetrics
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-fa-wrench': '\uf0ad', 'nf-fa-map': '\uf279', 'nf-fa-warehouse': '\ued92', 'nf-fa-suitcase': '\uf0f2', 'nf-fa-dragon': '\ueef8', 'nf-fa-users': '\uf0c0', 'nf-fa-shield': '\uf132', 'nf-fa-home': '\uf015', 'nf-fa-ban': '\uf05e', 'nf-fa-chevron_right': '\uf054', 'nf-fa-chevron_left': '\uf053', 'nf-fa-terminal': '\uf120'}
from i18n import t
ICONS = {'tools': nf.icons.get('nf-fa-wrench', '\uf0ad'), 'map': nf.icons.get('nf-fa-map', '\uf279'), 'base_inventory': nf.icons.get('nf-fa-warehouse', '\ued92'), 'player_inventory': nf.icons.get('nf-fa-suitcase', '\uf0f2'), 'pal_editor': nf.icons.get('nf-fa-dragon', '\ueef8'), 'players': nf.icons.get('nf-fa-users', '\uf0c0'), 'guilds': nf.icons.get('nf-fa-shield', '\uf132'), 'bases': nf.icons.get('nf-fa-home', '\uf015'), 'exclusions': nf.icons.get('nf-fa-ban', '\uf05e'), 'collapse_open': nf.icons.get('nf-fa-chevron_right', '\uf054'), 'collapse_close': nf.icons.get('nf-fa-chevron_left', '\uf053'), 'console': nf.icons.get('nf-fa-terminal', '\uf120')}
SIDEBAR_W = 48
ITEM_H = 44

class NerdBtn(QPushButton):
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
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()


class NerdLabel(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.text():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()


class NavItem(QPushButton):
    clicked_with_id = Signal(str)
    def __init__(self, button_id, icon_code, label, parent=None):
        super().__init__(parent)
        self._id = button_id
        self.setProperty('sidebarItem', True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFont(QFont('Hack Nerd Font', 18))
        self.setFixedSize(SIDEBAR_W, ITEM_H)
        self.setText(icon_code)
        self.setToolTip(label)
        self.clicked.connect(lambda: self.clicked_with_id.emit(self._id))
    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
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
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()

        if self.property('active'):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            pw, ph = 4, 20
            px, py = 3, (self.height() - ph) // 2
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
            p.end()
class BottomBtn(QPushButton):
    def __init__(self, icon_code, tooltip, parent=None):
        super().__init__(parent)
        self.setProperty('sidebarItem', True)
        self.setProperty('active', False)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFont(QFont('Hack Nerd Font', 16))
        self.setFixedSize(SIDEBAR_W, ITEM_H)
        self.setText(icon_code)
        self.setToolTip(tooltip)
    def set_icon(self, icon_code):
        self.setText(icon_code)
    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
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
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()

        if self.property('active'):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            pw, ph = 4, 20
            px, py = 3, (self.height() - ph) // 2
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
            p.end()
class SidebarWidget(QWidget):
    nav_changed = Signal(str)
    console_toggled = Signal()
    right_panel_toggled = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sideBar')
        self.setFixedWidth(SIDEBAR_W)
        self._buttons = {}
        self._nav_keys = {}
        self._active_id = None
        self._right_panel_visible = True
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(2)
        nav_items = [('tools', ICONS['tools'], t('tools_tab') if t else 'Tools'), ('map', ICONS['map'], t('map.viewer') if t else 'Map'), ('base_inventory', ICONS['base_inventory'], t('base_inventory.tab') if t else 'Base Inventory'), ('player_inventory', ICONS['player_inventory'], t('inventory.tab') if t else 'Player Inventory'), ('pal_editor', ICONS['pal_editor'], t('pal_editor.tab') if t else 'Pal Editor'), ('players', ICONS['players'], t('deletion.search_players') if t else 'Players'), ('guilds', ICONS['guilds'], t('deletion.search_guilds') if t else 'Guilds'), ('bases', ICONS['bases'], t('deletion.search_bases') if t else 'Bases'), ('exclusions', ICONS['exclusions'], t('deletion.menu.exclusions') if t else 'Exclusions')]
        for btn_id, icon, label in nav_items:
            item = NavItem(btn_id, icon, label)
            item.clicked_with_id.connect(self._on_item_clicked)
            self._buttons[btn_id] = item
            self._nav_keys[btn_id] = btn_id
            layout.addWidget(item)
        layout.addStretch()
        self._console_btn = BottomBtn(ICONS['console'], t('console.detach') if t else 'Console')
        self._console_btn.clicked.connect(self.console_toggled.emit)
        layout.addWidget(self._console_btn)
        self._right_panel_btn = BottomBtn(ICONS['collapse_open'], t('sidebar.close') if t else 'Close Panel')
        self._right_panel_btn.clicked.connect(self._on_right_panel_toggle)
        self._right_panel_btn.set_active(True)
        self._update_right_panel_icon()
        layout.addWidget(self._right_panel_btn)
    def _on_item_clicked(self, button_id):
        self.set_active(button_id)
        self.nav_changed.emit(button_id)
    def set_active(self, button_id):
        if button_id not in self._buttons:
            return
        self._active_id = button_id
        for bid, btn in self._buttons.items():
            btn.set_active(bid == button_id)
    def _on_right_panel_toggle(self):
        self._right_panel_visible = not self._right_panel_visible
        self._right_panel_btn.set_active(self._right_panel_visible)
        self._update_right_panel_icon()
        self.right_panel_toggled.emit()
    def set_right_panel_visible(self, visible):
        self._right_panel_visible = visible
        self._right_panel_btn.set_active(visible)
        self._update_right_panel_icon()
    def set_console_visible(self, visible):
        self._console_btn.set_active(visible)
    def _update_right_panel_icon(self):
        if self._right_panel_visible:
            self._right_panel_btn.set_icon(ICONS['collapse_open'])
            self._right_panel_btn.setToolTip(t('sidebar.close') if t else 'Close Panel')
        else:
            self._right_panel_btn.set_icon(ICONS['collapse_close'])
            self._right_panel_btn.setToolTip(t('sidebar.open') if t else 'Open Panel')
    def refresh_labels(self):
        nav_keys = {'tools': 'tools_tab', 'map': 'map.viewer', 'base_inventory': 'base_inventory.tab', 'player_inventory': 'inventory.tab', 'pal_editor': 'pal_editor.tab', 'players': 'deletion.search_players', 'guilds': 'deletion.search_guilds', 'bases': 'deletion.search_bases', 'exclusions': 'deletion.menu.exclusions'}
        for btn_id, btn in self._buttons.items():
            key = nav_keys.get(btn_id, btn_id)
            btn.setToolTip(t(key) if t else btn_id)
        self._console_btn.setToolTip(t('console.detach') if t else 'Console')
        self._update_right_panel_icon()

    def set_lock_state(self, locked):
        return True