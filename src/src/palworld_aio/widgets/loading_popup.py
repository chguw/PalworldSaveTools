import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QMovie
class LoadingPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._setup_ui()
        self.fade_animation = None
        self._is_visible = False
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignCenter)
        gif_path = self._get_gif_path()
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.gif_label.setMovie(self.movie)
                self.movie.start()
                self.movie.jumpToFrame(0)
                first_frame = self.movie.currentPixmap()
                if not first_frame.isNull():
                    scaled_size = first_frame.size()
                    self.setFixedSize(scaled_size)
                else:
                    self.setFixedSize(300, 300)
            else:
                self._show_fallback()
        else:
            self._show_fallback()
        layout.addWidget(self.gif_label)
    def _get_gif_path(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            src_dir = os.path.join(base_dir, 'src')
        else:
            current_file = os.path.abspath(__file__)
            src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        gif_path = os.path.join(src_dir, 'data', 'gui', 'chillet-loading.gif')
        return gif_path
    def _show_fallback(self):
        self.gif_label.setText('Loading...')
        self.gif_label.setStyleSheet("\n            QLabel {\n                color: #7DD3FC;\n                font-size: 24px;\n                font-weight: bold;\n                font-family: 'Segoe UI',Arial;\n                background: rgba(18,20,24,0.95);\n                border-radius: 12px;\n                padding: 40px;\n            }\n        ")
        self.setFixedSize(200, 120)
    def show_with_fade(self):
        if self._is_visible:
            return
        self._center_on_screen()
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_animation = QPropertyAnimation(self, b'windowOpacity')
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()
        self._is_visible = True
    def hide_with_fade(self, on_complete=None):
        if not self._is_visible:
            if on_complete:
                on_complete()
            return
        self.fade_animation = QPropertyAnimation(self, b'windowOpacity')
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        def on_fade_complete():
            self.hide()
            self._is_visible = False
            if on_complete:
                on_complete()
        self.fade_animation.finished.connect(on_fade_complete)
        self.fade_animation.start()
    def _center_on_screen(self):
        parent = self.parent()
        size = self.size()
        if parent and hasattr(parent, 'geometry'):
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
            self.move(x, y)
        else:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            x = (screen.width() - size.width()) // 2
            y = (screen.height() - size.height()) // 2
            self.move(x, y)
    def closeEvent(self, event):
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()
        super().closeEvent(event)