from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.theme.app_icon import ICON_SIZES, app_icon, app_icon_pixmap

ROOT = Path(__file__).resolve().parents[2]


def test_logo_is_drawn_at_every_windows_size(qapp: QApplication) -> None:
    for size in ICON_SIZES:
        image = app_icon_pixmap(size).toImage()
        assert (image.width(), image.height()) == (size, size)
        # Corners stay transparent (rounded square); the centre is drawn.
        assert image.pixelColor(0, 0).alpha() == 0
        assert image.pixelColor(size // 2, size // 2).alpha() == 255

    assert not app_icon().isNull()


def test_windows_icon_file_is_present() -> None:
    # Regenerate with scripts/make_app_icon.py after changing the logo.
    ico = ROOT / "packaging" / "loci.ico"
    assert ico.read_bytes()[:4] == b"\x00\x00\x01\x00"
