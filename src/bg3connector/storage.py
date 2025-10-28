"""Persistence helpers for BG3 Connector."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable, Iterator, List

from .models import PlayerPreferences


class PreferenceRepository:
    """Persist player preferences to a SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        path = Path(database_path).expanduser()
        self.database_path = str(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS player_preferences (
                    player_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    game_mode TEXT NOT NULL,
                    level_range TEXT NOT NULL,
                    voice_chat TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    notes TEXT,
                    tags TEXT NOT NULL
                )
                """
            )

    def list_all(self) -> List[PlayerPreferences]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT player_id, platform, game_mode, level_range, voice_chat, timezone, notes, tags FROM player_preferences ORDER BY player_id"
            ).fetchall()
        return [self._row_to_preferences(row) for row in rows]

    def get(self, player_id: str) -> PlayerPreferences | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT player_id, platform, game_mode, level_range, voice_chat, timezone, notes, tags FROM player_preferences WHERE player_id = ?",
                (player_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_preferences(row)

    def upsert(self, preference: PlayerPreferences) -> None:
        payload = preference.to_dict()
        tags = json.dumps(sorted(preference.tags))
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO player_preferences (
                    player_id, platform, game_mode, level_range, voice_chat, timezone, notes, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    platform = excluded.platform,
                    game_mode = excluded.game_mode,
                    level_range = excluded.level_range,
                    voice_chat = excluded.voice_chat,
                    timezone = excluded.timezone,
                    notes = excluded.notes,
                    tags = excluded.tags
                """,
                (
                    payload["player_id"],
                    payload["platform"],
                    payload["game_mode"],
                    payload["level_range"],
                    payload["voice_chat"],
                    payload["timezone"],
                    payload.get("notes"),
                    tags,
                ),
            )

    def remove(self, player_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM player_preferences WHERE player_id = ?",
                (player_id,),
            )
            return cursor.rowcount > 0

    def __iter__(self) -> Iterator[PlayerPreferences]:
        return iter(self.list_all())

    def _row_to_preferences(self, row: sqlite3.Row) -> PlayerPreferences:
        tags_raw = row["tags"] if isinstance(row, sqlite3.Row) else row[7]
        tags: Iterable[str] = json.loads(tags_raw) if tags_raw else []
        return PlayerPreferences(
            player_id=row["player_id"] if isinstance(row, sqlite3.Row) else row[0],
            platform=row["platform"] if isinstance(row, sqlite3.Row) else row[1],
            game_mode=row["game_mode"] if isinstance(row, sqlite3.Row) else row[2],
            level_range=row["level_range"] if isinstance(row, sqlite3.Row) else row[3],
            voice_chat=row["voice_chat"] if isinstance(row, sqlite3.Row) else row[4],
            timezone=row["timezone"] if isinstance(row, sqlite3.Row) else row[5],
            notes=row["notes"] if isinstance(row, sqlite3.Row) else row[6],
            tags=set(tags),
        )
