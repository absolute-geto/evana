# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# ============================================================
#  البيانات المضمّنة (assets كامل — خطوط، أيقونات، ffmpeg)
# ============================================================
datas = [
    ('assets', 'assets'),
]

# ============================================================
#  المكتبات المخفية
# ============================================================
hiddenimports = [
    'yt_dlp',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',
]
hiddenimports += collect_submodules('yt_dlp')

# ============================================================
#  استثناءات (لتقليل الحجم)
# ============================================================
excludes = [
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
    'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtLocation',
    'PySide6.QtNfc', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtPositioning', 'PySide6.QtQml', 'PySide6.QtQuick',
    'PySide6.QtQuick3D', 'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialPort', 'PySide6.QtSpatialAudio', 'PySide6.QtSql',
    'PySide6.QtStateMachine', 'PySide6.QtTest', 'PySide6.QtTextToSpeech',
    'PySide6.QtWebChannel', 'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebSockets',
    'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas',
    'PIL', 'notebook', 'IPython',
]

# ============================================================
#  بناء
# ============================================================
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Evana',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/evana_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Evana',
)