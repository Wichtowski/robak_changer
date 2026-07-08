![robal](https://raw.githubusercontent.com/Wichtowski/robak_changer/refs/heads/main/ta.jpg)

Discord nickname bot for generating and managing server nicknames.

## Setup

Install runtime and development dependencies with `uv`.

```bash
uv sync --extra dev
```

Create a local `.env` file or export the required environment variables.

```bash
DISCORD_TOKEN=your_bot_token
ZAO=discord_user_id
```

Optional configuration:

```bash
SYNC_APP_COMMANDS_ON_STARTUP=1
LOG_LEVEL=INFO
DEV_GUILD=discord_guild_id
DATA_DIR=./data
```

`DISCORD_TOKEN` and `ZAO` are required.

`ZAO` must be the Discord user ID of the target user.

The bot keeps a small per-guild request throttle of 5 requests per second.

Log files rotate automatically after 512 MB.

## Run

```bash
make dev
```

You can also run the entrypoint directly with:

```bash
uv run robak-changer
```

## Commands

All slash commands live under `/robak`.

Available commands:

- `generate`
- `add`
- `remove`
- `all`
- `last`
- `endorsed`
- `generate-zao`
- `more`
- `kiss`
- `balls`
- `blacklist add`
- `blacklist remove`
- `blacklist list`

`add`, `remove`, and the blacklist management commands are intended for guild moderators.

## Deploy

The GitHub Actions workflow in `.github/workflows/deploy.yml` deploys the bot to a VPS.

It runs manually via `workflow_dispatch`.

Required GitHub secrets:

- `DEPLOY_HOST` - VPS host IP or hostname
- `DEPLOY_USER` - SSH username
- `DEPLOY_SSH_KEY` - private SSH key
- `DEPLOY_SSH_PASSPHRASE` - optional passphrase for the private SSH key
- `DEPLOY_PATH` - target directory on the VPS, for example `/opt/robak_changer`
- `ENV_PRODUCTION` - contents of the production `.env` file, including `DISCORD_TOKEN` and `ZAO`

Required GitHub variables:

- `DEPLOY_ARCHIVE` - tarball filename, for example `release.tar.gz`

The workflow copies the codebase and generated production env file to the VPS, extracts the archive, and starts the container with `docker compose`.

The SQLite database and logs live in the `bot_data` volume, so they persist across deployments.
