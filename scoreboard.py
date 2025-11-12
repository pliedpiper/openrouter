from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlayerSummary:
    player: str
    rounds_played: int
    total_questions: int
    total_correct: int

    @property
    def accuracy(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return self.total_correct / self.total_questions


class ScoreStore:
    """Tiny SQLite-backed store for persisting round results."""

    def __init__(self, db_path: str | Path = "scores.db") -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_rounds_player
                ON rounds(player)
                """
            )

    @staticmethod
    def _validate(player: str, total: int, correct: int) -> None:
        if not player.strip():
            raise ValueError("player name must not be empty")
        if total <= 0:
            raise ValueError("total questions must be positive")
        if correct < 0 or correct > total:
            raise ValueError("correct answers must be between 0 and total")

    def record_round(self, player: str, total: int, correct: int) -> None:
        self._validate(player, total, correct)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO rounds(player, total, correct) VALUES (?, ?, ?)",
                (player.strip(), total, correct),
            )

    def get_player_summary(self, player: str) -> PlayerSummary | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as rounds_played,
                    COALESCE(SUM(total), 0) as total_questions,
                    COALESCE(SUM(correct), 0) as total_correct
                FROM rounds
                WHERE player = ?
                """,
                (player.strip(),),
            ).fetchone()

        if not row or row[0] == 0:
            return None

        return PlayerSummary(
            player=player.strip(),
            rounds_played=row[0],
            total_questions=row[1],
            total_correct=row[2],
        )

    def leaderboard(self, limit: int = 5) -> list[PlayerSummary]:
        if limit <= 0:
            return []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    player,
                    COUNT(*) as rounds_played,
                    SUM(total) as total_questions,
                    SUM(correct) as total_correct
                FROM rounds
                GROUP BY player
                HAVING SUM(total) > 0
                ORDER BY
                    CAST(total_correct AS REAL) / total_questions DESC,
                    total_correct DESC,
                    rounds_played DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            PlayerSummary(
                player=row[0],
                rounds_played=row[1],
                total_questions=row[2],
                total_correct=row[3],
            )
            for row in rows
        ]
