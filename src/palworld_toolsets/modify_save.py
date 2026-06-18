from import_libs import *
from PySide6.QtWidgets import QSizePolicy, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QMainWindow, QWidget, QComboBox, QLineEdit, QFileDialog, QApplication, QFrame, QProgressBar, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtCore import Qt, QTimer
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio import constants
from resource_resolver import resource_path, get_base_dir, get_resources_dir
import ssl
def _get_user_ca_path():
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))
    return os.path.join(base, APP_NAME, 'cert', 'cacert.pem')
def _update_ca_bundle():
    url = 'https://curl.se/ca/cacert.pem'
    dest = _get_user_ca_path()
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        print(f'[SSL] Downloading CA bundle from {url}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r, open(dest, 'wb') as f:
            f.write(r.read())
        print(f'[SSL] CA bundle saved: {dest}')
        return dest
    except Exception as e:
        print(f'[SSL] CA bundle download failed: {e}')
        return None
def _unverified_context():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
def _try_ca(cafile, label):
    if cafile and os.path.exists(cafile):
        try:
            ctx = ssl.create_default_context(cafile=cafile)
            print(f'[SSL] Using {label} CA: {cafile}')
            return ctx
        except Exception as e:
            print(f'[SSL] {label} CA failed ({e})')
    else:
        print(f'[SSL] {label} CA not found: {cafile}')
    return None
def _get_ssl_context():
    bundled = resource_path(get_base_dir(), 'cert', 'cacert.pem')
    user_ca = _get_user_ca_path()
    ctx = _try_ca(bundled, 'bundled')
    if ctx:
        return ctx
    ctx = _try_ca(user_ca, 'user-cached')
    if ctx:
        return ctx
    print('[SSL] No valid CA found, downloading fresh bundle...')
    downloaded = _update_ca_bundle()
    ctx = _try_ca(downloaded, 'freshly-downloaded')
    if ctx:
        return ctx
    print('[SSL] Using unverified context')
    return _unverified_context()
def _format_bytes(num: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if num < 1024 or unit == 'GB':
            return f'{num:.1f}{unit}' if unit != 'B' else f'{num}{unit}'
        num /= 1024
def download_from_github(repo_owner, repo_name, version, download_path, progress_callback=None):
    file_url = get_release_assets(repo_owner, repo_name, version)
    if not file_url:
        print('Error: No valid asset found.')
        return None
    try:
        file_name = file_url.split('/')[-1]
        file_path = os.path.join(download_path, file_name)
        req = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
        context = _get_ssl_context()
        with urllib.request.urlopen(req, context=context, timeout=60) as response, open(file_path, 'wb') as f:
            total = int(response.getheader('Content-Length', '0') or 0)
            downloaded = 0
            block = 1024 * 128
            last_pct = -1
            while True:
                chunk = response.read(block)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded * 100 / total)
                    if pct != last_pct and pct % 5 == 0:
                        if progress_callback:
                            progress_callback(pct)
                        else:
                            print(f'Downloading... {pct}%({_format_bytes(downloaded)}/{_format_bytes(total)})')
                            sys.stdout.flush()
                        last_pct = pct
        print(f"File '{file_name}' downloaded successfully to '{download_path}'")
        return file_path
    except Exception as e:
        print(f'Error downloading file: {e}')
        return None
def get_release_assets(repo_owner, repo_name, version):
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{version}'
    try:
        context = _get_ssl_context()
        with urllib.request.urlopen(api_url, context=context) as response:
            release_data = json.load(response)
            for asset in release_data.get('assets', []):
                name = asset['name'].lower()
                if 'windows-standalone' in name and name.endswith('.zip'):
                    return asset['browser_download_url']
    except Exception as e:
        print(f'Error fetching release info: {e}')
    return None
def get_release_asset_url_filtered(repo_owner, repo_name, version, keywords, extensions):
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{version}'
    try:
        context = _get_ssl_context()
        with urllib.request.urlopen(api_url, context=context) as response:
            release_data = json.load(response)
            for asset in release_data.get('assets', []):
                name = asset.get('name', '').lower()
                if any((k in name for k in keywords)) and any((name.endswith(ext) for ext in extensions)):
                    return asset.get('browser_download_url')
    except Exception as e:
        print(f'Error fetching filtered release info: {e}')
    return None
def extract_zip(directory, partial_name, extract_to):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.zip') and partial_name in file:
                zpath = os.path.join(root, file)
                try:
                    with zipfile.ZipFile(zpath, 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                    print(f'Extracted {file} to {extract_to}')
                except Exception as e:
                    print(f'Error extracting {file}: {e}')
def extract_exact_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f'Extracted {os.path.basename(zip_path)} to {extract_to}')
        return True
    except Exception as e:
        print(f'Error extracting {zip_path}: {e}')
        return False
def get_latest_version(repo_owner, repo_name):
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest'
    try:
        context = _get_ssl_context()
        with urllib.request.urlopen(api_url, context=context) as response:
            latest_release = json.load(response)
            return latest_release['tag_name']
    except Exception as e:
        print(f'Error fetching release info: {e}')
        return None
def find_exe(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower() == 'psp.exe':
                return os.path.join(root, f)
    return None
def find_any_exe(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.exe'):
                return os.path.join(root, f)
    return None
def open_exe_with_cwd(exe_path):
    subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
def _launch_save_pal():
    if os.name != 'nt':
        print('Palworld Save Pal is only available on Windows.')
        return
    repo_owner = 'oMaN-Rod'
    repo_name = 'palworld-save-pal'
    version = get_latest_version(repo_owner, repo_name)
    if not version:
        print('Unable to fetch latest release version.')
        return
    exe_path = find_exe('psp_windows')
    if exe_path:
        print('Opening Palworld Save Pal...')
        open_exe_with_cwd(exe_path)
        return
    print('Downloading Palworld Save Pal...')
    zip_file = download_from_github(repo_owner, repo_name, version, '.')
    if zip_file:
        extract_zip('.', 'windows-standalone', 'psp_windows')
        try:
            os.remove(zip_file)
        except FileNotFoundError:
            pass
        exe_path = find_exe('psp_windows')
        if exe_path:
            print('Opening Palworld Save Pal...')
            open_exe_with_cwd(exe_path)
        else:
            print('Extraction succeeded but could not find psp.exe.')
    else:
        print('Failed to download Palworld Save Pal...')
def _download_to(path_dir, file_url, progress_callback=None):
    try:
        os.makedirs(path_dir, exist_ok=True)
        file_name = file_url.split('/')[-1]
        file_path = os.path.join(path_dir, file_name)
        req = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
        context = _get_ssl_context()
        with urllib.request.urlopen(req, context=context, timeout=60) as response, open(file_path, 'wb') as f:
            total = int(response.getheader('Content-Length', '0') or 0)
            downloaded = 0
            block = 1024 * 128
            last_pct = -1
            while True:
                chunk = response.read(block)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded * 100 / total)
                    if pct != last_pct and pct % 5 == 0:
                        if progress_callback:
                            progress_callback(pct)
                        else:
                            print(f'Downloading... {pct}%')
                            sys.stdout.flush()
                        last_pct = pct
        print(f"File '{file_name}' downloaded successfully to '{path_dir}'")
        return file_path
    except Exception as e:
        print(f'Error downloading file: {e}')
        return None
def _launch_pal_editor():
    if os.name != 'nt':
        print('Palworld Pal Editor is only available on Windows.')
        return
    repo_owner = 'KrisCris'
    repo_name = 'Palworld-Pal-Editor'
    version = get_latest_version(repo_owner, repo_name)
    if not version:
        print('Unable to fetch latest release version.')
        open_file_with_default_app('https://github.com/KrisCris/Palworld-Pal-Editor')
        return
    target_dir = 'ppe_windows'
    exe_path = find_any_exe(target_dir)
    if exe_path:
        print('Opening Palworld Pal Editor...')
        open_exe_with_cwd(exe_path)
        return
    print('Downloading Palworld Pal Editor...')
    file_url = get_release_asset_url_filtered(repo_owner, repo_name, version, keywords=['win', 'windows'], extensions=['.zip', '.exe'])
    if not file_url:
        print('No suitable asset found for Pal Editor.')
        open_file_with_default_app('https://github.com/KrisCris/Palworld-Pal-Editor')
        return
    downloaded = _download_to('.', '' + file_url)
    if not downloaded:
        print('Failed to download Pal Editor.')
        return
    if downloaded.lower().endswith('.zip'):
        os.makedirs(target_dir, exist_ok=True)
        if extract_exact_zip(downloaded, target_dir):
            try:
                os.remove(downloaded)
            except FileNotFoundError:
                pass
            exe_path = find_any_exe(target_dir)
            if exe_path:
                print('Opening Palworld Pal Editor...')
                open_exe_with_cwd(exe_path)
            else:
                print('Extraction succeeded but could not find an exe.')
        else:
            print('Extraction failed for Pal Editor archive.')
    elif downloaded.lower().endswith('.exe'):
        os.makedirs(target_dir, exist_ok=True)
        try:
            dest = os.path.join(target_dir, os.path.basename(downloaded))
            if os.path.abspath(downloaded) != os.path.abspath(dest):
                try:
                    shutil.move(downloaded, dest)
                except Exception:
                    shutil.copy2(downloaded, dest)
                    os.remove(downloaded)
            open_exe_with_cwd(dest)
        except Exception as e:
            print(f'Error preparing Pal Editor executable: {e}')
    else:
        print('Downloaded file is not a supported type.')
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    size = win.sizeHint()
    if not size.isValid():
        win.adjustSize()
        size = win.size()
    win.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
def _build_selector_window():
    win = QDialog()
    win.setWindowTitle(t('modify.dialog.title'))
    win.setModal(True)
    win.setFixedSize(520, 250)
    try:
        ico_path = resource_path(get_base_dir(), 'icon.ico')
        if os.path.exists(ico_path):
            win.setWindowIcon(QIcon(ico_path))
    except Exception as e:
        print(f'Error setting icon: {e}')
    ThemeManager.load_styles(win)
    main = QVBoxLayout(win)
    main.setContentsMargins(12, 12, 12, 12)
    glass = QFrame()
    glass.setObjectName('glass')
    glass_layout = QVBoxLayout(glass)
    glass_layout.setSpacing(10)
    label1 = QLabel(t('modify.dialog.choose_editor'))
    label1.setFont(QFont(constants.FONT_FAMILY, 12, QFont.Bold))
    label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
    glass_layout.addWidget(label1)
    label2 = QLabel(t('modify.dialog.note_backup'))
    label2.setFont(QFont(constants.FONT_FAMILY, 10))
    label2.setStyleSheet('color: #ff5555; font-weight: bold; font-style: italic;')
    label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
    glass_layout.addWidget(label2)
    glass_layout.addSpacing(6)
    button_layout = QHBoxLayout()
    savepal_btn = QPushButton(t('modify.dialog.option.savepal'))
    paleditor_btn = QPushButton(t('modify.dialog.option.paleditor'))
    savepal_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    paleditor_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    def on_savepal():
        if os.name != 'nt':
            QMessageBox.information(win, 'Platform Error', 'Palworld Save Pal is only available on Windows.')
            return
        exe_path = find_exe('psp_windows')
        if exe_path:
            print('Opening Palworld Save Pal...')
            open_exe_with_cwd(exe_path)
            win.accept()
            return
        progress_bar.setVisible(True)
        win.setFixedSize(520, 280)
        QApplication.processEvents()
        def progress_callback(pct):
            progress_bar.setValue(pct)
        repo_owner = 'oMaN-Rod'
        repo_name = 'palworld-save-pal'
        version = get_latest_version(repo_owner, repo_name)
        if version:
            zip_file = download_from_github(repo_owner, repo_name, version, '.', progress_callback)
            if zip_file:
                extract_zip('.', 'windows-standalone', 'psp_windows')
                try:
                    os.remove(zip_file)
                except FileNotFoundError:
                    pass
                exe_path = find_exe('psp_windows')
                if exe_path:
                    print('Opening Palworld Save Pal...')
                    open_exe_with_cwd(exe_path)
                else:
                    print('Extraction succeeded but could not find psp.exe.')
            else:
                print('Failed to download Palworld Save Pal...')
        else:
            print('Unable to fetch latest release version.')
        progress_bar.setVisible(False)
        win.setFixedSize(520, 250)
        win.accept()
    def on_paleditor():
        if os.name != 'nt':
            QMessageBox.information(win, 'Platform Error', 'Palworld Pal Editor is only available on Windows.')
            return
        exe_path = find_any_exe('ppe_windows')
        if exe_path:
            print('Opening Palworld Pal Editor...')
            open_exe_with_cwd(exe_path)
            win.accept()
            return
        progress_bar.setVisible(True)
        win.setFixedSize(520, 280)
        QApplication.processEvents()
        def progress_callback(pct):
            progress_bar.setValue(pct)
        repo_owner = 'KrisCris'
        repo_name = 'Palworld-Pal-Editor'
        version = get_latest_version(repo_owner, repo_name)
        if version:
            file_url = get_release_asset_url_filtered(repo_owner, repo_name, version, keywords=['win', 'windows'], extensions=['.zip', '.exe'])
            if file_url:
                downloaded = _download_to('.', '' + file_url, progress_callback)
                if downloaded:
                    target_dir = 'ppe_windows'
                    if downloaded.lower().endswith('.zip'):
                        os.makedirs(target_dir, exist_ok=True)
                        if extract_exact_zip(downloaded, target_dir):
                            try:
                                os.remove(downloaded)
                            except FileNotFoundError:
                                pass
                            exe_path = find_any_exe(target_dir)
                            if exe_path:
                                print('Opening Palworld Pal Editor...')
                                open_exe_with_cwd(exe_path)
                            else:
                                print('Extraction succeeded but could not find an exe.')
                        else:
                            print('Extraction failed for Pal Editor archive.')
                    elif downloaded.lower().endswith('.exe'):
                        os.makedirs(target_dir, exist_ok=True)
                        try:
                            dest = os.path.join(target_dir, os.path.basename(downloaded))
                            if os.path.abspath(downloaded) != os.path.abspath(dest):
                                try:
                                    shutil.move(downloaded, dest)
                                except Exception:
                                    shutil.copy2(downloaded, dest)
                                    os.remove(downloaded)
                            print('Opening Palworld Pal Editor...')
                            open_exe_with_cwd(dest)
                        except Exception as e:
                            print(f'Error preparing Pal Editor executable: {e}')
                    else:
                        print('Downloaded file is not a supported type.')
                else:
                    print('Failed to download Pal Editor.')
            else:
                print('No suitable asset found for Pal Editor.')
                open_file_with_default_app('https://github.com/KrisCris/Palworld-Pal-Editor')
        else:
            print('Unable to fetch latest release version.')
            open_file_with_default_app('https://github.com/KrisCris/Palworld-Pal-Editor')
        progress_bar.setVisible(False)
        win.setFixedSize(520, 250)
        win.accept()
    savepal_btn.clicked.connect(on_savepal)
    paleditor_btn.clicked.connect(on_paleditor)
    button_layout.addWidget(savepal_btn)
    button_layout.addWidget(paleditor_btn)
    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    glass_layout.addWidget(progress_bar)
    glass_layout.addLayout(button_layout)
    main.addWidget(glass)
    QTimer.singleShot(0, lambda: center_window(win))
    return win
class MenuGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            ico_path = resource_path(get_base_dir(), 'icon.ico')
            if os.path.exists(ico_path):
                self.setWindowIcon(QIcon(ico_path))
        except Exception:
            pass
        self.setWindowTitle(t('app.title'))
        self.setFixedWidth(820)
        self.setMinimumHeight(540)
        self.info_labels = []
        self.category_frames = []
        self.tool_buttons = []
        self.lang_combo = None
        self.setup_ui()
        self._add_pal_tools_button()
        ThemeManager.load_styles(self)
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet('QScrollArea { border: none; }')
        main_layout.addWidget(scroll_area)
        container = QWidget()
        scroll_area.setWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(10)
        topbar_layout = QHBoxLayout()
        topbar_layout.setSpacing(8)
        lang_label = QLabel(t('lang.label') + ':')
        self.lang_combo = QComboBox()
        self.lang_combo.setEditable(False)
        self.lang_combo.currentTextChanged.connect(self.on_language_change)
        topbar_layout.addWidget(lang_label)
        topbar_layout.addWidget(self.lang_combo)
        topbar_layout.addStretch()
        container_layout.addLayout(topbar_layout)
        logo_path = resource_path(get_base_dir(), 'PalworldSaveTools.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(420, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                container_layout.addWidget(logo_label)
        info_items = [('app.subtitle', {}, '#6f9', QFont(constants.FONT_FAMILY_MONO, 10)), ('notice.backup', {}, '#f44', QFont(constants.FONT_FAMILY_MONO, 9, QFont.Weight.Bold)), ('notice.patch', {}, '#f44', QFont(constants.FONT_FAMILY_MONO, 9, QFont.Weight.Bold)), ('notice.errors', {}, '#f44', QFont(constants.FONT_FAMILY_MONO, 9, QFont.Weight.Bold))]
        for key, fmt, color, font in info_items:
            label = QLabel(t(key, **fmt))
            label.setFont(font)
            label.setStyleSheet(f'color: {color};')
            container_layout.addWidget(label)
            self.info_labels.append((label, key, fmt))
        separator = QLabel('=' * 86)
        separator.setFont(QFont(constants.FONT_FAMILY_MONO, 11))
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(separator)
        tools_widget = QWidget()
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setSpacing(12)
        left_frame = QFrame()
        left_frame.setObjectName('glass')
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        right_frame = QFrame()
        right_frame.setObjectName('glass')
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)
        tools_layout.addWidget(left_frame)
        tools_layout.addWidget(right_frame)
        container_layout.addWidget(tools_widget)
        self.category_frames = [left_frame, right_frame]
    def _add_pal_tools_button(self):
        btn = QPushButton(t('pal.tools.title'))
        btn.clicked.connect(lambda: _build_selector_window().exec())
        if self.category_frames and hasattr(self.category_frames[0], 'layout'):
            layout = self.category_frames[0].layout()
            if layout:
                layout.addWidget(btn)
        self.tool_buttons.append(btn)
    def on_language_change(self):
        lang = self.lang_combo.currentText()
        set_language(lang)
        load_resources(lang)
        for label, key, fmt in self.info_labels:
            label.setText(t(key, **fmt))
def modify_save():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    dialog = _build_selector_window()
    return dialog
if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    dlg = _build_selector_window()
    dlg.exec()