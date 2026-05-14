from PySide6.QtWidgets import QWidget, QPushButton, QFrame, QVBoxLayout, QListWidget, QListWidgetItem, QLineEdit
from PySide6.QtCore import Qt, Signal, QPoint, QEvent, QTimer
from PySide6.QtGui import QColor, QKeyEvent
class _SearchEditKeyHandler:
    def __init__(self, search_edit, combo):
        self._search_edit = search_edit
        self._combo = combo
        search_edit.installEventFilter(self)
    def eventFilter(self, obj, event):
        if obj == self._search_edit and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key_Down:
                self._combo._select_next_item()
                return True
            elif key == Qt.Key_Up:
                self._combo._select_prev_item()
                return True
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                self._combo._confirm_selection()
                return True
            elif key == Qt.Key_Escape:
                self._combo._hide_popup()
                return True
        return False
class StyledCombo(QWidget):
    currentIndexChanged = Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._all_items = []
        self._current_index = -1
        self._enabled = True
        self._max_visible_items = 12
        self._searchable = False
        self._setup_ui()
        self._update_styles()
    def _setup_ui(self):
        self._button = QPushButton()
        self._button.setFixedHeight(24)
        self._button.setCursor(Qt.PointingHandCursor)
        self._button.clicked.connect(self._toggle_popup)
        self._search_edit = QLineEdit()
        self._search_edit.setFixedHeight(24)
        self._search_edit.setPlaceholderText('Search...')
        self._search_edit.setFocusPolicy(Qt.StrongFocus)
        self._search_edit.hide()
        self._search_edit.textChanged.connect(self._on_search_text_changed)
        self._popup = QFrame(self, Qt.Popup)
        self._popup.setFixedWidth(300)
        self._popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self._popup.setAttribute(Qt.WA_TranslucentBackground)
        self._popup.setFocusPolicy(Qt.NoFocus)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)
        self._list = QListWidget()
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.setFocusPolicy(Qt.NoFocus)
        popup_layout.addWidget(self._list)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._button)
        main_layout.addWidget(self._search_edit)
        self._popup.installEventFilter(self)
        self._search_edit.installEventFilter(self)
        self._search_edit_key_handler = _SearchEditKeyHandler(self._search_edit, self)
        self._focus_out_timer = QTimer()
        self._focus_out_timer.setSingleShot(True)
        self._focus_out_timer.timeout.connect(self._check_focus_out)
    def eventFilter(self, obj, event):
        if hasattr(self, '_popup') and obj == self._popup:
            if event.type() == QEvent.MouseButtonPress:
                pos = self.mapFromGlobal(event.globalPosition().toPoint())
                if not self._popup.geometry().contains(pos):
                    self._hide_popup()
                    return True
        elif obj == self._search_edit:
            if event.type() == QEvent.FocusIn:
                if self._searchable and self._enabled:
                    self._filter_popup(self._search_edit.text())
                    self._show_popup()
            elif event.type() == QEvent.FocusOut:
                self._focus_out_timer.start(150)
        return super().eventFilter(obj, event)
    def _check_focus_out(self):
        if self._searchable and self._popup.isVisible():
            focused = QApplication.focusWidget()
            if focused != self._search_edit and focused != self._list and (not self._popup.isAncestorOf(focused) if focused else True):
                self._hide_popup()
    def _update_styles(self):
        btn_style = '\n            QPushButton {\n                background-color: rgba(30, 35, 45, 0.8);\n                border: 1px solid rgba(255, 255, 255, 0.2);\n                border-radius: 4px;\n                padding: 4px 8px;\n                color: #e0e0e0;\n                text-align: left;\n            }\n            QPushButton::menu-indicator {\n                width: 0px;\n                subcontrol-position: right center;\n                subcontrol-origin: padding;\n            }\n            QPushButton:hover {\n                border-color: rgba(74, 144, 226, 0.5);\n            }\n            QPushButton:disabled {\n                background-color: rgba(40, 45, 55, 0.6);\n                color: #888888;\n                border-color: rgba(255, 255, 255, 0.1);\n            }\n        '
        self._button.setStyleSheet(btn_style)
        search_style = '\n            QLineEdit {\n                background-color: rgba(30, 35, 45, 0.8);\n                border: 1px solid rgba(255, 255, 255, 0.2);\n                border-radius: 4px;\n                padding: 4px 8px;\n                color: #e0e0e0;\n                selection-background-color: rgba(59, 142, 208, 0.4);\n            }\n            QLineEdit:hover {\n                border-color: rgba(74, 144, 226, 0.5);\n            }\n            QLineEdit:disabled {\n                background-color: rgba(40, 45, 55, 0.6);\n                color: #888888;\n                border-color: rgba(255, 255, 255, 0.1);\n            }\n            QLineEdit:focus {\n                border-color: rgba(74, 144, 226, 0.7);\n            }\n        '
        self._search_edit.setStyleSheet(search_style)
        self._popup.setStyleSheet('\n            QFrame {\n                background-color: transparent;\n            }\n        ')
        self._list.setStyleSheet('\n            QListWidget {\n                background-color: rgba(18, 20, 24, 0.98);\n                border: 1px solid rgba(125, 211, 252, 0.3);\n                border-radius: 6px;\n                padding: 4px;\n                color: #e2e8f0;\n            }\n            QListWidget::item {\n                padding: 6px 12px;\n                border-radius: 3px;\n                height: 28px;\n            }\n            QListWidget::item:selected {\n                background-color: rgba(59, 142, 208, 0.3);\n                color: #ffffff;\n            }\n            QListWidget::item:hover {\n                background-color: rgba(59, 142, 208, 0.2);\n            }\n            QListWidget::item:disabled {\n                color: #666666;\n                background-color: transparent;\n            }\n            QScrollBar:vertical {\n                background: rgba(30, 35, 45, 0.5);\n                width: 8px;\n                border-radius: 4px;\n                margin: 2px;\n            }\n            QScrollBar::handle:vertical {\n                background: rgba(74, 144, 226, 0.5);\n                border-radius: 4px;\n                min-height: 30px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: rgba(74, 144, 226, 0.8);\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: none;\n            }\n        ')
    def setSearchable(self, searchable: bool):
        self._searchable = searchable
        if searchable:
            self._button.hide()
            self._search_edit.show()
        else:
            self._button.show()
            self._search_edit.hide()
    def setSearchPlaceholder(self, text: str):
        self._search_edit.setPlaceholderText(text)
    def setMaxVisibleItems(self, count):
        self._max_visible_items = count
        self._update_popup_height()
    def _update_popup_height(self):
        item_height = 28
        max_height = self._max_visible_items * item_height + 8
        self._list.setMaximumHeight(max_height)
    def _toggle_popup(self):
        if not self._enabled:
            return
        if self._popup.isVisible():
            self._hide_popup()
        else:
            self._show_popup()
    def _show_popup(self):
        self._update_popup_height()
        if self._searchable:
            self._list.setMinimumWidth(max(self._search_edit.width() - 8, 180))
            pos = self._search_edit.mapToGlobal(QPoint(0, self._search_edit.height()))
        else:
            self._list.setMinimumWidth(self._button.width() - 8)
            pos = self._button.mapToGlobal(QPoint(0, self._button.height()))
        self._popup.move(pos)
        self._popup.show()
        if not self._searchable:
            self._list.setFocus()
    def _hide_popup(self):
        self._popup.hide()
    def _select_next_item(self):
        if not self._popup.isVisible() or self._list.count() == 0:
            return
        current = self._list.currentRow()
        next_row = current + 1 if current < self._list.count() - 1 else 0
        self._list.setCurrentRow(next_row)
    def _select_prev_item(self):
        if not self._popup.isVisible() or self._list.count() == 0:
            return
        current = self._list.currentRow()
        prev_row = current - 1 if current > 0 else self._list.count() - 1
        self._list.setCurrentRow(prev_row)
    def _confirm_selection(self):
        if not self._popup.isVisible() or self._list.count() == 0:
            return
        current = self._list.currentRow()
        if current < 0:
            current = 0
        item = self._list.item(current)
        if item and (item.flags() & Qt.ItemIsEnabled):
            self._on_item_clicked(item)
    def _on_search_text_changed(self, text):
        self._filter_popup(text)
        if not self._popup.isVisible():
            self._show_popup()
    def _filter_popup(self, text):
        self._list.blockSignals(True)
        self._list.clear()
        self._items = []
        if not text:
            for data in self._all_items:
                item = QListWidgetItem(data['text'])
                item.setData(Qt.UserRole, data['userData'])
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self._list.addItem(item)
                self._items.append(data)
        else:
            query_lower = text.lower()
            for data in self._all_items:
                if query_lower in data['text'].lower():
                    item = QListWidgetItem(data['text'])
                    item.setData(Qt.UserRole, data['userData'])
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self._list.addItem(item)
                    self._items.append(data)
        self._update_popup_height()
        self._list.blockSignals(False)
    def _on_item_clicked(self, item):
        index = self._list.row(item)
        if item.flags() & Qt.ItemIsEnabled:
            self._current_index = index
            text = item.text()
            if self._searchable:
                self._search_edit.blockSignals(True)
                self._search_edit.setText(text)
                self._search_edit.blockSignals(False)
            else:
                self._button.setText(text)
            self._hide_popup()
            self.currentIndexChanged.emit(index)
    def addItem(self, text, userData=None):
        data = {'text': text, 'userData': userData, 'enabled': True}
        self._all_items.append(data)
        if self._searchable and self._search_edit.text():
            return
        self._items.append(data)
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, userData)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self._list.addItem(item)
        if self._current_index == -1:
            self.setCurrentIndex(0)
    def clear(self):
        self._all_items = []
        self._items = []
        self._list.clear()
        self._current_index = -1
        if self._searchable:
            self._search_edit.blockSignals(True)
            self._search_edit.clear()
            self._search_edit.blockSignals(False)
        else:
            self._button.setText('')
    def currentIndex(self):
        return self._current_index
    def currentData(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]['userData']
        return None
    def setCurrentIndex(self, index):
        if 0 <= index < len(self._items):
            self._current_index = index
            text = self._items[index]['text']
            if self._searchable:
                self._search_edit.blockSignals(True)
                self._search_edit.setText(text)
                self._search_edit.blockSignals(False)
            else:
                self._button.setText(text)
            self._list.setCurrentRow(index)
            return True
        return False
    def count(self):
        return len(self._items)
    def itemData(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]['userData']
        return None
    def setEnabled(self, enabled):
        self._enabled = enabled
        self._button.setEnabled(enabled)
        self._search_edit.setEnabled(enabled)
        if not enabled:
            if self._searchable:
                self._search_edit.blockSignals(True)
                self._search_edit.clear()
                self._search_edit.blockSignals(False)
            else:
                self._button.setText('')
            self._current_index = -1
    def setItemEnabled(self, index, enabled):
        if 0 <= index < len(self._items):
            self._items[index]['enabled'] = enabled
            item = self._list.item(index)
            if item:
                if enabled:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                else:
                    item.setFlags(Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
    def blockSignals(self, block):
        self._list.blockSignals(block)
    def currentText(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]['text']
        return ''
    def setItemText(self, index, text):
        if 0 <= index < len(self._items):
            self._items[index]['text'] = text
            item = self._list.item(index)
            if item:
                item.setText(text)
    def model(self):
        return self._list.model()
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QApplication
