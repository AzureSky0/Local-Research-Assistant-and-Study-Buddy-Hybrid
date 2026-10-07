"""Application-wide preferences saved in the user's data folder.

Preferences are a small JSON file rather than database rows because
they are read before the database is set up and are not tied to a
workspace.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.computer_profile import ComputerProfile, detect_profile
from app.core.paths import DATA_DIR

logger = logging.getLogger(__name__)

PREFERENCES_FILE = DATA_DIR / "preferences.json"


@dataclass(slots=True)
class UserPreferences:
    # None means "choose automatically from this computer".
    computer_profile: str | None = None

    @property
    def effective_profile(self) -> ComputerProfile:
        if self.computer_profile:
            try:
                return ComputerProfile(self.computer_profile)
            except ValueError:
                logger.warning("Unknown computer profile %r; detecting instead", self.computer_profile)

        return detect_profile()

    @property
    def is_automatic(self) -> bool:
        return self.computer_profile is None


def load_preferences(path: Path = PREFERENCES_FILE) -> UserPreferences:
    """Read preferences; a missing or damaged file gives the defaults."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return UserPreferences()
    except (OSError, ValueError) as error:
        logger.warning("Could not read preferences (%s); using defaults", error)
        return UserPreferences()

    known = {name: data[name] for name in UserPreferences.__dataclass_fields__ if name in data}
    return UserPreferences(**known)


def save_preferences(preferences: UserPreferences, path: Path = PREFERENCES_FILE) -> None:
    """Write preferences atomically, so a crash never leaves a half-written file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(preferences), indent=2), encoding="utf-8")
    temporary.replace(path)
