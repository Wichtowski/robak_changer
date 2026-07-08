# robak_changer

Discord nickname bot for generating and managing server nicknames.
![robal](https://raw.githubusercontent.com/Wichtowski/robak_changer/refs/heads/main/ta.jpg)

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

The GitHub Actions workflow in `.github/workflows/deploy.yml` deploys the bot to the VPS.
It runs manually via the `workflow_dispatch` trigger.

Required GitHub secrets:

- `DEPLOY_HOST`: VPS host IP or hostname.
- `DEPLOY_USER`: SSH username.
- `DEPLOY_SSH_KEY`: Private SSH key.
- `DEPLOY_SSH_PASSPHRASE`: Optional password for the private SSH key.
- `DEPLOY_PATH`: Target directory on the VPS (e.g. `/opt/robak_changer`).
- `ENV_PRODUCTION`: The contents of the production `.env` file (e.g., `DISCORD_TOKEN`, `ZAO`, etc.).

Required GitHub variables:

- `DEPLOY_ARCHIVE`: The filename for the tarball archive (e.g. `release.tar.gz`).

The workflow copies the codebase and the generated `.env.production` file to the VPS, extracts the files, and uses docker-compose to build and start the containerized service.
The database and logs are stored inside the `bot_data` Docker volume dynamically, ensuring they are preserved across deployments.

## Commands

Commands use `/robak`.

Main commands:

- `generate`
- `add`
- `remove`
- `all`
- `last`
- `endorsed`
- `generate-zao`
- `kiss`
- `balls`
- `more`
