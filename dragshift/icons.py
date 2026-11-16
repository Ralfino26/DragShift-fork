"""Line icons drawn with QPainter on a 24×24 grid (no SVG dependency: QtSvg isn't bundled).

    icons.paint(painter, "crop", QRectF(x, y, 20, 20), QColor("white"))
    button.setIcon(icons.icon("rotate-cw"))
"""
from __future__ import annotations

import math
from typing import Callable

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

Shape = tuple[QPainterPath, bool]          # (path, filled)


# ---------------------------------------------------------------- path helpers (24-unit grid)
def _poly(*pts: tuple[float, float], close: bool = False) -> QPainterPath:
    p = QPainterPath(QPointF(*pts[0]))
    for pt in pts[1:]:
        p.lineTo(QPointF(*pt))
    if close:
        p.closeSubpath()
    return p


def _line(x0, y0, x1, y1) -> QPainterPath:
    return _poly((x0, y0), (x1, y1))


def _rrect(x, y, w, h, r) -> QPainterPath:
    p = QPainterPath()
    p.addRoundedRect(QRectF(x, y, w, h), r, r)
    return p


def _circle(cx, cy, r) -> QPainterPath:
    p = QPainterPath()
    p.addEllipse(QPointF(cx, cy), r, r)
    return p


def _arrowhead(tip: tuple[float, float], angle_deg: float, size: float = 4.0, spread: float = 42) -> QPainterPath:
    """Open chevron at `tip`, pointing along `angle_deg` (screen coords, 0 = right, 90 = down)."""
    out = []
    for s in (-spread, spread):
        a = math.radians(angle_deg + 180 + s)
        out.append((tip[0] + size * math.cos(a), tip[1] + size * math.sin(a)))
    return _poly(out[0], tip, out[1])


def _arc_arrow(clockwise: bool) -> list[Shape]:
    r, c = 7.5, 12.0
    rect = QRectF(c - r, c - r, 2 * r, 2 * r)
    p = QPainterPath()
    # Qt arc angles: degrees, counter-clockwise from 3 o'clock
    start, sweep = (340.0, -290.0) if clockwise else (200.0, 290.0)
    p.arcMoveTo(rect, start)
    p.arcTo(rect, start, sweep)
    end = math.radians(start + sweep)
    tip = (c + r * math.cos(end), c - r * math.sin(end))
    # tangent in screen coords for the direction of travel
    d = (math.sin(end), math.cos(end)) if clockwise else (-math.sin(end), -math.cos(end))
    return [(p, False), (_arrowhead(tip, math.degrees(math.atan2(d[1], d[0])), 4.2), False)]


def _dot(cx, cy, r=1.1) -> Shape:
    return _circle(cx, cy, r), True


# ---------------------------------------------------------------- the set
def _eye_off() -> list[Shape]:
    eye = QPainterPath(QPointF(2.5, 12))
    eye.quadTo(QPointF(12, 2.5), QPointF(21.5, 12))
    eye.quadTo(QPointF(12, 21.5), QPointF(2.5, 12))
    return [(eye, False), (_circle(12, 12, 3), False), (_line(4, 4, 20, 20), False)]


def _lock() -> list[Shape]:
    shackle = QPainterPath(QPointF(8, 11))
    shackle.lineTo(8, 8)
    shackle.arcTo(QRectF(8, 4, 8, 8), 180, -180)
    shackle.lineTo(16, 11)
    return [(_rrect(4.5, 11, 15, 10, 2), False), (shackle, False)]


def _undo() -> list[Shape]:
    p = QPainterPath(QPointF(4.5, 9.5))
    p.lineTo(14.5, 9.5)
    p.arcTo(QRectF(9, 9.5, 11, 11), 90, -180)
    p.lineTo(10, 20.5)
    return [(p, False), (_poly((8.5, 5.5), (4.5, 9.5), (8.5, 13.5)), False)]


def _sliders() -> list[Shape]:
    s = []
    for y, x in ((6.5, 15.5), (12, 8.5), (17.5, 14)):
        if x - 2.2 > 3.5:
            s.append((_line(3.5, y, x - 2.2, y), False))
        s.append((_line(x + 2.2, y, 20.5, y), False))
        s.append((_circle(x, y, 2.2), False))
    return s


def _scissors() -> list[Shape]:
    return [(_circle(6.5, 6.5, 2.8), False), (_circle(6.5, 17.5, 2.8), False),
            (_line(8.6, 15.6, 20, 5), False), (_line(14.2, 13.8, 20, 19), False),
            (_line(8.6, 8.4, 11.6, 11.2), False)]


def _images() -> list[Shape]:
    back = QPainterPath(QPointF(3.5, 8))
    back.lineTo(3.5, 18)
    back.quadTo(3.5, 20.5, 6, 20.5)
    back.lineTo(16, 20.5)
    return [(back, False), (_rrect(7, 3.5, 13.5, 13, 2), False), (_dot(11.2, 7.8, 1.3)),
            (_poly((7.3, 14.5), (11.5, 10.5), (15, 13.5), (17, 11.8), (20.3, 14.5)), False)]


def _highlighter() -> list[Shape]:
    return [(_poly((14, 4), (20, 10), (12.5, 17.5), (6.5, 11.5), close=True), False),
            (_poly((6.5, 11.5), (4, 17), (7, 20), (12.5, 17.5)), False),
            (_line(13, 21, 21, 21), False)]


def _pencil() -> list[Shape]:
    return [(_poly((16, 3.8), (20.2, 8), (8.5, 19.7), (3.5, 20.5), (4.3, 15.5), close=True), False),
            (_line(13.5, 6.3, 17.7, 10.5), False)]


def _step() -> list[Shape]:
    return [(_circle(12, 12, 9), False), (_poly((10.2, 9.4), (12.6, 7.8), (12.6, 16.4)), False),
            (_line(10.2, 16.4, 15, 16.4), False)]


def _wand() -> list[Shape]:
    return [(_line(4, 20, 14.5, 9.5), False), (_line(12.5, 8, 16, 11.5), False),
            (_line(18, 3, 18, 7), False), (_line(16, 5, 20, 5), False),
            (_line(19.5, 12, 19.5, 15), False), (_line(18, 13.5, 21, 13.5), False),
            (_line(9.5, 3.5, 9.5, 6.5), False), (_line(8, 5, 11, 5), False)]


def _flip() -> list[Shape]:
    s: list[Shape] = [(_line(12, y, 12, y + 2), False) for y in (3, 7, 11, 15, 19)]
    s.append((_poly((9, 6), (3, 18), (9, 18), close=True), False))
    s.append((_poly((15, 6), (21, 18), (15, 18), close=True), False))
    return s


def _flip_v() -> list[Shape]:
    s: list[Shape] = [(_line(x, 12, x + 2, 12), False) for x in (3, 7, 11, 15, 19)]
    s.append((_poly((6, 9), (18, 3), (18, 9), close=True), False))
    s.append((_poly((6, 15), (18, 21), (18, 15), close=True), False))
    return s


def _alert() -> list[Shape]:
    tri = _poly((12, 3.5), (21.5, 20), (2.5, 20), close=True)
    return [(tri, False), (_line(12, 9.5, 12, 13.8), False), _dot(12, 16.8)]


ICONS: dict[str, Callable[[], list[Shape]]] = {
    "close": lambda: [(_line(6.5, 6.5, 17.5, 17.5), False), (_line(17.5, 6.5, 6.5, 17.5), False)],
    "check": lambda: [(_poly((5, 12.5), (9.8, 17.2), (19, 7)), False)],
    "plus": lambda: [(_line(12, 5, 12, 19), False), (_line(5, 12, 19, 12), False)],
    "chevron-down": lambda: [(_poly((6, 9.5), (12, 15.5), (18, 9.5)), False)],
    "chevron-up": lambda: [(_poly((6, 14.5), (12, 8.5), (18, 14.5)), False)],
    "alert": _alert,
    "info": lambda: [(_circle(12, 12, 9), False), (_line(12, 11, 12, 16.5), False), _dot(12, 7.9)],
    "undo": _undo,
    # tools
    "compress": lambda: [(_poly((4, 14), (10, 14), (10, 20)), False), (_poly((20, 10), (14, 10), (14, 4)), False),
                         (_line(14, 10, 20.5, 3.5), False), (_line(3.5, 20.5, 10, 14), False)],
    "resize": lambda: [(_poly((15, 3.5), (20.5, 3.5), (20.5, 9)), False), (_poly((9, 20.5), (3.5, 20.5), (3.5, 15)), False),
                       (_line(20.5, 3.5, 14, 10), False), (_line(3.5, 20.5, 10, 14), False)],
    "crop": lambda: [(_poly((6.5, 2.5), (6.5, 17.5), (21.5, 17.5)), False),
                     (_poly((2.5, 6.5), (17.5, 6.5), (17.5, 21.5)), False)],
    "edit": _sliders,
    "annotate": _pencil,
    "redact": _eye_off,
    "add-bg": lambda: [(_rrect(3, 3, 18, 18, 3), False), (_rrect(7.5, 7.5, 9, 9, 1.5), False)],
    "metadata": lambda: ICONS["info"](),
    "split": _scissors,
    "rotate-cw": lambda: _arc_arrow(True),
    "rotate-ccw": lambda: _arc_arrow(False),
    "merge": lambda: [(_rrect(3.5, 3.5, 11, 11, 2), False), (_rrect(9.5, 9.5, 11, 11, 2), False)],
    "protect": _lock,
    "extract": _images,
    # annotate tools
    "arrow": lambda: [(_line(5, 19, 18.5, 5.5), False), (_poly((9.5, 5.5), (18.5, 5.5), (18.5, 14.5)), False)],
    "box": lambda: [(_rrect(4, 5, 16, 14, 2), False)],
    "circle": lambda: [(_circle(12, 12, 8.5), False)],
    "pen": _pencil,
    "marker": _highlighter,
    "text": lambda: [(_poly((5, 7.5), (5, 5), (19, 5), (19, 7.5)), False), (_line(12, 5, 12, 19), False),
                     (_line(9, 19, 15, 19), False)],
    "step": _step,
    # edit
    "auto": _wand,
    "flip-h": _flip,
    "flip-v": _flip_v,
}
_ROTATED: set[str] = set()


def paint(p: QPainter, name: str, rect: QRectF, color: QColor | str, stroke: float = 1.75) -> None:
    shapes = ICONS[name]()
    col = QColor(color)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(rect.topLeft())
    p.scale(rect.width() / 24.0, rect.height() / 24.0)
    if name in _ROTATED:
        p.translate(12, 12)
        p.rotate(90)
        p.translate(-12, -12)
    pen = QPen(col, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    for path, filled in shapes:
        if filled:
            p.setPen(Qt.NoPen)
            p.setBrush(col)
        else:
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    p.restore()


def _dpr() -> float:
    from PySide6.QtGui import QGuiApplication
    screens = QGuiApplication.screens()
    return max([s.devicePixelRatio() for s in screens] + [2.0])


def pixmap(name: str, size: int = 16, color: QColor | str = "#ffffff", stroke: float = 1.75) -> QPixmap:
    dpr = _dpr()
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.transparent)
    pm.setDevicePixelRatio(dpr)
    p = QPainter(pm)
    paint(p, name, QRectF(0, 0, size, size), color, stroke)
    p.end()
    return pm


def icon(name: str, size: int = 16, color: QColor | str = "#ffffff") -> QIcon:
    ic = QIcon()
    ic.addPixmap(pixmap(name, size, color), QIcon.Normal)
    dim = QColor(color)
    dim.setAlphaF(dim.alphaF() * 0.4)
    ic.addPixmap(pixmap(name, size, dim), QIcon.Disabled)
    return ic


def icon_size(size: int = 16) -> QSize:
    return QSize(size, size)


def save_png(name: str, path: str, size: int, color: QColor | str, stroke: float = 2.0) -> None:
    """Write an icon to disk for stylesheet `image: url(...)` rules."""
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    paint(p, name, QRectF(0, 0, size * dpr, size * dpr), color, stroke)
    p.end()
    pm.save(path, "PNG")
