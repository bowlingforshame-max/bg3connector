"""Matchmaking logic for BG3 Connector."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from .models import PlayerPreferences


def compatibility_score(
    seeker: PlayerPreferences,
    candidate: PlayerPreferences,
    weight_platform: int = 3,
    weight_game_mode: int = 3,
    weight_level_range: int = 2,
    weight_voice_chat: int = 1,
    weight_timezone: int = 1,
    weight_tags: int = 1,
) -> int:
    """Compute a simple compatibility score between two players."""

    score = 0
    if seeker.platform == candidate.platform:
        score += weight_platform
    if seeker.game_mode == candidate.game_mode:
        score += weight_game_mode
    if seeker.level_range == candidate.level_range:
        score += weight_level_range
    if seeker.voice_chat == candidate.voice_chat:
        score += weight_voice_chat
    if seeker.timezone == candidate.timezone:
        score += weight_timezone

    shared_tags = seeker.tags.intersection(candidate.tags)
    if shared_tags:
        score += weight_tags * len(shared_tags)

    return score


def match_players(
    seeker: PlayerPreferences,
    candidates: Iterable[PlayerPreferences],
    *,
    min_score: int = 4,
    limit: int | None = 10,
) -> List[Tuple[PlayerPreferences, int]]:
    """Return a ranked list of compatible players for the seeker."""

    scored: List[Tuple[PlayerPreferences, int]] = []
    for candidate in candidates:
        if candidate.player_id == seeker.player_id:
            continue
        score = compatibility_score(seeker, candidate)
        if score >= min_score:
            scored.append((candidate, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    if limit is None:
        return scored
    return scored[:limit]


def summarize_matches(matches: Sequence[Tuple[PlayerPreferences, int]]) -> str:
    """Create a human readable summary of matches."""

    lines = []
    for preference, score in matches:
        tags = ", ".join(sorted(preference.tags)) if preference.tags else "none"
        lines.append(
            (
                f"{preference.player_id} — score {score}\n"
                f"  Platform: {preference.platform}\n"
                f"  Mode: {preference.game_mode}\n"
                f"  Level range: {preference.level_range}\n"
                f"  Voice chat: {preference.voice_chat}\n"
                f"  Timezone: {preference.timezone}\n"
                f"  Tags: {tags}\n"
                f"  Notes: {preference.notes or 'none'}"
            )
        )
    return "\n\n".join(lines)
