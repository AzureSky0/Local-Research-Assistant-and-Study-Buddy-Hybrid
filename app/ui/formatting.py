"""Human-friendly formatting for sizes, times and durations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def format_size(size_bytes: int) -> str:
    """Format a file size, for example 2.1 MB or 14 KB."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size = float(size_bytes)

    for unit in ("KB", "MB", "GB"):
        size /= 1024

        if size < 1024 or unit == "GB":
            if size >= 10 or unit == "KB":
                return f"{size:.0f} {unit}"
            return f"{size:.1f} {unit}"

    raise AssertionError("unreachable")


def format_relative_time(moment: datetime, now: datetime | None = None) -> str:
    """Describe how long ago something happened, for example '2 hours ago'."""

    now = now or datetime.now(UTC)
    seconds = (now - moment).total_seconds()

    if seconds < 60:
        return "just now"

    minutes = int(seconds // 60)
    if minutes < 60:
        return "1 minute ago" if minutes == 1 else f"{minutes} minutes ago"

    hours = minutes // 60
    if hours < 24:
        return "1 hour ago" if hours == 1 else f"{hours} hours ago"

    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "last week"
    if days < 30:
        return f"{days // 7} weeks ago"

    return moment.astimezone().strftime("%d %b %Y")


def format_day(moment: datetime, now: datetime | None = None) -> str:
    """Format a date as Today, Yesterday, or a short date (local time)."""

    now = now or datetime.now(UTC)
    local_moment = moment.astimezone()
    local_today = now.astimezone().date()

    if local_moment.date() == local_today:
        return "Today"
    if local_moment.date() == local_today - timedelta(days=1):
        return "Yesterday"

    return local_moment.strftime("%d %b %Y")


def format_timestamp(moment: datetime, now: datetime | None = None) -> str:
    """Format a date and time, for example 'Today, 10:42'."""

    return f"{format_day(moment, now)}, {moment.astimezone().strftime('%H:%M')}"


def format_duration(seconds: float) -> str:
    """Format a duration, for example '1 min 40 s' or '12 s'."""

    seconds = max(0, round(seconds))

    if seconds < 60:
        return f"{seconds} s"

    minutes, remainder = divmod(seconds, 60)

    if minutes < 60:
        return f"{minutes} min {remainder} s" if remainder else f"{minutes} min"

    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def format_time_left(seconds: float) -> str:
    """Format an estimate, for example 'about 6 minutes left'."""

    if seconds < 60:
        return "less than a minute left"

    minutes = round(seconds / 60)
    if minutes < 60:
        return "about 1 minute left" if minutes == 1 else f"about {minutes} minutes left"

    hours = round(minutes / 60)
    return "about 1 hour left" if hours == 1 else f"about {hours} hours left"


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    """Return '1 file' / '3 files'."""

    word = singular if count == 1 else (plural_form or f"{singular}s")
    return f"{count} {word}"
