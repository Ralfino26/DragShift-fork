"""Shared fixtures: realistic test images (photo-like content, Display P3 profile, camera EXIF),
quality metrics, and an isolated, headless Qt."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
from PIL import Image

from dragshift import convert  # noqa: E402  (registers the HEIF opener)
from dragshift.util import CONFIG

P3_PATH = Path("/System/Library/ColorSync/Profiles/Display P3.icc")
REAL_PAGES_TO_PDF = convert._pages_to_pdf  # before the autouse guard below swaps it out


# ---------------------------------------------------------------- images
def photo(w: int = 640, h: int = 480, seed: int = 1, alpha: bool = False) -> Image.Image:
    """Smooth gradients + fine grain: compresses like a real photo, so quality numbers mean something."""
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.stack([128 + 100 * np.sin(xx / 37), 128 + 100 * np.cos(yy / 29),
                  128 + 80 * np.sin((xx + yy) / 53)], -1)
    a += np.random.default_rng(seed).normal(0, 3, a.shape)
    im = Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGB")
    if alpha:
        m = np.zeros((h, w), "uint8")
        m[h // 4: 3 * h // 4, w // 4: 3 * w // 4] = 255
        im.putalpha(Image.fromarray(m))
    return im


def marked(w: int = 300, h: int = 200) -> Image.Image:
    """Grey image with a red block in the top-left corner: shows whether pixels are upright."""
    im = Image.new("RGB", (w, h), (128, 128, 128))
    im.paste((255, 0, 0), (0, 0, w // 5, h // 5))
    return im


def rgb(path_or_im) -> np.ndarray:
    im = path_or_im if isinstance(path_or_im, Image.Image) else Image.open(path_or_im)
    if im.mode == "RGBA":
        im = convert.flatten(im)
    return np.asarray(im.convert("RGB"), dtype=float)


def psnr(a, b) -> float:
    a, b = rgb(a), rgb(b)
    assert a.shape == b.shape, (a.shape, b.shape)
    mse = np.mean((a - b) ** 2)
    return float("inf") if mse == 0 else float(10 * np.log10(255 ** 2 / mse))


def reencode(im: Image.Image, fmt: str, **kw) -> Image.Image:
    buf = io.BytesIO()
    im.save(buf, fmt, **kw)
    buf.seek(0)
    return Image.open(buf)


def camera_exif(orientation: int | None = None, gps: bool = True) -> Image.Exif:
    ex = Image.Exif()
    ex[0x010F] = "Apple"                       # Make
    ex[0x0110] = "iPhone 17 Pro"               # Model
    ex[0x0132] = "2026:10:01 12:00:00"         # DateTime
    if orientation:
        ex[0x0112] = orientation
    ifd = ex.get_ifd(0x8769)                   # Exif sub-IFD
    ifd[0x9003] = "2026:10:01 11:59:58"        # DateTimeOriginal
    ifd[0x829A] = 1 / 250                      # ExposureTime
    if gps:
        g = ex.get_ifd(0x8825)
        g.update({1: "N", 2: (52.0, 22.0, 30.0), 3: "E", 4: (4.0, 53.0, 10.0)})
    return ex


def exif_of(path) -> Image.Exif:
    with Image.open(path) as im:
        ex = im.getexif()
        ex.get_ifd(0x8769)  # read the sub-IFDs while the file is still open
        ex.get_ifd(0x8825)
        return ex


def has_gps(path) -> bool:
    return bool(exif_of(path).get_ifd(0x8825))


def date_taken(path):
    return exif_of(path).get_ifd(0x8769).get(0x9003)


def icc_desc(path) -> str | None:
    from PIL import ImageCms
    with Image.open(path) as im:
        icc = im.info.get("icc_profile")
    if not icc:
        return None
    return ImageCms.ImageCmsProfile(io.BytesIO(icc)).profile.profile_description.strip()


@pytest.fixture(scope="session")
def p3() -> bytes:
    if not P3_PATH.exists():
        pytest.skip("Display P3 profile not available on this OS")
    return P3_PATH.read_bytes()


def pytest_configure(config):
    config.addinivalue_line("markers", "office: drives a real office app (Pages / LibreOffice)")


@pytest.fixture(autouse=True)
def _no_office_apps(request, monkeypatch):
    """Only tests marked 'office' may launch Pages or LibreOffice (permission prompts, windows)."""
    if request.node.get_closest_marker("office") is None:
        monkeypatch.setattr(convert, "_pages_to_pdf", lambda *a: False)
        monkeypatch.setattr(convert, "_libreoffice_to_pdf", lambda *a: False)


@pytest.fixture(autouse=True)
def _config():
    saved = dict(CONFIG)
    CONFIG.update(output="next", jpg_quality=90, pdf_dpi=200)
    yield
    CONFIG.clear()
    CONFIG.update(saved)


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtCore import QCoreApplication, QStandardPaths
    from PySide6.QtWidgets import QApplication
    QStandardPaths.setTestModeEnabled(True)   # QSettings never touch the real preferences
    QCoreApplication.setOrganizationName("DragShiftTests")
    app = QApplication.instance() or QApplication([])
    yield app
