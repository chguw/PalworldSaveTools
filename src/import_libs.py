import os, ssl
import sys, argparse, collections, copy, ctypes, datetime, gc, json, shutil, glob
import logging, multiprocessing, platform, re, subprocess, threading, pickle, zipfile, string, palworld_coord
import time, traceback, uuid, io, pathlib, urllib.request, tempfile, random, pandas as pd
from multiprocessing import shared_memory
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QDialog, QMessageBox, QFileDialog, QInputDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit, QTreeWidget, QTreeWidgetItem, QProgressBar, QCheckBox, QRadioButton, QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QScrollArea, QFrame, QMenuBar, QMenu, QStatusBar, QSystemTrayIcon, QStyle, QCommonStyle
from PySide6.QtGui import QPixmap, QIcon, QFont, QPainter, QPen, QBrush, QColor, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject, QEvent, QSize, QPoint, QRect
from i18n import init_language, t, set_language, get_language, load_resources
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'palworld_save_tools', 'commands')))
from palworld_save_tools.archive import *
from palworld_save_tools.palsav import *
from palworld_save_tools.paltypes import *
import palworld_save_tools.rawdata.group as palworld_save_group
from palobject import *
from palworld_save_tools.gvas import *
from palworld_save_tools.rawdata import *
from palworld_save_tools.json_tools import *
from palworld_coord import sav_to_map
from common import ICON_PATH
from collections import defaultdict
from common import *
from loading_manager import *
def backup_whole_directory(source_folder, backup_folder):
    import os, sys, shutil, datetime as dt
    def get_timestamp():
        return dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    source_folder = os.path.abspath(source_folder)
    if not os.path.isabs(backup_folder):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else get_base_directory()
        backup_folder = os.path.abspath(os.path.join(base_path, backup_folder))
    else:
        backup_folder = os.path.abspath(backup_folder)
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    print('Now backing up Level.sav,LevelMeta.sav and Players folder...')
    timestamp = get_timestamp()
    backup_path = os.path.join(backup_folder, f'PalworldSave_backup_{timestamp}')
    os.makedirs(backup_path, exist_ok=True)
    level_src = os.path.join(source_folder, 'Level.sav')
    levelmeta_src = os.path.join(source_folder, 'LevelMeta.sav')
    players_src = os.path.join(source_folder, 'Players')
    if os.path.exists(level_src):
        shutil.copy2(level_src, os.path.join(backup_path, 'Level.sav'))
    if os.path.exists(levelmeta_src):
        shutil.copy2(levelmeta_src, os.path.join(backup_path, 'LevelMeta.sav'))
    if os.path.exists(players_src):
        shutil.copytree(players_src, os.path.join(backup_path, 'Players'))
    print(f'Backup created at: {backup_path}')
def center_window(window):
    if hasattr(window, 'move'):
        screen = QApplication.primaryScreen().availableGeometry()
        size = window.size()
        window.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)