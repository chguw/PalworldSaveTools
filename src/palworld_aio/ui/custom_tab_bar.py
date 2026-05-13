from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QCursor
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-cod-triangle_left': '\ueb9b', 'nf-cod-triangle_right': '\ueb9c'}
from i18n import t
from .custom_floating_tab import FloatingTabBar
class TabBarContainer(QWidget):
    sidebar_toggle_clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    def _setup_ui(self):
        self.setObjectName('tabBarContainer')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(8)
        self.tab_bar = FloatingTabBar()
        self.tab_bar.setObjectName('customTabBar')
        self.tab_bar.setExpanding(False)
        layout.addWidget(self.tab_bar)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.collapse_btn = QPushButton()
        self.collapse_btn.setObjectName('sidebarChip')
        self.collapse_btn.setFlat(True)
        self.collapse_btn.setFont(QFont('Hack Nerd Font', 14))
        self.collapse_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.collapse_btn.clicked.connect(self.sidebar_toggle_clicked.emit)
        self.set_sidebar_collapsed(False)
        layout.addWidget(self.collapse_btn)
    def set_sidebar_collapsed(self, collapsed):
        if collapsed:
            icon = nf.icons['nf-cod-triangle_left']
            text = t('sidebar.open') if t else 'Open'
            tooltip = t('sidebar.open') if t else 'Open'
        else:
            icon = nf.icons['nf-cod-triangle_right']
            text = t('sidebar.close') if t else 'Close'
            tooltip = t('sidebar.close') if t else 'Close'
        self.collapse_btn.setText(f'{icon} {text}')
        self.collapse_btn.setToolTip(tooltip)
    def refresh_labels(self):
        collapsed = self.collapse_btn.text().startswith(nf.icons['nf-cod-triangle_left'])
        self.set_sidebar_collapsed(collapsed)