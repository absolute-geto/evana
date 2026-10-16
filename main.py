# ============================================================
#                    Evana v1.1.0
#              Media Player • Downloader • Converter • Gallery
#                    with Dark Mode support
# ============================================================

import sys
import subprocess
import os
from pathlib import Path

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer,
    QParallelAnimationGroup, QUrl, QEvent, QSizeF, Signal, QThread,
    QFileInfo, QSettings,
)
from PySide6.QtGui import (
    QIcon, QFontDatabase, QPainter, QBrush, QColor, QPixmap,
    QShortcut, QKeySequence, QImageReader,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager, QNetworkRequest, QNetworkReply,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QGraphicsOpacityEffect, QSlider, QComboBox,
    QListWidget, QListWidgetItem, QFileDialog,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QLineEdit, QProgressBar, QCheckBox, QGridLayout,
    QScrollArea, QSizePolicy, QDialog, QMessageBox,
)

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
    MULTIMEDIA_OK = True
except ImportError:
    MULTIMEDIA_OK = False

try:
    import yt_dlp
    YTDLP_OK = True
except ImportError:
    YTDLP_OK = False


BASE_DIR = Path(__file__).parent
FONTS_DIR = BASE_DIR / "assets" / "fonts"
ICONS_DIR = BASE_DIR / "assets" / "icons"
BIN_DIR = BASE_DIR / "assets" / "bin"


# ============================================================
#              THEME SYSTEM — Palettes & Manager
# ============================================================
LIGHT_PALETTE = {
    # Backgrounds
    "BG_APP":       "#F6F7FB",
    "BG_CARD":      "#FFFFFF",
    "BG_INPUT":     "#F6F7FB",
    "BG_HOVER":     "#F0F2FA",
    "BG_HOVER2":    "#EDF0FF",
    "BG_HOVER3":    "#E1E5F5",
    "BG_SELECTED":  "#E9EDFF",
    "BG_SCROLL":    "#D7DBE5",
    "BG_SCROLL_H":  "#B8BFCF",
    # Text
    "TEXT":         "#20263A",
    "TEXT_SECOND":  "#626B80",
    "TEXT_MUTED":   "#777F92",
    "TEXT_FAINT":   "#9299AA",
    "TEXT_BTN":     "#35405A",
    # Borders
    "BORDER":       "#E5E8F0",
    "BORDER2":      "#E7E9F1",
    "BORDER_HOVER": "#C9D1FF",
    # Accent (blue)
    "ACCENT":       "#4359D6",
    "ACCENT2":      "#6366F1",
    "ACCENT_HOVER": "#3548B8",
    "ACCENT_HOV2":  "#4F52D9",
    "ACCENT_PRESS": "#2A3A99",
    "ACCENT_PRS2":  "#3E42B8",
    # Icons
    "ICON":         "#20263A",
    "ICON_MUTED":   "#626B80",
    # Status
    "SUCCESS":      "#16A34A",
    "SUCCESS_LT":   "#4ADE80",
    "ERROR":        "#DC2626",
    "ERROR_LT":     "#F87171",
    "WARNING":      "#B45309",
    "WARNING_BG":   "#FEF3C7",
}

DARK_PALETTE = {
    # Backgrounds — layered greys
    "BG_APP":       "#0F1115",
    "BG_CARD":      "#181B22",
    "BG_INPUT":     "#1F232B",
    "BG_HOVER":     "#1F232B",
    "BG_HOVER2":    "#242934",
    "BG_HOVER3":    "#2A303C",
    "BG_SELECTED":  "#1E2640",
    "BG_SCROLL":    "#2A303C",
    "BG_SCROLL_H":  "#3A4150",
    # Text
    "TEXT":         "#E5E8F0",
    "TEXT_SECOND":  "#9CA3B0",
    "TEXT_MUTED":   "#7B8394",
    "TEXT_FAINT":   "#5A6070",
    "TEXT_BTN":     "#C7CCD6",
    # Borders
    "BORDER":       "#252A34",
    "BORDER2":      "#252A34",
    "BORDER_HOVER": "#3A4260",
    # Accent (blue — slightly brighter for dark bg)
    "ACCENT":       "#5B72E8",
    "ACCENT2":      "#7C8FFF",
    "ACCENT_HOVER": "#6B82F0",
    "ACCENT_HOV2":  "#8A9CFF",
    "ACCENT_PRESS": "#4A5CC4",
    "ACCENT_PRS2":  "#6A7AE8",
    # Icons
    "ICON":         "#C7CCD6",
    "ICON_MUTED":   "#9CA3B0",
    # Status
    "SUCCESS":      "#4ADE80",
    "SUCCESS_LT":   "#4ADE80",
    "ERROR":        "#F87171",
    "ERROR_LT":     "#F87171",
    "WARNING":      "#FBBF24",
    "WARNING_BG":   "#3A2E10",
}


# Global theme state
CURRENT_THEME = "light"


def _load_theme_setting() -> str:
    """يقرأ الثيم المحفوظ من QSettings"""
    try:
        s = QSettings("Evana", "Evana")
        theme = s.value("theme", "light")
        if isinstance(theme, bytes):
            theme = theme.decode()
        return theme if theme in ("light", "dark") else "light"
    except Exception:
        return "light"


def _save_theme_setting(theme: str):
    try:
        s = QSettings("Evana", "Evana")
        s.setValue("theme", theme)
    except Exception:
        pass


def set_theme(theme: str):
    """يغيّر الثيم الحالي ويحفظه"""
    global CURRENT_THEME
    CURRENT_THEME = "dark" if theme == "dark" else "light"
    _save_theme_setting(CURRENT_THEME)
    _ICON_CACHE.clear()   # ← مهم: نفسح الكاش لأن الأيقونات تلونت بالثيم القديم


def get_theme() -> str:
    return CURRENT_THEME


def get_palette() -> dict:
    return DARK_PALETTE if CURRENT_THEME == "dark" else LIGHT_PALETTE


# تهيئة الثيم من الإعدادات عند الاستيراد
CURRENT_THEME = _load_theme_setting()


# ============================================================
#              ICON HELPERS — theme-aware
# ============================================================
_ICON_CACHE = {}

# أيقونات ملونة بطبيعتها (لا تُلوّن أبداً)
COLORED_ICONS = {
    "play-circle(1).png",
    "pause-circle.png",
    "dot-circle.png",
    "heart-filled.png",
}


def _tint_pixmap(pix: QPixmap, color: str) -> QPixmap:
    """يلوّن pixmap بلون واحد مع حفظ الشفافية"""
    result = QPixmap(pix.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.drawPixmap(0, 0, pix)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color))
    painter.end()
    return result


def load_icon(name: str) -> QIcon:
    """
    يحمّل الأيقونة. في الوضع الفاتح: كما هي.
    في الوضع الغامق: تُلوّن تلقائياً بـ ICON color.
    """
    cache_key = (name, CURRENT_THEME)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    p = ICONS_DIR / name
    if not p.exists():
        icon = QIcon()
        _ICON_CACHE[cache_key] = icon
        return icon

    pix = QPixmap(str(p))
    if pix.isNull():
        icon = QIcon()
        _ICON_CACHE[cache_key] = icon
        return icon

    # أيقونات ملونة → كما هي دائماً
    if name in COLORED_ICONS:
        icon = QIcon(pix)
    elif CURRENT_THEME == "light":
        # في الوضع الفاتح → الأيقونة الأصلية (سوداء تقريباً)
        icon = QIcon(pix)
    else:
        # في الوضع الغامق → لوّنها باللون الفاتح
        tinted = _tint_pixmap(pix, get_palette()["ICON"])
        icon = QIcon(tinted)

    _ICON_CACHE[cache_key] = icon
    return icon


def load_icon_tinted(name: str, color: str) -> QIcon:
    """يحمّل الأيقونة ويلوّنها بلون محدد (يُستخدم في PhotoViewer مثلاً)"""
    p = ICONS_DIR / name
    if not p.exists():
        return QIcon()
    pix = QPixmap(str(p))
    if pix.isNull():
        return QIcon()
    return QIcon(_tint_pixmap(pix, color))


# ============================================================
#              File-type constants
# ============================================================
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif', '.heic', '.ico'}
VIDEO_EXT = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg', '.3gp'}
AUDIO_EXT = {'.mp3', '.m4a', '.wav', '.ogg', '.flac', '.aac', '.opus', '.wma'}

AUDIO_FORMATS = ["mp3", "m4a", "wav", "ogg", "flac"]
IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff", "ico"]
VIDEO_FORMATS = ["mp4", "mkv", "webm", "avi", "mov"]


def get_file_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    return "unknown"


def get_type_icon_name(ftype: str) -> str:
    if ftype == "image":
        return "picture.png"
    if ftype == "video":
        return "film.png"
    if ftype == "audio":
        return "waveform-path.png"
    return "add-document.png"


# ============================================================
#              FFmpeg setup
# ============================================================
def setup_ffmpeg():
    import shutil
    ffmpeg_path = None
    ffprobe_path = None
    if BIN_DIR.exists():
        current_path = os.environ.get("PATH", "")
        if str(BIN_DIR) not in current_path:
            os.environ["PATH"] = str(BIN_DIR) + os.pathsep + current_path
        for name in ("ffmpeg.exe", "ffmpeg"):
            p = BIN_DIR / name
            if p.exists():
                ffmpeg_path = p
                break
        for name in ("ffprobe.exe", "ffprobe"):
            p = BIN_DIR / name
            if p.exists():
                ffprobe_path = p
                break
    if not ffmpeg_path:
        s = shutil.which("ffmpeg")
        if s:
            ffmpeg_path = Path(s)
    if not ffprobe_path:
        s = shutil.which("ffprobe")
        if s:
            ffprobe_path = Path(s)
    return ffmpeg_path, ffprobe_path


FFMPEG_PATH, FFPROBE_PATH = setup_ffmpeg()
FFMPEG_AVAILABLE = FFMPEG_PATH is not None
if FFMPEG_AVAILABLE:
    print(f"✅ FFmpeg found: {FFMPEG_PATH}")
else:
    print("⚠️  FFmpeg NOT found — merging & MP3 won't work")


def load_fonts():
    if not FONTS_DIR.exists():
        return
    loaded = 0
    for pattern in ("*.ttf", "*.otf"):
        for f in FONTS_DIR.glob(pattern):
            if QFontDatabase.addApplicationFont(str(f)) != -1:
                loaded += 1
    print(f"✅ Loaded {loaded} fonts")


def _static_label(label):
    label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)


def format_time(ms: int) -> str:
    if ms < 0:
        ms = 0
    s = ms // 1000
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def _fmt_size(b):
    if not b:
        return "—"
    b = float(b)
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def _fmt_duration(s):
    if s is None:
        return "—"
    s = int(s)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"


# ============================================================
#              Video Player Widget
# ============================================================
class VideoPlayerWidget(QWidget):
    fullscreen_toggled = Signal(bool)
    prev_requested = Signal()
    next_requested = Signal()

    HIDE_DELAY = 10000
    OVERLAY_HEIGHT = 96
    OVERLAY_MARGIN = 14

    def __init__(self):
        super().__init__()
        if not MULTIMEDIA_OK:
            return

        self._is_fullscreen = False
        self._is_seeking = False
        self._overlay_hovered = False

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)
        self.media_player.setAudioOutput(self.audio_output)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#0E1117")))

        self.video_item = QGraphicsVideoItem()
        self.video_item.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.scene.addItem(self.video_item)
        self.media_player.setVideoOutput(self.video_item)

        self.overlay = self._build_overlay()
        self.overlay_proxy = self.scene.addWidget(self.overlay)
        self.overlay_proxy.setZValue(100)
        self.overlay_proxy.setOpacity(1.0)

        self.view = QGraphicsView(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.view.setOptimizationFlags(
            QGraphicsView.OptimizationFlag.DontSavePainterState
            | QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing
        )
        self.view.setStyleSheet("QGraphicsView { background: #0E1117; border: none; padding: 0; }")
        self.view.setMouseTracking(True)
        self.view.viewport().setMouseTracking(True)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view.installEventFilter(self)
        self.view.viewport().installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(self.HIDE_DELAY)
        self.hide_timer.timeout.connect(self._fade_out)

        self.media_player.positionChanged.connect(self._on_position)
        self.media_player.durationChanged.connect(self._on_duration)
        self.media_player.playbackStateChanged.connect(self._on_state)
        self.media_player.mediaStatusChanged.connect(self._on_status)

        QTimer.singleShot(0, self._update_layout)

    def _build_overlay(self):
        # ⚠️ الـ overlay داكن دائماً (فوق الفيديو) — لا يتأثر بالثيم
        ov = QWidget()
        ov.setObjectName("playerOverlay")
        ov.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ov.setMouseTracking(True)
        ov.installEventFilter(self)
        ov.setStyleSheet("""
            #playerOverlay { background-color: rgba(12, 15, 24, 220); border-radius: 12px; }
            #playerOverlay QLabel { color: #FFFFFF; background: transparent; }
        """)

        ol = QVBoxLayout(ov)
        ol.setContentsMargins(16, 10, 16, 10)
        ol.setSpacing(8)

        seek_row = QHBoxLayout()
        seek_row.setSpacing(10)

        self.cur_time = QLabel("00:00")
        self.cur_time.setStyleSheet("color: #C7CCD6; font-size: 12px; min-width: 50px;")
        seek_row.addWidget(self.cur_time)

        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.seek.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background-color: rgba(255,255,255,50); border-radius: 3px; }
            QSlider::sub-page:horizontal { background-color: #4359D6; border-radius: 3px; }
            QSlider::handle:horizontal { background-color: #FFFFFF; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }
            QSlider::handle:horizontal:hover { background-color: #E1E5F5; }
        """)
        self.seek.sliderPressed.connect(self._on_seek_press)
        self.seek.sliderMoved.connect(self._on_seek_drag)
        self.seek.sliderReleased.connect(self._on_seek_release)
        seek_row.addWidget(self.seek, 1)

        self.tot_time = QLabel("00:00")
        self.tot_time.setStyleSheet("color: #C7CCD6; font-size: 12px; min-width: 50px;")
        seek_row.addWidget(self.tot_time)
        ol.addLayout(seek_row)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)

        self.play_btn = QPushButton()
        self.play_btn.setIcon(load_icon("play-circle(1).png"))
        self.play_btn.setIconSize(QSize(34, 34))
        self.play_btn.setFixedSize(42, 42)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self.play_btn.clicked.connect(self._toggle_play)
        ctrl.addWidget(self.play_btn)

        def mk_btn(text, cb, size=16, tip=""):
            b = QPushButton(text)
            b.setFixedSize(34, 34)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if tip:
                b.setToolTip(tip)
            b.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: #FFFFFF; border: none; border-radius: 17px; font-size: {size}px;
                    font-family: "Segoe UI Symbol", "Arial Unicode MS", sans-serif; }}
                QPushButton:hover {{ background-color: rgba(255,255,255,30); }}
            """)
            b.clicked.connect(cb)
            return b

        ctrl.addWidget(mk_btn("⏮", self.prev_requested.emit, 17, "Prev"))
        ctrl.addWidget(mk_btn("⏭", self.next_requested.emit, 17, "Next"))
        ctrl.addWidget(mk_btn("⏹", self._stop, 15, "Stop"))
        ctrl.addSpacing(10)

        self.mute_btn = mk_btn("🔊", self._toggle_mute, 16, "Mute (M)")
        ctrl.addWidget(self.mute_btn)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.setFixedWidth(100)
        self.volume.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.volume.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background-color: rgba(255,255,255,50); border-radius: 2px; }
            QSlider::sub-page:horizontal { background-color: #4359D6; border-radius: 2px; }
            QSlider::handle:horizontal { background-color: #FFFFFF; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
        """)
        self.volume.valueChanged.connect(self._on_volume)
        ctrl.addWidget(self.volume)
        ctrl.addStretch()

        combo_style = """
            QComboBox { background-color: rgba(255,255,255,25); color: #FFFFFF; border: 1px solid rgba(255,255,255,40);
                border-radius: 8px; padding: 4px 8px; font-size: 12px; }
            QComboBox:hover { border-color: #4359D6; }
            QComboBox::drop-down { border: none; width: 16px; }
            QComboBox QAbstractItemView { background-color: #1A1F2E; color: #FFFFFF; border: 1px solid #2A3142;
                selection-background-color: #4359D6; selection-color: #FFFFFF; padding: 4px; }
        """

        spd = QLabel("Speed")
        spd.setStyleSheet("color: #9CA3B0; font-size: 12px; font-weight: 600;")
        ctrl.addWidget(spd)
        self.speed = QComboBox()
        self.speed.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed.setCurrentText("1.0x")
        self.speed.setFixedWidth(72)
        self.speed.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.speed.setStyleSheet(combo_style)
        self.speed.currentTextChanged.connect(self._on_speed)
        ctrl.addWidget(self.speed)

        rep = QLabel("Repeat")
        rep.setStyleSheet("color: #9CA3B0; font-size: 12px; font-weight: 600;")
        ctrl.addWidget(rep)
        self.repeat = QComboBox()
        self.repeat.addItems(["Off", "One", "All"])
        self.repeat.setFixedWidth(72)
        self.repeat.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.repeat.setStyleSheet(combo_style)
        ctrl.addWidget(self.repeat)

        ctrl.addWidget(mk_btn("⛶", self._on_fs_clicked, 18, "Fullscreen (F)"))
        ol.addLayout(ctrl)
        return ov

    def _on_fs_clicked(self):
        self.fullscreen_toggled.emit(not self._is_fullscreen)

    def set_fullscreen(self, fs: bool):
        self._is_fullscreen = fs
        if fs:
            self._schedule_hide()
        else:
            self.hide_timer.stop()
            self.overlay_proxy.setOpacity(1.0)
        QTimer.singleShot(120, self._update_layout)

    def _schedule_hide(self):
        if self._is_fullscreen and not self._overlay_hovered:
            self.hide_timer.start(self.HIDE_DELAY)

    def _show_overlay(self):
        a = QPropertyAnimation(self.overlay_proxy, b"opacity", self)
        a.setDuration(200)
        a.setStartValue(self.overlay_proxy.opacity())
        a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.start()
        self._ov_anim = a
        self._schedule_hide()

    def _fade_out(self):
        if self._overlay_hovered:
            return
        a = QPropertyAnimation(self.overlay_proxy, b"opacity", self)
        a.setDuration(500)
        a.setStartValue(self.overlay_proxy.opacity())
        a.setEndValue(0.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.start()
        self._ov_anim = a

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._update_layout)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(50, self._update_layout)

    def _update_layout(self):
        if not hasattr(self, "view"):
            return
        vw = self.view.viewport().width()
        vh = self.view.viewport().height()
        if vw <= 0 or vh <= 0:
            return
        self.scene.setSceneRect(0, 0, vw, vh)
        self.video_item.setSize(QSizeF(vw, vh))
        self.video_item.setPos(0, 0)
        ov_w = max(420, vw - 2 * self.OVERLAY_MARGIN)
        self.overlay.setFixedSize(ov_w, self.OVERLAY_HEIGHT)
        self.overlay_proxy.setPos(self.OVERLAY_MARGIN, vh - self.OVERLAY_HEIGHT - self.OVERLAY_MARGIN)
        self.overlay_proxy.setZValue(100)

    def eventFilter(self, obj, event):
        if not hasattr(self, "overlay"):
            return super().eventFilter(obj, event)
        t = event.type()
        if t == QEvent.Type.KeyPress:
            self._handle_key(event)
            return True
        if t in (QEvent.Type.MouseMove, QEvent.Type.HoverMove):
            if self._is_fullscreen:
                self._show_overlay()
        elif t == QEvent.Type.MouseButtonDblClick:
            self._on_fs_clicked()
            return True
        if obj is self.overlay:
            if t == QEvent.Type.Enter:
                self._overlay_hovered = True
                self.hide_timer.stop()
            elif t == QEvent.Type.Leave:
                self._overlay_hovered = False
                self._schedule_hide()
        return super().eventFilter(obj, event)

    def _handle_key(self, event):
        k = event.key()
        if k == Qt.Key.Key_Space:
            self._toggle_play()
        elif k == Qt.Key.Key_Left:
            self._skip(-5)
        elif k == Qt.Key.Key_Right:
            self._skip(5)
        elif k == Qt.Key.Key_Up:
            self.volume.setValue(min(100, self.volume.value() + 5))
        elif k == Qt.Key.Key_Down:
            self.volume.setValue(max(0, self.volume.value() - 5))
        elif k == Qt.Key.Key_M:
            self._toggle_mute()
        elif k == Qt.Key.Key_F:
            self._on_fs_clicked()
        else:
            super().keyPressEvent(event)

    def keyPressEvent(self, event):
        self._handle_key(event)

    def load_media(self, name: str, path: str):
        self.media_player.setSource(QUrl.fromLocalFile(path))
        self.media_player.play()

    def _toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
        QTimer.singleShot(30, self._update_play_icon)

    def _stop(self):
        self.media_player.stop()
        self._update_play_icon()

    def _skip(self, seconds):
        pos = self.media_player.position() + seconds * 1000
        pos = max(0, min(pos, self.media_player.duration()))
        self.media_player.setPosition(pos)

    def _on_seek_press(self):
        self._is_seeking = True

    def _on_seek_drag(self, pos):
        self._is_seeking = True
        self.cur_time.setText(format_time(pos))

    def _on_seek_release(self):
        self.media_player.setPosition(self.seek.value())
        self._is_seeking = False

    def _on_volume(self, v):
        self.audio_output.setVolume(v / 100)
        if v == 0:
            self.mute_btn.setText("🔇")
        elif v < 50:
            self.mute_btn.setText("🔉")
        else:
            self.mute_btn.setText("🔊")

    def _toggle_mute(self):
        muted = not self.audio_output.isMuted()
        self.audio_output.setMuted(muted)
        self.mute_btn.setText("🔇" if muted else "🔊")

    def _on_speed(self, text):
        self.media_player.setPlaybackRate(float(text.replace("x", "")))

    def _on_position(self, pos):
        if self._is_seeking:
            return
        self.seek.blockSignals(True)
        self.seek.setValue(pos)
        self.seek.blockSignals(False)
        self.cur_time.setText(format_time(pos))

    def _on_duration(self, dur):
        self.seek.setRange(0, dur)
        self.tot_time.setText(format_time(dur))

    def _update_play_icon(self):
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            icon = load_icon("pause-circle.png")
            if icon.isNull():
                self.play_btn.setIcon(QIcon())
                self.play_btn.setText("⏸")
            else:
                self.play_btn.setIcon(icon)
                self.play_btn.setText("")
        else:
            icon = load_icon("play-circle(1).png")
            if icon.isNull():
                self.play_btn.setIcon(QIcon())
                self.play_btn.setText("▶")
            else:
                self.play_btn.setIcon(icon)
                self.play_btn.setText("")

    def _on_state(self, state):
        self._update_play_icon()

    def _on_status(self, status):
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        mode = self.repeat.currentText()
        if mode == "One":
            self.media_player.setPosition(0)
            self.media_player.play()
        elif mode == "All":
            self.next_requested.emit()
        else:
            self.next_requested.emit()


# ============================================================
#              Fetch Info Worker
# ============================================================
class FetchInfoWorker(QThread):
    finished_signal = Signal(bool, object, str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        if not YTDLP_OK:
            self.finished_signal.emit(False, None, "yt-dlp not installed")
            return
        try:
            opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
            if FFMPEG_AVAILABLE:
                opts["ffmpeg_location"] = str(FFMPEG_PATH.parent)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            self.finished_signal.emit(True, info, "")
        except Exception as e:
            self.finished_signal.emit(False, None, str(e)[:200])


# ============================================================
#              Download Worker
# ============================================================
class DownloadWorker(QThread):
    progress_signal = Signal(dict)
    finished_signal = Signal(bool, str)

    def __init__(self, url: str, opts: dict):
        super().__init__()
        self.url = url
        self.opts = opts
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        if not YTDLP_OK:
            self.finished_signal.emit(False, "yt-dlp not installed")
            return
        try:
            def progress_hook(d):
                if self._cancelled:
                    raise yt_dlp.utils.DownloadError("__CANCELLED__")
                self.progress_signal.emit(d)

            def pp_hook(d):
                if d.get("status") == "started":
                    self.progress_signal.emit({"status": "postprocessing"})

            opts = dict(self.opts)
            opts["progress_hooks"] = [progress_hook]
            opts["postprocessor_hooks"] = [pp_hook]

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])

            self.finished_signal.emit(True, "Download complete")
        except Exception as e:
            msg = str(e)
            if "__CANCELLED__" in msg or self._cancelled:
                self.finished_signal.emit(False, "Cancelled")
            else:
                self.finished_signal.emit(False, msg[:200])


# ============================================================
#              Download Item Widget
# ============================================================
class DownloadItemWidget(QFrame):
    cancel_requested = Signal()

    def __init__(self, title: str = ""):
        super().__init__()
        self.setObjectName("downloadItem")
        self.setMinimumHeight(110)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self._finished = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(6)
        self.title_label = QLabel(title or "Preparing...")
        self.title_label.setObjectName("dlTitle")
        self.title_label.setToolTip(title)
        self.title_label.setMinimumWidth(0)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        top.addWidget(self.title_label, 1)

        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setObjectName("dlCancel")
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setToolTip("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        top.addWidget(self.cancel_btn)
        layout.addLayout(top)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setObjectName("dlProgress")
        self.progress.setFixedHeight(8)
        layout.addWidget(self.progress)

        bottom = QHBoxLayout()
        self.status_label = QLabel("Queued...")
        self.status_label.setObjectName("dlStatus")
        self.status_label.setMinimumWidth(0)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        bottom.addWidget(self.status_label, 1)
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("dlPercent")
        bottom.addWidget(self.percent_label)
        layout.addLayout(bottom)

    def update_progress(self, d: dict):
        status = d.get("status", "")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int(downloaded / total * 100)
                self.progress.setValue(pct)
                self.percent_label.setText(f"{pct}%")
            else:
                self.percent_label.setText("…")
            speed = d.get("speed")
            eta = d.get("eta")
            parts = []
            if downloaded:
                parts.append(_fmt_size(downloaded))
            if total:
                parts.append(_fmt_size(total))
            if speed:
                parts.append(f"{_fmt_size(speed)}/s")
            if eta is not None:
                parts.append(f"ETA {_fmt_duration(eta)}")
            self.status_label.setText("  •  ".join(parts) or "Downloading...")
        elif status == "finished":
            self.progress.setValue(100)
            self.percent_label.setText("100%")
            self.status_label.setText("Processing...")
        elif status == "postprocessing":
            self.status_label.setText("Running FFmpeg...")

    def set_completed(self, success: bool, msg: str = ""):
        self._finished = True
        if success:
            self.progress.setValue(100)
            self.percent_label.setText("✓")
            self.status_label.setText(msg or "Complete")
            self.cancel_btn.setText("✓")
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setStyleSheet("color: #4ADE80;")
        else:
            self.percent_label.setText("✕")
            self.status_label.setText(msg or "Failed")
            self.cancel_btn.setText("✕")
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setStyleSheet("color: #F87171;")
            # ============================================================
#                    Downloader Page
# ============================================================
class DownloaderPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("downloaderPage")
        self._downloads = []
        self._current_info = None
        self._current_url = ""
        self._fetch_worker = None
        self.net = QNetworkAccessManager(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(14)

        title = QLabel("Video Downloader")
        title.setObjectName("heading")
        _static_label(title)
        layout.addWidget(title)

        sub = QLabel("Download videos from YouTube, Vimeo, Twitter and 1000+ sites.")
        sub.setObjectName("description")
        _static_label(sub)
        layout.addWidget(sub)

        if not YTDLP_OK:
            warn = QLabel("⚠️  yt-dlp not installed — run: pip install yt-dlp")
            warn.setStyleSheet("color: #B45309; background: #FEF3C7; padding: 10px 16px;"
                " border-radius: 10px; font-size: 13px; font-weight: 600;")
            layout.addWidget(warn)

        if not FFMPEG_AVAILABLE:
            ff_warn = QLabel("⚠️  FFmpeg not found in assets/bin/ — merging & MP3 conversion will be limited")
            ff_warn.setStyleSheet("color: #B45309; background: #FEF3C7; padding: 10px 16px;"
                " border-radius: 10px; font-size: 13px; font-weight: 600;")
            layout.addWidget(ff_warn)

        layout.addSpacing(4)

        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(14)

        url_card = QFrame()
        url_card.setObjectName("card")
        uc = QVBoxLayout(url_card)
        uc.setContentsMargins(24, 20, 24, 20)
        uc.setSpacing(10)

        url_lbl = QLabel("VIDEO URL")
        url_lbl.setObjectName("fieldLabel")
        uc.addWidget(url_lbl)

        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/watch?v=...")
        self.url_input.setObjectName("urlInput")
        self.url_input.setFixedHeight(46)
        self.url_input.returnPressed.connect(self._on_fetch_clicked)
        url_row.addWidget(self.url_input, 1)

        paste_btn = QPushButton()
        paste_icon = load_icon("paste.png")
        if paste_icon.isNull():
            paste_btn.setText("📋")
        else:
            paste_btn.setIcon(paste_icon)
            paste_btn.setIconSize(QSize(20, 20))
        paste_btn.setObjectName("iconBtn")
        paste_btn.setFixedSize(46, 46)
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.setToolTip("Paste from clipboard")
        paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(paste_btn)

        clear_btn = QPushButton("✕")
        clear_btn.setObjectName("iconBtn")
        clear_btn.setFixedSize(46, 46)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setToolTip("Clear")
        clear_btn.clicked.connect(self._clear_all)
        url_row.addWidget(clear_btn)

        uc.addLayout(url_row)

        self.fetch_btn = QPushButton("  Fetch Info")
        self.fetch_btn.setObjectName("fetchButton")
        self.fetch_btn.setFixedHeight(48)
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        uc.addWidget(self.fetch_btn)

        self.fetch_status = QLabel("")
        self.fetch_status.setObjectName("fetchStatus")
        self.fetch_status.setWordWrap(True)
        uc.addWidget(self.fetch_status)

        left.addWidget(url_card)

        self.details_stack = QStackedWidget()
        self.details_stack.setObjectName("detailsStack")

        empty_page = QWidget()
        empty_lay = QVBoxLayout(empty_page)
        empty_lay.setContentsMargins(0, 0, 0, 0)
        self.details_stack.addWidget(empty_page)

        details_page = QWidget()
        dp = QVBoxLayout(details_page)
        dp.setContentsMargins(0, 0, 0, 0)
        dp.setSpacing(14)

        info_card = QFrame()
        info_card.setObjectName("card")
        ic = QHBoxLayout(info_card)
        ic.setContentsMargins(18, 16, 18, 16)
        ic.setSpacing(14)

        self.thumb_label = QLabel()
        self.thumb_label.setObjectName("thumbLabel")
        self.thumb_label.setFixedSize(220, 124)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("No preview")
        ic.addWidget(self.thumb_label)

        info_col = QVBoxLayout()
        info_col.setSpacing(6)
        info_col.addStretch()

        self.video_title = QLabel("")
        self.video_title.setObjectName("videoTitle")
        self.video_title.setWordWrap(True)
        info_col.addWidget(self.video_title)

        self.video_meta = QLabel("")
        self.video_meta.setObjectName("videoMeta")
        self.video_meta.setWordWrap(True)
        info_col.addWidget(self.video_meta)

        info_col.addStretch()
        ic.addLayout(info_col, 1)

        dp.addWidget(info_card)

        opts_card = QFrame()
        opts_card.setObjectName("card")
        oc = QVBoxLayout(opts_card)
        oc.setContentsMargins(24, 20, 24, 20)
        oc.setSpacing(14)

        opts_title = QLabel("Download Options")
        opts_title.setObjectName("cardTitle2")
        _static_label(opts_title)
        oc.addWidget(opts_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        q_lbl = QLabel("QUALITY")
        q_lbl.setObjectName("fieldLabel")
        grid.addWidget(q_lbl, 0, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.setObjectName("dlCombo")
        self.quality_combo.setFixedHeight(42)
        self.quality_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        grid.addWidget(self.quality_combo, 1, 0)

        f_lbl = QLabel("FORMAT")
        f_lbl.setObjectName("fieldLabel")
        grid.addWidget(f_lbl, 0, 1)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "MKV", "WEBM", "MP3", "M4A"])
        self.format_combo.setObjectName("dlCombo")
        self.format_combo.setFixedHeight(42)
        self.format_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        grid.addWidget(self.format_combo, 1, 1)

        p_lbl = QLabel("SAVE FOLDER")
        p_lbl.setObjectName("fieldLabel")
        grid.addWidget(p_lbl, 2, 0, 1, 2)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        path_row.setContentsMargins(0, 0, 0, 0)
        self.path_input = QLineEdit()
        self.path_input.setText(str(Path.home() / "Downloads"))
        self.path_input.setObjectName("urlInput")
        self.path_input.setFixedHeight(42)
        path_row.addWidget(self.path_input, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedSize(90, 42)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(browse_btn)

        pw = QWidget()
        pw.setLayout(path_row)
        grid.addWidget(pw, 3, 0, 1, 2)

        oc.addLayout(grid)

        checks_title = QLabel("ADDITIONAL OPTIONS")
        checks_title.setObjectName("fieldLabel")
        oc.addWidget(checks_title)

        checks_row = QHBoxLayout()
        checks_row.setSpacing(20)

        self.sub_check = QCheckBox("Subtitles")
        self.thumb_check = QCheckBox("Thumbnail")
        self.meta_check = QCheckBox("Metadata")
        for cb in (self.sub_check, self.thumb_check, self.meta_check):
            cb.setObjectName("dlCheck")
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            checks_row.addWidget(cb)

        checks_row.addStretch()
        oc.addLayout(checks_row)

        self.download_btn = QPushButton("  ⬇   Download")
        self.download_btn.setObjectName("downloadButton")
        self.download_btn.setFixedHeight(52)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.clicked.connect(self._start_download)
        oc.addWidget(self.download_btn)

        dp.addWidget(opts_card)
        dp.addStretch()

        self.details_stack.addWidget(details_page)

        left.addWidget(self.details_stack, 1)
        body.addLayout(left, 3)

        queue_card = QFrame()
        queue_card.setObjectName("playlistFrame")
        queue_card.setFixedWidth(400)

        qc = QVBoxLayout(queue_card)
        qc.setContentsMargins(18, 18, 18, 18)
        qc.setSpacing(12)

        qh = QHBoxLayout()
        qt = QLabel("Download Queue")
        qt.setObjectName("playlistTitle")
        _static_label(qt)
        qh.addWidget(qt)
        qh.addStretch()

        clear_btn = QPushButton("Clear Done")
        clear_btn.setObjectName("miniButtonSmall")
        clear_btn.setFixedHeight(28)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_completed)
        qh.addWidget(clear_btn)
        qc.addLayout(qh)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setObjectName("queueScroll")
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_scroll.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustIgnored)

        self.queue_container = QWidget()
        self.queue_container.setObjectName("queueContainer")
        self.queue_container.setMinimumWidth(0)
        self.queue_inner = QVBoxLayout(self.queue_container)
        self.queue_inner.setContentsMargins(0, 0, 0, 0)
        self.queue_inner.setSpacing(8)
        self.queue_inner.addStretch()

        self.queue_scroll.setWidget(self.queue_container)
        qc.addWidget(self.queue_scroll, 1)

        self.empty_label = QLabel("No downloads yet.\nPaste a URL to begin.")
        self.empty_label.setObjectName("miniLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc.addWidget(self.empty_label)

        body.addWidget(queue_card, 2)
        layout.addLayout(body, 1)

    def _paste_url(self):
        cb = QApplication.clipboard()
        self.url_input.setText(cb.text().strip())

    def _clear_all(self):
        self.url_input.clear()
        self.fetch_status.setText("")
        self._current_info = None
        self._current_url = ""
        self.details_stack.setCurrentIndex(0)

    def _browse_path(self):
        d = QFileDialog.getExistingDirectory(self, "Choose save folder", self.path_input.text())
        if d:
            self.path_input.setText(d)

    def _on_fetch_clicked(self):
        url = self.url_input.text().strip()
        if not url:
            self._set_fetch_status("Please enter a URL first.", error=True)
            return
        if not YTDLP_OK:
            self._set_fetch_status("yt-dlp is not installed.", error=True)
            return
        self.details_stack.setCurrentIndex(0)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("  Fetching...")
        self._set_fetch_status("Fetching video info...")
        self._current_url = url
        self._fetch_worker = FetchInfoWorker(url)
        self._fetch_worker.finished_signal.connect(self._on_fetch_finished)
        self._fetch_worker.start()

    def _set_fetch_status(self, text: str, error: bool = False):
        self.fetch_status.setText(text)
        p = get_palette()
        if error:
            self.fetch_status.setStyleSheet(f"color: {p['ERROR']}; font-size: 12px; font-weight: 600;"
                " background: transparent; padding: 2px 0;")
        else:
            self.fetch_status.setStyleSheet(f"color: {p['TEXT_SECOND']}; font-size: 12px; font-weight: 500;"
                " background: transparent; padding: 2px 0;")

    def _on_fetch_finished(self, success, info, error):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("  Fetch Info")
        if not success or not info:
            self._set_fetch_status(f"Failed: {error or 'Unknown error'}", error=True)
            return
        self._current_info = info
        self._set_fetch_status("✓ Info fetched successfully.", error=False)
        title = info.get("title") or "Untitled video"
        uploader = info.get("uploader") or info.get("channel") or "Unknown"
        duration = info.get("duration")
        view_count = info.get("view_count")
        self.video_title.setText(title)
        meta_parts = [f"By {uploader}"]
        if duration:
            meta_parts.append(f"⏱ {_fmt_duration(duration)}")
        if view_count:
            meta_parts.append(f"👁 {view_count:,}")
        self.video_meta.setText("  •  ".join(meta_parts))
        thumb_url = info.get("thumbnail")
        if thumb_url:
            self.thumb_label.setText("Loading...")
            self._load_thumbnail(thumb_url)
        else:
            self.thumb_label.setText("No preview")
        self._populate_qualities(info)
        self.details_stack.setCurrentIndex(1)

    def _load_thumbnail(self, url):
        req = QNetworkRequest(QUrl(url))
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        reply = self.net.get(req)
        reply.finished.connect(lambda r=reply: self._on_thumb_ready(r))

    def _on_thumb_ready(self, reply):
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                pix = QPixmap()
                if pix.loadFromData(data):
                    scaled = pix.scaled(self.thumb_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)
                    self.thumb_label.setPixmap(scaled)
                    return
            self.thumb_label.setText("No preview")
        finally:
            reply.deleteLater()

    def _populate_qualities(self, info):
        self.quality_combo.clear()
        formats = info.get("formats", []) or []
        heights = set()
        has_audio = False
        for f in formats:
            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            h = f.get("height")
            if vcodec and vcodec != "none" and h:
                heights.add(int(h))
            if acodec and acodec != "none":
                has_audio = True
        if heights:
            self.quality_combo.addItem("Best Available", "best")
        label_map = {4320: "8K", 2160: "4K", 1440: "2K", 1080: "1080p",
                     720: "720p", 480: "480p", 360: "360p", 240: "240p", 144: "144p"}
        for h in sorted(heights, reverse=True):
            label = label_map.get(h, f"{h}p")
            self.quality_combo.addItem(label, str(h))
        if has_audio:
            self.quality_combo.addItem("Audio Only", "audio")
        idx = self.quality_combo.findText("1080p")
        if idx >= 0:
            self.quality_combo.setCurrentIndex(idx)
        elif self.quality_combo.count() > 0:
            self.quality_combo.setCurrentIndex(0)

    def _build_opts(self) -> dict:
        quality_data = self.quality_combo.currentData()
        fmt = self.format_combo.currentText().lower()
        out_dir = self.path_input.text().strip() or str(Path.home() / "Downloads")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        opts = {
            "outtmpl": str(Path(out_dir) / "%(title)s.%(ext)s"),
            "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True,
        }
        if FFMPEG_AVAILABLE:
            opts["ffmpeg_location"] = str(FFMPEG_PATH.parent)
        needs_merge = False
        needs_extract = False
        if quality_data == "audio":
            opts["format"] = "bestaudio/best"
            needs_extract = True
        elif quality_data == "best" or not quality_data:
            if fmt in ("mp3", "m4a"):
                opts["format"] = "bestaudio/best"
                needs_extract = True
            else:
                opts["format"] = "bestvideo+bestaudio/best"
                needs_merge = True
        else:
            h = quality_data
            if fmt in ("mp3", "m4a"):
                opts["format"] = "bestaudio/best"
                needs_extract = True
            else:
                opts["format"] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
                needs_merge = True
        postprocessors = []
        if needs_extract and FFMPEG_AVAILABLE:
            codec = fmt if fmt in ("mp3", "m4a") else "mp3"
            postprocessors.append({"key": "FFmpegExtractAudio", "preferredcodec": codec})
        if needs_merge:
            opts["merge_output_format"] = fmt if fmt in ("mp4", "mkv", "webm") else "mp4"
        if needs_extract and not FFMPEG_AVAILABLE:
            opts["format"] = "bestaudio/best"
        if self.sub_check.isChecked():
            opts["writesubtitles"] = True
            opts["writeautomaticsub"] = True
            opts["subtitleslangs"] = ["en", "ar"]
            if FFMPEG_AVAILABLE:
                postprocessors.append({"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False})
        if self.thumb_check.isChecked():
            opts["writethumbnail"] = True
            if FFMPEG_AVAILABLE:
                postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
        if self.meta_check.isChecked():
            opts["addmetadata"] = True
            if FFMPEG_AVAILABLE:
                postprocessors.append({"key": "FFmpegMetadata"})
        if postprocessors:
            opts["postprocessors"] = postprocessors
        return opts

    def _start_download(self):
        if not self._current_url or not self._current_info:
            return
        title = self._current_info.get("title") or "Untitled"
        try:
            opts = self._build_opts()
        except Exception as e:
            print(f"⚠️ Options error: {e}")
            return
        item = DownloadItemWidget(title)
        self.queue_inner.insertWidget(self.queue_inner.count() - 1, item)
        self.empty_label.setVisible(False)
        worker = DownloadWorker(self._current_url, opts)
        worker.progress_signal.connect(item.update_progress)
        worker.finished_signal.connect(
            lambda ok, msg, it=item: self._on_download_finished(it, ok, msg))
        item.cancel_requested.connect(worker.cancel)
        self._downloads.append((worker, item))
        worker.start()

    def _on_download_finished(self, item, success, msg):
        item.set_completed(success, msg)

    def _clear_completed(self):
        remaining = []
        for w, it in self._downloads:
            if getattr(it, "_finished", False):
                it.setParent(None)
                it.deleteLater()
            else:
                remaining.append((w, it))
        self._downloads = remaining
        if not self._downloads:
            self.empty_label.setVisible(True)


# ============================================================
#                    Photo Viewer Dialog
# ============================================================
class PhotoViewer(QDialog):
    """
    عارض صور fullscreen بملء الشاشة.
    الثيم: داكن دائماً (لأنه فوق الصور — لا يتأثر بثيم التطبيق)
    """
    def __init__(self, files: list, start_index: int, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Photo Viewer")
        self.setStyleSheet("background: #0E1117;")
        self.files = list(files)
        self.index = max(0, min(start_index, len(self.files) - 1))
        self._zoom = 1.0
        self._favorites = set()
        self._info_visible = False
        self._needs_fit = True
        self._build_ui()
        self._load_current()
        QTimer.singleShot(60, self.showFullScreen)

    def _build_ui(self):
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#0E1117")))
        self.pix_item = QGraphicsPixmapItem()
        self.pix_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene.addItem(self.pix_item)

        self.view = QGraphicsView(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("QGraphicsView { background: #0E1117; border: none; }")
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.viewport().installEventFilter(self)

        top_bar = QWidget(self)
        top_bar.setObjectName("viewerTopBar")
        top_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        top_bar.setStyleSheet(
            "#viewerTopBar { background: rgba(12,15,24,220); }"
            "#viewerTopBar QLabel { color: #FFFFFF; background: transparent; }"
        )
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(18, 10, 18, 10)
        top_lay.setSpacing(10)

        self.title_label = QLabel("")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 700;")
        top_lay.addWidget(self.title_label)
        top_lay.addStretch()

        self.fav_btn = self._mk_toolbar_btn("heart.png", "Favorite (F)")
        self.fav_btn.clicked.connect(self._toggle_favorite)
        top_lay.addWidget(self.fav_btn)

        info_btn = self._mk_toolbar_btn("info.png", "Info (I)")
        info_btn.clicked.connect(self._toggle_info)
        top_lay.addWidget(info_btn)

        trash_btn = self._mk_toolbar_btn("trash.png", "Delete (Del)")
        trash_btn.clicked.connect(self._delete_current)
        top_lay.addWidget(trash_btn)

        close_btn = self._mk_toolbar_btn("cross-circle.png", "Close (Esc)")
        close_btn.clicked.connect(self.close)
        top_lay.addWidget(close_btn)

        bottom_bar = QWidget(self)
        bottom_bar.setObjectName("viewerBottomBar")
        bottom_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bottom_bar.setStyleSheet(
            "#viewerBottomBar { background: rgba(12,15,24,220); }"
            "#viewerBottomBar QLabel { color: #FFFFFF; background: transparent; }"
        )
        bot_lay = QHBoxLayout(bottom_bar)
        bot_lay.setContentsMargins(18, 10, 18, 10)
        bot_lay.setSpacing(10)

        prev_btn = self._mk_toolbar_btn("chevron-double-dots-left.png", "Previous (←)")
        prev_btn.clicked.connect(self._prev)
        bot_lay.addWidget(prev_btn)

        self.counter_label = QLabel("1 / 1")
        self.counter_label.setStyleSheet("color: #C7CCD6; font-size: 12px; min-width: 60px;")
        bot_lay.addWidget(self.counter_label)

        next_btn = self._mk_toolbar_btn("chevron-double-dots-right.png", "Next (→)")
        next_btn.clicked.connect(self._next)
        bot_lay.addWidget(next_btn)

        bot_lay.addStretch()

        zoom_out_btn = self._mk_toolbar_btn("zoom-out.png", "Zoom out (-)")
        zoom_out_btn.clicked.connect(lambda: self._change_zoom(-0.25))
        bot_lay.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #C7CCD6; font-size: 12px; min-width: 60px;")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_lay.addWidget(self.zoom_label)

        zoom_in_btn = self._mk_toolbar_btn("zoom-in.png", "Zoom in (+)")
        zoom_in_btn.clicked.connect(lambda: self._change_zoom(0.25))
        bot_lay.addWidget(zoom_in_btn)

        reset_btn = self._mk_toolbar_btn("refresh.png", "Reset (R)")
        reset_btn.clicked.connect(self._reset_zoom)
        bot_lay.addWidget(reset_btn)

        self.info_panel = QFrame(self)
        self.info_panel.setObjectName("infoPanel")
        self.info_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.info_panel.setStyleSheet(
            "#infoPanel { background: rgba(12,15,24,235); border-radius: 12px; }"
            "#infoPanel QLabel { color: #FFFFFF; background: transparent; }"
        )
        self.info_panel.setFixedWidth(320)
        ip = QVBoxLayout(self.info_panel)
        ip.setContentsMargins(18, 16, 18, 16)
        ip.setSpacing(10)

        ip_title = QLabel("Image Info")
        ip_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800;")
        ip.addWidget(ip_title)

        self.info_content = QLabel("")
        self.info_content.setWordWrap(True)
        self.info_content.setStyleSheet("color: #C7CCD6; font-size: 12px;")
        self.info_content.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        ip.addWidget(self.info_content)
        ip.addStretch()

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        main_lay.addWidget(top_bar)
        main_lay.addWidget(self.view, 1)
        main_lay.addWidget(bottom_bar)

        self._top_bar = top_bar
        self._bottom_bar = bottom_bar
        self._update_counter()

    def _mk_toolbar_btn(self, icon_name: str, tip: str) -> QPushButton:
        btn = QPushButton()
        icon = load_icon_tinted(icon_name, "#FFFFFF")
        if icon.isNull():
            btn.setText("?")
        else:
            btn.setIcon(icon)
            btn.setIconSize(QSize(22, 22))
        btn.setFixedSize(40, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 20px; color: #FFFFFF; font-size: 16px; }
            QPushButton:hover { background-color: rgba(255,255,255,30); }
            QPushButton:pressed { background-color: rgba(255,255,255,50); }
        """)
        return btn

    def _load_current(self):
        if not self.files:
            return
        path = self.files[self.index]
        pix = QPixmap(path)
        if pix.isNull():
            self.pix_item.setPixmap(QPixmap())
            self.title_label.setText("Cannot load image")
            return
        self.pix_item.setPixmap(pix)
        self.scene.setSceneRect(self.pix_item.boundingRect())
        self._zoom = 1.0
        self.view.resetTransform()
        self._needs_fit = True
        QTimer.singleShot(0, self._fit_to_view)
        self._update_zoom_label()
        self.title_label.setText(Path(path).name)
        self._update_counter()
        self._update_favorite_icon()
        if self._info_visible:
            self._update_info_content()

    def _fit_to_view(self):
        if self.pix_item.pixmap().isNull():
            return
        self.view.fitInView(self.pix_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.view.scale(0.98, 0.98)
        self._needs_fit = False

    def _update_counter(self):
        n = len(self.files)
        self.counter_label.setText(f"{self.index + 1} / {n}")

    def _update_zoom_label(self):
        self.zoom_label.setText(f"{int(self._zoom * 100)}%")

    def _change_zoom(self, delta):
        new_zoom = max(0.1, min(8.0, self._zoom + delta))
        factor = new_zoom / self._zoom
        self.view.scale(factor, factor)
        self._zoom = new_zoom
        self._update_zoom_label()
        self._needs_fit = False

    def _reset_zoom(self):
        self._zoom = 1.0
        self.view.resetTransform()
        self._needs_fit = True
        QTimer.singleShot(0, self._fit_to_view)
        self._update_zoom_label()

    def _prev(self):
        if not self.files:
            return
        self.index = (self.index - 1) % len(self.files)
        self._load_current()

    def _next(self):
        if not self.files:
            return
        self.index = (self.index + 1) % len(self.files)
        self._load_current()

    def _toggle_favorite(self):
        path = self.files[self.index]
        if path in self._favorites:
            self._favorites.discard(path)
        else:
            self._favorites.add(path)
        self._update_favorite_icon()

    def _update_favorite_icon(self):
        path = self.files[self.index]
        if path in self._favorites:
            icon = load_icon_tinted("heart-filled.png", "#EF4444")
        else:
            icon = load_icon_tinted("heart.png", "#FFFFFF")
        if icon.isNull():
            self.fav_btn.setIcon(QIcon())
            self.fav_btn.setText("♥")
        else:
            self.fav_btn.setIcon(icon)
            self.fav_btn.setIconSize(QSize(22, 22))
            self.fav_btn.setText("")

    def _toggle_info(self):
        self._info_visible = not self._info_visible
        if self._info_visible:
            self._update_info_content()
            self.info_panel.show()
            self._reposition_info()
            self.info_panel.raise_()
        else:
            self.info_panel.hide()

    def _update_info_content(self):
        path = self.files[self.index]
        fi = QFileInfo(path)
        pix = self.pix_item.pixmap()
        w = pix.width() if not pix.isNull() else 0
        h = pix.height() if not pix.isNull() else 0
        info_lines = [
            f"<b>Name:</b> {fi.fileName()}",
            f"<b>Size:</b> {_fmt_size(fi.size())}",
            f"<b>Dimensions:</b> {w} × {h}",
            f"<b>Format:</b> {fi.suffix().upper()}",
            f"<b>Modified:</b> {fi.lastModified().toString('yyyy-MM-dd HH:mm')}",
            f"<b>Path:</b> {fi.absolutePath()}",
        ]
        self.info_content.setText("<br>".join(info_lines))

    def _reposition_info(self):
        margin = 20
        top_offset = self._top_bar.height() + margin
        self.info_panel.setGeometry(
            self.width() - self.info_panel.width() - margin,
            top_offset,
            self.info_panel.width(),
            min(360, self.height() - top_offset - self._bottom_bar.height() - margin),
        )

    def _delete_current(self):
        if not self.files:
            return
        path = self.files[self.index]
        reply = QMessageBox.question(
            self, "Delete file",
            f"Move to trash?\n\n{Path(path).name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from PySide6.QtCore import QFile
            ok = QFile.moveToTrash(path)
        except Exception:
            ok = False
        if not ok:
            try:
                os.remove(path)
                ok = True
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete:\n{e}")
                return
        self.files.pop(self.index)
        if not self.files:
            self.close()
            return
        if self.index >= len(self.files):
            self.index = len(self.files) - 1
        self._load_current()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_info()
        if getattr(self, "_needs_fit", False):
            QTimer.singleShot(0, self._fit_to_view)

    def eventFilter(self, obj, event):
        if obj is self.view.viewport():
            if event.type() == QEvent.Type.Wheel:
                delta = event.angleDelta().y()
                if delta > 0:
                    self._change_zoom(0.1)
                elif delta < 0:
                    self._change_zoom(-0.1)
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_Escape:
            self.close()
        elif k == Qt.Key.Key_Left:
            self._prev()
        elif k == Qt.Key.Key_Right:
            self._next()
        elif k == Qt.Key.Key_Plus or k == Qt.Key.Key_Equal:
            self._change_zoom(0.25)
        elif k == Qt.Key.Key_Minus:
            self._change_zoom(-0.25)
        elif k == Qt.Key.Key_R:
            self._reset_zoom()
        elif k == Qt.Key.Key_F:
            self._toggle_favorite()
        elif k == Qt.Key.Key_I:
            self._toggle_info()
        elif k == Qt.Key.Key_Delete:
            self._delete_current()
        else:
            super().keyPressEvent(event)


# ============================================================
#                    Photo Gallery Page
# ============================================================
class PhotoGalleryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("galleryPage")
        self._folder = ""
        self._files = []
        self._thumb_index = 0
        self._icon_size = 180
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(14)

        head = QHBoxLayout()
        title = QLabel("Photo Gallery")
        title.setObjectName("heading")
        _static_label(title)
        head.addWidget(title)
        head.addStretch()

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setObjectName("miniLabel")
        _static_label(self.folder_label)
        head.addWidget(self.folder_label)
        layout.addLayout(head)

        toolbar = QFrame()
        toolbar.setObjectName("card")
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(18, 14, 18, 14)
        tb_lay.setSpacing(12)

        open_btn = QPushButton("  Open Folder")
        open_btn.setObjectName("openButton")
        open_btn.setIcon(load_icon("folder-open.png"))
        open_btn.setIconSize(QSize(20, 20))
        open_btn.setFixedHeight(42)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._open_folder)
        tb_lay.addWidget(open_btn)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(load_icon("refresh.png"))
        refresh_btn.setIconSize(QSize(20, 20))
        refresh_btn.setObjectName("iconBtn")
        refresh_btn.setFixedSize(42, 42)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        tb_lay.addWidget(refresh_btn)

        tb_lay.addSpacing(20)

        sort_lbl = QLabel("Sort")
        sort_lbl.setObjectName("fieldLabel")
        tb_lay.addWidget(sort_lbl)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Date", "Size"])
        self.sort_combo.setObjectName("dlCombo")
        self.sort_combo.setFixedHeight(38)
        self.sort_combo.setFixedWidth(120)
        self.sort_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_combo.currentTextChanged.connect(self._apply_sort)
        tb_lay.addWidget(self.sort_combo)

        tb_lay.addSpacing(16)

        zoom_lbl = QLabel("Size")
        zoom_lbl.setObjectName("fieldLabel")
        tb_lay.addWidget(zoom_lbl)

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(100, 320)
        self.size_slider.setValue(self._icon_size)
        self.size_slider.setFixedWidth(160)
        self.size_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        tb_lay.addWidget(self.size_slider)

        tb_lay.addStretch()

        self.count_label = QLabel("0 images")
        self.count_label.setObjectName("miniLabel")
        _static_label(self.count_label)
        tb_lay.addWidget(self.count_label)

        layout.addWidget(toolbar)

        self.grid = QListWidget()
        self.grid.setObjectName("galleryGrid")
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setIconSize(QSize(self._icon_size, self._icon_size))
        self.grid.setGridSize(QSize(self._icon_size + 24, self._icon_size + 54))
        self.grid.setSpacing(10)
        self.grid.setWordWrap(True)
        self.grid.setUniformItemSizes(True)
        self.grid.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.grid.itemDoubleClicked.connect(self._open_viewer)
        layout.addWidget(self.grid, 1)

        self.empty_label = QLabel(
            "No folder selected.\nClick  'Open Folder'  to browse your images."
        )
        self.empty_label.setObjectName("miniLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        self._size_timer = QTimer(self)
        self._size_timer.setSingleShot(True)
        self._size_timer.setInterval(300)
        self._size_timer.timeout.connect(self._reload_all_thumbs)

    def _open_folder(self):
        start_dir = self._folder or str(Path.home() / "Pictures")
        folder = QFileDialog.getExistingDirectory(self, "Choose folder", start_dir)
        if folder:
            self._set_folder(folder)

    def _refresh(self):
        if self._folder:
            self._set_folder(self._folder)

    def _set_folder(self, folder: str):
        self._folder = folder
        self.folder_label.setText(folder)
        self._files = []
        try:
            for p in Path(folder).iterdir():
                if p.is_file() and p.suffix.lower() in IMAGE_EXT:
                    self._files.append(str(p))
        except Exception as e:
            print(f"⚠️  Gallery read error: {e}")
        self._apply_sort()

    def _apply_sort(self):
        mode = self.sort_combo.currentText() if hasattr(self, "sort_combo") else "Name"
        if mode == "Name":
            self._files.sort(key=lambda p: Path(p).name.lower())
        elif mode == "Date":
            self._files.sort(key=lambda p: QFileInfo(p).lastModified(), reverse=True)
        elif mode == "Size":
            self._files.sort(key=lambda p: QFileInfo(p).size(), reverse=True)
        self._populate_grid()

    def _populate_grid(self):
        self.grid.clear()
        self._thumb_index = 0

        if not self._files:
            self.empty_label.setVisible(True)
            self.count_label.setText("0 images")
            return
        self.empty_label.setVisible(False)
        self.count_label.setText(f"{len(self._files)} images")

        for path in self._files:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            item.setToolTip(path)
            item.setIcon(QIcon())
            self.grid.addItem(item)

        QTimer.singleShot(0, self._load_thumbnails_batch)

    def _make_thumbnail(self, path: str, target: int) -> QPixmap:
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid() and (size.width() > target or size.height() > target):
            scaled = size.scaled(QSize(target, target), Qt.AspectRatioMode.KeepAspectRatio)
            reader.setScaledSize(scaled)
        img = reader.read()
        if img.isNull():
            return QPixmap()
        pix = QPixmap.fromImage(img)
        return pix.scaled(target, target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

    def _load_thumbnails_batch(self):
        if self._thumb_index >= len(self._files):
            return
        end = min(self._thumb_index + 6, len(self._files))
        for i in range(self._thumb_index, end):
            item = self.grid.item(i)
            if item is None:
                continue
            path = self._files[i]
            pix = self._make_thumbnail(path, self._icon_size)
            if not pix.isNull():
                item.setIcon(QIcon(pix))
        self._thumb_index = end
        QTimer.singleShot(15, self._load_thumbnails_batch)

    def _on_size_changed(self, value: int):
        self._icon_size = value
        self.grid.setIconSize(QSize(value, value))
        self.grid.setGridSize(QSize(value + 24, value + 54))
        self._size_timer.start()

    def _reload_all_thumbs(self):
        if not self._files:
            return
        target = self._icon_size
        for i, path in enumerate(self._files):
            item = self.grid.item(i)
            if item is None:
                continue
            pix = self._make_thumbnail(path, target)
            if not pix.isNull():
                item.setIcon(QIcon(pix))

    def _open_viewer(self, item):
        idx = self.grid.row(item)
        if 0 <= idx < len(self._files):
            viewer = PhotoViewer(self._files, idx, self)
            viewer.exec()
            remaining = [f for f in self._files if Path(f).exists()]
            if len(remaining) != len(self._files):
                self._files = remaining
                self._populate_grid()


# ============================================================
#              Convert Worker
# ============================================================
class ConvertWorker(QThread):
    file_started = Signal(int)
    file_progress = Signal(int, int)
    file_finished = Signal(int, bool, str)
    all_done = Signal(int, int)

    def __init__(self, files, out_dir: str, target_fmt: str):
        super().__init__()
        self.files = files
        self.out_dir = out_dir
        self.target_fmt = target_fmt.lower()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _duration(self, path: str) -> float:
        if not FFPROBE_PATH:
            return 0.0
        try:
            out = subprocess.run(
                [str(FFPROBE_PATH), "-v", "error",
                 "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1",
                 path],
                capture_output=True, text=True, timeout=15,
            )
            return float(out.stdout.strip() or 0)
        except Exception:
            return 0.0

    def _build_cmd(self, inp: str, out: str) -> list:
        fmt = self.target_fmt
        base = [str(FFMPEG_PATH), "-y", "-hide_banner", "-loglevel", "error",
                "-i", inp]

        # ---------- Audio ----------
        if fmt == "mp3":
            return base + ["-vn", "-c:a", "libmp3lame", "-q:a", "2",
                           "-progress", "pipe:1", out]
        if fmt == "m4a":
            return base + ["-vn", "-c:a", "aac", "-b:a", "192k",
                           "-progress", "pipe:1", out]
        if fmt == "wav":
            return base + ["-vn", "-c:a", "pcm_s16le",
                           "-progress", "pipe:1", out]
        if fmt == "ogg":
            return base + ["-vn", "-c:a", "libvorbis", "-q:a", "5",
                           "-progress", "pipe:1", out]
        if fmt == "flac":
            return base + ["-vn", "-c:a", "flac", "-compression_level", "5",
                           "-progress", "pipe:1", out]

        # ---------- Image ----------
        if fmt in ("jpg", "jpeg"):
            return base + ["-q:v", "2", out]
        if fmt == "png":
            return base + [out]
        if fmt == "webp":
            return base + ["-q:v", "80", out]
        if fmt == "bmp":
            return base + [out]
        if fmt == "tiff":
            return base + [out]
        if fmt == "gif":
            return base + ["-vf", "fps=10,scale=480:-1:flags=lanczos", out]
        if fmt == "ico":
            return base + [
                "-vf",
                "scale=256:256:force_original_aspect_ratio=decrease,"
                "pad=256:256:(ow-iw)/2:(oh-ih)/2:color=#00000000",
                "-frames:v", "1",
                out,
            ]

        # ---------- Video ----------
        if fmt == "mp4":
            return base + ["-c:v", "libx264", "-crf", "23", "-preset", "fast",
                           "-c:a", "aac", "-b:a", "192k",
                           "-movflags", "+faststart", "-progress", "pipe:1", out]
        if fmt == "mkv":
            return base + ["-c:v", "libx264", "-crf", "23", "-preset", "fast",
                           "-c:a", "aac", "-b:a", "192k",
                           "-progress", "pipe:1", out]
        if fmt == "webm":
            return base + ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
                           "-c:a", "libopus", "-progress", "pipe:1", out]
        if fmt == "avi":
            return base + ["-c:v", "mpeg4", "-q:v", "5",
                           "-c:a", "libmp3lame", "-q:a", "3",
                           "-progress", "pipe:1", out]
        if fmt == "mov":
            return base + ["-c:v", "libx264", "-crf", "23", "-preset", "fast",
                           "-c:a", "aac", "-b:a", "192k",
                           "-progress", "pipe:1", out]

        return base + [out]

    def run(self):
        if not FFMPEG_AVAILABLE:
            for i in range(len(self.files)):
                self.file_finished.emit(i, False, "FFmpeg not available")
            self.all_done.emit(0, len(self.files))
            return

        ok_count = 0
        fail_count = 0

        for i, inp in enumerate(self.files):
            if self._cancelled:
                self.file_finished.emit(i, False, "Cancelled")
                fail_count += 1
                continue

            self.file_started.emit(i)

            stem = Path(inp).stem
            out = str(Path(self.out_dir) / f"{stem}.{self.target_fmt}")

            if os.path.abspath(inp) == os.path.abspath(out):
                out = str(Path(self.out_dir) / f"{stem}_converted.{self.target_fmt}")

            ftype = get_file_type(inp)
            duration = 0.0
            if ftype in ("video", "audio"):
                duration = self._duration(inp)

            cmd = self._build_cmd(inp, out)

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                )

                last_pct = -1
                for line in proc.stdout:
                    if self._cancelled:
                        proc.terminate()
                        break
                    line = line.strip()
                    if line.startswith("out_time_ms=") and duration > 0:
                        try:
                            us = int(line.split("=", 1)[1])
                            sec = us / 1_000_000.0
                            pct = max(0, min(100, int(sec / duration * 100)))
                            if pct != last_pct:
                                last_pct = pct
                                self.file_progress.emit(i, pct)
                        except Exception:
                            pass
                    elif line == "progress=end":
                        self.file_progress.emit(i, 100)

                proc.wait(timeout=5)

                if self._cancelled:
                    self.file_finished.emit(i, False, "Cancelled")
                    fail_count += 1
                    try:
                        if os.path.exists(out):
                            os.remove(out)
                    except Exception:
                        pass
                    continue

                if proc.returncode == 0 and os.path.exists(out):
                    self.file_progress.emit(i, 100)
                    self.file_finished.emit(i, True, "Done")
                    ok_count += 1
                else:
                    err = ""
                    try:
                        err = proc.stderr.read()[-200:]
                    except Exception:
                        pass
                    self.file_finished.emit(i, False, err or "FFmpeg error")
                    fail_count += 1

            except FileNotFoundError:
                self.file_finished.emit(i, False, "FFmpeg not found")
                fail_count += 1
            except Exception as e:
                self.file_finished.emit(i, False, str(e)[:120])
                fail_count += 1

        self.all_done.emit(ok_count, fail_count)


# ============================================================
#              Convert Item Widget
# ============================================================
class ConvertItemWidget(QFrame):
    remove_requested = Signal()

    def __init__(self, path: str):
        super().__init__()
        self.setObjectName("convertItem")
        self.setMinimumHeight(78)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.path = path

        ftype = get_file_type(path)
        self._file_type = ftype

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(10)

        type_icon = QLabel()
        icon = load_icon(get_type_icon_name(ftype))
        if not icon.isNull():
            type_icon.setPixmap(icon.pixmap(22, 22))
        type_icon.setFixedSize(24, 24)
        top.addWidget(type_icon)

        self.name_label = QLabel(Path(path).name)
        self.name_label.setObjectName("cvName")
        self.name_label.setToolTip(path)
        self.name_label.setMinimumWidth(0)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        top.addWidget(self.name_label, 1)

        try:
            size_str = _fmt_size(QFileInfo(path).size())
        except Exception:
            size_str = "—"
        self.size_label = QLabel(size_str)
        self.size_label.setObjectName("cvSize")
        self.size_label.setMinimumWidth(60)
        top.addWidget(self.size_label)

        self.type_badge = QLabel(ftype.upper())
        self.type_badge.setObjectName("cvBadge")
        self.type_badge.setFixedHeight(22)
        self.type_badge.setMinimumWidth(60)
        self.type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self.type_badge)

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setObjectName("cvRemove")
        self.remove_btn.setFixedSize(22, 22)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Remove from queue")
        self.remove_btn.clicked.connect(self.remove_requested.emit)
        top.addWidget(self.remove_btn)

        layout.addLayout(top)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setObjectName("cvProgress")
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("cvStatus")
        self.status_label.setMinimumWidth(0)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.status_label)

    def set_running(self):
        self.status_label.setText("Converting...")
        self.progress.setValue(0)

    def set_progress(self, pct: int):
        self.progress.setValue(pct)

    def set_done(self, success: bool, msg: str):
        if success:
            self.progress.setValue(100)
            self.status_label.setText(f"✓  {msg}")
            self.status_label.setStyleSheet("color: #16A34A; font-size: 11px; font-weight: 600;")
            self.remove_btn.setEnabled(False)
        else:
            self.status_label.setText(f"✕  {msg}")
            self.status_label.setStyleSheet("color: #DC2626; font-size: 11px; font-weight: 600;")


# ============================================================
#              Converter Page
# ============================================================
class ConverterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("converterPage")
        self._items = []
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(14)

        title = QLabel("Media Converter")
        title.setObjectName("heading")
        _static_label(title)
        layout.addWidget(title)

        sub = QLabel("Convert images, videos, and audio between formats using FFmpeg.")
        sub.setObjectName("description")
        _static_label(sub)
        layout.addWidget(sub)

        if not FFMPEG_AVAILABLE:
            warn = QLabel("⚠️  FFmpeg not found in assets/bin/ — conversion unavailable")
            warn.setStyleSheet("color: #B45309; background: #FEF3C7; padding: 10px 16px;"
                " border-radius: 10px; font-size: 13px; font-weight: 600;")
            layout.addWidget(warn)

        layout.addSpacing(4)

        body = QHBoxLayout()
        body.setSpacing(16)

        left_card = QFrame()
        left_card.setObjectName("card")
        lc = QVBoxLayout(left_card)
        lc.setContentsMargins(20, 18, 20, 18)
        lc.setSpacing(12)

        head_row = QHBoxLayout()
        files_title = QLabel("Files")
        files_title.setObjectName("cardTitle2")
        _static_label(files_title)
        head_row.addWidget(files_title)
        head_row.addStretch()

        add_btn = QPushButton("  Add Files")
        add_btn.setObjectName("openButton")
        add_btn.setIcon(load_icon("add-document.png"))
        add_btn.setIconSize(QSize(18, 18))
        add_btn.setFixedHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_files)
        head_row.addWidget(add_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("miniButtonSmall")
        clear_btn.setFixedHeight(38)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        head_row.addWidget(clear_btn)

        lc.addLayout(head_row)

        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setObjectName("queueScroll")
        self.files_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.files_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.files_scroll.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustIgnored)

        self.files_container = QWidget()
        self.files_container.setObjectName("queueContainer")
        self.files_container.setMinimumWidth(0)
        self.files_inner = QVBoxLayout(self.files_container)
        self.files_inner.setContentsMargins(0, 0, 0, 0)
        self.files_inner.setSpacing(8)
        self.files_inner.addStretch()
        self.files_scroll.setWidget(self.files_container)
        lc.addWidget(self.files_scroll, 1)

        self.empty_label = QLabel("No files yet.\nClick  'Add Files'  to begin.")
        self.empty_label.setObjectName("miniLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lc.addWidget(self.empty_label)

        body.addWidget(left_card, 3)

        right_card = QFrame()
        right_card.setObjectName("card")
        right_card.setFixedWidth(360)
        rc = QVBoxLayout(right_card)
        rc.setContentsMargins(24, 20, 24, 20)
        rc.setSpacing(14)

        s_title = QLabel("Output Settings")
        s_title.setObjectName("cardTitle2")
        _static_label(s_title)
        rc.addWidget(s_title)

        fmt_lbl = QLabel("TARGET FORMAT")
        fmt_lbl.setObjectName("fieldLabel")
        rc.addWidget(fmt_lbl)

        self.fmt_combo = QComboBox()
        self.fmt_combo.setObjectName("dlCombo")
        self.fmt_combo.setFixedHeight(42)
        self.fmt_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for f in IMAGE_FORMATS:
            self.fmt_combo.addItem(f.upper(), f)
        for f in VIDEO_FORMATS:
            self.fmt_combo.addItem(f.upper(), f)
        for f in AUDIO_FORMATS:
            self.fmt_combo.addItem(f.upper(), f)
        idx = self.fmt_combo.findData("mp4")
        if idx >= 0:
            self.fmt_combo.setCurrentIndex(idx)
        rc.addWidget(self.fmt_combo)

        hint = QLabel("Tip: pick a format compatible with your files.")
        hint.setObjectName("miniLabel")
        hint.setWordWrap(True)
        _static_label(hint)
        rc.addWidget(hint)

        folder_lbl = QLabel("OUTPUT FOLDER")
        folder_lbl.setObjectName("fieldLabel")
        rc.addWidget(folder_lbl)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.out_input = QLineEdit()
        self.out_input.setText(str(Path.home() / "Downloads" / "Evana Converted"))
        self.out_input.setObjectName("urlInput")
        self.out_input.setFixedHeight(42)
        path_row.addWidget(self.out_input, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedSize(90, 42)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_out)
        path_row.addWidget(browse_btn)
        rc.addLayout(path_row)

        rc.addSpacing(6)

        self.overall_label = QLabel("Ready")
        self.overall_label.setObjectName("miniLabel")
        rc.addWidget(self.overall_label)

        self.overall_bar = QProgressBar()
        self.overall_bar.setRange(0, 100)
        self.overall_bar.setValue(0)
        self.overall_bar.setTextVisible(False)
        self.overall_bar.setObjectName("cvProgress")
        self.overall_bar.setFixedHeight(8)
        rc.addWidget(self.overall_bar)

        rc.addStretch()

        self.convert_btn = QPushButton("  Convert All")
        self.convert_btn.setObjectName("downloadButton")
        self.convert_btn.setIcon(load_icon("file-conversion.png"))
        self.convert_btn.setIconSize(QSize(20, 20))
        self.convert_btn.setFixedHeight(52)
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.clicked.connect(self._start)
        rc.addWidget(self.convert_btn)

        body.addWidget(right_card, 2)
        layout.addLayout(body, 1)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose files to convert", "",
            "All supported (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff *.ico "
            "*.mp4 *.mkv *.webm *.avi *.mov *.flv *.wmv *.m4v "
            "*.mp3 *.m4a *.wav *.ogg *.flac *.aac);;"
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff *.ico);;"
            "Videos (*.mp4 *.mkv *.webm *.avi *.mov *.flv *.wmv *.m4v);;"
            "Audio (*.mp3 *.m4a *.wav *.ogg *.flac *.aac);;"
            "All Files (*)"
        )
        if not files:
            return
        for f in files:
            self._add_file(f)

    def _add_file(self, path: str):
        for _, p in self._items:
            if p == path:
                return
        widget = ConvertItemWidget(path)
        widget.remove_requested.connect(lambda w=widget, p=path: self._remove_item(w, p))
        self.files_inner.insertWidget(self.files_inner.count() - 1, widget)
        self._items.append((widget, path))
        self.empty_label.setVisible(False)

    def _remove_item(self, widget, path):
        for i, (w, p) in enumerate(self._items):
            if w is widget and p == path:
                self._items.pop(i)
                break
        widget.setParent(None)
        widget.deleteLater()
        if not self._items:
            self.empty_label.setVisible(True)

    def _clear_all(self):
        for w, _ in self._items:
            w.setParent(None)
            w.deleteLater()
        self._items.clear()
        self.empty_label.setVisible(True)
        self.overall_bar.setValue(0)
        self.overall_label.setText("Ready")

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Choose output folder", self.out_input.text())
        if d:
            self.out_input.setText(d)

    def _start(self):
        if not self._items:
            QMessageBox.information(self, "No files", "Add some files first.")
            return
        if not FFMPEG_AVAILABLE:
            QMessageBox.warning(self, "FFmpeg missing",
                "FFmpeg not found in assets/bin/.")
            return

        out_dir = self.out_input.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "No folder", "Please select an output folder.")
            return
        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot create folder:\n{e}")
            return

        target = self.fmt_combo.currentData()
        files = [p for _, p in self._items]

        for w, _ in self._items:
            w.progress.setValue(0)
            w.status_label.setText("Queued")
            w.status_label.setStyleSheet("")

        self.overall_bar.setValue(0)
        self.overall_label.setText(f"Converting {len(files)} files → {target.upper()}...")
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("  Converting...")

        self._worker = ConvertWorker(files, out_dir, target)
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_progress.connect(self._on_file_progress)
        self._worker.file_finished.connect(self._on_file_finished)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _on_file_started(self, idx: int):
        if 0 <= idx < len(self._items):
            self._items[idx][0].set_running()

    def _on_file_progress(self, idx: int, pct: int):
        if 0 <= idx < len(self._items):
            self._items[idx][0].set_progress(pct)
            total = len(self._items)
            if total > 0:
                done = sum(w.progress.value() for w, _ in self._items)
                self.overall_bar.setValue(int(done / total))

    def _on_file_finished(self, idx: int, success: bool, msg: str):
        if 0 <= idx < len(self._items):
            self._items[idx][0].set_done(success, msg)

    def _on_all_done(self, ok: int, fail: int):
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("  Convert All")
        self.overall_bar.setValue(100)
        if fail == 0:
            self.overall_label.setText(f"✓ All done — {ok} converted")
            self.overall_label.setStyleSheet("color: #16A34A; font-size: 11px; font-weight: 700;")
        else:
            self.overall_label.setText(f"Done — {ok} ok, {fail} failed")
            self.overall_label.setStyleSheet("color: #DC2626; font-size: 11px; font-weight: 700;")
            # ============================================================
#                    Main Window — Evana
# ============================================================
class Evana(QMainWindow):
    SIDEBAR_EXPANDED = 290
    SIDEBAR_COLLAPSED = 100
    ANIM_DURATION = 380
    FADE_DURATION = 240
    TOGGLE_SIZE = 42
    NAV_HEIGHT = 54

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evana")
        # ✅ أيقونة النافذة
        icon_file = ICONS_DIR.parent / "evana_icon.ico"
        if not icon_file.exists():
            icon_file = ICONS_DIR.parent / "evana_icon.png"
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)

        self.sidebar_expanded = True

        root = QWidget()
        root.setObjectName("rootWidget")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(self.SIDEBAR_EXPANDED)

        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(20, 22, 20, 22)
        side_layout.setSpacing(0)

        # ---- Top row: toggle + theme button ----
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(6)

        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setObjectName("toggleButton")
        self.toggle_btn.setFixedSize(self.TOGGLE_SIZE, self.TOGGLE_SIZE)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setToolTip("Show / Hide sidebar")
        self.toggle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        toggle_row.addWidget(self.toggle_btn)

        toggle_row.addStretch()

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setFixedSize(self.TOGGLE_SIZE, self.TOGGLE_SIZE)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self._update_theme_button_label()
        toggle_row.addWidget(self.theme_btn)

        side_layout.addLayout(toggle_row)

        side_layout.addSpacing(14)

        # ---- Logo ----
        self.logo_container = QWidget()
        self.logo_container.setFixedHeight(46)
        self.logo_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        logo_row = QHBoxLayout(self.logo_container)
        logo_row.setContentsMargins(2, 0, 0, 0)
        self.logo_text = QLabel("Evana")
        self.logo_text.setObjectName("logo")
        _static_label(self.logo_text)
        logo_row.addWidget(self.logo_text)
        logo_row.addStretch()
        side_layout.addWidget(self.logo_container)

        side_layout.addSpacing(34)

        # ---- Pages ----
        self.pages = QStackedWidget()
        self.pages.setObjectName("pagesArea")
        self.buttons = []

        self.sections = [
            ("house-chimney.png", "Home"),
            ("play-circle.png", "Video Player"),
            ("down-to-line.png", "Video Downloader"),
            ("file-conversion.png", "Media Converter"),
            ("gallery.png", "Photo Gallery"),
        ]

        for index, (icon_name, name) in enumerate(self.sections):
            btn = QPushButton(f"  {name}")
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(load_icon(icon_name))
            btn.setIconSize(QSize(24, 24))
            btn.setFixedHeight(self.NAV_HEIGHT)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            # نتذكر اسم الأيقونة عشان نحدّثها عند تغيير الثيم
            btn.setProperty("evana_icon", icon_name)
            btn.clicked.connect(lambda checked=False, i=index: self.show_page(i))
            side_layout.addWidget(btn)
            side_layout.addSpacing(4)
            self.buttons.append(btn)

            if index == 1:
                page = self._build_video_launcher_page()
            elif index == 2:
                page = DownloaderPage()
            elif index == 3:
                page = ConverterPage()
            elif index == 4:
                page = PhotoGalleryPage()
            else:
                page = self._build_page(index, name)
            self.pages.addWidget(page)

        side_layout.addStretch()

        # ---- Footer ----
        self.footer_container = QWidget()
        self.footer_container.setFixedHeight(20)
        self.footer_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        foot_row = QHBoxLayout(self.footer_container)
        foot_row.setContentsMargins(2, 0, 0, 0)
        self.footer_label = QLabel("Evana  •  v1.1.0")
        self.footer_label.setObjectName("footer")
        _static_label(self.footer_label)
        foot_row.addWidget(self.footer_label)
        foot_row.addStretch()
        side_layout.addWidget(self.footer_container)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages, 1)

        self._apply_styles()

        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self._on_escape_pressed)

        self.show_page(0, animate=False)

    # ==========================================================
    #              Theme
    # ==========================================================
    def _update_theme_button_label(self):
        if CURRENT_THEME == "dark":
            self.theme_btn.setText("☀")
            self.theme_btn.setToolTip("Switch to light mode")
        else:
            self.theme_btn.setText("🌙")
            self.theme_btn.setToolTip("Switch to dark mode")

    def toggle_theme(self):
        new_theme = "light" if CURRENT_THEME == "dark" else "dark"
        set_theme(new_theme)             # يحدّث الحالة + يمسح كاش الأيقونات
        self._update_theme_button_label()
        self._refresh_all_icons()        # ← يعيد تحميل كل الأيقونات بالثيم الجديد
        self._apply_styles()             # ← يعيد بناء كل الـ CSS

    def _refresh_all_icons(self):
        """يعيد تحميل الأيقونات لكل الأزرار اللي عندها خاصية evana_icon"""
        for btn in self.findChildren(QPushButton):
            name = btn.property("evana_icon")
            if name:
                icon = load_icon(name)
                btn.setIcon(icon)
                if not icon.isNull():
                    btn.setIconSize(QSize(24, 24))

    # ==========================================================
    #              Video Player Page
    # ==========================================================
    def _build_video_launcher_page(self):
        page = QWidget()
        page.setObjectName("playerPage")
        self.player_page_layout = QVBoxLayout(page)
        self.player_page_layout.setContentsMargins(30, 26, 30, 26)
        self.player_page_layout.setSpacing(14)

        self.player_header = QWidget()
        header = QHBoxLayout(self.player_header)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        heading = QLabel("Video Player")
        heading.setObjectName("heading")
        _static_label(heading)
        header.addWidget(heading)
        header.addStretch()

        self.player_open_btn = QPushButton("  Open Video")
        self.player_open_btn.setObjectName("openButton")
        self.player_open_btn.setIcon(load_icon("play-circle(1).png"))
        self.player_open_btn.setIconSize(QSize(20, 20))
        self.player_open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.player_open_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.player_open_btn.setProperty("evana_icon", "play-circle(1).png")
        self.player_open_btn.clicked.connect(self._open_files)
        header.addWidget(self.player_open_btn)

        self.player_page_layout.addWidget(self.player_header)

        self.player_body_layout = QHBoxLayout()
        self.player_body_layout.setSpacing(14)

        self.player_widget = VideoPlayerWidget()
        self.player_widget.fullscreen_toggled.connect(self._on_fullscreen_toggle)
        self.player_widget.prev_requested.connect(self._play_prev)
        self.player_widget.next_requested.connect(self._play_next)
        self.player_body_layout.addWidget(self.player_widget, 1)

        self.playlist_frame = QFrame()
        self.playlist_frame.setObjectName("playlistFrame")
        self.playlist_frame.setFixedWidth(300)

        pl_layout = QVBoxLayout(self.playlist_frame)
        pl_layout.setContentsMargins(16, 16, 16, 16)
        pl_layout.setSpacing(10)

        pl_header = QHBoxLayout()
        pl_title = QLabel("Playlist")
        pl_title.setObjectName("playlistTitle")
        _static_label(pl_title)
        pl_header.addWidget(pl_title)
        pl_header.addStretch()

        add_pl = QPushButton("+")
        add_pl.setObjectName("miniButton")
        add_pl.setFixedSize(28, 28)
        add_pl.setCursor(Qt.CursorShape.PointingHandCursor)
        add_pl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        add_pl.setToolTip("Add files")
        add_pl.clicked.connect(self._open_files)
        pl_header.addWidget(add_pl)

        rem_pl = QPushButton("−")
        rem_pl.setObjectName("miniButton")
        rem_pl.setFixedSize(28, 28)
        rem_pl.setCursor(Qt.CursorShape.PointingHandCursor)
        rem_pl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        rem_pl.setToolTip("Remove selected")
        rem_pl.clicked.connect(self._remove_selected)
        pl_header.addWidget(rem_pl)

        pl_layout.addLayout(pl_header)

        self.playlist = QListWidget()
        self.playlist.setObjectName("playlistWidget")
        self.playlist.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.playlist.itemDoubleClicked.connect(self._play_from_playlist)
        pl_layout.addWidget(self.playlist, 1)

        self.player_body_layout.addWidget(self.playlist_frame)
        self.player_page_layout.addLayout(self.player_body_layout, 1)

        return page

    def _on_fullscreen_toggle(self, enter: bool):
        if enter:
            self.player_page_layout.setContentsMargins(0, 0, 0, 0)
            self.player_page_layout.setSpacing(0)
            self.player_body_layout.setContentsMargins(0, 0, 0, 0)
            self.player_body_layout.setSpacing(0)
            self.sidebar.hide()
            self.player_header.hide()
            self.playlist_frame.hide()
            self.showFullScreen()
            self.player_widget.set_fullscreen(True)
        else:
            self.showNormal()
            self.player_page_layout.setContentsMargins(30, 26, 30, 26)
            self.player_page_layout.setSpacing(14)
            self.player_body_layout.setSpacing(14)
            self.sidebar.show()
            self.player_header.show()
            self.playlist_frame.show()
            self.player_widget.set_fullscreen(False)

    def _on_escape_pressed(self):
        if self.isFullScreen():
            self._on_fullscreen_toggle(False)

    def _open_files(self):
        if not MULTIMEDIA_OK:
            return
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose video files", "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.m4v);;"
            "All Files (*)")
        if not files:
            return
        was_empty = self.playlist.count() == 0
        for f in files:
            item = QListWidgetItem(Path(f).name)
            item.setData(Qt.ItemDataRole.UserRole, f)
            item.setToolTip(f)
            self.playlist.addItem(item)
        if was_empty:
            self.playlist.setCurrentRow(0)
            self._play_current()

    def _play_from_playlist(self, item):
        self._play_current()

    def _play_current(self):
        item = self.playlist.currentItem()
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()
        self.player_widget.load_media(name, path)

    def _play_prev(self):
        n = self.playlist.count()
        if n == 0:
            return
        row = (self.playlist.currentRow() - 1) % n
        self.playlist.setCurrentRow(row)
        self._play_current()

    def _play_next(self):
        n = self.playlist.count()
        if n == 0:
            return
        row = (self.playlist.currentRow() + 1) % n
        self.playlist.setCurrentRow(row)
        self._play_current()

    def _remove_selected(self):
        for item in self.playlist.selectedItems():
            self.playlist.takeItem(self.playlist.row(item))

    # ==========================================================
    #              Home / Placeholder
    # ==========================================================
    def _build_page(self, index, name):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(48, 46, 48, 46)
        page_layout.setSpacing(20)

        heading = QLabel(name)
        heading.setObjectName("heading")
        _static_label(heading)
        page_layout.addWidget(heading)

        description = QLabel(f"{name} — Features coming soon.")
        description.setObjectName("description")
        description.setWordWrap(True)
        _static_label(description)
        page_layout.addWidget(description)

        if index == 0:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(34, 34, 34, 34)
            card_layout.setSpacing(16)

            welcome = QLabel("Welcome to Evana!")
            welcome.setObjectName("cardTitle")
            _static_label(welcome)

            info = QLabel(
                "Player, downloader, converter, and gallery.\n"
                "Everything you need in one application.")
            info.setObjectName("description")
            info.setWordWrap(True)
            _static_label(info)

            card_layout.addWidget(welcome)
            card_layout.addWidget(info)

            page_layout.addSpacing(12)
            page_layout.addWidget(card)

            quick_title = QLabel("Explore your tools")
            quick_title.setObjectName("sectionTitle")
            _static_label(quick_title)
            page_layout.addSpacing(14)
            page_layout.addWidget(quick_title)

            for target, icon_name, title, detail in [
                (1, "play-circle.png", "Video Player", "Play your local video files"),
                (2, "down-to-line.png", "Video Downloader", "Download videos from URLs"),
                (3, "file-conversion.png", "Media Converter", "Convert images, audio, and video"),
                (4, "gallery.png", "Photo Gallery", "Browse your image collection"),
            ]:
                quick = QPushButton(f"   {title}")
                quick.setObjectName("quickButton")
                quick.setCursor(Qt.CursorShape.PointingHandCursor)
                quick.setIcon(load_icon(icon_name))
                quick.setIconSize(QSize(26, 26))
                quick.setToolTip(detail)
                quick.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                quick.setProperty("evana_icon", icon_name)
                quick.clicked.connect(lambda checked=False, i=target: self.show_page(i))
                page_layout.addWidget(quick)

        page_layout.addStretch()
        return page

    # ==========================================================
    #              THE MAGIC — CSS with palette injection
    # ==========================================================
    def _apply_styles(self):
        """
        يستبدل __KEY__ في قالب CSS بقيمة اللون من اللوحة الحالية.
        هذي الطريقة أأمن من f-string لأنها ما تحتاج escape للأقواس {}.
        """
        css_template = """
            QMainWindow { background: __BG_APP__; }
            QWidget {
                color: __TEXT__;
                font-family: "JetBrains Mono", "Segoe UI", sans-serif;
                font-size: 17px;
            }
            #rootWidget { background: __BG_APP__; }
            #pagesArea, #pagesArea > QWidget { background: __BG_APP__; }

            /* ============ Sidebar ============ */
            #sidebar {
                background: __BG_CARD__;
                border-right: 1px solid __BORDER__;
            }
            #sidebar QWidget, #sidebar QLabel, #logoContainer, #footerContainer {
                background: transparent;
                border: none;
            }
            #logo { color: __ACCENT__; font-size: 26px; font-weight: 800; letter-spacing: 1px; }

            #toggleButton, #themeButton {
                background: transparent;
                color: __TEXT_SECOND__;
                border: none;
                border-radius: 10px;
                font-size: 22px;
                font-family: "Segoe UI Symbol", "Arial Unicode MS",
                             "JetBrains Mono", sans-serif;
            }
            #toggleButton:hover, #themeButton:hover {
                background: __BG_HOVER__;
                color: __ACCENT__;
            }
            #toggleButton:pressed, #themeButton:pressed { background: __BG_HOVER3__; }

            #navButton {
                background: transparent;
                color: __TEXT_SECOND__;
                text-align: left;
                padding: 0 14px 0 18px;
                border: none;
                border-left: 4px solid transparent;
                border-radius: 0;
                font-size: 16px;
                font-weight: 500;
            }
            #navButton:hover { background: __BG_HOVER__; color: __ACCENT__; }
            #navButton:checked {
                background: transparent;
                color: __ACCENT__;
                font-weight: 700;
                border-left: 4px solid __ACCENT__;
                padding-left: 14px;
            }

            /* ============ Typography ============ */
            #heading { font-size: 40px; font-weight: 800; color: __TEXT__; background: transparent; }
            #description { color: __TEXT_MUTED__; font-size: 18px; background: transparent; }
            #cardTitle { font-size: 28px; font-weight: 700; color: __TEXT__; background: transparent; }
            #cardTitle2 { font-size: 19px; font-weight: 700; color: __TEXT__; background: transparent; }
            #sectionTitle { font-size: 22px; font-weight: 700; color: __TEXT__; background: transparent; }
            #footer { color: __TEXT_FAINT__; font-size: 11px; background: transparent; }
            #miniLabel { color: __TEXT_FAINT__; font-size: 11px; font-weight: 600; background: transparent; }
            #fieldLabel { color: __TEXT_SECOND__; font-size: 11px; font-weight: 700;
                background: transparent; letter-spacing: 1px; }

            /* ============ Cards ============ */
            #card {
                background: __BG_CARD__;
                border: 1px solid __BORDER2__;
                border-radius: 20px;
            }
            #quickButton {
                background: __BG_CARD__;
                color: __TEXT_BTN__;
                text-align: left;
                padding: 18px 22px;
                border: 1px solid __BORDER2__;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 500;
            }
            #quickButton:hover {
                background: __BG_HOVER2__;
                border-color: __BORDER_HOVER__;
                color: __ACCENT__;
            }

            #openButton {
                background: __ACCENT__;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 12px 22px;
                font-size: 15px;
                font-weight: 700;
            }
            #openButton:hover { background: __ACCENT_HOVER__; }
            #openButton:pressed { background: __ACCENT_PRESS__; }

            /* ============ Playlist ============ */
            #playlistFrame {
                background: __BG_CARD__;
                border: 1px solid __BORDER2__;
                border-radius: 16px;
            }
            #playlistTitle { color: __TEXT__; font-size: 17px; font-weight: 700; }
            #playlistWidget { background: transparent; border: none; outline: none; font-size: 14px; }
            #playlistWidget::item { padding: 10px 8px; border-radius: 8px; color: __TEXT_BTN__; }
            #playlistWidget::item:hover { background: __BG_HOVER__; color: __ACCENT__; }
            #playlistWidget::item:selected {
                background: __BG_SELECTED__;
                color: __ACCENT__;
                font-weight: 600;
            }

            #miniButton {
                background: __BG_HOVER__;
                color: __ACCENT__;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
            }
            #miniButton:hover { background: __BG_HOVER3__; }
            #miniButtonSmall {
                background: __BG_HOVER__;
                color: __ACCENT__;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 12px;
            }
            #miniButtonSmall:hover { background: __BG_HOVER3__; }

            /* ============ Inputs ============ */
            #urlInput {
                background: __BG_INPUT__;
                border: 1px solid __BORDER2__;
                border-radius: 12px;
                padding: 0 16px;
                font-size: 14px;
                color: __TEXT__;
            }
            #urlInput:focus { border-color: __ACCENT__; background: __BG_CARD__; }

            #iconBtn {
                background: __BG_INPUT__;
                border: 1px solid __BORDER2__;
                border-radius: 12px;
                font-size: 18px;
                color: __TEXT_SECOND__;
            }
            #iconBtn:hover {
                background: __BG_HOVER2__;
                border-color: __BORDER_HOVER__;
                color: __ACCENT__;
            }

            #fetchButton {
                background: __BG_CARD__;
                color: __ACCENT__;
                border: 2px solid __ACCENT__;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 700;
            }
            #fetchButton:hover { background: __BG_HOVER2__; }
            #fetchButton:disabled {
                color: __TEXT_FAINT__;
                border-color: __BORDER2__;
                background: __BG_INPUT__;
            }
            #fetchStatus {
                color: __TEXT_SECOND__;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                padding: 2px 0;
            }
            #thumbLabel {
                background: __BG_HOVER__;
                border-radius: 12px;
                color: __TEXT_FAINT__;
                font-size: 12px;
            }
            #videoTitle { color: __TEXT__; font-size: 17px; font-weight: 700; background: transparent; }
            #videoMeta { color: __TEXT_MUTED__; font-size: 13px; font-weight: 500; background: transparent; }

            /* ============ Big Buttons (Download / Convert) ============ */
            #downloadButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 __ACCENT__, stop:1 __ACCENT2__);
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-size: 17px;
                font-weight: 700;
            }
            #downloadButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 __ACCENT_HOVER__, stop:1 __ACCENT_HOV2__);
            }
            #downloadButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 __ACCENT_PRESS__, stop:1 __ACCENT_PRS2__);
            }

            /* ============ Combos ============ */
            #dlCombo {
                background: __BG_INPUT__;
                border: 1px solid __BORDER2__;
                border-radius: 10px;
                padding: 0 12px;
                font-size: 14px;
                color: __TEXT__;
            }
            #dlCombo:hover { border-color: __BORDER_HOVER__; }
            #dlCombo::drop-down { border: none; width: 24px; }
            #dlCombo::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid __TEXT_SECOND__;
                margin-right: 10px;
            }
            #dlCombo QAbstractItemView {
                background: __BG_CARD__;
                border: 1px solid __BORDER2__;
                border-radius: 10px;
                selection-background-color: __BG_HOVER2__;
                selection-color: __ACCENT__;
                color: __TEXT__;
                padding: 4px;
                outline: none;
            }

            #browseBtn {
                background: __BG_HOVER__;
                color: __ACCENT__;
                border: 1px solid __BORDER2__;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }
            #browseBtn:hover { background: __BG_HOVER3__; border-color: __BORDER_HOVER__; }

            /* ============ Checkboxes ============ */
            #dlCheck { color: __TEXT_BTN__; font-size: 14px; font-weight: 500; spacing: 8px; }
            #dlCheck::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 2px solid __TEXT_FAINT__;
                background: __BG_CARD__;
            }
            #dlCheck::indicator:hover { border-color: __ACCENT__; }
            #dlCheck::indicator:checked { background: __ACCENT__; border-color: __ACCENT__; }

            /* ============ Scroll ============ */
            #queueScroll { background: transparent; border: none; }
            #queueScroll QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
            #queueScroll QScrollBar::handle:vertical {
                background: __BG_SCROLL__;
                border-radius: 4px;
                min-height: 30px;
            }
            #queueScroll QScrollBar::handle:vertical:hover { background: __BG_SCROLL_H__; }
            #queueScroll QScrollBar::add-line:vertical,
            #queueScroll QScrollBar::sub-line:vertical { height: 0; background: transparent; }
            #queueContainer { background: transparent; }

            /* ============ Download Item ============ */
            #downloadItem {
                background: __BG_INPUT__;
                border: 1px solid __BORDER2__;
                border-radius: 14px;
            }
            #dlTitle { color: __TEXT__; font-size: 13px; font-weight: 700; background: transparent; }
            #dlCancel {
                background: transparent;
                border: none;
                color: __TEXT_FAINT__;
                font-size: 14px;
                border-radius: 12px;
            }
            #dlCancel:hover { background: __BG_SELECTED__; color: __ACCENT__; }
            #dlProgress {
                background: __BORDER2__;
                border: none;
                border-radius: 4px;
            }
            #dlProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 __ACCENT__, stop:1 __ACCENT2__);
                border-radius: 4px;
            }
            #dlStatus { color: __TEXT_MUTED__; font-size: 11px; background: transparent; }
            #dlPercent { color: __ACCENT__; font-size: 12px; font-weight: 700; background: transparent; }

            /* ============ Gallery ============ */
            #galleryGrid {
                background: __BG_CARD__;
                border: 1px solid __BORDER2__;
                border-radius: 16px;
                padding: 12px;
                outline: none;
            }
            #galleryGrid::item {
                color: __TEXT_BTN__;
                border-radius: 12px;
                padding: 4px;
            }
            #galleryGrid::item:hover { background: __BG_HOVER2__; color: __ACCENT__; }
            #galleryGrid::item:selected { background: __BG_SELECTED__; color: __ACCENT__; }
            #galleryGrid QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
            #galleryGrid QScrollBar::handle:vertical {
                background: __BG_SCROLL__;
                border-radius: 5px;
                min-height: 30px;
            }
            #galleryGrid QScrollBar::handle:vertical:hover { background: __BG_SCROLL_H__; }
            #galleryGrid QScrollBar::add-line:vertical,
            #galleryGrid QScrollBar::sub-line:vertical { height: 0; background: transparent; }

            /* ============ Converter ============ */
            #convertItem {
                background: __BG_INPUT__;
                border: 1px solid __BORDER2__;
                border-radius: 12px;
            }
            #cvName { color: __TEXT__; font-size: 13px; font-weight: 700; background: transparent; }
            #cvSize { color: __TEXT_MUTED__; font-size: 12px; background: transparent; }
            #cvBadge {
                background: __BG_SELECTED__;
                color: __ACCENT__;
                font-size: 10px;
                font-weight: 800;
                border-radius: 6px;
                padding: 0 8px;
                letter-spacing: 1px;
            }
            #cvRemove {
                background: transparent;
                border: none;
                color: __TEXT_FAINT__;
                font-size: 12px;
                border-radius: 11px;
            }
            #cvRemove:hover { background: __BG_SELECTED__; color: __ACCENT__; }
            #cvProgress {
                background: __BORDER2__;
                border: none;
                border-radius: 3px;
            }
            #cvProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 __ACCENT__, stop:1 __ACCENT2__);
                border-radius: 3px;
            }
            #cvStatus { color: __TEXT_MUTED__; font-size: 11px; background: transparent; }

            /* ============ Global ============ */
            QLabel {
                background: transparent;
                border: none;
                outline: none;
                selection-background-color: transparent;
                selection-color: __TEXT__;
            }
            QPushButton:focus { outline: none; }

            QToolTip {
                background-color: __BG_CARD__;
                color: __TEXT__;
                border: 1px solid __BORDER__;
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
            }

            QMessageBox {
                background-color: __BG_CARD__;
            }
            QMessageBox QLabel {
                color: __TEXT__;
                background: transparent;
            }
            QMessageBox QPushButton {
                background: __BG_HOVER__;
                color: __TEXT__;
                border: 1px solid __BORDER2__;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: __ACCENT__;
                color: #FFFFFF;
                border-color: __ACCENT__;
            }
        """

        # Inject palette colors
        palette = get_palette()
        css = css_template
        for key, value in palette.items():
            css = css.replace(f"__{key}__", value)

        self.setStyleSheet(css)

    # ==========================================================
    #              Sidebar animation
    # ==========================================================
    def _animate_fade(self, widget, visible):
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(1.0 if visible else 0.0)
            widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(self.FADE_DURATION)
        anim.setStartValue(effect.opacity())
        anim.setEndValue(1.0 if visible else 0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        widget._fade_anim = anim

    def _animate_maxwidth(self, widget, visible, full_width=600):
        anim = QPropertyAnimation(widget, b"maximumWidth", widget)
        anim.setDuration(self.FADE_DURATION)
        anim.setStartValue(widget.maximumWidth())
        anim.setEndValue(full_width if visible else 0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        widget._mw_anim = anim

    def _fade_sidebar_text(self, visible):
        for w in (self.logo_text, self.footer_label):
            self._animate_fade(w, visible)
            self._animate_maxwidth(w, visible)

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        target = self.SIDEBAR_EXPANDED if self.sidebar_expanded else self.SIDEBAR_COLLAPSED

        group = QParallelAnimationGroup(self)
        for prop in (b"minimumWidth", b"maximumWidth"):
            anim = QPropertyAnimation(self.sidebar, prop)
            anim.setDuration(self.ANIM_DURATION)
            anim.setStartValue(self.sidebar.width())
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            group.addAnimation(anim)
        group.start()
        self._sidebar_anim = group

        if self.sidebar_expanded:
            QTimer.singleShot(int(self.ANIM_DURATION * 0.45),
                lambda: self._fade_sidebar_text(True) if self.sidebar_expanded else None)
        else:
            self._fade_sidebar_text(False)

        if not self.sidebar_expanded:
            self._update_nav_text(False)
        else:
            QTimer.singleShot(int(self.ANIM_DURATION * 0.5),
                lambda: self._update_nav_text(True) if self.sidebar_expanded else None)

    def _update_nav_text(self, expanded):
        for i, btn in enumerate(self.buttons):
            name = self.sections[i][1]
            btn.setText(f"  {name}" if expanded else "")
            if expanded:
                btn.setStyleSheet("text-align: left; padding: 0 14px 0 18px;")
            else:
                btn.setStyleSheet("text-align: center; padding: 0; border-left: 4px solid transparent;")

    def show_page(self, index, animate=True):
        if animate and index == self.pages.currentIndex():
            return
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        if not animate:
            return
        page = self.pages.currentWidget()
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        self._fade = QPropertyAnimation(effect, b"opacity", self)
        self._fade.setDuration(300)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()

    def closeEvent(self, event):
        event.accept()


# ============================================================
#                    Entry Point
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_fonts()

    # ✅ أيقونة التطبيق (تعمل مع PyInstaller ومع التطوير)
    def _get_icon_path():
        """يجد مسار الأيقونة سواء شغّلنا من الكود أو من EXE"""
        # 1. جرّب المسار النسبي لمجلد البرنامج
        if getattr(sys, 'frozen', False):
            # داخل EXE
            base = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
            p = base / "assets" / "evana_icon.ico"
            if p.exists():
                return p
            p = base / "assets" / "evana_icon.png"
            if p.exists():
                return p
        else:
            # تطوير
            p = ICONS_DIR.parent / "evana_icon.ico"
            if p.exists():
                return p
            p = ICONS_DIR.parent / "evana_icon.png"
            if p.exists():
                return p
        return None

    icon_path = _get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
        print(f"✅ App icon: {icon_path}")
    else:
        print("⚠️  App icon not found")

    # ✅ مهم على ويندوز: يجعل الأيقونة تظهر في Taskbar
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = 'evana.media.app.1.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    window = Evana()
    window.show()
    sys.exit(app.exec())

    print(f"🎨 Theme: {CURRENT_THEME}")

    if not MULTIMEDIA_OK:
        print("⚠️  QtMultimedia not available. Install: pip install PySide6-Addons")
    if not YTDLP_OK:
        print("⚠️  yt-dlp not available. Install: pip install yt-dlp")

    window = Evana()
    window.show()
    sys.exit(app.exec())