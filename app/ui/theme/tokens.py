"""Design tokens: the single source of colors and typography for the UI.

Matches the v0.2 design (UI redesign canvas). Widgets
and the stylesheet read from here instead of hard-coding values.
"""

from __future__ import annotations

from dataclasses import dataclass

# Typography -----------------------------------------------------------

# IBM Plex is preferred; Windows falls back to Segoe UI / Cascadia Mono.
FONT_FAMILIES = ["IBM Plex Sans", "Segoe UI", "Helvetica Neue", "sans-serif"]
MONO_FAMILIES = ["IBM Plex Mono", "Cascadia Mono", "Consolas", "monospace"]

FONT_SIZE = 14

# Neutrals ---------------------------------------------------------------

INK = "#16181D"
SUBTLE = "#3F4452"
MUTED = "#5B6170"
BACKGROUND = "#F4F5F7"
SURFACE = "#FFFFFF"
BORDER = "#E3E5EA"
BORDER_STRONG = "#D5D8DF"
DIVIDER = "#EEF0F3"
NEUTRAL_SOFT = "#ECEEF2"
BACKDROP = "#8A8F9C"

# Accent -----------------------------------------------------------------

ACCENT = "#2F4FCB"
ACCENT_HOVER = "#2843B3"
ACCENT_PRESSED = "#1F3699"
ACCENT_SOFT = "#E8EDFC"
ACCENT_SELECTED_ROW = "#F0F3FD"
ACCENT_DASHED = "#B9C3EC"

# Danger -----------------------------------------------------------------

DANGER = "#9A3412"
DANGER_BORDER = "#E8C4B0"

# Toast ------------------------------------------------------------------

TOAST_BACKGROUND = INK
TOAST_TEXT = "#FFFFFF"
TOAST_SUCCESS = "#8FE0B5"
TOAST_LINK = "#B9C8FF"


@dataclass(frozen=True, slots=True)
class Swatch:
    """A foreground color with its soft background tint."""

    label: str
    color: str
    tint: str


# Workspace colors, keyed by the value stored in the database.
WORKSPACE_COLORS: dict[str, Swatch] = {
    "blue": Swatch("Blue", "#2F4FCB", "#E8EDFC"),
    "purple": Swatch("Purple", "#6D3FC0", "#EFE8FB"),
    "teal": Swatch("Teal", "#1F6B5C", "#E1F2EE"),
    "orange": Swatch("Orange", "#9A4A12", "#FBEBDD"),
    "rose": Swatch("Rose", "#A3264F", "#FBE6EE"),
    "graphite": Swatch("Graphite", "#3F4452", "#ECEEF2"),
}

DEFAULT_WORKSPACE_COLOR = "blue"


def workspace_swatch(color_key: str) -> Swatch:
    """Return the swatch for a stored workspace color."""
    return WORKSPACE_COLORS.get(color_key, WORKSPACE_COLORS[DEFAULT_WORKSPACE_COLOR])


# Document file-type badges.
FILE_TYPE_COLORS: dict[str, Swatch] = {
    "pdf": Swatch("PDF", "#8A1F43", "#FBE6EE"),
    "md": Swatch("MD", "#1F6B5C", "#E1F2EE"),
    "txt": Swatch("TXT", "#3F4452", "#ECEEF2"),
}


def file_type_swatch(file_type: str) -> Swatch:
    """Return the badge colors for a document file type."""
    return FILE_TYPE_COLORS.get(
        file_type,
        Swatch(file_type.upper(), SUBTLE, NEUTRAL_SOFT),
    )


# Status chips: (text color, background). Each status also has its own
# icon so it never relies on color alone.
STATUS_READY = Swatch("Ready", "#1F6B4A", "#E3F3EA")
STATUS_IN_PROGRESS = Swatch("In progress", "#1F3699", "#E8EDFC")
STATUS_NEUTRAL = Swatch("Neutral", "#3F4452", "#ECEEF2")
STATUS_PROBLEM = Swatch("Problem", "#8A2E0E", "#FDEBDD")
