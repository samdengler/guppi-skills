"""Chrome browser history source adapter."""

import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .base import HistoryEntry, SourceAdapter

# Chrome stores timestamps as microseconds since 1601-01-01 (Windows epoch)
# Offset from Unix epoch (1970-01-01) to Windows epoch (1601-01-01)
CHROME_EPOCH_OFFSET = 11644473600

# Default Chrome History DB path (macOS)
DEFAULT_CHROME_PATH = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Google"
    / "Chrome"
    / "Default"
    / "History"
)


def _chrome_time_to_datetime(chrome_time: int) -> datetime:
    """Convert Chrome's microsecond timestamp to Python datetime."""
    # Chrome time is microseconds since 1601-01-01
    unix_timestamp = (chrome_time / 1_000_000) - CHROME_EPOCH_OFFSET
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)


def _datetime_to_chrome_time(dt: datetime) -> int:
    """Convert Python datetime to Chrome's microsecond timestamp."""
    unix_timestamp = dt.timestamp()
    return int((unix_timestamp + CHROME_EPOCH_OFFSET) * 1_000_000)


class ChromeAdapter(SourceAdapter):
    """Read Chrome browser history via SQLite."""

    def _db_path(self) -> Path:
        if self.path:
            return Path(self.path)
        return DEFAULT_CHROME_PATH

    def search(
        self,
        query: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
    ) -> list[HistoryEntry]:
        db_path = self._db_path()
        if not db_path.exists():
            return []

        # Copy DB to temp file to avoid Chrome's lock
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            shutil.copy2(db_path, tmp_path)
            return self._query_db(tmp_path, query, since, until, limit)
        finally:
            tmp_path.unlink(missing_ok=True)

    def _query_db(
        self,
        db_path: Path,
        query: str | None,
        since: datetime | None,
        until: datetime | None,
        limit: int,
    ) -> list[HistoryEntry]:
        conn = sqlite3.connect(str(db_path))
        try:
            conditions = []
            params: list = []

            if query:
                conditions.append("(u.url LIKE ? OR u.title LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            if since:
                conditions.append("v.visit_time >= ?")
                params.append(_datetime_to_chrome_time(since))

            if until:
                conditions.append("v.visit_time <= ?")
                params.append(_datetime_to_chrome_time(until))

            where = ""
            if conditions:
                where = "WHERE " + " AND ".join(conditions)

            sql = f"""
                SELECT v.visit_time, u.title, u.url
                FROM visits v
                JOIN urls u ON v.url = u.id
                {where}
                ORDER BY v.visit_time DESC
                LIMIT ?
            """
            params.append(limit)

            cursor = conn.execute(sql, params)
            entries = []
            for row in cursor:
                visit_time, title, url = row
                entries.append(
                    HistoryEntry(
                        timestamp=_chrome_time_to_datetime(visit_time),
                        source=self.name,
                        kind="url",
                        summary=title or url,
                        detail=url,
                    )
                )
            return entries
        finally:
            conn.close()

    def available(self) -> bool:
        return self._db_path().exists()

    def check_prereqs(self) -> list[str]:
        issues = []
        db_path = self._db_path()
        if not db_path.exists():
            issues.append(f"Chrome History DB not found: {db_path}")
            return issues
        # Test if we can actually read it
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(str(tmp_path))
            conn.execute("SELECT count(*) FROM urls")
            conn.close()
            tmp_path.unlink(missing_ok=True)
        except (PermissionError, sqlite3.OperationalError) as e:
            issues.append(
                f"Cannot read Chrome History DB: {e}\n"
                "On macOS, grant Full Disk Access to your terminal app in "
                "System Settings > Privacy & Security > Full Disk Access."
            )
        return issues

    def apply_prereqs(self) -> list[str]:
        # Chrome prereqs (Full Disk Access) can't be applied programmatically
        return []

    @classmethod
    def detect(cls) -> str | None:
        if DEFAULT_CHROME_PATH.exists():
            return str(DEFAULT_CHROME_PATH)
        return None
