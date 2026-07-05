# robak_changer

Discord nickname bot for generating and managing server nicknames.

## Setup

Install runtime dependencies:

```bash
python3 -m pip install discord.py python-dotenv
```

Create environment variables:

```bash
DISCORD_TOKEN=your_bot_token
ZAO=discord_user_id
```

Optional:

```bash
SYNC_APP_COMMANDS_ON_STARTUP=1
LOG_LEVEL=INFO
```

The bot allows up to 5 requests per second per Discord server.
Requests above that limit are ignored until the one-second window clears.
Log files are truncated automatically after 512MB.

## Run

```bash
python3 main.py
```

## Deploy

The GitHub Actions workflow in `.github/workflows/main.yml` deploys the selected ref to the VPS.
Pushes to `main` deploy automatically.
Manual runs can deploy a specific branch, tag, or commit SHA with the `ref` input.

Required GitHub secrets:

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`

Optional GitHub variables:

- `VPS_DEPLOY_PATH`, defaults to `/opt/robak_changer`
- `VPS_SERVICE_NAME`, defaults to `robak_changer`
- `VPS_SSH_PORT`, defaults to `22`

The VPS must have the runtime `.env` at `/opt/robak_changer/shared/.env` unless `VPS_DEPLOY_PATH` changes that base path.
The workflow preserves `/opt/robak_changer/shared/data.sqlite3` and `/opt/robak_changer/shared/logs`.
Deployment fails if `data.sqlite3` is larger than 1.5GB.
Log files over 512MB are truncated before and after restart, and logrotate is configured with the same limit.

## Commands

Commands use `/robak`.

Main commands:

- `generate`
- `add`
- `remove`
- `all`
- `last`
- `endorsed`
- `setlang`
- `generate-zao`
- `kiss`
- `sigma`
- `more`

Language codes are set with `/robak setlang`.
Common ISO language codes such as `en`, `pl`, `de`, `fr`, `es`, `ja`, `zh`, and `uk` are supported.
