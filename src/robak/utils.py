import sqlite3
import unicodedata
from dataclasses import dataclass
from random import sample
from threading import RLock
from typing import Final

from robak.config import BotConfig


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
        # legacy migrations removed for fresh deployment

    def generate_nickname(self, guild_id: int, who: str = "") -> NicknameGeneration:
        with self._lock:
            self._ensure_guild(guild_id)
            rows = self._connection.execute(
                "SELECT nick FROM nicknames WHERE guild_id = ? ORDER BY nick",
                (guild_id,),
            ).fetchall()
            guild_nicks = [row["nick"] for row in rows]

            if len(guild_nicks) < 2:
                return NicknameGeneration(
                    error="Not enough nicknames to generate a new one"
                )

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
            return (
                ", ".join(row["nick"] for row in rows) or "No generated nicknames yet"
            )

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

    # Blacklist management
    def add_blacklist_term(self, guild_id: int, term: str) -> str:
        term = term.strip().lower()
        if not term:
            return "Cannot add empty blacklist term"
        self._ensure_guild(guild_id)
        with self._lock:
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO blacklist (guild_id, term) VALUES (?, ?)",
                (guild_id, term),
            )
            self._connection.commit()
            if cursor.rowcount == 0:
                return f"{term} is already blacklisted"
            return f"Successfully blacklisted {term}"

    def list_matching_nicknames(self, guild_id: int, term: str) -> list[str]:
        term = term.strip().lower()
        if not term:
            return []
        self._ensure_guild(guild_id)
        with self._lock:
            rows = self._connection.execute(
                "SELECT nick FROM nicknames WHERE guild_id = ? ORDER BY nick",
                (guild_id,),
            ).fetchall()
            return [
                row["nick"]
                for row in rows
                if row["nick"].strip().lower() == term
            ]

    def move_nickname_to_blacklist(self, guild_id: int, term: str) -> tuple[int, str]:
        term = term.strip().lower()
        if not term:
            return 0, "Cannot move empty blacklist term"
        self._ensure_guild(guild_id)
        with self._lock:
            removed_cursor = self._connection.execute(
                "DELETE FROM nicknames WHERE guild_id = ? AND lower(nick) = ?",
                (guild_id, term),
            )
            blacklist_cursor = self._connection.execute(
                "INSERT OR IGNORE INTO blacklist (guild_id, term) VALUES (?, ?)",
                (guild_id, term),
            )
            self._connection.commit()
            removed_count = removed_cursor.rowcount
            if blacklist_cursor.rowcount == 0:
                if removed_count == 0:
                    return 0, f"{term} is already blacklisted"
                return removed_count, f"Moved {term} to blacklist"
            if removed_count == 0:
                return 0, f"Successfully blacklisted {term}"
            return removed_count, f"Moved {term} to blacklist"

    def remove_blacklist_term(self, guild_id: int, term: str) -> str:
        term = term.strip().lower()
        if not term:
            return "Cannot remove empty blacklist term"
        self._ensure_guild(guild_id)
        with self._lock:
            cursor = self._connection.execute(
                "DELETE FROM blacklist WHERE guild_id = ? AND term = ?",
                (guild_id, term),
            )
            self._connection.commit()
            if cursor.rowcount == 0:
                return f"{term} was not found in blacklist"
            return f"Successfully removed {term} from blacklist"

    def list_blacklist_terms(self, guild_id: int) -> set[str]:
        self._ensure_guild(guild_id)
        with self._lock:
            rows = self._connection.execute(
                "SELECT term FROM blacklist WHERE guild_id = ? ORDER BY term",
                (guild_id,),
            ).fetchall()
            return {row["term"] for row in rows}

    def is_blacklisted(self, guild_id: int, term: str) -> bool:
        term = term.strip().lower()
        if not term:
            return False
        with self._lock:
            row = self._connection.execute(
                "SELECT 1 FROM blacklist WHERE guild_id = ? AND term = ?",
                (guild_id, term),
            ).fetchone()
            return row is not None

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
        return "".join(
            char for char in user_input if self._is_allowed_nickname_character(char)
        ).strip()

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
                guild_id INTEGER NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
                term TEXT NOT NULL,
                PRIMARY KEY (guild_id, term)
            );

            -- legacy migrations table removed for fresh deployments
            """
        )
        self._connection.commit()

    # legacy migration helpers removed since this deployment starts fresh

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

    def _is_allowed_nickname_character(self, char: str) -> bool:
        if char in {" ", "-", "_"}:
            return True
        return unicodedata.category(char)[0] in {"L", "M", "N"}
