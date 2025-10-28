"""FastAPI application exposing the BG3 Connector matchmaking service."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .matcher import match_players
from .models import PlayerPreferences
from .storage import PreferenceRepository

DEFAULT_DB_PATH = Path.home() / ".bg3connector" / "matchmaker.db"


class PlayerPayload(BaseModel):
    player_id: str
    platform: str
    game_mode: str
    level_range: str
    voice_chat: str
    timezone: str
    notes: str | None = None
    tags: set[str] = Field(default_factory=set)

    def to_preferences(self) -> PlayerPreferences:
        return PlayerPreferences(
            player_id=self.player_id,
            platform=self.platform,
            game_mode=self.game_mode,
            level_range=self.level_range,
            voice_chat=self.voice_chat,
            timezone=self.timezone,
            notes=self.notes,
            tags=set(self.tags),
        )


class PlayerResponse(PlayerPayload):
    @classmethod
    def from_preferences(cls, preferences: PlayerPreferences) -> "PlayerResponse":
        return cls(**preferences.to_dict())


class MatchResponse(BaseModel):
    player: PlayerResponse
    score: int


def get_database_path() -> str:
    override = os.environ.get("BG3CONNECTOR_DB_PATH")
    if override:
        return override
    return str(DEFAULT_DB_PATH)


@lru_cache
def get_repository() -> PreferenceRepository:
    return PreferenceRepository(get_database_path())


def repository_dependency() -> PreferenceRepository:
    return get_repository()


app = FastAPI(title="BG3 Connector API", version="0.2.0")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/players", response_model=List[PlayerResponse])
def list_players(repo: PreferenceRepository = Depends(repository_dependency)) -> List[PlayerResponse]:
    players = repo.list_all()
    return [PlayerResponse.from_preferences(pref) for pref in players]


@app.post("/players", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def upsert_player(
    payload: PlayerPayload,
    repo: PreferenceRepository = Depends(repository_dependency),
) -> PlayerResponse:
    preferences = payload.to_preferences()
    repo.upsert(preferences)
    stored = repo.get(preferences.player_id)
    assert stored is not None  # pragma: no cover - stored immediately above
    return PlayerResponse.from_preferences(stored)


@app.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str, repo: PreferenceRepository = Depends(repository_dependency)) -> PlayerResponse:
    preference = repo.get(player_id)
    if preference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return PlayerResponse.from_preferences(preference)


@app.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: str, repo: PreferenceRepository = Depends(repository_dependency)) -> None:
    deleted = repo.remove(player_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")


@app.get("/players/{player_id}/matches", response_model=List[MatchResponse])
def find_matches(
    player_id: str,
    min_score: int = 4,
    limit: int | None = 10,
    repo: PreferenceRepository = Depends(repository_dependency),
) -> List[MatchResponse]:
    seeker = repo.get(player_id)
    if seeker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    candidates: Iterable[PlayerPreferences] = (pref for pref in repo if pref.player_id != player_id)
    normalized_limit = None if limit == 0 else limit
    matches = match_players(seeker, candidates, min_score=min_score, limit=normalized_limit)
    return [
        MatchResponse(player=PlayerResponse.from_preferences(pref), score=score)
        for pref, score in matches
    ]
