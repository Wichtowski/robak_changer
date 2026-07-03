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
DISCORD_APP_COMMAND_GUILD_ID=guild_id
SYNC_APP_COMMANDS_ON_STARTUP=1
LOG_LEVEL=INFO
```

## Run

```bash
python3 main.py
```

## Commands

Prefix commands use `!robak`.
Slash commands use `/robak`.

Main commands:

- `generate`
- `add`
- `remove`
- `all`
- `last`
- `endorsed`
- `setlang`
- `zao`
- `kiss`
- `sigma`
