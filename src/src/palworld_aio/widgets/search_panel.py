from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from i18n import t
from palworld_aio import constants
class SearchPanel(QWidget):
    item_selected = Signal(object)
    item_double_clicked = Signal(object)
    search_requested = Signal(str)
    def __init__(self, label_key, column_keys, column_widths=None, parent=None):
        super().__init__(parent)
        self.label_key = label_key
        self.column_keys = column_keys
        self.column_widths = column_widths or []
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        search_layout = QHBoxLayout()
        self.search_label = QLabel(t(self.label_key) if t else self.label_key)
        self.search_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.search_label.setObjectName('sectionHeader')
        search_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        self.search_input.setObjectName('searchInput')
        self.search_input.setPlaceholderText(t('search.placeholder') if t else 'Type to search...')
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input, stretch=1)
        layout.addLayout(search_layout)
        self.tree = QTreeWidget()
        self.tree.setObjectName('searchTree')
        self.columns = [t(k) if k else '' for k in self.column_keys]
        self.tree.setHeaderLabels(self.columns)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.tree.header()
        for i, width in enumerate(self.column_widths):
            if i < len(self.columns):
                self.tree.setColumnWidth(i, width)
        header.setStretchLastSection(True)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, stretch=1)
        self._all_items = []
    def _on_search(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            match = False
            for col in range(item.columnCount()):
                if text in item.text(col).lower():
                    match = True
                    break
            item.setHidden(not match)
    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if items:
            item = items[0]
            data = [item.text(i) for i in range(item.columnCount())]
            self.item_selected.emit(data)
    def _on_double_click(self, item, column):
        data = [item.text(i) for i in range(item.columnCount())]
        self.item_double_clicked.emit(data)
    def clear(self):
        self.tree.clear()
        self._all_items = []
    def add_item(self, values, data=None):
        item = QTreeWidgetItem([str(v) for v in values])
        if data:
            item.setData(0, Qt.UserRole, data)
        self.tree.addTopLevelItem(item)
        self._all_items.append(item)
        return item
    def get_selected_item(self):
        items = self.tree.selectedItems()
        if items:
            return items[0]
        return None
    def get_selected_data(self):
        item = self.get_selected_item()
        if item:
            return [item.text(i) for i in range(item.columnCount())]
        return None
    def set_items(self, items_data):
        self.clear()
        for values in items_data:
            self.add_item(values)
    def refresh_labels(self):
        self.search_label.setText(t(self.label_key) if t else self.label_key)
        self.search_input.setPlaceholderText(t('search.placeholder') if t else 'Type to search...')
        self.columns = [t(k) if k else '' for k in self.column_keys]
        self.tree.setHeaderLabels(self.columns)