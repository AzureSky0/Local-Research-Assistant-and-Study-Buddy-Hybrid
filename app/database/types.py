from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Stores datetimes in UTC and always returns timezone-aware UTC values.

    SQLite does not store timezone information, so values read back
    would otherwise be naive. Naive values written to the database
    are rejected to avoid ambiguous timestamps.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("Naive datetimes are not allowed; use a timezone-aware UTC datetime.")

        return value.astimezone(UTC)

    def process_result_value(
        self,
        value: Any,
        dialect: Dialect,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)
