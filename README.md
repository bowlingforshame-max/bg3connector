# BG3 Connector

A lightweight matchmaking service for Baldur's Gate 3 players. It exposes a FastAPI backend with a shared SQLite datastore and a CLI client that talks to the service over HTTP.

## Features

- Persist player matchmaking preferences in a shared SQLite database (configurable via `BG3CONNECTOR_DB_PATH`).
- Expose a REST API for creating, listing, matching, and removing players.
- Provide a CLI that calls the remote API to manage players and discover compatible teammates.
- Score compatibility based on platform, game mode, level range, voice chat, timezone, and shared tags.

## Installation

This project uses [PEP 621](https://peps.python.org/pep-0621/) metadata with `pyproject.toml`. Install it in an isolated environment (such as `venv`) and use `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running the API

Start the FastAPI application with Uvicorn. By default the service stores data in `~/.bg3connector/matchmaker.db`.

```bash
uvicorn bg3connector.api:app --reload
```

Set `BG3CONNECTOR_DB_PATH` to change the SQLite file location when starting the server:

```bash
BG3CONNECTOR_DB_PATH=/path/to/matchmaker.db uvicorn bg3connector.api:app
```

The API exposes the following endpoints:

- `GET /health` – quick status check.
- `GET /players` – list all registered players.
- `POST /players` – create or update a player's preferences.
- `GET /players/{player_id}` – fetch a single player's preferences.
- `DELETE /players/{player_id}` – remove a player.
- `GET /players/{player_id}/matches` – return ranked matches for the specified player.

## CLI Usage

The project installs the `bg3connector` command, which sends HTTP requests to the API. By default it targets `http://localhost:8000`, but you can override this with the `--api-base` option or the `BG3CONNECTOR_API_URL` environment variable.

```bash
# Add or update a player's preferences
bg3connector add TavTheWizard PC "story" "1-5" optional "UTC-5" \
  --tag roleplay --tag friendly --notes "Looking for weekend sessions"

# List all players currently in the shared service
bg3connector list --verbose

# Find compatible matches for a player
bg3connector match TavTheWizard --min-score 4 --limit 5

# Remove a player from the service
bg3connector remove TavTheWizard
```

If the CLI cannot reach the service it will display a helpful error suggesting you start the API or update the base URL.

## Development

Run the CLI without installing by executing the module directly (ensure the API is running first):

```bash
python -m bg3connector.cli --help
```

You can also launch the API using Python's module execution for a quick start:

```bash
python -m uvicorn bg3connector.api:app --reload
```

Adjust the matchmaking logic in `src/bg3connector/matcher.py` or extend the API to include notifications, authentication, or richer preference filtering as next steps.
