from collections import deque
from datetime import UTC, datetime

from bzl.models.activity import ActivityLogEntry

MAX_ENTRIES = 200


class ActivityLogService:
    def __init__(self) -> None:
        self._entries: deque[ActivityLogEntry] = deque(maxlen=MAX_ENTRIES)

    def add(self, source: str, message: str, level: str = "info", section: str = "summary") -> None:
        entry = ActivityLogEntry(
            timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
            source=source,
            message=message,
            level=level,
            section=section,
        )
        self._entries.append(entry)

    def all(self) -> list[ActivityLogEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()
