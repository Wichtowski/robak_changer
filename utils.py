import re
import sqlite3
from dataclasses import dataclass
from random import sample
from threading import RLock
from typing import Final

from config import BotConfig


@dataclass(frozen=True)
class NicknameGeneration:
    nickname: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.nickname is not None

    @property
    def message(self) -> str:
        return self.nickname or self.error or "Could not generate nickname"


class NicknameStore:
    def __init__(self):
        self.ENCODING: Final[str] = "utf-8"
        self._lock = RLock()
        self._connection = sqlite3.connect(BotConfig.DB_FILE, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._configure_connection()
        self._create_schema()
        self._migrate_legacy_files()

    def generate_nickname(self, guild_id: int, who: str = "") -> NicknameGeneration:
        with self._lock:
            self._ensure_guild(guild_id)
            rows = self._connection.execute(
                "SELECT nick FROM nicknames WHERE guild_id = ? ORDER BY nick",
                (guild_id,),
            ).fetchall()
            guild_nicks = [row["nick"] for row in rows]

            if len(guild_nicks) < 2:
                return NicknameGeneration(error="Not enough nicknames to generate a new one")

            n1, n2 = sample(guild_nicks, 2)
            fixed_nick = self._format_for_language(guild_id, n1, n2)
            generated = f"Żao {fixed_nick}" if who == "zaojoga" else fixed_nick
            self._connection.execute(
                "INSERT INTO generated (guild_id, nick, is_zao) VALUES (?, ?, ?)",
                (guild_id, generated, int(who == "zaojoga")),
            )
            self._connection.commit()
            return NicknameGeneration(nickname=generated)

    def list_nicknames(self, guild_id: int) -> str:
        with self._lock:
            rows = self._connection.execute(
                "SELECT nick FROM nicknames WHERE guild_id = ? ORDER BY nick",
                (guild_id,),
            ).fetchall()
            return "\n".join(row["nick"] for row in rows) or "No nicknames found"

    def add_nickname(self, guild_id: int, nickname: str) -> str:
        if len(nickname) > BotConfig.MAX_NICKNAME_LENGTH:
            return "Nickname is too long"
        if nickname == "":
            return "What am I supposed to do with an empty nickname?"

        with self._lock:
            self._ensure_guild(guild_id)
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO nicknames (guild_id, nick) VALUES (?, ?)",
                (guild_id, nickname),
            )
            self._connection.commit()
            if cursor.rowcount == 0:
                return f"{nickname} already exists"
            return f"Successfully added {nickname}"

    def remove_nickname(self, guild_id: int, nickname: str) -> str:
        if nickname == "":
            return "Umm do I look like I read minds?"

        with self._lock:
            cursor = self._connection.execute(
                "DELETE FROM nicknames WHERE guild_id = ? AND nick = ?",
                (guild_id, nickname),
            )
            self._connection.commit()
            if cursor.rowcount == 0:
                return f"{nickname} was not found"
            return f"Successfully deleted {nickname}"

    def list_recent_generated_nicknames(self, guild_id: int) -> str:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT nick
                FROM generated
                WHERE guild_id = ?
                ORDER BY id DESC
                LIMIT 10
                """,
                (guild_id,),
            ).fetchall()
            return ", ".join(row["nick"] for row in rows) or "No generated nicknames yet"

    def list_endorsed_nicknames(self, guild_id: int) -> str:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT nick, votes
                FROM endorsements
                WHERE guild_id = ?
                ORDER BY votes DESC, nick ASC
                LIMIT 10
                """,
                (guild_id,),
            ).fetchall()
            if not rows:
                return "No endorsed nicknames yet"
            return "\n".join(f"{row['nick']} - {row['votes']}" for row in rows)

    def set_language(self, guild_id: int, lang: str) -> str:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO guilds (guild_id, lang)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET lang = excluded.lang
                """,
                (guild_id, lang),
            )
            self._connection.commit()
            return f"Language set to {lang}"

    def get_language(self, guild_id: int) -> str:
        with self._lock:
            self._ensure_guild(guild_id)
            row = self._connection.execute(
                "SELECT lang FROM guilds WHERE guild_id = ?",
                (guild_id,),
            ).fetchone()
            return row["lang"] if row else "en"

    def sanitize_for_language(self, lang: str, user_input: str) -> str:
        match lang:
            case "pl":
                return re.sub(r"[^a-zA-Z\s\-_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", "", user_input).strip()
            case "en" | _:
                return re.sub(r"[^a-zA-Z\s\-_]", "", user_input).strip()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _configure_connection(self) -> None:
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL DEFAULT 'en'
            );

            CREATE TABLE IF NOT EXISTS nicknames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
                nick TEXT NOT NULL,
                UNIQUE (guild_id, nick)
            );

            CREATE TABLE IF NOT EXISTS generated (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
                nick TEXT NOT NULL,
                is_zao INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_generated_recent
            ON generated (guild_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS endorsements (
                guild_id INTEGER NOT NULL,
                nick TEXT NOT NULL,
                votes INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, nick)
            );

            CREATE TABLE IF NOT EXISTS blacklist (
                term TEXT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS legacy_migrations (
                guild_id INTEGER PRIMARY KEY,
                migrated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        self._connection.commit()

    def _migrate_legacy_files(self) -> None:
        for guild_dir in BotConfig.BASE_DIR.iterdir():
            if not guild_dir.is_dir() or not guild_dir.name.isdigit():
                continue

            guild_id = int(guild_dir.name)
            if self._legacy_migration_done(guild_id):
                continue

            self._ensure_guild(guild_id)
            self._migrate_lang(guild_id, guild_dir / "lang.csv")
            self._migrate_nicknames(guild_id, guild_dir / "nicknames.csv")
            self._migrate_generated(guild_id, guild_dir / "generated.csv", is_zao=False)
            self._migrate_generated(guild_id, guild_dir / "zao_generated.csv", is_zao=True)
            self._connection.execute(
                "INSERT OR IGNORE INTO legacy_migrations (guild_id) VALUES (?)",
                (guild_id,),
            )
        self._connection.commit()

    def _legacy_migration_done(self, guild_id: int) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM legacy_migrations WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return row is not None

    def _migrate_lang(self, guild_id: int, path) -> None:
        if not path.exists():
            return

        lang = self._read_legacy_lines(path)
        if not lang:
            return

        self._connection.execute(
            """
            INSERT INTO guilds (guild_id, lang)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET lang = excluded.lang
            """,
            (guild_id, lang[0]),
        )

    def _migrate_nicknames(self, guild_id: int, path) -> None:
        for nick in self._read_legacy_lines(path):
            self._connection.execute(
                "INSERT OR IGNORE INTO nicknames (guild_id, nick) VALUES (?, ?)",
                (guild_id, nick),
            )

    def _migrate_generated(self, guild_id: int, path, is_zao: bool) -> None:
        for nick in self._read_legacy_lines(path):
            self._connection.execute(
                "INSERT INTO generated (guild_id, nick, is_zao) VALUES (?, ?, ?)",
                (guild_id, nick, int(is_zao)),
            )

    def _read_legacy_lines(self, path) -> list[str]:
        if not path.exists():
            return []
        return [
            line.strip()
            for line in path.read_text(encoding=self.ENCODING).splitlines()
            if line.strip()
        ]

    def _ensure_guild(self, guild_id: int) -> None:
        self._connection.execute(
            "INSERT OR IGNORE INTO guilds (guild_id, lang) VALUES (?, 'en')",
            (guild_id,),
        )

    def _format_for_language(self, guild_id: int, n1: str, n2: str) -> str:
        guild_lang = self.get_language(guild_id)
        match guild_lang:
            case "pl":
                return self._format_polish_nicknames(n1, n2)
            case "en" | _:
                return f"{n1} {n2}"

    def _format_polish_nicknames(self, n1: str, n2: str) -> str:
        if not n1 or not n2:
            return ""
        if n1[-1] == "a" and n2[-1] == "y":
            n2 = n2[:-1] + "a"
        elif n2[-1] == "y":
            n2 = n2[:-1] + "a"
        return f"{n1} {n2}"
