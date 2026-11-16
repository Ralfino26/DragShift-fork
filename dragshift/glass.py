"""Visual system: colour tokens, the Qt stylesheet and the glass surface painter.

Glass (a refracted snapshot of what's behind) is used only for surfaces that float over
other apps: the radial menu and notifications. Editor windows are solid."""
from __future__ import annotations

import ctypes
import os
import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap)

# ---------------------------------------------------------------- tokens
TEXT = "#f2f2f3"
TEXT_DIM = "#a1a1a8"            # 7:1 on SURFACE
SURFACE = "#1c1c1f"             # window background
SURFACE_RAISED = "#26262b"      # controls, cards
SURFACE_HOVER = "#303036"
BORDER = "#36363d"
ACCENT = "#2f6fed"              # white text on it: 4.6:1
ACCENT_HOVER = "#3d7bf2"
ACCENT_PRESSED = "#285fd0"
SUCCESS = "#4cc38a"
WARNING = "#e8b04b"
DANGER = "#f06a6a"

GLASS_TINT = (22, 22, 26)       # neutral tint laid over refracted glass


def glass_tint(alpha: int) -> QColor:
    return QColor(*GLASS_TINT, alpha)


def blur_pixmap(pm: QPixmap, radius: int = 18) -> QPixmap:
    """Fast frosted blur: downscale, light box blur via repeated scaling, upscale."""
    if pm.isNull():
        return pm
    w, h = pm.width(), pm.height()
    f = max(2, radius // 3)
    small = pm.scaled(max(1, w // f), max(1, h // f), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    small = small.scaled(max(1, w // (f * 2)), max(1, h // (f * 2)), Qt.IgnoreAspectRatio,
                         Qt.SmoothTransformation)
    return small.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def paint_glass(p: QPainter, path: QPainterPath, backdrop: QPixmap | None = None,
                backdrop_offset: QPointF = QPointF(0, 0), tint: QColor | None = None,
                rim: bool = True, highlight: float = 1.0) -> None:
    """Paint a glass surface filling `path`: backdrop, tint, a faint top sheen and a hairline rim."""
    rect = path.boundingRect()
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setClipPath(path)
    if backdrop is not None and not backdrop.isNull():
        p.save()
        c = rect.center()
        p.translate(c)
        p.scale(1.04, 1.04)          # slight magnification reads as refraction
        p.translate(-c)
        p.drawPixmap(backdrop_offset, backdrop)
        p.restore()
    p.fillPath(path, tint or glass_tint(110))
    sheen = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + rect.height() * 0.5))
    sheen.setColorAt(0.0, QColor(255, 255, 255, int(28 * highlight)))
    sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillPath(path, sheen)
    p.restore()

    if rim:
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        edge = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        edge.setColorAt(0.0, QColor(255, 255, 255, int(110 * min(1.0, highlight))))
        edge.setColorAt(1.0, QColor(255, 255, 255, 40))
        p.setPen(QPen(QBrush(edge), 1.0))
        p.drawPath(path)
        p.restore()


# ---------------------------------------------------------------- Qt stylesheet
_QSS = f"""
* {{ color: {TEXT}; font-family: "@FONT@"; font-size: 10pt; }}
QWidget#glassRoot {{ background: transparent; }}
QLabel {{ background: transparent; }}
QLabel#title {{ font-size: 12pt; font-weight: 600; }}
QLabel#dim {{ color: {TEXT_DIM}; font-size: 9pt; }}
QLabel#section {{ color: {TEXT_DIM}; font-size: 9pt; font-weight: 600; padding: 6px 0 0 0; margin: 0; }}
QLabel#big {{ font-size: 16pt; font-weight: 600; }}
QLabel#good {{ color: {SUCCESS}; font-weight: 600; }}
QLabel#warn {{ color: {WARNING}; font-weight: 600; }}
QLabel#stepNum {{
  background: {SURFACE_RAISED}; border: 1px solid {BORDER}; border-radius: 12px;
  color: {TEXT_DIM}; font-weight: 600; font-size: 9pt;
}}

QPushButton {{
  background: {SURFACE_RAISED}; border: 1px solid {BORDER}; border-radius: 6px;
  padding: 5px 12px; min-height: 18px;
}}
QPushButton:hover {{ background: {SURFACE_HOVER}; }}
QPushButton:pressed {{ background: {SURFACE}; }}
QPushButton:disabled {{ color: #6b6b72; }}
QPushButton:checked {{ background: #32394a; border-color: {ACCENT}; }}
QPushButton:focus {{ outline: none; }}
QPushButton#primary {{
  background: {ACCENT}; border: 1px solid {ACCENT}; color: #ffffff; font-weight: 600; padding: 5px 16px;
}}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; border-color: {ACCENT_HOVER}; }}
QPushButton#primary:pressed {{ background: {ACCENT_PRESSED}; }}
QPushButton#primary:disabled {{ background: #2a3550; border-color: #2a3550; color: #8a93a8; }}
QPushButton#chrome {{ background: transparent; border: none; padding: 4px; border-radius: 6px; }}
QPushButton#chrome:hover {{ background: {SURFACE_HOVER}; }}
QPushButton#swatch {{
  border-radius: 12px; padding: 0; min-width: 24px; max-width: 24px; min-height: 24px; max-height: 24px;
  border: 1px solid rgba(255,255,255,0.18);
}}
QPushButton#swatch:checked {{ border: 2px solid #ffffff; }}

QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{
  background: #ffffff; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; border: none;
}}

QSpinBox, QLineEdit, QComboBox {{
  background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 8px;
  selection-background-color: {ACCENT}; min-height: 18px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url(@ICONS@/chevron-down.png); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
  background: {SURFACE_RAISED}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; outline: none;
}}
QSpinBox {{ padding-right: 20px; }}
QSpinBox::up-button, QSpinBox::down-button {{ border: none; width: 18px; background: transparent; }}
QSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-arrow {{ image: url(@ICONS@/chevron-up.png); width: 10px; height: 10px; }}
QSpinBox::down-arrow {{ image: url(@ICONS@/chevron-down.png); width: 10px; height: 10px; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
  width: 16px; height: 16px; border-radius: 4px; border: 1px solid #55555e; background: {SURFACE};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url(@ICONS@/check.png); }}

QFrame#card {{ background: {SURFACE_RAISED}; border: 1px solid {BORDER}; border-radius: 8px; }}
QTableWidget {{
  background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 6px; gridline-color: {BORDER};
  alternate-background-color: {SURFACE_RAISED};
}}
QHeaderView {{ background: transparent; }}
QTableCornerButton::section {{ background: transparent; border: none; }}
QHeaderView::section {{
  background: {SURFACE_RAISED}; border: none; border-bottom: 1px solid {BORDER}; padding: 5px 8px; font-weight: 600;
}}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: #4a4a52; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{ background: {SURFACE_RAISED}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 6px; }}
QMenu {{ background: {SURFACE_RAISED}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 4px; }}
QMenu::item:selected {{ background: {ACCENT}; color: #ffffff; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 6px; }}
"""

_ICON_DIR: str | None = None


def _icon_dir() -> str:
    """Write the few icons the stylesheet references (check, chevrons) to a cache folder."""
    global _ICON_DIR
    if _ICON_DIR is None:
        import tempfile
        from . import icons
        d = os.path.join(tempfile.gettempdir(), f"dragshift-ui-{os.getuid() if hasattr(os, 'getuid') else 0}")
        os.makedirs(d, exist_ok=True)
        icons.save_png("check", os.path.join(d, "check.png"), 16, "#ffffff", 2.6)
        icons.save_png("chevron-down", os.path.join(d, "chevron-down.png"), 12, TEXT_DIM, 2.2)
        icons.save_png("chevron-up", os.path.join(d, "chevron-up.png"), 12, TEXT_DIM, 2.2)
        _ICON_DIR = d.replace("\\", "/")
    return _ICON_DIR


def qss() -> str:
    """The stylesheet, with a font family that is really installed (see util.ui_family)."""
    from .util import ui_family
    return _QSS.replace("@FONT@", ui_family(False)).replace("@ICONS@", _icon_dir())


def __getattr__(name):        # keep `glass.QSS` working
    if name == "QSS":
        return qss()
    raise AttributeError(name)



def qimage_from_pil(im) -> QImage:
    im = im.convert("RGBA")
    data = im.tobytes("raw", "RGBA")
    qi = QImage(data, im.width, im.height, im.width * 4, QImage.Format_RGBA8888)
    return qi.copy()  # detach from the Python buffer


def pil_from_qimage(qi: QImage):
    from PIL import Image
    qi = qi.convertToFormat(QImage.Format_RGBA8888)
    ptr = qi.constBits()
    return Image.frombuffer("RGBA", (qi.width(), qi.height()), bytes(ptr), "raw", "RGBA",
                            qi.bytesPerLine(), 1).copy()


def rounded_rect_path(r: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(r, radius, radius)
    return path


# ---------------------------------------------------------------- live liquid backing
def exclude_from_capture(hwnd: int) -> bool:
    """Hide a window from screen capture (Windows 10 2004+), so we can re-capture what's
    behind it while it's visible. Skipped while recording demos (it would hide us)."""
    import os
    if sys.platform == "darwin":
        from . import platform_mac
        return platform_mac.OK      # macOS: we capture "below our window" instead
    if sys.platform != "win32" or os.environ.get("DRAGSHIFT_RECORDING"):
        return False
    try:
        return bool(ctypes.windll.user32.SetWindowDisplayAffinity(ctypes.c_void_p(hwnd), 0x11))
    except Exception:
        return False


from PySide6.QtCore import QObject, QRect, QRunnable, QThreadPool, QTimer, Signal  # noqa: E402


class _LiquidSig(QObject):
    done = Signal(int, QImage, bool)


class _LiquidJob(QRunnable):
    def __init__(self, serial, backdrop, w, h, radius, style):
        super().__init__()
        self.args = (serial, backdrop, w, h, radius, style)
        self.sig = _LiquidSig()

    def run(self):
        serial, backdrop, w, h, radius, style = self.args
        try:
            from . import liquid
            sdf = liquid.sdf_rounded_rect(w, h, 0.5, 0.5, w - 0.5, h - 0.5, radius)
            img, light = liquid.render(backdrop, sdf, style)
            try:
                self.sig.done.emit(serial, qimage_from_pil(img), light)
            except RuntimeError:
                pass  # window closed before the render finished
        except Exception:
            import traceback
            traceback.print_exc()


def grab_screen(x: int, y: int, w: int, h: int, below_window: int = 0):
    """Screen pixels under a rect (logical coords) as a PIL image of size w×h.
    macOS: native capture that leaves out the drag picture (and `below_window` and above)."""
    if sys.platform == "darwin":
        from . import platform_mac
        if platform_mac.OK:
            im = platform_mac.capture(x, y, w, h, below_window)
            if im is not None:
                return im
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QGuiApplication
    scr = QGuiApplication.screenAt(QPoint(x + w // 2, y + h // 2)) or QGuiApplication.primaryScreen()
    g = scr.geometry()
    try:
        shot = scr.grabWindow(0, x - g.x(), y - g.y(), w, h)
    except Exception:
        return None
    if shot.isNull():
        return None
    return pil_from_qimage(shot.toImage().scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))


class LiquidBacking(QObject):
    """Keeps a refracted snapshot of whatever is behind a rounded-rect window."""
    changed = Signal()

    def __init__(self, widget, radius: float, style=None):
        super().__init__(widget)
        from .liquid import GlassStyle
        self.w = widget
        self.radius = radius
        self.style = style or GlassStyle(blur=16, strength=14, bezel=20)
        self.image: QImage | None = None
        self.is_light = False
        self.excluded = False
        self._serial = 0
        self._debounce = QTimer(self, singleShot=True, interval=140, timeout=self.refresh)

    def capture_at(self, rect: QRect):
        """Grab the screen under `rect` (call before the window is shown, or when excluded)."""
        below = 0
        if sys.platform == "darwin" and self.w.isVisible():
            from . import platform_mac
            below = platform_mac.window_number(self.w)
        pil = grab_screen(rect.x(), rect.y(), rect.width(), rect.height(), below)
        if pil is None:
            return
        self._serial += 1
        job = _LiquidJob(self._serial, pil, rect.width(), rect.height(), self.radius, self.style)
        from .util import keep, release
        job.sig.done.connect(lambda *a, j=job: (release(j), self._done(*a)))
        QThreadPool.globalInstance().start(keep(job))

    def _done(self, serial, img, light):
        if serial == self._serial:
            self.image, self.is_light = img, light
            self.changed.emit()

    def moved(self):
        """Window moved/resized: refresh once it settles (only possible when excluded)."""
        if self.excluded:
            self.image = None if self.image is not None and self.image.size() != self.w.size() else self.image
            self._debounce.start()

    def refresh(self):
        if self.excluded and self.w.isVisible():
            self.capture_at(self.w.frameGeometry())


# ---------------------------------------------------------------- drag-image hiding
class hidden_drag_images:
    """While dragging, Windows draws a translucent picture of the file under the cursor.
    Hide it for the instant we capture the screen behind the menu, so it doesn't get frozen
    into the glass, then show it again. We hide every visible top-level window of another
    process that sits under the cursor and is layered + click-through (that is what drag
    images are), plus the known drag-image classes."""

    CLASSES = ("SysDragImage", "DragImageWindow", "DragWindow")
    WS_EX_LAYERED, WS_EX_TRANSPARENT = 0x00080000, 0x00000020

    def __init__(self, point=None):
        self.point = point
        self.hwnds: list[int] = []
        self.info: list[str] = []
        self.rects: list[tuple[int, int, int, int]] = []   # screen px, for inpainting

    def __enter__(self):
        if sys.platform != "win32":
            return self
        try:
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            user32.GetWindowLongW.restype = ctypes.c_long
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            mypid = os.getpid()
            found = []
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def cb(hwnd, _):
                h = ctypes.c_void_p(hwnd)
                if not user32.IsWindowVisible(h):
                    return True
                r = wintypes.RECT()
                user32.GetWindowRect(h, ctypes.byref(r))
                near = r.left - 40 <= pt.x <= r.right + 40 and r.top - 40 <= pt.y <= r.bottom + 40
                if not near or (r.right - r.left) > 900 or (r.bottom - r.top) > 900:
                    return True
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                if pid.value == mypid:
                    return True
                buf = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(h, buf, 64)
                ex = user32.GetWindowLongW(h, -20)  # GWL_EXSTYLE
                drag_like = (ex & self.WS_EX_LAYERED) and (ex & self.WS_EX_TRANSPARENT)
                if buf.value in self.CLASSES or drag_like:
                    found.append(hwnd)
                    self.rects.append((r.left, r.top, r.right, r.bottom))
                    self.info.append(f"{buf.value} ex=0x{ex & 0xffffffff:08x} {r.right - r.left}x{r.bottom - r.top}")
                return True
            user32.EnumWindows(WNDENUMPROC(cb), 0)
            for h in found:
                user32.ShowWindow(ctypes.c_void_p(h), 0)  # SW_HIDE
            self.hwnds = found
            if found:
                ctypes.windll.gdi32.GdiFlush()
                ctypes.windll.dwmapi.DwmFlush()  # wait for the compositor to drop them
                ctypes.windll.dwmapi.DwmFlush()
        except Exception as e:
            self.info.append(f"error: {e}")
        return self

    def __exit__(self, *exc):
        if self.hwnds:
            try:
                for h in self.hwnds:
                    ctypes.windll.user32.ShowWindow(ctypes.c_void_p(h), 8)  # SW_SHOWNA
            except Exception:
                pass
        return False


def inpaint_rects(im, rects, pad: int = 6):
    """Fill rectangles of a PIL image from their surroundings (normalised convolution):
    a smooth, colour-matched patch — invisible once refracted and blurred by the glass."""
    import numpy as np
    from PIL import Image, ImageFilter
    if not rects:
        return im
    rgb = im.convert("RGB")
    w, h = rgb.size
    mask = Image.new("L", (w, h), 255)
    from PIL import ImageDraw
    d = ImageDraw.Draw(mask)
    any_hit = False
    for (x0, y0, x1, y1) in rects:
        x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
        if x1 > x0 and y1 > y0:
            d.rectangle((x0, y0, x1, y1), fill=0)
            any_hit = True
    if not any_hit:
        return im
    a = np.asarray(rgb, np.float32)
    m = np.asarray(mask, np.float32)[..., None] / 255
    radius = 28
    num = np.asarray(Image.fromarray(np.clip(a * m, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius)), np.float32)
    den = np.asarray(mask.filter(ImageFilter.GaussianBlur(radius)), np.float32)[..., None] / 255
    fill = num / np.maximum(den, 1e-3)
    fill = np.asarray(Image.fromarray(np.clip(fill, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)
    # feather the seam: the glass bezel magnifies any hard edge into a visible line
    soft = np.asarray(mask.filter(ImageFilter.GaussianBlur(12)), np.float32)[..., None] / 255
    soft = np.minimum(soft, m)  # never let the drag picture bleed back in
    out = a * soft + fill * (1 - soft)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- no-compositor mode (XFCE etc.)
_NO_COMP = None


def no_compositor() -> bool:
    """Linux/X11 without a compositing manager: translucency would render black, so glass
    surfaces are cut to their exact shape with a window mask instead (XShape)."""
    global _NO_COMP
    if _NO_COMP is None:
        _NO_COMP = False
        if sys.platform.startswith("linux") and not os.environ.get("QT_QPA_PLATFORM", "").startswith("offscreen"):
            try:
                from . import platform_linux
                _NO_COMP = not platform_linux.composited()
            except Exception:
                _NO_COMP = False
    return _NO_COMP


def apply_shape(widget, path: QPainterPath):
    """Clip a top-level window to `path` when there's no compositor (no-op otherwise)."""
    if not no_compositor():
        return
    from PySide6.QtGui import QRegion
    region = QRegion()
    for poly in path.simplified().toFillPolygons():   # one polygon per separate piece
        region = region.united(QRegion(poly.toPolygon()))
    widget.setMask(region)
