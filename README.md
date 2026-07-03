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
