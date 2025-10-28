"""Data models for BG3 Connector."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, Optional


@dataclass(slots=True)
class PlayerPreferences:
    """Represents the matchmaking preferences of a player."""

    player_id: str
    platform: str
    game_mode: str
    level_range: str
    voice_chat: str
    timezone: str
    notes: Optional[str] = None
    tags: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerPreferences":
        """Create a :class:`PlayerPreferences` instance from a mapping."""

        tags: Iterable[str] | None = data.get("tags")
        return cls(
            player_id=data["player_id"],
            platform=data.get("platform", "unknown"),
            game_mode=data.get("game_mode", "unknown"),
            level_range=data.get("level_range", "any"),
            voice_chat=data.get("voice_chat", "optional"),
            timezone=data.get("timezone", "any"),
            notes=data.get("notes"),
            tags=set(tags) if tags else set(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the preferences to a dictionary."""

        data = asdict(self)
        data["tags"] = sorted(self.tags)
        return data
