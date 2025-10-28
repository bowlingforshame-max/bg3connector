"""Command line interface for the BG3 Connector."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .matcher import match_players, summarize_matches
from .models import PlayerPreferences
from .storage import PreferenceStore

DEFAULT_DATA_PATH = Path.home() / ".bg3connector" / "players.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--store",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"Path to the preferences store (default: {DEFAULT_DATA_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add or update a player's preferences")
    _add_player_arguments(add_parser)

    remove_parser = subparsers.add_parser("remove", help="Remove a player from the store")
    remove_parser.add_argument("player_id", help="Identifier of the player to remove")

    list_parser = subparsers.add_parser("list", help="List all stored players")
    list_parser.add_argument("--verbose", action="store_true", help="Show detailed preferences")

    match_parser = subparsers.add_parser("match", help="Find matches for a player")
    match_parser.add_argument("player_id", help="Identifier of the player seeking matches")
    match_parser.add_argument(
        "--min-score",
        type=int,
        default=4,
        help="Minimum compatibility score to consider a match",
    )
    match_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of matches to return (use 0 for no limit)",
    )

    return parser


def _add_player_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("player_id", help="Unique identifier or handle for the player")
    parser.add_argument("platform", help="Preferred platform, e.g., PC or PS5")
    parser.add_argument("game_mode", help="Desired game mode, e.g., campaign or honour")
    parser.add_argument("level_range", help="Character level range, e.g., 1-5")
    parser.add_argument("voice_chat", help="Voice chat preference: required/optional/none")
    parser.add_argument("timezone", help="Player timezone or preferred play window")
    parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        help="Add descriptive tags such as 'roleplay', 'modded', 'new player'",
    )
    parser.add_argument(
        "--notes",
        default=None,
        help="Optional free-form notes for potential teammates",
    )


def _create_preference_from_args(args: argparse.Namespace) -> PlayerPreferences:
    return PlayerPreferences(
        player_id=args.player_id,
        platform=args.platform,
        game_mode=args.game_mode,
        level_range=args.level_range,
        voice_chat=args.voice_chat,
        timezone=args.timezone,
        notes=args.notes,
        tags=set(args.tags or []),
    )


def _format_preferences(preferences: Iterable[PlayerPreferences], verbose: bool = False) -> str:
    lines = []
    for preference in preferences:
        base = f"{preference.player_id} — {preference.platform}, {preference.game_mode}, {preference.level_range}"
        if not verbose:
            lines.append(base)
            continue
        tags = ", ".join(sorted(preference.tags)) if preference.tags else "none"
        lines.append(
            (
                f"{base}\n"
                f"  Voice chat: {preference.voice_chat}\n"
                f"  Timezone: {preference.timezone}\n"
                f"  Tags: {tags}\n"
                f"  Notes: {preference.notes or 'none'}"
            )
        )
    return "\n\n".join(lines)


def run_cli(args: argparse.Namespace) -> str:
    store = PreferenceStore(args.store)

    if args.command == "add":
        preference = _create_preference_from_args(args)
        store.add_or_update(preference)
        return f"Stored preferences for {preference.player_id}."

    if args.command == "remove":
        removed = store.remove(args.player_id)
        if removed:
            return f"Removed preferences for {args.player_id}."
        return f"No preferences found for {args.player_id}."

    if args.command == "list":
        preferences = list(store)
        if not preferences:
            return "No players found in the store."
        return _format_preferences(preferences, verbose=args.verbose)

    if args.command == "match":
        seeker = store.find(args.player_id)
        if not seeker:
            return (
                "Player not found. Add them first with the 'add' command "
                "or ensure the ID is correct."
            )
        limit = None if args.limit == 0 else args.limit
        matches = match_players(seeker, store, min_score=args.min_score, limit=limit)
        if not matches:
            return "No compatible players were found."
        return summarize_matches(matches)

    raise ValueError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    message = run_cli(args)
    print(message)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
