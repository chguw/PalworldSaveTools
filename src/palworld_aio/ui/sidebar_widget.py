from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal, Qt, QVariantAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QCursor
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-cod-tools': '\uea83', 'nf-cod-globe': '\ueaf0', 'nf-cod-package': '\ueb3f', 'nf-cod-archive': '\ueb07', 'nf-cod-star-full': '\ueb7c', 'nf-cod-organization': '\ueb87', 'nf-cod-shield': '\ueb4b', 'nf-cod-home': '\ueaa2', 'nf-cod-circle-slash': '\uea54', 'nf-cod-triangle_right': '\ueb9c', 'nf-cod-triangle_left': '\ueb9b', 'nf-cod-terminal': '\ueac5', 'nf-cod-discord': '\ueb5c'}
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
    'collapse_open': nf.icons.get('nf-cod-triangle_right', '\ueb9c'),
    'collapse_close': nf.icons.get('nf-cod-triangle_left', '\ueb9b'),
    'console': nf.icons.get('nf-cod-terminal', '\ueac5'),
}

COLLAPSED_W = 48
EXPANDED_W = 160
ITEM_H = 44

class SidebarItem(QWidget):
    clicked_with_id = Signal(str)
    def __init__(self, button_id, icon_code, label, parent=None):
        super().__init__(parent)
        self._id = button_id
        self._label_text = label
        self._active = False
        self._hovered = False
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(ITEM_H)
        self.setFixedWidth(COLLAPSED_W)
        self._anim = QVariantAnimation()
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim.valueChanged.connect(self.setFixedWidth)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._icon = QLabel(icon_code)
        self._icon.setFont(QFont('Hack Nerd Font', 18))
        self._icon.setFixedWidth(COLLAPSED_W)
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)
        self._label = QLabel('')
        self._label.setFont(QFont(constants.FONT_FAMILY, 11, QFont.DemiBold))
        self._label.setVisible(False)
        layout.addWidget(self._label)
        layout.addStretch()
        self._refresh()
    def _refresh(self):
        if self._active:
            self._icon.setStyleSheet('color: #7DD3FC; font-size: 18px; border: none; background: transparent;')
            self._label.setStyleSheet('color: #7DD3FC; font-weight: 700; border: none; background: transparent;')
        elif self._hovered:
            self._icon.setStyleSheet('color: #E6EEF6; font-size: 18px; border: none; background: transparent;')
            self._label.setStyleSheet('color: #E6EEF6; border: none; background: transparent;')
        else:
            self._icon.setStyleSheet('color: #A6B8C8; font-size: 18px; border: none; background: transparent;')
            self._label.setStyleSheet('color: #A6B8C8; border: none; background: transparent;')
    def set_active(self, active):
        self._active = active
        self._refresh()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked_with_id.emit(self._id)
    def enterEvent(self, event):
        self._hovered = True
        self._label.setText(self._label_text)
        self._label.setVisible(True)
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(EXPANDED_W)
        self._anim.start()
        self._refresh()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(COLLAPSED_W)
        self._anim.start()
        QTimer.singleShot(200, lambda: self._label.setVisible(self._hovered))
        self._refresh()
        super().leaveEvent(event)

class BottomButton(QWidget):
    clicked = Signal()
    def __init__(self, icon_code, tooltip, parent=None):
        super().__init__(parent)
        self._hovered = False
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(COLLAPSED_W, ITEM_H)
        self.setToolTip(tooltip)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._icon = QLabel(icon_code)
        self._icon.setFont(QFont('Hack Nerd Font', 16))
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)
        self._refresh()
    def _refresh(self):
        if self._hovered:
            self._icon.setStyleSheet('color: #E6EEF6; font-size: 16px; border: none; background: transparent;')
        else:
            self._icon.setStyleSheet('color: #A6B8C8; font-size: 16px; border: none; background: transparent;')
    def set_icon(self, icon_code):
        self._icon.setText(icon_code)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
    def enterEvent(self, event):
        self._hovered = True
        self._refresh()
    def leaveEvent(self, event):
        self._hovered = False
        self._refresh()

class SidebarWidget(QWidget):
    nav_changed = Signal(str)
    console_toggled = Signal()
    right_panel_toggled = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sideBar')
        self.setFixedWidth(200)
        self._buttons = {}
        self._active_id = None
        self._right_panel_visible = True
        self._setup_ui()
    def _setup_ui(self):
        self._bg = QFrame(self)
        self._bg.setObjectName('sidebarBg')
        self._bg.setFixedWidth(COLLAPSED_W)
        container = QWidget(self)
        container.setObjectName('sidebarContent')
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(2)
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
            item = SidebarItem(btn_id, icon, label)
            item.clicked_with_id.connect(self._on_item_clicked)
            self._buttons[btn_id] = item
            layout.addWidget(item)
        layout.addStretch()
        self._console_btn = BottomButton(ICONS['console'], t('console.detach') if t else 'Console', container)
        self._console_btn.clicked.connect(self.console_toggled.emit)
        layout.addWidget(self._console_btn)
        self._right_panel_btn = BottomButton(ICONS['collapse_close'], t('sidebar.close') if t else 'Close Panel', container)
        self._right_panel_btn.clicked.connect(self._on_right_panel_toggle)
        layout.addWidget(self._right_panel_btn)
        container.setGeometry(0, 0, 200, 0)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._bg.setGeometry(0, 0, COLLAPSED_W, self.height())
        for child in self.findChildren(QWidget):
            if child.objectName() == 'sidebarContent':
                child.setGeometry(0, 0, 200, self.height())
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
        if self._right_panel_visible:
            self._right_panel_btn.set_icon(ICONS['collapse_close'])
            self._right_panel_btn.setToolTip(t('sidebar.close') if t else 'Close Panel')
        else:
            self._right_panel_btn.set_icon(ICONS['collapse_open'])
            self._right_panel_btn.setToolTip(t('sidebar.open') if t else 'Open Panel')
        self.right_panel_toggled.emit()
    def set_right_panel_visible(self, visible):
        self._right_panel_visible = visible
        if visible:
            self._right_panel_btn.set_icon(ICONS['collapse_close'])
            self._right_panel_btn.setToolTip(t('sidebar.close') if t else 'Close Panel')
        else:
            self._right_panel_btn.set_icon(ICONS['collapse_open'])
            self._right_panel_btn.setToolTip(t('sidebar.open') if t else 'Open Panel')
    def refresh_labels(self):
        pass
