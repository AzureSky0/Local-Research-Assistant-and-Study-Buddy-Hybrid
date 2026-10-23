"""Write packaging/loci.ico from the logo in app/ui/theme/app_icon.py.

Run after changing the logo, then commit the .ico:

    python scripts/make_app_icon.py

The .ico holds the logo drawn separately at each Windows icon size, so
small sizes stay sharp instead of being shrunk from one large image.
PyInstaller puts it on Loci.exe and Inno Setup on the installer.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QIODevice  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from app.ui.theme.app_icon import ICON_SIZES, app_icon_pixmap  # noqa: E402

ICO_PATH = ROOT / "packaging" / "loci.ico"


def png_image(size: int) -> Image.Image:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    app_icon_pixmap(size).save(buffer, "PNG")
    return Image.open(io.BytesIO(bytes(buffer.data().data()))).convert("RGBA")


def main() -> None:
    _app = QGuiApplication(sys.argv)  # QPixmap needs a GUI application
    images = [png_image(size) for size in ICON_SIZES]
    largest = images[-1]
    largest.save(
        ICO_PATH,
        format="ICO",
        sizes=[(size, size) for size in ICON_SIZES],
        append_images=images[:-1],
    )
    print(f"Wrote {ICO_PATH} ({', '.join(str(size) for size in ICON_SIZES)} px)")


if __name__ == "__main__":
    main()
