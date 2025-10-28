"""Command line interface for the BG3 Connector."""

from __future__ import annotations

import argparse
import os
from typing import Iterable, List

import httpx

from .matcher import summarize_matches
from .models import PlayerPreferences

DEFAULT_API_URL = os.environ.get("BG3CONNECTOR_API_URL", "http://localhost:8000")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-base",
        default=DEFAULT_API_URL,
        help="Base URL of the BG3 Connector API (default: %(default)s)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add or update a player's preferences")
    _add_player_arguments(add_parser)

    remove_parser = subparsers.add_parser("remove", help="Remove a player from the service")
    remove_parser.add_argument("player_id", help="Identifier of the player to remove")

    list_parser = subparsers.add_parser("list", help="List all registered players")
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


def _format_status_error(error: httpx.HTTPStatusError) -> str:
    response = error.response
    detail: str | None = None
    try:
        payload = response.json()
        if isinstance(payload, dict) and "detail" in payload:
            detail = str(payload["detail"])
    except ValueError:
        detail = None
    base = f"API error {response.status_code}"
    if detail:
        base += f": {detail}"
    return base


def run_cli(args: argparse.Namespace) -> str:
    try:
        with httpx.Client(base_url=args.api_base.rstrip("/")) as client:
            if args.command == "add":
                preference = _create_preference_from_args(args)
                response = client.post("/players", json=preference.to_dict())
                response.raise_for_status()
                data = response.json()
                return f"Stored preferences for {data['player_id']}."

            if args.command == "remove":
                response = client.delete(f"/players/{args.player_id}")
                if response.status_code == 404:
                    return f"No preferences found for {args.player_id}."
                response.raise_for_status()
                return f"Removed preferences for {args.player_id}."

            if args.command == "list":
                response = client.get("/players")
                response.raise_for_status()
                payload: List[dict] = response.json()
                if not payload:
                    return "No players found in the service."
                preferences = [PlayerPreferences.from_dict(item) for item in payload]
                return _format_preferences(preferences, verbose=args.verbose)

            if args.command == "match":
                params = {"min_score": args.min_score, "limit": args.limit}
                response = client.get(f"/players/{args.player_id}/matches", params=params)
                if response.status_code == 404:
                    return (
                        "Player not found. Add them first with the 'add' command "
                        "or ensure the ID is correct."
                    )
                response.raise_for_status()
                payload = response.json()
                if not payload:
                    return "No compatible players were found."
                matches = [
                    (PlayerPreferences.from_dict(item["player"]), item["score"])
                    for item in payload
                ]
                return summarize_matches(matches)
    except httpx.HTTPStatusError as error:
        return _format_status_error(error)
    except httpx.RequestError as error:
        return (
            "Failed to reach the BG3 Connector API. "
            f"Verify the service is running at {args.api_base}.\n"
            f"Details: {error}"
        )

    raise ValueError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    message = run_cli(args)
    print(message)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
