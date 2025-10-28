"""Persistence helpers for BG3 Connector."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, List

from .models import PlayerPreferences


class PreferenceStore:
    """Persist player preferences to a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_all(self) -> List[PlayerPreferences]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        return [PlayerPreferences.from_dict(item) for item in data]

    def save_all(self, preferences: Iterable[PlayerPreferences]) -> None:
        data = [pref.to_dict() for pref in preferences]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)

    def add_or_update(self, preference: PlayerPreferences) -> None:
        preferences = self.load_all()
        for index, existing in enumerate(preferences):
            if existing.player_id == preference.player_id:
                preferences[index] = preference
                break
        else:
            preferences.append(preference)
        self.save_all(preferences)

    def remove(self, player_id: str) -> bool:
        preferences = self.load_all()
        filtered = [pref for pref in preferences if pref.player_id != player_id]
        if len(filtered) == len(preferences):
            return False
        self.save_all(filtered)
        return True

    def find(self, player_id: str) -> PlayerPreferences | None:
        for preference in self.load_all():
            if preference.player_id == player_id:
                return preference
        return None

    def __iter__(self) -> Iterator[PlayerPreferences]:
        return iter(self.load_all())
