import os as _os
import re as _re

class ThemeManager:
    """Shared theme manager - loads darkmode.qss and applies to widgets."""
    _darkmode_content = None
    _base_dir = None

    @classmethod
    def init(cls, base_dir):
        cls._base_dir = base_dir

    @classmethod
    def _resolve_path(cls, base_dir=None):
        path = base_dir or cls._base_dir
        if not path:
            try:
                from palworld_aio import constants
                path = constants.get_src_path()
            except Exception:
                try:
                    from common import get_src_directory
                    path = get_src_directory()
                except Exception:
                    path = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        return path

    @classmethod
    def load_qss_content(cls, base_dir=None):
        if cls._darkmode_content is None:
            path = cls._resolve_path(base_dir)
            qss_path = _os.path.join(path, 'data', 'gui', 'darkmode.qss')
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    cls._darkmode_content = f.read()
            except FileNotFoundError:
                cls._darkmode_content = ''
        return cls._darkmode_content

    @classmethod
    def apply_global(cls, base_dir=None):
        qss = cls.load_qss_content(base_dir)
        if not qss:
            return cls._apply_fallback_global()
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
        except Exception:
            pass
        return True

    @classmethod
    def apply_to_widget(cls, widget, base_dir=None):
        qss = cls.load_qss_content(base_dir)
        if not qss:
            return cls._apply_fallback_widget(widget)
        try:
            widget.setStyleSheet(qss)
        except Exception:
            pass
        return True

    @classmethod
    def _apply_fallback_global(cls):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(_GLOBAL_FALLBACK_STYLE)
        except Exception:
            pass
        return False

    @classmethod
    def _apply_fallback_widget(cls, widget):
        try:
            widget.setStyleSheet(_GLOBAL_FALLBACK_STYLE)
        except Exception:
            pass
        return False

    @classmethod
    def load_styles(cls, widget):
        """Convenience method matching the external tools' load_styles pattern."""
        return cls.apply_to_widget(widget)


_GLOBAL_FALLBACK_STYLE = '''
QWidget {
    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,
        stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));
    color: #e2e8f0;
}
QLabel { color: #e2e8f0; }
QLineEdit {
    background: rgba(255,255,255,0.06); color: #e2e8f0;
    border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 6px 10px;
}
QPushButton {
    background: rgba(125,211,252,0.12); color: #7DD3FC;
    border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 8px 16px; font-weight: 600;
}
QPushButton:hover { background: rgba(125,211,252,0.2); color: #FFFFFF; }
QTreeWidget {
    background: rgba(255,255,255,0.03); color: #e2e8f0;
    border: 1px solid rgba(125,211,252,0.15); border-radius: 6px;
}
QHeaderView::section {
    background: rgba(125,211,252,0.1); color: #7DD3FC;
    border: none; border-right: 1px solid rgba(125,211,252,0.12); padding: 4px 8px;
}
'''

DIALOG_STYLE = '\nQDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n    color: #e2e8f0;\n}\nQLabel {\n    color: #e2e8f0;\n}\nQLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQSpinBox {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 4px 8px;\n}\nQSpinBox:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQComboBox {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQComboBox:hover {\n    border-color: rgba(125,211,252,0.3);\n}\nQComboBox QAbstractItemView {\n    background-color: rgba(18,20,24,0.98);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    selection-background-color: rgba(59,142,208,0.3);\n    border-radius: 4px;\n}\nQPushButton {\n    background: rgba(125,211,252,0.12);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    font-weight: 600;\n}\nQPushButton:hover {\n    background: rgba(125,211,252,0.2);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQPushButton:pressed {\n    background: rgba(125,211,252,0.3);\n}\nQListWidget {\n    background: rgba(255,255,255,0.03);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 6px;\n}\nQListWidget::item {\n    padding: 4px;\n    border: 1px solid rgba(125,211,252,0.12);\n    border-radius: 4px;\n    margin: 2px;\n}\nQListWidget::item:hover {\n    border: 1px solid rgba(125,211,252,0.3);\n    background: rgba(125,211,252,0.05);\n}\nQListWidget::item:selected {\n    border: 1px solid rgba(125,211,252,0.4);\n    background: rgba(59,142,208,0.2);\n}\n'
MENU_STYLE = '\nQMenu {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(10,12,16,0.98), stop:0.5 rgba(12,16,22,0.98), stop:1 rgba(8,10,14,0.98));\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    color: #e2e8f0;\n    padding: 4px;\n}\nQMenu::item {\n    padding: 6px 16px;\n    border-radius: 3px;\n    color: #e2e8f0;\n}\nQMenu::item:selected {\n    background: rgba(125,211,252,0.15);\n    color: #ffffff;\n}\nQMenu::separator {\n    height: 1px;\n    background: rgba(255,255,255,0.1);\n    margin: 4px 8px;\n}\n'
STATS_PANEL_STYLE = '\nStatsPanelWidget {\n    background: rgba(18,20,24,0.95);\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 8px;\n}\nStatsPanelWidget QLabel {\n    color: #e2e8f0;\n}\nStatsPanelWidget QLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 4px;\n    padding: 2px 4px;\n}\nStatsPanelWidget QLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nStatsPanelWidget QPushButton {\n    background: rgba(125,211,252,0.1);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 3px;\n    font-weight: bold;\n}\nStatsPanelWidget QPushButton:hover {\n    background: rgba(125,211,252,0.2);\n}\nStatsPanelWidget QProgressBar {\n    background: rgba(255,255,255,0.05);\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 3px;\n}\nStatsPanelWidget QProgressBar::chunk {\n    background: rgba(34,197,94,0.6);\n    border-radius: 2px;\n}\n'
PICKER_BG_STYLE = 'QWidget { background: rgba(18,20,24,0.98); border: 1px solid rgba(125,211,252,0.2); border-radius: 8px; }'
PICKER_SEARCH_STYLE = 'QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 4px 8px; font-size: 12px; }'
PICKER_LIST_STYLE = 'QListWidget { background: transparent; color: #e2e8f0; border: none; font-size: 12px; } QListWidget::item { padding: 3px 8px; border-radius: 3px; } QListWidget::item:hover { background: rgba(59,142,208,0.2); } QListWidget::item:selected { background: rgba(59,142,208,0.35); }'
INPUT_DIALOG_STYLE = 'QInputDialog{background:rgba(18,20,24,0.98);color:#e2e8f0}QLabel{color:#e2e8f0}QLineEdit{background:rgba(255,255,255,0.06);color:#e2e8f0;border:1px solid rgba(125,211,252,0.2);border-radius:4px;padding:4px 8px}QSpinBox{background:rgba(255,255,255,0.06);color:#e2e8f0;border:1px solid rgba(125,211,252,0.2);border-radius:4px;padding:4px}QPushButton{background:rgba(125,211,252,0.12);color:#7DD3FC;border:1px solid rgba(125,211,252,0.2);border-radius:4px;padding:4px 12px}QPushButton:hover{background:rgba(125,211,252,0.2)}'
TOOLTIP_STYLE = '\nQToolTip { background: rgba(18,20,24,0.98); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }'

def wrap_tooltip_text(text: str, width: int=80) -> str:
    if not text:
        return text
    lines = []
    for paragraph in text.replace('\r\n', '\n').split('\n'):
        words = paragraph.split(' ')
        current = ''
        for word in words:
            if len(current) + len(word) + 1 <= width or not current:
                current = (current + ' ' + word) if current else word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return '<br>'.join(lines)
