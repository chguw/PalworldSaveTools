from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGraphicsDropShadowEffect, QMenu, QLabel, QScrollArea, QMenu, QSizePolicy
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QEvent, QRect, QEventLoop
from PySide6.QtGui import QFont, QColor, QCursor, QGuiApplication, QIcon
from i18n import t
from palworld_aio import constants
_BTN_STYLE = '''QPushButton { background: transparent; border: none; padding: 6px 16px; text-align: left; color: #E2E8F0; font-size: 12px; font-weight: 500; border-radius: 3px; min-height: 28px; } QPushButton:hover { background: rgba(125,211,252,0.15); color: #FFFFFF; } QPushButton:checked { background: rgba(125,211,252,0.08); color: #7DD3FC; } QPushButton:checked:hover { background: rgba(125,211,252,0.2); }'''
_SEP_STYLE = 'border-top: 1px solid rgba(255,255,255,0.1); margin: 4px 8px;'
class ScrollableContextMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._loop = None
        self.is_dark = True
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        self.container = QFrame(self)
        self.container.setStyleSheet('QFrame { background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(10,12,16,0.98), stop:0.5 rgba(12,16,22,0.98), stop:1 rgba(8,10,14,0.98)); border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; }')
        _shadow = QGraphicsDropShadowEffect(self.container)
        _shadow.setBlurRadius(20)
        _shadow.setOffset(3, 3)
        _shadow.setColor(QColor(0, 0, 0, 120))
        self.container.setGraphicsEffect(_shadow)
        cl = QVBoxLayout(self.container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        self.scroll_area = QScrollArea(self.container)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setFixedHeight(215)
        self.scroll_area.setStyleSheet('QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 5px; background: rgba(255,255,255,0.02); border-radius: 2px; } QScrollBar::handle:vertical { background: rgba(125,211,252,0.15); border-radius: 2px; min-height: 20px; } QScrollBar::handle:vertical:hover { background: rgba(125,211,252,0.35); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }')
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet('background: transparent;')
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.content_widget.setMinimumWidth(200)
        self.scroll_area.setWidget(self.content_widget)
        cl.addWidget(self.scroll_area)
        main_layout.addWidget(self.container)
        self.setMinimumWidth(220)
    def add_item(self, key, text, checkable=False, checked=False):
        btn = QPushButton(text)
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(checkable)
        btn.setChecked(checked)
        btn.setMinimumHeight(34)
        btn.setStyleSheet(_BTN_STYLE)
        btn.clicked.connect(lambda: self._select(key))
        self.layout.addWidget(btn)
        return btn
    def add_sep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(_SEP_STYLE)
        self.layout.addWidget(sep)
    def add_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet('color: #94A3B8; font-size: 10px; font-weight: 600; padding: 4px 16px 2px 16px; background: transparent; border: none;')
        self.layout.addWidget(lbl)
    def add_action(self, action):
        btn = QPushButton(action.text())
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(34)
        btn.setStyleSheet(_BTN_STYLE)
        btn.clicked.connect(action.trigger)
        self.layout.addWidget(btn)
        return btn
    def addSeparator(self):
        self.add_sep()
    def exec(self, pos):
        return self.exec_(pos)
    def _select(self, key):
        self._result = key
        self.close()
    def exec_(self, pos):
        self._result = None
        self.move(pos)
        self.adjustSize()
        self.show()
        self.raise_()
        self.activateWindow()
        loop = QEventLoop()
        self._loop = loop
        self.destroyed.connect(loop.quit)
        loop.exec()
        return self._result
    def closeEvent(self, event):
        if self._loop and self._loop.isRunning():
            self._loop.quit()
        super().closeEvent(event)