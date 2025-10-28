# BG3 Connector

A lightweight command-line tool for Baldur's Gate 3 players to share their multiplayer preferences and discover compatible teammates.

## Features

- Store player matchmaking preferences locally in a simple JSON file.
- List all registered players and their key preferences.
- Find compatible matches based on platform, game mode, level range, voice chat, timezone, and shared tags.

## Installation

This project uses [PEP 621](https://peps.python.org/pep-0621/) metadata with `pyproject.toml`. Install it in an isolated environment (such as `venv`) and use `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

The tool installs the `bg3connector` command. Preferences are saved to `~/.bg3connector/players.json` by default, but you can override the path with the `--store` option.

```bash
# Add or update a player's preferences
bg3connector add TavTheWizard PC "story" "1-5" optional "UTC-5" \
  --tag roleplay --tag friendly --notes "Looking for weekend sessions"

# List all stored players
bg3connector list --verbose

# Find compatible matches for a player
bg3connector match TavTheWizard --min-score 4 --limit 5

# Remove a player from the store
bg3connector remove TavTheWizard
```

## Development

Run the CLI without installing by executing the module directly:

```bash
python -m bg3connector.cli --help
```

Feel free to extend the scoring logic in `src/bg3connector/matcher.py` or integrate with a real backend for a richer experience.
