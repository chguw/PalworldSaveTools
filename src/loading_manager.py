import sys, os, time, random, subprocess, threading, json, traceback
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QTextEdit, QGraphicsOpacityEffect, QMessageBox, QProgressBar, QDialog
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPropertyAnimation, QPoint, QSize
from PySide6.QtGui import QPixmap, QFont, QCursor
from import_libs import *
_result_data = {'status': 'idle', 'data': None}
def get_base_directory():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get_src_directory():
    base_dir = get_base_directory()
    return os.path.join(base_dir, 'src')
def get_resources_directory():
    return os.path.join(get_base_directory(), 'resources')
def get_path(filename):
    return os.path.normpath(os.path.join(get_resources_directory(), filename))
def _spawn_process(args):
    try:
        exe = sys.executable
        if getattr(sys, 'frozen', False):
            cmd = [exe] + args
        else:
            script_path = os.path.abspath(__file__)
            cmd = [exe, script_path] + args
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        if 'VIRTUAL_ENV' in os.environ:
            env['VIRTUAL_ENV'] = os.environ['VIRTUAL_ENV']
            venv_scripts = os.path.join(os.environ['VIRTUAL_ENV'], 'Scripts')
            if venv_scripts not in env['PATH']:
                env['PATH'] = venv_scripts + os.pathsep + env['PATH']
        resources_dir = os.path.join(os.getcwd(), 'resources')
        if resources_dir not in env.get('PYTHONPATH', ''):
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = resources_dir + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = resources_dir
        proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE, text=False, env=env, cwd=os.path.dirname(os.path.abspath(__file__)))
        return proc
    except Exception as e:
        print(f'Failed to spawn loader process: {e}')
        print(f'Exception type: {type(e).__name__}')
        import traceback
        traceback.print_exc()
        return None
if '--spawn-loader' in sys.argv:
    class STDINListener(QThread):
        message_received = Signal(dict)
        def run(self):
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                try:
                    data = json.loads(line)
                    self.message_received.emit(data)
                except Exception:
                    pass
    class OverlayController(QWidget):
        def __init__(self, start_time, phrases, parent_geom=None):
            super().__init__()
            self.phrases = phrases
            self.parent_geom = parent_geom
            self._target_pos = None
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMinimumSize(850, 500)
            self._drag_pos = QPoint()
            self.is_dark = self._load_theme_pref()
            self._load_theme()
            self.main_layout = QVBoxLayout(self)
            self.container = QFrame()
            self.container.setObjectName('mainContainer')
            self.main_layout.addWidget(self.container)
            self.inner = QVBoxLayout(self.container)
            self.inner.setContentsMargins(30, 10, 30, 30)
            self.setup_loader_ui(start_time)
            self.listener = STDINListener()
            self.listener.message_received.connect(self.handle_message)
            self.listener.start()
            self.center_on_cursor_screen()
        def center_on_cursor_screen(self):
            win_width, win_height = (850, 500)
            if self.parent_geom:
                px, py, pw, ph = self.parent_geom
                center_x = px + pw // 2 - win_width // 2
                center_y = py + ph // 2 - win_height // 2
                self._target_pos = (center_x, center_y)
                self.setGeometry(center_x, center_y, win_width, win_height)
            else:
                cursor_pos = QCursor.pos()
                screen = QApplication.screenAt(cursor_pos)
                if screen is None:
                    screen = QApplication.primaryScreen()
                screen_geometry = screen.availableGeometry()
                center_x = screen_geometry.x() + (screen_geometry.width() - win_width) // 2
                center_y = screen_geometry.y() + (screen_geometry.height() - win_height) // 2
                self._target_pos = (center_x, center_y)
                self.setGeometry(center_x, center_y, win_width, win_height)
        def showEvent(self, event):
            super().showEvent(event)
            if not event.spontaneous():
                if self._target_pos:
                    self.move(*self._target_pos)
                self.activateWindow()
                self.raise_()
        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        def _load_theme_pref(self):
            return True
        def _load_theme(self):
            base_path = get_src_directory()
            theme_file = 'darkmode.qss'
            theme_path = os.path.join(base_path, 'data', 'gui', theme_file)
            if os.path.exists(theme_path):
                try:
                    with open(theme_path, 'r', encoding='utf-8') as f:
                        qss_content = f.read()
                        self.setStyleSheet(qss_content)
                except Exception as e:
                    print(f'Failed to load theme {theme_file}: {e}')
                    self._apply_fallback_styles()
            else:
                self._apply_fallback_styles()
        def _apply_fallback_styles(self):
            bg_gradient = 'qlineargradient(spread:pad,x1:0.0,y1:0.0,x2:1.0,y2:1.0,stop:0 #07080a,stop:0.5 #08101a,stop:1 #05060a)'
            glass_bg = 'rgba(18,20,24,0.95)'
            glass_border = 'rgba(255,255,255,0.08)'
            txt_color = '#dfeefc'
            accent_color = '#7DD3FC'
            self.setStyleSheet(f"QWidget {{ background: {bg_gradient}; color: {txt_color}; font-family: 'Segoe UI',Roboto,Arial; }}")
            self.container.setStyleSheet(f'#mainContainer {{ background: {glass_bg}; border-radius: 10px; border: 1px solid {glass_border}; }}')
        def clear_layout(self):
            while self.inner.count():
                child = self.inner.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self._clear_sub_layout(child.layout())
        def _clear_sub_layout(self, layout):
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self._clear_sub_layout(child.layout())
        def setup_loader_ui(self, start_time):
            self.start_ts = start_time
            top_bar = QHBoxLayout()
            top_bar.addStretch()
            self.close_btn = QPushButton('✕')
            self.close_btn.setFixedSize(40, 40)
            self.close_btn.clicked.connect(self.safe_exit)
            self.close_btn.setObjectName('closeBtn')
            top_bar.addWidget(self.close_btn)
            self.inner.addLayout(top_bar)
            self.inner.addStretch()
            self.label = QLabel(random.choice(self.phrases))
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setWordWrap(True)
            self.label.setObjectName('loadingLabel')
            self.opacity_effect = QGraphicsOpacityEffect(self.label)
            self.label.setGraphicsEffect(self.opacity_effect)
            self.inner.addWidget(self.label)
            self.icon_label = QLabel()
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setObjectName('iconLabel')
            p = get_path('Xenolord.webp')
            if os.path.exists(p):
                pix = QPixmap(p)
                self.icon_label.setPixmap(pix.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.inner.addWidget(self.icon_label)
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFixedWidth(200)
            self.progress_bar.setFixedHeight(8)
            self.progress_bar.setObjectName('loadingProgress')
            progress_layout = QHBoxLayout()
            progress_layout.addStretch()
            progress_layout.addWidget(self.progress_bar)
            progress_layout.addStretch()
            self.inner.addLayout(progress_layout)
            self.timer_label = QLabel('00:00.00')
            self.timer_label.setAlignment(Qt.AlignCenter)
            self.timer_label.setObjectName('timerLabel')
            self.inner.addWidget(self.timer_label)
            self.inner.addStretch()
            self.tick_timer = QTimer(self)
            self.tick_timer.timeout.connect(self.update_loader)
            self.tick_timer.start(100)
            self.phrase_timer = QTimer(self)
            self.phrase_timer.timeout.connect(self.cycle_phrase)
            self.phrase_timer.start(3000)
        def cycle_phrase(self):
            self.anim = QPropertyAnimation(self.opacity_effect, b'opacity')
            self.anim.setDuration(400)
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.0)
            self.anim.finished.connect(self._change_and_fade_in)
            self.anim.start()
        def _change_and_fade_in(self):
            self.label.setText(random.choice(self.phrases))
            self.anim = QPropertyAnimation(self.opacity_effect, b'opacity')
            self.anim.setDuration(400)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()
        def update_loader(self):
            elapsed = time.time() - self.start_ts
            self.timer_label.setText(f'{int(elapsed // 60):02d}:{int(elapsed % 60):02d}.{int(elapsed * 100 % 100):02d}')
        def handle_message(self, data):
            cmd = data.get('cmd')
            if cmd == 'error':
                self.switch_to_error(data)
            elif cmd == 'exit':
                self.safe_exit()
        def safe_exit(self):
            QApplication.quit()
            os._exit(0)
        def copy_to_clipboard(self, text, btn):
            try:
                subprocess.run(['clip.exe'], input=text.encode('utf-16'), check=True)
                old_txt = btn.text()
                btn.setText('COPIED!')
                QTimer.singleShot(2000, lambda: btn.setText(old_txt))
            except:
                try:
                    clipboard = QApplication.clipboard()
                    clipboard.setText(text)
                    old_txt = btn.text()
                    btn.setText('COPIED!')
                    QTimer.singleShot(2000, lambda: btn.setText(old_txt))
                except:
                    pass
        def switch_to_error(self, data):
            if hasattr(self, 'tick_timer'):
                self.tick_timer.stop()
            if hasattr(self, 'phrase_timer'):
                self.phrase_timer.stop()
            self.clear_layout()
            self.repaint()
            glass_bg = 'rgba(18,20,24,0.95)'
            glass_border = 'rgba(255,59,48,0.3)'
            txt_color = '#dfeefc'
            accent_color = '#FF3B30'
            btn_bg = 'rgba(125,211,252,0.08)'
            btn_border = 'rgba(125,211,252,0.15)'
            btn_hover_bg = 'rgba(125,211,252,0.15)'
            self.container.setStyleSheet(f'#mainContainer {{ background: {glass_bg}; border-radius: 10px; border: 2px solid {glass_border}; }}')
            head = QHBoxLayout()
            img_p = get_path('lamball_error.webp')
            def mk_ico():
                l = QLabel()
                l.setStyleSheet('border:none;background:transparent;')
                if os.path.exists(img_p):
                    pix = QPixmap(img_p)
                    l.setPixmap(pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return l
            t_lbl = QLabel(data.get('title', 'ERROR'))
            t_lbl.setStyleSheet(f"color:{accent_color};font-weight:900;font-size:24px;border:none;background:transparent;font-family:'Segoe UI';")
            head.addStretch()
            head.addWidget(mk_ico())
            head.addSpacing(15)
            head.addWidget(t_lbl)
            head.addSpacing(15)
            head.addWidget(mk_ico())
            head.addStretch()
            self.inner.addLayout(head)
            txt_edit = QTextEdit()
            txt_edit.setReadOnly(True)
            txt_edit.setPlainText(data.get('text', ''))
            txt_edit.setStyleSheet(f"background: {glass_bg}; color: {txt_color}; font-family: 'Consolas'; font-size: 13px; padding: 15px; border: 1px solid {glass_border}; border-radius: 6px;")
            self.inner.addWidget(txt_edit)
            btns = QHBoxLayout()
            btn_style = f"QPushButton {{ background: {btn_bg}; color: {accent_color}; border: 1px solid {btn_border}; border-radius: 8px; padding: 10px 16px; font-weight: bold; min-width: 120px; font-size: 13px; font-family: 'Segoe UI'; }} QPushButton:hover {{ background: {btn_hover_bg}; border-color: {glass_border}; }}"
            c_btn = QPushButton(data.get('copy', 'COPY'))
            c_btn.setStyleSheet(btn_style)
            c_btn.clicked.connect(lambda: self.copy_to_clipboard(data.get('text', ''), c_btn))
            cl_btn = QPushButton(data.get('close', 'CLOSE'))
            cl_btn.setStyleSheet(btn_style)
            cl_btn.clicked.connect(self.safe_exit)
            btns.addStretch()
            btns.addWidget(c_btn)
            btns.addSpacing(20)
            btns.addWidget(cl_btn)
            btns.addStretch()
            self.inner.addLayout(btns)
    app = QApplication(sys.argv)
    idx = sys.argv.index('--spawn-loader')
    start_ts = float(sys.argv[idx + 1])
    phrases = json.loads(sys.argv[idx + 2])
    parent_geom = None
    if idx + 3 < len(sys.argv) and sys.argv[idx + 3] == '--parent-geom' and (idx + 7 < len(sys.argv)):
        try:
            parent_geom = (int(sys.argv[idx + 4]), int(sys.argv[idx + 5]), int(sys.argv[idx + 6]), int(sys.argv[idx + 7]))
        except (ValueError, IndexError):
            pass
    win = OverlayController(start_ts, phrases, parent_geom)
    win.show()
    sys.exit(app.exec())
def run_with_loading(callback, func, *args, parent=None, **kwargs):
    global _result_data
    if _result_data.get('status') == 'running':
        return
    _result_data.update({'status': 'running', 'data': None})
    start_ts = time.time()
    try:
        phrases = [t(f'loading.phrase.{i}') for i in range(1, 21)]
    except:
        phrases = ['LOADING...']
    if parent is None:
        for widget in QApplication.topLevelWidgets():
            if widget.isVisible() and widget.isWindow() and widget.windowTitle() and (not isinstance(widget, QDialog)):
                parent = widget
                break
    loader_args = ['--spawn-loader', str(start_ts), json.dumps(phrases)]
    if parent:
        geom = parent.geometry()
        if geom.width() > 0 and geom.height() > 0:
            loader_args.extend(['--parent-geom', str(geom.x()), str(geom.y()), str(geom.width()), str(geom.height())])
    loader_proc = _spawn_process(loader_args)
    if loader_proc is None:
        def task():
            try:
                _result_data['data'] = func(*args, **kwargs)
            except:
                _result_data['data'] = traceback.format_exc()
            _result_data['status'] = 'finished'
        threading.Thread(target=task, daemon=True).start()
        def monitor():
            if _result_data['status'] != 'finished':
                QTimer.singleShot(100, monitor)
                return
            res = _result_data['data']
            _result_data['status'] = 'idle'
            if isinstance(res, str) and 'Traceback' in res:
                try:
                    trans = {'title': t('error.overlay.title'), 'close': t('error.overlay.close'), 'copy': t('error.overlay.copy')}
                except:
                    trans = {'title': 'AN ERROR OCCURRED', 'close': 'CLOSE', 'copy': 'COPY'}
                dialog = ErrorDialog(res, parent=parent)
                dialog.exec()
            elif callback:
                callback(res)
        QTimer.singleShot(100, monitor)
        return
    def cleanup():
        if loader_proc and loader_proc.poll() is None:
            try:
                loader_proc.stdin.write(b'{"cmd":"exit"}\n')
                loader_proc.stdin.flush()
                loader_proc.wait(timeout=0.5)
            except:
                try:
                    loader_proc.kill()
                except:
                    pass
    def task():
        try:
            _result_data['data'] = func(*args, **kwargs)
        except:
            _result_data['data'] = traceback.format_exc()
        _result_data['status'] = 'finished'
    threading.Thread(target=task, daemon=True).start()
    def monitor():
        if _result_data['status'] != 'finished':
            QTimer.singleShot(100, monitor)
            return
        res = _result_data['data']
        _result_data['status'] = 'idle'
        if isinstance(res, str) and 'Traceback' in res:
            try:
                trans = {'title': t('error.overlay.title'), 'close': t('error.overlay.close'), 'copy': t('error.overlay.copy')}
            except:
                trans = {'title': 'AN ERROR OCCURRED', 'close': 'CLOSE', 'copy': 'COPY'}
            if loader_proc and loader_proc.poll() is None:
                try:
                    loader_proc.stdin.write((json.dumps({'cmd': 'error', 'text': res, **trans}) + '\n').encode())
                    loader_proc.stdin.flush()
                except:
                    cleanup()
            else:
                dialog = ErrorDialog(res, parent=parent)
                dialog.exec()
        else:
            cleanup()
            if callback:
                callback(res)
    QTimer.singleShot(100, monitor)
class ErrorDialog(QDialog):
    def __init__(self, error_text, parent=None):
        super().__init__(parent)
        self.error_text = error_text
        self.parent_window = parent
        self._target_pos = None
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(850, 500)
        self.adjustSize()
        self.center_on_cursor_screen()
        self.is_dark = self._load_theme_pref()
        self._load_theme()
        self.setup_error_ui()
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            if self._target_pos:
                self.move(*self._target_pos)
            self.activateWindow()
            self.raise_()
    def center_on_cursor_screen(self):
        win_width, win_height = (850, 500)
        if self.parent_window:
            geom = self.parent_window.geometry()
            center_x = geom.x() + geom.width() // 2 - win_width // 2
            center_y = geom.y() + geom.height() // 2 - win_height // 2
            self._target_pos = (center_x, center_y)
            self.setGeometry(center_x, center_y, win_width, win_height)
        else:
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            if screen is None:
                screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            center_x = screen_geometry.x() + (screen_geometry.width() - win_width) // 2
            center_y = screen_geometry.y() + (screen_geometry.height() - win_height) // 2
            self._target_pos = (center_x, center_y)
            self.setGeometry(center_x, center_y, win_width, win_height)
    def _load_theme_pref(self):
        return True
    def _load_theme(self):
        base_path = get_src_directory()
        theme_file = 'darkmode.qss'
        theme_path = os.path.join(base_path, 'data', 'gui', theme_file)
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                    self.setStyleSheet(qss_content)
            except Exception as e:
                print(f'Failed to load theme {theme_file}: {e}')
                self._apply_fallback_styles()
        else:
            self._apply_fallback_styles()
    def _apply_fallback_styles(self):
        bg_gradient = 'qlineargradient(spread:pad,x1:0.0,y1:0.0,x2:1.0,y2:1.0,stop:0 #07080a,stop:0.5 #08101a,stop:1 #05060a)'
        glass_bg = 'rgba(18,20,24,0.95)'
        glass_border = 'rgba(255,59,48,0.3)'
        txt_color = '#dfeefc'
        accent_color = '#FF3B30'
        btn_bg = 'rgba(125,211,252,0.08)'
        btn_border = 'rgba(125,211,252,0.15)'
        btn_hover_bg = 'rgba(125,211,252,0.15)'
        self.setStyleSheet(f"QWidget {{ background: {bg_gradient}; color: {txt_color}; font-family: 'Segoe UI',Roboto,Arial; }}")
    def setup_error_ui(self):
        self.container = QFrame()
        self.container.setObjectName('mainContainer')
        glass_bg = 'rgba(18,20,24,0.95)'
        glass_border = 'rgba(255,59,48,0.3)'
        txt_color = '#dfeefc'
        accent_color = '#FF3B30'
        btn_bg = 'rgba(125,211,252,0.08)'
        btn_border = 'rgba(125,211,252,0.15)'
        btn_hover_bg = 'rgba(125,211,252,0.15)'
        self.container.setStyleSheet(f'#mainContainer {{ background: {glass_bg}; border-radius: 10px; border: 2px solid {glass_border}; }}')
        layout = QVBoxLayout(self)
        layout.addWidget(self.container)
        self.inner = QVBoxLayout(self.container)
        self.inner.setContentsMargins(30, 10, 30, 30)
        head = QHBoxLayout()
        img_p = get_path('lamball_error.webp')
        def mk_ico():
            l = QLabel()
            l.setStyleSheet('border:none;background:transparent;')
            if os.path.exists(img_p):
                pix = QPixmap(img_p)
                l.setPixmap(pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            return l
        try:
            trans = {'title': t('error.overlay.title'), 'close': t('error.overlay.close'), 'copy': t('error.overlay.copy')}
        except:
            trans = {'title': 'AN ERROR OCCURRED', 'close': 'CLOSE', 'copy': 'COPY'}
        t_lbl = QLabel(trans['title'])
        t_lbl.setStyleSheet(f"color:{accent_color};font-weight:900;font-size:24px;border:none;background:transparent;font-family:'Segoe UI';")
        head.addStretch()
        head.addWidget(mk_ico())
        head.addSpacing(15)
        head.addWidget(t_lbl)
        head.addSpacing(15)
        head.addWidget(mk_ico())
        head.addStretch()
        self.inner.addLayout(head)
        txt_edit = QTextEdit()
        txt_edit.setReadOnly(True)
        txt_edit.setPlainText(self.error_text)
        txt_edit.setStyleSheet(f"background: {glass_bg}; color: {txt_color}; font-family: 'Consolas'; font-size: 13px; padding: 15px; border: 1px solid {glass_border}; border-radius: 6px;")
        self.inner.addWidget(txt_edit)
        btns = QHBoxLayout()
        btn_style = f"QPushButton {{ background: {btn_bg}; color: {accent_color}; border: 1px solid {btn_border}; border-radius: 8px; padding: 10px 16px; font-weight: bold; min-width: 120px; font-size: 13px; font-family: 'Segoe UI'; }} QPushButton:hover {{ background: {btn_hover_bg}; border-color: {glass_border}; }}"
        c_btn = QPushButton(trans['copy'])
        c_btn.setStyleSheet(btn_style)
        c_btn.clicked.connect(lambda: self.copy_to_clipboard(self.error_text, c_btn))
        cl_btn = QPushButton(trans['close'])
        cl_btn.setStyleSheet(btn_style)
        cl_btn.clicked.connect(self.close_app)
        btns.addStretch()
        btns.addWidget(c_btn)
        btns.addSpacing(20)
        btns.addWidget(cl_btn)
        btns.addStretch()
        self.inner.addLayout(btns)
    def close_app(self):
        self.accept()
        QApplication.quit()
        os._exit(0)
    def copy_to_clipboard(self, text, btn):
        try:
            subprocess.run(['clip.exe'], input=text.encode('utf-16'), check=True)
            old_txt = btn.text()
            btn.setText('COPIED!')
            QTimer.singleShot(2000, lambda: btn.setText(old_txt))
        except:
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                old_txt = btn.text()
                btn.setText('COPIED!')
                QTimer.singleShot(2000, lambda: btn.setText(old_txt))
            except:
                pass
def show_error_screen(error_text):
    dialog = ErrorDialog(error_text)
    dialog.exec()
def _center_message_box_on_parent(msg_box):
    parent = msg_box.parent()
    effective_parent = _get_effective_parent(parent)
    if effective_parent:
        parent_rect = effective_parent.geometry()
        size = msg_box.sizeHint()
        if not size.isValid():
            msg_box.adjustSize()
            size = msg_box.size()
        dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
        dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
        screen = QApplication.screenAt(parent_rect.center())
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        dialog_x = max(screen_geometry.x(), min(dialog_x, screen_geometry.right() - size.width()))
        dialog_y = max(screen_geometry.y(), min(dialog_y, screen_geometry.bottom() - size.height()))
        msg_box.move(dialog_x, dialog_y)
    else:
        parent = msg_box.parent()
        if parent and hasattr(parent, 'geometry'):
            parent_rect = parent.geometry()
            size = msg_box.sizeHint()
            if not size.isValid():
                msg_box.adjustSize()
                size = msg_box.size()
            dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
            dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
            msg_box.move(dialog_x, dialog_y)
def _get_effective_parent(parent):
    current = parent
    while current is not None:
        if hasattr(current, 'isWindow') and current.isWindow() and current.isVisible():
            if hasattr(current, 'windowTitle') and current.windowTitle():
                return current
        current = current.parent()
    for widget in QApplication.topLevelWidgets():
        if widget.isVisible() and widget.isWindow() and hasattr(widget, 'windowTitle') and widget.windowTitle() and (not isinstance(widget, QDialog)) and hasattr(widget, 'geometry'):
            return widget
    active = QApplication.activeWindow()
    if active and hasattr(active, 'geometry') and active.isVisible():
        return active
    return None
_MSG_BOX_DARK_STYLESHEET = '\n    QMessageBox {\n        background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                    stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a);\n        color: #dfeefc;\n    }\n    QMessageBox QLabel {\n        color: #dfeefc;\n    }\n    QPushButton {\n        background-color: #3a3a3a;\n        color: #dfeefc;\n        border: 1px solid #555555;\n        border-radius: 4px;\n        padding: 6px 16px;\n        min-width: 70px;\n    }\n    QPushButton:hover {\n        background-color: #4a4a4a;\n    }\n'
def _load_theme_to_msg_box(msg_box):
    try:
        msg_box.setStyleSheet(_MSG_BOX_DARK_STYLESHEET)
    except Exception as e:
        print(f'Failed to load theme for message box: {e}')
def show_information(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setIcon(QMessageBox.Information)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    dialog.exec()
def show_warning(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setIcon(QMessageBox.Warning)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    dialog.exec()
def show_critical(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setIcon(QMessageBox.Critical)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    dialog.exec()
def show_question(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setIcon(QMessageBox.Question)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    return dialog.exec() == QMessageBox.Yes